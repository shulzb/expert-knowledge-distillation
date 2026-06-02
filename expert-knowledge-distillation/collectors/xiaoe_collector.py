#!/usr/bin/env python3
"""
distill-system: xiaoe_collector.py v5
小鹅通圈子采集器 — 支持DB直写、增量更新、完整内容
"""

import sys, os, json, re, requests
from datetime import datetime
from typing import List, Dict, Optional

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)

from collectors.base_collector import BaseCollector
from db.database import add_source, add_post, rebuild_fts, get_conn

API_DOMAIN = 'https://quanzi.xiaoe-tech.com/xe.community.community_service/small_community'
COOKIE_PATH = os.path.join(SYSTEM_DIR, 'config', 'xiaoe_cookie.json')


def load_cookie() -> str:
    """加载小鹅通 Cookie"""
    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH, encoding='utf-8') as f:
            return json.load(f).get('cookie', '')
    # 兼容旧路径 (quanzi-skill)
    old_paths = [
        os.path.expanduser(r'~\.workbuddy\skills\quanzi-skill\config.json'),
        os.path.join(os.path.dirname(SYSTEM_DIR), 'skills', 'quanzi-skill', 'config.json'),
    ]
    for old_path in old_paths:
        if os.path.exists(old_path):
            with open(old_path, encoding='utf-8') as f:
                return json.load(f).get('cookie', '')
    return ''


def save_cookie(cookie: str):
    """保存 Cookie"""
    os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
    with open(COOKIE_PATH, 'w', encoding='utf-8') as f:
        json.dump({'cookie': cookie, 'updated_at': datetime.now().isoformat()}, f, ensure_ascii=False)


def clean_html(html_str: str) -> str:
    """HTML转纯文本"""
    if not isinstance(html_str, str):
        return ''
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ').replace('&quot;', '"')
    return re.sub(r'\s+', ' ', text).strip()


def extract_text(feed: Dict, full: bool = False) -> str:
    """
    从feed数据中提取可读文本。
    full=True 返回完整文本（不限长度）。
    """
    raw = feed.get('org_content') or feed.get('content') or ''
    if isinstance(raw, dict):
        parts = []
        if raw.get('text'):
            parts.append(raw['text'])
        for rec in raw.get('mix_records', raw.get('audio_records', [])):
            if isinstance(rec, dict) and rec.get('text'):
                parts.append(rec['text'])
        return '\n'.join(parts)
    return clean_html(raw)


class XiaoeCollector(BaseCollector):
    """小鹅通圈子采集器"""

    def __init__(self, source_id: str, config: dict):
        super().__init__(source_id)
        self.name = config['name']
        self.community_id = config['community_id']
        self.app_id = config['app_id']
        self.expert_name = config.get('expert_name', '')
        self.cookie = config.get('cookie', '') or load_cookie()
        self.tag_filter = config.get('tag_filter', '')

    @property
    def source_name(self) -> str:
        return self.name

    @property
    def source_type(self) -> str:
        return 'xiaoe'

    def _build_headers(self):
        return {
            'accept': 'application/json, text/plain, */*',
            'agent-type': 'pc',
            'app_id': self.app_id,
            'cookie': self.cookie,
            'login_app_id': self.app_id,
            'referer': 'https://quanzi.xiaoe-tech.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/132.0.0.0 Safari/537.36',
        }

    def fetch_posts(self, since_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        获取帖子列表。
        since_id: 上次抓取的最后一条 post_id（用于增量）
        """
        headers = self._build_headers()
        api = f'{API_DOMAIN}/xe.community/get_feeds_list/1.1.0'
        all_feeds = []

        page_limit = 5
        found_since = not since_id  # 没有since_id则全部获取

        for page in range(1, page_limit + 1):
            params = {
                'app_id': self.app_id,
                'community_id': self.community_id,
                'feeds_list_type': '-2',
                'order_filed': 'created_at',
                'hide_exercise': '1',
                'page': str(page),
                'page_size': '50',
            }
            r = requests.get(api, headers=headers, params=params, timeout=30)
            d = r.json()
            code = d.get('code')
            if code != 0:
                print(f"  ⚠️ Page {page}: API错误 code={code} msg={d.get('msg','')}")
                if code == 23:
                    print("  ❌ Cookie已过期，请重新获取")
                break

            feeds = d.get('data', {}).get('list', [])
            for feed in feeds:
                feed_id = feed.get('id', '')
                # 检查是否已抓取过
                if since_id and feed_id == since_id:
                    found_since = True
                    break
                if found_since:
                    all_feeds.append(feed)

            if len(feeds) < 50:
                break
            if found_since and since_id:
                break

        if since_id and not found_since:
            print(f"  ⚠️ 未找到 since_id={since_id}，可能为新数据源，已抓取 {len(all_feeds)} 条")

        # 标准化
        results = []
        for feed in all_feeds:
            normalized = self._normalize_feed(feed)
            if normalized:
                results.append(normalized)

        return results

    def fetch_full_content(self, post_id: str) -> str:
        """获取完整内容（暂同 fetch_posts）"""
        return ''

    def _normalize_feed(self, feed: Dict) -> Optional[Dict]:
        """将单条feed标准化为统一格式"""
        post_id = feed.get('id', '')
        if not post_id:
            return None

        # 标签筛选（如果设定了）
        if self.tag_filter:
            ftags = [t.get('tag_name', '') for t in feed.get('tags', [])]
            if self.tag_filter not in ftags:
                return None

        title = (feed.get('title') or '').strip()

        # 获取完整内容
        content = extract_text(feed, full=True)

        # 如果标题为空，尝试从内容中提取
        if not title and content:
            first_line = content.split('\n')[0].strip()
            m = re.match(r'#刘润日课\s+\d{4}年\d{1,2}月\d{1,2}日\s+(.*)', first_line)
            if m:
                title = m.group(1).strip()
            else:
                title = first_line[:40]

        # 元数据
        created_at = feed.get('created_at', '')
        nick_name = feed.get('nick_name', '')
        role_name = feed.get('role_name', '')

        # 标签
        tags_list = [t.get('tag_name', '') for t in feed.get('tags', [])]

        return {
            'post_id': post_id,
            'title': title,
            'content': content,
            'raw_content': json.dumps(feed, ensure_ascii=False),
            'author_name': nick_name,
            'author_role': role_name,
            'tags': json.dumps(tags_list, ensure_ascii=False),
            'is_picked': 1 if feed.get('is_chosen') else 0,
            'comment_cnt': feed.get('comment_count', 0),
            'like_cnt': feed.get('zan_num', 0),
            'share_cnt': feed.get('share_num', 0),
            'published_at': created_at,
        }

    def set_cookie(self, cookie: str):
        """设置并保存Cookie"""
        self.cookie = cookie
        save_cookie(cookie)

    def check_cookie(self) -> bool:
        """检测Cookie是否有效"""
        headers = self._build_headers()
        api = f'{API_DOMAIN}/xe.community/get_feeds_list/1.1.0'
        params = {
            'app_id': self.app_id,
            'community_id': self.community_id,
            'feeds_list_type': '-2',
            'order_filed': 'created_at',
            'hide_exercise': '1',
            'page': '1',
            'page_size': '1',
        }
        try:
            r = requests.get(api, headers=headers, params=params, timeout=15)
            return r.json().get('code') == 0
        except Exception:
            return False


def run_collect(source_id: str, config: dict, incremental: bool = True):
    """
    一站式采集：创建采集器 → 抓取 → 写入DB → 重建索引
    """
    collector = XiaoeCollector(source_id, config)

    # Cookie检查
    if not collector.cookie:
        print('❌ Cookie 未配置，请先设置')
        return 0

    if not collector.check_cookie():
        print('⚠️ Cookie 可能已过期，尝试继续...')

    # 注册数据源
    add_source(
        source_id=source_id,
        name=config['name'],
        platform='xiaoe',
        expert_name=config.get('expert_name', ''),
        description=config.get('description', ''),
    )

    # 增量抓取
    since_id = None
    if incremental:
        conn = get_conn()
        row = conn.execute(
            "SELECT post_id FROM posts WHERE source_id=? ORDER BY published_at DESC LIMIT 1",
            (source_id,)
        ).fetchone()
        conn.close()
        if row:
            since_id = row['post_id']
            print(f'📌 增量模式，上次最后一条: {since_id}')

    print(f'🔄 正在抓取 {config["name"]} ...')
    posts = collector.fetch_posts(since_id=since_id)
    print(f'📊 获取到 {len(posts)} 条新帖子')

    if not posts:
        print('✅ 无新内容')
        return 0

    # 写入数据库
    imported = 0
    for p in posts:
        result = add_post(source_id, **p)
        if result is not None:
            imported += 1

    rebuild_fts()
    print(f'✅ 新增 {imported}/{len(posts)} 条帖子')
    return imported


# 预配置数据源
SOURCES = {
    'xiaoe_liurun': {
        'name': '刘润进化岛',
        'community_id': 'c_6142e4a53faeb_xQC3MEX54398',
        'app_id': 'apphKIqvnYG9370',
        'expert_name': '刘润',
        'tag_filter': '刘润日课',
        'description': '刘润老师的商业付费社群 — 刘润日课',
    },
    'xiaoe_runyu': {
        'name': '润宇创业笔记',
        'community_id': 'c_682ada7ab22a1_nTDX4Y5g3647',
        'app_id': 'appgup6vo5q4830',
        'expert_name': '润宇',
        'tag_filter': '润宇票圈',
        'description': '润宇老师主理社群，一个持续进化的商业成长圈 — 润宇票圈',
    },
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='小鹅通采集器 v5')
    parser.add_argument('--source', choices=list(SOURCES.keys()), help='数据源ID')
    parser.add_argument('--set-cookie', help='设置Cookie')
    parser.add_argument('--check', action='store_true', help='检测Cookie')
    parser.add_argument('--full', action='store_true', help='全量抓取（覆盖增量）')
    parser.add_argument('--list', action='store_true', help='列出数据源')
    args = parser.parse_args()

    if args.list:
        print('可用数据源:')
        for k, v in SOURCES.items():
            print(f'  {k}: {v["name"]} — {v.get("description","")}')
        return

    if args.set_cookie:
        save_cookie(args.set_cookie)
        print('✅ Cookie 已保存')
        return

    if args.check:
        for sid in SOURCES:
            col = XiaoeCollector(sid, SOURCES[sid])
            ok = col.check_cookie()
            print(f'  {sid}: {"✅有效" if ok else "❌无效"}')
        return

    if args.source:
        config = SOURCES[args.source]
        run_collect(args.source, config, incremental=not args.full)
    else:
        print('请指定 --source，或 --list 查看可用数据源')


if __name__ == '__main__':
    main()

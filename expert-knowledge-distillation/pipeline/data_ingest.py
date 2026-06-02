#!/usr/bin/env python3
"""
distill-system: data_ingest.py
从现有的 Markdown 报告文件解析帖子，导入 SQLite 数据库。
"""

import sys, os, re, json
from datetime import datetime

# 确保能找到 db 模块
SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)

from db.database import (
    init_db, add_source, add_post, rebuild_fts,
    get_conn, list_sources
)


def parse_riko_report(md_path: str) -> list:
    """
    解析刘润日课合集的 Markdown 报告。
    返回 list[dict]，每个 dict 包含帖子的结构化数据。
    """
    with open(md_path, encoding='utf-8') as f:
        text = f.read()

    # 按 "### N. " 分割每个帖子
    posts_raw = re.split(r'\n### \d+\.\s+', text)
    posts = []

    for block in posts_raw[1:]:  # 跳过标题/速览等头部内容
        lines = block.strip().split('\n')
        if not lines:
            continue

        # 提取标题（第一条非空行就是标题）
        title = lines[0].strip()

        # 提取时间和作者
        meta_match = re.search(r'🕐\s*([\d\-:\s]+)(?:\s*\|\s*👤\s*([^(]+?)\s*(?:\(([^)]*)\))?)?(?:\s*\|\s*⭐\s*精选)?', block)
        published_at = meta_match.group(1).strip() if meta_match else ''
        author_name = meta_match.group(2).strip() if meta_match and meta_match.group(2) else ''
        author_role = meta_match.group(3).strip() if meta_match and meta_match.group(3) else ''

        # 提取标签
        tag_match = re.search(r'🏷️\s*(.+?)(?:\n|$)', block)
        tags = []
        if tag_match:
            tags = [t.strip() for t in tag_match.group(1).split(',')]

        # 提取互动数据
        cc_match = re.search(r'💬\s*(\d+)', block)
        zn_match = re.search(r'👍\s*(\d+)', block)
        sn_match = re.search(r'🔄\s*(\d+)', block)
        comment_cnt = int(cc_match.group(1)) if cc_match else 0
        like_cnt = int(zn_match.group(1)) if zn_match else 0
        share_cnt = int(sn_match.group(1)) if sn_match else 0

        # 提取正文内容（> 开头的引用块）
        content_lines = []
        in_content = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('> '):
                in_content = True
                content_lines.append(stripped[2:])  # 去掉 "> "
            elif stripped.startswith('>'):
                content_lines.append(stripped[1:])
            elif in_content and stripped == '':
                # 内容块内的空行保留
                content_lines.append('')
            elif in_content and not stripped.startswith('*'):
                # 内容结束
                pass
            else:
                in_content = False

        content = '\n'.join(content_lines).strip()
        # 去掉末尾的 "*内容较长，已截取*" 标注
        content = re.sub(r'\n>\s*\*内容较长，已截取\*\s*$', '', content)

        # 从内容中提取真正的标题（#刘润日课 格式）
        extracted_title = title
        if extracted_title.startswith('动态 #'):
            # 尝试从内容中提取标题
            first_line = content.split('\n')[0] if content else ''
            m = re.match(r'#刘润日课\s+\d{4}年\d{1,2}月\d{1,2}日\s+(.*?)(?:\s{2,}|$)', first_line)
            if m:
                extracted_title = m.group(1).strip()
            elif first_line:
                # 取前20个字作为标题
                extracted_title = first_line[:30].strip()

        # 提取摘要（前150字）
        summary = ''
        if content:
            clean_content = re.sub(r'\s+', ' ', content).strip()
            summary = clean_content[:150]

        # 生成 post_id（使用发布时间+标题hash）
        post_id = f"riko_{published_at.replace(' ','_').replace(':','')}"

        posts.append({
            'post_id': post_id,
            'title': extracted_title,
            'content': content,
            'summary': summary,
            'author_name': author_name or '刘润',
            'author_role': author_role or '圈主',
            'tags': json.dumps(tags, ensure_ascii=False),
            'is_picked': 1,  # 全部为精选
            'comment_cnt': comment_cnt,
            'like_cnt': like_cnt,
            'share_cnt': share_cnt,
            'published_at': published_at,
        })

    return posts


def import_riko(source_id: str = 'xiaoe_liurun'):
    """导入刘润日课数据"""
    md_path = os.path.join(
        SYSTEM_DIR, '..', '..',
        'WorkBuddy', '2026-05-22-06-37-12',
        '刘润进化岛_刘润日课合集.md'
    )
    # 尝试绝对路径
    alt_path = r'C:\Users\Administrator\WorkBuddy\2026-05-22-06-37-12\刘润进化岛_刘润日课合集.md'
    if os.path.exists(alt_path):
        md_path = alt_path

    if not os.path.exists(md_path):
        print(f"❌ 未找到日课文件: {md_path}")
        return 0

    print(f"📖 解析文件: {md_path}")
    posts = parse_riko_report(md_path)
    print(f"📊 解析到 {len(posts)} 条帖子")

    # 注册数据源
    add_source(
        source_id=source_id,
        name='刘润进化岛',
        platform='xiaoe',
        expert_name='刘润',
        description='刘润老师的商业付费社群 — 刘润日课合集'
    )

    # 写入数据库
    imported = 0
    for p in posts:
        result = add_post(source_id, **p)
        if result is not None:
            imported += 1

    # 重建 FTS 索引
    rebuild_fts()

    print(f"✅ 导入完成: {imported}/{len(posts)} 条新帖子入库")
    return imported


def import_runyu(source_id: str = 'xiaoe_runyu'):
    """导入润宇创业笔记数据（预留）"""
    md_path = r'C:\Users\Administrator\WorkBuddy\2026-05-22-06-37-12\润宇创业笔记_动态汇总.md'
    if not os.path.exists(md_path):
        print(f"❌ 未找到文件: {md_path}")
        return 0

    # TODO: 实现润宇笔记的解析
    print("⏳ 润宇创业笔记导入等待实现")
    return 0


def main():
    print("=" * 50)
    print("🧠 专家认知蒸馏系统 · 数据导入管道")
    print("=" * 50)

    # 初始化数据库
    init_db()

    total = 0
    total += import_riko()

    # 显示当前数据库状态
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    sources = list_sources()
    print(f"\n📊 数据库状态:")
    print(f"   数据源: {len(sources)} 个")
    for s in sources:
        cnt = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=?", (s['id'],)).fetchone()[0]
        print(f"   - {s['name']} ({s['expert_name']}): {cnt} 条")
    print(f"   总计: {count} 条帖子")
    conn.close()


if __name__ == '__main__':
    main()

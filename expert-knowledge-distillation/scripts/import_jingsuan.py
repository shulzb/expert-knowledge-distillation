#!/usr/bin/env python3
"""
distill-system: import_jingsuan.py
从 wechat-article-exporter 拉取的 JSON 数据导入精算视觉公众号文章
"""
import sys, os, json, datetime
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn, rebuild_fts, add_source

SOURCE_ID = 'weixin_jingsuan'

def parse_jingsuan_json():
    """解析已下载的 JSON 文件，返回帖子列表"""
    base_dir = r'C:\Users\Administrator\WorkBuddy\2026-05-28-21-19-05'
    posts = []
    
    for page in range(1, 6):
        filepath = os.path.join(base_dir, f'jingsuan_page{page}.json')
        if not os.path.exists(filepath):
            print(f"  [WARN] 文件不存在: {filepath}")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        print(f"  [第{page}页]: {len(articles)} 篇文章")
        
        for a in articles:
            # 确保 post_id 唯一
            aid = a.get('aid', '')
            ts = a.get('create_time', 0)
            dt = datetime.datetime.fromtimestamp(ts) if ts else None
            
            post_id = f"jingsuan_{aid}" if aid else f"jingsuan_{ts}"
            
            # 格式化发布时间
            published_at = dt.strftime('%Y-%m-%d %H:%M:%S') if dt else ''
            
            # 正文暂用摘要填充，后续可通过下载接口获取完整内容
            content = a.get('digest', '')
            
            posts.append({
                'post_id': post_id,
                'title': a.get('title', '无标题')[:200],
                'content': content,
                'summary': content[:200],
                'url': a.get('link', ''),
                'author_name': a.get('author_name', '精算视觉'),
                'author_role': '公众号主理人',
                'tags': json.dumps(['精算视觉', '保险', '精算'], ensure_ascii=False),
                'is_picked': 0,
                'comment_cnt': 0,
                'like_cnt': 0,
                'share_cnt': 0,
                'published_at': published_at,
            })
    
    return posts


def import_jingsuan():
    print("=" * 60)
    print("[精算视觉] 公众号文章导入管道")
    print("=" * 60)
    
    print("\n解析已下载的 JSON 文件...")
    posts = parse_jingsuan_json()
    print(f"解析到 {len(posts)} 篇文章")
    
    with_content = sum(1 for p in posts if p['content'])
    print(f"  有摘要内容: {with_content} 篇")
    print(f"  仅标题(无摘要): {len(posts) - with_content} 篇")
    
    # 注册数据源
    add_source(
        source_id=SOURCE_ID,
        name='精算视觉公众号',
        platform='weixin',
        expert_name='精算视觉（Alex）',
        description='精算视角看保险，公众号精算视觉的全部历史文章'
    )
    
    conn = get_conn()
    
    # 获取已存在的 post_ids
    existing = set(r['post_id'] for r in 
        conn.execute("SELECT post_id FROM posts WHERE source_id=?", (SOURCE_ID,)).fetchall())
    conn.close()
    
    # 写入数据库
    imported = 0
    skipped = 0
    
    for p in posts:
        if p['post_id'] in existing:
            skipped += 1
            continue
        
        conn = get_conn()
        try:
            conn.execute(
                """INSERT OR IGNORE INTO posts 
                   (source_id, post_id, title, content, summary,
                    url, author_name, author_role, tags, is_picked,
                    comment_cnt, like_cnt, share_cnt, published_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    SOURCE_ID, p['post_id'], p['title'], p['content'], p['summary'],
                    p['url'], p['author_name'], p['author_role'], p['tags'], p['is_picked'],
                    p['comment_cnt'], p['like_cnt'], p['share_cnt'], p['published_at']
                )
            )
            conn.commit()
            imported += 1
        except Exception as e:
            print(f"  [ERROR] 导入失败 {p['post_id']}: {e}")
        finally:
            conn.close()
    
    # 重建 FTS
    rebuild_fts()
    
    print("\n导入结果:")
    print(f"  [OK] 新入库: {imported} 篇")
    print(f"  [SKIP] 已存在跳过: {skipped} 篇")
    
    # 最终统计
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=?", (SOURCE_ID,)).fetchone()[0]
    print(f"  [DONE] 精算视觉总计入库: {total} 篇")
    
    total_all = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    print(f"  [ALL] 数据库总计: {total_all} 条帖子")
    conn.close()
    
    return imported


if __name__ == '__main__':
    import_jingsuan()

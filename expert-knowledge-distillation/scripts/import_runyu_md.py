#!/usr/bin/env python3
"""
distill-system: import_runyu_md.py
从桌面 Markdown 解析并导入润宇创业笔记数据
"""
import sys, os, re, json
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn, rebuild_fts, add_source

MD_PATH = r'C:\Users\Administrator\Desktop\润宇创业笔记_150条完整汇总.md'
SOURCE_ID = 'xiaoe_runyu'

def parse_runyu_md(md_path: str) -> list:
    """
    解析润宇 Markdown 文件，返回帖子列表
    """
    with open(md_path, encoding='utf-8') as f:
        text = f.read()
    
    # 按 "### N. " 分割（支持多位数序号）
    sections = re.split(r'\n### (\d+)\.\s+', text)
    
    posts = []
    # sections 格式: [前文, 序号1, 内容1, 序号2, 内容2, ...]
    i = 1
    while i < len(sections) - 1:
        seq = sections[i].strip()
        block = sections[i + 1]
        i += 2
        
        lines = block.strip().split('\n')
        if not lines:
            continue
        
        # 第一行是标题
        title = lines[0].strip()
        # 去掉可能的 "（⭐ 精选）" 标记
        title = re.sub(r'[（(]?\s*⭐\s*精选\s*[）)]?', '', title).strip()
        
        # 提取时间
        time_match = re.search(r'🕐\s*([\d\-]+\s+[\d:]+)', block)
        published_at = time_match.group(1).strip() if time_match else ''
        
        # 提取互动数据
        comment_match = re.search(r'💬\s*(\d+)', block)
        like_match = re.search(r'👍\s*(\d+)', block)
        share_match = re.search(r'🔄\s*(\d+)', block)
        comment_cnt = int(comment_match.group(1)) if comment_match else 0
        like_cnt = int(like_match.group(1)) if like_match else 0
        share_cnt = int(share_match.group(1)) if share_match else 0
        
        # 提取正文（> 开头的行）
        content_lines = []
        for line in lines:
            stripped = line.strip()
            # 处理 > 开头的引用行
            m = re.match(r'^>\s*(.*)', stripped)
            if m:
                content_lines.append(m.group(1))
        
        # 清理内容
        content = '\n'.join(content_lines).strip()
        # 清理多余的 *** 等标记
        content = re.sub(r'^\*+', '', content).strip()
        
        # 生成 post_id
        post_id = f"runyu_{seq}"
        if published_at:
            clean_time = published_at.replace(' ', '_').replace(':', '')
            post_id = f"runyu_{clean_time}"
        
        posts.append({
            'post_id': post_id,
            'title': title[:200] if title else f'动态 #{seq}',
            'content': content,
            'summary': content[:150] if content else '',
            'author_name': '润宇',
            'author_role': '圈主',
            'tags': json.dumps(['润宇创业笔记'], ensure_ascii=False),
            'is_picked': 1,
            'comment_cnt': comment_cnt,
            'like_cnt': like_cnt,
            'share_cnt': share_cnt,
            'published_at': published_at,
        })
    
    return posts


def import_runyu():
    print("=" * 60)
    print("📝 润宇创业笔记导入管道")
    print("=" * 60)
    
    print(f"\n📖 解析文件: {MD_PATH}")
    posts = parse_runyu_md(MD_PATH)
    print(f"📊 解析到 {len(posts)} 条帖子")
    
    # 统计有内容的
    with_content = sum(1 for p in posts if p['content'])
    print(f"   有正文内容: {with_content} 条")
    print(f"   仅标题(无正文): {len(posts) - with_content} 条")
    
    # 注册数据源
    add_source(
        source_id=SOURCE_ID,
        name='润宇创业笔记',
        platform='xiaoe',
        expert_name='润宇',
        description='润宇老师的创业笔记圈子'
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
                    author_name, author_role, tags, is_picked,
                    comment_cnt, like_cnt, share_cnt, published_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    SOURCE_ID, p['post_id'], p['title'], p['content'], p['summary'],
                    p['author_name'], p['author_role'], p['tags'], p['is_picked'],
                    p['comment_cnt'], p['like_cnt'], p['share_cnt'], p['published_at']
                )
            )
            conn.commit()
            imported += 1
        except Exception as e:
            print(f"  ❌ 导入失败 {p['post_id']}: {e}")
        finally:
            conn.close()
    
    # 重建 FTS
    rebuild_fts()
    
    print(f"\n📊 导入结果:")
    print(f"  ✅ 新入库: {imported} 条")
    print(f"  ⏭️ 已存在跳过: {skipped} 条")
    
    # 最终统计
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=?", (SOURCE_ID,)).fetchone()[0]
    print(f"  📦 总计入库: {total} 条")
    
    total_all = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    print(f"  📚 数据库总计: {total_all} 条帖子")
    conn.close()
    
    return imported


if __name__ == '__main__':
    import_runyu()

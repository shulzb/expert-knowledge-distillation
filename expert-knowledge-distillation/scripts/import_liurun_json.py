#!/usr/bin/env python3
"""
distill-system: import_liurun_json.py
从 liurun_riko_full.json 全量导入刘润数据到数据库
"""
import sys, os, json, re
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn, rebuild_fts

JSON_PATH = r'C:\Users\Administrator\.workbuddy\distill-system\data\raw\liurun_riko_full.json'
DB_PATH = r'C:\Users\Administrator\.workbuddy\distill-system\data\distill.db'
SOURCE_ID = 'xiaoe_liurun'

def extract_text(item):
    """从 JSON item 中提取纯文本正文"""
    content = item.get('content', {}) or {}
    text = content.get('text', '') or ''
    
    # 如果有音频记录，也提取
    audio_texts = []
    for audio in content.get('audio_records', []) or []:
        if isinstance(audio, dict) and audio.get('text'):
            audio_texts.append(audio['text'])
    
    # 合并文本
    all_text = text
    if audio_texts:
        all_text = all_text + '\n' + '\n'.join(audio_texts)
    
    return all_text.strip()


def import_liurun_json():
    """全量导入刘润 JSON 数据"""
    print("=" * 60)
    print("🧠 刘润全量导入管道")
    print("=" * 60)
    
    # 加载 JSON
    print(f"\n📖 加载 JSON: {JSON_PATH}")
    with open(JSON_PATH, encoding='utf-8') as f:
        data = json.load(f)
    print(f"  共 {len(data)} 条记录")
    
    conn = get_conn()
    
    # 获取已存在的 post_ids
    existing = set(r['post_id'] for r in 
        conn.execute("SELECT post_id FROM posts WHERE source_id=?", (SOURCE_ID,)).fetchall())
    print(f"  数据库中已有 {len(existing)} 条刘润帖子")
    
    # 确保数据源存在
    from db.database import add_source
    add_source(
        source_id='xiaoe_liurun',
        name='刘润进化岛',
        platform='xiaoe',
        expert_name='刘润',
        description='刘润老师的商业付费社群 — 刘润日课'
    )
    
    # 逐个导入
    imported = 0
    skipped = 0
    empty = 0
    
    for item in data:
        post_id = item.get('id', '')
        if not post_id:
            continue
        
        if post_id in existing:
            skipped += 1
            continue
        
        # 提取内容
        text = extract_text(item)
        if not text:
            empty += 1
            # 空内容也标记，但使用占位符
            title = item.get('title', '') or ''
            if not title:
                title = f"动态 #{item.get('record_num', '')}"
        
        title = item.get('title', '') or ''
        if not title:
            # 从内容第一行提取标题
            first_line = text.split('\n')[0] if text else ''
            title = first_line[:80] if first_line else f"动态 #{item.get('record_num', '')}"
        
        created_at = item.get('created_at', '') or ''
        # 从 created_at 提取时间 (格式: 1748056800 或 "2026-05-24 13:00:00")
        published_at = ''
        if created_at:
            if created_at.isdigit():
                import datetime
                try:
                    dt = datetime.datetime.fromtimestamp(int(created_at))
                    published_at = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    published_at = created_at
            else:
                published_at = created_at
        
        # 重新获取连接（每个帖子新连接避免锁定）
        conn2 = get_conn()
        try:
            conn2.execute(
                """INSERT OR IGNORE INTO posts 
                   (source_id, post_id, title, content, raw_content, 
                    author_name, author_role, tags, is_picked,
                    comment_cnt, like_cnt, share_cnt, published_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    SOURCE_ID, post_id, title[:200], text[:50000], json.dumps(item, ensure_ascii=False),
                    item.get('nick_name', '刘润'), item.get('role_name', '圈主'),
                    json.dumps(['刘润日课'], ensure_ascii=False),
                    1 if item.get('is_chosen') == 1 else 0,
                    item.get('comment_count', 0) or 0,
                    item.get('zan_num', 0) or 0,
                    item.get('share_num', 0) or 0,
                    published_at
                )
            )
            conn2.commit()
            imported += 1
        except Exception as e:
            print(f"  ❌ 导入失败 {post_id}: {e}")
        finally:
            conn2.close()
        
        if imported % 50 == 0 and imported > 0:
            print(f"  已导入 {imported} 条...")
    
    # 重建 FTS
    rebuild_fts()
    
    print(f"\n📊 导入结果:")
    print(f"  ✅ 新入库: {imported} 条")
    print(f"  ⏭️ 已存在跳过: {skipped} 条")
    print(f"  ⚠️ 空内容: {empty} 条")
    
    # 最终统计
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=?", (SOURCE_ID,)).fetchone()[0]
    print(f"  📦 总计入库: {total} 条")
    conn.close()
    
    return imported


if __name__ == '__main__':
    import_liurun_json()

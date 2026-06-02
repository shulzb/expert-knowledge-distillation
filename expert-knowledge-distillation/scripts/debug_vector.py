#!/usr/bin/env python3
"""检查刘润蒸馏相关帖子及其向量搜索表现"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn
from query.vector_store import _init_embedding_model, _get_embedding, _get_chroma

conn = get_conn()

# 查找刘润的日课中包含"蒸馏"的
print("=" * 60)
print("刘润日课中包含「蒸馏」的帖子:")
print("=" * 60)
rows = conn.execute(
    "SELECT id, title, content, published_at FROM posts "
    "WHERE source_id='xiaoe_liurun' AND content LIKE '%蒸馏%'"
).fetchall()
print(f"共 {len(rows)} 条")
for r in rows:
    print(f"\nPost#{r['id']}: {r['title']} ({r['published_at']})")
    text_sample = r['content'][:200]
    print(f"  内容开头: {text_sample}...")

# 看这些帖子是否有被向量化
print("\n" + "=" * 60)
print("检查 ChromaDB 中刘润蒸馏帖子的向量:")
print("=" * 60)
try:
    client = _get_chroma()
    col = client.get_collection('posts')
    count = col.count()
    print(f"ChromaDB 'posts' 集合: {count} 条")
    
    # 查看刘润5月20日帖子的向量
    post_ids_str = [f"post_{r['id']}" for r in rows[:5]]
    if post_ids_str:
        results = col.get(ids=post_ids_str)
        print(f"请求 {len(post_ids_str)} 个向量，实际获取 {len(results['ids'])} 个")
        for i, pid in enumerate(results['ids']):
            meta = results['metadatas'][i]
            print(f"  {pid}: source={meta.get('source_id','?')} tags={meta.get('tags','')}")
except Exception as e:
    print(f"错误: {e}")

# 看润宇的"万物皆可蒸馏"帖子的向量
print("\n" + "=" * 60)
print("润宇「万物皆可蒸馏」帖子显示:")
print("=" * 60)
runyu_rows = conn.execute(
    "SELECT id, title, content[:200] FROM posts "
    "WHERE source_id='xiaoe_runyu' AND title LIKE '%蒸馏%'"
).fetchall()
for r in runyu_rows:
    print(f"Post#{r['id']}: {r['title']}")
    print(f"  内容: {r['content'][:150]}...")

conn.close()

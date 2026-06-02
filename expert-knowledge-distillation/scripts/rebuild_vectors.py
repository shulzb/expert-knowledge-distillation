#!/usr/bin/env python3
"""重新生成所有向量嵌入（修复维度问题）"""
import sys, os
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn
from query.vector_store import _init_embedding_model, _get_embedding, _get_collection

# 初始化模型
print('初始化嵌入模型...')
model_ok = _init_embedding_model()
print(f'模型状态: {"✅ 可用" if model_ok else "⚠️ 无模型"}')

conn = get_conn()
rows = conn.execute(
    "SELECT id, title, content, published_at, source_id, tags FROM posts"
).fetchall()
conn.close()

print(f'共 {len(rows)} 条帖子')

col = _get_collection('posts')

imported = 0
for row in rows:
    post_id = row['id']
    text = f"{row['title']} {row['content']}"[:5000]  # 限制长度
    if not text.strip():
        continue
    metadata = {
        'post_id': post_id,
        'source_id': row['source_id'],
        'published_at': (row['published_at'] or '')[:10],
        'tags': row['tags'] or '',
    }
    try:
        embedding = _get_embedding(text)
        col.add(
            embeddings=[embedding],
            ids=[f'post_{post_id}'],
            metadatas=[metadata]
        )
        imported += 1
    except Exception as e:
        print(f'  ❌ post#{post_id} 失败: {e}')

count = col.count()
print(f'\n✅ 完成: {imported} 条, ChromaDB中共 {count} 条')

#!/usr/bin/env python3
"""重新生成所有向量嵌入（带进度输出）"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn
from query.vector_store import _init_embedding_model, _get_embedding, _get_collection

# 清空旧集合
print('清空旧向量数据...')
try:
    from query.vector_store import clear_all
    clear_all()
except:
    print('  清空失败，继续...')

# 初始化模型
print('初始化嵌入模型...')
model_ok = _init_embedding_model()
print(f'模型状态: {"✅ 可用" if model_ok else "⚠️ 无模型"}')

conn = get_conn()
rows = conn.execute(
    "SELECT id, title, content, published_at, source_id, tags FROM posts ORDER BY id"
).fetchall()
conn.close()

total = len(rows)
print(f'共 {total} 条帖子')

col = _get_collection('posts')

imported = 0
errors = 0
start_time = time.time()

for idx, row in enumerate(rows, 1):
    post_id = row['id']
    text = f"{row['title']} {row['content']}"[:5000]
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
        errors += 1
        print(f'  ❌ post#{post_id} ({row["title"][:30]}): {e}')
    
    # 每 50 条报告一次进度
    if idx % 50 == 0:
        elapsed = time.time() - start_time
        rate = idx / elapsed if elapsed > 0 else 0
        eta = (total - idx) / rate if rate > 0 else 0
        print(f'  📊 [{idx}/{total}] 已导入 {imported} 条 | 速度 {rate:.1f}条/秒 | 预计剩余 {eta:.0f}秒')

# 增加一个大的进度报告
elapsed = time.time() - start_time
print(f'\n⏱️ 总耗时: {elapsed:.0f} 秒')
print(f'  速度: {total/elapsed:.1f} 条/秒' if elapsed > 0 else '')

count = col.count()
print(f'\n✅ 完成: {imported} 条成功, {errors} 条失败')
print(f'   ChromaDB中共 {count} 条')

#!/usr/bin/env python3
"""
embed_knowledge_units.py
将知识单元（knowledge_units）批量嵌入 ChromaDB knowledge 集合

用法:
  python scripts/embed_knowledge_units.py
  python scripts/embed_knowledge_units.py --rebuild    # 重建（清空旧数据）
"""
import sys, os, time, argparse

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)
sys.stdout.reconfigure(encoding='utf-8')

from db.database import get_conn
from query.vector_store import _init_embedding_model, _get_collection, _get_chroma
import chromadb.utils.embedding_functions as ef


BATCH_SIZE = 100  # 每批 100 条


def embed_knowledge(rebuild: bool = False):
    """批量嵌入知识单元到 ChromaDB knowledge 集合（批量处理）"""

    # 初始化嵌入模型
    model = ef.DefaultEmbeddingFunction()

    if rebuild:
        print('清空旧的 knowledge 集合...')
        try:
            client = _get_chroma()
            client.delete_collection('knowledge')
        except Exception:
            pass
        print('旧数据已清空\n')

    col = _get_collection('knowledge')

    # 读数据
    conn = get_conn()
    rows = conn.execute(
        """SELECT ku.id, ku.content, ku.unit_type, ku.title, ku.keywords, ku.post_id,
                  p.source_id, p.published_at
           FROM knowledge_units ku
           LEFT JOIN posts p ON p.id = ku.post_id
           WHERE ku.content != '' AND ku.content IS NOT NULL
           ORDER BY ku.id"""
    ).fetchall()
    conn.close()

    total = len(rows)
    print(f'共 {total} 条知识单元待嵌入\n')

    imported = 0
    errors = 0
    start_time = time.time()

    # 分批处理
    for batch_start in range(0, total, BATCH_SIZE):
        batch = rows[batch_start:batch_start + BATCH_SIZE]
        batch_texts = []
        batch_ids = []
        batch_metadatas = []

        for row in batch:
            uid = row['id']
            text = row['content'][:3000]
            if not text.strip():
                continue

            batch_texts.append(text)
            batch_ids.append(f'ku_{uid}')
            batch_metadatas.append({
                'unit_id': uid,
                'unit_type': row['unit_type'],
                'post_id': row['post_id'],
                'source_id': row['source_id'] or '',
                'published_at': (row['published_at'] or '')[:10],
                'title': (row['title'] or '')[:200],
                'keywords': (row['keywords'] or '')[:200],
            })

        if not batch_texts:
            continue

        try:
            # 批量生成嵌入
            embeddings = model(batch_texts)
            # 批量写入 ChromaDB
            col.add(
                embeddings=embeddings,
                ids=batch_ids,
                metadatas=batch_metadatas
            )
            imported += len(batch_texts)
        except Exception as e:
            errors += len(batch_texts)
            print(f'  批次错误 (id={batch_ids[0]}~{batch_ids[-1]}): {e}')

        # 进度报告
        processed = batch_start + len(batch)
        if processed % 500 == 0 or processed == total:
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed) / rate if rate > 0 else 0
            print(f'  [{processed}/{total}] 已导入 {imported} 条 | 速度 {rate:.1f}条/秒 | 预计剩余 {eta:.0f}秒')

    elapsed = time.time() - start_time
    count = col.count()

    print(f'\n=== 完成 ===')
    print(f'  成功: {imported} 条')
    print(f'  失败: {errors} 条')
    print(f'  耗时: {elapsed:.0f} 秒')
    print(f'  ChromaDB knowledge 集合: {count} 条')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='知识单元向量嵌入')
    parser.add_argument('--rebuild', action='store_true', help='重建集合（清空旧数据）')
    args = parser.parse_args()
    embed_knowledge(rebuild=args.rebuild)

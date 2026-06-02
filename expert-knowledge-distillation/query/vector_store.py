#!/usr/bin/env python3
"""
distill-system: vector_store.py
ChromaDB 向量存储封装 — 语义搜索
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json
from typing import List, Dict, Optional

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(SYSTEM_DIR, 'data', 'chroma_db')

# 延迟导入（chromadb 较大）
_chroma = None
_collections = {}


def _get_chroma():
    global _chroma
    if _chroma is None:
        import chromadb
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    return _chroma


def _get_collection(name: str):
    if name not in _collections:
        client = _get_chroma()
        try:
            _collections[name] = client.get_collection(name)
        except Exception:
            _collections[name] = client.create_collection(name)
    return _collections[name]


def add_post_embedding(post_id: int, text: str, metadata: dict):
    """为单篇帖子生成向量并存储"""
    col = _get_collection('posts')
    try:
        embedding = _get_embedding(text)
        col.add(
            embeddings=[embedding],
            ids=[f'post_{post_id}'],
            metadatas=[metadata]
        )
    except Exception as e:
        print(f'  ⚠️ 向量生成失败 post#{post_id}: {e}')


def add_knowledge_embedding(unit_id: int, text: str, metadata: dict):
    """为知识单元生成向量并存储"""
    col = _get_collection('knowledge')
    try:
        embedding = _get_embedding(text)
        col.add(
            embeddings=[embedding],
            ids=[f'ku_{unit_id}'],
            metadatas=[metadata]
        )
    except Exception as e:
        print(f'  ⚠️ 向量生成失败 ku#{unit_id}: {e}')


# 尝试初始化嵌入模型
_embedding_model = None

def _init_embedding_model():
    global _embedding_model
    if _embedding_model is not None:
        return True
    
    # 尝试1: ChromaDB 内置 ONNX 模型
    try:
        import chromadb.utils.embedding_functions as ef
        _embedding_model = ef.DefaultEmbeddingFunction()
        # 测试是否可用
        test = _embedding_model(['test'])
        if test and len(test[0]) > 0:
            print('  📦 使用 ChromaDB 内置嵌入模型')
            return True
    except Exception:
        pass
    
    # 尝试2: sentence-transformers（离线）
    try:
        import os
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print('  📦 使用 sentence-transformers all-MiniLM-L6-v2')
        return True
    except Exception:
        pass
    
    print('  ⚠️ 无可用嵌入模型，使用简化向量')
    _embedding_model = None
    return False


def _get_embedding(text: str) -> list:
    """生成文本的向量嵌入"""
    global _embedding_model
    
    if _embedding_model is None:
        _init_embedding_model()
    
    if _embedding_model is not None:
        try:
            if hasattr(_embedding_model, '__call__'):
                return _embedding_model([text])[0]
            return _embedding_model.encode(text).tolist()
        except Exception:
            pass
    
    # 回退：简化语义向量
    words = text.split()[:100]
    vec = [0.0] * 128
    for i, w in enumerate(words):
        h = hash(w) 
        vec[i % 128] += (h % 1000) / 1000.0
    # 归一化
    norm = sum(x*x for x in vec) ** 0.5
    if norm > 0:
        vec = [x/norm for x in vec]
    return vec


def semantic_search(query: str, collection: str = 'posts', top_k: int = 10) -> List[Dict]:
    """语义搜索"""
    col = _get_collection(collection)
    embedding = _get_embedding(query)
    results = col.query(
        query_embeddings=[embedding],
        n_results=top_k
    )
    items = []
    if results['ids'] and results['ids'][0]:
        for i in range(len(results['ids'][0])):
            items.append({
                'id': results['ids'][0][i],
                'distance': results['distances'][0][i] if results.get('distances') else 0,
                'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
            })
    return items


def semantic_search_all(query: str, posts_top_k: int = 5, knowledge_top_k: int = 10) -> dict:
    """
    同时搜索 posts 和 knowledge 两个集合
    返回: { 'posts': [...], 'knowledge': [...] }
    """
    embedding = _get_embedding(query)
    results = {'posts': [], 'knowledge': []}

    # 搜索 posts
    try:
        col = _get_collection('posts')
        res = col.query(query_embeddings=[embedding], n_results=posts_top_k)
        if res['ids'] and res['ids'][0]:
            for i in range(len(res['ids'][0])):
                results['posts'].append({
                    'id': res['ids'][0][i],
                    'distance': res['distances'][0][i] if res.get('distances') else 0,
                    'metadata': res['metadatas'][0][i] if res.get('metadatas') else {},
                })
    except Exception:
        pass

    # 搜索 knowledge
    try:
        col = _get_collection('knowledge')
        res = col.query(query_embeddings=[embedding], n_results=knowledge_top_k)
        if res['ids'] and res['ids'][0]:
            for i in range(len(res['ids'][0])):
                results['knowledge'].append({
                    'id': res['ids'][0][i],
                    'distance': res['distances'][0][i] if res.get('distances') else 0,
                    'metadata': res['metadatas'][0][i] if res.get('metadatas') else {},
                })
    except Exception:
        pass

    return results


def collection_summary() -> dict:
    """返回所有 ChromaDB 集合的摘要信息"""
    client = _get_chroma()
    summary = {}
    for col in client.list_collections():
        summary[col.name] = col.count()
    return summary


def embed_all_posts():
    """为所有帖子批量生成向量"""
    import sys
    sys.path.insert(0, SYSTEM_DIR)
    from db.database import get_conn

    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, content, published_at, source_id, tags FROM posts"
    ).fetchall()
    conn.close()

    col = _get_collection('posts')

    for row in rows:
        post_id = row['id']
        text = f"{row['title']} {row['content']}"
        metadata = {
            'post_id': post_id,
            'source_id': row['source_id'],
            'published_at': row['published_at'][:10] if row['published_at'] else '',
            'tags': row['tags'],
        }
        add_post_embedding(post_id, text, metadata)

    count = col.count()
    print(f'✅ 已生成 {count} 个帖子向量嵌入')
    return count


def clear_all():
    """清空所有向量数据"""
    client = _get_chroma()
    for name in list(_collections.keys()):
        try:
            client.delete_collection(name)
        except Exception:
            pass
    _collections.clear()
    print('✅ 向量数据已清空')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='向量存储管理')
    parser.add_argument('--embed', action='store_true', help='为所有帖子生成向量')
    parser.add_argument('--clear', action='store_true', help='清空向量数据')
    parser.add_argument('--search', help='语义搜索测试 (posts)')
    parser.add_argument('--search-all', help='搜索所有集合 (posts + knowledge)')
    parser.add_argument('--summary', action='store_true', help='显示集合摘要')
    args = parser.parse_args()

    if args.embed:
        embed_all_posts()
    elif args.clear:
        clear_all()
    elif args.summary:
        s = collection_summary()
        print('ChromaDB 集合摘要:')
        for name, cnt in s.items():
            print(f'  {name}: {cnt} 条')
    elif args.search:
        results = semantic_search(args.search)
        print(f'搜索结果: {len(results)} 条')
        for r in results:
            print(f'  {r["id"]} (距离: {r["distance"]:.4f})')
            print(f'    元数据: {r["metadata"]}')
    elif args.search_all:
        results = semantic_search_all(args.search_all)
        print(f'Posts 结果: {len(results["posts"])} 条')
        for r in results['posts']:
            print(f'  {r["id"]} (距离: {r["distance"]:.4f})')
        print(f'Knowledge 结果: {len(results["knowledge"])} 条')
        for r in results['knowledge']:
            print(f'  {r["id"]} (距离: {r["distance"]:.4f})')
            print(f'    元数据: {r["metadata"]}')
    else:
        print('请指定操作: --embed / --clear / --search / --search-all / --summary')

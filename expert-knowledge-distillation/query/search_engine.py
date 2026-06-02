#!/usr/bin/env python3
"""
distill-system: search_engine.py
混合搜索引擎 — FTS5 全文搜索 + ChromaDB 语义搜索
"""

import sys, os, json
from typing import List, Dict, Optional

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)

from db.database import get_conn, fts_search


def hybrid_search(query: str, top_k: int = 10) -> List[Dict]:
    """
    混合搜索：FTS5 全文搜索 + ChromaDB 语义搜索
    返回合并去重后的结果
    """
    results = []

    # 1. 全文搜索
    fts_results = fts_search(query, limit=top_k)
    seen_ids = set()
    for r in fts_results:
        results.append({
            'id': r['id'],
            'title': r['title'],
            'content_preview': r['content'][:300] if r['content'] else '',
            'published_at': r['published_at'],
            'author_name': r['author_name'],
            'source_id': r['source_id'],
            'tags': r['tags'],
            'match_type': 'fts',
            'rank': len(results),
        })
        seen_ids.add(r['id'])

    # 2. 语义搜索（如果ChromaDB已初始化）
    try:
        from query.vector_store import semantic_search
        vec_results = semantic_search(query, top_k=top_k)
        if vec_results:
            conn = get_conn()
            for vr in vec_results:
                pid_str = vr['id'].replace('post_', '')
                try:
                    pid = int(pid_str)
                except ValueError:
                    continue
                if pid in seen_ids:
                    continue
                row = conn.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
                if row:
                    results.append({
                        'id': row['id'],
                        'title': row['title'],
                        'content_preview': row['content'][:300],
                        'published_at': row['published_at'],
                        'author_name': row['author_name'],
                        'source_id': row['source_id'],
                        'tags': row['tags'],
                        'match_type': 'semantic',
                        'distance': vr['distance'],
                        'rank': len(results),
                    })
                    seen_ids.add(pid)
            conn.close()
    except Exception:
        pass  # 语义搜索不可用时仅返回 FTS 结果

    return results


def search_posts(query: str, source_id: str = '', tag: str = '',
                 start_date: str = '', end_date: str = '',
                 limit: int = 20) -> List[Dict]:
    """
    高级搜索：支持按数据源、标签、时间范围筛选
    """
    conn = get_conn()
    conditions = []
    params = []

    if query:
        conditions.append("(content LIKE ? OR title LIKE ?)")
        params.extend([f'%{query}%', f'%{query}%'])
    if source_id:
        conditions.append("source_id = ?")
        params.append(source_id)
    if tag:
        conditions.append("tags LIKE ?")
        params.append(f'%{tag}%')
    if start_date:
        conditions.append("published_at >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("published_at <= ?")
        params.append(end_date)

    sql = "SELECT * FROM posts"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY published_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_concepts_by_expert(source_id: str) -> List[Dict]:
    """获取某专家的所有概念"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT DISTINCT c.* FROM concepts c
        JOIN concept_posts cp ON cp.concept_id = c.id
        JOIN posts p ON p.id = cp.post_id
        WHERE p.source_id = ?
        ORDER BY c.name
    """, (source_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_opinions_on_topic(topic: str, source_id: str = '') -> List[Dict]:
    """获取某话题的所有观点"""
    conn = get_conn()
    sql = """
        SELECT ku.*, p.title as post_title, p.published_at, p.author_name
        FROM knowledge_units ku
        JOIN posts p ON p.id = ku.post_id
        WHERE ku.unit_type = 'argument'
          AND (ku.content LIKE ? OR ku.title LIKE ?)
    """
    params = [f'%{topic}%', f'%{topic}%']
    if source_id:
        sql += " AND p.source_id = ?"
        params.append(source_id)
    sql += " ORDER BY p.published_at DESC LIMIT 30"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

#!/usr/bin/env python3
"""
distill-system - 数据库核心模块
SQLite 连接管理、建表、基础 CRUD
"""

import os, sqlite3, json
from datetime import datetime
from typing import Optional, List, Dict

# 系统根目录
SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(SYSTEM_DIR, 'data', 'distill.db')
SCHEMA_PATH = os.path.join(SYSTEM_DIR, 'schema.sql')


def get_conn() -> sqlite3.Connection:
    """获取数据库连接（自动创建 DB）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库（建表）"""
    conn = get_conn()
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        schema = f.read()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")


# ── 数据源 CRUD ──

def add_source(source_id: str, name: str, platform: str, expert_name: str,
               description: str = "", config_json: str = "{}") -> bool:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO sources (id, name, platform, expert_name, description, config_json) VALUES (?,?,?,?,?,?)",
            (source_id, name, platform, expert_name, description, config_json)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ add_source 失败: {e}")
        return False
    finally:
        conn.close()


def get_source(source_id: str) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_sources() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sources").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 帖子 CRUD ──

def add_post(source_id: str, post_id: str, content: str, *,
             title: str = "", raw_content: str = "", summary: str = "",
             url: str = "", author_name: str = "", author_role: str = "",
             tags: str = "[]", is_picked: int = 0,
             comment_cnt: int = 0, like_cnt: int = 0, share_cnt: int = 0,
             published_at: str = "") -> Optional[int]:
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT OR IGNORE INTO posts 
               (source_id, post_id, title, content, raw_content, summary, url,
                author_name, author_role, tags, is_picked,
                comment_cnt, like_cnt, share_cnt, published_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (source_id, post_id, title, content, raw_content, summary, url,
             author_name, author_role, tags, is_picked,
             comment_cnt, like_cnt, share_cnt, published_at)
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"❌ add_post 失败 ({source_id}/{post_id}): {e}")
        return None
    finally:
        conn.close()


def get_unprocessed_posts(source_id: str = "", limit: int = 20) -> List[Dict]:
    """获取未提取知识的帖子"""
    conn = get_conn()
    if source_id:
        rows = conn.execute(
            "SELECT * FROM posts WHERE source_id=? AND is_extracted=0 ORDER BY published_at DESC LIMIT ?",
            (source_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM posts WHERE is_extracted=0 ORDER BY published_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_post_extracted(post_db_id: int):
    """标记帖子已提取"""
    conn = get_conn()
    conn.execute("UPDATE posts SET is_extracted=1 WHERE id=?", (post_db_id,))
    conn.commit()
    conn.close()


# ── 知识单元 CRUD ──

def add_knowledge_unit(post_id: int, unit_type: str, content: str, *,
                       title: str = "", keywords: str = "[]", confidence: float = 0.8) -> Optional[int]:
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO knowledge_units (post_id, unit_type, title, content, keywords, confidence) VALUES (?,?,?,?,?,?)",
            (post_id, unit_type, title, content, keywords, confidence)
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"❌ add_knowledge_unit 失败: {e}")
        return None
    finally:
        conn.close()


def search_knowledge(keyword: str, limit: int = 20) -> List[Dict]:
    """搜索知识单元"""
    conn = get_conn()
    rows = conn.execute(
        """SELECT ku.*, p.title as post_title, p.source_id, p.published_at
           FROM knowledge_units ku
           JOIN posts p ON p.id = ku.post_id
           WHERE ku.content LIKE ? OR ku.title LIKE ?
           ORDER BY ku.confidence DESC LIMIT ?""",
        (f'%{keyword}%', f'%{keyword}%', limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── 全文搜索 ──

def rebuild_fts():
    """重建全文搜索索引"""
    conn = get_conn()
    conn.execute("INSERT INTO posts_fts(posts_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()
    print("✅ FTS 索引重建完成")


def fts_search(query: str, limit: int = 20) -> List[Dict]:
    """搜索帖子（支持多词组合查询）"""
    conn = get_conn()
    terms = query.strip().split()
    if not terms:
        conn.close()
        return []
    
    # 构建组合查询：匹配所有关键词
    conditions = []
    params = []
    for t in terms:
        conditions.append("(content LIKE ? OR title LIKE ?)")
        params.extend([f'%{t}%', f'%{t}%'])
    
    sql = f"SELECT * FROM posts WHERE {' AND '.join(conditions)} ORDER BY published_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == '__main__':
    init_db()
    print(f"已注册数据源: {len(list_sources())} 个")

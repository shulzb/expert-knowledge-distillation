#!/usr/bin/env python3
"""验证数据库状态"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn

conn = get_conn()

print('=== 数据概览 ===')
rows = conn.execute("SELECT source_id, COUNT(*) as cnt, MAX(published_at) as latest FROM posts GROUP BY source_id").fetchall()
for r in rows:
    print(f'  {r["source_id"]}: {r["cnt"]} 条, 最新: {r["latest"]}')

print('\n=== 前3条帖子标题 ===')
rows = conn.execute("SELECT title, published_at, comment_cnt, like_cnt FROM posts ORDER BY published_at DESC LIMIT 3").fetchall()
for r in rows:
    print(f'  [{r["published_at"]}] {r["comment_cnt"]}💬 {r["like_cnt"]}👍 | {r["title"][:40]}')

print('\n=== 内容完整性检查 ===')
rows = conn.execute("SELECT id, LENGTH(content) as clen, LENGTH(summary) as slen FROM posts ORDER BY clen DESC LIMIT 5").fetchall()
for r in rows:
    print(f'  post#{r["id"]}: 正文 {r["clen"]}字, 摘要 {r["slen"]}字')

# 搜索测试
print('\n=== 搜索测试: "AI" ===')
rows = conn.execute("SELECT title, published_at FROM posts WHERE title LIKE '%AI%' OR content LIKE '%AI%' LIMIT 5").fetchall()
for r in rows:
    print(f'  [{r["published_at"][:10]}] {r["title"][:40]}')

conn.close()

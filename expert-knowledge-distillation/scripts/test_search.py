#!/usr/bin/env python3
"""测试搜索"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import fts_search, get_conn

# 直接测试 LIKE
conn = get_conn()
r = conn.execute("SELECT COUNT(*) FROM posts WHERE content LIKE '%普通人%'").fetchone()
print(f'包含"普通人"的帖子: {r[0]}条')
r = conn.execute("SELECT id, title, published_at FROM posts WHERE content LIKE '%普通人%' LIMIT 3").fetchall()
for x in r:
    print(f'  [{x["published_at"][:10]}] {x["title"][:30]}')
conn.close()

# 测试搜索函数
print('\nft_search测试:')
r = fts_search('普通人', 3)
print(f'找到{len(r)}条')
for x in r:
    print(f'  [{x["published_at"][:10]}] {x["title"][:30]}')

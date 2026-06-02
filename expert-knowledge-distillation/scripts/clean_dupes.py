#!/usr/bin/env python3
"""清理重复数据，保留完整内容版本"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn, rebuild_fts

conn = get_conn()

# 找出重复的（同一source_id下published_at重复的 或 post_id格式不同的相同内容）
rows = conn.execute("""
    SELECT p1.id as old_id, p2.id as new_id,
           LENGTH(p1.content) as old_len, LENGTH(p2.content) as new_len,
           p1.title as old_title, p2.title as new_title
    FROM posts p1
    JOIN posts p2 ON p1.source_id = p2.source_id 
                  AND p1.published_at = p2.published_at
                  AND p1.id < p2.id
""").fetchall()

print(f'发现 {len(rows)} 对重复数据')
deleted = 0
for r in rows:
    conn.execute('DELETE FROM posts WHERE id=?', (r['old_id'],))
    deleted += 1
    print(f'  删除 old#{r["old_id"]} ({r["old_len"]}字), 保留 new#{r["new_id"]} ({r["new_len"]}字)')

conn.commit()

# 修复标题（去掉 "#刘润日课 2026年X月X日" 前缀）
conn.execute("""
    UPDATE posts 
    SET title = TRIM(SUBSTR(title, INSTR(title, '日 ') + 2))
    WHERE title LIKE '#刘润日课%' AND INSTR(title, '日 ') > 0
""")
fixed = conn.execute("SELECT changes()").fetchone()[0]
print(f'修复标题: {fixed} 条')

conn.commit()
rebuild_fts()

cnt = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
print(f'当前总帖子数: {cnt}')
max_len = conn.execute('SELECT MAX(LENGTH(content)) FROM posts').fetchone()[0]
print(f'最长正文: {max_len} 字')
avg_len = conn.execute('SELECT AVG(LENGTH(content)) FROM posts').fetchone()[0]
print(f'平均正文: {int(avg_len)} 字')

conn.close()

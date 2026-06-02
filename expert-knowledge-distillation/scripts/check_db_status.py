#!/usr/bin/env python3
"""检查蒸馏数据库当前状态"""
import sys, json
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn

conn = get_conn()

# 数据源统计
sources = conn.execute("SELECT * FROM sources").fetchall()
print("📚 数据源:")
for s in sources:
    s = dict(s)
    total = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=?", (s['id'],)).fetchone()[0]
    extracted = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=? AND is_extracted=1", (s['id'],)).fetchone()[0]
    print(f"  · {s['name']} ({s['expert_name']}): {total} 条帖子, 已提取 {extracted} 条")

# 刘润帖子示例（已有的）
print("\n📋 刘润已有帖子（最近5条）:")
rows = conn.execute("SELECT post_id, title, published_at FROM posts WHERE source_id='xiaoe_liurun' ORDER BY id DESC LIMIT 5").fetchall()
for r in rows:
    print(f"  {dict(r)}")

print(f"\n📋 刘润已有帖子总数: {conn.execute('SELECT COUNT(*) FROM posts WHERE source_id=\"xiaoe_liurun\"').fetchone()[0]}")

# 查看 JSON 中数据
print("\n📦 刘润 JSON 数据:")
data = json.load(open(r'C:\Users\Administrator\.workbuddy\distill-system\data\raw\liurun_riko_full.json', encoding='utf-8'))
print(f"  共 {len(data)} 条")

# 检查 JSON 中每条数据的 id 与已入库的对比
existing_ids = set(r['post_id'] for r in conn.execute("SELECT post_id FROM posts WHERE source_id='xiaoe_liurun'").fetchall())
json_ids = set(item['id'] for item in data)
# 检查标题是否包含 "刘润日课"
riko_items = [item for item in data if '刘润日课' in json.dumps(item['content'], ensure_ascii=False)]
non_riko_items = [item for item in data if item not in riko_items]
print(f"  含'刘润日课'的帖子: {len(riko_items)} 条")
print(f"  其他帖子: {len(non_riko_items)} 条")
print(f"  JSON IDs 数: {len(json_ids)}")
print(f"  已入库 post_ids 数: {len(existing_ids)}")
print(f"  交集: {len(existing_ids & json_ids)}")
print(f"  JSON 中未入库的: {len(json_ids - existing_ids)}")

conn.close()

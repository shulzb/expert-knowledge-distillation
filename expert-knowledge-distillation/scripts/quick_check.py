#!/usr/bin/env python3
"""快速检查提取进度"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn
conn = get_conn()
l = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id='xiaoe_liurun' AND is_extracted=1").fetchone()[0]
r = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id='xiaoe_runyu' AND is_extracted=1").fetchone()[0]
k = conn.execute("SELECT COUNT(*) FROM knowledge_units").fetchone()[0]
print(f"刘润: {l}/636  润宇: {r}/250  知识单元: {k}")
conn.close()

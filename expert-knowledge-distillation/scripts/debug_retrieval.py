#!/usr/bin/env python3
"""调试：ask 命令的检索流程"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import fts_search
from query.search_engine import hybrid_search

question = "刘润会怎么看待我蒸馏了他这件事情"
source_id = 'xiaoe_liurun'

print("=" * 60)
print("1. FTS 搜索结果（前10条）")
print("=" * 60)
fts_results = fts_search(question, limit=10)
print(f"共 {len(fts_results)} 条")
for r in fts_results:
    sid = r.get('source_id', '?')
    author = r.get('author_name', '?')
    title = r['title'][:40]
    print(f"  [{sid}] {author}: {title}")

# 按 source 过滤
filtered = [r for r in fts_results if r.get('source_id', '') == source_id]
print(f"\n过滤后（仅 {source_id}）: {len(filtered)} 条")
for r in filtered:
    author = r.get('author_name', '?')
    title = r['title'][:40]
    print(f"  {author}: {title}")

print("\n" + "=" * 60)
print("2. 混合搜索结果")
print("=" * 60)
try:
    semantic_results = hybrid_search(question, top_k=5)
    print(f"共 {len(semantic_results)} 条")
    for r in semantic_results:
        sid = r.get('source_id', '?')
        author = r.get('author_name', '?')
        title = r['title'][:40]
        print(f"  [{sid}] {author}: {title}")
    
    filtered_sem = [r for r in semantic_results if r.get('source_id', '') == source_id]
    print(f"\n过滤后（仅 {source_id}）: {len(filtered_sem)} 条")
    for r in filtered_sem:
        author = r.get('author_name', '?')
        title = r['title'][:40]
        print(f"  {author}: {title}")
except Exception as e:
    print(f"混合搜索失败: {e}")

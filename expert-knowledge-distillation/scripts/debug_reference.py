#!/usr/bin/env python3
"""调试：刘润知识单元中是否有"蒸馏/知识传播/二次分发"相关内容"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
from db.database import get_conn

conn = get_conn()

# 1. 刘润知识搜索：蒸馏/知识传播相关
print("=" * 60)
print("1️⃣  刘润知识单元：搜索'蒸馏/知识传播/二次分发'")
print("=" * 60)
keywords = ['蒸馏', '知识传播', '二次分发', '知识杠杆', '复制']
for kw in keywords:
    rows = conn.execute(
        "SELECT ku.id, ku.unit_type, p.title, p.published_at, ku.content "
        "FROM knowledge_units ku JOIN posts p ON p.id = ku.post_id "
        "WHERE p.source_id='xiaoe_liurun' AND ku.content LIKE ?",
        (f'%{kw}%',)
    ).fetchall()
    print(f"\n  搜索「{kw}」: 找到 {len(rows)} 条")
    for r in rows[:5]:
        print(f"    [{r['published_at']}] {r['title'][:30]} | {r['unit_type']} | {r['content'][:80]}...")

# 2. 检查润宇知识单元中类似的匹配
print("\n" + "=" * 60)
print("2️⃣  润宇知识单元：搜索相同关键词")
print("=" * 60)
for kw in keywords:
    rows = conn.execute(
        "SELECT ku.id, ku.unit_type, p.title, p.published_at, ku.content "
        "FROM knowledge_units ku JOIN posts p ON p.id = ku.post_id "
        "WHERE p.source_id='xiaoe_runyu' AND ku.content LIKE ?",
        (f'%{kw}%',)
    ).fetchall()
    print(f"\n  搜索「{kw}」: 找到 {len(rows)} 条")
    for r in rows[:5]:
        print(f"    [{r['published_at']}] {r['title'][:30]} | {r['unit_type']} | {r['content'][:80]}...")

# 3. 看看全量提取前后的提取质量差异
print("\n" + "=" * 60)
print("3️⃣  刘润日课4月12日、19日、20日的内容（用户说历史截图提到的）")
print("=" * 60)
dates = ['2026-04-12', '2026-04-13', '2026-04-19', '2026-04-20']
for d in dates:
    rows = conn.execute(
        "SELECT id, title, content, is_extracted FROM posts "
        "WHERE source_id='xiaoe_liurun' AND published_at LIKE ?",
        (f'{d}%',)
    ).fetchall()
    for r in rows:
        print(f"\n  Post#{r['id']}: {r['title']} (extracted={r['is_extracted']})")
        print(f"  正文前200字: {r['content'][:200]}...")
        # 查看知识单元
        kus = conn.execute(
            "SELECT unit_type, title, content FROM knowledge_units WHERE post_id=?",
            (r['id'],)
        ).fetchall()
        print(f"  知识单元: {len(kus)} 个")
        for ku in kus[:5]:
            print(f"    [{ku['unit_type']}] {ku['title'][:30]}: {ku['content'][:80]}...")

conn.close()

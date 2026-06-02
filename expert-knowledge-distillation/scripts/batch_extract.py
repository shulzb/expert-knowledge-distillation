#!/usr/bin/env python3
"""
distill-system: batch_extract.py
批量知识提取 — 持续运行直至所有未提取帖子处理完毕
支持多个数据源，自动跳过已提取的帖子
"""
import sys, os, json, time, re
sys.stdout.reconfigure(encoding='utf-8')

SYSTEM_DIR = r'C:\Users\Administrator\.workbuddy\distill-system'
sys.path.insert(0, SYSTEM_DIR)

from db.database import get_conn, add_knowledge_unit
from pipeline.extraction_pipeline import load_llm_config, extract_knowledge

BATCH_SIZE = 999       # 每次查询未提取帖子的数量
SLEEP_BETWEEN = 0.5    # API 调用间隔（秒），避免限流


def get_unprocessed_count(source_id: str = '') -> int:
    conn = get_conn()
    if source_id:
        cnt = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=? AND is_extracted=0", (source_id,)).fetchone()[0]
    else:
        cnt = conn.execute("SELECT COUNT(*) FROM posts WHERE is_extracted=0").fetchone()[0]
    conn.close()
    return cnt


def get_unprocessed_posts(source_id: str = '', limit: int = 999) -> list:
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
    conn = get_conn()
    conn.execute("UPDATE posts SET is_extracted=1 WHERE id=?", (post_db_id,))
    conn.commit()
    conn.close()


def process_source(source_id: str, source_name: str, config: dict):
    """处理单个数据源的全部未提取帖子"""
    remaining = get_unprocessed_count(source_id)
    print(f"\n📊 {source_name} ({source_id}) 待处理: {remaining} 条")
    
    if remaining == 0:
        print(f"✅ {source_name} 全部已提取，跳过")
        return 0
    
    processed = 0
    api_errors = 0
    
    while remaining > 0:
        posts = get_unprocessed_posts(source_id=source_id, limit=BATCH_SIZE)
        if not posts:
            break
        
        for i, post in enumerate(posts, 1):
            try:
                content = post.get('content', '')
                if not content or len(content) < 50:
                    mark_post_extracted(post['id'])
                    remaining -= 1
                    processed += 1
                    print(f"  [{processed}] Post#{post['id']}: ⏭️ 内容过短，跳过")
                    continue
                
                result = extract_knowledge(content, config)
                
                # 写入知识单元
                if result.get('summary'):
                    add_knowledge_unit(
                        post_id=post['id'], unit_type='summary',
                        title=f'{post["title"][:50]} - 摘要',
                        content=result['summary'], confidence=0.9
                    )
                
                if result.get('main_argument'):
                    add_knowledge_unit(
                        post_id=post['id'], unit_type='argument',
                        title=f'{post["title"][:50]} - 核心论点',
                        content=result['main_argument'], confidence=0.85
                    )
                
                for concept in result.get('concepts', []):
                    add_knowledge_unit(
                        post_id=post['id'], unit_type='concept',
                        title=concept.get('name', ''),
                        content=f"{concept.get('description', '')}",
                        keywords=json.dumps([concept.get('name', '')], ensure_ascii=False),
                        confidence=0.8
                    )
                
                logic = result.get('logic_chain', '')
                if logic:
                    add_knowledge_unit(
                        post_id=post['id'], unit_type='logic_chain',
                        title=f'{post["title"][:50]} - 逻辑链',
                        content=logic, confidence=0.75
                    )
                
                for jp in result.get('judgment_patterns', []):
                    content_str = f"{jp.get('condition', '')} → {jp.get('conclusion', '')} ({jp.get('reasoning', '')})"
                    add_knowledge_unit(
                        post_id=post['id'], unit_type='logic_chain',
                        title=f"判断模式: {jp.get('condition', '')[:40]}",
                        content=content_str, confidence=0.7
                    )
                
                mark_post_extracted(post['id'])
                remaining -= 1
                processed += 1
                concepts_count = len(result.get('concepts', []))
                patterns_count = len(result.get('judgment_patterns', []))
                print(f"  [{processed}] Post#{post['id']}: ✅ 摘要+{concepts_count}概念+{patterns_count}逻辑")
                
                if processed % 10 == 0:
                    still_left = get_unprocessed_count(source_id)
                    print(f"     📊 进度: {processed} 已处理, 剩余约 {still_left} 条")
                
            except Exception as e:
                api_errors += 1
                print(f"  ❌ Post#{post['id']}: API 失败: {e}，标记跳过")
                mark_post_extracted(post['id'])
                remaining -= 1
                processed += 1
            
            # API 限流睡眠
            time.sleep(SLEEP_BETWEEN)
        
        # 再次检查是否有新未处理的（避免循环空转）
        remaining = get_unprocessed_count(source_id)
        
        if remaining > 0:
            print(f"\n⏳ 仍有 {remaining} 条未处理，继续下一批...\n")
    
    print(f"\n✅ {source_name} 提取完成！共处理 {processed} 条，API 错误 {api_errors} 次")
    return processed


def main():
    print("=" * 60)
    print("🧠 知识蒸馏 · 批量提取管道")
    print("=" * 60)
    
    config = load_llm_config()
    has_api = bool(config.get('api_key', ''))
    if not has_api:
        print("⚠️ 未配置 API Key，无法提取！")
        return
    
    print(f"🤖 使用模型: {config.get('model', 'unknown')}")
    print(f"📍 API: {config.get('api_base', 'unknown')}")
    print()
    
    total_processed = 0
    
    # 1. 刘润
    liurun_processed = process_source('xiaoe_liurun', '刘润进化岛', config)
    total_processed += liurun_processed
    
    # 2. 润宇
    runyu_processed = process_source('xiaoe_runyu', '润宇创业笔记', config)
    total_processed += runyu_processed
    
    # 3. 精算视觉
    jingsuan_processed = process_source('weixin_jingsuan', '精算视觉公众号', config)
    total_processed += jingsuan_processed
    
    # 最终统计
    print("\n" + "=" * 60)
    print(f"📊 总处理: {total_processed} 条帖子")
    
    # 检查是否全部完成
    conn = get_conn()
    sources = conn.execute("SELECT id FROM sources").fetchall()
    all_done = True
    for s in sources:
        sid = s['id']
        total = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=?", (sid,)).fetchone()[0]
        extracted = conn.execute("SELECT COUNT(*) FROM posts WHERE source_id=? AND is_extracted=1", (sid,)).fetchone()[0]
        status = "✅" if total == extracted else "❌"
        print(f"  {status} {sid}: {extracted}/{total} 已提取")
        if total != extracted:
            all_done = False
    conn.close()
    
    if all_done:
        print("\n🎉 所有数据源全部提取完成！")
        print("   下一步建议运行: python scripts/rebuild_vectors.py")
    

if __name__ == '__main__':
    main()

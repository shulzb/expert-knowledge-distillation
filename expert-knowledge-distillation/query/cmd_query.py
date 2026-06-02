#!/usr/bin/env python3
"""
distill-system: cmd_query.py
命令行搜索与查询工具

用法:
  distill-cli search "关键词"          # 全文搜索
  distill-cli ask "自然语言问题"        # 语义搜索 + LLM回答
  distill-cli opinion "话题"           # 观点查询
  distill-cli list                     # 列出数据源
  distill-cli stats                    # 数据统计
"""

import sys, os, json, argparse
from datetime import datetime

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)

from db.database import get_conn, fts_search, list_sources
from query.search_engine import hybrid_search, search_posts
from pipeline.extraction_pipeline import call_llm, load_llm_config


def cmd_search(args):
    """搜索帖子"""
    query = ' '.join(args.query)
    limit = args.limit or 20

    if args.semantic:
        results = hybrid_search(query, top_k=limit)
    else:
        results = fts_search(query, limit=limit)

    if not results:
        print('😴 未找到匹配内容')
        return

    print(f'📚 找到 {len(results)} 条结果:\n')
    for i, r in enumerate(results, 1):
        title = r.get('title', '') or '(无标题)'
        pub = (r.get('published_at') or '')[:10]
        author = r.get('author_name', '')
        tag = r.get('match_type', 'fts') if args.semantic else 'fts'
        tag_label = '🔍' if tag == 'fts' else '🧠'
        
        print(f'{tag_label} [{pub}] {title}')
        if author:
            print(f'   作者: {author}')
        
        preview = r.get('content_preview', '') or (r.get('content', '') or '')[:200]
        if preview:
            print(f'   {preview[:200]}...')
        print()


def cmd_ask(args):
    """AI问答 - 基于知识库回答问题"""
    query = ' '.join(args.query)
    
    # 1. 搜索相关上下文
    print('🔎 搜索知识库...')
    fts_results = fts_search(query, limit=5)
    
    if not fts_results:
        print('😴 知识库中未找到相关内容')
        return

    # 2. 构建上下文
    context_parts = []
    for r in fts_results:
        title = r.get('title', '') or '(无标题)'
        content = (r.get('content', '') or '')[:800]
        pub = (r.get('published_at', '') or '')[:10]
        context_parts.append(f"[{pub}] {title}\n{content}")
    
    context = '\n\n---\n\n'.join(context_parts)
    
    # 3. 调用 LLM
    config = load_llm_config()
    system_prompt = """你是一位基于刘润进化岛知识库的AI助手。
根据检索到的刘润日课内容回答问题。
- 回答要贴合刘润的观点和表达风格
- 如果知识库中没有相关信息，请明确说明
- 可以引用具体日期和原文"""

    user_prompt = f"""基于以下刘润日课内容，回答问题：

{context}

问题：{query}

请用刘润的风格回答，简明扼要，最好引用到具体内容。"""

    print('🤖 生成回答...')
    answer = call_llm(system_prompt, user_prompt, config)
    
    print(f'\n{"="*50}')
    print(f'💡 回答:\n')
    print(answer)
    print(f'\n{"="*50}')
    
    # 显示引用来源
    print(f'\n📖 参考来源 ({len(fts_results)} 篇):')
    for r in fts_results[:3]:
        title = r.get('title', '') or '(无标题)'
        pub = (r.get('published_at', '') or '')[:10]
        print(f'  · [{pub}] {title}')
    if len(fts_results) > 3:
        print(f'  ... 及其他 {len(fts_results)-3} 篇')


def cmd_opinion(args):
    """观点查询"""
    topic = ' '.join(args.query)
    conn = get_conn()
    
    # 搜索相关帖子
    rows = conn.execute(
        """SELECT title, content, published_at, author_name, source_id, like_cnt, comment_cnt
           FROM posts 
           WHERE content LIKE ? OR title LIKE ?
           ORDER BY published_at DESC LIMIT 20""",
        (f'%{topic}%', f'%{topic}%')
    ).fetchall()
    conn.close()

    if not rows:
        print(f'😴 未找到关于 "{topic}" 的观点')
        return

    print(f'📚 找到 {len(rows)} 篇相关文章:\n')
    for r in rows:
        title = r['title'] or '(无标题)'
        pub = (r['published_at'] or '')[:16]
        author = r['author_name'] or ''
        likes = r['like_cnt'] or 0
        # 提取观点摘要（取包含关键词的句子）
        content = r['content'] or ''
        sentences = content.replace('。', '。\n').split('\n')
        relevant = [s.strip() for s in sentences if topic in s]
        excerpt = relevant[0][:200] if relevant else content[:200]

        print(f'━━━ [{pub}] {title} (👍{likes})')
        if author:
            print(f'   作者: {author}')
        print(f'   {excerpt}')
        print()


def cmd_stats(args):
    """显示数据统计"""
    conn = get_conn()
    
    print('📊 数据库统计\n')
    
    # 数据源统计
    sources = list_sources()
    print(f'数据源: {len(sources)} 个')
    for s in sources:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE source_id=?", (s['id'],)
        ).fetchone()[0]
        extracted = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE source_id=? AND is_extracted=1", (s['id'],)
        ).fetchone()[0]
        last = conn.execute(
            "SELECT MAX(published_at) FROM posts WHERE source_id=?", (s['id'],)
        ).fetchone()[0]
        print(f'  · {s["name"]} ({s["expert_name"]}):')
        print(f'    帖子: {cnt} 条 | 已提取: {extracted} 条')
        print(f'    最新: {last or "N/A"}')
        print()
    
    # 知识单元统计
    ku_count = conn.execute("SELECT COUNT(*) FROM knowledge_units").fetchone()[0]
    ku_types = conn.execute(
        "SELECT unit_type, COUNT(*) as cnt FROM knowledge_units GROUP BY unit_type ORDER BY cnt DESC"
    ).fetchall()
    print(f'知识单元: {ku_count} 个')
    for t in ku_types:
        print(f'  · {t["unit_type"]}: {t["cnt"]} 个')
    
    # 总字数
    total_chars = conn.execute("SELECT SUM(LENGTH(content)) FROM posts").fetchone()[0] or 0
    print(f'\n知识库总字数: {total_chars:,} 字')
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='🧠 专家认知蒸馏系统 - CLI 查询工具')
    parser.add_argument('command', nargs='?', default='stats',
                        choices=['search', 'ask', 'opinion', 'list', 'stats'],
                        help='命令')
    parser.add_argument('query', nargs='*', help='搜索词/问题')
    parser.add_argument('--limit', type=int, default=10, help='结果数量限制')
    parser.add_argument('--semantic', action='store_true', help='使用语义搜索')
    
    args = parser.parse_args()
    
    if args.command == 'search':
        cmd_search(args)
    elif args.command == 'ask':
        cmd_ask(args)
    elif args.command == 'opinion':
        cmd_opinion(args)
    elif args.command == 'list':
        sources = list_sources()
        print('📚 已注册数据源:\n')
        for s in sources:
            print(f'  · {s["name"]} ({s["expert_name"]}) — {s.get("description","")}')
    elif args.command == 'stats':
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

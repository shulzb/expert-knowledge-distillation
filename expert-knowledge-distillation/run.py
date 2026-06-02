#!/usr/bin/env python3
"""
distill-system: run.py
总入口脚本

用法:
  python run.py collect                    # 增量采集
  python run.py collect --full             # 全量采集
  python run.py ingest                     # 导入已有数据
  python run.py extract                    # 知识提取
  python run.py extract --dry-run          # 知识提取预览
  python run.py search "关键词"            # 搜索
  python run.py ask "问题"                 # AI问答
  python run.py opinion "话题"             # 观点查询
  python run.py stats                      # 统计
  python run.py chat                       # 交互对话
  python run.py set-key "API_KEY"          # 设置API Key
  python run.py embed                      # 生成向量
  python run.py embed-knowledge             # 生成知识单元向量
  python run.py embed-knowledge --rebuild   # 重建知识单元向量
"""

import sys, os

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SYSTEM_DIR)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == 'collect':
        from collectors.xiaoe_collector import run_collect, SOURCES
        full = '--full' in args
        source = None
        for a in args:
            if a.startswith('--source='):
                source = a.split('=', 1)[1]
        if not source:
            source = 'xiaoe_liurun'
        run_collect(source, SOURCES[source], incremental=not full)

    elif cmd == 'ingest':
        from pipeline.data_ingest import main as ingest_main
        ingest_main()

    elif cmd == 'extract':
        from pipeline.extraction_pipeline import process_all_posts, load_llm_config
        dry_run = '--dry-run' in args
        source = None
        for a in args:
            if a.startswith('--source='):
                source = a.split('=', 1)[1]
        config = load_llm_config()
        process_all_posts(source_id=source or '', config=config, dry_run=dry_run)

    elif cmd == 'search':
        from query.cmd_query import cmd_search
        class FakeArgs:
            query = args
            limit = 10
            semantic = '--semantic' in args
        cmd_search(FakeArgs())

    elif cmd == 'ask':
        from persona.persona_chat import single_answer
        question = ' '.join(args)
        single_answer(question)

    elif cmd == 'opinion':
        from query.cmd_query import cmd_opinion
        class FakeArgs:
            query = args
        cmd_opinion(FakeArgs())

    elif cmd == 'stats':
        from query.cmd_query import cmd_stats
        cmd_stats(None)

    elif cmd == 'chat':
        from persona.persona_chat import interactive_chat
        interactive_chat()

    elif cmd == 'set-key':
        from pipeline.extraction_pipeline import save_llm_config, load_llm_config
        key = args[0] if args else ''
        config = load_llm_config()
        save_llm_config(key, config.get('api_base', ''), config.get('model', 'gpt-4o-mini'))

    elif cmd == 'embed':
        from scripts.rebuild_vectors import main as embed_main
        embed_main()

    elif cmd == 'embed-knowledge':
        from scripts.embed_knowledge_units import embed_knowledge
        rebuild = '--rebuild' in args
        embed_knowledge(rebuild=rebuild)

    elif cmd == 'list':
        from db.database import list_sources
        sources = list_sources()
        print('📚 数据源列表:\n')
        for s in sources:
            print(f'  · {s["name"]} ({s["expert_name"]}) — {s.get("description","")}')

    else:
        print(f'未知命令: {cmd}')
        print(__doc__)


if __name__ == '__main__':
    main()

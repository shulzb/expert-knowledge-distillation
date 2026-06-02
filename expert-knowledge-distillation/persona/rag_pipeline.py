#!/usr/bin/env python3
"""
distill-system: rag_pipeline.py
RAG 检索增强生成管道
"""

import sys, os
from typing import List, Dict, Optional

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)

from db.database import get_conn, fts_search
from query.search_engine import hybrid_search
from pipeline.extraction_pipeline import call_llm, load_llm_config
from persona.prompt_builder import PersonaPromptBuilder


def rag_answer(question: str, expert_name: str = '刘润', 
               source_id: str = 'xiaoe_liurun',
               config: dict = None) -> Dict:
    """
    RAG 管道：检索 → 构建上下文 → 组装 Prompt → LLM 回答
    
    Returns:
        dict with keys: answer, sources, context_used
    """
    if config is None:
        config = load_llm_config()

    builder = PersonaPromptBuilder(expert_name, source_id)

    # Step 1: 检索帖子（FTS + 语义）
    fts_results = fts_search(question, limit=10)

    seen_ids = {r['id'] for r in fts_results}

    # Step 2: 语义搜索补充帖子
    try:
        semantic_results = hybrid_search(question, top_k=5)
        for r in semantic_results:
            if r['id'] not in seen_ids:
                fts_results.append(r)
                seen_ids.add(r['id'])
    except Exception:
        pass

    # Step 2.5: 按指定数据源过滤
    if source_id and fts_results:
        filtered = [r for r in fts_results if r.get('source_id', '') == source_id]
        if filtered:
            fts_results = filtered

    # Step 3: 检索知识单元（语义搜索）
    knowledge_units = []
    try:
        from query.vector_store import semantic_search_all, _get_chroma
        # 先检查 knowledge 集合是否存在
        client = _get_chroma()
        has_knowledge = any(c.name == 'knowledge' for c in client.list_collections())
        if has_knowledge:
            all_results = semantic_search_all(question, posts_top_k=3, knowledge_top_k=8)
            # 从知识单元中按数据源过滤
            for ku in all_results.get('knowledge', []):
                meta = ku.get('metadata', {})
                if source_id and meta.get('source_id', '') != source_id:
                    continue
                knowledge_units.append(ku)
    except Exception:
        pass

    # Step 4: 合并上下文
    has_context = bool(fts_results) or bool(knowledge_units)
    if not has_context:
        return {
            'answer': f'抱歉，我的知识库中暂无"{expert_name}"关于此问题的论述。',
            'sources': [],
            'context_used': False
        }

    # Step 5: 构建 System Prompt
    system_prompt = builder.build_system_prompt()

    # Step 6: 构建 User Prompt（含帖子 + 知识单元上下文）
    user_prompt = builder.build_rag_query(
        question, fts_results,
        knowledge_units=knowledge_units
    )

    # Step 7: 调用 LLM
    answer = call_llm(system_prompt, user_prompt, config)

    # Step 8: 格式化引用来源
    sources = []
    for r in fts_results[:5]:
        title = r.get('title', '') or '(无标题)'
        pub = (r.get('published_at', '') or '')[:10]
        author = r.get('author_name', '') or expert_name
        sources.append(f'[{pub}] {title} (作者: {author})')
    for ku in knowledge_units[:3]:
        meta = ku.get('metadata', {})
        utype = meta.get('unit_type', '知识')
        sources.append(f'[知识单元] {utype}: {meta.get("title", "") or meta.get("keywords", "")[:60]}')

    return {
        'answer': answer,
        'sources': sources,
        'context_used': True
    }

#!/usr/bin/env python3
"""
distill-system: extraction_pipeline.py
LLM 知识提取管道 — 概念提取、观点归纳、判断逻辑链

使用 OpenAI 兼容 API（可接入 GPT-4o, Claude, 智谱 GLM 等）
"""
import sys, os, json, re, time
sys.stdout.reconfigure(encoding='utf-8')
from typing import List, Dict, Optional

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)

from db.database import (
    get_conn, get_unprocessed_posts, mark_post_extracted,
    add_knowledge_unit
)

# ── 配置 ──
# 默认使用环境变量或配置文件中的 API 配置
CONFIG_PATH = os.path.join(SYSTEM_DIR, 'config', 'llm_config.json')


def load_llm_config() -> dict:
    """加载 LLM API 配置"""
    defaults = {
        'api_key': '',
        'api_base': 'https://api.openai.com/v1',
        'model': 'gpt-4o-mini',
        'max_tokens': 4096,
        'temperature': 0.3,
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding='utf-8') as f:
            config = json.load(f)
        defaults.update(config)
    return defaults


def save_llm_config(api_key: str, api_base: str = '', model: str = 'gpt-4o-mini'):
    """保存 LLM API 配置"""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    config = {
        'api_key': api_key,
        'api_base': api_base or 'https://api.openai.com/v1',
        'model': model,
    }
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f'✅ LLM 配置已保存: {CONFIG_PATH}')


def call_llm(system_prompt: str, user_prompt: str, config: dict = None) -> str:
    """
    调用 LLM API（OpenAI 兼容格式）
    支持: GPT-4o, Claude (via Anthropic API), 智谱 GLM 等
    """
    if config is None:
        config = load_llm_config()

    api_key = config.get('api_key', '')
    if not api_key:
        print('⚠️ 未配置 API Key，使用回退（提取摘要）')
        return _fallback_extract(user_prompt)

    api_base = config.get('api_base', 'https://api.openai.com/v1')
    model = config.get('model', 'gpt-4o-mini')

    try:
        import requests
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': config.get('temperature', 0.3),
            'max_tokens': config.get('max_tokens', 4096),
        }
        r = requests.post(
            f'{api_base.rstrip("/")}/chat/completions',
            headers=headers, json=payload, timeout=120
        )
        result = r.json()
        if 'choices' in result:
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f'⚠️ API 返回异常: {result.get("error", {}).get("message", str(result))}')
            return _fallback_extract(user_prompt)
    except Exception as e:
        print(f'⚠️ API 调用失败: {e}')
        return _fallback_extract(user_prompt)


def _fallback_extract(text: str) -> str:
    """无 API 时的回退提取：取前200字作为摘要"""
    import re
    clean = re.sub(r'\s+', ' ', text).strip()
    summary = clean[:200]
    return json.dumps({
        'summary': summary,
        'concepts': [{'name': '(待API提取)', 'category': '', 'description': ''}],
        'main_argument': summary[:100],
        'logic_chain': '',
    }, ensure_ascii=False)


# ── Prompt 模板 ──

SYSTEM_EXTRACT = """你是一位商业分析专家和认知科学研究者。
请从给定的文本中提取结构化知识。

严格按照 JSON 格式输出，不要添加任何额外说明。

输出格式：
{
  "summary": "100-150字的摘要",
  "concepts": [
    {
      "name": "概念名称",
      "category": "商业/AI/管理/心理学/个人成长/其他",
      "description": "简要定义",
      "related_concepts": ["关联概念"]
    }
  ],
  "main_argument": "核心论点，1-2句话",
  "logic_chain": "推理逻辑链，用 因为...所以... 或 如果...那么... 格式描述",
  "judgment_patterns": [
    {
      "condition": "当...时",
      "conclusion": "则...",
      "reasoning": "推理过程"
    }
  ]
}"""


def extract_knowledge(content: str, config: dict = None) -> dict:
    """提取单篇文章的知识"""
    user_prompt = f"请分析以下文本：\n\n{content[:6000]}"
    try:
        result_text = call_llm(SYSTEM_EXTRACT, user_prompt, config)
        # 尝试解析 JSON
        result = json.loads(result_text)
        return result
    except json.JSONDecodeError:
        # 如果 LLM 返回非 JSON，尝试从文本中提取 JSON
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # 完全失败时返回摘要
        clean = re.sub(r'\s+', ' ', content).strip()
        return {
            'summary': clean[:200],
            'concepts': [],
            'main_argument': clean[:150],
            'logic_chain': '',
            'judgment_patterns': [],
        }


def process_all_posts(source_id: str = '', config: dict = None, dry_run: bool = False):
    """
    批量处理所有未提取的帖子。
    
    Args:
        source_id: 指定数据源，空字符串则处理所有
        config: LLM 配置
        dry_run: 仅预览，不实际写入
    """
    if config is None:
        config = load_llm_config()

    has_api = bool(config.get('api_key', ''))
    if not has_api:
        print('⚠️ 未配置 API Key，使用回退提取（仅摘要，无结构化知识）')
        print(f'   请运行: python extraction_pipeline.py --set-key "你的API_KEY"\n')

    posts = get_unprocessed_posts(source_id=source_id, limit=999)
    print(f'📊 待处理帖子: {len(posts)} 条')

    for i, post in enumerate(posts, 1):
        print(f'\n[{i}/{len(posts)}] Post#{post["id"]}: {post["title"][:40]}...', end=' ')
        
        content = post.get('content', '')
        if not content or len(content) < 50:
            print('⏭️ 内容过短，跳过')
            mark_post_extracted(post['id'])
            continue

        result = extract_knowledge(content, config)

        if dry_run:
            print(f'📋 {result.get("summary", "")[:60]}...')
            concepts = result.get('concepts', [])
            print(f'   概念: {len(concepts)} 个')
            for c in concepts[:3]:
                print(f'     - {c.get("name","")}: {c.get("description","")[:40]}')
            patterns = result.get('judgment_patterns', [])
            print(f'   判断逻辑: {len(patterns)} 条')
            continue

        # 写入知识单元
        # 1. 摘要
        if result.get('summary'):
            add_knowledge_unit(
                post_id=post['id'],
                unit_type='summary',
                title=f'{post["title"][:50]} - 摘要',
                content=result['summary'],
                confidence=0.9
            )

        # 2. 核心论点
        if result.get('main_argument'):
            add_knowledge_unit(
                post_id=post['id'],
                unit_type='argument',
                title=f'{post["title"][:50]} - 核心论点',
                content=result['main_argument'],
                confidence=0.85
            )

        # 3. 概念
        for concept in result.get('concepts', []):
            add_knowledge_unit(
                post_id=post['id'],
                unit_type='concept',
                title=concept.get('name', ''),
                content=f"{concept.get('description', '')}",
                keywords=json.dumps([concept.get('name', '')], ensure_ascii=False),
                confidence=0.8
            )

        # 4. 判断逻辑链
        logic = result.get('logic_chain', '')
        if logic:
            add_knowledge_unit(
                post_id=post['id'],
                unit_type='logic_chain',
                title=f'{post["title"][:50]} - 逻辑链',
                content=logic,
                confidence=0.75
            )

        # 5. 判断模式
        for jp in result.get('judgment_patterns', []):
            content_str = f"{jp.get('condition', '')} → {jp.get('conclusion', '')} ({jp.get('reasoning', '')})"
            add_knowledge_unit(
                post_id=post['id'],
                unit_type='logic_chain',
                title=f"判断模式: {jp.get('condition', '')[:40]}",
                content=content_str,
                confidence=0.7
            )

        mark_post_extracted(post['id'])
        concepts_count = len(result.get('concepts', []))
        patterns_count = len(result.get('judgment_patterns', []))
        print(f'✅ 摘要+{concepts_count}概念+{patterns_count}逻辑')

        # 避免 API 限流
        if has_api:
            time.sleep(1)

    print(f'\n✅ 处理完成!')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='知识提取管道')
    parser.add_argument('--source', help='数据源ID（默认全部）')
    parser.add_argument('--dry-run', action='store_true', help='仅预览不写入')
    parser.add_argument('--set-key', help='设置 API Key')
    parser.add_argument('--set-base', help='设置 API Base URL')
    parser.add_argument('--set-model', help='设置模型名')
    args = parser.parse_args()

    if args.set_key:
        config = load_llm_config()
        save_llm_config(
            api_key=args.set_key,
            api_base=args.set_base or config.get('api_base', 'https://api.openai.com/v1'),
            model=args.set_model or config.get('model', 'gpt-4o-mini'),
        )
        return

    config = load_llm_config()
    process_all_posts(source_id=args.source or '', config=config, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

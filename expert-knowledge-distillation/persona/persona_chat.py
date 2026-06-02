#!/usr/bin/env python3
"""
distill-system: persona_chat.py
AI 人格化对话 — 实时交互
"""

import sys, os

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SYSTEM_DIR)

from persona.rag_pipeline import rag_answer
from pipeline.extraction_pipeline import load_llm_config


def interactive_chat():
    """交互式对话"""
    print('🧠 专家认知蒸馏系统 · AI人格化对话')
    print('=' * 50)
    
    config = load_llm_config()
    has_api = bool(config.get('api_key', ''))
    
    if not has_api:
        print('⚠️  未配置 LLM API Key')
        print('   回答将使用知识库检索 + 回退摘要')
        print('   配置方法: distill-cli --set-key "你的API_KEY"\n')
    
    print(f'当前专家: 刘润（基于刘润日课79条知识库）')
    print(f'输入问题，或输入 /quit 退出\n')
    
    while True:
        try:
            question = input('❓ > ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n再见！')
            break
        
        if not question:
            continue
        if question.lower() in ('/quit', '/exit', 'quit', 'exit'):
            print('再见！')
            break
        
        print('🤔 思考中...')
        result = rag_answer(question, config=config)
        
        print(f'\n💡 回答:\n')
        print(result['answer'])
        
        if result['sources']:
            print(f'\n📖 参考来源:')
            for s in result['sources'][:3]:
                print(f'  · {s}')
        
        print('─' * 50)


def single_answer(question: str, expert: str = '刘润', source: str = 'xiaoe_liurun'):
    """单次回答（非交互模式）"""
    config = load_llm_config()
    result = rag_answer(question, expert_name=expert, source_id=source, config=config)
    
    print(f'💡 回答:\n')
    print(result['answer'])
    
    if result['sources']:
        print(f'\n📖 参考来源:')
        for s in result['sources'][:3]:
            print(f'  · {s}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='AI人格化对话')
    parser.add_argument('--question', help='直接提问（非交互模式）')
    parser.add_argument('--expert', default='刘润', help='专家名称')
    parser.add_argument('--source', default='xiaoe_liurun', help='数据源ID')
    args = parser.parse_args()
    
    if args.question:
        single_answer(args.question, args.expert, args.source)
    else:
        interactive_chat()

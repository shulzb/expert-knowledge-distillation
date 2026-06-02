#!/usr/bin/env python3
"""配置 DeepSeek API 并测试"""
import sys, json, os

sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
config_path = r'C:\Users\Administrator\.workbuddy\distill-system\config\llm_config.json'

# ⚠️ 请从环境变量 DEEPSEEK_API_KEY 读取，或手动编辑 config/llm_config.json
api_key = os.environ.get('DEEPSEEK_API_KEY', '')
if not api_key:
    # 尝试从已有配置读取
    if os.path.exists(config_path):
        with open(config_path) as f:
            existing = json.load(f)
        api_key = existing.get('api_key', '')
if not api_key:
    print('⚠️ 未设置 DEEPSEEK_API_KEY 环境变量，请手动编辑 config/llm_config.json')
    print('   或运行: set DEEPSEEK_API_KEY=你的key')
    api_key = 'YOUR_API_KEY_HERE'

config = {
    'api_key': api_key,
    'api_base': 'https://api.deepseek.com',
    'model': 'deepseek-chat',
    'max_tokens': 4096,
    'temperature': 0.3,
}
os.makedirs(os.path.dirname(config_path), exist_ok=True)
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
print('DeepSeek 配置已保存')

# 测试调用
from pipeline.extraction_pipeline import call_llm
print('测试 API 连接...')
result = call_llm('你是一个助手', '请回复"API连接成功"这五个字', config)
print(f'API 响应: {result[:80]}')

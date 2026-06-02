#!/usr/bin/env python3
"""调试cookie加载路径"""
import os, sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')

# 模拟SYSTEM_DIR
SYSTEM_DIR = r'C:\Users\Administrator\.workbuddy\distill-system'

# 检查旧cookie路径
old_path1 = os.path.join(os.path.dirname(SYSTEM_DIR), 'quanzi-skill', 'config.json')
old_path2 = os.path.join(os.path.dirname(os.path.dirname(SYSTEM_DIR)), 'quanzi-skill', 'config.json')

print(f'SYSTEM_DIR: {SYSTEM_DIR}')
print(f'os.path.dirname(SYSTEM_DIR): {os.path.dirname(SYSTEM_DIR)}')
print(f'os.path.dirname(os.path.dirname(SYSTEM_DIR)): {os.path.dirname(os.path.dirname(SYSTEM_DIR))}')
print(f'')
print(f'旧路径1: {old_path1}')
print(f'  存在: {os.path.exists(old_path1)}')
print(f'旧路径2: {old_path2}')
print(f'  存在: {os.path.exists(old_path2)}')

# 直接测试旧的 scraper 配置
old_scraper_path = os.path.expanduser(r'~\.workbuddy\skills\quanzi-skill\config.json')
print(f'')
print(f'skills路径: {old_scraper_path}')
print(f'  存在: {os.path.exists(old_scraper_path)}')

# 尝试加载cookie
if os.path.exists(old_scraper_path):
    with open(old_scraper_path, 'r', encoding='utf-8') as f:
        import json
        config = json.load(f)
    cookie = config.get('cookie', '')
    print(f'  Cookie长度: {len(cookie)}')
    
    # 用直接请求测试
    import requests
    headers = {
        'accept': 'application/json, text/plain, */*',
        'agent-type': 'pc',
        'app_id': 'apphKIqvnYG9370',
        'cookie': cookie,
        'login_app_id': 'apphKIqvnYG9370',
        'referer': 'https://quanzi.xiaoe-tech.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    }
    api = 'https://quanzi.xiaoe-tech.com/xe.community.community_service/small_community/xe.community/get_feeds_list/1.1.0'
    params = {'app_id': 'apphKIqvnYG9370', 'community_id': 'c_6142e4a53faeb_xQC3MEX54398', 'feeds_list_type': '-2', 'order_filed': 'created_at', 'hide_exercise': '1', 'page': '1', 'page_size': '1'}
    try:
        r = requests.get(api, headers=headers, params=params, timeout=15)
        result = r.json()
        print(f'  API返回code: {result.get("code")}')
        print(f'  API返回msg: {result.get("msg", "")}')
        if result.get('code') == 0:
            print(f'  ✅ Cookie有效！')
        else:
            print(f'  ❌ Cookie无效 (code={result.get("code")})')
    except Exception as e:
        print(f'  ❌ 请求失败: {e}')

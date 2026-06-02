#!/usr/bin/env python3
"""检查cookie状态"""
import os, json

old_path = os.path.expanduser(r'~\.workbuddy\skills\quanzi-skill\config.json')
if os.path.exists(old_path):
    with open(old_path, encoding='utf-8') as f:
        c = json.load(f)
    cookie = c.get('cookie', '')
    print(f'旧cookie存在，长度: {len(cookie)}')
    print(f'更新于: {c.get("cookie_updated_at", "unknown")}')
    print(f'前100字符: {cookie[:100]}...')
else:
    print('旧config不存在')

new_dir = os.path.expanduser(r'~\.workbuddy\distill-system\config')
new_path = os.path.join(new_dir, 'xiaoe_cookie.json')
print(f'\n新cookie路径: {new_path}')
if os.path.exists(new_path):
    with open(new_path) as f:
        d = json.load(f)
    print(f'存在，更新于: {d.get("updated_at","unknown")}')
else:
    print('不存在')

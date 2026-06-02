#!/usr/bin/env python3
"""测试更远历史数据 + 修复润宇Cookie"""
import sys, os, json, requests

API_DOMAIN = 'https://quanzi.xiaoe-tech.com/xe.community.community_service/small_community'

# 尝试直接用小鹅通的scraper里的cookie
quanzi_config = os.path.expanduser(r'~\.workbuddy\skills\quanzi-skill\config.json')
with open(quanzi_config, encoding='utf-8') as f:
    config = json.load(f)
cookie = config['cookie']

# ========== 1. 刘润: 测试更远历史 ==========
print('=== 刘润进化岛: 探索更远历史 ===')
community_lr = {
    'id': 'c_6142e4a53faeb_xQC3MEX54398',
    'app_id': 'apphKIqvnYG9370',
}
headers = {
    'accept': 'application/json, text/plain, */*',
    'agent-type': 'pc',
    'app_id': community_lr['app_id'],
    'cookie': cookie,
    'login_app_id': community_lr['app_id'],
    'referer': 'https://quanzi.xiaoe-tech.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/132.0.0.0',
}
api = f'{API_DOMAIN}/xe.community/get_feeds_list/1.1.0'

# 拉更多页，看看能追溯到多久
for page in [25, 30, 35, 40, 50]:
    params = {
        'app_id': community_lr['app_id'],
        'community_id': community_lr['id'],
        'feeds_list_type': '-2',
        'order_filed': 'created_at',
        'hide_exercise': '1',
        'page': str(page),
        'page_size': '50',
    }
    try:
        r = requests.get(api, headers=headers, params=params, timeout=15)
        d = r.json()
        feeds = d.get('data', {}).get('list', [])
        if feeds:
            first_d = feeds[0].get('created_at', '')[:10]
            last_d = feeds[-1].get('created_at', '')[:10]
            riko = sum(1 for f in feeds if any(t.get('tag_name') == '刘润日课' for t in f.get('tags', [])))
            print(f'  page={page}: {len(feeds)}条, {first_d} ~ {last_d}, 日课={riko}条')
        else:
            print(f'  page={page}: 空了')
            break
    except Exception as e:
        print(f'  page={page}: {e}')
        break

# ========== 2. 润宇: 测试不同的 feeds_list_type ==========
print('\n=== 润宇创业笔记: 测试不同参数 ===')
community_ry = {
    'id': 'c_682ada7ab22a1_nTDX4Y5g3647',
    'app_id': 'appgup6vo5q4830',
}
headers_ry = {
    'accept': 'application/json, text/plain, */*',
    'agent-type': 'pc',
    'app_id': community_ry['app_id'],
    'cookie': cookie,  # 用同一个cookie
    'login_app_id': community_ry['app_id'],
    'referer': 'https://quanzi.xiaoe-tech.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/132.0.0.0',
}

# 尝试不同 feeds_list_type
for flt in ['-2', '0', '1', '2']:
    params = {
        'app_id': community_ry['app_id'],
        'community_id': community_ry['id'],
        'feeds_list_type': flt,
        'order_filed': 'created_at',
        'hide_exercise': '1',
        'page': '1',
        'page_size': '20',
    }
    try:
        r = requests.get(api, headers=headers_ry, params=params, timeout=15)
        d = r.json()
        feeds = d.get('data', {}).get('list', [])
        code = d.get('code')
        msg = d.get('msg', '')
        print(f'  feeds_list_type={flt}: code={code}, {len(feeds)}条, msg={msg}')
        if feeds:
            # 看标签
            tags = set()
            for f in feeds:
                for t in f.get('tags', []):
                    tags.add(t.get('tag_name', ''))
            print(f'    标签: {tags}')
    except Exception as e:
        print(f'  feeds_list_type={flt}: 错误 {e}')

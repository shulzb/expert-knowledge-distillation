#!/usr/bin/env python3
"""全量拉取刘润日课历史数据（约2年）"""
import sys, os, json, requests, time

SKILL_DIR = os.path.expanduser(r'~\.workbuddy\skills\quanzi-skill')
CONFIG_PATH = os.path.join(SKILL_DIR, 'config.json')
API_DOMAIN = 'https://quanzi.xiaoe-tech.com/xe.community.community_service/small_community'

with open(CONFIG_PATH, encoding='utf-8') as f:
    config = json.load(f)
cookie = config['cookie']

community = {
    'id': 'c_6142e4a53faeb_xQC3MEX54398',
    'app_id': 'apphKIqvnYG9370',
}
headers = {
    'accept': 'application/json, text/plain, */*',
    'agent-type': 'pc',
    'app_id': community['app_id'],
    'cookie': cookie,
    'login_app_id': community['app_id'],
    'referer': 'https://quanzi.xiaoe-tech.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/132.0.0.0',
}
api = f'{API_DOMAIN}/xe.community/get_feeds_list/1.1.0'

all_riko = []
last_date = ''

for page in range(1, 51):  # 50页，每页50条
    params = {
        'app_id': community['app_id'],
        'community_id': community['id'],
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
        if not feeds:
            print(f'page {page}: 空了，停止')
            break
        
        # 筛选刘润日课
        for f in feeds:
            tags = f.get('tags', [])
            if any(t.get('tag_name') == '刘润日课' for t in tags):
                all_riko.append(f)
        
        fd = feeds[0].get('created_at','')[:10]
        ld = feeds[-1].get('created_at','')[:10]
        last_date = ld
        print(f'page {page}/50: {len(feeds)}条, {fd} ~ {ld}, 累计日课: {len(all_riko)}条')
        
        if ld < '2024-01-01':
            print('已到2024年之前，停止')
            break
    except Exception as e:
        print(f'page {page}: 错误 {e}')
        break

print(f'\n✅ 共获取到 {len(all_riko)} 条刘润日课')
print(f'时间跨度: {all_riko[-1].get("created_at","")[:10]} ~ {all_riko[0].get("created_at","")[:10]}')

# 保存原始JSON用于后续入库
output_dir = os.path.expanduser(r'~\.workbuddy\distill-system\data\raw')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'liurun_riko_full.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(all_riko, f, ensure_ascii=False)
print(f'原始数据已保存: {output_path}')
print(f'文件大小: {os.path.getsize(output_path) / 1024:.0f} KB')

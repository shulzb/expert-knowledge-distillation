#!/usr/bin/env python3
"""探查润宇票圈总量 + 刘润进度"""
import sys, os, json, requests

cookie_path = os.path.expanduser(r'~\.workbuddy\distill-system\config\xiaoe_cookie.json')
with open(cookie_path, encoding='utf-8') as f:
    cookie_data = json.load(f)
cookie = cookie_data['cookie']

api = 'https://quanzi.xiaoe-tech.com/xe.community.community_service/small_community/xe.community/get_feeds_list/1.1.0'
headers = {
    'accept': 'application/json, text/plain, */*',
    'agent-type': 'pc',
    'app_id': 'appgup6vo5q4830',
    'cookie': cookie,
    'login_app_id': 'appgup6vo5q4830',
    'referer': 'https://quanzi.xiaoe-tech.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/132.0.0.0',
}

# 拉20页看看润宇票圈总量
total_piaoquan = 0
for page in range(1, 21):
    params = {
        'app_id': 'appgup6vo5q4830',
        'community_id': 'c_682ada7ab22a1_nTDX4Y5g3647',
        'feeds_list_type': '-2',
        'order_filed': 'created_at',
        'hide_exercise': '1',
        'page': str(page),
        'page_size': '50',
    }
    r = requests.get(api, headers=headers, params=params, timeout=15)
    d = r.json()
    feeds = d.get('data', {}).get('list', [])
    if not feeds:
        print(f'page {page}: 空了')
        break
    pq = [f for f in feeds if any(t.get('tag_name') == '润宇票圈' for t in f.get('tags', []))]
    total_piaoquan += len(pq)
    fd = feeds[0].get('created_at','')[:10]
    ld = feeds[-1].get('created_at','')[:10]
    print(f'page {page}: {len(feeds)}条 {fd}~{ld} | 润宇票圈={len(pq)}条 | 累计={total_piaoquan}条')

print(f'\n✅ 润宇票圈总计约: {total_piaoquan} 条')

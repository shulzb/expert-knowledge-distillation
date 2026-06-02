#!/usr/bin/env python3
"""测试小鹅通API可以获取多少条历史数据"""
import sys, os, json, requests

SKILL_DIR = os.path.expanduser(r'~\.workbuddy\skills\quanzi-skill')
CONFIG_PATH = os.path.join(SKILL_DIR, 'config.json')
API_DOMAIN = 'https://quanzi.xiaoe-tech.com/xe.community.community_service/small_community'

with open(CONFIG_PATH, encoding='utf-8') as f:
    config = json.load(f)

cookie = config['cookie']

# 刘润进化岛
community = {
    'name': '刘润进化岛',
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

# 测试不同页码，看API还有多少数据
print('=== 刘润进化岛: 测试API能拉多少页 ===')
for page_size in [50, 100]:
    for page in [1, 5, 10, 15, 20]:
        params = {
            'app_id': community['app_id'],
            'community_id': community['id'],
            'feeds_list_type': '-2',
            'order_filed': 'created_at',
            'hide_exercise': '1',
            'page': str(page),
            'page_size': str(page_size),
        }
        try:
            r = requests.get(api, headers=headers, params=params, timeout=15)
            d = r.json()
            feeds = d.get('data', {}).get('list', [])
            if feeds:
                first_date = feeds[0].get('created_at', '')[:10]
                last_date = feeds[-1].get('created_at', '')[:10]
                riko_count = sum(1 for f in feeds if any(t.get('tag_name') == '刘润日课' for t in f.get('tags', [])))
                print(f'  page={page}, page_size={page_size}: {len(feeds)}条, 首帖={first_date}, 末帖={last_date}, 日课={riko_count}')
            else:
                print(f'  page={page}, page_size={page_size}: 0条 (空了)')
                if page == 15:
                    break
        except Exception as e:
            print(f'  page={page}: 错误 {e}')

# 润宇创业笔记 - 测试润宇票圈标签
print('\n=== 润宇创业笔记: 先看有什么标签 ===')
community2 = {
    'name': '润宇创业笔记',
    'id': 'c_682ada7ab22a1_nTDX4Y5g3647',
    'app_id': 'appgup6vo5q4830',
}

headers2 = {
    'accept': 'application/json, text/plain, */*',
    'agent-type': 'pc',
    'app_id': community2['app_id'],
    'cookie': cookie,
    'login_app_id': community2['app_id'],
    'referer': 'https://quanzi.xiaoe-tech.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/132.0.0.0',
}

# 抓一页看看所有标签
params = {
    'app_id': community2['app_id'],
    'community_id': community2['id'],
    'feeds_list_type': '-2',
    'order_filed': 'created_at',
    'hide_exercise': '1',
    'page': '1',
    'page_size': '100',
}
r2 = requests.get(api, headers=headers2, params=params, timeout=15)
d2 = r2.json()
feeds2 = d2.get('data', {}).get('list', [])

all_tags = {}
for f in feeds2:
    for t in f.get('tags', []):
        tag_name = t.get('tag_name', '')
        if tag_name:
            all_tags[tag_name] = all_tags.get(tag_name, 0) + 1

print(f'第一页共 {len(feeds2)} 条帖子，标签分布:')
for tag, count in sorted(all_tags.items(), key=lambda x: -x[1]):
    print(f'  #{tag}: {count} 条')

# 专门检查润宇票圈
runyu_piaoquan = [f for f in feeds2 if any(t.get('tag_name') == '润宇票圈' for t in f.get('tags', []))]
print(f'\n第一页中"润宇票圈"标签帖子: {len(runyu_piaoquan)} 条')
if runyu_piaoquan:
    for f in runyu_piaoquan[:3]:
        print(f'  [{f.get("created_at","")[:16]}] {f.get("title","(无标题)")[:50]}')

#!/usr/bin/env python3
"""解析用户提供的cURL Cookie并保存"""
import os, json

# 从cURL中提取的cookie（用户提供的）
cookie = 'XIAOEID=de20226fd1f6744992f62b414b1d5355; view_url=http%3A%2F%2Fsem.xiaoe-tech.com%2F%3Fjzl_act%3D%257Buserid%257D%26jzl_adp%3D%257Bunitid%257D%26jzl_ch%3D11%26jzl_cpg%3D%257Bplanid%257D%26jzl_ctv%3D%257Bcreative%257D%26jzl_dv%3D1%26jzl_kwd%3D254394723259%26jzl_sty%3D%257Bpa_mt_id%257D; cookie_referer=https%3A%2F%2Fwww.baidu.com%2Fother.php%3Fsc.0f0000jDxyQlVZSeaQ8HBRrRAdqh3u-cgBCjqsGWzIcfhAuloOuq_C9Q86_3g4FxcKFfrqHRRO4ayJ89m850H_zTkDdo0VbKiZURZXRv86a4CztvFKoIorbsHGBdZYBYsT5u7tVsI-f9IIWDO6adfFyfblAQ8ec3QUVAoJtKcFSkw7kJrHCgNST2Xf8H2C7oJ-8Xx5COJW8qIj5pOAyrJckWkMC6.7b_NR2Ar5Od66WHGt89eQb4lampbfItEjw4XL68mzU81WEe5ZFkzUVOgQsYXyA9qjZOOdjn-h6OlDOOOxgQsYXyAGB8Eo-3p521jfmOOS_Dpu_gOOLdztPZ-9klh5OOoZwuBkxOOxgQsYXNheAkOOqmcMYngOOLdztPZ-WCpA5OOoA1zlpZQBOOSS8g9CtVLYnNoDk_vyUSrHIgzdS5QRze-kl-9h9molUrMk0.TLFWgv-b5Hczn1D0TLFWpyfqnWc1nfKk5Ia9V81PJ0KYUHLfCUU_1p60IgP-T-qYXgK-5H00mywxIZ-suHYv0ZIEThfqY2AvenvC0ZFWIWYs0ZNzU7qGujYkPH63PW6LnHTz0Addgv-b5HD3nWDYnHRY0AdxpyfqnHTsPH6dnWD0UgwsU7qGujYknWb3r0KsI-qGujYs0A-bm1dri6Kspyfqn6KWpyfqPj0s0ZPGujd9rHfYrAckmW0kmyNbuWm40AN3T7qYpyd-5HD3njmYnWcYnj00Tv7xuhk9u1Ys0APzm1YvnHfsn0%26ck%3D729.0.212.214.402.NaN.NaN.0%26dt%3D1779396312%26wd%3D%25E5%25B0%258F%25E9%25B9%2585%25E9%2580%259A%26tpl%3Dtpl_12988_39147_0%26l%3D1588687172%26ai%3D0_428435621_1_0%26us%3DlinkVersion%253D1%2526compPath%253D10048.0-10063.1-10065.1-10058.3%2526label%253D%2525E4%2525B8%2525BB%2525E6%25258C%252589%2525E9%252592%2525AE%2526linkType%253D%2526linkText%253D%2525E8%2525BF%25259B%2525E5%252585%2525A5%2525E5%2525AE%252598%2525E7%2525BD%252591; channel=11-254394723259; cookie_channel=11-254394723259; cookie_session_id=SdTr3lnI4pE59qswHBCYudt8SB8U3Nz9; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219e4c491709b8b-0923cb543e3fdf-26011b51-1881600-19e4c49170a3fb%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219e4c491709b8b-0923cb543e3fdf-26011b51-1881600-19e4c49170a3fb%22%7D; p_token=pceadminuniwebd87mtsdnqtlh73j2o7k0; app_id=appgup6vo5q4830; activity_id=appgup6vo5q4830-c_682ada7ab22a1_nTDX4Y5g3647; last_created_token_app_id=appgup6vo5q4830; pc_token_appgup6vo5q4830=5c1c1aa07f6dde60be38d2527edb7e39; user_id_appgup6vo5q4830=u_68922a0fc3cef_Gozb0h7aOv; union_id=oTHW5v7rg1WTdVtRcDYBl4dEazo8'

# 保存到两个地方
# 1. quanzi-skill 配置（兼容旧系统）
quanzi_config = os.path.expanduser(r'~\.workbuddy\skills\quanzi-skill\config.json')
with open(quanzi_config, encoding='utf-8') as f:
    old_config = json.load(f)
old_config['cookie'] = cookie
old_config['cookie_updated_at'] = '2026-05-24T13:23:00.000Z'
with open(quanzi_config, 'w', encoding='utf-8') as f:
    json.dump(old_config, f, ensure_ascii=False, indent=2)
print(f'已更新: {quanzi_config}')

# 2. distill-system 配置
distill_cookie = os.path.expanduser(r'~\.workbuddy\distill-system\config\xiaoe_cookie.json')
os.makedirs(os.path.dirname(distill_cookie), exist_ok=True)
with open(distill_cookie, 'w', encoding='utf-8') as f:
    json.dump({'cookie': cookie, 'updated_at': '2026-05-24T13:23:00.000Z'}, f, ensure_ascii=False, indent=2)
print(f'已保存: {distill_cookie}')

# 3. 测试润宇接口
import requests
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
params = {
    'app_id': 'appgup6vo5q4830',
    'community_id': 'c_682ada7ab22a1_nTDX4Y5g3647',
    'feeds_list_type': '-2',
    'order_filed': 'created_at',
    'hide_exercise': '1',
    'page': '1',
    'page_size': '20',
}
r = requests.get(api, headers=headers, params=params, timeout=15)
d = r.json()
code = d.get('code')
print(f'\n润宇API测试: code={code}')
if code == 0:
    feeds = d.get('data', {}).get('list', [])
    print(f'成功获取 {len(feeds)} 条帖子')
    
    # 检查标签
    all_tags = {}
    for f in feeds:
        for t in f.get('tags', []):
            tn = t.get('tag_name', '')
            if tn:
                all_tags[tn] = all_tags.get(tn, 0) + 1
    
    print(f'标签分布:')
    for tag, cnt in sorted(all_tags.items(), key=lambda x: -x[1]):
        print(f'  #{tag}: {cnt} 条')
    
    # 专门看润宇票圈
    piaoquan = [f for f in feeds if any(t.get('tag_name') == '润宇票圈' for t in f.get('tags', []))]
    print(f'\n"润宇票圈"标签帖子: {len(piaoquan)} 条')
else:
    print(f'失败: {d.get("msg","")}')

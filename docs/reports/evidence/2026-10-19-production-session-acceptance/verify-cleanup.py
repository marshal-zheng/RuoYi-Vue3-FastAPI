"""Read only checks for this run's exact fixtures; never prints credentials or session values."""
import asyncio
import base64
import json
import pathlib
import sys

EVIDENCE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE.parents[3] / 'ruoyi-fastapi-backend'))

from config.database import async_engine
from sqlalchemy import text
import redis


async def main():
    fixture = json.loads((EVIDENCE / 'fixtures.json').read_text())
    counts = {}
    queries = {
        'active_users': 'select count(*) from sys_user where user_id in (:a,:b) and del_flag=\'0\'',
        'user_roles': 'select count(*) from sys_user_role where user_id in (:a,:b)',
        'user_posts': 'select count(*) from sys_user_post where user_id in (:a,:b)',
        'active_roles': 'select count(*) from sys_role where role_id in (:r,:s) and del_flag=\'0\'',
        'role_menus': 'select count(*) from sys_role_menu where role_id in (:r,:s)',
        'role_depts': 'select count(*) from sys_role_dept where role_id in (:r,:s)',
        'menus': 'select count(*) from sys_menu where menu_name like :prefix',
        'device_categories': 'select count(*) from sys_device_category where device_category_id=:category',
        'accidental_devices': 'select count(*) from sys_device where device_name like :prefix',
    }
    params = {'a': fixture['userA'], 'b': fixture['userB'], 'r': fixture['role'],
              's': fixture['roleB'], 'prefix': fixture['tag']+'%', 'category': fixture['category']}
    async with async_engine.connect() as conn:
        for name, query in queries.items():
            counts[name] = (await conn.execute(text(query), params)).scalar_one()
    await async_engine.dispose()
    cache = redis.Redis(host='127.0.0.1', port=6379, db=2)
    own_sessions = 0
    for key in cache.scan_iter('sec:user_session:*'):
        raw = cache.get(key)
        if raw and str(json.loads(raw).get('userId')) in {str(fixture['userA']),str(fixture['userB'])}:
            own_sessions += 1
    counts['own_session_metadata'] = own_sessions
    own_access = 0
    for key in cache.scan_iter('access_token:*'):
        raw = cache.get(key)
        if not raw:
            continue
        try:
            payload = raw.decode().split('.')[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
        except (ValueError, IndexError):
            continue
        if str(claims.get('user_id')) in {str(fixture['userA']), str(fixture['userB'])}:
            own_access += 1
    counts['own_access_tokens'] = own_access
    counts['own_active_pointers'] = sum(cache.exists(f'sec:active_session:{uid}') for uid in (fixture['userA'],fixture['userB']))
    counts['own_csrf'] = sum(cache.exists(f'sec:csrf:{uid}') for uid in (fixture['userA'],fixture['userB']))
    result = {'counts': counts, 'all_zero': all(value == 0 for value in counts.values())}
    (EVIDENCE / 'cleanup-storage.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


asyncio.run(main())

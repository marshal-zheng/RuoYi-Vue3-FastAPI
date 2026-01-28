import asyncio
from sqlalchemy import text
from config.get_db import get_async_db_engine

async def check_menu():
    engine = get_async_db_engine()
    async with engine.begin() as conn:
        # 检查菜单 500 是否存在
        result = await conn.execute(text('SELECT menu_id, menu_name, path, component, parent_id FROM sys_menu WHERE menu_id IN (108, 500) ORDER BY menu_id'))
        rows = result.fetchall()
        print('菜单数据:')
        for row in rows:
            print(f'  menu_id={row[0]}, name={row[1]}, path={row[2]}, component={row[3]}, parent_id={row[4]}')
        
        # 检查 admin 用户的角色
        result = await conn.execute(text('SELECT r.role_id, r.role_name, r.role_key FROM sys_user u JOIN sys_user_role ur ON u.user_id = ur.user_id JOIN sys_role r ON ur.role_id = r.role_id WHERE u.user_name = "admin"'))
        rows = result.fetchall()
        print('\nadmin 用户的角色:')
        for row in rows:
            print(f'  role_id={row[0]}, name={row[1]}, key={row[2]}')

asyncio.run(check_menu())

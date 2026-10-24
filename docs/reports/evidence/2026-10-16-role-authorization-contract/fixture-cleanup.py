import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,'/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-backend');sys.argv=['cleanup','--env=dev']
from server import app
from config.database import AsyncSessionLocal
from sqlalchemy import text,bindparam
folder=Path('/tmp/ruoyi-role-authorization'); data=json.loads((folder/'owned.json').read_text()); owned=data['owned'];tag=data['tag']
async def main():
 async with AsyncSessionLocal() as db:
  for kind,key,table,name in [('user','userId','sys_user','user_name'),('role','roleId','sys_role','role_key'),('dept','deptId','sys_dept','dept_name')]:
   ids=[r[key] for r in owned[kind]]
   if not ids:continue
   column={'user':'user_id','role':'role_id','dept':'dept_id'}[kind]
   stmt=text(f'SELECT {name} FROM {table} WHERE {column} IN :ids').bindparams(bindparam('ids',expanding=True))
   names=(await db.execute(stmt,{'ids':ids})).scalars().all();assert all(n.startswith(tag) for n in names),(kind,names)
   relations={'user':['sys_user_role','sys_user_post'],'role':['sys_role_menu','sys_role_dept','sys_user_role'],'dept':['sys_role_dept']}[kind]
   for target in relations+[table]:
    await db.execute(text(f'DELETE FROM {target} WHERE {column} IN :ids').bindparams(bindparam('ids',expanding=True)),{'ids':ids})
  await db.commit()
  rows=(await db.execute(text('SELECT user_id,role_id FROM sys_user_role ORDER BY user_id,role_id'))).all()
  assert [list(r) for r in rows]==json.loads((folder/'initial-relations.json').read_text())
 print('Owned fixture rows removed; original user-role associations exact')
asyncio.run(main())

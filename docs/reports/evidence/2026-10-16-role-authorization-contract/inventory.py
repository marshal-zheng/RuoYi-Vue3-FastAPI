"""Compare pre-existing business identities and all permission associations, excluding owned fixtures."""
import asyncio,hashlib,json,sys
from pathlib import Path
mode=sys.argv[1]
sys.path.insert(0,'/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-backend');sys.argv=['inventory','--env=dev']
from server import app
from config.database import AsyncSessionLocal
from sqlalchemy import text
folder=Path('/tmp/ruoyi-role-authorization'); owned=json.loads((folder/'owned.json').read_text())['owned']
ids={'user_id':{x['userId'] for x in owned['user']},'role_id':{x['roleId'] for x in owned['role']},'dept_id':{x['deptId'] for x in owned['dept']}}
tables={'sys_user':['user_id','user_name','dept_id','status','del_flag'],'sys_role':['role_id','role_key','status','del_flag','data_scope'],'sys_dept':['dept_id','parent_id','ancestors','dept_name','status','del_flag'],'sys_user_role':['user_id','role_id'],'sys_user_post':['user_id','post_id'],'sys_role_menu':['role_id','menu_id'],'sys_role_dept':['role_id','dept_id']}
async def main():
 snapshot={}
 async with AsyncSessionLocal() as db:
  for table,cols in tables.items():
   rows=(await db.execute(text('SELECT '+','.join(cols)+' FROM '+table+' ORDER BY '+','.join(cols)))).mappings().all()
   snapshot[table]=[dict(row) for row in rows if not any(row.get(k) in v for k,v in ids.items())]
 path=folder/'original-business-inventory.json'
 if mode=='capture':path.write_text(json.dumps(snapshot,ensure_ascii=False,sort_keys=True))
 else:assert snapshot==json.loads(path.read_text()),'Original business data drift'
 result={'mode':mode,'ok':True,'tables':{k:{'rows':len(v),'sha256':hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()} for k,v in snapshot.items()}}
 (folder/f'inventory-{mode}.json').write_text(json.dumps(result,indent=2));print(mode,'business inventory OK')
asyncio.run(main())

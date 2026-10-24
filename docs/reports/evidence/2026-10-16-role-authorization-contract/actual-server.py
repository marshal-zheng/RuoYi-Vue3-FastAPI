"""Local authorization verification wrapper, isolated Redis and controlled transaction faults."""
import contextvars
import json
import os
from pathlib import Path
import secrets
import sys
sys.path.insert(0, '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-backend')
sys.argv = ['authorization-probe', '--env=dev']
os.environ.update(APP_RELOAD='false', REDIS_PORT='16379', DEV_MANAGED_DATA_HOT_RECONCILE_ENABLED='false')
from fastapi import Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from server import app
from config.database import AsyncSessionLocal
from modules.system.infrastructure.user_role_repository import UserRoleRepository
from module_admin.entity.do.user_do import UserRoleDO
import uvicorn
folder=Path('/tmp/ruoyi-role-authorization')
secret=secrets.token_urlsafe(32)
(folder/'config.json').write_text(json.dumps({'secret':secret}))
fault=contextvars.ContextVar('authorization_fault',default=None)
original_add=UserRoleRepository.add
original_commit=AsyncSession.commit
async def add(self, entity):
    state=fault.get()
    if state and state['mode']=='second-insert':
        state['adds']+=1
        if state['adds']==2: raise RuntimeError('Authorization verification: second insert failed')
    return await original_add(self,entity)
async def commit(self):
    state=fault.get()
    if state and state['mode']=='commit': raise RuntimeError('Authorization verification: commit failed')
    return await original_commit(self)
UserRoleRepository.add=add
AsyncSession.commit=commit
@app.middleware('http')
async def controlled_fault(request:Request,call_next):
    mode=request.headers.get('x-authorization-fault') if request.headers.get('x-probe-secret')==secret else None
    token=fault.set({'mode':mode,'adds':0} if mode else None)
    try: return await call_next(request)
    finally: fault.reset(token)
@app.get('/__authorization_probe',include_in_schema=False)
async def state(request:Request):
    if request.headers.get('x-probe-secret')!=secret: raise HTTPException(status_code=403)
    async with AsyncSessionLocal() as db:
        rows=(await db.execute(select(UserRoleDO.user_id,UserRoleDO.role_id).order_by(UserRoleDO.user_id,UserRoleDO.role_id))).all()
    return {'relations':[list(row) for row in rows]}
uvicorn.run(app,host='127.0.0.1',port=8088,access_log=False)

"""Opt-in real Redis + private SQLite verification of global maintenance routes."""

import json
import os

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from config import get_redis
from config.get_db import get_db
from container import build_container
from exceptions.handle import handle_exception
from module_admin.entity.do.audit_log_do import AuditLogDO
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.job_do import JobLogDO
from module_admin.entity.do.log_do import LogininforDO, OperLogDO
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.application.services.login_service import LoginService
from modules.identity.ports import get_current_user
from modules.scheduler.api.job_controller import jobController
from modules.system.api.audit_controller import auditController
from modules.system.api.cache_controller import cache_router
from modules.system.api.config_controller import configController
from modules.system.api.dict_controller import dictController
from modules.system.api.log_controller import logController


@pytest.fixture
async def isolated_api(test_engine, monkeypatch):
    url = os.environ.get('RUOYI_ACCEPTANCE_PRIVATE_REDIS_URL')
    if not url:
        pytest.skip('Requires a disposable Redis instance, never the shared development Redis')
    redis = Redis.from_url(url, decode_responses=True)
    assert redis.connection_pool.connection_kwargs['port'] != 6379
    await redis.flushdb()
    sessions = async_sessionmaker(test_engine, expire_on_commit=False)
    monkeypatch.setattr(get_redis, 'AsyncSessionLocal', sessions)

    async def db():
        async with sessions() as session:
            yield session
            await session.commit()

    user = CurrentUserModel(user={'userId': 1, 'userName': 'isolated-qa'}, permissions=['*:*:*'], roles=['admin'])
    app = FastAPI()
    handle_exception(app)
    app.state.container = build_container()
    app.state.redis = redis
    app.dependency_overrides[get_db] = db
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[LoginService.get_current_user] = lambda: user
    for router in [logController, auditController, jobController, configController, dictController, cache_router]:
        app.include_router(router)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://isolated') as client:
            yield client, sessions, redis
    finally:
        await redis.flushdb()
        await redis.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('path', 'model', 'row'),
    [
        ('operlog', OperLogDO, {'oper_id': 1, 'oper_name': 'isolated-qa'}),
        ('logininfor', LogininforDO, {'info_id': 1, 'user_name': 'isolated-qa'}),
        ('audit', AuditLogDO, {'audit_id': 1, 'table_name': 'isolated_fixture', 'action': 'UPDATE'}),
        (
            'jobLog',
            JobLogDO,
            {
                'job_log_id': 1,
                'job_name': 'isolated-qa',
                'job_group': 'DEFAULT',
                'job_executor': 'default',
                'invoke_target': 'module_task.scheduler_test.job',
            },
        ),
    ],
)
async def test_global_log_clean_is_persisted_in_private_database(isolated_api, path, model, row):
    client, sessions, _redis = isolated_api
    async with sessions.begin() as session:
        session.add(model(**row))
    response = await client.delete(f'/monitor/{path}/clean')
    assert response.status_code == 204, response.text
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['config', 'dict', 'all'])
async def test_cache_refresh_and_clear_all_use_real_private_storage(isolated_api, operation):
    client, sessions, redis = isolated_api
    async with sessions.begin() as session:
        session.add(
            ConfigDO(config_id=1, config_name='Owned', config_key='qa_private', config_value='stored', config_type='N')
        )
        session.add(DictTypeDO(dict_id=1, dict_name='Owned', dict_type='qa_private', status='0'))
        session.add(
            DictDataDO(dict_code=1, dict_type='qa_private', dict_label='Owned', dict_value='stored', status='0')
        )
    await redis.mset({'sys_config:stale': 'stale', 'sys_dict:stale': 'stale', 'other:sentinel': 'kept'})
    path = {
        'config': '/system/config/refreshCache',
        'dict': '/system/dict/type/refreshCache',
        'all': '/monitor/cache/clearCacheAll',
    }[operation]
    response = await client.delete(path)
    assert response.status_code == (204 if operation == 'all' else 200), response.text
    if operation in ('config', 'all'):
        assert await redis.get('sys_config:qa_private') == 'stored'
        assert await redis.get('sys_config:stale') is None
    if operation in ('dict', 'all'):
        values = json.loads(await redis.get('sys_dict:qa_private'))
        assert values[0]['dictValue'] == 'stored'
        assert await redis.get('sys_dict:stale') is None
    assert await redis.get('other:sentinel') == (None if operation == 'all' else 'kept')

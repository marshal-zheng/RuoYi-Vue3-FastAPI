from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.enums import BusinessType
from container import build_container
from exceptions.exception import AuthException
from module_admin.annotation import log_annotation
from module_admin.entity.do.log_do import LogininforDO


@pytest.mark.asyncio
async def test_failed_login_log_survives_the_request_rollback(tmp_path, monkeypatch):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path}/failed-login.db')
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(lambda sync: LogininforDO.__table__.create(sync))
    container = build_container()
    container._session_factory = sessions
    app = FastAPI()
    app.state.container = container
    monkeypatch.setattr(log_annotation, '_is_test_env', lambda: False)
    monkeypatch.setattr(log_annotation.AppConfig, 'app_ip_location_query', False)

    @log_annotation.Log(title='用户登录', business_type=BusinessType.OTHER, log_type='login')
    async def failed_login(request: Request, form_data, query_db: AsyncSession):
        await query_db.execute(select(LogininforDO))
        raise AuthException(user_message='密码错误')

    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    request = Request(
        {
            'type': 'http',
            'app': app,
            'method': 'POST',
            'scheme': 'http',
            'server': ('test', 80),
            'path': '/login',
            'query_string': b'',
            'headers': [(b'user-agent', b'QA'), (b'x-forwarded-for', b'127.0.0.1')],
        },
        receive,
    )
    try:
        async with sessions() as session:
            with pytest.raises(AuthException) as error:
                await failed_login(request=request, form_data=SimpleNamespace(username='owned-qa'), query_db=session)
            assert error.value.http_status == 401
            await session.rollback()
        async with sessions() as session:
            logs = (await session.scalars(select(LogininforDO))).all()
            assert len(logs) == 1
            assert (logs[0].user_name, logs[0].status, logs[0].msg) == ('owned-qa', '1', '密码错误')
    finally:
        await engine.dispose()

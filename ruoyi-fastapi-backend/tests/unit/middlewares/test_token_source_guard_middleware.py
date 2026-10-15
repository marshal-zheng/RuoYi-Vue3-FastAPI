import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from middlewares.token_source_guard_middleware import (
    TokenSourceGuardASGIMiddleware,
    add_token_source_guard_middleware,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    add_token_source_guard_middleware(app)

    @app.get('/api/secure')
    async def get_secure():
        return {'ok': True}

    @app.post('/api/secure')
    async def post_secure():
        return {'ok': True}

    return app


@pytest.mark.asyncio
async def test_reject_query_token_source():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/api/secure?token=abc')

    assert response.status_code == 400
    assert response.json().get('title') == '非法认证来源'


@pytest.mark.asyncio
async def test_reject_cookie_token_source():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/api/secure', headers={'Cookie': 'access_token=abc'})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_reject_form_token_source():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.post('/api/secure', data={'access_token': 'abc'})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_allow_bearer_header_source():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.get('/api/secure', headers={'Authorization': 'Bearer abc'})

    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize('body', [b'page=1&pageSize=10', b''])
async def test_form_replay_waits_for_real_disconnect(body):
    messages = asyncio.Queue()
    messages.put_nowait({'type': 'http.request', 'body': body, 'more_body': False})
    disconnect = {'type': 'http.disconnect'}

    async def endpoint(scope, receive, send):
        assert await Request(scope, receive).body() == body
        pending = asyncio.create_task(receive())
        try:
            await asyncio.sleep(0)
            assert not pending.done(), 'Body replay must wait for the server after the final chunk'
            messages.put_nowait(disconnect)
            assert await asyncio.wait_for(pending, timeout=1) is disconnect
        finally:
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)

    middleware = TokenSourceGuardASGIMiddleware(endpoint, exclude_prefixes=[])
    scope = {
        'type': 'http',
        'method': 'POST',
        'path': '/api/secure',
        'headers': [(b'content-type', b'application/x-www-form-urlencoded')],
    }
    await asyncio.wait_for(middleware(scope, messages.get, AsyncMock()), timeout=1)

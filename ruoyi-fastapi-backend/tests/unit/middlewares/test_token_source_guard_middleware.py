import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from middlewares.token_source_guard_middleware import add_token_source_guard_middleware


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

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from config.env import JwtConfig
from middlewares.rate_limit_middleware import RateLimitASGIMiddleware


def _build_app(**middleware_overrides) -> FastAPI:
    app = FastAPI()
    middleware_config = {
        'enabled': True,
        'window_seconds': 60,
        'exclude_paths': ['/health'],
        'auth_paths': ['/login'],
        'write_methods': ['POST', 'PUT', 'PATCH', 'DELETE'],
        'auth_ip_limit': 2,
        'auth_user_limit': 5,
        'write_ip_limit': 10,
        'write_user_limit': 2,
        'read_ip_limit': 2,
        'read_user_limit': 4,
    }
    middleware_config.update(middleware_overrides)
    app.add_middleware(
        RateLimitASGIMiddleware,
        **middleware_config,
    )

    @app.post('/login')
    async def login_endpoint():
        return {'ok': True}

    @app.post('/api/write')
    async def write_endpoint(payload: dict):
        return {'ok': True, 'payload': payload}

    @app.get('/api/read')
    async def read_endpoint():
        return {'ok': True}

    return app


@pytest.mark.asyncio
async def test_auth_tier_ip_limit():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        resp1 = await client.post('/login')
        resp2 = await client.post('/login')
        resp3 = await client.post('/login')

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 429
    assert resp3.headers.get('retry-after') is not None
    assert resp3.headers.get('x-ratelimit-tier') == 'auth'


@pytest.mark.asyncio
async def test_write_tier_user_limit():
    app = _build_app()
    transport = ASGITransport(app=app)
    token = jwt.encode({'user_id': '42'}, JwtConfig.jwt_secret_key, algorithm=JwtConfig.jwt_algorithm)
    headers = {'Authorization': f'Bearer {token}'}

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        resp1 = await client.post('/api/write', json={'a': 1}, headers=headers)
        resp2 = await client.post('/api/write', json={'a': 2}, headers=headers)
        resp3 = await client.post('/api/write', json={'a': 3}, headers=headers)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 429
    assert resp3.headers.get('x-ratelimit-tier') == 'write'
    assert resp3.json().get('data', {}).get('scope') == 'user'


@pytest.mark.asyncio
async def test_read_tier_ip_limit():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        resp1 = await client.get('/api/read')
        resp2 = await client.get('/api/read')
        resp3 = await client.get('/api/read')

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 429
    assert resp3.headers.get('x-ratelimit-tier') == 'read'
    assert resp1.headers.get('x-ratelimit-limit') == '2'


@pytest.mark.asyncio
async def test_untrusted_proxy_ignores_x_forwarded_for():
    app = _build_app(
        read_ip_limit=2,
        trusted_proxies=['10.0.0.1'],
    )
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        resp1 = await client.get('/api/read', headers={'X-Forwarded-For': '1.1.1.1'})
        resp2 = await client.get('/api/read', headers={'X-Forwarded-For': '2.2.2.2'})
        resp3 = await client.get('/api/read', headers={'X-Forwarded-For': '3.3.3.3'})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 429

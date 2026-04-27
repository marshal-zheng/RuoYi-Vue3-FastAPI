import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from middlewares.rate_limit_middleware import RateLimitASGIMiddleware


def _build_app(**middleware_overrides) -> FastAPI:
    app = FastAPI()
    class _FakeSecurityTokenService:
        @staticmethod
        async def extract_user_context_from_token(token: str):
            if token.startswith('token-user-'):
                user_id = token.replace('token-user-', '')
                return {'userId': user_id}
            return None

    app.state.security_token_service = _FakeSecurityTokenService()
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
    assert resp3.headers.get('ratelimit-limit') == '2'
    assert resp3.headers.get('ratelimit-remaining') == '0'
    assert resp3.json()['status'] == 429
    assert resp3.json()['errorCode'] == 42901


@pytest.mark.asyncio
async def test_write_tier_user_limit():
    app = _build_app()
    transport = ASGITransport(app=app)
    token = 'token-user-42'
    headers = {'Authorization': f'Bearer {token}'}

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        resp1 = await client.post('/api/write', json={'a': 1}, headers=headers)
        resp2 = await client.post('/api/write', json={'a': 2}, headers=headers)
        resp3 = await client.post('/api/write', json={'a': 3}, headers=headers)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 429
    assert resp3.headers.get('ratelimit-limit') == '2'
    assert resp3.headers.get('ratelimit-remaining') == '0'
    assert resp3.json()['detail'].startswith('请求已触发限流')


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
    assert resp3.headers.get('ratelimit-limit') == '2'
    assert resp1.headers.get('ratelimit-limit') == '2'
    assert resp1.headers.get('ratelimit-remaining') == '1'


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

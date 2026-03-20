import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from middlewares.idempotency_middleware import IdempotencyASGIMiddleware


def _build_app(**middleware_overrides) -> FastAPI:
    app = FastAPI()
    class _FakeSecurityTokenService:
        @staticmethod
        async def extract_user_context_from_token(token: str):
            if token.startswith('token-user-'):
                user_id = token.replace('token-user-', '')
                return {'userId': user_id, 'sessionId': f's-{user_id}', 'tenantId': 't-1'}
            return None

    app.state.security_token_service = _FakeSecurityTokenService()
    middleware_config = {
        'enabled': True,
        'ttl_seconds': 120,
        'lock_ttl_seconds': 10,
        'wait_timeout_ms': 1000,
        'methods': ['POST', 'PUT'],
        'path_prefixes': ['/api'],
        'exclude_paths': [],
    }
    middleware_config.update(middleware_overrides)
    app.add_middleware(
        IdempotencyASGIMiddleware,
        **middleware_config,
    )

    app.state.write_calls = 0
    app.state.slow_write_calls = 0

    @app.post('/api/write')
    async def write_endpoint(payload: dict):
        app.state.write_calls += 1
        return {'ok': True, 'calls': app.state.write_calls, 'payload': payload}

    @app.post('/api/slow-write')
    async def slow_write_endpoint(payload: dict):
        app.state.slow_write_calls += 1
        await asyncio.sleep(0.2)
        return {'ok': True, 'calls': app.state.slow_write_calls, 'payload': payload}

    return app


@pytest.mark.asyncio
async def test_same_key_same_payload_replays_cached_response():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        headers = {'X-Idempotency-Key': 'idem-key-1'}
        first = await client.post('/api/write', json={'a': 1, 'b': 2}, headers=headers)
        second = await client.post('/api/write', json={'b': 2, 'a': 1}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert app.state.write_calls == 1


@pytest.mark.asyncio
async def test_same_key_different_payload_returns_conflict():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        headers = {'X-Idempotency-Key': 'idem-key-2'}
        first = await client.post('/api/write', json={'a': 1}, headers=headers)
        second = await client.post('/api/write', json={'a': 2}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.headers.get('content-type', '').startswith('application/problem+json')
    assert app.state.write_calls == 1


@pytest.mark.asyncio
async def test_without_idempotency_key_request_passthrough():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        first = await client.post('/api/write', json={'a': 1})
        second = await client.post('/api/write', json={'a': 1})

    assert first.status_code == 200
    assert second.status_code == 200
    assert app.state.write_calls == 2


@pytest.mark.asyncio
async def test_concurrent_retry_same_key_executes_once():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        headers = {'X-Idempotency-Key': 'idem-key-3'}
        task1 = asyncio.create_task(client.post('/api/slow-write', json={'a': 1}, headers=headers))
        await asyncio.sleep(0.02)
        task2 = asyncio.create_task(client.post('/api/slow-write', json={'a': 1}, headers=headers))
        resp1, resp2 = await asyncio.gather(task1, task2)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()
    assert app.state.slow_write_calls == 1


@pytest.mark.asyncio
async def test_same_key_different_user_should_not_replay():
    app = _build_app()
    transport = ASGITransport(app=app)
    token_a = 'token-user-1001'
    token_b = 'token-user-1002'

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        headers_a = {'X-Idempotency-Key': 'idem-key-user', 'Authorization': f'Bearer {token_a}'}
        headers_b = {'X-Idempotency-Key': 'idem-key-user', 'Authorization': f'Bearer {token_b}'}
        first = await client.post('/api/write', json={'a': 1}, headers=headers_a)
        second = await client.post('/api/write', json={'a': 1}, headers=headers_b)

    assert first.status_code == 200
    assert second.status_code == 200
    assert app.state.write_calls == 2


@pytest.mark.asyncio
async def test_large_request_body_skips_idempotency_cache():
    app = _build_app(max_request_body_bytes=32)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        headers = {'X-Idempotency-Key': 'idem-key-large'}
        payload = {'text': 'x' * 200}
        first = await client.post('/api/write', json=payload, headers=headers)
        second = await client.post('/api/write', json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert app.state.write_calls == 2


@pytest.mark.asyncio
async def test_release_lock_does_not_delete_other_owner_lock():
    async def passthrough_app(scope, receive, send):
        return None

    class FakeRedis:
        def __init__(self):
            self.get = AsyncMock(return_value="other-owner")
            self.delete = AsyncMock(return_value=1)

    middleware = IdempotencyASGIMiddleware(passthrough_app)
    redis_client = FakeRedis()
    scope = {"app": SimpleNamespace(state=SimpleNamespace(redis=redis_client))}

    await middleware._release_lock(scope, "idem:lock:1", "current-owner", backend="redis")

    redis_client.delete.assert_not_called()


@pytest.mark.asyncio
async def test_release_lock_deletes_only_when_owner_matches():
    async def passthrough_app(scope, receive, send):
        return None

    class FakeRedis:
        def __init__(self):
            self.get = AsyncMock(return_value=b"current-owner")
            self.delete = AsyncMock(return_value=1)

    middleware = IdempotencyASGIMiddleware(passthrough_app)
    redis_client = FakeRedis()
    scope = {"app": SimpleNamespace(state=SimpleNamespace(redis=redis_client))}

    await middleware._release_lock(scope, "idem:lock:2", "current-owner", backend="redis")

    redis_client.delete.assert_awaited_once_with("idem:lock:2")

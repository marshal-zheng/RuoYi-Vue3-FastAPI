import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from middlewares.csrf_guard_middleware import add_csrf_guard_middleware


class _FakeSecurityService:
    @staticmethod
    async def verify_access_token(token: str, **kwargs):
        _ = token
        _ = kwargs
        return {'sub': 'user:1'}

    @staticmethod
    async def validate_csrf_token(subject: str, token: str) -> bool:
        return subject == 'user:1' and token == 'csrf-ok'


def _build_app() -> FastAPI:
    app = FastAPI()
    app.state.security_token_service = _FakeSecurityService()
    add_csrf_guard_middleware(app)

    @app.post('/auth/ws-ticket')
    async def ws_ticket():
        return {'ok': True}

    @app.post('/auth/embed/grants')
    async def embed_grants():
        return {'ok': True}

    return app


@pytest.mark.asyncio
async def test_csrf_cookie_context_requires_token_and_origin():
    app = _build_app()
    transport = ASGITransport(app=app)

    headers = {
        'Origin': 'http://localhost:5173',
        'Authorization': 'Bearer token-user',
        'Cookie': 'csrf_token=csrf-ok',
    }
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.post('/auth/ws-ticket', headers=headers, json={'session_id': 's-1'})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_csrf_cookie_context_passes_with_valid_binding():
    app = _build_app()
    transport = ASGITransport(app=app)

    headers = {
        'Origin': 'http://localhost:5173',
        'Authorization': 'Bearer token-user',
        'Cookie': 'csrf_token=csrf-ok',
        'X-CSRF-Token': 'csrf-ok',
    }
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.post('/auth/ws-ticket', headers=headers, json={'session_id': 's-1'})

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_csrf_bypass_for_non_cookie_m2m_call():
    app = _build_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.post('/auth/embed/grants', json={'tenant_id': 't', 'integration_id': 'i', 'subject': '1'})

    assert response.status_code == 200

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from config.env import SecurityConfig
from exceptions.exception import AuthException
from modules.identity.api.login_controller import loginController, logout


class _FakeSecurityService:
    def __init__(self) -> None:
        self.registered_session_ids: list[str] = []
        self.registrations: list[dict] = []

    async def verify_access_token(self, token: str, **kwargs):
        assert token == 'refresh-old'
        assert kwargs.get('expected_use') == 'user_refresh'
        assert kwargs.get('enforce_replay') is False
        return {
            'sub': 'user:1',
            'user_id': '1',
            'user_name': 'admin',
            'dept_name': '平台',
            'session_id': 'sess-1',
            'login_info': {'ip': '127.0.0.1'},
        }

    async def issue_access_token(self, **kwargs):
        token_use = kwargs.get('token_use')
        if token_use == 'user_access':
            return 'access-new'
        if token_use == 'user_refresh':
            return 'refresh-new'
        raise AssertionError(f'Unexpected token_use: {token_use}')

    async def register_user_session(self, **kwargs):
        self.registrations.append(kwargs)
        self.registered_session_ids.append(str(kwargs.get('session_id') or ''))

    async def issue_csrf_token(self, subject: str):
        assert subject == '1'
        return 'csrf-new', 3600


@pytest.mark.asyncio
async def test_refresh_endpoint_rotates_tokens_and_sets_cookies():
    app = FastAPI()
    fake_service = _FakeSecurityService()
    app.state.security_token_service = fake_service
    app.include_router(loginController)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    cookie_header = f'{SecurityConfig.security_refresh_cookie_name}=refresh-old; csrf_token=csrf-new'
    headers = {'Origin': 'http://localhost:80', 'Cookie': cookie_header, 'X-CSRF-Token': 'csrf-new'}
    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.post('/auth/refresh', headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body['token'] == 'access-new'
    assert body['csrfToken'] == 'csrf-new'
    assert fake_service.registered_session_ids == ['sess-1']
    assert fake_service.registrations[0]['previous_refresh_token'] == 'refresh-old'
    assert fake_service.registrations[0]['refresh_token'] == 'refresh-new'
    assert fake_service.registrations[0]['refresh_expires_at'] > fake_service.registrations[0]['expires_at']

    set_cookie = response.headers.get('set-cookie', '')
    assert SecurityConfig.security_access_cookie_name in set_cookie
    assert SecurityConfig.security_refresh_cookie_name in set_cookie


@pytest.mark.asyncio
async def test_logout_falls_back_to_refresh_when_access_token_has_expired():
    service = AsyncMock()
    service.verify_access_token.side_effect = [
        AuthException(user_message='expired'), {'session_id': 'expired-access-session'},
    ]
    app = FastAPI()
    app.state.security_token_service = service
    request = Request({'type': 'http', 'app': app, 'scheme': 'http', 'server': ('localhost', 80),
                       'path': '/auth/logout', 'headers': [(b'cookie',
                         f'{SecurityConfig.security_refresh_cookie_name}=still-valid-refresh'.encode())]})
    response = await logout(request=request, token='expired-access', login_service=None)
    assert response.status_code == 204
    service.revoke_user_session.assert_awaited_once_with('expired-access-session')

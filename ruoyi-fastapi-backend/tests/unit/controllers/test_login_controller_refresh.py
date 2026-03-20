import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from config.env import SecurityConfig
from modules.identity.api.login_controller import loginController


class _FakeSecurityService:
    def __init__(self) -> None:
        self.registered_session_ids: list[str] = []

    async def verify_access_token(self, token: str, **kwargs):
        assert token == 'refresh-old'
        assert kwargs.get('expected_use') == 'user_refresh'
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
    assert body['data']['token'] == 'access-new'
    assert body['data']['csrfToken'] == 'csrf-new'
    assert fake_service.registered_session_ids == ['sess-1']

    set_cookie = response.headers.get('set-cookie', '')
    assert SecurityConfig.security_access_cookie_name in set_cookie
    assert SecurityConfig.security_refresh_cookie_name in set_cookie

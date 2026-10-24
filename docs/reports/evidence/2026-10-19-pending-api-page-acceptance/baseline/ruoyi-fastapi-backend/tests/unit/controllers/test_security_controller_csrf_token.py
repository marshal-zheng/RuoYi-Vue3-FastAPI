import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.identity.api.security_controller import securityController
from modules.identity.application.services.login_service import LoginService


class _FakeSecurityService:
    @staticmethod
    async def issue_csrf_token(subject: str) -> tuple[str, int]:
        assert subject == '1'
        return 'csrf-test-token', 300


def _build_current_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=['*:*:*'],
        roles=['admin'],
        user=UserInfoModel(
            userId=1,
            userName='admin',
            nickName='admin',
            deptId=1,
            status='0',
            delFlag='0',
        ),
    )


def _build_app() -> FastAPI:
    app = FastAPI()
    app.state.security_token_service = _FakeSecurityService()
    app.include_router(securityController)

    async def _override_get_current_user() -> CurrentUserModel:
        return _build_current_user()

    app.dependency_overrides[LoginService.get_current_user] = _override_get_current_user
    return app


@pytest.mark.asyncio
async def test_issue_csrf_token_returns_cookie_without_internal_error():
    app = _build_app()
    transport = ASGITransport(app=app, raise_app_exceptions=False)

    async with AsyncClient(transport=transport, base_url='http://testserver') as client:
        response = await client.post('/auth/csrf-token', headers={'Authorization': 'Bearer any-token'})

    assert response.status_code == 200
    set_cookie = response.headers.get('set-cookie', '')
    assert 'csrf_token=csrf-test-token' in set_cookie

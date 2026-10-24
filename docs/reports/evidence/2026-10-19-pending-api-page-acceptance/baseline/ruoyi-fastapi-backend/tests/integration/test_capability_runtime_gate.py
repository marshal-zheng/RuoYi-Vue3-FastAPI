"""Integration tests for runtime capability gating."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from config.enums import RedisInitKeyConfig
from container import build_container
from exceptions.handle import handle_exception
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.identity.api.login_controller import loginController
from modules.identity.application.services.login_service import LoginService
from modules.project.api.project_controller import projectController
from modules.registry import ModuleRegistration, RouterRegistration, register_modules
from modules.system.application.services.capability_gate_service import CapabilityGateService
from scripts.internal.db_workflow.capability_models import CapabilityRuntimeGate


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)


class _FakeLoginService:
    def __init__(self, routers: list[dict[str, object]]) -> None:
        self.routers = routers

    async def get_current_user_routers(self, user_id: int):
        assert user_id == 1
        return list(self.routers)


class _FakeProjectService:
    async def get_project_detail(self, project_id: int):
        return {'projectId': project_id, 'projectName': 'demo'}

    async def get_project_list(self, project_page_query, is_page: bool = True):
        return {'items': [], 'total': 0, 'page': 1, 'pageSize': 10}


def _build_admin_user() -> CurrentUserModel:
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


def _platform_gate_key() -> str:
    return f'{RedisInitKeyConfig.SYS_CONFIG.key}:capability.platform.enabled'


def _build_gate_test_client(*, routers: list[dict[str, object]] | None = None, gate_value: str | None = 'true') -> TestClient:
    app = FastAPI()
    handle_exception(app)

    container = build_container()
    container.override('login_service', lambda _session: _FakeLoginService(routers or []))
    container.override('project_service', lambda _session: _FakeProjectService())

    redis = _FakeRedis()
    if gate_value is not None:
        redis.store[_platform_gate_key()] = gate_value

    app.state.container = container
    app.state.redis = redis
    app.state.capability_gate_service = CapabilityGateService(
        runtime_gates={
            'platform': CapabilityRuntimeGate(
                module_key='platform',
                config_key='capability.platform.enabled',
                default_enabled=False,
            )
        }
    )

    async def override_get_current_user() -> CurrentUserModel:
        return _build_admin_user()

    app.dependency_overrides[LoginService.get_current_user] = override_get_current_user
    register_modules(
        app,
        registry=(
            ModuleRegistration(
                name='identity',
                version='v1',
                routers=(RouterRegistration(router=loginController, tags=('登录模块',)),),
            ),
            ModuleRegistration(
                name='project',
                version='v1',
                routers=(RouterRegistration(router=projectController, tags=('工程管理',), capability_module_key='platform'),),
            ),
        ),
    )
    return TestClient(app)


def test_get_routers_contract_stays_unchanged_when_module_menus_are_absent():
    with _build_gate_test_client(routers=[], gate_value='false') as client:
        response = client.get('/getRouters')

    assert response.status_code == 200
    assert response.json() == {'items': []}


def test_platform_api_returns_forbidden_when_gate_disabled():
    with _build_gate_test_client(gate_value='false') as client:
        response = client.get('/project/1')

    assert response.status_code == 403
    assert response.json()['detail'] == '模块 platform 当前未启用'


def test_platform_api_defaults_to_disabled_when_gate_config_is_missing():
    with _build_gate_test_client(gate_value=None) as client:
        response = client.get('/project/1')

    assert response.status_code == 403
    assert response.json()['detail'] == '模块 platform 当前未启用'

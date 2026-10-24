"""Real FastAPI request parsing for the four authorization JSON operations."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from config.get_db import get_db
from module_admin.aspect.data_scope import GetDataScope
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.do.role_do import RoleDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.identity.ports import get_current_user
from modules.system.api.dependencies import provide_system_mediator
from modules.system.api.role_controller import roleController
from modules.system.api.user_controller import userController
from modules.system.application.services.role_service import RoleService
from modules.system.application.services.user_service import UserService
from modules.system.infrastructure.role_repository import RoleRepository

OPERATIONS = [
    ('/system/user/authRole', {'userId': 42, 'roleIds': [2, 3]}, 'user_role'),
    ('/system/role/authUser/selectAll', {'roleId': 2, 'userIds': [42, 43]}, 'role_user'),
    ('/system/role/authUser/cancel', {'roleId': 2, 'userId': 42}, 'role_user'),
    ('/system/role/authUser/cancelAll', {'roleId': 2, 'userIds': [42, 43]}, 'role_user'),
]


@pytest.fixture
def authorization_http():
    app = FastAPI()
    app.include_router(userController)
    app.include_router(roleController)
    mediator = SimpleNamespace(send=AsyncMock(return_value=SimpleNamespace(data={'message': 'ok'})))
    current = CurrentUserModel(permissions=[], roles=[], user=UserInfoModel(userId=7, userName='actor'))
    app.dependency_overrides[get_current_user] = lambda: current
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[provide_system_mediator] = lambda: mediator

    def override_scopes(dependant):
        for dependency in dependant.dependencies:
            if isinstance(dependency.call, (GetDataScope, CheckUserInterfaceAuth)):
                app.dependency_overrides[dependency.call] = lambda: 'True'
            override_scopes(dependency)

    for route in app.routes:
        if hasattr(route, 'dependant'):
            override_scopes(route.dependant)
    with TestClient(app) as client:
        yield client, mediator


@pytest.mark.parametrize('path,payload,field', OPERATIONS)
def test_json_operation_reaches_typed_command_and_returns_no_content(authorization_http, path, payload, field):
    client, mediator = authorization_http
    response = client.put(path, json=payload)
    assert response.status_code == 204, response.text
    assert response.content == b''
    command = mediator.send.await_args.args[0]
    assert getattr(command, field).model_dump(by_alias=True) == payload
    assert command.enforce_scope_checks is True
    assert command.user_data_scope_sql == 'True'
    assert command.role_data_scope_sql == 'True'


@pytest.mark.parametrize('path,payload,field', OPERATIONS)
def test_query_only_old_payload_is_rejected(authorization_http, path, payload, field):
    client, mediator = authorization_http
    response = client.put(path, params=payload)
    assert response.status_code == 422
    mediator.send.assert_not_awaited()


def test_user_roles_empty_array_is_an_explicit_replacement(authorization_http):
    client, mediator = authorization_http
    response = client.put('/system/user/authRole', json={'userId': 42, 'roleIds': []})
    assert response.status_code == 204, response.text
    assert mediator.send.await_args.args[0].user_role.role_ids == []


@pytest.mark.parametrize('path,payload,field', OPERATIONS)
@pytest.mark.parametrize('bad_value', [None, '42,43', [True], [0], [1.5], ['42']])
def test_invalid_json_is_rejected_before_dispatch(authorization_http, path, payload, field, bad_value):
    client, mediator = authorization_http
    collection = 'roleIds' if 'roleIds' in payload else 'userIds' if 'userIds' in payload else None
    key = collection or 'userId'
    response = client.put(path, json={**payload, key: bad_value})
    assert response.status_code == 422, response.text
    mediator.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_json_writes_round_trip_through_production_mediator_and_sqlite(
    authorization_http, db_session, app_container
):
    """Keep production DI registration, command pipeline, handlers, services and repositories."""
    client, _ = authorization_http
    app = client.app
    app.dependency_overrides.pop(provide_system_mediator)
    app.dependency_overrides[get_db] = lambda: db_session
    services = {
        'user_service': UserService(query_db=db_session),
        'role_service': RoleService(RoleRepository(db_session), AsyncMock(), AsyncMock(), AsyncMock(), db_session),
    }
    for name in (
        'config_service',
        'dept_service',
        'dict_type_service',
        'dict_data_service',
        'menu_service',
        'notice_service',
        'post_service',
        'role_service',
        'user_service',
    ):
        service = services.get(name, AsyncMock())
        app_container.override(name, lambda _db, service=service: service)
    app.state.container = app_container
    db_session.add_all(
        [
            UserDO(user_id=42, user_name='u42', nick_name='U42', password='hash'),
            UserDO(user_id=43, user_name='u43', nick_name='U43', password='hash'),
            RoleDO(role_id=20, role_name='R20', role_key='r20', role_sort=20),
            RoleDO(role_id=21, role_name='R21', role_key='r21', role_sort=21),
        ]
    )
    await db_session.flush()

    async def relations():
        return set((await db_session.execute(select(UserRoleDO.user_id, UserRoleDO.role_id))).all())

    operations = [
        ('/system/user/authRole', {'userId': 42, 'roleIds': [20, 21]}, {(42, 20), (42, 21)}),
        ('/system/role/authUser/selectAll', {'roleId': 20, 'userIds': [42, 43]}, {(42, 20), (42, 21), (43, 20)}),
        ('/system/role/authUser/cancel', {'roleId': 21, 'userId': 42}, {(42, 20), (43, 20)}),
        ('/system/role/authUser/cancelAll', {'roleId': 20, 'userIds': [42, 43]}, set()),
        ('/system/user/authRole', {'userId': 43, 'roleIds': []}, set()),
    ]
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as http:
        for path, payload, expected in operations:
            response = await http.put(path, json=payload)
            assert response.status_code == 204, response.text
            assert response.content == b''
            assert await relations() == expected

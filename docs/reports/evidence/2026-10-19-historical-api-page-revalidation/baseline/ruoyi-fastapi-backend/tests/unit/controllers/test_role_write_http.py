"""Role write contracts through HTTP, production command DI and SQLite repositories."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.get_db import get_db
from exceptions.handle import handle_exception
from module_admin.aspect.data_scope import GetDataScope
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.do.role_do import RoleDeptDO, RoleDO, RoleMenuDO
from module_admin.entity.do.user_do import UserRoleDO
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.identity.ports import get_current_user
from modules.system.api.role_controller import roleController
from modules.system.application.services.role_service import RoleService
from modules.system.infrastructure.role_dept_repository import RoleDeptRepository
from modules.system.infrastructure.role_menu_repository import RoleMenuRepository
from modules.system.infrastructure.role_repository import RoleRepository
from modules.system.infrastructure.user_repository import UserRepository


@pytest.fixture
async def role_write_http(app_container):
    """Keep real mediator/handlers/transactions; isolate persistence from other tests."""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        for model in (RoleDO, RoleDeptDO, RoleMenuDO, UserRoleDO):
            await connection.run_sync(model.__table__.create)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add_all(
            [
                RoleDO(role_id=20, role_name='Existing', role_key='existing', role_sort=2, data_scope='2'),
                RoleDO(role_id=21, role_name='Other', role_key='other', role_sort=3),
                RoleMenuDO(role_id=20, menu_id=101),
                RoleDeptDO(role_id=20, dept_id=201),
            ]
        )
        await session.commit()
        service = RoleService(
            RoleRepository(session),
            RoleMenuRepository(session),
            RoleDeptRepository(session),
            UserRepository(session),
            session,
        )
        app = FastAPI()
        handle_exception(app)
        app.include_router(roleController)
        app.dependency_overrides[get_db] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: CurrentUserModel(
            permissions=['*:*:*'], roles=['admin'], user=UserInfoModel(userId=1, userName='actor')
        )
        for route in app.routes:
            if hasattr(route, 'dependant'):
                pending = [route.dependant]
                while pending:
                    dependency = pending.pop()
                    if isinstance(dependency.call, (GetDataScope, CheckUserInterfaceAuth)):
                        app.dependency_overrides[dependency.call] = lambda: 'True'
                    pending.extend(dependency.dependencies)
        for name in (
            'config_service',
            'dept_service',
            'dict_type_service',
            'dict_data_service',
            'menu_service',
            'notice_service',
            'post_service',
            'user_service',
            'role_service',
        ):
            value = service if name == 'role_service' else AsyncMock()
            app_container.override(name, lambda _db, value=value: value)
        app.state.container = app_container
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            yield SimpleNamespace(client=client, session=session, service=service, app=app)
    await engine.dispose()


def drawer_payload(**changes):
    """Exact RoleFormDrawer fields, including its default zero sort."""
    return {
        'roleName': 'Created',
        'roleKey': 'created',
        'roleSort': 0,
        'status': '0',
        'menuCheckStrictly': True,
        'remark': '',
        'menuIds': [101, 102],
        **changes,
    }


async def snapshot(session):
    role = (await session.execute(select(RoleDO.__table__).where(RoleDO.role_id == 20))).mappings().one()
    menus = set((await session.scalars(select(RoleMenuDO.menu_id).where(RoleMenuDO.role_id == 20))).all())
    depts = set((await session.scalars(select(RoleDeptDO.dept_id).where(RoleDeptDO.role_id == 20))).all())
    return dict(role), menus, depts


@pytest.mark.parametrize('menus', [{}, {'menuIds': []}, {'menuIds': None}, {'menuIds': [102]}])
async def test_partial_edit_preserves_scalars_and_replaces_only_supplied_menus(role_write_http, menus):
    http = role_write_http
    before, _, _ = await snapshot(http.session)
    response = await http.client.put('/system/role', json={'roleId': 20, 'remark': 'changed', **menus})
    assert response.status_code == 200, response.text
    after, actual_menus, depts = await snapshot(http.session)
    assert response.json()['remark'] == after['remark'] == 'changed'
    for field in ('role_name', 'role_key', 'role_sort', 'status', 'data_scope', 'dept_check_strictly'):
        assert after[field] == before[field]
    assert actual_menus == (set(menus['menuIds'] or []) if menus else {101})
    assert depts == {201}


@pytest.mark.parametrize('menus', [{}, {'menuIds': []}, {'menuIds': None}])
async def test_create_accepts_missing_empty_and_null_relations(role_write_http, menus):
    payload = drawer_payload()
    payload.pop('menuIds')
    response = await role_write_http.client.post('/system/role', json={**payload, **menus})
    assert response.status_code == 201, response.text
    role_id = response.json()['roleId']
    assert response.headers['location'] == f'http://test/system/role/{role_id}'
    assert response.json()['roleSort'] == 0
    stored = await role_write_http.session.get(RoleDO, role_id)
    assert stored.role_name == 'Created' and stored.role_sort == 0
    assert not (
        await role_write_http.session.scalars(select(RoleMenuDO.menu_id).where(RoleMenuDO.role_id == role_id))
    ).all()


@pytest.mark.parametrize('scope', ['1', '2', '3', '4', '5'])
@pytest.mark.parametrize('depts', [{}, {'deptIds': []}, {'deptIds': None}, {'deptIds': [202]}])
async def test_scope_updates_preserve_omitted_depts_and_other_domains(role_write_http, scope, depts):
    http = role_write_http
    before, _, _ = await snapshot(http.session)
    response = await http.client.put('/system/role/dataScope', json={'roleId': 20, 'dataScope': scope, **depts})
    assert response.status_code == 200, response.text
    after, menus, actual_depts = await snapshot(http.session)
    assert response.json()['dataScope'] == after['data_scope'] == scope
    for field in ('role_name', 'role_key', 'role_sort', 'status', 'menu_check_strictly', 'remark'):
        assert after[field] == before[field]
    assert menus == {101}
    expected = {201} if not depts else set(depts['deptIds'] or []) if scope == '2' else set()
    assert actual_depts == expected


INVALID_WRITES = [
    ('post', '', {'roleKey': 'created', 'roleSort': 0}),
    ('post', '', drawer_payload(roleName='')),
    ('post', '', drawer_payload(roleKey='')),
    ('post', '', drawer_payload(roleSort=None)),
    ('post', '', drawer_payload(dataScope='2')),
    ('post', '', drawer_payload(roleId=22)),
    ('put', '', {'roleId': 20, 'roleName': None, 'menuIds': []}),
    ('put', '', {'roleId': 20, 'roleKey': None}),
    ('put', '', {'roleId': 20, 'roleSort': None}),
    ('put', '', {'roleId': 20, 'status': None}),
    ('put', '', {'roleId': 20, 'dataScope': '1'}),
    ('put', '', {'roleId': 20, 'deptIds': []}),
    ('put', '', {'roleId': 20, 'createBy': 'intruder'}),
    ('put', '', {'roleId': 20, 'delFlag': '2'}),
    ('put', '', {'roleId': 20, 'type': 'status'}),
    ('put', '/changeStatus', {'roleId': 20}),
    ('put', '/changeStatus', {'roleId': 20, 'status': None}),
    ('put', '/changeStatus', {'roleId': 20, 'status': '9'}),
    ('put', '/changeStatus', {'roleId': 20, 'status': '1', 'menuIds': []}),
    ('put', '/changeStatus', {'roleId': 20, 'status': '1', 'remark': 'intruder'}),
    ('put', '/dataScope', {'roleId': 20, 'dataScope': '9', 'deptIds': []}),
    ('put', '/dataScope', {'roleId': 20}),
    ('put', '/dataScope', {'roleId': 20, 'dataScope': None}),
    ('put', '/dataScope', {'roleId': 20, 'dataScope': '2', 'status': '1'}),
    ('put', '/dataScope', {'roleId': 20, 'dataScope': '2', 'menuIds': []}),
    ('put', '', {'roleId': 0, 'remark': 'invalid id'}),
]


@pytest.mark.parametrize('method,path,payload', INVALID_WRITES)
async def test_invalid_or_cross_operation_fields_are_rejected_before_writes(role_write_http, method, path, payload):
    http = role_write_http
    before = await snapshot(http.session)
    response = await http.client.request(method, f'/system/role{path}', json=payload)
    assert response.status_code == 422, response.text
    assert await snapshot(http.session) == before
    assert (await http.session.scalars(select(RoleDO.role_id))).all() == [20, 21]


async def test_actual_drawer_scope_status_and_delete_round_trip(role_write_http):
    http = role_write_http
    response = await http.client.post('/system/role', json=drawer_payload())
    assert response.status_code == 201, response.text
    role_id = response.json()['roleId']
    for scope in ['1', '2', '3', '4', '5']:
        response = await http.client.put(
            '/system/role/dataScope',
            json={
                'roleId': role_id,
                'dataScope': scope,
                'deptCheckStrictly': True,
                'deptIds': [201, 202] if scope == '2' else [],
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()['dataScope'] == scope
    response = await http.client.put(
        '/system/role',
        json=drawer_payload(
            roleId=role_id,
            roleName='Edited',
            roleKey='edited',
            roleSort=4,
            menuIds=[102],
            remark='saved',
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json()['roleName'] == 'Edited' and response.json()['dataScope'] == '5'
    for status in ['1', '0']:
        response = await http.client.put('/system/role/changeStatus', json={'roleId': role_id, 'status': status})
        assert response.status_code == 200, response.text
        assert response.json()['status'] == status
        assert response.json()['roleName'] == 'Edited' and response.json()['dataScope'] == '5'
        response = await http.client.get(f'/system/role/{role_id}')
        assert response.status_code == 200 and response.json()['status'] == status
    http.session.add(UserRoleDO(user_id=900, role_id=role_id))
    await http.session.flush()
    response = await http.client.delete(f'/system/role/{role_id}')
    assert response.status_code == 409, response.text
    await http.session.execute(delete(UserRoleDO).where(UserRoleDO.role_id == role_id))
    response = await http.client.delete(f'/system/role/{role_id}')
    assert response.status_code == 204 and response.content == b''
    assert not (await http.session.scalars(select(RoleMenuDO.menu_id).where(RoleMenuDO.role_id == role_id))).all()
    response = await http.client.get(f'/system/role/{role_id}')
    assert response.status_code == 404, response.text


async def test_conflict_does_not_apply_scalar_or_relation_changes(role_write_http):
    http = role_write_http
    before = await snapshot(http.session)
    response = await http.client.put('/system/role', json={'roleId': 20, 'roleKey': 'other', 'menuIds': []})
    assert response.status_code == 409, response.text
    assert await snapshot(http.session) == before


async def test_mid_write_failure_rolls_back_scalars_and_relations(role_write_http, monkeypatch):
    http = role_write_http
    before = await snapshot(http.session)
    monkeypatch.setattr(http.service.role_menu_repo, 'add', AsyncMock(side_effect=RuntimeError('write failure')))
    response = await http.client.put('/system/role', json={'roleId': 20, 'remark': 'must roll back', 'menuIds': [102]})
    assert response.status_code == 500, response.text
    assert await snapshot(http.session) == before


async def test_openapi_exposes_operation_specific_input_and_actual_resource_responses(role_write_http):
    document = role_write_http.app.openapi()
    artifact = json.loads((Path(__file__).parents[4] / 'shared' / 'openapi.json').read_text())
    operations = [
        ('/system/role', 'post', 'RoleCreateModel', '201'),
        ('/system/role', 'put', 'RoleUpdateModel', '200'),
        ('/system/role/dataScope', 'put', 'RoleDataScopeUpdateModel', '200'),
        ('/system/role/changeStatus', 'put', 'RoleStatusUpdateModel', '200'),
    ]
    for path, method, name, success_status in operations:
        operation = document['paths'][path][method]
        body = operation['requestBody']['content']['application/json']['schema']
        assert body == {'$ref': f'#/components/schemas/{name}'}
        response = operation['responses'][success_status]['content']['application/json']['schema']
        assert response == {'$ref': '#/components/schemas/RoleModel'}
        assert document['components']['schemas'][name]['additionalProperties'] is False
        published = artifact['paths'][path][method]
        assert published['requestBody'] == operation['requestBody']
        assert published['responses'] == operation['responses']
        assert artifact['components']['schemas'][name] == document['components']['schemas'][name]
    assert 'AddRoleModel' not in artifact['components']['schemas']

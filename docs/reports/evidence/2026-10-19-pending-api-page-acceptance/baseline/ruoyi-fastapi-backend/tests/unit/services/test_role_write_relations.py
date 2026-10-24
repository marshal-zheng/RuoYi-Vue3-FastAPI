"""Persistence regressions for operation fields and omitted/empty associations."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from module_admin.entity.do.role_do import RoleDeptDO, RoleDO, RoleMenuDO
from module_admin.entity.do.user_do import UserDO, UserPostDO, UserRoleDO
from module_admin.entity.vo.role_vo import AddRoleModel, RoleModel
from module_admin.entity.vo.user_vo import EditUserModel
from modules.system.application.services.role_service import RoleService
from modules.system.application.services.user_service import UserService
from modules.system.infrastructure.role_dept_repository import RoleDeptRepository
from modules.system.infrastructure.role_menu_repository import RoleMenuRepository
from modules.system.infrastructure.role_repository import RoleRepository
from modules.system.infrastructure.user_post_repository import UserPostRepository
from modules.system.infrastructure.user_role_repository import UserRoleRepository


@pytest.mark.asyncio
@pytest.mark.parametrize('provided', ['omitted', 'empty', 'null', 'replace'])
@pytest.mark.parametrize('operation', ['edit', 'scope'])
async def test_role_relationship_presence_is_preserved(db_session, provided, operation):
    role = RoleDO(role_id=42, role_name='Before', role_key='before', role_sort=1, data_scope='2', status='0')
    db_session.add(role)
    db_session.add_all([RoleMenuDO(role_id=42, menu_id=20), RoleDeptDO(role_id=42, dept_id=30)])
    await db_session.flush()
    service = RoleService(
        RoleRepository(db_session),
        RoleMenuRepository(db_session),
        RoleDeptRepository(db_session),
        AsyncMock(),
        db_session,
    )
    service.role_detail_services = AsyncMock(return_value=RoleModel(roleId=42))
    service.check_role_name_unique_services = AsyncMock(return_value=True)
    service.check_role_key_unique_services = AsyncMock(return_value=True)
    field = 'menuIds' if operation == 'edit' else 'deptIds'
    old = 20 if operation == 'edit' else 30
    values = {'omitted': {}, 'empty': {field: []}, 'null': {field: None}, 'replace': {field: [old + 1]}}
    payload = {'roleId': 42, **values[provided]}
    if operation == 'edit':
        payload['roleName'] = 'After'
        await service.edit_role_services(AddRoleModel(**payload))
    else:
        payload['dataScope'] = '2'
        await service.role_datascope_services(AddRoleModel(**payload))
    menus = [row.menu_id for row in await service.role_menu_repo.find_by_role_id(42)]
    depts = [row.dept_id for row in await service.role_dept_repo.find_by_role_id(42)]
    expected = [old] if provided == 'omitted' else [old + 1] if provided == 'replace' else []
    assert (menus if operation == 'edit' else depts) == expected
    assert (depts if operation == 'edit' else menus) == ([30] if operation == 'edit' else [20])


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['edit', 'scope', 'status'])
async def test_role_service_updates_only_operation_fields(db_session, operation):
    role = RoleDO(
        role_id=42,
        role_name='Before',
        role_key='before',
        role_sort=1,
        data_scope='2',
        status='0',
        del_flag='0',
        create_by='original',
    )
    db_session.add(role)
    await db_session.flush()
    service = RoleService(
        RoleRepository(db_session),
        RoleMenuRepository(db_session),
        RoleDeptRepository(db_session),
        AsyncMock(),
        db_session,
    )
    service.role_detail_services = AsyncMock(return_value=RoleModel(roleId=42))
    service.check_role_name_unique_services = AsyncMock(return_value=True)
    service.check_role_key_unique_services = AsyncMock(return_value=True)
    data = {'roleId': 42, 'delFlag': '2', 'createBy': 'smuggled'}
    if operation == 'edit':
        data.update(roleName='After', dataScope='1', menuIds=[])
        await service.edit_role_services(AddRoleModel(**data))
        assert role.role_name == 'After'
        assert role.data_scope == '2'
    elif operation == 'scope':
        data.update(roleName='Smuggled', dataScope='1', deptIds=[])
        await service.role_datascope_services(AddRoleModel(**data))
        assert role.role_name == 'Before'
        assert role.data_scope == '1'
    else:
        data.update(roleName='Smuggled', status='1', type='status')
        await service.edit_role_services(AddRoleModel(**data))
        assert role.role_name == 'Before'
        assert role.status == '1'
    assert role.del_flag == '0'
    assert role.create_by == 'original'


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['profile', 'status', 'edit'])
async def test_user_service_restricts_fields_and_profile_does_not_touch_relations(db_session, operation):
    user = UserDO(
        user_id=42,
        user_name='alice',
        nick_name='Before',
        dept_id=7,
        status='0',
        del_flag='0',
        password='original-hash',
        login_ip='original',
    )
    db_session.add(user)
    db_session.add_all([UserRoleDO(user_id=42, role_id=20), UserPostDO(user_id=42, post_id=30)])
    await db_session.flush()
    payload = {
        'userId': 42,
        'userName': 'alice',
        'nickName': 'After',
        'password': 'smuggled',
        'delFlag': '2',
        'loginIp': 'smuggled',
        'roleIds': [],
        'postIds': [],
    }
    if operation == 'profile':
        payload.update(type='profile', deptId=999, status='1')
    elif operation == 'status':
        payload.update(type='status', status='1')
    await UserService().edit_user_services(db_session, EditUserModel(**payload))
    assert user.password == 'original-hash'
    assert user.del_flag == '0'
    assert user.login_ip == 'original'
    assert user.nick_name == ('Before' if operation == 'status' else 'After')
    if operation == 'profile':
        assert user.dept_id == 7
        assert user.status == '0'
    if operation != 'edit':
        assert [row.role_id for row in await UserRoleRepository(db_session).find_by_user_id(42)] == [20]
        assert [row.post_id for row in await UserPostRepository(db_session).find_by_user_id(42)] == [30]


@pytest.mark.asyncio
async def test_login_bookkeeping_updates_login_fields_without_using_status_operation(db_session):
    user = UserDO(user_id=42, user_name='login_user', nick_name='Before', status='0')
    db_session.add(user)
    await db_session.flush()
    login_date = datetime(2026, 1, 1)
    await UserService().edit_user_services(
        db_session, EditUserModel(userId=42, loginDate=login_date, status='1', nickName='Smuggled', type='login')
    )
    assert user.login_date == login_date
    assert user.status == '0'
    assert user.nick_name == 'Before'

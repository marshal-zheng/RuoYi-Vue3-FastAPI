"""Authorization editing exposes complete existing relations and enforces target scope."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import delete

from exceptions.exception import PermissionException, ResourceNotFoundException
from module_admin.entity.do.role_do import RoleDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from module_admin.entity.vo.user_vo import UserRoleQueryModel
from modules.system.application.handlers.query.user_query_handlers import GetUserAuthRoleQueryHandler
from modules.system.application.queries.user_queries import GetUserAuthRoleQuery
from modules.system.application.services.user_service import UserService


@pytest.mark.asyncio
async def test_authorization_read_includes_assigned_disabled_and_admin_roles(db_session):
    db_session.add(UserDO(user_id=42, user_name='owned', nick_name='Owned', password='hash'))
    db_session.add_all(
        [
            RoleDO(role_id=1, role_name='Admin', role_key='admin', role_sort=1, status='0'),
            RoleDO(role_id=20, role_name='Active', role_key='active', role_sort=2, status='0'),
            RoleDO(role_id=21, role_name='Assigned disabled', role_key='disabled', role_sort=3, status='1'),
            RoleDO(role_id=22, role_name='Other disabled', role_key='other', role_sort=4, status='1'),
        ]
    )
    db_session.add_all([UserRoleDO(user_id=42, role_id=1), UserRoleDO(user_id=42, role_id=21)])
    await db_session.flush()
    result = await UserService(query_db=db_session).get_user_role_allocated_list_services(
        db_session, UserRoleQueryModel(userId=42)
    )
    assert {role.role_id for role in result.roles} == {1, 20, 21}
    assert {role.role_id for role in result.roles if role.flag} == {1, 21}
    assert {role.role_id for role in result.user.role} == {1, 21}
    assert set(result.user.role_ids.split(',')) == {'1', '21'}

    await db_session.execute(delete(UserRoleDO).where(UserRoleDO.user_id == 42, UserRoleDO.role_id == 21))
    db_session.add(UserRoleDO(user_id=42, role_id=20))
    active_role = await db_session.get(RoleDO, 20)
    active_role.role_name = 'Renamed'
    await db_session.flush()

    refreshed = await UserService(query_db=db_session).get_user_role_allocated_list_services(
        db_session, UserRoleQueryModel(userId=42)
    )
    assert {role.role_id for role in refreshed.roles} == {1, 20}
    assert {role.role_id for role in refreshed.roles if role.flag} == {1, 20}
    assert next(role.role_name for role in refreshed.roles if role.role_id == 20) == 'Renamed'
    assert {role.role_id for role in result.roles if role.flag} == {1, 21}


@pytest.mark.asyncio
async def test_authorization_read_missing_user_is_not_found(db_session):
    with pytest.raises(ResourceNotFoundException):
        await UserService(query_db=db_session).get_user_role_allocated_list_services(
            db_session, UserRoleQueryModel(userId=40442)
        )


@pytest.mark.asyncio
async def test_authorization_read_rejects_out_of_scope_target_before_loading():
    service = AsyncMock()
    service.check_user_data_scope_services.side_effect = PermissionException(user_message='out of scope')
    handler = GetUserAuthRoleQueryHandler(service)
    with pytest.raises(PermissionException):
        await handler.handle(
            GetUserAuthRoleQuery(query_db=object(), user_id=42, require_scope_check=True, data_scope_sql=False)
        )
    service.get_user_role_allocated_list_services.assert_not_awaited()

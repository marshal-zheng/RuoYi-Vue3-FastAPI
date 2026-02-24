from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from module_admin.entity.vo.role_vo import AddRoleModel, DeleteRoleModel
from module_admin.entity.vo.user_vo import CrudUserRoleModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import (
    AddRoleCommand,
    AddRoleUserCommand,
    AssignRoleDataScopeCommand,
    CancelRoleUserCommand,
    ChangeRoleStatusCommand,
    DeleteRoleCommand,
    EditRoleCommand,
)
from modules.system.application.handlers.command.role_command_handlers import (
    AddRoleCommandHandler,
    AddRoleUserCommandHandler,
    AssignRoleDataScopeCommandHandler,
    CancelRoleUserCommandHandler,
    ChangeRoleStatusCommandHandler,
    DeleteRoleCommandHandler,
    EditRoleCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _RoleServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.grant_called_with = None
        self.delete_called_with = None
        self.allowed_called_with = []
        self.scope_called_with = []

    async def add_role_services(self, payload):
        self.add_called_with = payload
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_role_services(self, payload):
        self.edit_called_with = payload
        return _CrudResponse(is_success=True, message='更新成功')

    async def role_datascope_services(self, payload):
        self.grant_called_with = payload
        return _CrudResponse(is_success=True, message='分配成功')

    async def delete_role_services(self, payload):
        self.delete_called_with = payload
        return _CrudResponse(is_success=True, message='删除成功')

    async def check_role_allowed_services(self, payload):
        self.allowed_called_with.append(payload)
        return _CrudResponse(is_success=True, message='校验通过')

    async def check_role_data_scope_services(self, role_ids, data_scope_sql):
        self.scope_called_with.append((role_ids, data_scope_sql))
        return _CrudResponse(is_success=True, message='校验通过')


class _UserServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.delete_called_with = None

    async def add_user_role_services(self, query_db, payload):
        self.add_called_with = (query_db, payload)
        return _CrudResponse(is_success=True, message='分配成功')

    async def delete_user_role_services(self, query_db, payload):
        self.delete_called_with = (query_db, payload)
        return _CrudResponse(is_success=True, message='删除成功')


@pytest.mark.asyncio
async def test_role_command_handlers_success() -> None:
    role_service = _RoleServiceStub()
    add_handler = AddRoleCommandHandler(role_service)
    edit_handler = EditRoleCommandHandler(role_service)
    grant_handler = AssignRoleDataScopeCommandHandler(role_service)
    delete_handler = DeleteRoleCommandHandler(role_service)
    change_status_handler = ChangeRoleStatusCommandHandler(role_service)

    add_result = await add_handler.handle(
        AddRoleCommand(
            role=AddRoleModel(roleName='系统管理员', roleKey='sys_admin', roleSort=1, status='0', menuIds=[1]),
            operator='admin',
        )
    )
    edit_result = await edit_handler.handle(
        EditRoleCommand(
            role=AddRoleModel(
                roleId=2,
                roleName='运维角色',
                roleKey='ops',
                roleSort=2,
                status='0',
                menuIds=[1, 2],
            ),
            operator='admin',
        )
    )
    grant_result = await grant_handler.handle(
        AssignRoleDataScopeCommand(
            role=AddRoleModel(
                roleId=2,
                dataScope='2',
                deptIds=[1],
                deptCheckStrictly=True,
                updateBy='admin',
                updateTime=datetime.now(),
            ),
            operator='admin',
        )
    )
    delete_result = await delete_handler.handle(
        DeleteRoleCommand(
            delete_role=DeleteRoleModel(roleIds='2', updateBy='admin', updateTime=datetime.now()),
            operator='admin',
        )
    )
    change_status_result = await change_status_handler.handle(
        ChangeRoleStatusCommand(
            role=AddRoleModel(
                roleId=2,
                status='1',
                updateBy='admin',
                updateTime=datetime.now(),
                type='status',
            ),
            operator='admin',
        )
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert grant_result.status == 'granted'
    assert delete_result.status == 'deleted'
    assert change_status_result.status == 'updated'
    assert role_service.add_called_with is not None
    assert role_service.edit_called_with is not None
    assert role_service.grant_called_with is not None
    assert role_service.delete_called_with is not None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_role_write_commands() -> None:
    role_service = _RoleServiceStub()
    user_service = _UserServiceStub()
    mediator = provide_system_mediator(role_service=role_service, user_service=user_service)

    add_result = await mediator.send(
        AddRoleCommand(
            role=AddRoleModel(roleName='系统管理员', roleKey='sys_admin', roleSort=1, status='0', menuIds=[1]),
        )
    )
    delete_result = await mediator.send(
        DeleteRoleCommand(
            delete_role=DeleteRoleModel(roleIds='2', updateBy='admin', updateTime=datetime.now()),
        )
    )

    assert add_result.status == 'created'
    assert delete_result.status == 'deleted'
    assert role_service.add_called_with is not None
    assert role_service.delete_called_with is not None


@pytest.mark.asyncio
async def test_role_user_command_handlers_success() -> None:
    role_service = _RoleServiceStub()
    user_service = _UserServiceStub()
    add_handler = AddRoleUserCommandHandler(user_service, role_service)
    cancel_handler = CancelRoleUserCommandHandler(user_service)
    query_db = object()

    grant_result = await add_handler.handle(
        AddRoleUserCommand(
            role_user=CrudUserRoleModel(userIds='1,2', roleId=2),
            query_db=query_db,
            operator='admin',
        )
    )
    cancel_result = await cancel_handler.handle(
        CancelRoleUserCommand(
            role_user=CrudUserRoleModel(userIds='1,2', roleId=2),
            query_db=query_db,
            operator='admin',
        )
    )

    assert grant_result.status == 'granted'
    assert cancel_result.status == 'deleted'
    assert user_service.add_called_with is not None
    assert user_service.delete_called_with is not None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_role_user_commands() -> None:
    role_service = _RoleServiceStub()
    user_service = _UserServiceStub()
    mediator = provide_system_mediator(role_service=role_service, user_service=user_service)
    query_db = object()

    grant_result = await mediator.send(
        AddRoleUserCommand(
            role_user=CrudUserRoleModel(userIds='1,2', roleId=2),
            query_db=query_db,
        )
    )
    cancel_result = await mediator.send(
        CancelRoleUserCommand(
            role_user=CrudUserRoleModel(userIds='1,2', roleId=2),
            query_db=query_db,
        )
    )

    assert grant_result.status == 'granted'
    assert cancel_result.status == 'deleted'
    assert user_service.add_called_with is not None
    assert user_service.delete_called_with is not None

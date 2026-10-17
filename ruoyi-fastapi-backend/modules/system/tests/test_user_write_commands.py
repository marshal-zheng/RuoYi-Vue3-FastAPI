from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from module_admin.entity.vo.user_role_write_vo import UserRolesAssignModel
from module_admin.entity.vo.user_vo import (
    AddUserModel,
    CurrentUserModel,
    DeleteUserModel,
    EditUserModel,
    ResetUserModel,
    UserInfoModel,
)
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import (
    AddUserCommand,
    AssignUserRolesCommand,
    DeleteUserCommand,
    EditUserCommand,
    ImportUsersCommand,
    ResetUserPasswordCommand,
)
from modules.system.application.handlers.command.user_command_handlers import (
    AddUserCommandHandler,
    AssignUserRolesCommandHandler,
    DeleteUserCommandHandler,
    EditUserCommandHandler,
    ImportUsersCommandHandler,
    ResetUserPasswordCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _UserServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None
        self.reset_called_with = None
        self.import_called_with = None
        self.assign_called_with = None
        self.allowed_called_with = []
        self.scope_called_with = []

    async def add_user_services(self, query_db, payload):
        self.add_called_with = (query_db, payload)
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_user_services(self, query_db, payload):
        self.edit_called_with = (query_db, payload)
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_user_services(self, query_db, payload):
        self.delete_called_with = (query_db, payload)
        return _CrudResponse(is_success=True, message='删除成功')

    async def reset_user_services(self, query_db, payload):
        self.reset_called_with = (query_db, payload)
        return _CrudResponse(is_success=True, message='重置成功')

    async def batch_import_user_services(
        self,
        request,
        query_db,
        file,
        update_support,
        current_user,
        user_data_scope_sql,
        dept_data_scope_sql,
    ):
        self.import_called_with = (
            request,
            query_db,
            file,
            update_support,
            current_user,
            user_data_scope_sql,
            dept_data_scope_sql,
        )
        return _CrudResponse(is_success=True, message='导入成功')

    async def assign_user_roles(self, query_db, payload, **scope):
        self.assign_called_with = (query_db, payload)
        return _CrudResponse(is_success=True, message='分配成功')

    async def check_user_allowed_services(self, payload):
        self.allowed_called_with.append(payload)
        return _CrudResponse(is_success=True, message='校验通过')

    async def check_user_data_scope_services(self, query_db, user_id, data_scope_sql):
        self.scope_called_with.append((query_db, user_id, data_scope_sql))
        return _CrudResponse(is_success=True, message='校验通过')


class _DeptServiceStub:
    def __init__(self) -> None:
        self.scope_called_with = []

    async def check_dept_data_scope_services(self, dept_id, data_scope_sql):
        self.scope_called_with.append((dept_id, data_scope_sql))
        return _CrudResponse(is_success=True, message='校验通过')


class _RoleServiceStub:
    def __init__(self) -> None:
        self.scope_called_with = []

    async def check_role_data_scope_services(self, role_ids, data_scope_sql):
        self.scope_called_with.append((role_ids, data_scope_sql))
        return _CrudResponse(is_success=True, message='校验通过')


def _build_current_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=[],
        roles=[],
        user=UserInfoModel(
            userId=1,
            userName='admin',
            nickName='管理员',
            roleIds='1',
            postIds='1',
        ),
    )


@pytest.mark.asyncio
async def test_user_command_handlers_success() -> None:
    user_service = _UserServiceStub()
    dept_service = _DeptServiceStub()
    role_service = _RoleServiceStub()
    query_db = object()
    request = object()
    file = object()
    current_user = _build_current_user()

    add_handler = AddUserCommandHandler(user_service, dept_service, role_service)
    edit_handler = EditUserCommandHandler(user_service, dept_service, role_service)
    delete_handler = DeleteUserCommandHandler(user_service)
    reset_handler = ResetUserPasswordCommandHandler(user_service)
    import_handler = ImportUsersCommandHandler(user_service)
    assign_handler = AssignUserRolesCommandHandler(user_service)

    add_result = await add_handler.handle(
        AddUserCommand(
            query_db=query_db,
            user=AddUserModel(
                deptId=1,
                userName='alice',
                nickName='Alice',
                password='hashed-password',
                status='0',
                roleIds=[1],
                postIds=[1],
            ),
            operator='admin',
        )
    )
    edit_result = await edit_handler.handle(
        EditUserCommand(
            query_db=query_db,
            user=EditUserModel(
                userId=2,
                deptId=1,
                userName='alice2',
                nickName='Alice2',
                status='0',
                roleIds=[1],
                postIds=[1],
            ),
            operator='admin',
        )
    )
    delete_result = await delete_handler.handle(
        DeleteUserCommand(
            query_db=query_db,
            delete_user=DeleteUserModel(userIds='2', updateBy='admin', updateTime=datetime.now()),
            operator='admin',
        )
    )
    reset_result = await reset_handler.handle(
        ResetUserPasswordCommand(
            query_db=query_db,
            reset_user=ResetUserModel(
                userId=2,
                oldPassword='old-pass',
                password='new-pass',
                updateBy='admin',
                updateTime=datetime.now(),
            ),
            operator='admin',
        )
    )
    import_result = await import_handler.handle(
        ImportUsersCommand(
            request=request,
            query_db=query_db,
            file=file,
            update_support=True,
            current_user=current_user,
            user_data_scope_sql=' AND 1=1',
            dept_data_scope_sql=' AND 1=1',
            operator='admin',
        )
    )
    assign_result = await assign_handler.handle(
        AssignUserRolesCommand(
            query_db=query_db,
            user_role=UserRolesAssignModel(userId=2, roleIds=[1, 2]),
            operator='admin',
        )
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert reset_result.status == 'updated'
    assert import_result.status == 'imported'
    assert assign_result.status == 'granted'
    assert user_service.add_called_with is not None
    assert user_service.edit_called_with is not None
    assert user_service.delete_called_with is not None
    assert user_service.reset_called_with is not None
    assert user_service.import_called_with is not None
    assert user_service.assign_called_with is not None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_user_write_commands() -> None:
    user_service = _UserServiceStub()
    dept_service = _DeptServiceStub()
    role_service = _RoleServiceStub()
    mediator = provide_system_mediator(
        user_service=user_service,
        dept_service=dept_service,
        role_service=role_service,
    )
    query_db = object()

    add_result = await mediator.send(
        AddUserCommand(
            query_db=query_db,
            user=AddUserModel(
                deptId=1,
                userName='alice',
                nickName='Alice',
                password='hashed-password',
                status='0',
                roleIds=[1],
                postIds=[1],
            ),
        )
    )
    delete_result = await mediator.send(
        DeleteUserCommand(
            query_db=query_db,
            delete_user=DeleteUserModel(userIds='2', updateBy='admin', updateTime=datetime.now()),
        )
    )

    assert add_result.status == 'created'
    assert delete_result.status == 'deleted'
    assert user_service.add_called_with is not None
    assert user_service.delete_called_with is not None

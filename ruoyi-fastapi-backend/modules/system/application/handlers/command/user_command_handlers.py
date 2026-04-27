"""Command handlers for user operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from module_admin.entity.vo.user_vo import UserModel
from modules.system.application.commands.user_commands import (
    AddUserCommand,
    AssignUserRolesCommand,
    DeleteUserCommand,
    EditUserCommand,
    ImportUsersCommand,
    ResetUserPasswordCommand,
)
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.handlers.command.result_data import command_result_data
from modules.system.application.event_factory import build_system_event

if TYPE_CHECKING:
    from modules.system.application.services.dept_service import DeptService
    from modules.system.application.services.role_service import RoleService
    from modules.system.application.services.user_service import UserService


def _build_metadata(request) -> dict[str, str | None]:
    return {
        'operator': request.operator,
        'trace_id': request.trace_id,
        'request_id': request.request_id,
    }


class AddUserCommandHandler(ICommandHandler[AddUserCommand, dict[str, str]]):
    """Handle user create command."""

    def __init__(
        self,
        user_service: UserService,
        dept_service: DeptService,
        role_service: RoleService,
    ):
        self._user_service = user_service
        self._dept_service = dept_service
        self._role_service = role_service

    async def handle(self, request: AddUserCommand) -> CommandResult[dict[str, str]]:
        request.user.validate_fields()
        if request.enforce_scope_checks:
            await self._dept_service.check_dept_data_scope_services(request.user.dept_id, request.dept_data_scope_sql)
            role_ids = _serialize_role_ids(request.user.role_ids)
            if role_ids:
                await self._role_service.check_role_data_scope_services(role_ids, request.role_data_scope_sql)
        create_result = await self._user_service.add_user_services(request.query_db, request.user)
        event = build_system_event(
            event_type='system.user.created',
            aggregate_type='user',
            aggregate_id=str(request.user.user_id or request.user.user_name or 'unknown'),
            payload={
                'userId': request.user.user_id,
                'userName': request.user.user_name,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=create_result.is_success,
            status='created' if create_result.is_success else 'failed',
            data=command_result_data(create_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class EditUserCommandHandler(ICommandHandler[EditUserCommand, dict[str, str]]):
    """Handle user update command."""

    def __init__(
        self,
        user_service: UserService,
        dept_service: DeptService,
        role_service: RoleService,
    ):
        self._user_service = user_service
        self._dept_service = dept_service
        self._role_service = role_service

    async def handle(self, request: EditUserCommand) -> CommandResult[dict[str, str]]:
        edit_type = request.user.type or ''
        if edit_type not in {'status', 'avatar', 'pwd'}:
            request.user.validate_fields()
        await self._user_service.check_user_allowed_services(request.user)
        if request.enforce_scope_checks:
            await self._user_service.check_user_data_scope_services(
                request.query_db,
                request.user.user_id,
                request.user_data_scope_sql,
            )
            if edit_type not in {'status', 'avatar', 'pwd'}:
                await self._dept_service.check_dept_data_scope_services(
                    request.user.dept_id,
                    request.dept_data_scope_sql,
                )
                role_ids = _serialize_role_ids(request.user.role_ids)
                if role_ids:
                    await self._role_service.check_role_data_scope_services(role_ids, request.role_data_scope_sql)
        update_result = await self._user_service.edit_user_services(request.query_db, request.user)
        event = build_system_event(
            event_type='system.user.updated',
            aggregate_type='user',
            aggregate_id=str(request.user.user_id or request.user.user_name or 'unknown'),
            payload={
                'userId': request.user.user_id,
                'userName': request.user.user_name,
                'type': request.user.type,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=update_result.is_success,
            status='updated' if update_result.is_success else 'failed',
            data=command_result_data(update_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class DeleteUserCommandHandler(ICommandHandler[DeleteUserCommand, dict[str, str]]):
    """Handle user delete command."""

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def handle(self, request: DeleteUserCommand) -> CommandResult[dict[str, str]]:
        user_id_list = [int(item) for item in request.delete_user.user_ids.split(',') if item]
        if request.current_user_id is not None and request.current_user_id in user_id_list:
            raise BusinessException(
                user_message='当前登录用户不能删除',
                error_code=ErrorCode.USER_NOT_FOUND,
                http_status=400,
            )

        for user_id in user_id_list:
            await self._user_service.check_user_allowed_services(UserModel(userId=user_id))
            if request.enforce_scope_checks:
                await self._user_service.check_user_data_scope_services(
                    request.query_db,
                    user_id,
                    request.user_data_scope_sql,
                )
        delete_result = await self._user_service.delete_user_services(request.query_db, request.delete_user)
        event = build_system_event(
            event_type='system.user.deleted',
            aggregate_type='user',
            aggregate_id=str(request.delete_user.user_ids or 'unknown'),
            payload={'user_ids': user_id_list},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data=command_result_data(delete_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class ResetUserPasswordCommandHandler(ICommandHandler[ResetUserPasswordCommand, dict[str, str]]):
    """Handle current user password reset command."""

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def handle(self, request: ResetUserPasswordCommand) -> CommandResult[dict[str, str]]:
        reset_result = await self._user_service.reset_user_services(request.query_db, request.reset_user)
        event = build_system_event(
            event_type='system.user.password_reset',
            aggregate_type='user',
            aggregate_id=str(request.reset_user.user_id or 'unknown'),
            payload={'userId': request.reset_user.user_id},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=reset_result.is_success,
            status='updated' if reset_result.is_success else 'failed',
            data=command_result_data(reset_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class ImportUsersCommandHandler(ICommandHandler[ImportUsersCommand, dict[str, str]]):
    """Handle batch user import command."""

    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def handle(self, request: ImportUsersCommand) -> CommandResult[dict[str, str]]:
        import_result = await self._user_service.batch_import_user_services(
            request.request,
            request.query_db,
            request.file,
            request.update_support,
            request.current_user,
            request.user_data_scope_sql,
            request.dept_data_scope_sql,
        )
        event = build_system_event(
            event_type='system.user.imported',
            aggregate_type='user',
            aggregate_id='batch_import',
            payload={'updateSupport': request.update_support},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=import_result.is_success,
            status='imported' if import_result.is_success else 'failed',
            data=command_result_data(import_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class AssignUserRolesCommandHandler(ICommandHandler[AssignUserRolesCommand, dict[str, str]]):
    """Handle assign roles to user command."""

    def __init__(self, user_service: UserService, role_service: RoleService):
        self._user_service = user_service
        self._role_service = role_service

    async def handle(self, request: AssignUserRolesCommand) -> CommandResult[dict[str, str]]:
        if request.enforce_scope_checks and request.user_role.user_id is not None:
            await self._user_service.check_user_data_scope_services(
                request.query_db,
                request.user_role.user_id,
                request.user_data_scope_sql,
            )
            role_ids = request.user_role.role_ids or ''
            if role_ids:
                await self._role_service.check_role_data_scope_services(role_ids, request.role_data_scope_sql)

        assign_result = await self._user_service.add_user_role_services(request.query_db, request.user_role)
        event = build_system_event(
            event_type='system.user.roles_assigned',
            aggregate_type='user',
            aggregate_id=str(request.user_role.user_id or 'unknown'),
            payload={
                'userId': request.user_role.user_id,
                'roleIds': request.user_role.role_ids,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=assign_result.is_success,
            status='granted' if assign_result.is_success else 'failed',
            data=command_result_data(assign_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


def _serialize_role_ids(role_ids) -> str:
    if not role_ids:
        return ''
    return ','.join(str(item) for item in role_ids)

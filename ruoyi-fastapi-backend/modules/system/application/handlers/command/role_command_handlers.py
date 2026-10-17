"""Command handlers for role operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from module_admin.entity.vo.role_vo import RoleModel
from modules.system.application.commands.role_commands import (
    AddRoleCommand,
    AddRoleUserCommand,
    AssignRoleDataScopeCommand,
    BatchCancelRoleUserCommand,
    CancelRoleUserCommand,
    ChangeRoleStatusCommand,
    DeleteRoleCommand,
    EditRoleCommand,
)
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.event_factory import build_system_event
from modules.system.application.handlers.command.result_data import command_result_data

if TYPE_CHECKING:
    from modules.system.application.services.role_service import RoleService
    from modules.system.application.services.user_role_service import UserRoleService


def _build_metadata(request) -> dict[str, str | None]:
    return {
        'operator': request.operator,
        'trace_id': request.trace_id,
        'request_id': request.request_id,
    }


class AddRoleCommandHandler(ICommandHandler[AddRoleCommand, dict[str, str]]):
    """Handle role create command."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: AddRoleCommand) -> CommandResult[dict[str, str]]:
        request.role.validate_fields()
        create_result = await self._role_service.add_role_services(request.role)
        event = build_system_event(
            event_type='system.role.created',
            aggregate_type='role',
            aggregate_id=str(request.role.role_id or request.role.role_name or 'unknown'),
            payload={
                'roleId': request.role.role_id,
                'roleName': request.role.role_name,
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


class EditRoleCommandHandler(ICommandHandler[EditRoleCommand, dict[str, str]]):
    """Handle role update command."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: EditRoleCommand) -> CommandResult[dict[str, str]]:
        request.role.validate_fields()
        await self._ensure_role_permission(
            role=request.role,
            enforce_data_scope=request.enforce_data_scope,
            data_scope_sql=request.data_scope_sql,
        )
        update_result = await self._role_service.edit_role_services(request.role)
        event = build_system_event(
            event_type='system.role.updated',
            aggregate_type='role',
            aggregate_id=str(request.role.role_id or request.role.role_name or 'unknown'),
            payload={
                'roleId': request.role.role_id,
                'roleName': request.role.role_name,
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

    async def _ensure_role_permission(self, role, *, enforce_data_scope: bool, data_scope_sql: str) -> None:
        await self._role_service.check_role_allowed_services(role)
        if enforce_data_scope:
            await self._role_service.check_role_data_scope_services(str(role.role_id), data_scope_sql)


class AssignRoleDataScopeCommandHandler(ICommandHandler[AssignRoleDataScopeCommand, dict[str, str]]):
    """Handle role data-scope assignment command."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: AssignRoleDataScopeCommand) -> CommandResult[dict[str, str]]:
        await self._role_service.check_role_allowed_services(request.role)
        if request.enforce_data_scope:
            await self._role_service.check_role_data_scope_services(str(request.role.role_id), request.data_scope_sql)
        grant_result = await self._role_service.role_datascope_services(request.role)
        event = build_system_event(
            event_type='system.role.data_scope_assigned',
            aggregate_type='role',
            aggregate_id=str(request.role.role_id or 'unknown'),
            payload={
                'roleId': request.role.role_id,
                'dataScope': request.role.data_scope,
            },
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=grant_result.is_success,
            status='granted' if grant_result.is_success else 'failed',
            data=command_result_data(grant_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class DeleteRoleCommandHandler(ICommandHandler[DeleteRoleCommand, dict[str, str]]):
    """Handle role delete command."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: DeleteRoleCommand) -> CommandResult[dict[str, str]]:
        role_id_list = request.delete_role.role_ids.split(',') if request.delete_role.role_ids else []
        for role_id in role_id_list:
            await self._role_service.check_role_allowed_services(RoleModel(roleId=int(role_id)))
            if request.enforce_data_scope:
                await self._role_service.check_role_data_scope_services(role_id, request.data_scope_sql)

        delete_result = await self._role_service.delete_role_services(request.delete_role)
        event = build_system_event(
            event_type='system.role.deleted',
            aggregate_type='role',
            aggregate_id=str(request.delete_role.role_ids or 'unknown'),
            payload={'roleIds': request.delete_role.role_ids},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data=command_result_data(delete_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class ChangeRoleStatusCommandHandler(ICommandHandler[ChangeRoleStatusCommand, dict[str, str]]):
    """Handle role status change command."""

    def __init__(self, role_service: RoleService):
        self._role_service = role_service

    async def handle(self, request: ChangeRoleStatusCommand) -> CommandResult[dict[str, str]]:
        await self._role_service.check_role_allowed_services(request.role)
        if request.enforce_data_scope:
            await self._role_service.check_role_data_scope_services(str(request.role.role_id), request.data_scope_sql)
        update_result = await self._role_service.edit_role_services(request.role)
        event = build_system_event(
            event_type='system.role.status_changed',
            aggregate_type='role',
            aggregate_id=str(request.role.role_id or 'unknown'),
            payload={
                'roleId': request.role.role_id,
                'status': request.role.status,
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


class AddRoleUserCommandHandler(ICommandHandler[AddRoleUserCommand, dict[str, str]]):
    def __init__(self, user_role_service: UserRoleService):
        self._user_role_service = user_role_service

    async def handle(self, request: AddRoleUserCommand) -> CommandResult[dict[str, str]]:
        result = await self._user_role_service.grant_role_users(
            request.query_db, request.role_user, **_authorization_scope(request)
        )
        return _authorization_result(request, result, 'granted')


class CancelRoleUserCommandHandler(ICommandHandler[CancelRoleUserCommand, dict[str, str]]):
    def __init__(self, user_role_service: UserRoleService):
        self._user_role_service = user_role_service

    async def handle(self, request: CancelRoleUserCommand) -> CommandResult[dict[str, str]]:
        result = await self._user_role_service.revoke_role_user(
            request.query_db, request.role_user, **_authorization_scope(request)
        )
        return _authorization_result(request, result, 'deleted')


class BatchCancelRoleUserCommandHandler(ICommandHandler[BatchCancelRoleUserCommand, dict[str, str]]):
    def __init__(self, user_role_service: UserRoleService):
        self._user_role_service = user_role_service

    async def handle(self, request: BatchCancelRoleUserCommand) -> CommandResult[dict[str, str]]:
        result = await self._user_role_service.revoke_role_users(
            request.query_db, request.role_user, **_authorization_scope(request)
        )
        return _authorization_result(request, result, 'deleted')


def _authorization_scope(request):
    return {
        'enforce_scope_checks': request.enforce_scope_checks,
        'user_data_scope_sql': request.user_data_scope_sql,
        'role_data_scope_sql': request.role_data_scope_sql,
    }


def _authorization_result(request, result, status):
    event = build_system_event(
        event_type='system.role.user_granted' if status == 'granted' else 'system.role.user_revoked',
        aggregate_type='role',
        aggregate_id=str(request.role_user.role_id),
        payload=request.role_user.model_dump(by_alias=True),
        metadata=_build_metadata(request),
    )
    return CommandResult(
        success=result.is_success,
        status=status if result.is_success else 'failed',
        data=command_result_data(result),
        events=(event,),
        metadata=_build_metadata(request),
    )

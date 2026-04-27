"""Command handlers for department operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from modules.system.application.commands.dept_commands import AddDeptCommand, DeleteDeptCommand, EditDeptCommand
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.handlers.command.result_data import command_result_data
from modules.system.application.event_factory import build_system_event

if TYPE_CHECKING:
    from modules.system.application.services.dept_service import DeptService


def _ensure_redis(redis_client):
    if redis_client is None:
        raise BusinessException(
            user_message='缓存服务未初始化',
            error_code=ErrorCode.CACHE_ERROR,
            developer_message='Redis client is missing from command context',
        )
    return redis_client


def _build_metadata(request) -> dict[str, str | None]:
    return {
        'operator': request.operator,
        'trace_id': request.trace_id,
        'request_id': request.request_id,
    }


class AddDeptCommandHandler(ICommandHandler[AddDeptCommand, dict[str, str]]):
    """Handle department create command."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: AddDeptCommand) -> CommandResult[dict[str, str]]:
        _ensure_redis(request.redis_client)
        request.dept.validate_fields()
        create_result = await self._dept_service.add_dept_services(request.dept)
        event = build_system_event(
            event_type='system.dept.created',
            aggregate_type='dept',
            aggregate_id=str(request.dept.dept_id or request.dept.dept_name or 'unknown'),
            payload={
                'deptId': request.dept.dept_id,
                'deptName': request.dept.dept_name,
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


class EditDeptCommandHandler(ICommandHandler[EditDeptCommand, dict[str, str]]):
    """Handle department update command."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: EditDeptCommand) -> CommandResult[dict[str, str]]:
        _ensure_redis(request.redis_client)
        request.dept.validate_fields()
        if request.enforce_data_scope:
            await self._dept_service.check_dept_data_scope_services(request.dept.dept_id, request.data_scope_sql)
        update_result = await self._dept_service.edit_dept_services(request.dept)
        event = build_system_event(
            event_type='system.dept.updated',
            aggregate_type='dept',
            aggregate_id=str(request.dept.dept_id or request.dept.dept_name or 'unknown'),
            payload={
                'deptId': request.dept.dept_id,
                'deptName': request.dept.dept_name,
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


class DeleteDeptCommandHandler(ICommandHandler[DeleteDeptCommand, dict[str, str]]):
    """Handle department delete command."""

    def __init__(self, dept_service: DeptService):
        self._dept_service = dept_service

    async def handle(self, request: DeleteDeptCommand) -> CommandResult[dict[str, str]]:
        _ensure_redis(request.redis_client)
        if request.enforce_data_scope:
            dept_id_list = request.delete_dept.dept_ids.split(',') if request.delete_dept.dept_ids else []
            for dept_id in dept_id_list:
                await self._dept_service.check_dept_data_scope_services(int(dept_id), request.data_scope_sql)
        delete_result = await self._dept_service.delete_dept_services(request.delete_dept)
        event = build_system_event(
            event_type='system.dept.deleted',
            aggregate_type='dept',
            aggregate_id=str(request.delete_dept.dept_ids or 'unknown'),
            payload={'deptIds': request.delete_dept.dept_ids},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data=command_result_data(delete_result),
            events=(event,),
            metadata=_build_metadata(request),
        )

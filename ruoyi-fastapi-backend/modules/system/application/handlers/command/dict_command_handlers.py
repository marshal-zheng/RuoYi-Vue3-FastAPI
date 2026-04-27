"""Command handlers for dictionary operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from modules.system.application.commands.dict_commands import (
    AddDictDataCommand,
    AddDictTypeCommand,
    DeleteDictDataCommand,
    DeleteDictTypeCommand,
    EditDictDataCommand,
    EditDictTypeCommand,
    RefreshDictCacheCommand,
)
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.handlers.command.result_data import command_result_data
from modules.system.application.event_factory import build_system_event

if TYPE_CHECKING:
    from modules.system.application.services import DictDataService, DictTypeService


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


class AddDictTypeCommandHandler(ICommandHandler[AddDictTypeCommand, dict[str, str]]):
    """Handle dictionary type create command."""

    def __init__(self, dict_type_service: DictTypeService):
        self._dict_type_service = dict_type_service

    async def handle(self, request: AddDictTypeCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        request.dict_type.validate_fields()
        create_result = await self._dict_type_service.add_dict_type_services(
            redis_client,
            request.dict_type,
            operator=request.operator,
        )
        event = build_system_event(
            event_type='system.dict_type.created',
            aggregate_type='dict_type',
            aggregate_id=str(request.dict_type.dict_id or request.dict_type.dict_type or 'unknown'),
            payload={
                'dictId': request.dict_type.dict_id,
                'dictType': request.dict_type.dict_type,
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


class EditDictTypeCommandHandler(ICommandHandler[EditDictTypeCommand, dict[str, str]]):
    """Handle dictionary type update command."""

    def __init__(self, dict_type_service: DictTypeService):
        self._dict_type_service = dict_type_service

    async def handle(self, request: EditDictTypeCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        request.dict_type.validate_fields()
        update_result = await self._dict_type_service.edit_dict_type_services(
            redis_client,
            request.dict_type,
            operator=request.operator,
        )
        event = build_system_event(
            event_type='system.dict_type.updated',
            aggregate_type='dict_type',
            aggregate_id=str(request.dict_type.dict_id or request.dict_type.dict_type or 'unknown'),
            payload={
                'dictId': request.dict_type.dict_id,
                'dictType': request.dict_type.dict_type,
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


class DeleteDictTypeCommandHandler(ICommandHandler[DeleteDictTypeCommand, dict[str, str]]):
    """Handle dictionary type delete command."""

    def __init__(self, dict_type_service: DictTypeService):
        self._dict_type_service = dict_type_service

    async def handle(self, request: DeleteDictTypeCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        delete_result = await self._dict_type_service.delete_dict_type_services(redis_client, request.delete_dict_type)
        event = build_system_event(
            event_type='system.dict_type.deleted',
            aggregate_type='dict_type',
            aggregate_id=str(request.delete_dict_type.dict_ids or 'unknown'),
            payload={'dictIds': request.delete_dict_type.dict_ids},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data=command_result_data(delete_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class RefreshDictCacheCommandHandler(ICommandHandler[RefreshDictCacheCommand, dict[str, str]]):
    """Handle dictionary cache refresh command."""

    def __init__(self, dict_type_service: DictTypeService):
        self._dict_type_service = dict_type_service

    async def handle(self, request: RefreshDictCacheCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        refresh_result = await self._dict_type_service.refresh_sys_dict_services(redis_client)
        event = build_system_event(
            event_type='system.dict.cache_refreshed',
            aggregate_type='dict_cache',
            aggregate_id='cache',
            payload={},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=refresh_result.is_success,
            status='refreshed' if refresh_result.is_success else 'failed',
            data=command_result_data(refresh_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class AddDictDataCommandHandler(ICommandHandler[AddDictDataCommand, dict[str, str]]):
    """Handle dictionary data create command."""

    def __init__(self, dict_data_service: DictDataService):
        self._dict_data_service = dict_data_service

    async def handle(self, request: AddDictDataCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        request.dict_data.validate_fields()
        create_result = await self._dict_data_service.add_dict_data_services(
            redis_client,
            request.dict_data,
            operator=request.operator,
        )
        event = build_system_event(
            event_type='system.dict_data.created',
            aggregate_type='dict_data',
            aggregate_id=str(request.dict_data.dict_code or request.dict_data.dict_type or 'unknown'),
            payload={
                'dictCode': request.dict_data.dict_code,
                'dictType': request.dict_data.dict_type,
                'dictValue': request.dict_data.dict_value,
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


class EditDictDataCommandHandler(ICommandHandler[EditDictDataCommand, dict[str, str]]):
    """Handle dictionary data update command."""

    def __init__(self, dict_data_service: DictDataService):
        self._dict_data_service = dict_data_service

    async def handle(self, request: EditDictDataCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        request.dict_data.validate_fields()
        update_result = await self._dict_data_service.edit_dict_data_services(
            redis_client,
            request.dict_data,
            operator=request.operator,
        )
        event = build_system_event(
            event_type='system.dict_data.updated',
            aggregate_type='dict_data',
            aggregate_id=str(request.dict_data.dict_code or request.dict_data.dict_type or 'unknown'),
            payload={
                'dictCode': request.dict_data.dict_code,
                'dictType': request.dict_data.dict_type,
                'dictValue': request.dict_data.dict_value,
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


class DeleteDictDataCommandHandler(ICommandHandler[DeleteDictDataCommand, dict[str, str]]):
    """Handle dictionary data delete command."""

    def __init__(self, dict_data_service: DictDataService):
        self._dict_data_service = dict_data_service

    async def handle(self, request: DeleteDictDataCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        delete_result = await self._dict_data_service.delete_dict_data_services(redis_client, request.delete_dict_data)
        event = build_system_event(
            event_type='system.dict_data.deleted',
            aggregate_type='dict_data',
            aggregate_id=str(request.delete_dict_data.dict_codes or 'unknown'),
            payload={'dictCodes': request.delete_dict_data.dict_codes},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data=command_result_data(delete_result),
            events=(event,),
            metadata=_build_metadata(request),
        )

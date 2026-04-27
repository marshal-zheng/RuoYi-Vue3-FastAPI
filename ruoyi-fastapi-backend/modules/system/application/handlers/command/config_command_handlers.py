"""Command handlers for system configuration operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from modules.system.application.commands.config_commands import (
    AddConfigCommand,
    DeleteConfigCommand,
    EditConfigCommand,
    RefreshConfigCacheCommand,
)
from modules.system.application.contracts import CommandResult, ICommandHandler
from modules.system.application.handlers.command.result_data import command_result_data
from modules.system.application.event_factory import build_system_event

if TYPE_CHECKING:
    from modules.system.application.services.config_service import ConfigService


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


class AddConfigCommandHandler(ICommandHandler[AddConfigCommand, dict[str, str]]):
    """Handle config create command."""

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service

    async def handle(self, request: AddConfigCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        request.config.validate_fields()
        create_result = await self._config_service.add_config_services(redis_client, request.config)
        event = build_system_event(
            event_type='system.config.created',
            aggregate_type='config',
            aggregate_id=str(request.config.config_key or request.config.config_id or 'unknown'),
            payload={
                'configKey': request.config.config_key,
                'configName': request.config.config_name,
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


class EditConfigCommandHandler(ICommandHandler[EditConfigCommand, dict[str, str]]):
    """Handle config update command."""

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service

    async def handle(self, request: EditConfigCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        request.config.validate_fields()
        update_result = await self._config_service.edit_config_services(redis_client, request.config)
        event = build_system_event(
            event_type='system.config.updated',
            aggregate_type='config',
            aggregate_id=str(request.config.config_id or request.config.config_key or 'unknown'),
            payload={
                'configId': request.config.config_id,
                'configKey': request.config.config_key,
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


class DeleteConfigCommandHandler(ICommandHandler[DeleteConfigCommand, dict[str, str]]):
    """Handle config delete command."""

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service

    async def handle(self, request: DeleteConfigCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)
        delete_result = await self._config_service.delete_config_services(redis_client, request.delete_config)
        event = build_system_event(
            event_type='system.config.deleted',
            aggregate_type='config',
            aggregate_id=str(request.delete_config.config_ids or 'unknown'),
            payload={'configIds': request.delete_config.config_ids},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=delete_result.is_success,
            status='deleted' if delete_result.is_success else 'failed',
            data=command_result_data(delete_result),
            events=(event,),
            metadata=_build_metadata(request),
        )


class RefreshConfigCacheCommandHandler(ICommandHandler[RefreshConfigCacheCommand, dict[str, str]]):
    """Handle cache refresh command via config service."""

    def __init__(self, config_service: ConfigService):
        self._config_service = config_service

    async def handle(self, request: RefreshConfigCacheCommand) -> CommandResult[dict[str, str]]:
        redis_client = _ensure_redis(request.redis_client)

        await self._config_service.init_cache_sys_config_services(redis_client)
        event = build_system_event(
            event_type='system.config.cache_refreshed',
            aggregate_type='config',
            aggregate_id='cache',
            payload={},
            metadata=_build_metadata(request),
        )
        return CommandResult(
            success=True,
            status='refreshed',
            data={},
            events=(event,),
            metadata=_build_metadata(request),
        )

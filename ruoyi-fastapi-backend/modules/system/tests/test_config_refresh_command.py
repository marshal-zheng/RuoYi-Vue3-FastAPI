from __future__ import annotations

import pytest

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import RefreshConfigCacheCommand
from modules.system.application.handlers.command.config_command_handlers import RefreshConfigCacheCommandHandler


class _ConfigServiceStub:
    def __init__(self) -> None:
        self.called_with = None

    async def init_cache_sys_config_services(self, redis_client):
        self.called_with = redis_client


@pytest.mark.asyncio
async def test_refresh_config_cache_command_handler_success() -> None:
    config_service = _ConfigServiceStub()
    handler = RefreshConfigCacheCommandHandler(config_service)

    command = RefreshConfigCacheCommand(
        redis_client=object(),
        operator='admin',
        trace_id='trace-1',
        request_id='req-1',
    )

    result = await handler.handle(command)

    assert result.success is True
    assert result.status == 'refreshed'
    assert result.data == {}
    assert result.metadata['operator'] == 'admin'
    assert result.metadata['trace_id'] == 'trace-1'
    assert result.metadata['request_id'] == 'req-1'
    assert len(result.events) == 1
    assert result.events[0].event_type == 'system.config.cache_refreshed'
    assert config_service.called_with is command.redis_client


@pytest.mark.asyncio
async def test_refresh_config_cache_command_handler_raises_when_redis_missing() -> None:
    config_service = _ConfigServiceStub()
    handler = RefreshConfigCacheCommandHandler(config_service)

    with pytest.raises(BusinessException) as exc_info:
        await handler.handle(RefreshConfigCacheCommand(redis_client=None))

    assert exc_info.value.error_code == ErrorCode.CACHE_ERROR
    assert config_service.called_with is None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_refresh_command() -> None:
    config_service = _ConfigServiceStub()
    mediator = provide_system_mediator(config_service=config_service)

    redis_client = object()
    result = await mediator.send(RefreshConfigCacheCommand(redis_client=redis_client, operator='tester'))

    assert result.success is True
    assert result.data == {}
    assert result.status == 'refreshed'
    assert result.metadata['operator'] == 'tester'
    assert config_service.called_with is redis_client

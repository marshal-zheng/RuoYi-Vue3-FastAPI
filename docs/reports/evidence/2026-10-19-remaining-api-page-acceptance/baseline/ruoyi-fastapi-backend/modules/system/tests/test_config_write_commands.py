from __future__ import annotations

from dataclasses import dataclass

import pytest

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from module_admin.entity.vo.config_vo import ConfigModel, DeleteConfigModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddConfigCommand, DeleteConfigCommand, EditConfigCommand
from modules.system.application.handlers.command.config_command_handlers import (
    AddConfigCommandHandler,
    DeleteConfigCommandHandler,
    EditConfigCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _ConfigServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None

    async def add_config_services(self, redis_client, config):
        self.add_called_with = (redis_client, config)
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_config_services(self, redis_client, config):
        self.edit_called_with = (redis_client, config)
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_config_services(self, redis_client, delete_config):
        self.delete_called_with = (redis_client, delete_config)
        return _CrudResponse(is_success=True, message='删除成功')


@pytest.mark.asyncio
async def test_add_config_command_handler_success() -> None:
    config_service = _ConfigServiceStub()
    handler = AddConfigCommandHandler(config_service)
    redis_client = object()
    config = ConfigModel(configName='测试参数', configKey='test.key', configValue='1', configType='N')

    result = await handler.handle(
        AddConfigCommand(
            config=config,
            redis_client=redis_client,
            operator='admin',
            trace_id='trace-1',
            request_id='req-1',
        )
    )

    assert result.success is True
    assert result.status == 'created'
    assert result.data == {}
    assert result.metadata['operator'] == 'admin'
    assert config_service.add_called_with == (redis_client, config)


@pytest.mark.asyncio
async def test_edit_config_command_handler_success() -> None:
    config_service = _ConfigServiceStub()
    handler = EditConfigCommandHandler(config_service)
    redis_client = object()
    config = ConfigModel(configId=1, configName='测试参数', configKey='test.key', configValue='2', configType='N')

    result = await handler.handle(
        EditConfigCommand(
            config=config,
            redis_client=redis_client,
            operator='admin',
        )
    )

    assert result.success is True
    assert result.status == 'updated'
    assert result.data == {}
    assert config_service.edit_called_with == (redis_client, config)


@pytest.mark.asyncio
async def test_delete_config_command_handler_success() -> None:
    config_service = _ConfigServiceStub()
    handler = DeleteConfigCommandHandler(config_service)
    redis_client = object()
    delete_config = DeleteConfigModel(configIds='1,2')

    result = await handler.handle(
        DeleteConfigCommand(
            delete_config=delete_config,
            redis_client=redis_client,
            operator='admin',
        )
    )

    assert result.success is True
    assert result.status == 'deleted'
    assert result.data == {}
    assert config_service.delete_called_with == (redis_client, delete_config)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('handler_type', 'command_factory'),
    [
        (
            AddConfigCommandHandler,
            lambda: AddConfigCommand(
                config=ConfigModel(configName='测试参数', configKey='test.key', configValue='1', configType='N'),
                redis_client=None,
            ),
        ),
        (
            EditConfigCommandHandler,
            lambda: EditConfigCommand(
                config=ConfigModel(
                    configId=1,
                    configName='测试参数',
                    configKey='test.key',
                    configValue='2',
                    configType='N',
                ),
                redis_client=None,
            ),
        ),
        (
            DeleteConfigCommandHandler,
            lambda: DeleteConfigCommand(delete_config=DeleteConfigModel(configIds='1'), redis_client=None),
        ),
    ],
)
async def test_write_config_command_handlers_raise_when_redis_missing(handler_type, command_factory) -> None:
    config_service = _ConfigServiceStub()
    handler = handler_type(config_service)

    with pytest.raises(BusinessException) as exc_info:
        await handler.handle(command_factory())

    assert exc_info.value.error_code == ErrorCode.CACHE_ERROR


@pytest.mark.asyncio
async def test_system_mediator_dispatches_config_write_commands() -> None:
    config_service = _ConfigServiceStub()
    mediator = provide_system_mediator(config_service=config_service)
    redis_client = object()

    add_result = await mediator.send(
        AddConfigCommand(
            config=ConfigModel(configName='测试参数', configKey='test.key', configValue='1', configType='N'),
            redis_client=redis_client,
        )
    )
    edit_result = await mediator.send(
        EditConfigCommand(
            config=ConfigModel(
                configId=1,
                configName='测试参数',
                configKey='test.key',
                configValue='2',
                configType='N',
            ),
            redis_client=redis_client,
        )
    )
    delete_result = await mediator.send(
        DeleteConfigCommand(
            delete_config=DeleteConfigModel(configIds='1'),
            redis_client=redis_client,
        )
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert config_service.add_called_with is not None
    assert config_service.edit_called_with is not None
    assert config_service.delete_called_with is not None

from __future__ import annotations

from dataclasses import dataclass

import pytest

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from module_admin.entity.vo.dict_vo import DeleteDictDataModel, DeleteDictTypeModel, DictDataModel, DictTypeModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import (
    AddDictDataCommand,
    AddDictTypeCommand,
    DeleteDictDataCommand,
    DeleteDictTypeCommand,
    EditDictDataCommand,
    EditDictTypeCommand,
    RefreshDictCacheCommand,
)
from modules.system.application.handlers.command.dict_command_handlers import (
    AddDictDataCommandHandler,
    AddDictTypeCommandHandler,
    DeleteDictDataCommandHandler,
    DeleteDictTypeCommandHandler,
    EditDictDataCommandHandler,
    EditDictTypeCommandHandler,
    RefreshDictCacheCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _DictTypeServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None
        self.refresh_called_with = None

    async def add_dict_type_services(self, redis_client, payload, operator=None):
        self.add_called_with = (redis_client, payload, operator)
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_dict_type_services(self, redis_client, payload, operator=None):
        self.edit_called_with = (redis_client, payload, operator)
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_dict_type_services(self, redis_client, payload):
        self.delete_called_with = (redis_client, payload)
        return _CrudResponse(is_success=True, message='删除成功')

    async def refresh_sys_dict_services(self, redis_client):
        self.refresh_called_with = redis_client
        return _CrudResponse(is_success=True, message='刷新成功')


class _DictDataServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None

    async def add_dict_data_services(self, redis_client, payload, operator=None):
        self.add_called_with = (redis_client, payload, operator)
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_dict_data_services(self, redis_client, payload, operator=None):
        self.edit_called_with = (redis_client, payload, operator)
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_dict_data_services(self, redis_client, payload):
        self.delete_called_with = (redis_client, payload)
        return _CrudResponse(is_success=True, message='删除成功')


class _ConfigServiceStub:
    async def init_cache_sys_config_services(self, redis_client):
        _ = redis_client


@pytest.mark.asyncio
async def test_dict_type_command_handlers_success() -> None:
    dict_type_service = _DictTypeServiceStub()
    add_handler = AddDictTypeCommandHandler(dict_type_service)
    edit_handler = EditDictTypeCommandHandler(dict_type_service)
    delete_handler = DeleteDictTypeCommandHandler(dict_type_service)
    refresh_handler = RefreshDictCacheCommandHandler(dict_type_service)

    redis_client = object()
    dict_type = DictTypeModel(dictName='用户状态', dictType='sys_user_status', status='0')

    add_result = await add_handler.handle(
        AddDictTypeCommand(dict_type=dict_type, redis_client=redis_client, operator='admin')
    )
    edit_result = await edit_handler.handle(
        EditDictTypeCommand(
            dict_type=DictTypeModel(dictId=1, dictName='用户状态', dictType='sys_user_status', status='0'),
            redis_client=redis_client,
            operator='admin',
        )
    )
    delete_result = await delete_handler.handle(
        DeleteDictTypeCommand(delete_dict_type=DeleteDictTypeModel(dictIds='1'), redis_client=redis_client)
    )
    refresh_result = await refresh_handler.handle(RefreshDictCacheCommand(redis_client=redis_client))

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert refresh_result.status == 'refreshed'
    assert dict_type_service.add_called_with is not None
    assert dict_type_service.edit_called_with is not None
    assert dict_type_service.delete_called_with is not None
    assert dict_type_service.refresh_called_with is redis_client


@pytest.mark.asyncio
async def test_dict_data_command_handlers_success() -> None:
    dict_data_service = _DictDataServiceStub()
    add_handler = AddDictDataCommandHandler(dict_data_service)
    edit_handler = EditDictDataCommandHandler(dict_data_service)
    delete_handler = DeleteDictDataCommandHandler(dict_data_service)

    redis_client = object()
    dict_data = DictDataModel(dictType='sys_user_status', dictLabel='正常', dictValue='0', status='0')

    add_result = await add_handler.handle(
        AddDictDataCommand(dict_data=dict_data, redis_client=redis_client, operator='admin')
    )
    edit_result = await edit_handler.handle(
        EditDictDataCommand(
            dict_data=DictDataModel(
                dictCode=1,
                dictType='sys_user_status',
                dictLabel='正常',
                dictValue='0',
                status='0',
            ),
            redis_client=redis_client,
            operator='admin',
        )
    )
    delete_result = await delete_handler.handle(
        DeleteDictDataCommand(delete_dict_data=DeleteDictDataModel(dictCodes='1'), redis_client=redis_client)
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert dict_data_service.add_called_with is not None
    assert dict_data_service.edit_called_with is not None
    assert dict_data_service.delete_called_with is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('handler_type', 'command_factory'),
    [
        (
            AddDictTypeCommandHandler,
            lambda: AddDictTypeCommand(
                dict_type=DictTypeModel(dictName='用户状态', dictType='sys_user_status', status='0'),
                redis_client=None,
            ),
        ),
        (
            EditDictTypeCommandHandler,
            lambda: EditDictTypeCommand(
                dict_type=DictTypeModel(dictId=1, dictName='用户状态', dictType='sys_user_status', status='0'),
                redis_client=None,
            ),
        ),
        (
            DeleteDictTypeCommandHandler,
            lambda: DeleteDictTypeCommand(delete_dict_type=DeleteDictTypeModel(dictIds='1'), redis_client=None),
        ),
        (
            RefreshDictCacheCommandHandler,
            lambda: RefreshDictCacheCommand(redis_client=None),
        ),
    ],
)
async def test_dict_type_handlers_raise_when_redis_missing(handler_type, command_factory) -> None:
    dict_type_service = _DictTypeServiceStub()
    handler = handler_type(dict_type_service)

    with pytest.raises(BusinessException) as exc_info:
        await handler.handle(command_factory())

    assert exc_info.value.error_code == ErrorCode.CACHE_ERROR


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('handler_type', 'command_factory'),
    [
        (
            AddDictDataCommandHandler,
            lambda: AddDictDataCommand(
                dict_data=DictDataModel(dictType='sys_user_status', dictLabel='正常', dictValue='0', status='0'),
                redis_client=None,
            ),
        ),
        (
            EditDictDataCommandHandler,
            lambda: EditDictDataCommand(
                dict_data=DictDataModel(
                    dictCode=1,
                    dictType='sys_user_status',
                    dictLabel='正常',
                    dictValue='0',
                    status='0',
                ),
                redis_client=None,
            ),
        ),
        (
            DeleteDictDataCommandHandler,
            lambda: DeleteDictDataCommand(delete_dict_data=DeleteDictDataModel(dictCodes='1'), redis_client=None),
        ),
    ],
)
async def test_dict_data_handlers_raise_when_redis_missing(handler_type, command_factory) -> None:
    dict_data_service = _DictDataServiceStub()
    handler = handler_type(dict_data_service)

    with pytest.raises(BusinessException) as exc_info:
        await handler.handle(command_factory())

    assert exc_info.value.error_code == ErrorCode.CACHE_ERROR


@pytest.mark.asyncio
async def test_system_mediator_dispatches_dict_write_commands() -> None:
    dict_type_service = _DictTypeServiceStub()
    dict_data_service = _DictDataServiceStub()
    mediator = provide_system_mediator(
        config_service=_ConfigServiceStub(),
        dict_type_service=dict_type_service,
        dict_data_service=dict_data_service,
    )

    redis_client = object()

    add_type_result = await mediator.send(
        AddDictTypeCommand(
            dict_type=DictTypeModel(dictName='用户状态', dictType='sys_user_status', status='0'),
            redis_client=redis_client,
        )
    )
    add_data_result = await mediator.send(
        AddDictDataCommand(
            dict_data=DictDataModel(dictType='sys_user_status', dictLabel='正常', dictValue='0', status='0'),
            redis_client=redis_client,
        )
    )

    assert add_type_result.status == 'created'
    assert add_data_result.status == 'created'
    assert dict_type_service.add_called_with is not None
    assert dict_data_service.add_called_with is not None

from __future__ import annotations

from dataclasses import dataclass

import pytest

from config.error_codes import ErrorCode
from exceptions.exception import BusinessException
from module_admin.entity.vo.dept_vo import DeleteDeptModel, DeptModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddDeptCommand, DeleteDeptCommand, EditDeptCommand
from modules.system.application.handlers.command.dept_command_handlers import (
    AddDeptCommandHandler,
    DeleteDeptCommandHandler,
    EditDeptCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _DeptServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None
        self.scope_called_with = []

    async def add_dept_services(self, payload, **scope):
        self.add_scope = scope
        self.add_called_with = payload
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_dept_services(self, payload, **scope):
        self.edit_scope = scope
        self.edit_called_with = payload
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_dept_services(self, payload):
        self.delete_called_with = payload
        return _CrudResponse(is_success=True, message='删除成功')

    async def check_dept_data_scope_services(self, dept_id, data_scope_sql):
        self.scope_called_with.append((dept_id, data_scope_sql))
        return _CrudResponse(is_success=True, message='校验通过')


class _ConfigServiceStub:
    async def init_cache_sys_config_services(self, redis_client):
        _ = redis_client


class _DictTypeServiceStub:
    async def add_dict_type_services(self, redis_client, payload, operator=None):
        _ = redis_client, payload, operator

    async def edit_dict_type_services(self, redis_client, payload, operator=None):
        _ = redis_client, payload, operator

    async def delete_dict_type_services(self, redis_client, payload):
        _ = redis_client, payload

    async def refresh_sys_dict_services(self, redis_client):
        _ = redis_client


class _DictDataServiceStub:
    async def add_dict_data_services(self, redis_client, payload, operator=None):
        _ = redis_client, payload, operator

    async def edit_dict_data_services(self, redis_client, payload, operator=None):
        _ = redis_client, payload, operator

    async def delete_dict_data_services(self, redis_client, payload):
        _ = redis_client, payload


@pytest.mark.asyncio
async def test_dept_command_handlers_success() -> None:
    dept_service = _DeptServiceStub()
    add_handler = AddDeptCommandHandler(dept_service)
    edit_handler = EditDeptCommandHandler(dept_service)
    delete_handler = DeleteDeptCommandHandler(dept_service)
    redis_client = object()

    add_result = await add_handler.handle(
        AddDeptCommand(
            dept=DeptModel(
                parentId=1,
                deptName='研发部',
                orderNum=1,
                leader='张三',
                phone='13800000000',
                email='dev@example.com',
                status='0',
            ),
            redis_client=redis_client,
            operator='admin',
        )
    )
    edit_result = await edit_handler.handle(
        EditDeptCommand(
            dept=DeptModel(
                deptId=2,
                parentId=1,
                deptName='研发部',
                orderNum=1,
                leader='张三',
                phone='13800000000',
                email='dev@example.com',
                status='0',
            ),
            redis_client=redis_client,
            operator='admin',
        )
    )
    delete_result = await delete_handler.handle(
        DeleteDeptCommand(
            delete_dept=DeleteDeptModel(deptIds='2'),
            redis_client=redis_client,
            operator='admin',
        )
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert dept_service.add_called_with is not None
    assert dept_service.edit_called_with is not None
    assert dept_service.delete_called_with is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('handler_type', 'command_factory'),
    [
        (
            AddDeptCommandHandler,
            lambda: AddDeptCommand(
                dept=DeptModel(
                    parentId=1,
                    deptName='研发部',
                    orderNum=1,
                    leader='张三',
                    phone='13800000000',
                    email='dev@example.com',
                    status='0',
                ),
                redis_client=None,
            ),
        ),
        (
            EditDeptCommandHandler,
            lambda: EditDeptCommand(
                dept=DeptModel(
                    deptId=2,
                    parentId=1,
                    deptName='研发部',
                    orderNum=1,
                    leader='张三',
                    phone='13800000000',
                    email='dev@example.com',
                    status='0',
                ),
                redis_client=None,
            ),
        ),
        (
            DeleteDeptCommandHandler,
            lambda: DeleteDeptCommand(delete_dept=DeleteDeptModel(deptIds='2'), redis_client=None),
        ),
    ],
)
async def test_dept_command_handlers_raise_when_redis_missing(handler_type, command_factory) -> None:
    dept_service = _DeptServiceStub()
    handler = handler_type(dept_service)

    with pytest.raises(BusinessException) as exc_info:
        await handler.handle(command_factory())

    assert exc_info.value.error_code == ErrorCode.CACHE_ERROR


@pytest.mark.asyncio
async def test_system_mediator_dispatches_dept_write_commands() -> None:
    dept_service = _DeptServiceStub()
    mediator = provide_system_mediator(
        config_service=_ConfigServiceStub(),
        dept_service=dept_service,
        dict_type_service=_DictTypeServiceStub(),
        dict_data_service=_DictDataServiceStub(),
    )
    redis_client = object()

    add_result = await mediator.send(
        AddDeptCommand(
            dept=DeptModel(
                parentId=1,
                deptName='研发部',
                orderNum=1,
                leader='张三',
                phone='13800000000',
                email='dev@example.com',
                status='0',
            ),
            redis_client=redis_client,
        )
    )
    delete_result = await mediator.send(
        DeleteDeptCommand(
            delete_dept=DeleteDeptModel(deptIds='2'),
            redis_client=redis_client,
        )
    )

    assert add_result.status == 'created'
    assert delete_result.status == 'deleted'
    assert dept_service.add_called_with is not None
    assert dept_service.delete_called_with is not None


@pytest.mark.asyncio
async def test_dept_command_handlers_enforce_data_scope_when_enabled() -> None:
    dept_service = _DeptServiceStub()
    edit_handler = EditDeptCommandHandler(dept_service)
    delete_handler = DeleteDeptCommandHandler(dept_service)
    redis_client = object()

    await edit_handler.handle(
        EditDeptCommand(
            dept=DeptModel(
                deptId=2,
                parentId=1,
                deptName='研发部',
                orderNum=1,
                leader='张三',
                phone='13800000000',
                email='dev@example.com',
                status='0',
            ),
            redis_client=redis_client,
            enforce_data_scope=True,
            data_scope_sql=' AND dept_id in (2)',
        )
    )
    await delete_handler.handle(
        DeleteDeptCommand(
            delete_dept=DeleteDeptModel(deptIds='2,3'),
            redis_client=redis_client,
            enforce_data_scope=True,
            data_scope_sql=' AND dept_id in (2,3)',
        )
    )

    assert dept_service.scope_called_with == [
        (2, ' AND dept_id in (2)'),
        (2, ' AND dept_id in (2,3)'),
        (3, ' AND dept_id in (2,3)'),
    ]

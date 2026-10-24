from __future__ import annotations

from dataclasses import dataclass

import pytest

from module_admin.entity.vo.menu_vo import DeleteMenuModel, MenuModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.commands import AddMenuCommand, DeleteMenuCommand, EditMenuCommand
from modules.system.application.handlers.command.menu_command_handlers import (
    AddMenuCommandHandler,
    DeleteMenuCommandHandler,
    EditMenuCommandHandler,
)


@dataclass
class _CrudResponse:
    is_success: bool
    message: str


class _MenuServiceStub:
    def __init__(self) -> None:
        self.add_called_with = None
        self.edit_called_with = None
        self.delete_called_with = None

    async def add_menu_services(self, payload):
        self.add_called_with = payload
        return _CrudResponse(is_success=True, message='新增成功')

    async def edit_menu_services(self, payload):
        self.edit_called_with = payload
        return _CrudResponse(is_success=True, message='更新成功')

    async def delete_menu_services(self, payload):
        self.delete_called_with = payload
        return _CrudResponse(is_success=True, message='删除成功')


@pytest.mark.asyncio
async def test_menu_command_handlers_success() -> None:
    menu_service = _MenuServiceStub()
    add_handler = AddMenuCommandHandler(menu_service)
    edit_handler = EditMenuCommandHandler(menu_service)
    delete_handler = DeleteMenuCommandHandler(menu_service)
    redis_client = object()

    add_result = await add_handler.handle(
        AddMenuCommand(
            menu=MenuModel(
                menuName='系统管理',
                parentId=0,
                orderNum=1,
                path='/system',
                component='Layout',
                menuType='C',
                perms='system:menu:list',
                isFrame='1',
                isCache='1',
                visible='0',
                status='0',
            ),
            redis_client=redis_client,
            operator='admin',
        )
    )
    edit_result = await edit_handler.handle(
        EditMenuCommand(
            menu=MenuModel(
                menuId=1,
                menuName='系统管理',
                parentId=0,
                orderNum=1,
                path='/system',
                component='Layout',
                menuType='C',
                perms='system:menu:list',
                isFrame='1',
                isCache='1',
                visible='0',
                status='0',
            ),
            redis_client=redis_client,
            operator='admin',
        )
    )
    delete_result = await delete_handler.handle(
        DeleteMenuCommand(
            delete_menu=DeleteMenuModel(menuIds='1'),
            redis_client=redis_client,
            operator='admin',
        )
    )

    assert add_result.status == 'created'
    assert edit_result.status == 'updated'
    assert delete_result.status == 'deleted'
    assert menu_service.add_called_with is not None
    assert menu_service.edit_called_with is not None
    assert menu_service.delete_called_with is not None


@pytest.mark.asyncio
async def test_system_mediator_dispatches_menu_write_commands() -> None:
    menu_service = _MenuServiceStub()
    mediator = provide_system_mediator(menu_service=menu_service)
    redis_client = object()

    add_result = await mediator.send(
        AddMenuCommand(
            menu=MenuModel(
                menuName='系统管理',
                parentId=0,
                orderNum=1,
                path='/system',
                component='Layout',
                menuType='C',
                perms='system:menu:list',
                isFrame='1',
                isCache='1',
                visible='0',
                status='0',
            ),
            redis_client=redis_client,
        )
    )
    delete_result = await mediator.send(
        DeleteMenuCommand(
            delete_menu=DeleteMenuModel(menuIds='1'),
            redis_client=redis_client,
        )
    )

    assert add_result.status == 'created'
    assert delete_result.status == 'deleted'
    assert menu_service.add_called_with is not None
    assert menu_service.delete_called_with is not None

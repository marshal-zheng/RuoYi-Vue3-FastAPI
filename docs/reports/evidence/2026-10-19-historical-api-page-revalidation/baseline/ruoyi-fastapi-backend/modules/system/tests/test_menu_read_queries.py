from __future__ import annotations

import pytest

from module_admin.entity.vo.menu_vo import MenuQueryModel
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.system.api.dependencies import provide_system_mediator
from modules.system.application.handlers.query.menu_query_handlers import (
    GetMenuDetailQueryHandler,
    GetMenuListQueryHandler,
    GetMenuTreeQueryHandler,
    GetRoleMenuTreeQueryHandler,
)
from modules.system.application.queries import (
    GetMenuDetailQuery,
    GetMenuListQuery,
    GetMenuTreeQuery,
    GetRoleMenuTreeQuery,
)
from modules.system.application.read_models import (
    MenuItemReadModel,
    MenuTreeNodeReadModel,
    RoleMenuTreeReadModel,
)


def _build_current_user(*, is_admin: bool = True) -> CurrentUserModel:
    return CurrentUserModel(
        permissions=[],
        roles=['admin'] if is_admin else ['common'],
        user=UserInfoModel(
            userId=1 if is_admin else 100,
            userName='admin' if is_admin else 'tester',
            admin=is_admin,
        ),
    )


class _MenuServiceStub:
    def __init__(self) -> None:
        self.tree_called_with = None
        self.role_tree_called_with = None
        self.list_called_with = None
        self.detail_called_with = None

    async def get_menu_tree_services(self, current_user):
        self.tree_called_with = current_user
        return [
            {
                'id': 1,
                'label': '系统管理',
                'parentId': 0,
                'children': [
                    {
                        'id': 2,
                        'label': '用户管理',
                        'parentId': 1,
                    }
                ],
            }
        ]

    async def get_role_menu_tree_services(self, role_id, current_user):
        self.role_tree_called_with = (role_id, current_user)
        return {
            'menus': [
                {
                    'id': 1,
                    'label': '系统管理',
                    'parentId': 0,
                }
            ],
            'checkedKeys': [1],
        }

    async def get_menu_list_services(self, query, current_user):
        self.list_called_with = (query, current_user)
        return [
            {
                'menuId': 1,
                'menuName': '系统管理',
                'parentId': 0,
                'menuType': 'M',
                'visible': '0',
                'status': '0',
            }
        ]

    async def menu_detail_services(self, menu_id):
        self.detail_called_with = menu_id
        return {
            'menuId': menu_id,
            'menuName': '系统管理',
            'parentId': 0,
            'menuType': 'M',
            'visible': '0',
            'status': '0',
        }


@pytest.mark.asyncio
async def test_menu_query_handlers_success() -> None:
    menu_service = _MenuServiceStub()
    current_user = _build_current_user()

    tree_handler = GetMenuTreeQueryHandler(menu_service)
    role_tree_handler = GetRoleMenuTreeQueryHandler(menu_service)
    list_handler = GetMenuListQueryHandler(menu_service)
    detail_handler = GetMenuDetailQueryHandler(menu_service)

    tree_result = await tree_handler.handle(GetMenuTreeQuery(current_user=current_user, operator='admin'))
    role_tree_result = await role_tree_handler.handle(
        GetRoleMenuTreeQuery(role_id=1, current_user=current_user, operator='admin')
    )
    list_result = await list_handler.handle(
        GetMenuListQuery(query=MenuQueryModel(menuName='系统'), current_user=current_user, operator='admin')
    )
    detail_result = await detail_handler.handle(GetMenuDetailQuery(menu_id=1, operator='admin'))

    assert isinstance(tree_result[0], MenuTreeNodeReadModel)
    assert isinstance(role_tree_result, RoleMenuTreeReadModel)
    assert isinstance(list_result[0], MenuItemReadModel)
    assert isinstance(detail_result, MenuItemReadModel)
    assert role_tree_result.checked_keys == [1]
    assert menu_service.tree_called_with is current_user
    assert menu_service.role_tree_called_with == (1, current_user)


@pytest.mark.asyncio
async def test_system_mediator_dispatches_menu_read_queries() -> None:
    menu_service = _MenuServiceStub()
    current_user = _build_current_user()
    mediator = provide_system_mediator(menu_service=menu_service)

    tree_result = await mediator.query(GetMenuTreeQuery(current_user=current_user))
    list_result = await mediator.query(
        GetMenuListQuery(
            query=MenuQueryModel(menuName='系统'),
            current_user=current_user,
        )
    )
    detail_result = await mediator.query(GetMenuDetailQuery(menu_id=1))

    assert isinstance(tree_result[0], MenuTreeNodeReadModel)
    assert isinstance(list_result[0], MenuItemReadModel)
    assert isinstance(detail_result, MenuItemReadModel)
    assert detail_result.menu_id == 1

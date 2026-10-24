"""Query handlers for menu operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from modules.system.application.contracts import IQueryHandler
from modules.system.application.queries.menu_queries import (
    GetMenuDetailQuery,
    GetMenuListQuery,
    GetMenuTreeQuery,
    GetRoleMenuTreeQuery,
)
from modules.system.application.read_models.menu_read_models import (
    MenuItemReadModel,
    MenuTreeNodeReadModel,
    RoleMenuTreeReadModel,
)

if TYPE_CHECKING:
    from modules.system.application.services.menu_service import MenuService


def _extract_payload(raw: Any) -> dict[str, Any]:
    if hasattr(raw, 'model_dump'):
        return raw.model_dump(by_alias=False)
    if isinstance(raw, dict):
        return raw
    return {}


def _to_menu_item(raw: Any) -> MenuItemReadModel:
    return MenuItemReadModel.model_validate(_extract_payload(raw))


def _to_menu_tree_node(raw: Any) -> MenuTreeNodeReadModel:
    payload = dict(_extract_payload(raw))
    children_payload = payload.get('children') or []
    payload['children'] = [_to_menu_tree_node(child) for child in children_payload]
    return MenuTreeNodeReadModel.model_validate(payload)


class GetMenuTreeQueryHandler(IQueryHandler[GetMenuTreeQuery, list[MenuTreeNodeReadModel]]):
    """Handle menu tree query."""

    def __init__(self, menu_service: MenuService):
        self._menu_service = menu_service

    async def handle(self, request: GetMenuTreeQuery) -> list[MenuTreeNodeReadModel]:
        tree_result = await self._menu_service.get_menu_tree_services(request.current_user)
        return [_to_menu_tree_node(row) for row in tree_result]


class GetRoleMenuTreeQueryHandler(IQueryHandler[GetRoleMenuTreeQuery, RoleMenuTreeReadModel]):
    """Handle role menu tree query."""

    def __init__(self, menu_service: MenuService):
        self._menu_service = menu_service

    async def handle(self, request: GetRoleMenuTreeQuery) -> RoleMenuTreeReadModel:
        result = await self._menu_service.get_role_menu_tree_services(request.role_id, request.current_user)
        payload = _extract_payload(result)
        menus_payload = payload.get('menus') or []
        checked_keys = payload.get('checked_keys') or payload.get('checkedKeys') or []
        return RoleMenuTreeReadModel(
            menus=[_to_menu_tree_node(row) for row in menus_payload],
            checked_keys=[int(key) for key in checked_keys],
        )


class GetMenuListQueryHandler(IQueryHandler[GetMenuListQuery, list[MenuItemReadModel]]):
    """Handle menu list query."""

    def __init__(self, menu_service: MenuService):
        self._menu_service = menu_service

    async def handle(self, request: GetMenuListQuery) -> list[MenuItemReadModel]:
        list_result = await self._menu_service.get_menu_list_services(request.query, request.current_user)
        return [_to_menu_item(row) for row in list_result]


class GetMenuDetailQueryHandler(IQueryHandler[GetMenuDetailQuery, MenuItemReadModel]):
    """Handle menu detail query."""

    def __init__(self, menu_service: MenuService):
        self._menu_service = menu_service

    async def handle(self, request: GetMenuDetailQuery) -> MenuItemReadModel:
        detail_result = await self._menu_service.menu_detail_services(request.menu_id)
        return _to_menu_item(detail_result)

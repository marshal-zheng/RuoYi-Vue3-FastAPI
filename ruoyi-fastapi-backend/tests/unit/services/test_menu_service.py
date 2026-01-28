"""
Unit tests for menu service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from module_admin.service.menu_service import MenuService
from module_admin.entity.do.menu_do import SysMenu


@pytest.fixture
def mock_menu_dao():
    """Create mock menu DAO."""
    dao = MagicMock()
    dao.get_menu_by_id = AsyncMock()
    dao.get_menu_list = AsyncMock()
    dao.add_menu = AsyncMock()
    dao.edit_menu = AsyncMock()
    dao.delete_menu = AsyncMock()
    return dao


@pytest.fixture
def menu_service(mock_menu_dao):
    """Create menu service with mocked dependencies."""
    service = MenuService()
    service.menu_dao = mock_menu_dao
    return service


@pytest.fixture
def sample_menus():
    """Create sample menu tree."""
    return [
        SysMenu(
            menu_id=1,
            menu_name='系统管理',
            parent_id=0,
            order_num=1,
            path='/system',
            menu_type='M',
            visible='0',
            status='0',
        ),
        SysMenu(
            menu_id=2,
            menu_name='用户管理',
            parent_id=1,
            order_num=1,
            path='user',
            menu_type='C',
            visible='0',
            status='0',
        ),
        SysMenu(
            menu_id=3,
            menu_name='角色管理',
            parent_id=1,
            order_num=2,
            path='role',
            menu_type='C',
            visible='0',
            status='0',
        ),
    ]


class TestMenuServiceQuery:
    """Test suite for menu query operations."""

    @pytest.mark.asyncio
    async def test_get_menu_by_id(self, menu_service, mock_menu_dao, sample_menus):
        """Test getting menu by ID."""
        mock_menu_dao.get_menu_by_id.return_value = sample_menus[0]

        result = await menu_service.get_menu_by_id(1)

        assert result is not None
        assert result.menu_name == '系统管理'

    @pytest.mark.asyncio
    async def test_get_menu_list(self, menu_service, mock_menu_dao, sample_menus):
        """Test getting menu list."""
        mock_menu_dao.get_menu_list.return_value = sample_menus

        result = await menu_service.get_menu_list()

        assert len(result) == 3


class TestMenuServiceTree:
    """Test suite for menu tree operations."""

    @pytest.mark.asyncio
    async def test_build_menu_tree(self, menu_service, mock_menu_dao, sample_menus):
        """Test building menu tree structure."""
        mock_menu_dao.get_menu_list.return_value = sample_menus

        result = await menu_service.build_menu_tree()

        assert len(result) == 1  # One root menu
        assert result[0]['menu_id'] == 1
        assert len(result[0]['children']) == 2  # Two child menus

    @pytest.mark.asyncio
    async def test_build_menu_tree_empty(self, menu_service, mock_menu_dao):
        """Test building tree with no menus."""
        mock_menu_dao.get_menu_list.return_value = []

        result = await menu_service.build_menu_tree()

        assert result == []

    def test_find_children_menus(self, menu_service, sample_menus):
        """Test finding children of a menu."""
        children = menu_service._find_children(sample_menus, 1)

        assert len(children) == 2
        assert all(m.parent_id == 1 for m in children)


class TestMenuServiceCreate:
    """Test suite for menu creation."""

    @pytest.mark.asyncio
    async def test_add_menu_success(self, menu_service, mock_menu_dao):
        """Test adding new menu."""
        mock_menu_dao.add_menu.return_value = 1

        menu_data = {
            'menu_name': '新菜单',
            'parent_id': 0,
            'order_num': 1,
            'path': '/new',
            'menu_type': 'M',
        }

        result = await menu_service.add_menu(menu_data)

        assert result == 1

    @pytest.mark.asyncio
    async def test_add_menu_validates_type(self, menu_service):
        """Test menu creation validates type."""
        menu_data = {
            'menu_name': '新菜单',
            'menu_type': 'X',  # Invalid
        }

        with pytest.raises(ValueError, match='菜单类型无效'):
            await menu_service.add_menu(menu_data)

    @pytest.mark.asyncio
    async def test_add_menu_validates_parent(self, menu_service, mock_menu_dao):
        """Test menu creation validates parent exists."""
        mock_menu_dao.get_menu_by_id.return_value = None

        menu_data = {
            'menu_name': '新菜单',
            'parent_id': 999,  # Non-existent
        }

        with pytest.raises(ValueError, match='父菜单不存在'):
            await menu_service.add_menu(menu_data)


class TestMenuServiceUpdate:
    """Test suite for menu update operations."""

    @pytest.mark.asyncio
    async def test_edit_menu_success(self, menu_service, mock_menu_dao, sample_menus):
        """Test editing menu."""
        mock_menu_dao.get_menu_by_id.return_value = sample_menus[0]
        mock_menu_dao.edit_menu.return_value = True

        menu_data = {
            'menu_id': 1,
            'menu_name': '更新菜单',
        }

        result = await menu_service.edit_menu(menu_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_edit_menu_cannot_be_own_parent(self, menu_service, mock_menu_dao, sample_menus):
        """Test menu cannot be its own parent."""
        mock_menu_dao.get_menu_by_id.return_value = sample_menus[0]

        menu_data = {
            'menu_id': 1,
            'parent_id': 1,  # Same as menu_id
        }

        with pytest.raises(ValueError, match='不能设置自己为父菜单'):
            await menu_service.edit_menu(menu_data)


class TestMenuServiceDelete:
    """Test suite for menu deletion."""

    @pytest.mark.asyncio
    async def test_delete_menu_success(self, menu_service, mock_menu_dao, sample_menus):
        """Test deleting menu."""
        mock_menu_dao.get_menu_by_id.return_value = sample_menus[1]
        mock_menu_dao.get_menu_list.return_value = []  # No children
        mock_menu_dao.delete_menu.return_value = True

        result = await menu_service.delete_menu(2)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_menu_with_children_forbidden(self, menu_service, mock_menu_dao, sample_menus):
        """Test cannot delete menu with children."""
        mock_menu_dao.get_menu_by_id.return_value = sample_menus[0]
        mock_menu_dao.get_menu_list.return_value = [sample_menus[1], sample_menus[2]]

        with pytest.raises(ValueError, match='存在子菜单，不允许删除'):
            await menu_service.delete_menu(1)


class TestMenuServicePermissions:
    """Test suite for menu permission operations."""

    @pytest.mark.asyncio
    async def test_get_user_menu_permissions(self, menu_service, mock_menu_dao, sample_menus):
        """Test getting user menu permissions."""
        mock_menu_dao.get_user_menus = AsyncMock(return_value=sample_menus)

        result = await menu_service.get_user_menu_permissions(1)

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_check_menu_permission(self, menu_service, mock_menu_dao):
        """Test checking if user has menu permission."""
        mock_menu_dao.check_user_menu = AsyncMock(return_value=True)

        result = await menu_service.check_menu_permission(1, 2)

        assert result is True


class TestMenuServiceRoutes:
    """Test suite for route generation."""

    @pytest.mark.asyncio
    async def test_build_routes(self, menu_service, mock_menu_dao, sample_menus):
        """Test building frontend routes from menus."""
        mock_menu_dao.get_menu_list.return_value = sample_menus

        result = await menu_service.build_routes()

        assert len(result) > 0
        assert 'path' in result[0]
        assert 'component' in result[0]

    def test_menu_to_route_conversion(self, menu_service, sample_menus):
        """Test converting menu to route object."""
        menu = sample_menus[0]

        route = menu_service._menu_to_route(menu)

        assert route['path'] == menu.path
        assert route['name'] == menu.menu_name

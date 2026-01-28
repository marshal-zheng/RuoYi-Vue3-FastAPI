"""
Unit tests for menu controller.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from module_admin.controller.menu_controller import menuController


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(menuController)
    return app


@pytest.fixture
def mock_menu_service():
    """Create mock menu service."""
    with patch('module_admin.controller.menu_controller.MenuService') as mock:
        mock.get_menu_tree_services = AsyncMock()
        mock.get_role_menu_tree_services = AsyncMock()
        mock.get_menu_list_services = AsyncMock()
        mock.add_menu_services = AsyncMock()
        mock.edit_menu_services = AsyncMock()
        mock.delete_menu_services = AsyncMock()
        mock.menu_detail_services = AsyncMock()
        yield mock


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    user = MagicMock()
    user.user_id = 1
    user.user_name = 'admin'
    user.admin = True
    
    current_user = MagicMock()
    current_user.user = user
    return current_user


@pytest.fixture
def mock_login_service(mock_current_user):
    """Create mock login service."""
    with patch('module_admin.controller.menu_controller.LoginService') as mock:
        mock.get_current_user = AsyncMock(return_value=mock_current_user)
        yield mock


@pytest.fixture
def mock_auth():
    """Mock authentication decorator."""
    with patch('module_admin.controller.menu_controller.CheckUserInterfaceAuth') as mock:
        mock.return_value = lambda: True
        yield mock


@pytest.fixture
def mock_db():
    """Create mock database session."""
    with patch('module_admin.controller.menu_controller.get_db') as mock:
        db = AsyncMock()
        mock.return_value = db
        yield db


class TestMenuControllerQuery:
    """Test suite for menu query endpoints."""

    @pytest.mark.asyncio
    async def test_get_menu_tree_success(
        self, app, mock_menu_service, mock_login_service, mock_db
    ):
        """Test getting menu tree successfully."""
        mock_menu_service.get_menu_tree_services.return_value = [
            {
                'menu_id': 1,
                'menu_name': 'System',
                'children': [
                    {'menu_id': 2, 'menu_name': 'User', 'children': []},
                    {'menu_id': 3, 'menu_name': 'Role', 'children': []},
                ],
            }
        ]

        with TestClient(app) as client:
            response = client.get('/system/menu/treeselect')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['menu_id'] == 1
        assert len(data[0]['children']) == 2

    @pytest.mark.asyncio
    async def test_get_role_menu_tree_success(
        self, app, mock_menu_service, mock_login_service, mock_db
    ):
        """Test getting role menu tree successfully."""
        mock_menu_service.get_role_menu_tree_services.return_value = MagicMock(
            menus=[
                {'menu_id': 1, 'menu_name': 'System', 'children': []},
            ],
            checkedKeys=[1, 2, 3],
        )

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/roleMenuTreeselect/1')

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_menu_list_success(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting menu list successfully."""
        mock_menu_service.get_menu_list_services.return_value = [
            {'menu_id': 1, 'menu_name': 'System', 'menu_type': 'M'},
            {'menu_id': 2, 'menu_name': 'User', 'menu_type': 'C'},
        ]

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/list')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_menu_list_with_filters(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting menu list with filters."""
        mock_menu_service.get_menu_list_services.return_value = [
            {'menu_id': 1, 'menu_name': 'System', 'menu_type': 'M'},
        ]

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/list?menuName=System&status=0')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_menu_detail_success(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting menu detail successfully."""
        mock_menu_service.menu_detail_services.return_value = {
            'menu_id': 1,
            'menu_name': 'System',
            'menu_type': 'M',
            'path': '/system',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/1')

        assert response.status_code == 200
        data = response.json()
        assert data['menu_id'] == 1
        assert data['menu_name'] == 'System'


class TestMenuControllerCreate:
    """Test suite for menu creation endpoints."""

    @pytest.mark.asyncio
    async def test_add_menu_success(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding menu successfully."""
        mock_menu_service.add_menu_services.return_value = MagicMock(message='新增成功')

        menu_data = {
            'menuName': 'New Menu',
            'menuType': 'C',
            'path': '/new',
            'component': 'new/index',
            'orderNum': 1,
            'visible': '0',
            'status': '0',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/menu', json=menu_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '新增成功'

    @pytest.mark.asyncio
    async def test_add_menu_validation_error(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding menu with validation error."""
        menu_data = {
            'menuName': '',  # Empty menu name
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/menu', json=menu_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_add_directory_menu(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding directory menu."""
        mock_menu_service.add_menu_services.return_value = MagicMock(message='新增成功')

        menu_data = {
            'menuName': 'Directory',
            'menuType': 'M',
            'path': '/directory',
            'orderNum': 1,
            'visible': '0',
            'status': '0',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/menu', json=menu_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_button_menu(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding button menu."""
        mock_menu_service.add_menu_services.return_value = MagicMock(message='新增成功')

        menu_data = {
            'menuName': 'Add Button',
            'menuType': 'F',
            'perms': 'system:user:add',
            'orderNum': 1,
            'visible': '0',
            'status': '0',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/menu', json=menu_data)

        assert response.status_code == 200


class TestMenuControllerUpdate:
    """Test suite for menu update endpoints."""

    @pytest.mark.asyncio
    async def test_edit_menu_success(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test editing menu successfully."""
        mock_menu_service.edit_menu_services.return_value = MagicMock(message='修改成功')

        menu_data = {
            'menuId': 2,
            'menuName': 'Updated Menu',
            'menuType': 'C',
            'path': '/updated',
            'orderNum': 2,
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/menu', json=menu_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'

    @pytest.mark.asyncio
    async def test_edit_menu_changes_status(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test editing menu status."""
        mock_menu_service.edit_menu_services.return_value = MagicMock(message='修改成功')

        menu_data = {
            'menuId': 2,
            'status': '1',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/menu', json=menu_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_edit_menu_changes_visibility(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test editing menu visibility."""
        mock_menu_service.edit_menu_services.return_value = MagicMock(message='修改成功')

        menu_data = {
            'menuId': 2,
            'visible': '1',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/menu', json=menu_data)

        assert response.status_code == 200


class TestMenuControllerDelete:
    """Test suite for menu deletion endpoints."""

    @pytest.mark.asyncio
    async def test_delete_menu_success(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test deleting menu successfully."""
        mock_menu_service.delete_menu_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/menu/2')

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '删除成功'

    @pytest.mark.asyncio
    async def test_delete_multiple_menus(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test deleting multiple menus."""
        mock_menu_service.delete_menu_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/menu/2,3,4')

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '删除成功'

    @pytest.mark.asyncio
    async def test_delete_menu_with_children_fails(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test that deleting menu with children fails."""
        mock_menu_service.delete_menu_services.return_value = MagicMock(
            message='存在子菜单，不允许删除'
        )

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/menu/1')

        assert response.status_code == 200
        data = response.json()
        assert '子菜单' in data['msg']


class TestMenuControllerEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_get_menu_tree_empty(
        self, app, mock_menu_service, mock_login_service, mock_db
    ):
        """Test getting empty menu tree."""
        mock_menu_service.get_menu_tree_services.return_value = []

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/treeselect')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_menu_list_empty(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting empty menu list."""
        mock_menu_service.get_menu_list_services.return_value = []

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/list')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_menu_detail_not_found(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting non-existent menu detail."""
        mock_menu_service.menu_detail_services.return_value = None

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/999')

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_menu_with_parent(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding menu with parent."""
        mock_menu_service.add_menu_services.return_value = MagicMock(message='新增成功')

        menu_data = {
            'menuName': 'Child Menu',
            'menuType': 'C',
            'parentId': 1,
            'path': '/child',
            'orderNum': 1,
            'visible': '0',
            'status': '0',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/menu', json=menu_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_menu_with_icon(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding menu with icon."""
        mock_menu_service.add_menu_services.return_value = MagicMock(message='新增成功')

        menu_data = {
            'menuName': 'Menu with Icon',
            'menuType': 'C',
            'path': '/icon',
            'icon': 'user',
            'orderNum': 1,
            'visible': '0',
            'status': '0',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/menu', json=menu_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_external_link_menu(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding external link menu."""
        mock_menu_service.add_menu_services.return_value = MagicMock(message='新增成功')

        menu_data = {
            'menuName': 'External Link',
            'menuType': 'C',
            'path': 'http://example.com',
            'isFrame': '0',
            'orderNum': 1,
            'visible': '0',
            'status': '0',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/menu', json=menu_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_edit_menu_order(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test editing menu order."""
        mock_menu_service.edit_menu_services.return_value = MagicMock(message='修改成功')

        menu_data = {
            'menuId': 2,
            'orderNum': 10,
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/menu', json=menu_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_empty_menu_ids(
        self, app, mock_menu_service, mock_login_service, mock_auth, mock_db
    ):
        """Test deleting with empty menu IDs."""
        mock_menu_service.delete_menu_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/menu/')

        assert response.status_code == 200


class TestMenuControllerTreeStructure:
    """Test suite for menu tree structure operations."""

    @pytest.mark.asyncio
    async def test_get_nested_menu_tree(
        self, app, mock_menu_service, mock_login_service, mock_db
    ):
        """Test getting nested menu tree."""
        mock_menu_service.get_menu_tree_services.return_value = [
            {
                'menu_id': 1,
                'menu_name': 'System',
                'children': [
                    {
                        'menu_id': 2,
                        'menu_name': 'User Management',
                        'children': [
                            {'menu_id': 3, 'menu_name': 'User List', 'children': []},
                        ],
                    },
                ],
            }
        ]

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/treeselect')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert len(data[0]['children']) == 1
        assert len(data[0]['children'][0]['children']) == 1

    @pytest.mark.asyncio
    async def test_get_role_menu_tree_with_checked_keys(
        self, app, mock_menu_service, mock_login_service, mock_db
    ):
        """Test getting role menu tree with checked keys."""
        mock_menu_service.get_role_menu_tree_services.return_value = MagicMock(
            menus=[
                {'menu_id': 1, 'menu_name': 'System', 'children': []},
                {'menu_id': 2, 'menu_name': 'Monitor', 'children': []},
            ],
            checkedKeys=[1, 2, 3, 4],
        )

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/menu/roleMenuTreeselect/1')

        assert response.status_code == 200

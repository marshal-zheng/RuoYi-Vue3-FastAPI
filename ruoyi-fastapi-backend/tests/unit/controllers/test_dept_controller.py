"""
Unit tests for department controller.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from module_admin.controller.dept_controller import deptController


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(deptController)
    return app


@pytest.fixture
def mock_dept_service():
    """Create mock dept service."""
    with patch('module_admin.controller.dept_controller.DeptService') as mock:
        mock.get_dept_tree_services = AsyncMock()
        mock.get_dept_list_services = AsyncMock()
        mock.add_dept_services = AsyncMock()
        mock.edit_dept_services = AsyncMock()
        mock.delete_dept_services = AsyncMock()
        mock.dept_detail_services = AsyncMock()
        mock.check_dept_data_scope_services = AsyncMock()
        mock.export_dept_list_services = AsyncMock()
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
    with patch('module_admin.controller.dept_controller.LoginService') as mock:
        mock.get_current_user = AsyncMock(return_value=mock_current_user)
        yield mock


@pytest.fixture
def mock_auth():
    """Mock authentication decorator."""
    with patch('module_admin.controller.dept_controller.CheckUserInterfaceAuth') as mock:
        mock.return_value = lambda: True
        yield mock


@pytest.fixture
def mock_data_scope():
    """Mock data scope decorator."""
    with patch('module_admin.controller.dept_controller.GetDataScope') as mock:
        mock.return_value = lambda: ''
        yield mock


@pytest.fixture
def mock_db():
    """Create mock database session."""
    with patch('module_admin.controller.dept_controller.get_db') as mock:
        db = AsyncMock()
        mock.return_value = db
        yield db


class TestDeptControllerQuery:
    """Test suite for department query endpoints."""

    def test_get_dept_tree_success(
        self, app, mock_dept_service, mock_login_service, mock_data_scope, mock_db
    ):
        """Test getting department tree successfully."""
        mock_dept_service.get_dept_tree_services.return_value = [
            {
                'dept_id': 100,
                'dept_name': 'Company',
                'children': [
                    {'dept_id': 101, 'dept_name': 'Dept1', 'children': []},
                    {'dept_id': 102, 'dept_name': 'Dept2', 'children': []},
                ],
            }
        ]

        with TestClient(app) as client:
            response = client.get('/system/dept/treeselect')

        assert response.status_code == 200

    def test_get_dept_list_success(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting department list successfully."""
        mock_dept_service.get_dept_list_services.return_value = [
            {'dept_id': 100, 'dept_name': 'Company'},
            {'dept_id': 101, 'dept_name': 'Dept1'},
        ]

        with TestClient(app) as client:
            response = client.get('/system/dept/list')

        assert response.status_code == 200

    def test_get_dept_list_with_filters(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting department list with filters."""
        mock_dept_service.get_dept_list_services.return_value = [
            {'dept_id': 100, 'dept_name': 'Company'},
        ]

        with TestClient(app) as client:
            response = client.get('/system/dept/list?deptName=Company&status=0')

        assert response.status_code == 200

    def test_get_dept_detail_success(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting department detail successfully."""
        mock_dept_service.dept_detail_services.return_value = {
            'dept_id': 100,
            'dept_name': 'Company',
            'parent_id': 0,
        }

        with TestClient(app) as client:
            response = client.get('/system/dept/100')

        assert response.status_code == 200


class TestDeptControllerCreate:
    """Test suite for department creation endpoints."""

    def test_add_dept_success(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test adding department successfully."""
        mock_dept_service.add_dept_services.return_value = MagicMock(message='新增成功')

        dept_data = {
            'deptName': 'New Dept',
            'parentId': 100,
            'orderNum': 1,
            'status': '0',
        }

        with TestClient(app) as client:
            response = client.post('/system/dept', json=dept_data)

        assert response.status_code == 200

    def test_add_dept_validation_error(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test adding department with validation error."""
        dept_data = {
            'deptName': '',  # Empty dept name
        }

        with TestClient(app) as client:
            response = client.post('/system/dept', json=dept_data)

        assert response.status_code == 422


class TestDeptControllerUpdate:
    """Test suite for department update endpoints."""

    def test_edit_dept_success(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test editing department successfully."""
        mock_dept_service.edit_dept_services.return_value = MagicMock(message='修改成功')

        dept_data = {
            'deptId': 101,
            'deptName': 'Updated Dept',
            'orderNum': 2,
        }

        with TestClient(app) as client:
            response = client.put('/system/dept', json=dept_data)

        assert response.status_code == 200


class TestDeptControllerDelete:
    """Test suite for department deletion endpoints."""

    def test_delete_dept_success(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test deleting department successfully."""
        mock_dept_service.delete_dept_services.return_value = MagicMock(message='删除成功')

        with TestClient(app) as client:
            response = client.delete('/system/dept/101')

        assert response.status_code == 200


class TestDeptControllerExport:
    """Test suite for department export endpoints."""

    def test_export_dept_list_success(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test exporting department list successfully."""
        mock_dept_service.get_dept_list_services.return_value = [
            {'dept_id': 100, 'dept_name': 'Company'},
        ]
        mock_dept_service.export_dept_list_services.return_value = b'excel_data'

        with TestClient(app) as client:
            response = client.post('/system/dept/export')

        assert response.status_code == 200


class TestDeptControllerEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_get_dept_tree_empty(
        self, app, mock_dept_service, mock_login_service, mock_data_scope, mock_db
    ):
        """Test getting empty department tree."""
        mock_dept_service.get_dept_tree_services.return_value = []

        with TestClient(app) as client:
            response = client.get('/system/dept/treeselect')

        assert response.status_code == 200

    def test_get_dept_list_empty(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting empty department list."""
        mock_dept_service.get_dept_list_services.return_value = []

        with TestClient(app) as client:
            response = client.get('/system/dept/list')

        assert response.status_code == 200

    def test_add_dept_with_parent(
        self, app, mock_dept_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test adding department with parent."""
        mock_dept_service.add_dept_services.return_value = MagicMock(message='新增成功')

        dept_data = {
            'deptName': 'Child Dept',
            'parentId': 100,
            'orderNum': 1,
            'status': '0',
        }

        with TestClient(app) as client:
            response = client.post('/system/dept', json=dept_data)

        assert response.status_code == 200

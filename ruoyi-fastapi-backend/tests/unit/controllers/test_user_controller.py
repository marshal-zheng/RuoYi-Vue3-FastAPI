"""
Unit tests for user controller.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from module_admin.controller.user_controller import userController
from module_admin.entity.vo.user_vo import (
    UserModel,
    AddUserModel,
    EditUserModel,
    CurrentUserModel,
    UserPageQueryModel,
)
from utils.response_util import ResponseUtil


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(userController)
    return app


@pytest.fixture
def mock_user_service():
    """Create mock user service."""
    with patch('module_admin.controller.user_controller.UserService') as mock:
        mock.get_user_list_services = AsyncMock()
        mock.add_user_services = AsyncMock()
        mock.edit_user_services = AsyncMock()
        mock.delete_user_services = AsyncMock()
        mock.user_detail_services = AsyncMock()
        mock.user_profile_services = AsyncMock()
        mock.check_user_allowed_services = AsyncMock()
        mock.check_user_data_scope_services = AsyncMock()
        mock.reset_user_services = AsyncMock()
        mock.batch_import_user_services = AsyncMock()
        mock.get_user_import_template_services = AsyncMock()
        mock.export_user_list_services = AsyncMock()
        mock.get_user_role_allocated_list_services = AsyncMock()
        mock.add_user_role_services = AsyncMock()
        yield mock


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    user = MagicMock()
    user.user_id = 1
    user.user_name = 'admin'
    user.admin = True
    user.role_ids = '1,2'
    user.post_ids = '1'
    user.role = MagicMock()
    
    current_user = MagicMock()
    current_user.user = user
    return current_user


@pytest.fixture
def mock_login_service(mock_current_user):
    """Create mock login service."""
    with patch('module_admin.controller.user_controller.LoginService') as mock:
        mock.get_current_user = AsyncMock(return_value=mock_current_user)
        yield mock


@pytest.fixture
def mock_auth():
    """Mock authentication decorator."""
    with patch('module_admin.controller.user_controller.CheckUserInterfaceAuth') as mock:
        mock.return_value = lambda: True
        yield mock


@pytest.fixture
def mock_data_scope():
    """Mock data scope decorator."""
    with patch('module_admin.controller.user_controller.GetDataScope') as mock:
        mock.return_value = lambda: ''
        yield mock


@pytest.fixture
def mock_db():
    """Create mock database session."""
    with patch('module_admin.controller.user_controller.get_db') as mock:
        db = AsyncMock()
        mock.return_value = db
        yield db


class TestUserControllerQuery:
    """Test suite for user query endpoints."""

    @pytest.mark.asyncio
    async def test_get_user_list_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting user list successfully."""
        mock_user_service.get_user_list_services.return_value = {
            'total': 2,
            'rows': [
                {'user_id': 1, 'user_name': 'admin'},
                {'user_id': 2, 'user_name': 'user1'},
            ],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/user/list?pageNum=1&pageSize=10')

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['rows']) == 2

    @pytest.mark.asyncio
    async def test_get_user_list_with_filters(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting user list with filters."""
        mock_user_service.get_user_list_services.return_value = {
            'total': 1,
            'rows': [{'user_id': 1, 'user_name': 'admin'}],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get(
                '/system/user/list?pageNum=1&pageSize=10&userName=admin&status=0'
            )

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1

    @pytest.mark.asyncio
    async def test_get_user_detail_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting user detail successfully."""
        mock_user_service.user_detail_services.return_value = {
            'user': {'user_id': 1, 'user_name': 'admin'},
            'roles': [],
            'posts': [],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/user/1')

        assert response.status_code == 200
        data = response.json()
        assert data['user']['user_id'] == 1

    @pytest.mark.asyncio
    async def test_get_user_profile_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting user profile successfully."""
        mock_user_service.user_profile_services.return_value = {
            'user': {'user_id': 1, 'user_name': 'admin'},
            'roleGroup': 'admin',
            'postGroup': 'CEO',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/user/profile')

        assert response.status_code == 200
        data = response.json()
        assert data['user']['user_id'] == 1

    @pytest.mark.asyncio
    async def test_get_dept_tree_success(
        self, app, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting department tree successfully."""
        with patch('module_admin.controller.user_controller.DeptService') as mock_dept:
            mock_dept.get_dept_tree_services = AsyncMock(return_value=[
                {'dept_id': 1, 'dept_name': 'Root', 'children': []}
            ])

            async with AsyncClient(app=app, base_url='http://test') as client:
                response = await client.get('/system/user/deptTree')

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1


class TestUserControllerCreate:
    """Test suite for user creation endpoints."""

    @pytest.mark.asyncio
    async def test_add_user_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test adding user successfully."""
        mock_user_service.add_user_services.return_value = MagicMock(message='新增成功')

        user_data = {
            'userName': 'newuser',
            'nickName': 'New User',
            'email': 'new@example.com',
            'phonenumber': '13900139000',
            'password': 'password123',
            'status': '0',
            'deptId': 100,
            'roleIds': [2],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/user', json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '新增成功'

    @pytest.mark.asyncio
    async def test_add_user_validation_error(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test adding user with validation error."""
        user_data = {
            'userName': '',  # Empty username
            'password': 'password123',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/user', json=user_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_add_user_checks_dept_scope(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db, mock_current_user
    ):
        """Test that adding user checks department scope for non-admin."""
        mock_current_user.user.admin = False
        mock_user_service.add_user_services.return_value = MagicMock(message='新增成功')

        with patch('module_admin.controller.user_controller.DeptService') as mock_dept:
            mock_dept.check_dept_data_scope_services = AsyncMock()
            with patch('module_admin.controller.user_controller.RoleService') as mock_role:
                mock_role.check_role_data_scope_services = AsyncMock()

                user_data = {
                    'userName': 'newuser',
                    'nickName': 'New User',
                    'password': 'password123',
                    'deptId': 100,
                    'roleIds': [2],
                }

                async with AsyncClient(app=app, base_url='http://test') as client:
                    response = await client.post('/system/user', json=user_data)

                assert response.status_code == 200
                mock_dept.check_dept_data_scope_services.assert_called_once()
                mock_role.check_role_data_scope_services.assert_called_once()


class TestUserControllerUpdate:
    """Test suite for user update endpoints."""

    @pytest.mark.asyncio
    async def test_edit_user_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test editing user successfully."""
        mock_user_service.check_user_allowed_services.return_value = None
        mock_user_service.edit_user_services.return_value = MagicMock(message='修改成功')

        user_data = {
            'userId': 2,
            'nickName': 'Updated Name',
            'email': 'updated@example.com',
            'deptId': 100,
            'roleIds': [2],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/user', json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'

    @pytest.mark.asyncio
    async def test_reset_user_password_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test resetting user password successfully."""
        mock_user_service.check_user_allowed_services.return_value = None
        mock_user_service.edit_user_services.return_value = MagicMock(message='重置成功')

        user_data = {
            'userId': 2,
            'password': 'newpassword123',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/user/resetPwd', json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '重置成功'

    @pytest.mark.asyncio
    async def test_change_user_status_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test changing user status successfully."""
        mock_user_service.check_user_allowed_services.return_value = None
        mock_user_service.edit_user_services.return_value = MagicMock(message='修改成功')

        user_data = {
            'userId': 2,
            'status': '1',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/user/changeStatus', json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'

    @pytest.mark.asyncio
    async def test_update_profile_info_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_db
    ):
        """Test updating profile info successfully."""
        mock_user_service.edit_user_services.return_value = MagicMock(message='修改成功')

        user_data = {
            'nickName': 'Updated Name',
            'email': 'updated@example.com',
            'phonenumber': '13900139000',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/user/profile', json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'

    @pytest.mark.asyncio
    async def test_update_profile_password_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_db
    ):
        """Test updating profile password successfully."""
        mock_user_service.reset_user_services.return_value = MagicMock(message='修改成功')

        password_data = {
            'oldPassword': 'oldpass123',
            'newPassword': 'newpass123',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/user/profile/updatePwd', json=password_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'


class TestUserControllerDelete:
    """Test suite for user deletion endpoints."""

    @pytest.mark.asyncio
    async def test_delete_user_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test deleting user successfully."""
        mock_user_service.check_user_allowed_services.return_value = None
        mock_user_service.delete_user_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/user/2,3')

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '删除成功'

    @pytest.mark.asyncio
    async def test_delete_current_user_forbidden(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db, mock_current_user
    ):
        """Test that current user cannot delete themselves."""
        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/user/1')

        assert response.status_code == 200
        data = response.json()
        assert '不能删除' in data['msg']

    @pytest.mark.asyncio
    async def test_delete_user_checks_allowed(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test that deleting user checks if allowed."""
        mock_user_service.check_user_allowed_services.return_value = None
        mock_user_service.delete_user_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/user/2')

        assert response.status_code == 200
        mock_user_service.check_user_allowed_services.assert_called()


class TestUserControllerImportExport:
    """Test suite for user import/export endpoints."""

    @pytest.mark.asyncio
    async def test_export_user_list_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test exporting user list successfully."""
        mock_user_service.get_user_list_services.return_value = {
            'total': 2,
            'rows': [
                {'user_id': 1, 'user_name': 'admin'},
                {'user_id': 2, 'user_name': 'user1'},
            ],
        }
        mock_user_service.export_user_list_services.return_value = b'excel_data'

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/user/export')

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_import_template_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting import template successfully."""
        mock_user_service.get_user_import_template_services.return_value = b'template_data'

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/user/importTemplate')

        assert response.status_code == 200


class TestUserControllerRole:
    """Test suite for user role management endpoints."""

    @pytest.mark.asyncio
    async def test_get_allocated_role_list_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_db
    ):
        """Test getting allocated role list successfully."""
        mock_user_service.get_user_role_allocated_list_services.return_value = {
            'user': {'user_id': 1, 'user_name': 'admin'},
            'roles': [{'role_id': 1, 'role_name': 'admin'}],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/user/authRole/1')

        assert response.status_code == 200
        data = response.json()
        assert data['user']['user_id'] == 1

    @pytest.mark.asyncio
    async def test_update_user_role_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test updating user role successfully."""
        mock_user_service.add_user_role_services.return_value = MagicMock(message='授权成功')

        with patch('module_admin.controller.user_controller.RoleService') as mock_role:
            mock_role.check_role_data_scope_services = AsyncMock()

            async with AsyncClient(app=app, base_url='http://test') as client:
                response = await client.put('/system/user/authRole?userId=2&roleIds=1,2')

            assert response.status_code == 200
            data = response.json()
            assert data['msg'] == '授权成功'


class TestUserControllerEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_get_user_list_empty_result(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting empty user list."""
        mock_user_service.get_user_list_services.return_value = {
            'total': 0,
            'rows': [],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/user/list?pageNum=1&pageSize=10')

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 0
        assert len(data['rows']) == 0

    @pytest.mark.asyncio
    async def test_get_user_detail_not_found(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting non-existent user detail."""
        mock_user_service.user_detail_services.return_value = None

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/user/999')

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_empty_user_ids(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test deleting with empty user IDs."""
        mock_user_service.delete_user_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/user/')

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_user_with_minimal_data(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test adding user with minimal required data."""
        mock_user_service.add_user_services.return_value = MagicMock(message='新增成功')

        user_data = {
            'userName': 'minimaluser',
            'password': 'password123',
            'deptId': 100,
            'roleIds': [],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/user', json=user_data)

        assert response.status_code == 200

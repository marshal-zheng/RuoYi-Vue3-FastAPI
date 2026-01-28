"""
Unit tests for role controller.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from httpx import AsyncClient

from module_admin.controller.role_controller import roleController


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(roleController)
    return app


@pytest.fixture
def mock_role_service():
    """Create mock role service."""
    with patch('module_admin.controller.role_controller.RoleService') as mock:
        mock.get_role_list_services = AsyncMock()
        mock.add_role_services = AsyncMock()
        mock.edit_role_services = AsyncMock()
        mock.delete_role_services = AsyncMock()
        mock.role_detail_services = AsyncMock()
        mock.check_role_allowed_services = AsyncMock()
        mock.check_role_data_scope_services = AsyncMock()
        mock.role_datascope_services = AsyncMock()
        mock.get_role_dept_tree_services = AsyncMock()
        mock.export_role_list_services = AsyncMock()
        mock.get_role_user_allocated_list_services = AsyncMock()
        mock.get_role_user_unallocated_list_services = AsyncMock()
        yield mock


@pytest.fixture
def mock_user_service():
    """Create mock user service."""
    with patch('module_admin.controller.role_controller.UserService') as mock:
        mock.add_user_role_services = AsyncMock()
        mock.delete_user_role_services = AsyncMock()
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
    with patch('module_admin.controller.role_controller.LoginService') as mock:
        mock.get_current_user = AsyncMock(return_value=mock_current_user)
        yield mock


@pytest.fixture
def mock_auth():
    """Mock authentication decorator."""
    with patch('module_admin.controller.role_controller.CheckUserInterfaceAuth') as mock:
        mock.return_value = lambda: True
        yield mock


@pytest.fixture
def mock_data_scope():
    """Mock data scope decorator."""
    with patch('module_admin.controller.role_controller.GetDataScope') as mock:
        mock.return_value = lambda: ''
        yield mock


@pytest.fixture
def mock_db():
    """Create mock database session."""
    with patch('module_admin.controller.role_controller.get_db') as mock:
        db = AsyncMock()
        mock.return_value = db
        yield db


class TestRoleControllerQuery:
    """Test suite for role query endpoints."""

    @pytest.mark.asyncio
    async def test_get_role_list_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting role list successfully."""
        mock_role_service.get_role_list_services.return_value = {
            'total': 2,
            'rows': [
                {'role_id': 1, 'role_name': 'admin'},
                {'role_id': 2, 'role_name': 'user'},
            ],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/role/list?pageNum=1&pageSize=10')

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2
        assert len(data['rows']) == 2

    @pytest.mark.asyncio
    async def test_get_role_list_with_filters(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting role list with filters."""
        mock_role_service.get_role_list_services.return_value = {
            'total': 1,
            'rows': [{'role_id': 1, 'role_name': 'admin'}],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get(
                '/system/role/list?pageNum=1&pageSize=10&roleName=admin&status=0'
            )

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1

    @pytest.mark.asyncio
    async def test_get_role_detail_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting role detail successfully."""
        mock_role_service.role_detail_services.return_value = MagicMock(
            role_id=1,
            role_name='admin',
            role_key='admin',
            model_dump=lambda by_alias=True: {'role_id': 1, 'role_name': 'admin'},
        )

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/role/1')

        assert response.status_code == 200
        data = response.json()
        assert data['role_id'] == 1

    @pytest.mark.asyncio
    async def test_get_role_dept_tree_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting role department tree successfully."""
        mock_role_service.get_role_dept_tree_services.return_value = MagicMock(
            depts=[{'dept_id': 1, 'dept_name': 'Root'}],
            checkedKeys=[1],
        )

        with patch('module_admin.controller.role_controller.DeptService') as mock_dept:
            mock_dept.get_dept_tree_services = AsyncMock(return_value=[
                {'dept_id': 1, 'dept_name': 'Root'}
            ])

            async with AsyncClient(app=app, base_url='http://test') as client:
                response = await client.get('/system/role/deptTree/1')

            assert response.status_code == 200


class TestRoleControllerCreate:
    """Test suite for role creation endpoints."""

    @pytest.mark.asyncio
    async def test_add_role_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding role successfully."""
        mock_role_service.add_role_services.return_value = MagicMock(message='新增成功')

        role_data = {
            'roleName': 'newrole',
            'roleKey': 'newrole',
            'roleSort': 3,
            'status': '0',
            'menuIds': [1, 2, 3],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/role', json=role_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '新增成功'

    @pytest.mark.asyncio
    async def test_add_role_validation_error(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding role with validation error."""
        role_data = {
            'roleName': '',  # Empty role name
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/role', json=role_data)

        assert response.status_code == 422  # Validation error


class TestRoleControllerUpdate:
    """Test suite for role update endpoints."""

    @pytest.mark.asyncio
    async def test_edit_role_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test editing role successfully."""
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.edit_role_services.return_value = MagicMock(message='修改成功')

        role_data = {
            'roleId': 2,
            'roleName': 'Updated Role',
            'roleKey': 'updated',
            'roleSort': 2,
            'status': '0',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role', json=role_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'

    @pytest.mark.asyncio
    async def test_edit_role_checks_allowed(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test that editing role checks if allowed."""
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.edit_role_services.return_value = MagicMock(message='修改成功')

        role_data = {
            'roleId': 2,
            'roleName': 'Updated Role',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role', json=role_data)

        assert response.status_code == 200
        mock_role_service.check_role_allowed_services.assert_called()

    @pytest.mark.asyncio
    async def test_change_role_status_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test changing role status successfully."""
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.edit_role_services.return_value = MagicMock(message='修改成功')

        role_data = {
            'roleId': 2,
            'status': '1',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role/changeStatus', json=role_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'

    @pytest.mark.asyncio
    async def test_edit_role_datascope_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test editing role data scope successfully."""
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.role_datascope_services.return_value = MagicMock(message='修改成功')

        role_data = {
            'roleId': 2,
            'dataScope': '2',
            'deptIds': [100, 101],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role/dataScope', json=role_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '修改成功'


class TestRoleControllerDelete:
    """Test suite for role deletion endpoints."""

    @pytest.mark.asyncio
    async def test_delete_role_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test deleting role successfully."""
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.delete_role_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/role/2,3')

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '删除成功'

    @pytest.mark.asyncio
    async def test_delete_role_checks_allowed(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test that deleting role checks if allowed."""
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.delete_role_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/role/2')

        assert response.status_code == 200
        mock_role_service.check_role_allowed_services.assert_called()

    @pytest.mark.asyncio
    async def test_delete_multiple_roles(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test deleting multiple roles."""
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.delete_role_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/role/2,3,4')

        assert response.status_code == 200
        # Should check each role
        assert mock_role_service.check_role_allowed_services.call_count == 3


class TestRoleControllerExport:
    """Test suite for role export endpoints."""

    @pytest.mark.asyncio
    async def test_export_role_list_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test exporting role list successfully."""
        mock_role_service.get_role_list_services.return_value = {
            'total': 2,
            'rows': [
                {'role_id': 1, 'role_name': 'admin'},
                {'role_id': 2, 'role_name': 'user'},
            ],
        }
        mock_role_service.export_role_list_services.return_value = b'excel_data'

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/role/export')

        assert response.status_code == 200


class TestRoleControllerUserManagement:
    """Test suite for role user management endpoints."""

    @pytest.mark.asyncio
    async def test_get_allocated_user_list_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting allocated user list successfully."""
        mock_role_service.get_role_user_allocated_list_services.return_value = {
            'total': 2,
            'rows': [
                {'user_id': 1, 'user_name': 'admin'},
                {'user_id': 2, 'user_name': 'user1'},
            ],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get(
                '/system/role/authUser/allocatedList?roleId=1&pageNum=1&pageSize=10'
            )

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 2

    @pytest.mark.asyncio
    async def test_get_unallocated_user_list_success(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting unallocated user list successfully."""
        mock_role_service.get_role_user_unallocated_list_services.return_value = {
            'total': 1,
            'rows': [{'user_id': 3, 'user_name': 'user2'}],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get(
                '/system/role/authUser/unallocatedList?roleId=1&pageNum=1&pageSize=10'
            )

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1

    @pytest.mark.asyncio
    async def test_add_role_user_success(
        self, app, mock_user_service, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test adding user to role successfully."""
        mock_user_service.add_user_role_services.return_value = MagicMock(message='授权成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role/authUser/selectAll?roleId=2&userIds=3,4')

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '授权成功'

    @pytest.mark.asyncio
    async def test_cancel_role_user_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_db
    ):
        """Test canceling user from role successfully."""
        mock_user_service.delete_user_role_services.return_value = MagicMock(message='取消授权成功')

        cancel_data = {
            'roleId': 2,
            'userId': 3,
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role/authUser/cancel', json=cancel_data)

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '取消授权成功'

    @pytest.mark.asyncio
    async def test_batch_cancel_role_user_success(
        self, app, mock_user_service, mock_login_service, mock_auth, mock_db
    ):
        """Test batch canceling users from role successfully."""
        mock_user_service.delete_user_role_services.return_value = MagicMock(message='取消授权成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role/authUser/cancelAll?roleId=2&userIds=3,4')

        assert response.status_code == 200
        data = response.json()
        assert data['msg'] == '取消授权成功'


class TestRoleControllerEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_get_role_list_empty_result(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test getting empty role list."""
        mock_role_service.get_role_list_services.return_value = {
            'total': 0,
            'rows': [],
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.get('/system/role/list?pageNum=1&pageSize=10')

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 0
        assert len(data['rows']) == 0

    @pytest.mark.asyncio
    async def test_delete_empty_role_ids(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db
    ):
        """Test deleting with empty role IDs."""
        mock_role_service.delete_role_services.return_value = MagicMock(message='删除成功')

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.delete('/system/role/')

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_role_with_minimal_data(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_db
    ):
        """Test adding role with minimal required data."""
        mock_role_service.add_role_services.return_value = MagicMock(message='新增成功')

        role_data = {
            'roleName': 'minimalrole',
            'roleKey': 'minimal',
            'roleSort': 1,
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.post('/system/role', json=role_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_non_admin_checks_data_scope(
        self, app, mock_role_service, mock_login_service, mock_auth, mock_data_scope, mock_db, mock_current_user
    ):
        """Test that non-admin user checks data scope."""
        mock_current_user.user.admin = False
        mock_role_service.check_role_allowed_services.return_value = None
        mock_role_service.check_role_data_scope_services.return_value = None
        mock_role_service.edit_role_services.return_value = MagicMock(message='修改成功')

        role_data = {
            'roleId': 2,
            'roleName': 'Updated Role',
        }

        async with AsyncClient(app=app, base_url='http://test') as client:
            response = await client.put('/system/role', json=role_data)

        assert response.status_code == 200
        mock_role_service.check_role_data_scope_services.assert_called()

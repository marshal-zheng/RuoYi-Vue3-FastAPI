"""
Unit tests for role service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from module_admin.service.role_service import RoleService
from module_admin.entity.do.role_do import RoleDO
from module_admin.entity.vo.role_vo import RoleQueryModel, AddRoleModel, EditRoleModel


@pytest.fixture
def mock_role_dao():
    """Create mock role DAO."""
    dao = MagicMock()
    dao.get_role_by_id = AsyncMock()
    dao.get_role_list = AsyncMock()
    dao.add_role = AsyncMock()
    dao.edit_role = AsyncMock()
    dao.delete_role = AsyncMock()
    dao.count_roles = AsyncMock()
    return dao


@pytest.fixture
def role_service(mock_role_dao):
    """Create role service with mocked dependencies."""
    service = RoleService()
    service.role_dao = mock_role_dao
    return service


@pytest.fixture
def sample_admin_role():
    """Create sample admin role."""
    return RoleDO(
        role_id=1,
        role_name='超级管理员',
        role_key='admin',
        role_sort=1,
        data_scope='1',
        status='0',
        del_flag='0',
        create_time=datetime.now(),
    )


@pytest.fixture
def sample_common_role():
    """Create sample common role."""
    return RoleDO(
        role_id=2,
        role_name='普通角色',
        role_key='common',
        role_sort=2,
        data_scope='2',
        status='0',
        del_flag='0',
        create_time=datetime.now(),
    )


class TestRoleServiceQuery:
    """Test suite for role query operations."""

    @pytest.mark.asyncio
    async def test_get_role_by_id_success(self, role_service, mock_role_dao, sample_admin_role):
        """Test getting role by ID."""
        mock_role_dao.get_role_by_id.return_value = sample_admin_role

        result = await role_service.get_role_by_id(1)

        assert result is not None
        assert result.role_key == 'admin'
        assert result.role_name == '超级管理员'

    @pytest.mark.asyncio
    async def test_get_role_list_with_filters(self, role_service, mock_role_dao, sample_admin_role):
        """Test getting role list with filters."""
        mock_role_dao.get_role_list.return_value = [sample_admin_role]
        mock_role_dao.count_roles.return_value = 1

        query = RoleQueryModel(role_name='管理员', status='0')
        result = await role_service.get_role_list(query)

        assert result['total'] == 1
        assert len(result['rows']) == 1


class TestRoleServiceCreate:
    """Test suite for role creation."""

    @pytest.mark.asyncio
    async def test_add_role_success(self, role_service, mock_role_dao):
        """Test adding new role."""
        mock_role_dao.add_role.return_value = 1

        role_data = AddRoleModel(
            role_name='测试角色',
            role_key='test',
            role_sort=3,
            data_scope='2',
            status='0',
        )

        result = await role_service.add_role(role_data)

        assert result == 1
        mock_role_dao.add_role.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_role_duplicate_key(self, role_service, mock_role_dao, sample_admin_role):
        """Test adding role with duplicate key."""
        mock_role_dao.get_role_by_key = AsyncMock(return_value=sample_admin_role)

        role_data = AddRoleModel(
            role_name='测试角色',
            role_key='admin',
            role_sort=3,
        )

        with pytest.raises(ValueError, match='角色权限已存在'):
            await role_service.add_role(role_data)

    @pytest.mark.asyncio
    async def test_add_role_validates_data_scope(self, role_service):
        """Test role creation validates data scope."""
        role_data = AddRoleModel(
            role_name='测试角色',
            role_key='test',
            data_scope='9',  # Invalid
        )

        with pytest.raises(ValueError, match='数据范围无效'):
            await role_service.add_role(role_data)


class TestRoleServiceUpdate:
    """Test suite for role update operations."""

    @pytest.mark.asyncio
    async def test_edit_role_success(self, role_service, mock_role_dao, sample_common_role):
        """Test editing role."""
        mock_role_dao.get_role_by_id.return_value = sample_common_role
        mock_role_dao.edit_role.return_value = True

        role_data = EditRoleModel(
            role_id=2,
            role_name='更新角色',
            status='0',
        )

        result = await role_service.edit_role(role_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_edit_admin_role_forbidden(self, role_service, mock_role_dao, sample_admin_role):
        """Test that admin role cannot be edited."""
        mock_role_dao.get_role_by_id.return_value = sample_admin_role

        role_data = EditRoleModel(role_id=1, role_name='修改管理员')

        with pytest.raises(ValueError, match='不能修改超级管理员'):
            await role_service.edit_role(role_data)


class TestRoleServiceDelete:
    """Test suite for role deletion."""

    @pytest.mark.asyncio
    async def test_delete_role_success(self, role_service, mock_role_dao, sample_common_role):
        """Test deleting role."""
        mock_role_dao.get_role_by_id.return_value = sample_common_role
        mock_role_dao.delete_role.return_value = True

        result = await role_service.delete_role(2)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_admin_role_forbidden(self, role_service, mock_role_dao, sample_admin_role):
        """Test that admin role cannot be deleted."""
        mock_role_dao.get_role_by_id.return_value = sample_admin_role

        with pytest.raises(ValueError, match='不能删除超级管理员'):
            await role_service.delete_role(1)


class TestRoleServicePermissions:
    """Test suite for role permission management."""

    @pytest.mark.asyncio
    async def test_assign_menu_permissions(self, role_service, mock_role_dao):
        """Test assigning menu permissions to role."""
        mock_role_dao.assign_menus = AsyncMock(return_value=True)

        menu_ids = [1, 2, 3, 4, 5]
        result = await role_service.assign_menu_permissions(2, menu_ids)

        assert result is True
        mock_role_dao.assign_menus.assert_called_once_with(2, menu_ids)

    @pytest.mark.asyncio
    async def test_get_role_menu_permissions(self, role_service, mock_role_dao):
        """Test getting role menu permissions."""
        mock_role_dao.get_role_menus = AsyncMock(return_value=[1, 2, 3])

        result = await role_service.get_role_menu_permissions(2)

        assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_change_data_scope(self, role_service, mock_role_dao, sample_common_role):
        """Test changing role data scope."""
        mock_role_dao.get_role_by_id.return_value = sample_common_role
        mock_role_dao.edit_role.return_value = True

        result = await role_service.change_data_scope(2, '3', [1, 2])

        assert result is True


class TestRoleServiceDataScope:
    """Test suite for data scope validation."""

    def test_validate_data_scope_all(self, role_service):
        """Test data scope: all data."""
        assert role_service._validate_data_scope('1') is True

    def test_validate_data_scope_custom(self, role_service):
        """Test data scope: custom."""
        assert role_service._validate_data_scope('2') is True

    def test_validate_data_scope_dept(self, role_service):
        """Test data scope: department."""
        assert role_service._validate_data_scope('3') is True

    def test_validate_data_scope_dept_and_below(self, role_service):
        """Test data scope: department and below."""
        assert role_service._validate_data_scope('4') is True

    def test_validate_data_scope_self(self, role_service):
        """Test data scope: self only."""
        assert role_service._validate_data_scope('5') is True

    def test_validate_data_scope_invalid(self, role_service):
        """Test invalid data scope."""
        with pytest.raises(ValueError):
            role_service._validate_data_scope('9')

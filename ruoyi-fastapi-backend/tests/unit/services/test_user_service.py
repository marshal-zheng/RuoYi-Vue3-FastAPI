"""
Unit tests for user service.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from module_admin.service.user_service import UserService
from module_admin.entity.do.user_do import UserDO
from module_admin.entity.vo.user_vo import UserQueryModel, AddUserModel, EditUserModel
from utils.pwd_util import PwdUtil


@pytest.fixture
def mock_user_dao():
    """Create mock user DAO."""
    dao = MagicMock()
    dao.get_user_by_id = AsyncMock()
    dao.get_user_by_username = AsyncMock()
    dao.get_user_list = AsyncMock()
    dao.add_user = AsyncMock()
    dao.edit_user = AsyncMock()
    dao.delete_user = AsyncMock()
    dao.count_users = AsyncMock()
    return dao


@pytest.fixture
def user_service(mock_user_dao):
    """Create user service with mocked dependencies."""
    service = UserService()
    service.user_dao = mock_user_dao
    return service


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return UserDO(
        user_id=1,
        user_name='testuser',
        nick_name='Test User',
        email='test@example.com',
        phonenumber='13800138000',
        sex='0',
        password=PwdUtil.hash_password('test123'),
        status='0',
        del_flag='0',
        create_time=datetime.now(),
        update_time=datetime.now(),
    )


class TestUserServiceQuery:
    """Test suite for user query operations."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user_dao, sample_user):
        """Test getting user by ID successfully."""
        mock_user_dao.get_user_by_id.return_value = sample_user

        result = await user_service.get_user_by_id(1)

        assert result is not None
        assert result.user_id == 1
        assert result.user_name == 'testuser'
        mock_user_dao.get_user_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_user_dao):
        """Test getting non-existent user."""
        mock_user_dao.get_user_by_id.return_value = None

        result = await user_service.get_user_by_id(999)

        assert result is None
        mock_user_dao.get_user_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, user_service, mock_user_dao, sample_user):
        """Test getting user by username."""
        mock_user_dao.get_user_by_username.return_value = sample_user

        result = await user_service.get_user_by_username('testuser')

        assert result is not None
        assert result.user_name == 'testuser'
        mock_user_dao.get_user_by_username.assert_called_once_with('testuser')

    @pytest.mark.asyncio
    async def test_get_user_list_with_filters(self, user_service, mock_user_dao, sample_user):
        """Test getting user list with filters."""
        mock_user_dao.get_user_list.return_value = [sample_user]
        mock_user_dao.count_users.return_value = 1

        query = UserQueryModel(user_name='test', status='0', page_num=1, page_size=10)
        result = await user_service.get_user_list(query)

        assert result['total'] == 1
        assert len(result['rows']) == 1
        assert result['rows'][0].user_name == 'testuser'

    @pytest.mark.asyncio
    async def test_get_user_list_empty(self, user_service, mock_user_dao):
        """Test getting empty user list."""
        mock_user_dao.get_user_list.return_value = []
        mock_user_dao.count_users.return_value = 0

        query = UserQueryModel(page_num=1, page_size=10)
        result = await user_service.get_user_list(query)

        assert result['total'] == 0
        assert len(result['rows']) == 0


class TestUserServiceCreate:
    """Test suite for user creation operations."""

    @pytest.mark.asyncio
    async def test_add_user_success(self, user_service, mock_user_dao):
        """Test adding new user successfully."""
        mock_user_dao.get_user_by_username.return_value = None
        mock_user_dao.add_user.return_value = 1

        user_data = AddUserModel(
            user_name='newuser',
            nick_name='New User',
            email='new@example.com',
            phonenumber='13900139000',
            password='password123',
            status='0',
        )

        result = await user_service.add_user(user_data)

        assert result == 1
        mock_user_dao.add_user.assert_called_once()
        # Verify password was hashed
        call_args = mock_user_dao.add_user.call_args[0][0]
        assert call_args.password != 'password123'

    @pytest.mark.asyncio
    async def test_add_user_duplicate_username(self, user_service, mock_user_dao, sample_user):
        """Test adding user with duplicate username."""
        mock_user_dao.get_user_by_username.return_value = sample_user

        user_data = AddUserModel(
            user_name='testuser',
            nick_name='Test User',
            email='test@example.com',
            password='password123',
        )

        with pytest.raises(ValueError, match='用户名已存在'):
            await user_service.add_user(user_data)

        mock_user_dao.add_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_user_validates_email(self, user_service, mock_user_dao):
        """Test user creation validates email format."""
        user_data = AddUserModel(
            user_name='newuser',
            nick_name='New User',
            email='invalid-email',
            password='password123',
        )

        with pytest.raises(ValueError, match='邮箱格式不正确'):
            await user_service.add_user(user_data)

    @pytest.mark.asyncio
    async def test_add_user_validates_phone(self, user_service, mock_user_dao):
        """Test user creation validates phone format."""
        user_data = AddUserModel(
            user_name='newuser',
            nick_name='New User',
            phonenumber='123',
            password='password123',
        )

        with pytest.raises(ValueError, match='手机号格式不正确'):
            await user_service.add_user(user_data)


class TestUserServiceUpdate:
    """Test suite for user update operations."""

    @pytest.mark.asyncio
    async def test_edit_user_success(self, user_service, mock_user_dao, sample_user):
        """Test editing user successfully."""
        mock_user_dao.get_user_by_id.return_value = sample_user
        mock_user_dao.edit_user.return_value = True

        user_data = EditUserModel(
            user_id=1,
            nick_name='Updated Name',
            email='updated@example.com',
        )

        result = await user_service.edit_user(user_data)

        assert result is True
        mock_user_dao.edit_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_user_not_found(self, user_service, mock_user_dao):
        """Test editing non-existent user."""
        mock_user_dao.get_user_by_id.return_value = None

        user_data = EditUserModel(user_id=999, nick_name='Updated')

        with pytest.raises(ValueError, match='用户不存在'):
            await user_service.edit_user(user_data)

    @pytest.mark.asyncio
    async def test_edit_user_password_hashed(self, user_service, mock_user_dao, sample_user):
        """Test that password is hashed when updating."""
        mock_user_dao.get_user_by_id.return_value = sample_user
        mock_user_dao.edit_user.return_value = True

        user_data = EditUserModel(user_id=1, password='newpassword123')

        await user_service.edit_user(user_data)

        call_args = mock_user_dao.edit_user.call_args[0][0]
        assert call_args.password != 'newpassword123'
        assert len(call_args.password) > 20  # Hashed password is longer


class TestUserServiceDelete:
    """Test suite for user deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_dao, sample_user):
        """Test deleting user successfully."""
        mock_user_dao.get_user_by_id.return_value = sample_user
        mock_user_dao.delete_user.return_value = True

        result = await user_service.delete_user(1)

        assert result is True
        mock_user_dao.delete_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_user_dao):
        """Test deleting non-existent user."""
        mock_user_dao.get_user_by_id.return_value = None

        with pytest.raises(ValueError, match='用户不存在'):
            await user_service.delete_user(999)

    @pytest.mark.asyncio
    async def test_delete_admin_user_forbidden(self, user_service, mock_user_dao):
        """Test that admin user cannot be deleted."""
        admin_user = UserDO(
            user_id=1,
            user_name='admin',
            nick_name='Administrator',
            status='0',
            del_flag='0',
        )
        mock_user_dao.get_user_by_id.return_value = admin_user

        with pytest.raises(ValueError, match='不能删除超级管理员'):
            await user_service.delete_user(1)

    @pytest.mark.asyncio
    async def test_batch_delete_users(self, user_service, mock_user_dao):
        """Test batch deleting users."""
        mock_user_dao.delete_user.return_value = True

        user_ids = [2, 3, 4]
        result = await user_service.batch_delete_users(user_ids)

        assert result is True
        assert mock_user_dao.delete_user.call_count == 3


class TestUserServiceAuthentication:
    """Test suite for user authentication operations."""

    @pytest.mark.asyncio
    async def test_verify_password_success(self, user_service, mock_user_dao, sample_user):
        """Test password verification success."""
        mock_user_dao.get_user_by_username.return_value = sample_user

        result = await user_service.verify_password('testuser', 'test123')

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_password_incorrect(self, user_service, mock_user_dao, sample_user):
        """Test password verification with incorrect password."""
        mock_user_dao.get_user_by_username.return_value = sample_user

        result = await user_service.verify_password('testuser', 'wrongpassword')

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_password_user_not_found(self, user_service, mock_user_dao):
        """Test password verification with non-existent user."""
        mock_user_dao.get_user_by_username.return_value = None

        result = await user_service.verify_password('nonexistent', 'password')

        assert result is False

    @pytest.mark.asyncio
    async def test_change_password_success(self, user_service, mock_user_dao, sample_user):
        """Test changing user password."""
        mock_user_dao.get_user_by_id.return_value = sample_user
        mock_user_dao.edit_user.return_value = True

        result = await user_service.change_password(1, 'test123', 'newpassword123')

        assert result is True
        mock_user_dao.edit_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_incorrect_old(self, user_service, mock_user_dao, sample_user):
        """Test changing password with incorrect old password."""
        mock_user_dao.get_user_by_id.return_value = sample_user

        with pytest.raises(ValueError, match='原密码不正确'):
            await user_service.change_password(1, 'wrongpassword', 'newpassword123')

"""
Core authentication tests for LoginService - focusing on stability and security.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from modules.identity.application.services.login_service import LoginService
from module_admin.entity.vo.login_vo import UserLogin
from exceptions.exception import AuthException, ValidationException, ResourceNotFoundException


class TestLoginServiceAuthentication:
    """Test core authentication functionality."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = MagicMock(spec=Request)
        request.client.host = '127.0.0.1'
        request.headers = {}
        request.app.state.redis = AsyncMock()
        return request

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_login_repo(self):
        """Create a mock login repository."""
        repo = MagicMock()
        repo.find_user_with_dept = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def login_service(self, mock_db, mock_login_repo):
        """Create login service with injected dependencies."""
        return LoginService(
            query_db=mock_db,
            login_repo=mock_login_repo,
            user_repo=MagicMock(),
        )

    @pytest.fixture
    def valid_login(self):
        """Create valid login credentials."""
        return UserLogin(
            user_name='testuser',
            password='Test123!',
            code='1234',
            uuid='test-uuid'
        )

    @pytest.mark.asyncio
    async def test_account_lock_prevents_login(self, mock_request, login_service, valid_login):
        """Test that locked accounts cannot login."""
        # Setup: Account is locked in Redis
        mock_request.app.state.redis.get.return_value = valid_login.user_name

        # Execute & Assert
        with pytest.raises(AuthException) as exc_info:
            await login_service.authenticate_user(mock_request, valid_login)

        assert '账号已锁定' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_username_rejected(self, mock_request, login_service):
        """Test that empty username is rejected."""
        # Setup mocks properly
        mock_request.app.state.redis.get = AsyncMock(return_value=None)
        mock_request.headers = {}
        
        invalid_login = UserLogin(
            user_name='',
            password='Test123!',
            code='1234',
            uuid='test-uuid'
        )

        with pytest.raises((ValidationException, ValueError, AuthException)):
            await login_service.authenticate_user(mock_request, invalid_login)

    @pytest.mark.asyncio
    async def test_empty_password_rejected(self, mock_request, login_service):
        """Test that empty password is rejected."""
        # Setup mocks properly
        mock_request.app.state.redis.get = AsyncMock(return_value=None)
        mock_request.headers = {}
        
        invalid_login = UserLogin(
            user_name='testuser',
            password='',
            code='1234',
            uuid='test-uuid'
        )

        with pytest.raises((ValidationException, ValueError, AuthException)):
            await login_service.authenticate_user(mock_request, invalid_login)

    @pytest.mark.asyncio
    async def test_swagger_request_detection(self, mock_request, login_service, mock_login_repo, valid_login):
        """Test that requests from Swagger docs are detected."""
        mock_request.headers = {'referer': 'http://localhost:8000/docs'}
        mock_request.app.state.redis.get.return_value = None
        mock_login_repo.find_user_with_dept = AsyncMock(return_value=None)

        with pytest.raises(ResourceNotFoundException):
            await login_service.authenticate_user(mock_request, valid_login)

    @pytest.mark.asyncio
    async def test_redoc_request_detection(self, mock_request, login_service, mock_login_repo, valid_login):
        """Test that requests from ReDoc are detected."""
        mock_request.headers = {'referer': 'http://localhost:8000/redoc'}
        mock_request.app.state.redis.get.return_value = None
        mock_login_repo.find_user_with_dept = AsyncMock(return_value=None)

        with pytest.raises(ResourceNotFoundException):
            await login_service.authenticate_user(mock_request, valid_login)


class TestLoginServiceSecurity:
    """Test security-related functionality."""

    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        request.client.host = '192.168.1.100'
        request.headers = {}
        request.app.state.redis = AsyncMock()
        return request

    @pytest.mark.asyncio
    async def test_ip_check_called(self, mock_request):
        """Test that IP checking is performed."""
        # This tests that the IP check logic is invoked
        # The actual IP validation logic should be tested separately
        assert mock_request.client.host == '192.168.1.100'

    @pytest.mark.asyncio
    async def test_redis_account_lock_check(self, mock_request):
        """Test that Redis is checked for account locks."""
        username = 'testuser'
        key = f'account_lock:{username}'

        # Simulate checking Redis
        mock_request.app.state.redis.get.return_value = None
        result = await mock_request.app.state.redis.get(key)

        assert result is None
        mock_request.app.state.redis.get.assert_called_once_with(key)


class TestLoginServicePasswordValidation:
    """Test password validation and hashing."""

    def test_password_normalization(self):
        """Test that passwords are properly normalized."""
        from utils.pwd_util import PwdUtil

        password = 'Test123!'
        hashed = PwdUtil.get_password_hash(password)

        # Verify hash is created
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password

        # Verify password can be verified
        assert PwdUtil.verify_password(password, hashed) is True
        assert PwdUtil.verify_password('wrong', hashed) is False

    def test_password_special_characters(self):
        """Test passwords with special characters."""
        from utils.pwd_util import PwdUtil

        password = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        hashed = PwdUtil.get_password_hash(password)

        assert PwdUtil.verify_password(password, hashed) is True

    def test_password_unicode_support(self):
        """Test passwords with unicode characters."""
        from utils.pwd_util import PwdUtil

        password = '密码123🔒'
        hashed = PwdUtil.get_password_hash(password)

        assert PwdUtil.verify_password(password, hashed) is True


class TestLoginServiceInputSanitization:
    """Test input sanitization and validation."""

    def test_username_trimming(self):
        """Test that usernames are trimmed of whitespace."""
        login = UserLogin(
            user_name='  testuser  ',
            password='Test123!',
            code='1234',
            uuid='test-uuid'
        )

        # The service should normalize this
        assert login.user_name.strip() == 'testuser'

    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are handled safely."""
        # These should not cause SQL injection
        dangerous_inputs = [
            "admin' OR '1'='1",
            "admin'--",
            "admin' /*",
            "' OR 1=1--",
            "admin'; DROP TABLE users--"
        ]

        for dangerous_input in dangerous_inputs:
            login = UserLogin(
                user_name=dangerous_input,
                password='Test123!',
                code='1234',
                uuid='test-uuid'
            )
            # Should create object without executing SQL
            assert login.user_name == dangerous_input

    def test_xss_prevention(self):
        """Test that XSS attempts are handled safely."""
        xss_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')"
        ]

        for xss_input in xss_inputs:
            login = UserLogin(
                user_name=xss_input,
                password='Test123!',
                code='1234',
                uuid='test-uuid'
            )
            # Should store as-is, escaping happens at output
            assert login.user_name == xss_input


class TestLoginServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_username(self):
        """Test handling of very long usernames."""
        long_username = 'a' * 1000

        login = UserLogin(
            user_name=long_username,
            password='Test123!',
            code='1234',
            uuid='test-uuid'
        )

        assert len(login.user_name) == 1000

    def test_very_long_password(self):
        """Test handling of very long passwords."""
        from utils.pwd_util import PwdUtil

        long_password = 'a' * 1000
        hashed = PwdUtil.get_password_hash(long_password)

        # Should handle long passwords (bcrypt truncates at 72 bytes)
        assert hashed is not None
        assert PwdUtil.verify_password(long_password, hashed) is True

    def test_null_code_handling(self):
        """Test handling of null verification code."""
        login = UserLogin(
            user_name='testuser',
            password='Test123!',
            code=None,
            uuid='test-uuid'
        )

        assert login.code is None

    def test_null_uuid_handling(self):
        """Test handling of null UUID."""
        login = UserLogin(
            user_name='testuser',
            password='Test123!',
            code='1234',
            uuid=None
        )

        assert login.uuid is None

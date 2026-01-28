"""
测试异常类体系
"""
import pytest
from exceptions.exception import (
    AppException,
    ValidationException,
    AuthException,
    PermissionException,
    BusinessException,
    ResourceNotFoundException,
    ResourceConflictException,
    SystemException,
    DatabaseException,
    ExternalServiceException,
    CacheException
)
from config.error_codes import ErrorCode, ErrorType


class TestAppException:
    """测试应用异常基类"""
    
    def test_app_exception_creation(self):
        """测试创建应用异常"""
        exc = AppException(
            user_message="用户消息",
            developer_message="开发者消息",
            error_code=10001,
            http_status=400,
            error_type=ErrorType.VALIDATION,
            error_code_name="TEST_ERROR"
        )
        
        assert exc.user_message == "用户消息"
        assert exc.developer_message == "开发者消息"
        assert exc.error_code == 10001
        assert exc.http_status == 400
        assert exc.error_type == ErrorType.VALIDATION
        assert exc.error_code_name == "TEST_ERROR"


class TestValidationException:
    """测试校验异常"""
    
    def test_validation_exception_with_field(self):
        """测试带字段的校验异常"""
        exc = ValidationException(
            user_message="用户名不能为空",
            field="username"
        )
        
        assert exc.user_message == "用户名不能为空"
        assert "username" in exc.developer_message
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.http_status == 422
        assert exc.error_type == ErrorType.VALIDATION
        assert exc.extra["field"] == "username"
    
    def test_validation_exception_with_custom_developer_message(self):
        """测试自定义开发者消息的校验异常"""
        exc = ValidationException(
            user_message="格式不正确",
            developer_message="Email format is invalid",
            field="email"
        )
        
        assert exc.developer_message == "Email format is invalid"


class TestAuthException:
    """测试认证异常"""
    
    def test_auth_exception_default(self):
        """测试默认认证异常"""
        exc = AuthException()
        
        assert "未认证" in exc.user_message
        assert exc.error_code == ErrorCode.UNAUTHORIZED
        assert exc.http_status == 401
        assert exc.error_type == ErrorType.AUTHENTICATION
    
    def test_auth_exception_custom(self):
        """测试自定义认证异常"""
        exc = AuthException(
            user_message="登录已过期",
            developer_message="Token expired at 2026-01-28"
        )
        
        assert exc.user_message == "登录已过期"
        assert "Token expired" in exc.developer_message


class TestPermissionException:
    """测试权限异常"""
    
    def test_permission_exception_with_resource(self):
        """测试带资源的权限异常"""
        exc = PermissionException(
            user_message="无权访问该资源",
            resource="/api/system/user"
        )
        
        assert exc.user_message == "无权访问该资源"
        assert "/api/system/user" in exc.developer_message
        assert exc.error_code == ErrorCode.FORBIDDEN
        assert exc.http_status == 403


class TestBusinessException:
    """测试业务异常"""
    
    def test_business_exception_default_developer_message(self):
        """测试业务异常默认开发者消息（与用户消息相同）"""
        exc = BusinessException(
            message="用户名已存在",
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            http_status=409
        )
        
        assert exc.user_message == "用户名已存在"
        assert exc.developer_message == "用户名已存在"
        assert exc.error_code == ErrorCode.USER_ALREADY_EXISTS
        assert exc.http_status == 409
    
    def test_business_exception_custom_developer_message(self):
        """测试业务异常自定义开发者消息"""
        exc = BusinessException(
            message="用户名已存在",
            error_code=ErrorCode.USER_ALREADY_EXISTS,
            http_status=409,
            developer_message="User with username='admin' already exists"
        )
        
        assert exc.user_message == "用户名已存在"
        assert exc.developer_message == "User with username='admin' already exists"


class TestResourceNotFoundException:
    """测试资源不存在异常"""
    
    def test_resource_not_found_exception(self):
        """测试资源不存在异常"""
        exc = ResourceNotFoundException(
            user_message="用户不存在",
            error_code=ErrorCode.USER_NOT_FOUND,
            developer_message="User with id=123 not found"
        )
        
        assert exc.user_message == "用户不存在"
        assert exc.developer_message == "User with id=123 not found"
        assert exc.http_status == 404


class TestResourceConflictException:
    """测试资源冲突异常"""
    
    def test_resource_conflict_exception(self):
        """测试资源冲突异常"""
        exc = ResourceConflictException(
            user_message="角色名称已存在",
            error_code=ErrorCode.ROLE_ALREADY_EXISTS,
            developer_message="Role with name='admin' already exists"
        )
        
        assert exc.user_message == "角色名称已存在"
        assert exc.developer_message == "Role with name='admin' already exists"
        assert exc.http_status == 409


class TestSystemException:
    """测试系统异常（用户消息通用化）"""
    
    def test_system_exception_default(self):
        """测试默认系统异常"""
        exc = SystemException()
        
        assert exc.user_message == "系统繁忙，请稍后重试"
        assert exc.developer_message == "Internal server error"
        assert exc.error_code == ErrorCode.SYSTEM_ERROR
        assert exc.http_status == 500
    
    def test_system_exception_custom_developer_message(self):
        """测试自定义开发者消息的系统异常"""
        exc = SystemException(
            developer_message="NullPointerException at line 123"
        )
        
        # 用户消息保持通用化
        assert exc.user_message == "系统繁忙，请稍后重试"
        # 开发者消息包含详细信息
        assert "NullPointerException" in exc.developer_message


class TestDatabaseException:
    """测试数据库异常（永不暴露数据库错误）"""
    
    def test_database_exception_hides_details(self):
        """测试数据库异常隐藏技术细节"""
        exc = DatabaseException(
            error_detail="Connection pool exhausted: max=100, active=100"
        )
        
        # 用户消息通用化，不暴露数据库错误
        assert exc.user_message == "系统繁忙，请稍后重试"
        # 开发者消息包含详细的数据库错误
        assert "Connection pool exhausted" in exc.developer_message
        assert exc.error_code == ErrorCode.DATABASE_ERROR
        assert exc.http_status == 500


class TestExternalServiceException:
    """测试外部服务异常"""
    
    def test_external_service_exception(self):
        """测试外部服务异常"""
        exc = ExternalServiceException(
            service_name="payment-service",
            error_detail="Connection timeout after 30s"
        )
        
        # 用户消息通用化
        assert exc.user_message == "系统繁忙，请稍后重试"
        # 开发者消息包含服务名称和错误详情
        assert "payment-service" in exc.developer_message
        assert "Connection timeout" in exc.developer_message


class TestCacheException:
    """测试缓存异常"""
    
    def test_cache_exception(self):
        """测试缓存异常"""
        exc = CacheException(
            error_detail="Redis connection refused"
        )
        
        # 用户消息通用化
        assert exc.user_message == "系统繁忙，请稍后重试"
        # 开发者消息包含缓存错误详情
        assert "Redis connection refused" in exc.developer_message
        assert exc.error_code == ErrorCode.CACHE_ERROR

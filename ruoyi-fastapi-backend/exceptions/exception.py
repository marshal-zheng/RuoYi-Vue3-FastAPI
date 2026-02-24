"""
异常体系（支持双层消息设计）
遵循 RFC 7807 标准和双层消息最佳实践
"""
from typing import Optional, Any
from config.error_codes import ErrorCode, ErrorType


class AppException(Exception):
    """应用异常基类（支持双层消息）"""
    
    def __init__(
        self,
        user_message: str,           # 用户消息（前端展示）
        developer_message: str,      # 开发者消息（日志记录）
        error_code: int,
        http_status: int,
        error_type: str,
        data: Optional[Any] = None,
        error_code_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(user_message)
        self.user_message = user_message
        self.message = user_message
        self.developer_message = developer_message
        self.error_code = error_code
        self.http_status = http_status
        self.error_type = error_type
        self.data = data
        self.error_code_name = error_code_name
        self.extra = kwargs  # 额外字段（如 field, value, username 等）


class ValidationException(AppException):
    """校验异常"""
    
    def __init__(
        self, 
        user_message: str = "参数校验失败",
        developer_message: Optional[str] = None, 
        field: Optional[str] = None, 
        error_code: int = ErrorCode.VALIDATION_ERROR,
        **kwargs
    ):
        super().__init__(
            user_message=user_message,
            developer_message=developer_message or f"Validation failed for field: {field}",
            error_code=error_code,
            http_status=422,
            error_type=ErrorType.VALIDATION,
            error_code_name="VALIDATION_ERROR",
            field=field,
            **kwargs
        )


class AuthException(AppException):
    """认证异常"""
    
    def __init__(
        self, 
        user_message: str = "未认证，请先登录",
        developer_message: Optional[str] = None,
        error_code: int = ErrorCode.UNAUTHORIZED,
        **kwargs
    ):
        super().__init__(
            user_message=user_message,
            developer_message=developer_message or "Authentication token missing or invalid",
            error_code=error_code,
            http_status=401,
            error_type=ErrorType.AUTHENTICATION,
            error_code_name="UNAUTHORIZED",
            **kwargs
        )


class PermissionException(AppException):
    """权限异常"""
    
    def __init__(
        self, 
        user_message: str = "权限不足，无法执行此操作",
        developer_message: Optional[str] = None,
        resource: Optional[str] = None,
        error_code: int = ErrorCode.FORBIDDEN,
        **kwargs
    ):
        dev_msg = developer_message or f"User does not have permission to access: {resource}"
        super().__init__(
            user_message=user_message,
            developer_message=dev_msg,
            error_code=error_code,
            http_status=403,
            error_type=ErrorType.AUTHORIZATION,
            error_code_name="FORBIDDEN",
            resource=resource,
            **kwargs
        )


class BusinessException(AppException):
    """业务异常（用户消息 = 开发者消息，或略有差异）"""
    
    def __init__(
        self, 
        user_message: str,
        error_code: int, 
        http_status: int = 400, 
        developer_message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            user_message=user_message,
            developer_message=developer_message or user_message,  # 默认相同
            error_code=error_code,
            http_status=http_status,
            error_type=ErrorType.BUSINESS,
            **kwargs
        )


class ResourceNotFoundException(BusinessException):
    """资源不存在"""
    
    def __init__(
        self, 
        user_message: str = "资源不存在",
        error_code: int = ErrorCode.SYSTEM_ERROR,
        developer_message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            user_message=user_message,
            error_code=error_code,
            http_status=404,
            developer_message=developer_message,
            **kwargs
        )


class ResourceConflictException(BusinessException):
    """资源冲突"""
    
    def __init__(
        self, 
        user_message: str = "资源冲突",
        error_code: int = ErrorCode.SYSTEM_ERROR,
        developer_message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            user_message=user_message,
            error_code=error_code,
            http_status=409,
            developer_message=developer_message,
            **kwargs
        )


class SystemException(AppException):
    """系统异常（用户消息通用化，开发者消息详细化）"""
    
    def __init__(
        self, 
        user_message: str = "系统繁忙，请稍后重试",
        developer_message: Optional[str] = None,
        error_code: int = ErrorCode.SYSTEM_ERROR,
        **kwargs
    ):
        super().__init__(
            user_message=user_message,
            developer_message=developer_message or "Internal server error",
            error_code=error_code,
            http_status=500,
            error_type=ErrorType.SYSTEM,
            error_code_name="SYSTEM_ERROR",
            **kwargs
        )


class DatabaseException(SystemException):
    """数据库异常（永远不向用户暴露数据库错误）"""
    
    def __init__(self, error_detail: str, **kwargs):
        super().__init__(
            user_message="系统繁忙，请稍后重试",
            developer_message=f"Database operation failed: {error_detail}",
            error_code=ErrorCode.DATABASE_ERROR,
            **kwargs
        )


class ExternalServiceException(SystemException):
    """外部服务异常"""
    
    def __init__(self, service_name: str, error_detail: str, **kwargs):
        super().__init__(
            user_message="系统繁忙，请稍后重试",
            developer_message=f"External service call failed: service={service_name}, error={error_detail}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            **kwargs
        )


class CacheException(SystemException):
    """缓存异常"""
    
    def __init__(self, error_detail: str, **kwargs):
        super().__init__(
            user_message="系统繁忙，请稍后重试",
            developer_message=f"Cache operation failed: {error_detail}",
            error_code=ErrorCode.CACHE_ERROR,
            **kwargs
        )


# ==================== 兼容旧代码的异常类（标记为废弃）====================

class ServiceException(AppException):
    """
    服务异常（兼容旧代码，建议使用具体异常类型）
    
    @deprecated: 请使用 BusinessException, SystemException 等具体异常类型
    """
    
    def __init__(self, message: str, developer_message: Optional[str] = None, **kwargs):
        import warnings
        warnings.warn(
            "ServiceException is deprecated, use BusinessException or SystemException instead",
            DeprecationWarning,
            stacklevel=2
        )
        error_code = kwargs.pop('error_code', ErrorCode.SYSTEM_ERROR)
        http_status = kwargs.pop('http_status', 500)
        
        super().__init__(
            user_message=message,
            developer_message=developer_message or message,
            error_code=error_code,
            http_status=http_status,
            error_type=ErrorType.SYSTEM,
            **kwargs
        )


class LoginException(AuthException):
    """
    登录异常（兼容旧代码）
    
    @deprecated: 请使用 AuthException
    """
    
    def __init__(self, message: str = "登录失败", data: Optional[Any] = None, **kwargs):
        import warnings
        warnings.warn(
            "LoginException is deprecated, use AuthException instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        super().__init__(
            user_message=message,
            developer_message=f"Login failed: {message}",
            data=data,
            **kwargs
        )


class ModelValidatorException(ValidationException):
    """
    模型校验异常（兼容旧代码）
    
    @deprecated: 请使用 ValidationException
    """
    
    def __init__(self, message: str, data: Optional[Any] = None, **kwargs):
        import warnings
        warnings.warn(
            "ModelValidatorException is deprecated, use ValidationException instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        super().__init__(
            user_message=message,
            developer_message=f"Model validation failed: {message}",
            data=data,
            **kwargs
        )


class ServiceWarning(AppException):
    """
    服务警告（兼容旧代码）
    
    @deprecated: 请使用 BusinessException
    """
    
    def __init__(self, message: str, data: Optional[Any] = None, **kwargs):
        import warnings
        warnings.warn(
            "ServiceWarning is deprecated, use BusinessException instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        super().__init__(
            user_message=message,
            developer_message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            http_status=400,
            error_type=ErrorType.BUSINESS,
            error_code_name="SERVICE_WARNING",
            data=data,
            **kwargs
        )

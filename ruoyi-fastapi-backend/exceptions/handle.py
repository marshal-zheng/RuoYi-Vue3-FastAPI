from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from pydantic import ValidationError
from pydantic_validation_decorator import FieldValidationError

# 导入异常类
from exceptions.exception import (
    AppException,
    ValidationException,
    AuthException,
    PermissionException,
    BusinessException,
    SystemException,
    DatabaseException,
    # 兼容旧代码的异常类
    ServiceException,
    LoginException,
    ModelValidatorException,
    ServiceWarning,
)

# 导入新的响应工具
from utils.response_util import ResponseUtil

# 导入错误码和消息
from config.error_codes import ErrorCode, ErrorType, get_error_info
from config.error_messages import get_user_message, get_developer_message

# 导入日志和 RequestId
from utils.log_util import logger
from middlewares.trace_middleware import get_request_id

DEFAULT_ERROR_MSG = '接口异常'


def handle_exception(app: FastAPI):
    """
    全局异常处理（RFC 7807 标准 + 双层消息设计）
    
    遵循最佳实践：
    1. 所有异常返回 RFC 7807 格式
    2. 使用真实 HTTP 状态码
    3. 双层消息设计：用户消息（前端展示）+ 开发者消息（日志记录）
    4. 系统异常不向用户暴露技术细节
    5. 所有响应包含 requestId 用于追踪
    """

    # 应用异常处理器（新异常体系）
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理所有 AppException 及其子类"""
        request_id = get_request_id()
        
        # 记录日志（包含完整的开发者消息）
        log_message = (
            f"[{request_id}] {exc.error_type}: "
            f"user_message='{exc.user_message}', "
            f"developer_message='{exc.developer_message}', "
            f"error_code={exc.error_code}, "
            f"http_status={exc.http_status}"
        )
        
        if exc.http_status >= 500:
            logger.error(log_message)
        elif exc.http_status >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # 返回 RFC 7807 响应
        return ResponseUtil.problem_details(
            request=request,
            error_code=exc.error_code,
            user_message=exc.user_message,
            developer_message=exc.developer_message,
            http_status=exc.http_status,
            error_type=exc.error_type,
            error_code_name=exc.error_code_name,
            data=exc.data,
            **exc.extra
        )
    
    # Pydantic 校验错误处理器
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """处理 Pydantic 校验错误（422）"""
        request_id = get_request_id()
        
        # 构建字段级错误列表
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "code": error["type"].upper()
            })
        
        # 开发者消息：详细错误信息
        developer_message = f"Pydantic validation failed: {len(errors)} errors - {errors}"
        
        # 记录日志
        logger.warning(f"[{request_id}] {developer_message}")
        
        # 返回 RFC 7807 校验错误响应
        return ResponseUtil.validation_problem(
            request=request,
            errors=errors,
            developer_message=developer_message
        )
    
    # FieldValidationError 处理器（兼容旧代码）
    @app.exception_handler(FieldValidationError)
    async def field_validation_error_handler(request: Request, exc: FieldValidationError):
        """处理字段校验错误（兼容旧代码）"""
        request_id = get_request_id()
        
        # 构建错误列表
        errors = [{
            "field": "unknown",
            "message": exc.message,
            "code": "FIELD_VALIDATION_ERROR"
        }]
        
        developer_message = f"Field validation failed: {exc.message}"
        logger.warning(f"[{request_id}] {developer_message}")
        
        return ResponseUtil.validation_problem(
            request=request,
            errors=errors,
            developer_message=developer_message
        )
    
    # HTTP 异常处理器
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理 FastAPI HTTPException"""
        request_id = get_request_id()
        
        # 用户消息：使用异常的 detail
        user_message = exc.detail
        
        # 开发者消息：包含 HTTP 状态码
        developer_message = f"HTTP {exc.status_code}: {exc.detail}"
        
        # 记录日志
        if exc.status_code >= 500:
            logger.error(f"[{request_id}] {developer_message}")
        else:
            logger.warning(f"[{request_id}] {developer_message}")
        
        # 返回 RFC 7807 响应
        return ResponseUtil.problem_details(
            request=request,
            error_code=exc.status_code,
            user_message=user_message,
            developer_message=developer_message,
            http_status=exc.status_code,
            error_type=ErrorType.SYSTEM
        )
    
    # 通用异常处理器（兜底）
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        处理所有未捕获的异常（兜底处理器）
        
        关键设计：
        - 用户消息：通用化（"系统繁忙，请稍后重试"）
        - 开发者消息：详细错误信息和堆栈跟踪
        - 永远不向用户暴露技术细节
        """
        request_id = get_request_id()
        
        # 用户消息：通用化，不暴露技术细节
        user_message = "系统繁忙，请稍后重试"
        
        # 开发者消息：详细错误信息
        exception_type = type(exc).__name__
        exception_message = str(exc)
        developer_message = f"Unhandled exception: {exception_type}: {exception_message}"
        
        # 记录完整堆栈跟踪（仅在日志中）
        logger.exception(f"[{request_id}] {developer_message}")
        
        # 返回 RFC 7807 响应
        return ResponseUtil.problem_details(
            request=request,
            error_code=ErrorCode.SYSTEM_ERROR,
            user_message=user_message,
            developer_message=developer_message,
            http_status=500,
            error_type=ErrorType.SYSTEM,
            error_code_name="SYSTEM_ERROR"
        )

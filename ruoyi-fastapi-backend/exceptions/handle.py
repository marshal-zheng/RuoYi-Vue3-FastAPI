from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pydantic_validation_decorator import FieldValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 导入错误码和消息
from config.error_codes import ErrorCode, ErrorType

# 导入异常类
from exceptions.exception import (
    AppException,
    AuthException,
    BusinessException,
    DatabaseException,
    LoginException,
    ModelValidatorException,
    PermissionException,
    # 兼容旧代码的异常类
    ServiceException,
    ServiceWarning,
    SystemException,
    ValidationException,
)
from middlewares.trace_middleware import get_request_id
from utils.log_safety import database_exception, log_safe_exception, safe_exception_summary

# 导入日志和 RequestId
from utils.log_util import logger

# 导入新的响应工具
from utils.response_util import ResponseUtil

DEFAULT_ERROR_MSG = '接口异常'

_PROBLEM_TYPE_SLUGS = {
    ErrorCode.VALIDATION_ERROR: 'validation-error',
    ErrorCode.UNAUTHORIZED: 'unauthorized',
    ErrorCode.FORBIDDEN: 'forbidden',
    ErrorCode.SYSTEM_ERROR: None,
    ErrorCode.DATABASE_ERROR: 'database-error',
    ErrorCode.EXTERNAL_SERVICE_ERROR: 'external-service-error',
    ErrorCode.CACHE_ERROR: 'cache-error',
}


def _resolve_problem_type_slug(error_code: int | None, fallback: str | None = None) -> str | None:
    if fallback:
        return str(fallback).strip().lower().replace('_', '-')
    if error_code is None:
        return None
    return _PROBLEM_TYPE_SLUGS.get(int(error_code))


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
            f"user_message='{'系统繁忙，请稍后重试' if database_exception(exc) else exc.user_message}', "
            f"developer_message='{safe_exception_summary(exc) if database_exception(exc) else exc.developer_message}', "
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
        errors = None
        field = exc.extra.get('field') if hasattr(exc, 'extra') else None
        if exc.http_status == 422 and field:
            errors = [{'field': field, 'message': exc.user_message, 'code': 'value_error'}]

        return ResponseUtil.problem_details(
            request=request,
            http_status=exc.http_status,
            title='系统繁忙，请稍后重试' if database_exception(exc) else exc.user_message,
            detail='系统繁忙，请稍后重试' if database_exception(exc) else exc.user_message,
            type_slug=_resolve_problem_type_slug(exc.error_code, exc.error_code_name),
            error_code=exc.error_code,
            errors=errors,
        )
    
    # Pydantic 校验错误处理器
    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        """处理 FastAPI 请求参数校验错误（422）"""
        request_id = get_request_id()

        errors = []
        for error in exc.errors():
            loc = [str(item) for item in error.get('loc', ())]
            # Only the transport prefix is metadata; document.body is a real field.
            field = ".".join(loc[1:] if loc[:1] == ['body'] else loc) or "unknown"
            errors.append(
                {
                    "field": field,
                    "message": error.get('msg', 'Validation failed'),
                    "code": str(error.get('type', 'validation_error')),
                }
            )

        developer_message = f"Request validation failed: {len(errors)} errors - {errors}"
        logger.warning(f"[{request_id}] {developer_message}")

        return ResponseUtil.validation_problem(
            request=request,
            errors=errors,
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
                "code": error["type"]
            })
        
        # 开发者消息：详细错误信息
        developer_message = f"Pydantic validation failed: {len(errors)} errors - {errors}"
        
        # 记录日志
        logger.warning(f"[{request_id}] {developer_message}")
        
        # 返回 RFC 7807 校验错误响应
        return ResponseUtil.validation_problem(
            request=request,
            errors=errors,
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
            "code": "field_validation_error"
        }]
        
        developer_message = f"Field validation failed: {exc.message}"
        logger.warning(f"[{request_id}] {developer_message}")
        
        return ResponseUtil.validation_problem(
            request=request,
            errors=errors,
        )
    
    # HTTP 异常处理器
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
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
            http_status=exc.status_code,
            title=user_message,
            detail=user_message,
            type_slug=None if exc.status_code >= 500 else f'http-{exc.status_code}',
            error_code=exc.status_code,
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
        exception_message = safe_exception_summary(exc)
        developer_message = f"Unhandled exception: {exception_message}"
        
        # 记录完整堆栈跟踪（仅在日志中）
        log_safe_exception(logger, f"[{request_id}] {developer_message}", exc)
        
        # 返回 RFC 7807 响应
        return ResponseUtil.problem_details(
            request=request,
            http_status=500,
            title=user_message,
            detail=user_message,
            type_slug=_resolve_problem_type_slug(ErrorCode.SYSTEM_ERROR),
            error_code=ErrorCode.SYSTEM_ERROR,
        )

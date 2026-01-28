"""
响应工具类（RFC 7807 标准 + 双层消息设计）

遵循 RFC 7807 Problem Details for HTTP APIs 标准
支持双层消息设计：用户消息 + 开发者消息

迁移说明：
- success(msg=xxx) -> success(message=xxx) （推荐）
- failure/unauthorized/forbidden/error -> 已废弃，建议使用异常类
- streaming() -> 保持不变
"""
from datetime import datetime
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask
from typing import Any, Dict, List, Mapping, Optional

from config.constant import HttpStatusConstant
from config.env import ErrorHandlingConfig
from middlewares.trace_middleware import get_request_id
from utils.response_serializer import serialize_for_response


def _merge_model_content(result: Dict[str, Any], model_content: Any) -> None:
    """合并 Pydantic 模型或字典内容到结果中"""
    if model_content is None:
        return
    serialized = serialize_for_response(model_content)
    if isinstance(serialized, Mapping):
        result.update(dict(serialized))
        return
    # Fallback: attach as data to avoid hard failures
    result['data'] = serialized


def _apply_payload(
    result: Dict[str, Any],
    data: Optional[Any],
    rows: Optional[Any],
    dict_content: Optional[Dict],
    model_content: Optional[BaseModel],
) -> None:
    if data is not None:
        result['data'] = serialize_for_response(data)
    if rows is not None:
        result['rows'] = serialize_for_response(rows)
    if dict_content is not None:
        serialized_dict = serialize_for_response(dict_content)
        if isinstance(serialized_dict, Mapping):
            result.update(dict(serialized_dict))
        else:
            result['data'] = serialized_dict
    _merge_model_content(result, model_content)


class ResponseUtil:
    """响应工具类（RFC 7807 标准 + 双层消息）"""
    
    # ==================== 新标准方法（RFC 7807）====================
    
    @classmethod
    def success(
        cls,
        msg: Optional[str] = None,
        message: Optional[str] = None,
        data: Optional[Any] = None,
        rows: Optional[Any] = None,
        dict_content: Optional[Dict] = None,
        model_content: Optional[BaseModel] = None,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
        http_status: int = status.HTTP_200_OK,
    ) -> Response:
        """
        成功响应（HTTP 2xx + RFC 7807 标准）

        Args:
            msg: 可选，自定义成功响应信息（已废弃，请使用 message）
            message: 可选，自定义成功响应信息（推荐使用）
            data: 可选，成功响应结果中属性为data的值
            rows: 可选，成功响应结果中属性为rows的值
            dict_content: 可选，dict类型，成功响应结果中自定义属性的值
            model_content: 可选，BaseModel或Mapping类型，成功响应结果中自定义属性的值
            headers: 可选，响应头信息
            media_type: 可选，响应结果媒体类型
            background: 可选，响应返回后执行的后台任务
            http_status: HTTP 状态码（默认 200）
            
        Returns:
            JSONResponse: 成功响应 {data, message, requestId}
        """
        # 支持新旧参数名，优先使用 message
        final_message = message if message is not None else (msg if msg is not None else '操作成功')
        request_id = get_request_id()
        
        # 构建数据对象 - 统一响应格式标准：
        # 1. data 参数直接作为 result["data"] 返回，不做包装
        # 2. rows/dict_content/model_content 合并到 dict 中
        result_data: Any = None
        
        if data is not None:
            result_data = serialize_for_response(data)
        
        # 如果有额外字段需要合并，确保 result_data 是 dict
        if rows is not None or dict_content is not None or model_content is not None:
            if result_data is None:
                result_data = {}
            elif not isinstance(result_data, dict):
                # 如果 data 不是 dict 但有其他字段要合并，包装为 {"data": ...}
                result_data = {"data": result_data}
            
            if rows is not None:
                result_data["rows"] = serialize_for_response(rows)
            if dict_content is not None:
                serialized_dict = serialize_for_response(dict_content)
                if isinstance(serialized_dict, Mapping):
                    result_data.update(dict(serialized_dict))
                else:
                    result_data["extra"] = serialized_dict
            _merge_model_content(result_data, model_content)
        
        # RFC 7807 标准成功响应
        result = {
            "data": result_data if result_data else None,
            "message": final_message,
            "requestId": request_id
        }
        
        response_headers = {"X-Request-Id": request_id}
        if headers:
            response_headers.update(headers)
        
        return JSONResponse(
            status_code=http_status,
            content=jsonable_encoder(result),
            headers=response_headers,
            media_type=media_type,
            background=background,
        )
    
    @classmethod
    def problem_details(
        cls,
        request: Request,
        error_code: int,
        user_message: str,
        developer_message: str,
        http_status: int,
        error_type: str,
        error_code_name: Optional[str] = None,
        data: Optional[Any] = None,
        **kwargs
    ) -> Response:
        """
        RFC 7807 错误响应（双层消息）
        
        Args:
            request: FastAPI Request 对象
            error_code: 业务错误码
            user_message: 用户友好的错误消息（前端展示）
            developer_message: 开发者详细错误消息（日志记录）
            http_status: HTTP 状态码
            error_type: 错误类型
            error_code_name: 错误码名称
            data: 额外数据
            **kwargs: 其他字段（如 field, username 等）
            
        Returns:
            JSONResponse: RFC 7807 格式的错误响应
        """
        request_id = get_request_id()
        
        # 构建 RFC 7807 响应
        result = {
            "type": f"https://api.example.com/problems/{error_code_name or 'error'}",
            "title": user_message,
            "status": http_status,
            "detail": user_message,
            "instance": str(request.url.path),
            "errorCode": error_code,
            "requestId": request_id
        }
        
        # 开发环境：包含开发者消息
        if ErrorHandlingConfig.include_developer_message:
            result["developerMessage"] = developer_message
        
        # 添加额外数据
        if data is not None:
            result["data"] = serialize_for_response(data)
        
        # 添加额外字段
        if kwargs:
            result.update(serialize_for_response(kwargs))
        
        return JSONResponse(
            status_code=http_status,
            content=jsonable_encoder(result),
            headers={
                "X-Request-Id": request_id,
                "Content-Type": "application/problem+json"
            }
        )
    
    @classmethod
    def validation_problem(
        cls,
        request: Request,
        errors: List[Dict[str, str]],
        developer_message: Optional[str] = None
    ) -> Response:
        """
        RFC 7807 校验错误响应（双层消息）
        
        Args:
            request: FastAPI Request 对象
            errors: 校验错误列表 [{"field": "xxx", "message": "xxx", "code": "xxx"}]
            developer_message: 开发者消息（可选）
            
        Returns:
            JSONResponse: RFC 7807 格式的校验错误响应
        """
        request_id = get_request_id()
        
        result = {
            "type": "https://api.example.com/problems/validation-error",
            "title": "参数验证失败",
            "status": 422,
            "detail": "请检查输入的信息是否正确",
            "instance": str(request.url.path),
            "errorCode": 10001,
            "requestId": request_id,
            "errors": serialize_for_response(errors),
        }
        
        # 开发环境：包含开发者消息
        if ErrorHandlingConfig.include_developer_message and developer_message:
            result["developerMessage"] = developer_message
        
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(result),
            headers={
                "X-Request-Id": request_id,
                "Content-Type": "application/problem+json"
            }
        )
    
    @classmethod
    def streaming(
        cls,
        *,
        data: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ) -> Response:
        """
        流式响应方法（用于文件下载等场景）

        Args:
            data: 流式传输的内容
            headers: 可选，响应头信息
            media_type: 可选，响应结果媒体类型
            background: 可选，响应返回后执行的后台任务
            
        Returns:
            StreamingResponse: 流式响应结果
        """
        request_id = get_request_id()
        
        response_headers = {"X-Request-Id": request_id}
        if headers:
            response_headers.update(headers)
        
        return StreamingResponse(
            status_code=status.HTTP_200_OK,
            content=data,
            headers=response_headers,
            media_type=media_type,
            background=background
        )
    
    # ==================== 兼容旧代码的方法（标记为废弃）====================

    
    @classmethod
    def failure(
        cls,
        msg: str = '操作失败',
        data: Optional[Any] = None,
        rows: Optional[Any] = None,
        dict_content: Optional[Dict] = None,
        model_content: Optional[BaseModel] = None,
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ) -> Response:
        """
        失败响应方法（已废弃，建议抛出异常）

        @deprecated: 请使用异常类（ValidationException, BusinessException等）
        """
        import warnings
        warnings.warn(
            "failure() is deprecated, use exception classes instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        request_id = get_request_id()
        result = {'code': HttpStatusConstant.WARN, 'msg': msg}

        _apply_payload(result, data, rows, dict_content, model_content)

        result.update({'success': False, 'time': datetime.now(), 'requestId': request_id})

        response_headers = {"X-Request-Id": request_id}
        if headers:
            response_headers.update(headers)

        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(result),
            headers=response_headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def unauthorized(
        cls,
        msg: str = '登录信息已过期，访问系统资源失败',
        data: Optional[Any] = None,
        rows: Optional[Any] = None,
        dict_content: Optional[Dict] = None,
        model_content: Optional[BaseModel] = None,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ) -> Response:
        """
        未认证响应方法（已废弃，建议抛出 AuthException）

        @deprecated: 请使用 AuthException
        """
        import warnings
        warnings.warn(
            "unauthorized() is deprecated, use AuthException instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        request_id = get_request_id()
        result = {'code': HttpStatusConstant.UNAUTHORIZED, 'msg': msg}

        _apply_payload(result, data, rows, dict_content, model_content)

        result.update({'success': False, 'time': datetime.now(), 'requestId': request_id})

        response_headers = {"X-Request-Id": request_id}
        if headers:
            response_headers.update(headers)

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=jsonable_encoder(result),
            headers=response_headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def forbidden(
        cls,
        msg: str = '该用户无此接口权限',
        data: Optional[Any] = None,
        rows: Optional[Any] = None,
        dict_content: Optional[Dict] = None,
        model_content: Optional[BaseModel] = None,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ) -> Response:
        """
        未授权响应方法（已废弃，建议抛出 PermissionException）

        @deprecated: 请使用 PermissionException
        """
        import warnings
        warnings.warn(
            "forbidden() is deprecated, use PermissionException instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        request_id = get_request_id()
        result = {'code': HttpStatusConstant.FORBIDDEN, 'msg': msg}

        _apply_payload(result, data, rows, dict_content, model_content)

        result.update({'success': False, 'time': datetime.now(), 'requestId': request_id})

        response_headers = {"X-Request-Id": request_id}
        if headers:
            response_headers.update(headers)

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(result),
            headers=response_headers,
            media_type=media_type,
            background=background,
        )

    @classmethod
    def error(
        cls,
        msg: str = '接口异常',
        code: Optional[int] = None,
        data: Optional[Any] = None,
        rows: Optional[Any] = None,
        dict_content: Optional[Dict] = None,
        model_content: Optional[BaseModel] = None,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ) -> Response:
        """
        错误响应方法（已废弃，建议抛出 SystemException）

        @deprecated: 请使用 SystemException
        """
        import warnings
        warnings.warn(
            "error() is deprecated, use SystemException instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        request_id = get_request_id()
        result = {'code': code if code is not None else HttpStatusConstant.ERROR, 'msg': msg}

        _apply_payload(result, data, rows, dict_content, model_content)

        result.update({'success': False, 'time': datetime.now(), 'requestId': request_id})

        response_headers = {"X-Request-Id": request_id}
        if headers:
            response_headers.update(headers)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(result),
            headers=response_headers,
            media_type=media_type,
            background=background,
        )

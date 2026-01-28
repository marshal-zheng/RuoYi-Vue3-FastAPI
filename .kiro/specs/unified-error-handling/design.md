# 统一错误处理系统 - 设计文档（标准化版）

## 1. 架构设计

### 1.1 整体架构
```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  @zxio/http Interceptor (http.ts)                      │ │
│  │  ├─ Request: Token, Anti-Replay, Params Transform     │ │
│  │  ├─ Response: HTTP 2xx Success Parser                 │ │
│  │  └─ Error Handler: RFC 7807 Parser + Unified Display  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ▼ HTTP Request
┌─────────────────────────────────────────────────────────────┐
│                        Backend Layer                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Middleware: TraceId Generation                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Controller: No try-catch, throw exceptions only       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Service: Business logic + throw typed exceptions      │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Global Exception Handler (exceptions/handle.py)       │ │
│  │  ├─ Map exception → HTTP status + errorCode           │ │
│  │  ├─ Format RFC 7807 response                          │ │
│  │  └─ Add X-Request-Id header                           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则
1. **HTTP 语义化**: 使用真实 HTTP 状态码表达请求结果
2. **RFC 7807 标准**: 所有错误响应遵循 Problem Details 格式
3. **单一职责**: Controller 不处理异常，Service 抛出业务异常，全局处理器统一响应
4. **业务错误码补充**: errorCode 用于业务语义，不替代 HTTP 状态码
5. **可观测性**: 每个响应携带 requestId，日志可追踪

---

## 2. 后端详细设计

### 2.1 错误码体系设计

#### 2.1.1 错误码结构
```python
# config/error_codes.py
from enum import IntEnum
from typing import Dict

class ErrorCode(IntEnum):
    """统一错误码枚举"""
    # 系统级错误 (1xxxx)
    VALIDATION_ERROR = 10001      # 参数校验失败
    REQUIRED_FIELD = 10002         # 必填字段缺失
    INVALID_FORMAT = 10003         # 格式不正确
    
    # 认证授权错误 (2xxxx)
    UNAUTHORIZED = 20001           # 未认证
    TOKEN_EXPIRED = 20002          # Token过期
    TOKEN_INVALID = 20003          # Token无效
    FORBIDDEN = 20004              # 无权限
    
    # 业务错误 - 用户模块 (3xxxx)
    USER_NOT_FOUND = 30001         # 用户不存在
    USER_ALREADY_EXISTS = 30002    # 用户已存在
    USER_DISABLED = 30003          # 用户已禁用
    PASSWORD_INCORRECT = 30004     # 密码错误
    
    # 业务错误 - 角色模块 (4xxxx)
    ROLE_NOT_FOUND = 40001         # 角色不存在
    ROLE_ALREADY_EXISTS = 40002    # 角色已存在
    
    # 系统错误 (5xxxx)
    SYSTEM_ERROR = 50000           # 系统未知错误
    DATABASE_ERROR = 50001         # 数据库异常
    EXTERNAL_SERVICE_ERROR = 50002 # 外部服务异常
    FILE_UPLOAD_ERROR = 50003      # 文件上传失败

class ErrorType(str, Enum):
    """错误类型"""
    VALIDATION = "VALIDATION"      # 校验错误
    AUTHENTICATION = "AUTHENTICATION"  # 认证错误
    AUTHORIZATION = "AUTHORIZATION"    # 授权错误
    BUSINESS = "BUSINESS"          # 业务错误
    SYSTEM = "SYSTEM"              # 系统错误

class ErrorCodeInfo:
    """错误码信息（双层消息设计）"""
    def __init__(
        self,
        code: int,
        user_message_zh: str,        # 用户消息（中文）- 简洁友好
        user_message_en: str,        # 用户消息（英文）- 简洁友好
        developer_message: str,      # 开发者消息 - 详细技术信息
        http_status: int,
        error_type: ErrorType,
        error_code_name: str
    ):
        self.code = code
        self.user_message_zh = user_message_zh
        self.user_message_en = user_message_en
        self.developer_message = developer_message
        self.http_status = http_status
        self.error_type = error_type
        self.error_code_name = error_code_name

# 错误码映射表（双层消息示例）
ERROR_CODE_MAP: Dict[int, ErrorCodeInfo] = {
    # 业务错误：用户消息 = 开发者消息（业务语义清晰）
    ErrorCode.VALIDATION_ERROR: ErrorCodeInfo(
        code=10001,
        user_message_zh="参数校验失败",
        user_message_en="Validation failed",
        developer_message="Request parameter validation failed",
        http_status=422,
        error_type=ErrorType.VALIDATION,
        error_code_name="VALIDATION_ERROR"
    ),
    ErrorCode.USER_ALREADY_EXISTS: ErrorCodeInfo(
        code=30002,
        user_message_zh="该用户名已被使用，请换一个试试",
        user_message_en="Username already exists, please try another one",
        developer_message="User with username '{username}' already exists in database",
        http_status=409,
        error_type=ErrorType.BUSINESS,
        error_code_name="USER_ALREADY_EXISTS"
    ),
    
    # 系统错误：用户消息通用化，开发者消息详细化
    ErrorCode.DATABASE_ERROR: ErrorCodeInfo(
        code=50001,
        user_message_zh="系统繁忙，请稍后重试",
        user_message_en="System is busy, please try again later",
        developer_message="Database operation failed: {error_detail}",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="DATABASE_ERROR"
    ),
    ErrorCode.SYSTEM_ERROR: ErrorCodeInfo(
        code=50000,
        user_message_zh="系统繁忙，请稍后重试",
        user_message_en="System is busy, please try again later",
        developer_message="Internal server error: {error_detail}",
        http_status=500,
        error_type=ErrorType.SYSTEM,
        error_code_name="SYSTEM_ERROR"
    ),
    # ... 其他错误码映射
}
```

#### 2.1.2 双层消息设计
```python
# config/error_messages.py（双层消息）
from typing import Dict

# 用户消息：简洁、友好、可操作
USER_MESSAGES_ZH: Dict[int, str] = {
    # 业务错误：直接描述业务问题
    10001: "参数校验失败",
    10002: "必填字段缺失",
    10003: "格式不正确",
    20001: "未认证，请先登录",
    20002: "登录已过期，请重新登录",
    30001: "用户不存在",
    30002: "该用户名已被使用，请换一个试试",
    
    # 系统错误：通用化，不暴露技术细节
    50000: "系统繁忙，请稍后重试",
    50001: "系统繁忙，请稍后重试",  # 数据库错误
    50002: "系统繁忙，请稍后重试",  # 外部服务错误
    50003: "文件上传失败，请重试",
}

USER_MESSAGES_EN: Dict[int, str] = {
    10001: "Validation failed",
    10002: "Required field missing",
    10003: "Invalid format",
    20001: "Unauthorized, please login",
    20002: "Session expired, please login again",
    30001: "User not found",
    30002: "Username already exists, please try another one",
    50000: "System is busy, please try again later",
    50001: "System is busy, please try again later",
    50002: "System is busy, please try again later",
    50003: "File upload failed, please try again",
}

# 开发者消息：详细技术信息（仅用于日志和开发环境）
DEVELOPER_MESSAGES: Dict[int, str] = {
    # 业务错误：与用户消息相同或略详细
    10001: "Request parameter validation failed",
    10002: "Required field missing: {field}",
    10003: "Invalid format for field: {field}",
    20001: "Authentication token missing or invalid",
    20002: "Authentication token expired at {expired_at}",
    30001: "User with id={user_id} not found in database",
    30002: "User with username='{username}' already exists in database",
    
    # 系统错误：详细技术原因
    50000: "Internal server error: {error_detail}",
    50001: "Database operation failed: {error_detail}",
    50002: "External service call failed: service={service_name}, error={error_detail}",
    50003: "File upload failed: {error_detail}",
}

def get_user_message(code: int, lang: str = "zh", **kwargs) -> str:
    """获取用户消息（前端展示）"""
    messages = USER_MESSAGES_ZH if lang == "zh" else USER_MESSAGES_EN
    template = messages.get(code, messages.get(50000))
    return template.format(**kwargs) if kwargs else template

def get_developer_message(code: int, **kwargs) -> str:
    """获取开发者消息（日志记录和开发环境）"""
    template = DEVELOPER_MESSAGES.get(code, DEVELOPER_MESSAGES.get(50000))
    return template.format(**kwargs) if kwargs else template
```

**消息分类规则**：
1. **业务错误**（10xxx-40xxx）：
   - 用户消息：直接描述业务问题，用户可理解
   - 开发者消息：与用户消息相同或略详细，包含参数名称
   
2. **系统错误**（50xxx）：
   - 用户消息：通用化表述（"系统繁忙，请稍后重试"），不暴露技术细节
   - 开发者消息：详细技术原因（数据库错误、连接池耗尽、SQL错误等）

3. **永远不向用户暴露**：
   - 数据库错误详情（如"Connection pool exhausted"）
   - SQL 语句或查询错误
   - 堆栈跟踪信息
   - 内部文件路径
   - 服务器配置信息
   - 第三方服务的详细错误

### 2.3 环境配置设计

```python
# config/env.py（新增配置）
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 错误处理配置
    INCLUDE_DEVELOPER_MESSAGE: bool = False  # 是否在响应中包含开发者消息
    ERROR_LOG_LEVEL: str = "ERROR"           # 错误日志级别
    
    class Config:
        env_file = ".env"

# 使用示例
settings = Settings()

# 开发环境 .env.dev
# INCLUDE_DEVELOPER_MESSAGE=true

# 生产环境 .env.prod
# INCLUDE_DEVELOPER_MESSAGE=false
```

**环境区分策略**：
- **开发环境**：`INCLUDE_DEVELOPER_MESSAGE=true`
  - 响应包含 `developerMessage` 字段
  - 帮助开发者快速定位问题
  
- **生产环境**：`INCLUDE_DEVELOPER_MESSAGE=false`
  - 响应不包含 `developerMessage` 字段
  - 保护系统安全，不暴露技术细节
  
- **所有环境**：
  - 日志始终记录完整的 `developerMessage`
  - 用于问题排查和审计

### 2.4 异常体系设计

#### 2.4.1 异常类层级（支持双层消息）
```python
# exceptions/exception.py (升级版 - 支持双层消息)
from typing import Optional, Dict, Any
from config.error_codes import ErrorCode, ErrorType

class AppException(Exception):
    """应用异常基类（支持双层消息）"""
    def __init__(
        self,
        user_message: str,           # 用户消息（前端展示）
        developer_message: str,      # 开发者消息（日志记录）
        error_code: int,
        http_status: int,
        error_type: ErrorType,
        data: Optional[Any] = None,
        error_code_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(user_message)
        self.user_message = user_message
        self.developer_message = developer_message
        self.error_code = error_code
        self.http_status = http_status
        self.error_type = error_type
        self.data = data
        self.error_code_name = error_code_name
        self.extra = kwargs  # 额外字段（如 field, value）

class ValidationException(AppException):
    """校验异常"""
    def __init__(self, user_message: str, developer_message: Optional[str] = None, field: Optional[str] = None, **kwargs):
        super().__init__(
            user_message=user_message,
            developer_message=developer_message or f"Validation failed for field: {field}",
            error_code=ErrorCode.VALIDATION_ERROR,
            http_status=422,
            error_type=ErrorType.VALIDATION,
            error_code_name="VALIDATION_ERROR",
            field=field,
            **kwargs
        )

class BusinessException(AppException):
    """业务异常（用户消息 = 开发者消息）"""
    def __init__(self, message: str, error_code: int, http_status: int = 400, **kwargs):
        super().__init__(
            user_message=message,
            developer_message=kwargs.pop('developer_message', message),  # 默认相同
            error_code=error_code,
            http_status=http_status,
            error_type=ErrorType.BUSINESS,
            **kwargs
        )

class SystemException(AppException):
    """系统异常（用户消息通用化，开发者消息详细化）"""
    def __init__(
        self, 
        user_message: str = "系统繁忙，请稍后重试",
        developer_message: str = "Internal server error",
        error_code: int = ErrorCode.SYSTEM_ERROR,
        **kwargs
    ):
        super().__init__(
            user_message=user_message,
            developer_message=developer_message,
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

# 保持 ServiceException 兼容（标记为废弃）
class ServiceException(AppException):
    """服务异常（兼容旧代码，建议使用具体异常类型）"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            user_message=message,
            developer_message=kwargs.pop('developer_message', message),
            error_code=kwargs.get('error_code', ErrorCode.SYSTEM_ERROR),
            http_status=kwargs.get('http_status', 500),
            error_type=ErrorType.SYSTEM,
            **kwargs
        )
```

**使用示例**：
```python
# 业务异常：用户消息清晰
raise BusinessException(
    message="该用户名已被使用，请换一个试试",
    error_code=ErrorCode.USER_ALREADY_EXISTS,
    http_status=409,
    username="admin"
)

# 系统异常：用户消息通用化，开发者消息详细化
raise DatabaseException(
    error_detail="Connection pool exhausted: max_connections=100, active=100, idle=0"
)
# 用户看到："系统繁忙，请稍后重试"
# 日志记录："Database operation failed: Connection pool exhausted: max_connections=100, active=100, idle=0"
```

### 2.5 RequestId 中间件设计

```python
# middlewares/trace_middleware/trace_id_middleware.py (升级)
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

# 全局 ContextVar 存储 requestId
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 生成或获取 requestId
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4().hex)
        request_id_var.set(request_id)
        
        # 存储到 request.state
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # 添加响应头
        response.headers["X-Request-Id"] = request_id
        
        return response

def get_request_id() -> str:
    """获取当前请求的 requestId"""
    return request_id_var.get()
```

### 2.6 全局异常处理器设计（RFC 7807 + 双层消息）

```python
# exceptions/handle.py (标准化版 + 双层消息)
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from pydantic import ValidationError
from exceptions.exception import *
from utils.response_util import ResponseUtil
from utils.log_util import logger
from middlewares.trace_middleware.trace_id_middleware import get_request_id
from config.error_codes import ERROR_CODE_MAP, ErrorCode
from config.env import settings

def handle_exception(app: FastAPI):
    """全局异常处理（RFC 7807 标准 + 双层消息）"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        request_id = get_request_id()
        
        # 记录日志（包含开发者消息）
        logger.error(
            f"[{request_id}] {exc.error_type}: "
            f"user_message={exc.user_message}, "
            f"developer_message={exc.developer_message}"
        )
        
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
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        request_id = get_request_id()
        
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "code": error["type"].upper()
            })
        
        developer_message = f"Validation failed: {errors}"
        logger.warning(f"[{request_id}] {developer_message}")
        
        return ResponseUtil.validation_problem(
            request=request,
            errors=errors,
            developer_message=developer_message
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = get_request_id()
        developer_message = f"HTTP {exc.status_code}: {exc.detail}"
        logger.error(f"[{request_id}] {developer_message}")
        
        return ResponseUtil.problem_details(
            request=request,
            error_code=exc.status_code,
            user_message=exc.detail,
            developer_message=developer_message,
            http_status=exc.status_code,
            error_type=ErrorType.SYSTEM
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        request_id = get_request_id()
        
        # 用户消息：通用化
        user_message = "系统繁忙，请稍后重试"
        
        # 开发者消息：详细错误信息
        developer_message = f"Unhandled exception: {type(exc).__name__}: {str(exc)}"
        
        # 记录完整堆栈跟踪
        logger.exception(f"[{request_id}] {developer_message}")
        
        return ResponseUtil.problem_details(
            request=request,
            error_code=ErrorCode.SYSTEM_ERROR,
            user_message=user_message,
            developer_message=developer_message,
            http_status=500,
            error_type=ErrorType.SYSTEM
        )
```

**关键设计点**：
1. **日志记录**：所有异常都记录完整的 `developer_message`，包含技术细节
2. **响应内容**：根据环境配置决定是否包含 `developerMessage` 字段
3. **系统异常**：未捕获的异常统一返回通用用户消息，不暴露技术细节
4. **请求追踪**：所有日志包含 `requestId`，便于问题排查

### 2.7 ResponseUtil 升级设计（双层消息）

```python
# utils/response_util.py (标准化版 + 双层消息)
from datetime import datetime
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from typing import Optional, Any, Dict, List
from middlewares.trace_middleware.trace_id_middleware import get_request_id
from config.env import settings

class ResponseUtil:
    """响应工具类（RFC 7807 标准 + 双层消息）"""
    
    @classmethod
    def success(
        cls,
        data: Optional[Any] = None,
        message: str = "操作成功",
        http_status: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None
    ) -> Response:
        """成功响应（HTTP 2xx）"""
        request_id = get_request_id()
        
        result = {
            "data": data,
            "message": message,
            "requestId": request_id
        }
        
        response_headers = {"X-Request-Id": request_id}
        if headers:
            response_headers.update(headers)
        
        return JSONResponse(
            status_code=http_status,
            content=jsonable_encoder(result),
            headers=response_headers
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
        """RFC 7807 错误响应（双层消息）"""
        request_id = get_request_id()
        
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
        if settings.INCLUDE_DEVELOPER_MESSAGE:
            result["developerMessage"] = developer_message
        
        # 添加额外字段
        if kwargs:
            result.update(kwargs)
        
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
        """RFC 7807 校验错误响应（双层消息）"""
        request_id = get_request_id()
        
        result = {
            "type": "https://api.example.com/problems/validation-error",
            "title": "参数验证失败",
            "status": 422,
            "detail": "请检查输入的信息是否正确",
            "instance": str(request.url.path),
            "errorCode": 10001,
            "requestId": request_id,
            "errors": errors
        }
        
        # 开发环境：包含开发者消息
        if settings.INCLUDE_DEVELOPER_MESSAGE and developer_message:
            result["developerMessage"] = developer_message
        
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(result),
            headers={
                "X-Request-Id": request_id,
                "Content-Type": "application/problem+json"
            }
        )
    
    # 保留旧方法用于兼容（标记为废弃）
    @classmethod
    def failure(cls, msg: str = "操作失败", **kwargs):
        """废弃：请使用 problem_details"""
        import warnings
        warnings.warn("failure() is deprecated, use problem_details()", DeprecationWarning)
        return cls.problem_details(
            request=kwargs.get('request'),
            error_code=kwargs.get('code', 50000),
            user_message=msg,
            developer_message=msg,
            http_status=kwargs.get('status_code', 400),
            error_type="SYSTEM"
        )
```

**关键设计点**：
1. **环境区分**：通过 `settings.INCLUDE_DEVELOPER_MESSAGE` 控制是否返回 `developerMessage`
2. **双层消息**：`user_message` 用于前端展示，`developer_message` 用于开发调试
3. **安全性**：生产环境不返回技术细节，保护系统安全

---

## 3. 前端详细设计

### 3.1 响应解析器升级（HTTP 语义化）

```typescript
// utils/http.ts (升级 successResolver)
const successResolver: SuccessResolver = ({ response }) => {
  const payload = (response.data || {}) as Record<string, unknown>;
  
  // 基于 HTTP 状态码判定成功
  const status = response.status;
  const ok = status >= 200 && status < 300;
  
  // 成功响应
  if (ok) {
    return {
      ok: true,
      data: payload.data || payload,
      message: (payload.message as string) || '操作成功',
      code: status,
      raw: payload,
    };
  }
  
  // 错误响应（RFC 7807）
  return {
    ok: false,
    data: payload,
    message: (payload.detail as string) || (payload.title as string) || '操作失败',
    code: (payload.errorCode as number) || status,
    raw: payload,
  };
};
```

### 3.2 错误处理器升级（RFC 7807）

```typescript
// utils/http.ts (升级 afterResponseTransform)
const afterResponseTransform: HttpTransformHook = {
  async afterResponse(response, options, context) {
    const silentError = ((response.config as Record<string, unknown>)?.silentError as boolean) === true;
    
    // 二进制数据直接返回
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return response;
    }
    
    // 2xx 成功响应
    if (response.status >= 200 && response.status < 300) {
      return response;
    }
    
    // 4xx/5xx 错误响应
    const payload = response.data as Record<string, unknown>;
    const errorCode = (payload.errorCode as number) || response.status;
    const message = (payload.detail as string) || (payload.title as string) || '操作失败';
    
    // 401 未授权
    if (response.status === 401 || errorCode === 20001 || errorCode === 20002) {
      if (!isRelogin.show) {
        isRelogin.show = true;
        ElMessageBox.confirm('登录状态已过期，您可以继续留在该页面，或者重新登录', '系统提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning',
        })
          .then(() => {
            isRelogin.show = false;
            useUserStore().logOut().then(() => {
              location.href = '/index';
            });
          })
          .catch(() => {
            isRelogin.show = false;
          });
      }
      return Promise.reject('无效的会话，或者会话已过期，请重新登录。');
    }
    
    // 403 权限不足
    if (response.status === 403 || errorCode === 20004) {
      if (!silentError) {
        ElMessage({ message: message || '权限不足', type: 'error' });
      }
      return Promise.reject(new Error(message || '权限不足'));
    }
    
    // 422 校验错误
    if (response.status === 422 || errorCode === 10001) {
      if (!silentError) {
        const errors = (payload.errors as Array<{ field: string; message: string }>) || [];
        
        if (errors.length > 0) {
          // 展示字段级错误
          const errorMsg = errors.map(e => `${e.field}: ${e.message}`).join('\n');
          ElNotification.error({
            title: '参数验证失败',
            message: errorMsg,
            duration: 5000
          });
        } else {
          ElMessage({ message: message || '参数验证失败', type: 'error' });
        }
      }
      return Promise.reject(new Error(message || '参数验证失败'));
    }
    
    // 500+ 系统错误
    if (response.status >= 500) {
      if (!silentError) {
        ElMessage({ message: message || '系统错误', type: 'error' });
      }
      return Promise.reject(new Error(message || '系统错误'));
    }
    
    // 其他 4xx 错误
    if (response.status >= 400) {
      if (!silentError) {
        ElNotification.error({ title: message || '操作失败' });
      }
      return Promise.reject(new Error(message || '操作失败'));
    }
    
    return response;
  },
  
  async onError(error, options, context) {
    const axiosError = error as { 
      config?: Record<string, unknown>; 
      message?: string;
      response?: { data?: Record<string, unknown> }
    };
    const silentError = (axiosError.config?.silentError as boolean) === true;
    
    // 优先从响应体获取错误信息（RFC 7807）
    let message = '';
    if (axiosError.response?.data) {
      const data = axiosError.response.data;
      message = (data.detail as string) || (data.title as string) || (data.message as string) || '';
    }
    
    if (!message) {
      message = axiosError.message || '';
      if (message === 'Network Error') {
        message = '后端接口连接异常';
      } else if (message.includes('timeout')) {
        message = '系统接口请求超时';
      } else if (message.includes('Request failed with status code')) {
        message = '系统接口' + message.substr(message.length - 3) + '异常';
      }
    }
    
    if (!silentError && message) {
      ElMessage({ message, type: 'error', duration: 5000 });
    }
    
    throw error;
  },
};
```

### 3.3 错误码映射扩展

```typescript
// utils/errorCode.ts (扩展)
export default {
  // HTTP 标准状态码
  '200': '操作成功',
  '201': '创建成功',
  '204': '删除成功',
  '400': '请求参数错误',
  '401': '认证失败，无法访问系统资源',
  '403': '当前操作没有权限',
  '404': '访问资源不存在',
  '409': '资源冲突',
  '422': '参数验证失败',
  '500': '系统内部错误',
  '502': '网关错误',
  '503': '服务不可用',
  
  // 业务错误码
  '10001': '参数校验失败',
  '10002': '必填字段缺失',
  '10003': '格式不正确',
  '20001': '未认证，请先登录',
  '20002': '登录已过期，请重新登录',
  '20003': 'Token无效',
  '20004': '权限不足',
  '30001': '用户不存在',
  '30002': '用户已存在',
  '30003': '用户已禁用',
  '30004': '密码错误',
  '40001': '角色不存在',
  '40002': '角色已存在',
  '50000': '系统未知错误',
  '50001': '数据库异常',
  '50002': '外部服务异常',
  '50003': '文件上传失败',
  
  'default': '系统未知错误'
};
```

---

## 4. 迁移策略（破坏性变更）

### 4.1 后端迁移步骤

#### Phase 1: 基础设施（1-2天）
1. 创建 `config/error_codes.py`
2. 创建 `config/error_messages.py`
3. 升级 `exceptions/exception.py`
4. 升级 `middlewares/trace_middleware`

#### Phase 2: 响应工具（1天）
1. 升级 `utils/response_util.py`
2. 添加 `problem_details()` 和 `validation_problem()`
3. 标记旧方法为废弃

#### Phase 3: 异常处理（1天）
1. 升级 `exceptions/handle.py`
2. 所有异常返回 RFC 7807
3. 设置真实 HTTP 状态码

#### Phase 4: 业务代码迁移（3-5天）
1. 移除 Controller 中的 try-catch
2. Service 层使用新异常类
3. 移除手动 `ResponseUtil.error()` 调用

### 4.2 前端迁移步骤

#### Phase 1: 拦截器升级（1天）
1. 升级 `utils/http.ts` 的 `successResolver`
2. 升级 `afterResponseTransform`
3. 升级 `onError`

#### Phase 2: 错误码映射（0.5天）
1. 扩展 `utils/errorCode.ts`

#### Phase 3: 业务代码清理（2-3天）
1. 移除业务代码中的手动错误处理
2. 依赖拦截器统一处理

### 4.3 测试与验证（2-3天）
1. 单元测试
2. 集成测试
3. 端到端测试
4. 回归测试

**总预计工期**: 10-15 天

---

## 5. 测试策略

### 5.1 后端单元测试
```python
# tests/unit/test_error_handling.py
import pytest
from exceptions.exception import ValidationException, BusinessException
from config.error_codes import ErrorCode

def test_validation_exception():
    exc = ValidationException("字段不能为空", field="username")
    assert exc.error_code == 10001
    assert exc.http_status == 422
    assert exc.error_type == "VALIDATION"
    assert exc.extra["field"] == "username"

def test_business_exception():
    exc = BusinessException(
        message="用户已存在",
        error_code=ErrorCode.USER_ALREADY_EXISTS,
        http_status=409
    )
    assert exc.error_code == 30002
    assert exc.http_status == 409
```

### 5.2 后端集成测试
```python
# tests/integration/test_error_responses.py
from fastapi.testclient import TestClient

def test_rfc7807_error_response(client: TestClient):
    response = client.post("/api/user", json={"username": ""})
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    
    data = response.json()
    assert data["status"] == 422
    assert data["errorCode"] == 10001
    assert "requestId" in data
    assert "errors" in data
    assert data["type"].startswith("https://")

def test_success_response(client: TestClient):
    response = client.get("/api/user/1")
    assert response.status_code == 200
    assert "X-Request-Id" in response.headers
    
    data = response.json()
    assert "data" in data
    assert "requestId" in data
```

### 5.3 前端单元测试
```typescript
// tests/unit/utils/http.test.ts
import { describe, it, expect } from 'vitest';

describe('HTTP Error Handling', () => {
  it('should handle RFC 7807 401 error', async () => {
    const mockResponse = {
      status: 401,
      data: {
        errorCode: 20001,
        detail: '未认证',
        title: 'Unauthorized',
        requestId: 'xxx'
      },
      headers: { 'content-type': 'application/problem+json' }
    };
    
    // Test error handling
    // ...
  });
  
  it('should handle RFC 7807 validation error', async () => {
    const mockResponse = {
      status: 422,
      data: {
        errorCode: 10001,
        detail: 'Validation failed',
        errors: [{ field: 'username', message: '不能为空' }],
        requestId: 'xxx'
      },
      headers: { 'content-type': 'application/problem+json' }
    };
    
    // Test error handling
    // ...
  });
});
```

---

## 6. 性能与安全

### 6.1 性能优化
- 错误码映射使用字典查找，O(1) 复杂度
- RequestId 使用 uuid.uuid4().hex，性能损耗 < 0.1ms
- 异常处理不阻塞响应

### 6.2 安全措施
- 响应中不返回堆栈信息
- 错误消息脱敏
- RequestId 用于审计追踪

---

## 7. 最佳实践

### 7.1 后端最佳实践
```python
# ✅ 推荐：Service 层抛出业务异常
class UserService:
    async def create_user(self, username: str):
        existing = await self.user_repo.find_by_username(username)
        if existing:
            raise ResourceConflictException(
                message=f"用户名 '{username}' 已存在",
                error_code=ErrorCode.USER_ALREADY_EXISTS,
                username=username
            )
        # ...

# ❌ 不推荐：Controller 层 try-catch
@router.post("/user")
async def create_user(data: UserCreateRequest):
    try:
        result = await user_service.create_user(data.username)
        return ResponseUtil.success(data=result)
    except Exception as e:
        return ResponseUtil.error(msg=str(e))  # 不要这样做
```

### 7.2 前端最佳实践
```typescript
// ✅ 推荐：依赖拦截器统一处理
async function createUser(userData: UserCreateRequest) {
  const result = await http.post({ url: '/api/user', data: userData });
  return result.data;
}

// ❌ 不推荐：手动错误处理
async function createUser(userData: UserCreateRequest) {
  try {
    const result = await http.post({ url: '/api/user', data: userData });
    ElMessage.success('创建成功');  // 不要这样做
    return result.data;
  } catch (error) {
    ElMessage.error('创建失败');  // 不要这样做
  }
}
```

---

**文档版本**: 2.0  
**创建日期**: 2026-01-28  
**最后更新**: 2026-01-28  
**负责人**: Kiro AI  
**状态**: 待审核

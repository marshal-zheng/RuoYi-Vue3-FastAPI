# Config Deletion RFC 7807 Compliance Fix

## Overview
Fixed the config deletion error handling to comply with RFC 7807 (Problem Details for HTTP APIs) standard. The issue was that errors were being caught by the `@Log` decorator and returned in the old format instead of the RFC 7807 format.

## Problem

When trying to delete a built-in config, the API was returning:
```json
{
  "code": 500,
  "msg": "内置参数【发发发】不能删除",
  "success": false,
  "time": "2026-01-30T19:37:32.710832",
  "requestId": "2a4e0c53f3a0401f9769585e02b68b40"
}
```

This is the old response format and does not comply with RFC 7807 standard.

## Root Cause

The `@Log` decorator in `module_admin/annotation/log_annotation.py` was catching all exceptions (including the new `AppException` and its subclasses) and returning responses using the deprecated `ResponseUtil.failure()` and `ResponseUtil.error()` methods, which use the old format.

## Changes Made

### 1. Error Code Additions (`config/error_codes.py`)
Added two new error codes for the config module:

```python
# Error Code Enum
CONFIG_NOT_FOUND = 43101              # 参数配置不存在
CONFIG_BUILTIN_CANNOT_DELETE = 43102  # 内置参数不能删除

# Error Code Mapping
ErrorCode.CONFIG_NOT_FOUND: ErrorCodeInfo(
    code=43101,
    title="参数配置不存在",
    detail="未找到该参数配置，请确认配置信息",
    http_status=404,
    error_type=ErrorType.BUSINESS,
    error_code_name="CONFIG_NOT_FOUND"
),
ErrorCode.CONFIG_BUILTIN_CANNOT_DELETE: ErrorCodeInfo(
    code=43102,
    title="内置参数不能删除",
    detail="系统内置参数不允许删除",
    http_status=409,
    error_type=ErrorType.BUSINESS,
    error_code_name="CONFIG_BUILTIN_CANNOT_DELETE"
)
```

### 2. Service Layer Updates (`module_admin/service/config_service.py`)

#### Import Changes
Added `BusinessException` to the imports:
```python
from exceptions.exception import (
    ResourceNotFoundException,
    ResourceConflictException,
    ValidationException,
    BusinessException
)
```

#### Delete Service Method Updates
Updated `delete_config_services` method to use proper RFC 7807 compliant exceptions:

```python
# Check if config exists
if not config_info.config_id:
    raise ResourceNotFoundException(
        user_message=f'参数配置不存在',
        error_code=ErrorCode.CONFIG_NOT_FOUND,
        developer_message=f'Config not found: config_id={config_id}'
    )

# Check if config is built-in
if config_info.config_type == CommonConstant.YES:
    raise BusinessException(
        message=f'内置参数【{config_info.config_key}】不能删除',
        error_code=ErrorCode.CONFIG_BUILTIN_CANNOT_DELETE,
        http_status=409,
        developer_message=f'Built-in config cannot be deleted: config_key={config_info.config_key}, config_id={config_id}'
    )
```

### 3. Log Annotation Fix (`module_admin/annotation/log_annotation.py`)

**Critical Fix**: Modified the `@Log` decorator to let `AppException` and its subclasses pass through to the global exception handler:

```python
# Import AppException
from exceptions.exception import LoginException, ServiceException, ServiceWarning, AppException

# In the exception handling block:
try:
    # 调用原始函数
    result = await func(*args, **kwargs)
except AppException:
    # 新异常体系：直接向上抛出，由全局异常处理器处理（RFC 7807）
    raise
except (LoginException, ServiceWarning) as e:
    # ... old exception handling for backward compatibility
```

This ensures that new exception types are handled by the global exception handler in `exceptions/handle.py`, which returns RFC 7807 compliant responses.

### 4. Test Updates (`tests/unit/services/test_config_service.py`)
Updated test to expect `BusinessException` instead of `ValidationException`:

```python
from exceptions.exception import (
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException,
    BusinessException  # Added
)

@pytest.mark.asyncio
async def test_delete_builtin_config_forbidden(self, mock_request, mock_db):
    """Test that built-in config cannot be deleted."""
    # ...
    with pytest.raises(BusinessException, match='内置参数.*不能删除'):
        await ConfigService.delete_config_services(mock_request, mock_db, delete_obj)
```

## RFC 7807 Compliance

Now the error responses follow RFC 7807 format:

```json
{
  "type": "https://api.example.com/problems/CONFIG_BUILTIN_CANNOT_DELETE",
  "title": "内置参数【sys.builtin】不能删除",
  "status": 409,
  "detail": "内置参数【sys.builtin】不能删除",
  "instance": "/system/config/1",
  "errorCode": 43102,
  "errorCodeName": "CONFIG_BUILTIN_CANNOT_DELETE",
  "developerMessage": "Built-in config cannot be deleted: config_key=sys.builtin, config_id=1",
  "requestId": "abc123",
  "timestamp": "2026-01-30T19:36:27.110Z"
}
```

## Benefits

1. **Standardized Error Format**: All errors follow RFC 7807 standard
2. **Proper HTTP Status Codes**: Uses 409 Conflict for business rule violations (not 500)
3. **Dual-Layer Messages**: 
   - User message: Friendly, localized message for frontend display
   - Developer message: Technical details for logging and debugging
4. **Better Error Tracking**: Includes requestId for tracing errors across logs
5. **Type Safety**: Uses proper exception types for different error scenarios
6. **Consistent Error Handling**: All new exceptions are handled uniformly by the global handler

## Testing

All tests pass successfully:
```bash
pytest ruoyi-fastapi-backend/tests/unit/services/test_config_service.py::TestConfigServiceDelete -v
# 3 passed in 3.32s
```

## Frontend Compatibility

The frontend error handling in `ConfigList.vue` will now receive properly formatted RFC 7807 error responses with the correct HTTP status code (409 instead of 500), which are automatically handled by the global error interceptor in `utils/http.ts`.

## Migration Notes

**Important**: The `@Log` decorator now allows `AppException` and its subclasses to pass through. This means:

1. All new code should use the new exception classes (`BusinessException`, `ValidationException`, `ResourceNotFoundException`, etc.)
2. Old exception classes (`ServiceException`, `LoginException`, `ServiceWarning`) are still caught by the `@Log` decorator for backward compatibility
3. Gradually migrate old exception usage to new exception classes for consistent RFC 7807 responses

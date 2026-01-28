# 双层消息设计指南 (Dual-Layer Message Design Guide)

## 1. 设计理念

### 1.1 为什么需要双层消息？

在企业级应用中，错误消息需要服务于两类不同的受众：

1. **最终用户（End Users）**
   - 需要简洁、友好、可操作的提示
   - 不应看到技术细节（数据库错误、SQL、堆栈跟踪等）
   - 关注"发生了什么"和"如何解决"

2. **开发者/运维人员（Developers/Operators）**
   - 需要详细的技术信息用于问题排查
   - 需要了解错误的根本原因
   - 关注"为什么发生"和"如何修复"

**双层消息设计**通过分离这两类消息，在保证用户体验的同时，提供充分的技术信息用于问题诊断。

### 1.2 国际标准参考

主流云服务商和 API 提供商的实践：

#### Stripe API
```json
{
  "error": {
    "message": "Your card was declined.",
    "type": "card_error",
    "code": "card_declined",
    "decline_code": "generic_decline"
  }
}
```
- `message`: 用户友好的错误描述
- `type`, `code`, `decline_code`: 开发者用于诊断的技术信息

#### Google Cloud API
```json
{
  "error": {
    "code": 403,
    "message": "The caller does not have permission",
    "status": "PERMISSION_DENIED",
    "details": [...]
  }
}
```
- `message`: 简洁的用户消息
- `status`, `details`: 开发者用于调试的详细信息

#### Azure REST API
```json
{
  "error": {
    "code": "ResourceNotFound",
    "message": "The Resource 'Microsoft.Compute/virtualMachines/vm1' under resource group 'rg1' was not found.",
    "details": [...]
  }
}
```

**共同特点**：
- 用户消息简洁明了
- 技术细节通过额外字段提供
- 生产环境可选择性暴露技术信息

---

## 2. 双层消息架构

### 2.1 消息层级定义

```
┌─────────────────────────────────────────────────────────┐
│                    错误响应体                            │
├─────────────────────────────────────────────────────────┤
│  User Message (用户消息)                                 │
│  ├─ title: 简短错误标题                                  │
│  └─ detail: 详细描述 + 可操作建议                        │
│                                                          │
│  Developer Message (开发者消息) [可选]                   │
│  └─ developerMessage: 技术细节 + 根本原因                │
│                                                          │
│  Metadata (元数据)                                       │
│  ├─ errorCode: 业务错误码                                │
│  ├─ requestId: 请求追踪ID                                │
│  └─ type: 错误类型URI                                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 RFC 7807 映射

```json
{
  "type": "https://api.example.com/problems/user-already-exists",
  "title": "用户已存在",                    // User Message (简短)
  "status": 409,
  "detail": "该用户名已被使用，请换一个试试",  // User Message (详细)
  "instance": "/api/system/user",
  "errorCode": 30002,
  "requestId": "c0d9c1f2b30f4c0faef6d62b6f6d4d71",
  "developerMessage": "User with username='admin' already exists in database, user_id=123"  // Developer Message
}
```

**字段说明**：
- `title` + `detail`: 用户消息（前端展示）
- `developerMessage`: 开发者消息（仅开发环境返回，生产环境仅记录日志）

---

## 3. 消息分类规则

### 3.1 业务错误（10xxx-40xxx）

**特点**：错误原因清晰，用户可理解

#### 规则
- **用户消息**：直接描述业务问题，用户可理解
- **开发者消息**：与用户消息相同或略详细，包含参数名称/值

#### 示例

**用户名已存在（30002）**
```python
# 用户消息
user_message = "该用户名已被使用，请换一个试试"

# 开发者消息
developer_message = "User with username='admin' already exists in database, user_id=123"
```

**参数校验失败（10001）**
```python
# 用户消息
user_message = "用户名不能为空"

# 开发者消息
developer_message = "Validation failed for field: username, value=None, constraint=required"
```

**角色正在使用中（40003）**
```python
# 用户消息
user_message = "该角色正在使用中，无法删除"

# 开发者消息
developer_message = "Role with id=5 is assigned to 12 users, cannot delete"
```

### 3.2 系统错误（50xxx）

**特点**：技术性错误，用户无法理解技术细节

#### 规则
- **用户消息**：通用化表述（"系统繁忙，请稍后重试"），不暴露技术细节
- **开发者消息**：详细技术原因（数据库错误、连接池耗尽、SQL错误等）

#### 示例

**数据库错误（50001）**
```python
# 用户消息（通用化）
user_message = "系统繁忙，请稍后重试"

# 开发者消息（详细化）
developer_message = "Database operation failed: Connection pool exhausted, max_connections=100, active=100, idle=0, waiting=5"
```

**外部服务错误（50002）**
```python
# 用户消息（通用化）
user_message = "系统繁忙，请稍后重试"

# 开发者消息（详细化）
developer_message = "External service call failed: service=payment-gateway, endpoint=https://api.payment.com/charge, status=503, error=Service Unavailable, retry_after=60s"
```

**缓存错误（50005）**
```python
# 用户消息（通用化）
user_message = "系统繁忙，请稍后重试"

# 开发者消息（详细化）
developer_message = "Cache operation failed: Redis connection timeout after 5000ms, host=redis.example.com:6379, error=ETIMEDOUT"
```

---

## 4. 安全规范

### 4.1 永远不向用户暴露的内容

❌ **禁止在用户消息中包含**：

1. **数据库错误详情**
   - ❌ "Connection pool exhausted"
   - ❌ "Deadlock detected"
   - ❌ "Foreign key constraint violation"
   - ✅ "系统繁忙，请稍后重试"

2. **SQL 语句或查询错误**
   - ❌ "Syntax error near 'SELECT * FROM users WHERE id=1'"
   - ❌ "Table 'users' doesn't exist"
   - ✅ "系统繁忙，请稍后重试"

3. **堆栈跟踪信息**
   - ❌ "File '/app/service/user_service.py', line 123, in create_user"
   - ❌ "Traceback (most recent call last)..."
   - ✅ "系统繁忙，请稍后重试"

4. **内部文件路径**
   - ❌ "/var/www/app/config/database.py"
   - ❌ "C:\Program Files\App\config.ini"
   - ✅ "系统繁忙，请稍后重试"

5. **服务器配置信息**
   - ❌ "Redis host: 192.168.1.100:6379"
   - ❌ "Database: mysql://root:password@localhost:3306/db"
   - ✅ "系统繁忙，请稍后重试"

6. **第三方服务的详细错误**
   - ❌ "Payment gateway returned: Invalid API key"
   - ❌ "AWS S3 error: Access Denied for bucket 'private-data'"
   - ✅ "系统繁忙，请稍后重试"

### 4.2 开发者消息的安全使用

✅ **开发者消息应该**：
- 仅在开发环境的响应中返回（`INCLUDE_DEVELOPER_MESSAGE=true`）
- 在生产环境中仅记录到服务端日志（`INCLUDE_DEVELOPER_MESSAGE=false`）
- 包含足够的技术细节用于问题排查
- 包含 requestId 用于日志关联

---

## 5. 环境配置策略

### 5.1 开发环境（Development）

**配置**：`.env.dev`
```bash
INCLUDE_DEVELOPER_MESSAGE=true
ERROR_LOG_LEVEL=DEBUG
```

**响应示例**：
```json
{
  "type": "https://api.example.com/problems/database-error",
  "title": "系统繁忙，请稍后重试",
  "status": 500,
  "detail": "系统繁忙，请稍后重试",
  "errorCode": 50001,
  "requestId": "abc123",
  "developerMessage": "Database operation failed: Connection pool exhausted, max_connections=100, active=100, idle=0"
}
```

**优点**：
- 开发者可以快速定位问题
- 无需查看服务端日志即可调试
- 加速开发和测试流程

### 5.2 生产环境（Production）

**配置**：`.env.prod`
```bash
INCLUDE_DEVELOPER_MESSAGE=false
ERROR_LOG_LEVEL=ERROR
```

**响应示例**：
```json
{
  "type": "https://api.example.com/problems/database-error",
  "title": "系统繁忙，请稍后重试",
  "status": 500,
  "detail": "系统繁忙，请稍后重试",
  "errorCode": 50001,
  "requestId": "abc123"
}
```

**服务端日志**：
```
[2026-01-28 10:30:45] ERROR [abc123] Database operation failed: Connection pool exhausted, max_connections=100, active=100, idle=0
```

**优点**：
- 保护系统安全，不暴露技术细节
- 用户体验友好
- 通过 requestId 可追踪到完整日志

---

## 6. 代码实现

### 6.1 后端异常类设计

```python
class AppException(Exception):
    """应用异常基类（支持双层消息）"""
    
    def __init__(
        self,
        user_message: str,           # 用户消息（前端展示）
        developer_message: str,      # 开发者消息（日志记录）
        error_code: int,
        http_status: int,
        error_type: str,
        **kwargs
    ):
        super().__init__(user_message)
        self.user_message = user_message
        self.developer_message = developer_message
        self.error_code = error_code
        self.http_status = http_status
        self.error_type = error_type
        self.extra = kwargs
```

### 6.2 业务异常示例

```python
# 业务错误：用户消息清晰
raise BusinessException(
    message="该用户名已被使用，请换一个试试",
    error_code=ErrorCode.USER_ALREADY_EXISTS,
    http_status=409,
    developer_message="User with username='admin' already exists in database, user_id=123",
    username="admin"
)
```

### 6.3 系统异常示例

```python
# 系统错误：用户消息通用化，开发者消息详细化
raise DatabaseException(
    error_detail="Connection pool exhausted: max_connections=100, active=100, idle=0, waiting=5"
)
# 用户看到："系统繁忙，请稍后重试"
# 日志记录："Database operation failed: Connection pool exhausted: max_connections=100, active=100, idle=0, waiting=5"
```

### 6.4 全局异常处理器

```python
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
        developer_message=exc.developer_message,  # 根据环境配置决定是否返回
        http_status=exc.http_status,
        error_type=exc.error_type,
        **exc.extra
    )
```

### 6.5 ResponseUtil 实现

```python
@classmethod
def problem_details(
    cls,
    request: Request,
    error_code: int,
    user_message: str,
    developer_message: str,
    http_status: int,
    error_type: str,
    **kwargs
) -> Response:
    """RFC 7807 错误响应（双层消息）"""
    request_id = get_request_id()
    
    result = {
        "type": f"https://api.example.com/problems/{error_code}",
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
    
    return JSONResponse(
        status_code=http_status,
        content=jsonable_encoder(result),
        headers={
            "X-Request-Id": request_id,
            "Content-Type": "application/problem+json"
        }
    )
```

---

## 7. 最佳实践

### 7.1 用户消息编写规范

✅ **好的用户消息**：
- "该用户名已被使用，请换一个试试"
- "密码长度必须在 8-20 位之间"
- "该角色正在使用中，无法删除"
- "文件大小不能超过 10MB"

❌ **不好的用户消息**：
- "Duplicate entry 'admin' for key 'username'"
- "Constraint violation: FK_user_role"
- "NullPointerException at line 123"
- "Redis connection timeout"

### 7.2 开发者消息编写规范

✅ **好的开发者消息**：
- "User with username='admin' already exists in database, user_id=123"
- "Database operation failed: Connection pool exhausted, max_connections=100, active=100, idle=0"
- "External service call failed: service=payment-gateway, status=503, retry_after=60s"
- "Validation failed for field: email, value='invalid', constraint=email_format"

❌ **不好的开发者消息**：
- "Error"
- "Failed"
- "Something went wrong"
- "Unknown error"

### 7.3 消息模板变量

支持在消息中使用变量占位符：

```python
# 错误码定义
ErrorCodeInfo(
    code=30002,
    user_message_zh="该用户名已被使用，请换一个试试",
    developer_message="User with username='{username}' already exists in database, user_id={user_id}"
)

# 使用时
raise BusinessException(
    message="该用户名已被使用，请换一个试试",
    error_code=ErrorCode.USER_ALREADY_EXISTS,
    developer_message=f"User with username='{username}' already exists in database, user_id={existing_user.id}",
    username=username,
    user_id=existing_user.id
)
```

---

## 8. 测试策略

### 8.1 单元测试

```python
def test_business_exception_dual_message():
    """测试业务异常的双层消息"""
    exc = BusinessException(
        message="用户已存在",
        error_code=ErrorCode.USER_ALREADY_EXISTS,
        http_status=409,
        developer_message="User with username='admin' already exists, user_id=123"
    )
    
    assert exc.user_message == "用户已存在"
    assert exc.developer_message == "User with username='admin' already exists, user_id=123"
    assert exc.error_code == 30002
    assert exc.http_status == 409

def test_system_exception_dual_message():
    """测试系统异常的双层消息"""
    exc = DatabaseException(
        error_detail="Connection pool exhausted"
    )
    
    # 用户消息通用化
    assert exc.user_message == "系统繁忙，请稍后重试"
    # 开发者消息详细化
    assert "Connection pool exhausted" in exc.developer_message
    assert exc.error_code == 50001
    assert exc.http_status == 500
```

### 8.2 集成测试

```python
def test_error_response_with_developer_message(client: TestClient, monkeypatch):
    """测试开发环境包含 developerMessage"""
    monkeypatch.setenv("INCLUDE_DEVELOPER_MESSAGE", "true")
    
    response = client.post("/api/user", json={"username": "admin"})
    
    assert response.status_code == 409
    data = response.json()
    assert data["title"] == "该用户名已被使用，请换一个试试"
    assert "developerMessage" in data
    assert "already exists" in data["developerMessage"]

def test_error_response_without_developer_message(client: TestClient, monkeypatch):
    """测试生产环境不包含 developerMessage"""
    monkeypatch.setenv("INCLUDE_DEVELOPER_MESSAGE", "false")
    
    response = client.post("/api/user", json={"username": "admin"})
    
    assert response.status_code == 409
    data = response.json()
    assert data["title"] == "该用户名已被使用，请换一个试试"
    assert "developerMessage" not in data  # 生产环境不返回
```

---

## 9. 迁移指南

### 9.1 从单层消息迁移

**旧代码**：
```python
raise ServiceException("用户名已存在")
```

**新代码**：
```python
raise BusinessException(
    message="该用户名已被使用，请换一个试试",
    error_code=ErrorCode.USER_ALREADY_EXISTS,
    http_status=409,
    developer_message=f"User with username='{username}' already exists in database, user_id={existing_user.id}",
    username=username
)
```

### 9.2 系统错误迁移

**旧代码**：
```python
try:
    result = await db.execute(query)
except Exception as e:
    raise ServiceException(f"数据库错误: {str(e)}")  # ❌ 暴露技术细节
```

**新代码**：
```python
try:
    result = await db.execute(query)
except Exception as e:
    raise DatabaseException(
        error_detail=f"Query failed: {str(e)}, query={query}"
    )
    # 用户看到："系统繁忙，请稍后重试"
    # 日志记录："Database operation failed: Query failed: ..., query=..."
```

---

## 10. 常见问题 (FAQ)

### Q1: 为什么不直接在响应中返回所有技术细节？
**A**: 安全原因。技术细节可能暴露系统架构、数据库结构、内部路径等敏感信息，增加安全风险。

### Q2: 开发环境和生产环境的区别是什么？
**A**: 
- 开发环境：响应包含 `developerMessage`，方便调试
- 生产环境：响应不包含 `developerMessage`，但日志中记录完整信息

### Q3: 如何追踪生产环境的错误？
**A**: 通过 `requestId` 关联响应和服务端日志，日志中包含完整的 `developer_message`。

### Q4: 业务错误和系统错误的消息策略有什么不同？
**A**:
- 业务错误：用户消息清晰描述业务问题，开发者消息略详细
- 系统错误：用户消息通用化（"系统繁忙"），开发者消息详细化技术原因

### Q5: 如何处理第三方服务的错误？
**A**: 使用 `ExternalServiceException`，用户消息通用化，开发者消息包含服务名称和详细错误。

---

## 11. 参考资料

- [RFC 7807 - Problem Details for HTTP APIs](https://tools.ietf.org/html/rfc7807)
- [Stripe API Error Handling](https://stripe.com/docs/api/errors)
- [Google Cloud API Error Model](https://cloud.google.com/apis/design/errors)
- [Microsoft Azure REST API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md#7102-error-condition-responses)
- [OWASP - Error Handling](https://owasp.org/www-community/Improper_Error_Handling)

---

**文档版本**: 1.0  
**创建日期**: 2026-01-28  
**最后更新**: 2026-01-28  
**负责人**: Kiro AI  
**状态**: 已完成

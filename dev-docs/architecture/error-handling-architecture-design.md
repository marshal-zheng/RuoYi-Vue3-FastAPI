# 统一错误处理系统 - 架构设计（标准化版）

## 1. 设计目标
- **标准模式单一化**：所有接口使用真实 HTTP 状态码 + RFC 7807 错误体
- **统一入口**：异常只在全局处理器收敛，不在 Controller try-catch
- **业务错误码补充**：`errorCode` 用于业务语义，不替代 HTTP
- **可观测性**：每个响应携带 `requestId`，日志可追踪

## 2. 当前系统要点（现状）
- 后端：
  - `utils/response_util.py` 统一返回 `{code, msg, success, time}`
  - `exceptions/handle.py` 捕获 `ServiceException/AuthException/...`
  - 默认 HTTP 200
- 前端：
  - `src/utils/http.ts` 使用 `@zxio/http`，通过 `code === 200` 判成功

## 3. 目标架构概览（标准模式）
```
Request
  ↓
Trace Middleware (生成 requestId)
  ↓
业务逻辑 (Service 抛出业务异常)
  ↓
Global Exception Handler
  ├─ 2xx 成功响应
  └─ 4xx/5xx RFC 7807 Problem Details
  ↓
Response (带 requestId)
```

## 4. 核心组件设计

### 4.1 错误码注册中心
**文件建议**：`ruoyi-fastapi-backend/config/error_codes.py`
- 统一维护业务码与系统码
- 避免散落字符串

### 4.2 异常模型
建议新增 `AppException`（或扩展 `ServiceException`）：
- `error_code`：业务码（5位）
- `http_status`：HTTP 状态码（真实语义）
- `type`：BUSINESS / AUTH / VALIDATION / SYSTEM
- `message/detail`：面向用户文案
- `data`：可选扩展信息

### 4.3 Response Builder
- 成功响应：直接返回业务数据（或标准化 envelope）
- 错误响应：RFC 7807（`application/problem+json`）
- 响应头：追加 `X-Request-Id`

### 4.4 请求追踪
- 使用现有 `TraceCtx` 生成 `requestId`
- 响应体包含 `requestId`
- 日志记录 `requestId`

## 5. 错误映射策略

| 异常类型 | http_status | type | errorCode |
|---|---|---|---|
| AuthException | 401 | AUTH | 200xx |
| PermissionException | 403 | AUTH | 300xx |
| ValidationError | 422 | VALIDATION | 10001 |
| ResourceNotFound | 404 | BUSINESS | 1xxxx/2xxxx |
| ResourceConflict | 409 | BUSINESS | 1xxxx/2xxxx |
| SystemException | 500 | SYSTEM | 50000 |

## 6. 前端适配设计（@zxio/http）

### 6.1 successResolver
- 以 **HTTP 2xx** 判定成功
- 读取 `response.status` 而非 `payload.code`

### 6.2 onError
- 优先读取 `error.response?.data`（RFC 7807）
- 提示顺序：
  1) `detail` / `title`
  2) `message` / `msg`
  3) `errorCode` 映射

### 6.3 静默错误
- 使用 `meta.silent` / `meta.silentCodes`

## 7. 迁移实施步骤（单一标准）

### 阶段 1：后端标准化
- 将异常处理器改为 RFC 7807
- 返回真实 HTTP 状态码
- 添加 `X-Request-Id`

### 阶段 2：前端适配
- 调整 `@zxio/http` 成功判定与错误解析
- 去除 `code === 200` 依赖

### 阶段 3：测试与文档
- 更新前后端测试
- 更新错误码文档与示例

## 8. 安全与合规
- 响应不输出堆栈
- 错误数据脱敏
- 详细错误信息仅在日志内可见

## 9. 测试要点
- 所有错误返回 RFC 7807 + 真实 HTTP 状态码
- 401/403/422/500 处理正确
- requestId 贯穿日志与响应


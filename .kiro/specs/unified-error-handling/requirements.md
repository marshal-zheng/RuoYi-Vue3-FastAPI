# 统一错误处理系统 - 需求文档（标准化版）

## 1. 项目概述

### 1.1 背景（结合当前项目现状）
当前项目存在以下现实情况：
- 后端已存在 `ResponseUtil`，默认以 `code/msg/success/time` 为响应体
- 现有异常处理集中在 `exceptions/handle.py`，且大量业务使用 `ServiceException`
- 前端已统一使用 `@zxio/http`，并以 `code === 200` 作为成功判定
- 业务代码仍有局部手动错误提示/捕获，容易重复与风格不一致

### 1.2 目标
建设一套**统一、标准、工程化**的错误处理系统，采用**单一标准模式**：
- **后端**：真实 HTTP 状态码 + RFC 7807 错误响应 + 结构化错误码体系
- **前端**：基于 HTTP 语义处理错误，统一拦截与展示
- **对齐国际标准**：RFC 7807 / RFC 9110 / Google API / Stripe / Azure 的通用实践

### 1.3 关键设计原则
1. **标准优先**：HTTP 状态码真实表达结果，错误使用 RFC 7807
2. **单一入口**：异常只在全局处理器统一收敛，不在 Controller 里 try-catch
3. **业务错误码作为补充**：`errorCode` 用于业务语义，不替代 HTTP 状态码
4. **可观测**：响应携带 `requestId`，日志可追踪
5. **安全**：响应中不返回堆栈信息与敏感字段

### 1.4 术语
- **Problem Details (RFC 7807)**：标准错误响应格式
- **errorCode**：业务错误码（5位数字，分模块）
- **requestId/traceId**：请求链路标识

---

## 2. 后端需求设计（标准模式）

### 2.1 错误码体系
**业务错误码（5位数字，分模块）**
- 格式：`MXXXX`
- `M` 为模块标识，`XXXX` 为具体错误码
- 示例：
  - 10001 参数校验失败
  - 20001 用户名已存在

**系统错误码（5xxxx）**
- 50000 系统未知错误
- 50001 数据库异常
- 50002 外部服务异常

**约束**
- 业务错误码仅在错误响应中使用
- HTTP 状态码始终真实反映请求结果

### 2.2 统一响应格式（单一标准）

#### 2.2.1 成功响应
使用真实 HTTP 状态码（200/201/204 等）。
```json
{
  "data": {},
  "message": "操作成功",
  "requestId": "c0d9c1f2b30f4c0faef6d62b6f6d4d71"
}
```
> 204 时无响应体。

#### 2.2.2 错误响应（RFC 7807 标准）
`Content-Type: application/problem+json`

**业务错误示例**：
```json
{
  "type": "https://api.example.com/problems/user-already-exists",
  "title": "用户已存在",
  "status": 409,
  "detail": "该用户名已被使用，请换一个试试",
  "instance": "/api/system/user",
  "errorCode": 30002,
  "requestId": "c0d9c1f2b30f4c0faef6d62b6f6d4d71"
}
```

**系统错误示例**：
```json
{
  "type": "https://api.example.com/problems/system-error",
  "title": "系统错误",
  "status": 500,
  "detail": "系统繁忙，请稍后重试",
  "instance": "/api/system/user",
  "errorCode": 50001,
  "requestId": "c0d9c1f2b30f4c0faef6d62b6f6d4d71"
}
```

**RFC 7807 字段说明**（对齐 Stripe/Google/Azure）：
- **title**: 简短错误标题（用户可读）
- **detail**: 详细错误描述（用户可读，提供可操作建议）
- **type**: 错误类型 URI（机器可读）
- **status**: HTTP 状态码
- **errorCode**: 业务错误码（补充信息）
- **requestId**: 请求追踪 ID

**消息设计原则**：
1. **title**: 简洁明了的错误类型（如"用户已存在"、"参数错误"）
2. **detail**: 友好的详细描述，提供可操作建议
3. **安全性**: 永不暴露技术细节（数据库错误、SQL、堆栈、内部路径）
4. **日志记录**: 技术细节记录在服务端日志，不返回给前端

#### 2.2.3 参数校验错误（对齐 Google Cloud API）
```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "参数验证失败",
  "status": 422,
  "detail": "请检查输入的信息是否正确",
  "instance": "/api/system/user",
  "errorCode": 10001,
  "requestId": "c0d9c1f2b30f4c0faef6d62b6f6d4d71",
  "errors": [
    { "field": "userName", "message": "用户名不能为空" },
    { "field": "email", "message": "邮箱格式不正确" }
  ]
}
```

### 2.3 异常体系（标准化）
统一为结构化异常层级（可在现有异常上扩展字段）：
```
AppException
├── AuthException
├── PermissionException
├── BusinessException
│   ├── ResourceNotFound
│   ├── ResourceConflict
│   └── ValidationError
└── SystemException
```

设计约束：
- `ServiceException` 可保留但应携带 `error_code/http_status/type`
- Controller 层不捕获异常
- Service 层抛出业务异常
- 全局异常处理器统一映射到 RFC 7807

### 2.4 全局异常处理器
- 所有异常统一输出 RFC 7807 响应
- 设置真实 HTTP 状态码
- 响应头追加 `X-Request-Id`

### 2.5 RequestId / TraceId
- 使用现有 `TraceCtx` 生成 requestId
- 响应头返回 `X-Request-Id`
- 响应体包含 `requestId`

### 2.6 错误码管理（对齐国际标准）
- 统一定义：`config/error_codes.py`
- 消息定义：
  - **title**: 简短错误标题（如"用户已存在"）
  - **detail**: 详细描述，提供可操作建议
  - 单一语言（中文），国际化通过 i18n 系统处理
- 消息设计原则：
  - **业务错误**（10xxx-40xxx）：清晰描述业务问题
  - **系统错误**（50xxx）：通用化表述（"系统繁忙，请稍后重试"）
  - **安全性**：永不暴露技术细节（数据库错误、SQL、堆栈、内部路径）
- 技术细节记录在服务端日志，不返回给前端
- 提供自动化文档生成脚本（错误码清单）

### 2.7 非功能需求
- 性能：错误处理不增加明显延迟
- 可观测：所有异常必须记录日志（包含 requestId）
- 安全：响应中不返回堆栈信息或敏感字段

---

## 3. 前端设计（基于 @zxio/http）

### 3.1 成功判定策略
- 以 **HTTP 2xx** 作为成功判定标准
- 204 无响应体需安全处理

### 3.2 响应处理规则
```
HTTP 拦截器
├── 网络错误处理
├── HTTP 状态码处理（4xx/5xx）
├── RFC 7807 错误解析
└── 成功响应处理（2xx）
```

### 3.3 错误提示规则
- 401：弹出重新登录确认框
- 403：提示权限不足
- 422：展示字段级校验错误（Notification）
- 500+：统一提示系统错误

### 3.4 静默错误配置
使用请求配置，不使用 header：
```ts
http.get({ url: '/api', meta: { silent: true, silentCodes: [10002] } })
```

### 3.5 错误消息优先级
1) `detail` / `title`（RFC 7807）
2) `message` / `msg`
3) `errorCode` 映射

---

## 4. 验收标准

### 4.1 后端
- [ ] 所有错误响应符合 RFC 7807
- [ ] 所有错误使用真实 HTTP 状态码
- [ ] `X-Request-Id` 响应头存在
- [ ] 日志包含 requestId

### 4.2 前端
- [ ] `@zxio/http` 以 HTTP 2xx 判定成功
- [ ] 非 2xx 统一走错误处理
- [ ] 401/403/422/500 提示策略生效

### 4.3 文档
- [ ] 错误码文档生成
- [ ] 前后端错误处理最佳实践

---

## 5. 约束条件
- 后端: FastAPI + Python 3.9+
- 前端: Vue 3 + TypeScript + @zxio/http（已确定）
- 不引入新的第三方依赖
- **允许一次性破坏性变更**以达成标准化

---

## 6. 风险与缓解
- **风险**：现有 `code/msg` 依赖较多，改动大
  - **缓解**：集中改造窗口 + 全量回归测试
- **风险**：前端对 RFC 7807 解析不完善
  - **缓解**：统一封装解析逻辑 + 充分错误用例覆盖

---

## 7. 参考资料
- RFC 7807 - Problem Details for HTTP APIs
- RFC 9110 - HTTP Semantics
- Google API Error Handling
- Stripe API Error Handling
- Microsoft Azure REST API Guidelines

---

**文档版本**: 2.0  \
**创建日期**: 2026-01-28  \
**最后更新**: 2026-01-28  \
**负责人**: Kiro AI

# Message 治理上下文与最佳长期方案

日期：2026-04-22

状态：原始记录（v2 - 已补充顶尖 API 设计评估与修正方向）

目的：记录本轮关于平台消息治理的有效上下文、现状审查结论，以及当前推荐的最佳长期方案，供后续规格设计和实施使用。

## 1. 本轮问题背景

当前平台存在消息提示不统一的问题，典型现象包括：

- 同一次服务端操作会出现重复提示
- 同类操作在不同页面的成功文案不一致
- 通用文案如“操作成功”语义过弱，用户无法直观看出成功了什么
- 同一类错误在 `ElMessage`、`ElNotification`、页面内联提示之间没有稳定规则
- 现有接口未来可能单独提供对外 RESTful 能力，不能把 UI 组件语义直接绑进 API contract

本轮讨论中额外确认了两个重要约束：

- 前端 `http` 模块本身具备 `message` / `modal` 等 notifier 能力
- 但对外接口设计不能直接暴露 `toast` / `dialog` / `modal` 这种 UI 指令，否则会显得过度 UI 绑定，不够专业

## 2. 现状审查结论

### 2.1 前端现状

当前前端存在多个消息出口：

- `ruoyi-fastapi-frontend/src/utils/http.ts`
- `ruoyi-fastapi-frontend/src/plugins/modal.js`
- 页面和组件中直接调用 `ElMessage.*`
- 页面和组件中直接调用 `proxy.$modal.msg*`

已确认的关键实现点：

- `ruoyi-fastapi-frontend/src/utils/http.ts`
  - 存在 `notifier` 适配器，支持 `message` 和 `modal`
  - 同时又在 `afterResponseTransform` 中手动对写操作调用 `ElMessage.success(...)`
  - 错误处理按状态码分支，混用 `ElMessage` 和 `ElNotification`
- `ruoyi-fastapi-frontend/src/plugins/modal.js`
  - 继续暴露 `msgSuccess` / `msgError` / `msgWarning`
  - 本质是另一套全局消息入口
- `ruoyi-fastapi-frontend/src/views/system/role/index.vue`
  - 角色状态切换完成后手动弹 `停用成功/启用成功`
- `ruoyi-fastapi-frontend/src/views/system/role/components/RoleFormDrawer.vue`
  - 保存角色后手动弹 `新增成功/修改成功`

### 2.2 前端消息分布扫描结果

对 `ruoyi-fastapi-frontend/src` 的粗扫描结果：

- `ElMessage.success`: 76 处
- `ElMessage.error`: 61 处
- `ElMessage.warning`: 30 处
- `$modal.msgSuccess`: 58 处
- `$modal.msgError`: 42 处
- `$modal.msgWarning`: 4 处
- `ElNotification.*`: 6 处

这说明当前问题不是单点 bug，而是平台级治理缺失。

### 2.3 后端现状

后端实际上已经具备一部分统一治理的基础：

- 有统一错误异常体系
  - `ruoyi-fastapi-backend/exceptions/exception.py`
- 有统一异常处理器
  - `ruoyi-fastapi-backend/exceptions/handle.py`
- 有统一成功/错误响应工具
  - `ruoyi-fastapi-backend/utils/response_util.py`
- 有 `BusinessType` 操作类型枚举
  - `ruoyi-fastapi-backend/config/enums.py`
- Controller 层广泛使用 `@Log(title, business_type)`

但当前后端成功响应仍然存在两个明显问题：

- 成功文案大量是自由文本，散落在 service/controller 各层
- 成功响应只返回 `message`，没有结构化业务语义，前端无法基于稳定 contract 做统一映射

### 2.4 RFC 状态结论

本轮结论明确如下：

- 错误链路应继续使用 RFC 9457 Problem Details
- 当前项目错误链路已经基本按 RFC 7807 风格实现，后续应正式对齐 RFC 9457
- 成功链路不适合硬套 Problem Details
- 当前 `ResponseUtil.success()` 注释中把成功也写成 “RFC 7807 标准” 不严谨，后续应修正

## 3. 已确认的架构判断

### 3.1 不应采用的方案

不推荐把 UI 组件语义直接放进公共 REST 响应体，例如：

```json
{
  "message": "角色已停用",
  "feedback": {
    "channel": "toast",
    "type": "success"
  }
}
```

原因：

- API contract 过度绑定 Web UI
- 第三方调用方、CLI、移动端、SDK 难以复用
- 不符合长期对外 REST 接口的专业性要求

### 3.2 最佳长期方向

最佳长期方案不是“API 告诉前端弹什么 UI”，而是：

1. 核心 API 只返回业务结果语义
2. Web 侧 `http` 层统一把业务语义映射为 UI 展示
3. 页面层不再直接写服务端 CRUD 成败提示

这套方案同时满足：

- 对外 REST 专业
- 对内 Web 能统一反馈逻辑
- 不和具体 UI 框架绑死

## 4. 最佳长期方案的数据结构

### 4.1 总体分层

接口分成三类：

1. 查询接口：返回资源数据
2. 命令接口：返回动作结果语义
3. 错误接口：RFC 9457 Problem Details

### 4.2 通用元数据

```ts
type RequestMeta = {
  requestId: string;
  traceId?: string;
  timestamp: string;
};

type PaginationMeta = {
  page: number;
  pageSize: number;
  total: number;
};
```

说明：

- `requestId` 面向客户端问题定位
- `traceId` 面向服务端分布式链路（OpenTelemetry trace-id），两者一一对应但不等同
- 两者必须同时出现在成功响应和 Problem Details 中，保证一次调用全链路可追溯

### 4.3 Warning 结构

```ts
type WarningItem = {
  code: string;
  detail?: string;
  target?: {
    id?: string | number;
    field?: string;
    name?: string;
  };
};
```

说明：

- warning 是业务语义，不是 UI warning
- 它表示“动作完成了，但有遗留问题需要提示”
- 不能完成的场景仍应走 RFC 9457 error
- **warning 与 outcome 语义边界**：
  - `outcome=succeeded` 时 `warnings` 必须为空数组或省略
  - 一旦出现 warning，outcome 必须是 `partially_succeeded`
  - 禁止出现“succeeded + 非空 warnings”的模糊态（v1 版本存在此歧义，v2 明确禁止）

### 4.4 命令结果结构（v2 修正版）

**v1 问题**：`outcome` 与 HTTP 状态码（2xx/202）语义重复；`scope`/`count` 放 meta 里脱离 data。

**v2 原则**：优先用 HTTP 语义表达通用状态，`meta.operation` 只保留 HTTP 表达不了的业务语义。

```ts
// 同步完成动作 → HTTP 200/201/204
// 异步受理动作 → HTTP 202 + Location header + data.jobId
// 部分成功    → HTTP 207 Multi-Status 或 200 + data.results[]

type OperationAction =
  | 'create' | 'update' | 'delete'
  | 'enable' | 'disable' | 'grant' | 'revoke'
  | 'import' | 'export' | 'run' | 'clean' | 'clone'
  | 'other';

type OperationMeta = {
  /** 业务事件码，对应 i18n key，必须在 code registry 注册 */
  code: string;
  /** 资源域，如 system.role / project.task */
  resource: string;
  /** 动作枚举 */
  action: OperationAction;
  /** code 的插值变量（i18n 模板参数） */
  params?: Record<string, string | number>;
  /** 动作目标（单条或代表性条目），批量走 data.results */
  target?: {
    id?: string | number;
    name?: string;
  };
  /** 见 4.3 warning 语义边界 */
  warnings?: WarningItem[];
};
```

**关键删改**：

- 删除 `outcome`：交给 HTTP 状态码（200/201/202/204/207）
- 删除 `scope` / `count`：批量场景由 `data.results[]` 自带
- 新增 `params`：前端 i18n 插值的结构化入参（见第 5 节）

### 4.5 查询响应

```ts
type QueryResponse<T> = {
  data: T;
  meta: RequestMeta & {
    pagination?: PaginationMeta;
  };
};
```

示例：

```json
{
  "data": {
    "rows": [
      { "roleId": 1, "roleName": "管理员" }
    ]
  },
  "meta": {
    "requestId": "req_20260422_001",
    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
    "timestamp": "2026-04-22T10:30:00+08:00",
    "pagination": { "page": 1, "pageSize": 20, "total": 1 }
  }
}
```

规则：

- 查询接口默认不返回 success message
- 查询成功默认不弹绿色提示

### 4.6 命令响应

```ts
type CommandResponse<T = null> = {
  data: T;
  meta: RequestMeta & {
    operation: OperationMeta;
  };
};
```

#### 4.6.1 单条成功（HTTP 200）

```json
{
  "data": null,
  "meta": {
    "requestId": "req_20260422_002",
    "traceId": "4bf92f35...",
    "timestamp": "2026-04-22T10:31:00+08:00",
    "operation": {
      "code": "system.role.disabled",
      "resource": "system.role",
      "action": "disable",
      "params": { "name": "测试角色" },
      "target": { "id": 12, "name": "测试角色" }
    }
  }
}
```

#### 4.6.2 批量部分成功（HTTP 207 Multi-Status，per-item 结果）

**v1 问题**：只给 `successCount/failedCount`，调用方无法补偿/重试。

**v2 要求**：批量一律返回 per-item `results`，每项带自身状态与错误。

```json
{
  "data": {
    "results": [
      { "id": 101, "status": "succeeded" },
      { "id": 102, "status": "succeeded" },
      {
        "id": 103,
        "status": "failed",
        "error": {
          "type": "https://api.example.com/problems/row-invalid",
          "title": "数据行无效",
          "errorCode": "ROW_INVALID",
          "detail": "字段 name 不能为空"
        }
      }
    ],
    "summary": { "total": 3, "succeeded": 2, "failed": 1 }
  },
  "meta": {
    "requestId": "req_20260422_003",
    "traceId": "...",
    "timestamp": "2026-04-22T10:32:00+08:00",
    "operation": {
      "code": "project.import.partially_succeeded",
      "resource": "project",
      "action": "import",
      "params": { "succeeded": 2, "failed": 1 }
    }
  }
}
```

#### 4.6.3 异步受理（HTTP 202 + Location + Operation-Location）

```
HTTP/1.1 202 Accepted
Location: /jobs/job_123
Operation-Location: /jobs/job_123
```

```json
{
  "data": { "jobId": "job_123" },
  "meta": {
    "requestId": "req_20260422_004",
    "traceId": "...",
    "timestamp": "2026-04-22T10:33:00+08:00",
    "operation": {
      "code": "project.export.submitted",
      "resource": "project",
      "action": "export",
      "params": { "count": 12 }
    }
  }
}
```

### 4.7 错误响应（RFC 9457 + 扩展规范）

错误统一按 RFC 9457 Problem Details，自有扩展字段必须加前缀避免与未来 IETF 字段冲突。

**扩展字段命名规则**：

- 全部归入 `ext` 对象，或
- 平铺但统一加 `x-` 前缀（团队二选一，全局保持一致）
- 本项目采用**平铺 + 无前缀但字段白名单**：`errorCode` / `requestId` / `traceId` / `errors` 四个扩展字段在项目层面冻结

资源冲突示例：

```json
{
  "type": "https://api.example.com/problems/role-name-conflict",
  "title": "角色名称已存在",
  "status": 409,
  "detail": "角色名称“管理员”已存在",
  "instance": "/system/role",
  "errorCode": "ROLE_NAME_CONFLICT",
  "requestId": "req_20260422_005",
  "traceId": "4bf92f35..."
}
```

422 校验示例（对齐 IETF draft-ietf-httpapi-problem-field-validation）：

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "参数验证失败",
  "status": 422,
  "detail": "请检查输入的信息是否正确",
  "instance": "/system/role",
  "errorCode": "VALIDATION_ERROR",
  "requestId": "req_20260422_006",
  "traceId": "...",
  "errors": [
    { "field": "roleName", "message": "角色名称不能为空", "code": "REQUIRED" }
  ]
}
```

429 限流示例（必须带标准 RateLimit 头）：

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
RateLimit-Limit: 100
RateLimit-Remaining: 0
RateLimit-Reset: 30
```

## 5. i18n 与 code registry 治理

**v1 缺失**：只提了 `code: "system.role.disabled"`，没有 i18n 规范。**v2 补足**。

### 5.1 code 命名规范

- 格式：`{resource}.{action}.{result}`，全小写，点分隔
- 示例：`system.role.disabled` / `project.import.partially_succeeded`
- `result` 枚举：`created` / `updated` / `deleted` / `enabled` / `disabled` / `submitted` / `partially_succeeded` / `completed`
- 禁止出现空格、中文、大写、下划线

### 5.2 code registry（注册表）

- 位置：`docs/api/operation-codes.yaml`（单一真源）
- 每条 code 必须登记：
  - `code` / `description` / `defaultAction` / `params`（插值变量契约）/ `deprecatedAt`
- 后端 `ResponseUtil.command(code=...)` 在启动时校验 code 是否在 registry 内，非注册 code 直接报错
- 废弃策略：标 `deprecatedAt`，保留 2 个大版本后移除
- CI 阶段扫描前端 i18n 文件，任何缺失 code 的翻译必须报 fail

### 5.3 翻译文件组织

```
ruoyi-fastapi-frontend/src/locales/
├── zh-CN/
│   └── operations.json   # key 与 code 一一对应
└── en-US/
    └── operations.json
```

```json
{
  "system.role.disabled": "角色 {name} 已停用",
  "project.import.partially_succeeded": "导入完成：成功 {succeeded} 条，失败 {failed} 条"
}
```

- 插值变量名必须与 `operation.params` 字段名一致
- fallback：目标语言缺失 → en-US → `code` 原文（最后兜底，禁止降级为“操作成功”）
- 复数走 ICU MessageFormat（`{count, plural, one {...} other {...}}`）

### 5.4 后端是否返回本地化文本？

**决策：不返回**。后端只返回 `code` + `params`，所有本地化由前端完成。

理由：

- 后端返回文本会污染 API contract、导致 SDK 多语言复杂化
- `Accept-Language` 仅用于后端日志 / 邮件 / 推送等脱离 HTTP 响应的通道
- 移动端、CLI、第三方 SDK 可各自维护翻译包

## 6. 前端反馈层契约

前端 `http` 层是服务端反馈**默认**出口，但必须提供结构化 opt-out 机制。

### 6.1 展示默认规则

- `GET` / 查询成功：不提示
- HTTP 2xx 命令：绿色 `message`
- HTTP 202 命令：蓝色 `message` 或轻量通知（含"查看进度"跳转 Operation-Location）
- HTTP 207 部分成功：黄色 `notification` 或页面级 `banner`，展开显示失败项
- HTTP 422：优先表单内联（按 `errors[].field` 映射），不只打一条红 toast
- HTTP 409/403/404 等其他 4xx：红色错误反馈
- HTTP 429：红色错误 + 显示 `Retry-After` 倒计时
- HTTP 5xx：红色错误 + 含 `requestId` / `traceId` 以便用户反馈
- `dialog` 只用于前端提交前确认，不来自 API

### 6.2 调用端声明式配置（opt-out 与扩展）

```ts
// 每个 http 调用支持这些配置
interface RequestOptions {
  /** 静默：完全不弹任何提示（自动保存、轮询等场景） */
  silent?: boolean;
  /** 手动接管：http 层不弹，调用端自行处理 meta.operation */
  feedback?: 'auto' | 'manual' | 'silent';
  /** 自定义 code → 文案映射覆盖 */
  i18nOverrides?: Record<string, string>;
  /** idempotency key（命令接口建议传） */
  idempotencyKey?: string;
}
```

### 6.3 页面层边界（比 v1 更清晰）

**页面层禁止**（lint 强制）：

- 调用 `ElMessage.*` / `$modal.msg*` 处理服务端 CRUD 响应
- 自己拼“新增成功”“删除成功”等服务端反馈文案

**页面层允许**：

- 本地表单校验提示（未发起请求前）
- 图形交互、拖拽、上传器进度等本地 UX 状态
- WebSocket / SSE 实时事件提示（非 HTTP 响应）
- 基于 `response.meta.operation` 做**业务逻辑**（跳转、刷新、乐观更新回滚），但不再**显示**文案
- 传 `feedback: 'manual'` 完全接管反馈（需 code review 审批）

### 6.4 必备的横切能力

- **Idempotency-Key**：所有非幂等命令接口支持 `Idempotency-Key` header，后端 24h 窗口去重（对齐 Stripe / IETF draft-ietf-httpapi-idempotency-key-header）
- **分布式追踪**：接入 OpenTelemetry，`traceparent` header 贯穿前后端
- **API 版本**：URL path 版本（`/api/v1/...`），破坏性变更走 v2，deprecated 端点返回 `Deprecation` / `Sunset` header

## 7. 需要治理的现有反模式

需要逐步消除以下反模式：

- 后端成功响应默认值使用“操作成功”
- Controller 和 service 到处散落 `新增成功/更新成功/删除成功`
- 页面直接调用 `ElMessage.success/error/warning` 处理服务端 CRUD 结果
- 页面直接调用 `$modal.msgSuccess/msgError` 处理服务端 CRUD 结果
- 同一个动作同时由 `http.ts` 和页面各弹一次
- 把“部分成功”混成纯 success
- 批量接口只返回聚合数字、不返回 per-item 结果
- 使用未注册的 operation code
- 成功响应里同时出现 `succeeded` 和非空 `warnings`

## 8. 后续推荐改造方向

### 8.1 后端

- 保留并规范化 RFC 9457 错误实现，四个扩展字段白名单锁定
- 新增两类成功响应工具：
  - `ResponseUtil.data(data, pagination=None)` → 查询
  - `ResponseUtil.command(code, *, params=None, target=None, data=None, http_status=200, warnings=None)` → 命令
  - `ResponseUtil.batch(code, *, results, params=None)` → 批量（自动 207）
- 不再让查询接口返回“操作成功”
- 命令接口统一返回 `meta.operation`
- warning 统一用结构化 `warnings[]`，且遵守 4.3 语义边界
- `BusinessType` / `@Log(title, business_type)` 作为 code 默认推断，但 controller 必须显式声明 `operation_code`
- 启动时校验所有 code 在 registry 内
- 接入 OpenTelemetry，把 `traceId` 注入所有响应

### 8.2 前端

- `ruoyi-fastapi-frontend/src/utils/http.ts` 成为服务端反馈唯一默认出口，支持 `silent` / `feedback` / `i18nOverrides` / `idempotencyKey` 选项
- 新增统一反馈层：
  - `src/platform/feedback/types.ts`
  - `src/platform/feedback/presenter.ts`（HTTP 状态 + operation 到 UI 的映射表）
  - `src/platform/feedback/policies.ts`（默认规则 + opt-out 合并策略）
  - `src/platform/feedback/i18n.ts`（code + params → 本地化文本，带 fallback）
- `src/plugins/modal.js` 不再作为服务端 CRUD 反馈主入口（保留确认对话框能力）
- 页面层移除服务端 CRUD 的直接消息调用

### 8.3 治理规则

- 禁止公共 REST API 返回 `toast/dialog/modal`
- 禁止页面层直接写服务端 CRUD 的成功/失败 toast（ESLint 规则 + PR 检查）
- 禁止 mutation 成功只返回“操作成功”
- 禁止把提交前确认做成后端响应的一部分
- 禁止使用未注册 code
- 禁止批量接口只返回聚合数字

## 9. 建议的迁移顺序

1. 先冻结目标 contract（含 operation code registry 初版）
2. 改后端成功响应模型与 `ResponseUtil`，加 code 启动时校验
3. 接入 OpenTelemetry，前后端响应都带 `traceId`
4. 改前端 `http.ts` 按 HTTP 状态 + `meta.operation` 统一映射，实现 i18n 层
5. 加 ESLint 规则（`no-raw-elmessage-for-crud`）
6. 先迁移 `system/user`、`system/role`、`monitor/job`
7. 批量改造导入/导出类接口到 per-item results
8. 批量清理页面中的服务端 CRUD `ElMessage` / `$modal`
9. 补 Idempotency-Key 支持（命令接口）
10. 增加 PR review rule 与 CI 检查，阻止新增直接调用

## 10. 本轮最终结论

本轮最终推荐的最佳长期方案是：

- **错误**：RFC 9457 Problem Details + 四个扩展字段白名单（errorCode / requestId / traceId / errors）
- **成功查询**：资源数据响应，不返回 success 文案
- **成功命令**：HTTP 状态码承担通用状态（2xx/202/207），`meta.operation` 只承载业务语义（code + params + target），删除与 HTTP 重复的 outcome/scope/count
- **批量命令**：per-item `results[]`，可补偿、可重试
- **i18n**：code registry + 前端翻译，后端不返回本地化文本
- **横切能力**：traceId / Idempotency-Key / 标准 RateLimit headers / API 版本
- **Web `http` 层**：统一决定展示方式，支持 `silent` / `feedback: 'manual'` opt-out
- **页面层**：不再手写服务端 CRUD 成败消息，但可接管业务逻辑

这是一套兼顾长期专业性、平台统一治理能力、客户端解耦和可国际化的方案，对齐 Stripe / GitHub / Google Cloud / Microsoft Graph 等头部 API 的工程实践。

## 11. v1 → v2 修正摘要

| 项 | v1 | v2 |
|---|---|---|
| `operation.outcome` | `succeeded`/`partially_succeeded`/`accepted` | **删除**，由 HTTP 状态码承担 |
| `operation.scope` / `count` | meta 里的聚合字段 | **删除**，批量走 `data.results[]` |
| 批量响应 | `successCount` / `failedCount` | per-item `results[]` + `summary`，HTTP 207 |
| i18n | 未提 | code registry + `params` 插值 + fallback 链 |
| RFC 9457 扩展字段 | 未约束 | `errorCode` / `requestId` / `traceId` / `errors` 白名单 |
| 追踪 | 仅 `requestId` | `requestId` + `traceId`（OpenTelemetry） |
| warning 语义 | 与 succeeded 可叠加（模糊） | 与 outcome 互斥，出现 warning 必 partially |
| 前端 opt-out | 仅说"页面可处理本地 warning" | `silent` / `feedback: 'manual'` / `i18nOverrides` 声明式 API |
| Idempotency | 未提 | 命令接口必须支持 `Idempotency-Key` |
| 限流 | 未提 | 标准 `RateLimit-*` + `Retry-After` headers |
| API 版本 | 未提 | URL path 版本 + `Deprecation` / `Sunset` headers |

## 12. 参考资料

- RFC 9457 Problem Details for HTTP APIs
  - https://datatracker.ietf.org/doc/html/rfc9457
- IETF Problem Details Validation Fields (draft)
  - https://datatracker.ietf.org/doc/draft-ietf-httpapi-problem-field-validation/
- IETF Idempotency-Key Header (draft)
  - https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/
- IETF RateLimit Header Fields for HTTP (draft)
  - https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
- RFC 8594 The Sunset HTTP Header Field
  - https://datatracker.ietf.org/doc/html/rfc8594
- OpenTelemetry Trace Context (W3C)
  - https://www.w3.org/TR/trace-context/
- ICU MessageFormat
  - https://unicode-org.github.io/icu/userguide/format_parse/messages/
- Stripe API Design
  - https://stripe.com/docs/api
- Google Cloud API Design Guide
  - https://cloud.google.com/apis/design
- Microsoft REST API Guidelines
  - https://github.com/microsoft/api-guidelines
- Atlassian Success Messages
  - https://atlassian.design/foundations/content/designing-messages/success-messages
- IBM Carbon Notification Usage
  - https://carbondesignsystem.com/components/notification/usage/
- Microsoft Fluent Message Bar Usage
  - https://fluent2.microsoft.design/components/web/react/core/messagebar/usage
- Ant Design Message
  - https://ant.design/components/message/

# 平台消息治理与 API 反馈契约 需求规格

## 简介

本规格定义平台级“消息治理与 API 反馈契约”的最终长期方案，目标是在不再频繁重构响应结构的前提下，同时解决以下问题：

- 后端成功响应语义混乱，列表、详情、写操作和批量操作缺少稳定边界。
- 前端默认反馈出口、页面直接提示和旧兼容层并存，导致重复提示和弱语义提示长期存在。
- 错误响应已基本接近 Problem Details，但仍残留旧 `{code,msg,success}` 风格出口，没有彻底收口。

本规格采用的长期方向如下：

- 错误：统一采用 RFC 9457 Problem Details。
- 成功：采用资源导向的 HTTP 语义，不引入全局 success envelope。
- 前端：由统一反馈层拥有默认反馈与成功文案，页面层不再直接处理服务端 CRUD 成败提示。
- 发布：在现有 API 路径上对业务 JSON HTTP API 硬切，不保留温和兼容窗口。

## 非目标

- 不要求完整采用 JSON:API、OData 或其他完整文档规范。
- 不要求由后端返回 `toast`、`dialog`、`modal` 等 UI 指令。
- 不要求在成功响应上定义全局 `{ data, meta }` envelope。
- 不要求在成功响应上定义全局 `meta.operation` / operation code registry 运行时 contract。
- 不要求在本轮重做 `health` / `metrics` / `docs`、二进制下载、streaming、WebSocket / SSE、本地拖拽等协议型或非业务 JSON 响应链路。
- 不要求在本轮引入 operation code registry、多语言反馈文案或后端返回 i18n key；前端反馈层文案本轮以单一语言（zh-CN）硬编码内置于 feedback registry，未来如需 i18n 仅替换渲染层，不视为契约 breaking change。
- 不要求在本轮实现 cursor/keyset 分页的业务落地；列表契约预留 cursor 模式字段以便未来扩展，但本轮所有业务列表接口仅使用 offset-total 模式。
- 不要求在本轮支持仓库外部调用方（移动端 App、第三方 SDK、CLI）；本次硬切的前提假设是当前业务 JSON HTTP API 仅被仓库内 `ruoyi-fastapi-frontend` 一个消费方使用，因此不引入 `Deprecation` / `Sunset` 头或 `/v2` 并行路径。

## 需求列表

### R1: API contract 必须与 UI 展示彻底解耦
**用户故事:** 作为平台架构维护者，我希望公共 API 返回稳定的资源或业务结果，而不是 UI 指令，以便 Web、移动端、CLI、SDK 和第三方调用方都能复用同一套 contract。  
**验收标准 (EARS):**
- R1.AC1: WHEN 公共 HTTP API 返回成功结果 THEN 系统 SHALL 返回资源、集合或动作结果，而 SHALL NOT 返回 `toast`、`dialog`、`modal` 等 UI 组件指令。
- R1.AC2: WHEN 公共 HTTP API 被 Web 端以外的调用方消费 THEN 该 contract SHALL 能直接理解和复用，而 SHALL NOT 额外依赖 Element Plus、页面路由或前端组件语义。
- R1.AC3: WHEN 服务端需要表达“成功了什么” THEN 系统 SHALL 优先使用 HTTP 状态码和资源/结果对象表达语义，而 SHALL NOT 依赖自由文本成功文案作为主 contract。

### R2: 成功响应必须采用资源导向语义而不是全局 success envelope
**用户故事:** 作为前后端开发者，我希望不同类型的成功响应有清晰、长期稳定的返回模式，以便后续不再因 success envelope 反复改结构。  
**验收标准 (EARS):**
- R2.AC1: WHEN 详情查询接口成功 THEN 系统 SHALL 返回资源对象或该查询专属结果对象，而 SHALL NOT 依赖根级 success message 驱动调用方逻辑。
- R2.AC2: WHEN 列表查询接口成功 THEN 系统 SHALL 返回集合结果对象，其主集合字段 SHALL 为 `items`，且默认分页模式 SHALL 使用 `total`、`page`、`pageSize` 这组显式字段，而 SHALL NOT 继续使用遗留的 `rows` 作为长期字段名。
- R2.AC3: WHEN 创建资源成功 THEN 系统 SHALL 默认返回符合 HTTP 语义的创建结果，例如 `201 Created` 与新创建的完整资源；仅在明确不需要响应体时才允许返回更小结果对象。
- R2.AC4: WHEN 更新资源成功 THEN 系统 SHALL 默认返回更新后的完整资源；仅在明确不需要响应体时才允许返回 `204 No Content`，而 SHALL NOT 仅返回“修改成功”等自由文本。
- R2.AC5: WHEN 删除资源成功 THEN 系统 SHALL 优先返回 `204 No Content`，除非业务确实需要返回额外结果对象。
- R2.AC6: WHEN 业务 JSON HTTP API 返回成功结果 THEN 系统 SHALL NOT 强制包裹为统一的 `{ data, meta }` success envelope。

### R3: 异步、批量和部分成功场景必须采用专门模式
**用户故事:** 作为调用方开发者，我希望异步、批量和部分成功有稳定的专门返回模式，以便调用方可正确展示、补偿和重试。  
**验收标准 (EARS):**
- R3.AC1: WHEN 命令接口被异步受理 THEN 系统 SHALL 返回 `202 Accepted`，并提供用于查询进度的定位信息（例如 `Location` 或等效任务资源定位）。
- R3.AC2: WHEN 批量操作成功或部分成功 THEN 系统 SHALL 返回对象级 `results[]` 或等效逐项结果结构，而 SHALL NOT 仅返回聚合数字。
- R3.AC3: WHEN 批量操作出现部分失败 THEN 系统 SHALL 让调用方能够识别每一项的成功、失败和失败原因，而 SHALL NOT 把部分成功伪装成纯成功消息。
- R3.AC4: WHEN 某写操作本质上返回的是业务动作结果而非资源 THEN 系统 SHALL 返回该动作专属结果对象，而 SHALL NOT 为了统一而套入全局 success envelope。
- R3.AC5: WHEN 批量操作出现部分成功或部分失败 THEN 系统 SHALL 默认使用 `200 OK` 配合 `results[]` / `summary` 表达逐项状态，而 SHALL NOT 将 `207 Multi-Status` 作为本规格下的常规默认策略。

### R4: 错误响应必须统一对齐 RFC 9457 Problem Details
**用户故事:** 作为客户端开发者，我希望所有错误都遵循稳定标准，以便统一展示、定位、重试与自动化处理。  
**验收标准 (EARS):**
- R4.AC1: WHEN 业务 JSON HTTP API 返回错误 THEN 系统 SHALL 使用 RFC 9457 Problem Details 结构，并返回 `application/problem+json`。
- R4.AC2: WHEN 平台返回问题详情对象 THEN 核心字段 SHALL 包含 `type`、`title`、`status`、`detail`、`instance`。
- R4.AC3: WHEN 平台返回项目自定义扩展信息 THEN 扩展字段 SHALL 收敛为冻结白名单：`errorCode`、`requestId`、`traceId`、`errors`，其他扩展字段仅在明确设计后引入。
- R4.AC4: WHEN 参数校验失败 THEN 系统 SHALL 返回字段级 `errors[]` 结构，供前端映射到表单或字段提示。
- R4.AC5: WHEN 发生服务器错误或未知异常 THEN 系统 SHALL 返回可追踪的问题详情对象，而 SHALL NOT 暴露未审计的底层技术细节。
- R4.AC6: WHEN 仓库内仍存在旧 `{code,msg,success}` 风格错误出口 THEN 这些出口 SHALL 被清理或禁止作为长期正式 contract。

### R5: 前端统一反馈层必须拥有默认反馈与成功文案
**用户故事:** 作为前端维护者，我希望服务端 CRUD 的默认反馈只有一个所有者，以便避免重复提示和页面层散落文案。  
**验收标准 (EARS):**
- R5.AC1: WHEN Web 端收到业务 JSON HTTP API 响应 THEN 系统 SHALL 由统一反馈层作为默认反馈出口，而 SHALL NOT 让页面层和 `http` 层并行各弹一次消息。
- R5.AC2: WHEN 服务端 CRUD 响应需要展示成功反馈 THEN 成功文案 SHALL 由前端统一反馈层或其 presenter/registry 生成，而 SHALL NOT 由后端 success body 作为长期主来源。
- R5.AC3: WHEN 页面处理服务端 CRUD 响应 THEN 页面层 SHALL NOT 直接调用 `ElMessage.*`、`ElNotification.*` 或 `$modal.msg*` 生成默认成败提示。
- R5.AC4: IF 请求显式声明 `silent` 或 `feedback='manual'` THEN 统一反馈层 SHALL 允许调用端接管展示逻辑。
- R5.AC5: WHEN 场景属于提交前确认、本地表单校验、本地交互状态或非 HTTP 实时事件 THEN 页面层 MAY 使用本地反馈能力。

### R6: Web 端必须对不同 HTTP/业务语义采用稳定展示策略
**用户故事:** 作为最终用户，我希望相同行为在不同页面得到一致、可理解的反馈，以便减少误判与困惑。  
**验收标准 (EARS):**
- R6.AC1: WHEN 普通写操作以 2xx 成功完成 THEN Web 端 SHALL 采用统一的正向反馈策略，而 SHALL NOT 依赖后端 success message 原文透传。
- R6.AC2: WHEN 接口返回 `202 Accepted` THEN Web 端 SHALL 展示“已受理/可查看进度”的反馈，而 SHALL NOT 假装任务已完成。
- R6.AC3: WHEN 批量接口出现部分成功 THEN Web 端 SHALL 使用可承载失败明细的 warning/notification/banner 反馈，而 SHALL NOT 将其展示为纯成功 toast。
- R6.AC4: WHEN 接口返回 422 字段级错误 THEN Web 端 SHALL 优先支持字段级或表单级映射，而 SHALL NOT 只打一条红色 toast。
- R6.AC5: WHEN 接口返回 403、404、409、429 或 5xx 错误 THEN Web 端 SHALL 展示一致的错误反馈，并在适用时带出 `requestId` / `traceId` / 限流信息。
- R6.AC6: WHEN 查询接口成功 THEN Web 端默认反馈层 SHALL NOT 弹出绿色成功提示。

### R7: 响应必须具备跨链路追踪、幂等和限流基础
**用户故事:** 作为运维与问题排查人员，我希望任何一次调用都可追踪、可安全重试、可限流，以便线上问题可定位且调用方行为可控。  
**验收标准 (EARS):**
- R7.AC1: WHEN 系统返回成功响应 THEN 系统 SHALL 通过响应头携带 `requestId`，并在可用时通过响应头携带 `traceId`，而 SHALL NOT 为此污染资源导向的成功响应体结构。
- R7.AC2: WHEN 调用链存在分布式追踪上下文 THEN 系统 SHALL 贯通并返回与该调用对应的 `traceId`。
- R7.AC3: WHEN 客户端对非幂等写操作发起可能重试的请求 THEN 系统 SHALL 支持 `Idempotency-Key` 语义以避免重复执行。
- R7.AC4: WHEN 接口触发限流 THEN 系统 SHALL 返回标准化 `Retry-After` 与 RateLimit 相关响应头，供客户端统一展示与退避。
- R7.AC5: WHEN 系统返回 RFC 9457 Problem Details 错误响应 THEN 响应体 SHALL 包含 `requestId` 与可用的 `traceId` 扩展字段，并 SHOULD 同时通过响应头回传相同追踪标识。

### R8: 治理规则必须可被静态检查、契约测试和 CI 强制执行
**用户故事:** 作为代码治理维护者，我希望坏模式不能继续靠 code review 人肉兜底，以便平台标准长期稳定生效。  
**验收标准 (EARS):**
- R8.AC1: WHEN 前端页面新增服务端 CRUD 的直接消息调用 THEN 系统 SHALL 通过 ESLint 规则、扫描脚本或等效机制阻断合入。
- R8.AC2: WHEN 后端新增旧 `{code,msg,success}` 风格错误响应或旧错误出口调用 THEN 系统 SHALL 在测试或检查阶段失败。
- R8.AC3: WHEN 后端新增业务 JSON HTTP API 的成功响应 THEN 系统 SHALL 符合资源导向模式，而 SHALL NOT 再引入全局 success envelope 或自由文本成功 contract。
- R8.AC4: WHEN 后端新增批量或异步接口 THEN 系统 SHALL 通过契约测试验证 `results[]`、`202 Accepted` 或等效专门模式是否正确实现。
- R8.AC5: WHEN DELETE/写操作不需要响应体 THEN 系统 SHALL 通过契约测试验证其是否正确使用 `204` 或明确的结果对象语义。
- R8.AC6: WHEN command handler 组装 `CommandResult.data` THEN 系统 SHALL 仅放入业务结果字段，而 SHALL NOT 把 service 层 `message/msg` 作为成功 contract 回流。
- R8.AC7: WHEN controller 消费 command result THEN 系统 SHALL 按接口语义选择 `ok_resource/created_resource/batch_result/no_content` 等显式工厂，而 SHALL NOT 直接把 `_result.data` 透传到成功响应。
- R8.AC8: WHEN 文件上传、导入或其他非标准回调链路完成 THEN 前端 SHALL 消费结构化结果或显式 manual feedback，而 SHALL NOT 读取 `response.msg/res.msg` 作为服务端成功文案。

### R9: 现有系统必须在现有路径上按硬切方式完成统一调整
**用户故事:** 作为仓库维护者，我希望这次治理在现有系统中一次切到位，以便尽快消除双轨 contract、双套提示逻辑和长期兼容成本。  
**验收标准 (EARS):**
- R9.AC1: WHEN 新契约开始落地 THEN 系统 SHALL 在现有 API 路径上直接执行硬切，而 SHALL NOT 新增并行 `/v2` 或等效平行路径来维持旧 contract。
- R9.AC2: WHEN 本次硬切实施 THEN 所有业务 JSON HTTP API 的后端接口、前端 `http` 层适配、页面反馈逻辑、测试和治理规则 SHALL 在同一轮切换中完成调整。
- R9.AC3: WHEN 本次硬切完成 THEN 仓库内消费这些接口的现有调用方 SHALL 已迁移到新契约，而 SHALL NOT 继续依赖旧 success message 或旧错误形状。
- R9.AC4: IF 接口属于 `health` / `metrics` / `docs`、二进制下载、streaming 或其他协议型、非业务 JSON 响应 THEN 这些接口 MAY 保持各自协议约定，而 SHALL NOT 被强制套用本规格的 success 结构。
- R9.AC5: WHEN 引入本次 breaking change THEN 系统 SHALL 在规格、实现、测试和发布说明中明确标记受影响范围，并在合入前完成仓库内联动修改。
- R9.AC6: WHEN 本次治理实施 THEN 系统 SHALL 优先保留现有动作型 URL 与路由组织方式，只统一响应契约、错误标准和前端反馈规则；动作接口的资源导向 URL 重构 SHALL NOT 作为本轮必做范围。

## Clarifications

### Session 2026-04-23
- Q: 错误部分最终采用什么标准？ -> A: 采用 RFC 9457 Problem Details，并把现有 Problem Details 风格实现正式收口到该标准术语和正式出口。
- Q: 成功响应是否需要统一成全局 `{ data, meta }`？ -> A: 不需要；成功采用资源导向语义，不引入全局 success envelope。
- Q: 成功响应是否需要统一成 `meta.operation` / operation code registry？ -> A: 不需要；成功反馈文案由前端统一反馈层拥有，不把它设计成公共 API 运行时 contract。
- Q: 现有系统怎么上线这套方案？ -> A: 在现有 API 路径上硬切，覆盖所有业务 JSON HTTP API，不保留温和兼容窗口。
- Q: 哪些链路不纳入本次强制统一？ -> A: `health` / `metrics` / `docs`、二进制下载、streaming、WebSocket / SSE 等协议型或非业务 JSON 响应链路不强制套用本规格的 success 结构。
- Q: 列表分页的长期主模式是什么？ -> A: 采用 offset-total 模式，列表默认返回 `items`、`total`、`page`、`pageSize`。
- Q: create/update 成功后的长期主模式是什么？ -> A: 默认返回完整资源；仅在明确不需要响应体时才返回 `204` 或更小结果对象。
- Q: 现有大量动作型接口 URL 是否要在本轮一起改成更资源导向的路由？ -> A: 不改；本轮保留现有动作型 URL，只统一响应契约、错误标准和前端反馈。
- Q: 成功响应里的 `requestId/traceId` 放哪里？ -> A: 成功响应放在响应头；错误响应继续在 Problem Details body 中带出并同时保留响应头。
- Q: 批量部分成功的默认状态码策略是什么？ -> A: 默认使用 `200 OK` 配合 `results[]/summary` 表达逐项状态，不把 `207 Multi-Status` 作为常规默认策略。

### Session 2026-04-23 (设计评审)
- Q: 本轮是否引入 i18n / operation code registry？ -> A: 不引入；前端反馈层文案本轮以 zh-CN 硬编码存入 feedback registry，未来如需多语言仅替换渲染层。
- Q: cursor 分页本轮是否实现？ -> A: 不实现业务落地，但契约层预留 `nextCursor` 可选字段与后端 `ok_cursor` 工厂签名；本轮所有业务列表接口仅使用 offset 模式。
- Q: 本次硬切是否考虑外部调用方？ -> A: 不考虑；假设当前业务 JSON HTTP API 仅被仓库内前端消费，因此不引入 `Deprecation` / `Sunset` 头或并行路径。
- Q: Problem Details `type` 使用相对路径还是绝对 URL？ -> A: 使用绝对 URL；应用层通过可配置前缀（如 `PROBLEM_TYPE_BASE_URL`）拼接，未映射到具体 problem slug 的通用错误回退为 `about:blank`，不把拼装职责丢给网关。
- Q: 校验错误 `errors[].code` 的值域如何定义？ -> A: 直接采用 pydantic v2 的原生 `type`（如 `missing` / `string_too_short` / `value_error`），不自定义映射层。
- Q: 非分页的纯集合列表（字典枚举等）是否强制带分页字段？ -> A: 不强制；成功响应模式拆分为 `ok_collection`（纯集合，仅 `items`）与 `ok_page`（offset 分页）两个显式工厂，业务按语义选择。
- Q: 批量 `results[i].error` 是否是完整 Problem Details？ -> A: 不是；仅保留 `errorCode` / `title` / `detail` 三字段，不带 `type` / `status` / `instance`，避免被误当成完整 Problem Details 处理。
- Q: 限流响应头采用 IETF 最新单头结构化草案还是旧三头？ -> A: 本项目固定采用旧三头方案 `RateLimit-Limit` / `RateLimit-Remaining` / `RateLimit-Reset`，等 IETF 草案定稿后再考虑切换。

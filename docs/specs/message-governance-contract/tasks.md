# 平台消息治理与 API 反馈契约 实现任务

- 1. 建立硬切迁移基线与受影响范围清单
  - 盘点全部业务 JSON HTTP API，按"列表/详情/写操作/批量/异步/排除范围"分类，形成本轮硬切迁移清单：产出 `docs/specs/message-governance-contract/migration-inventory.md`。
  - 明确 `health` / `metrics` / `docs`、二进制下载、streaming、WebSocket / SSE 的排除规则，并在清单中标记不纳入 success 结构统一（见 inventory 第 14 节）。
  - 盘点前端受影响的 `src/api/**`、`src/views/**`、`src/utils/http.ts`、`src/utils/request.ts`、表格封装与代码生成模板，作为同轮联动修改基线。
  - 在发布说明草案中明确"现有路径硬切、无 `/v2`、保留动作型 URL、不保留 success message 兼容"的 breaking change 边界。
  - 后续各 Task 的实施均以 `migration-inventory.md` 为勾选基线，每条目迁移完成后在清单中打勾。
  *需求追溯: R9.AC1, R9.AC4, R9.AC5, R9.AC6*
- 1. 重构后端响应工厂为资源导向成功契约与 RFC 9457 错误契约
  - 重写 `ruoyi-fastapi-backend/utils/response_util.py`，落地 `ok_resource`、`ok_collection`、`ok_page`、`ok_cursor`（签名预留，本轮无业务接入）、`created_resource`、`accepted_job`、`batch_result`、`no_content` 等显式语义方法。
  - 删除 success body 中的 `message`、`msg`、`requestId`，删除 `rows`、`dict_content`、`model_content` 这种可绕开契约边界的拼装入口；禁止泛化的 `success(msg=..., rows=...)` / `ok_list(total=None)` 双形态写法。
  - 收敛 `problem_details()` / `validation_problem()`，仅保留 RFC 9457 核心字段与冻结扩展字段 `errorCode`、`requestId`、`traceId`、`errors`；`type` 由可配置前缀 `PROBLEM_TYPE_BASE_URL` 拼接为绝对 URL，未映射 slug 时回退 `about:blank`；`errors[].code` 直接透传 pydantic v2 原生 `type`。
  - `created_resource` / `accepted_job` 的 `Location` 必须输出绝对 URL；`batch_result` 的 `results[i].error` 仅保留 `errorCode/title/detail` 三字段，不输出 `type/status/instance`。
  - 删除旧 `failure` / `unauthorized` / `forbidden` / `error` 出口，并同步更新 `tests/unit/test_response_util.py`、`tests/unit/utils/test_response_naming.py`。
  *需求追溯: R1.AC1, R1.AC2, R1.AC3, R2.AC1, R2.AC3, R2.AC4, R2.AC5, R2.AC6, R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R4.AC6, R7.AC1, R7.AC5*
- 1. 打通异常转换、追踪头与跨域暴露链路
  - 调整 `ruoyi-fastapi-backend/exceptions/handle.py`，让 `AppException`、校验异常、HTTP 异常和未知异常全部只走 RFC 9457 Problem Details 单一出口。
  - 重构 `ruoyi-fastapi-backend/module_admin/annotation/log_annotation.py`，移除在装饰器中直接构造旧风格错误响应的逻辑，统一改为抛出标准异常。
  - 为成功与错误响应统一写入 `X-Request-Id`、`X-Trace-Id`，并改造 trace 解析逻辑，优先接入 `traceparent`，兼容内部 `X-Trace-Id` 输入。
  - 更新 CORS 暴露头配置，确保浏览器可读取 `X-Request-Id`、`X-Trace-Id`、`Location`、`Retry-After`、`RateLimit-`*。
  *需求追溯: R4.AC1, R4.AC5, R7.AC1, R7.AC2, R7.AC5, R9.AC2*
- 1. 标准化幂等与限流中间件契约
  - 改造 `ruoyi-fastapi-backend/middlewares/idempotency_middleware.py`，将入站幂等头从 `X-Idempotency-Key` 切换为标准 `Idempotency-Key`。
  - 改造 `ruoyi-fastapi-backend/middlewares/rate_limit_middleware.py`，将限流头统一为 `Retry-After`、`RateLimit-Limit`、`RateLimit-Remaining`、`RateLimit-Reset`。
  - 清理限流和幂等冲突场景下 Problem Details 中的非白名单扩展字段，确保错误 body 不再塞入 `data` 或临时结构。
  - 更新相关单元测试与中间件注册验证，确保全局链路顺序不破坏回放、限流与外层通用中间件行为。
  *需求追溯: R4.AC1, R4.AC3, R7.AC3, R7.AC4, R7.AC5, R8.AC4*
- 1. 批量迁移业务 JSON 控制器到新成功响应模式
  - 逐模块迁移 `modules/system/api/`*、`modules/project/api/*`、`modules/scheduler/api/*`、`module_admin/controller/*`、`module_generator/controller/*` 中的业务 JSON 控制器。
  - 将详情查询统一改为资源对象响应；字典/枚举等纯集合接口使用 `ok_collection({items})`；带筛选分页的列表统一使用 `ok_page({items,total,page,pageSize})`；将创建/更新统一改为完整资源返回；将删除默认改为 `204 No Content`。
  - 在请求参数层统一对外使用 `page` / `pageSize`，必要时仅保留内部 alias 以支持仓库内迁移，不向外继续暴露 `pageNum` / `rows`。
  - 保留现有动作型 URL 与路由组织方式，不在本轮做资源导向 URL 重写，同时清理 success message 依赖和旧 success envelope 残留。
  - 本轮所有业务列表接口仅使用 offset 模式；cursor 模式（`ok_cursor`）不接入任何业务接口，仅在响应工厂中保留签名与契约测试。
  *需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R2.AC6, R8.AC3, R9.AC2, R9.AC3, R9.AC4, R9.AC6*
- 1. 迁移异步、批量与动作结果接口
  - 识别导入、批量删除、状态切换、同步、运行、清理等接口，区分“资源返回”“动作结果返回”“异步受理返回”三类模式。
  - 对异步受理接口落地 `202 Accepted + Location + job result`，明确前端可轮询/跳转的任务定位信息。
  - 对批量与部分成功接口统一返回 `results[] + summary`，确保每一项都有成功/失败状态与失败原因。
  - 对本质为业务动作结果而非资源对象的接口，定义专属结果对象，不为统一而回退到全局 success envelope 或自由文本。
  *需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R6.AC2, R6.AC3, R8.AC4, R8.AC5, R9.AC6*
- 1. 更新代码生成器与脚手架模板，阻断旧结构回流
  - 改造 `ruoyi-fastapi-backend/module_generator/templates/python/controller.py.jinja2`，默认生成 `ok_page / ok_resource / created_resource / no_content` 等新响应模式（字典/枚举类模板走 `ok_collection`）。
  - 改造 `ruoyi-fastapi-backend/module_generator/templates/vue/index.vue.jinja2` 与 `vue/v3/index.vue.jinja2`，让列表默认消费 `items`，API wrapper 默认声明 `feedback: { mode: 'auto', key: '<module>.<resource>.<action>' }`，写操作不再生成 `msgSuccess('新增成功')` / `msgSuccess('修改成功')`。
  - 同步检查现有生成器控制器实现，确保生成链路不再注入 `ResponseUtil.success(msg=...)`、`ResponseUtil.ok_list(...)`、`response.rows`、`pageNum/pageSize` 等旧模式。
  - 为模板输出补齐最小回归测试或快照校验，确保新代码默认符合本轮契约。
  *需求追溯: R2.AC2, R2.AC3, R2.AC4, R5.AC2, R8.AC2, R8.AC3, R9.AC3*
- 1. 重构前端 HTTP 客户端与统一反馈层
  - 改造 `ruoyi-fastapi-frontend/src/utils/http.ts`，移除对 `payload.message|payload.msg` 的默认成功文案依赖，修复 `successCodes: [200]` 仅支持单一状态码的问题，并显式支持 `201/202/204`。
  - 改造 `ruoyi-fastapi-frontend/src/utils/request.ts`，新增 `feedback.mode`、`feedback.key`、`successContext`、`validationTarget` 等统一反馈配置项。
  - 新增统一反馈模块（如 `src/utils/feedback/presenter.ts`、`registry.ts`、`types.ts`），按 `2xx/202/422/429/5xx` 语义映射 toast、notification、banner、字段错误。
  - 将错误反馈统一改为读取 RFC 9457 Problem Details 与响应头中的 `X-Request-Id`、`X-Trace-Id`、`Retry-After`、`RateLimit-`*，查询成功默认不弹绿色 toast。
  *需求追溯: R5.AC1, R5.AC2, R5.AC4, R6.AC1, R6.AC2, R6.AC4, R6.AC5, R6.AC6, R7.AC1, R7.AC4, R7.AC5*
- 1. 迁移 API wrapper、页面反馈与列表消费方
  - 逐步改造 `src/api/*`*，将默认反馈 ownership 下沉到 API wrapper，通过 `feedback.key` 统一声明 CRUD 成功反馈与 partial success 展示策略；非 CRUD 请求（下载、上传、轮询探活等）显式声明 `feedback: { mode: 'silent' }`。
  - 批量清理 `src/views/**` 与 `src/components/**` 中针对服务端 CRUD 结果的 `ElMessage.*`、`ElNotification.*`、`$modal.msg*` 调用，保留仅属于本地交互的消息提示。
  - 迁移所有列表页、表格封装和分页入参，统一消费 `items/total/page/pageSize`；grid 适配层按字段自动识别纯集合 / offset 分页 / cursor 分页三种模式，清理 `response.rows` 与 `pageNum/pageSize` 直读。
  - 新建 `src/utils/feedback/registry.ts` 作为全量 feedback key 单一真源，key 命名统一为 `{module}.{resource}.{action}`；实现启动校验：dev 下缺失 key 抛错，prod 下降级为 `'操作成功'` 并 `console.warn(key)`。
  - 完成角色、用户、字典、菜单、设备、监控、项目等现有消费方迁移，确保仓库内调用方全部切到新契约，不再依赖旧 success message 或旧错误形状。
  *需求追溯: R2.AC2, R5.AC2, R5.AC3, R5.AC5, R6.AC1, R6.AC3, R6.AC6, R9.AC2, R9.AC3*
- 1. 完善前后端测试矩阵与契约回归
  - 更新 `ruoyi-fastapi-backend/tests/unit/test_response_util.py`、`tests/integration/test_error_handling_rfc7807.py`、`tests/unit/middlewares/test_idempotency_middleware.py`、`tests/unit/middlewares/test_rate_limit_middleware.py`。
  - 新增列表/详情/创建/更新/删除/异步/批量接口的后端契约测试，断言纯集合 `{items}`、offset 分页 `{items,total,page,pageSize}`、cursor 分页 `{items,pageSize,nextCursor}`（签名级测试）、`201 + 绝对 Location`、`204`、`202 + 绝对 Location`、`results[] + summary` 以及 `results[i].error` 仅含 `errorCode/title/detail` 三字段。
  - 为前端 `src/utils/http.ts`、统一反馈层、grid 适配器、feedback registry 启动校验补齐 Vitest，覆盖 `201/202/204/422/429`、字段级校验映射、部分成功展示、header 读取、纯集合/offset/cursor 三种分页识别、dev 下缺失 key 抛错。
  - 在测试中明确验证 success body 不再包含 `message/requestId`，Problem Details 不再包含非白名单扩展字段，`type` 为绝对 URL 或 `about:blank`，`errors[].code` 对齐 pydantic v2 原生 `type`。
  *需求追溯: R2.AC3, R2.AC4, R2.AC5, R3.AC1, R3.AC2, R3.AC3, R3.AC5, R4.AC1, R4.AC4, R7.AC3, R7.AC4, R8.AC4, R8.AC5*
- 1. 落地静态治理、CI 门禁与发布说明
  - 为前端新增 ESLint 规则或扫描脚本，阻断页面层对服务端 CRUD 成功/失败直接调用 `ElMessage.`*、`ElNotification.*`、`$modal.msg*`，阻断 API wrapper 缺少 `feedback` 选项声明。
  - 为后端新增扫描和检查，阻断 `ResponseUtil.failure/error/unauthorized/forbidden`、`ResponseUtil.success(`、`ResponseUtil.ok_list(`、`rows` 主字段、Problem Details `type` 以 `/problems/` 开头的相对路径、旧 `{code,msg,success}` 错误出口与自由文本 success contract 回流。
  - 将扫描脚本、前后端测试与契约测试接入 CI，确保不满足新契约的提交无法合入。
  - 完成规格、实现说明和发布说明，明确受影响范围、迁移完成条件与合入前验收项，作为本次硬切上线依据；在发布说明中明确"本次硬切假设当前业务 JSON HTTP API 仅被仓库内前端消费，不支持外部调用方"。
  *需求追溯: R8.AC1, R8.AC2, R8.AC3, R9.AC1, R9.AC2, R9.AC5*
- 1. 硬化 command/upload 边界，补齐 review 漏网点
  - 新增 command result payload helper，统一从 service result 中提取业务 `result`，缺失 `result` 时返回空对象，并过滤 `message/msg`，阻断 service 层成功文案回流到 `CommandResult.data`。
  - 将 system 模块 command handlers 从 `data={'message': ...}` / 直接读取 `.result` 的散点写法收敛到统一 helper，避免无业务结果的写操作因缺少 `.result` 崩溃。
  - 将 `/system/user/importData` 明确返回 `ResponseUtil.batch_result(results=..., summary=...)`，用户导入 service 产出逐行 `results[]` 与 `summary`，部分失败保留逐项错误原因。
  - 将 `UserImportDialog.vue` 改为消费结构化 `results/summary`，不再读取 `response.msg`；失败明细展示前进行 HTML escape。
  - 扩展后端治理脚本扫描 `data={'message': ...}` 与 `ResponseUtil.ok_resource(*_result.data)`，扩展前端治理脚本扫描 `response.msg/res.msg`。
  - 补充 `/system/user/importData` controller 级契约测试，断言成功 body 不含 `message/msg`，批量失败项 `error` 仅含 `errorCode/title/detail`。
  *需求追溯: R3.AC2, R3.AC3, R5.AC2, R6.AC3, R8.AC4, R8.AC6, R8.AC7, R8.AC8, R9.AC3*
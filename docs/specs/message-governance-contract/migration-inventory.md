# 平台消息治理与 API 反馈契约 迁移清单

本清单对应 `tasks.md` Task 1 的盘点产出，覆盖本轮硬切范围内所有需要迁移的后端/前端/模板/测试文件。每条目标注用法量级（基于当前仓库状态扫描）与迁移动作。迁移完成后将每条前面的 `[ ]` 勾上。

扫描基线日期：2026-04-23。
回写状态：2026-04-27 已按实现、治理扫描、前端 type-check 与定向回归完成全量回写；本清单已收口到 100%，不存在未勾选项。

## 0. 收口状态（2026-04-23）

- [x] 业务 JSON controller 的 create/update/import/clone 已统一到“返回资源 / 返回动作结果 / 返回批量结果 / 返回 accepted job”四类成功契约，创建类缺失资源标识时改为显式契约失败，不再静默回退 `204 No Content`。
- [x] `module_generator` 运行时 controller 与 Python 模板已完成治理迁移；代码生成相关动作端点返回结构化结果，分页参数对外统一为 `page` / `pageSize`。
- [x] 前端 blind spot 已补齐：`tool/gen`、`Monitor` 组件与治理扫描目录已覆盖，仓库内目标业务页不再消费旧 `rows/pageNum` 契约。
- [x] 真实 controller 级契约回归已覆盖 `project`、`notice`、`gen`、`job`、`protocol`，并结合前后端治理扫描作为当前完成态门禁。
- [x] review 漏网点已收口：`/system/user/importData` 已纳入真实 controller 级批量契约回归；system command handlers 通过统一 helper 过滤 `message/msg`，controller 不再直接透传 command result data。
- [x] `demo-offline` / `mocks` 的 HTTP 边界与内部分页 helper 已统一到新契约：列表对内对外均使用 `items/total/page/pageSize`，错误返回 Problem Details，不再保留 `rows/pageNum` 兼容层。
- [x] 前端业务路径已删除 `$modal.msg* / $modal.notify*` 依赖；`device/protocol/project` 导入与 `simulation` 事件 CRUD 默认反馈已下沉到 wrapper `feedback` + registry，`src/plugins/modal.js` 仅保留对话框/遮罩能力。
- [x] 后端 `modules/system/infrastructure/log_repository.py` 的 cursor helper 已统一为 `items/nextCursor/pageSize`，并纳入 backend governance gate；service 层残留的 `page_size` 旧 cache key 也已收口。
- [x] 本次实际验收结果：`node scripts/check_message_governance_frontend.mjs` 通过，`python3 scripts/check_message_governance_backend.py` 通过，`cd ruoyi-fastapi-frontend && yarn type-check` 通过，`yarn test:run src/utils/http.test.ts src/utils/feedback/presenter.test.ts src/utils/feedback/registry.test.ts` 为 `16 passed`，`cd ruoyi-fastapi-backend && ./.venv/bin/python -m pytest tests/integration/test_success_contract_responses.py -q -n0 --no-cov` 为 `14 passed`，`cd ruoyi-fastapi-backend && ./.venv/bin/python -m pytest modules/system/tests/test_*_write_commands.py -q -n0 --no-cov` 为 `35 passed`。

说明：下方 1-16 节保留为扫描基线和审计快照；当前完成态以本文件勾选结果、治理脚本和验收命令为准。

## 图例

- **用法**：基于 `rg` 扫描的"匹配次数"，迁移完成后该模式应降为 0。
- **动作**：`REWRITE` 整体重写 / `EDIT` 局部替换 / `DELETE` 删除 / `TEMPLATE` 模板改造 / `TEST` 配套测试。
- **优先级**：P0 基础设施（未完成则阻断其他工作）/ P1 业务主链路 / P2 辅助与边缘。

---

## 1. 总览统计

| 维度 | 数量 | 扫描模式 |
| --- | --- | --- |
| 后端受影响控制器文件 | 29 | `ResponseUtil.(success\|failure\|error\|unauthorized\|forbidden\|streaming)` |
| 后端 `ResponseUtil.*` 总调用 | 230+ | 同上 |
| 后端分页/VO 模型文件 | 30+ | `PageResponseModel\|page_num\|page_size` |
| 前端 API wrapper 文件 | 33 | `src/api/**/*.{ts,js}` |
| 前端页面 (views) 文件 | 29+ | `src/views/**/index.vue` |
| 前端页面调 `ElMessage/$modal/ElNotification` | 200+ | 见前端页面小节 |
| 前端文件使用 `rows` / `.rows` | 50+ | `\.rows\|'rows'\|"rows"` |
| 前端文件使用 `pageNum` | 40+ | `pageNum` |

---

## 2. 后端 P0 基础设施

### 2.1 响应工厂与契约
- [x] `ruoyi-fastapi-backend/utils/response_util.py` — REWRITE — 拆分为 `ok_resource/ok_collection/ok_page/ok_cursor/created_resource/accepted_job/batch_result/no_content/problem_details/validation_problem`；删除 `success/failure/error/unauthorized/forbidden/streaming` 旧出口与 `rows/dict_content/model_content` 拼装入口。
- [x] `ruoyi-fastapi-backend/common/http_contracts.py` — CREATE — 新建，定义 `CollectionResult[T]`、`PagedResult[T]`、`CursorResult[T]`、`BatchResult`、`BatchItemResult`、`BatchItemError`、`AcceptedJobResult`、`ProblemDetails`、`ValidationErrorItem`。
- [x] `ruoyi-fastapi-backend/config/env.py` — EDIT — 新增 `PROBLEM_TYPE_BASE_URL` 配置项（dev 默认 `http://localhost/problems`）。

### 2.2 异常转换与中间件
- [x] `ruoyi-fastapi-backend/exceptions/handle.py` — REWRITE — 统一异常 → `problem_details()` 单出口；`AppException`/`RequestValidationError`/`StarletteHTTPException`/通用异常全覆盖；`errors[].code` 透传 pydantic v2 原生 `type`；未映射 slug 的 `type` 回退 `about:blank`。
- [x] `ruoyi-fastapi-backend/middlewares/handle.py` — EDIT — 统一响应头写入器写入 `X-Request-Id` / `X-Trace-Id`，接入 `traceparent` 解析；成功响应也必带 `X-Request-Id`。
- [x] `ruoyi-fastapi-backend/middlewares/idempotency_middleware.py` — EDIT — 入站头从 `X-Idempotency-Key` 切换为标准 `Idempotency-Key`；冲突返回 RFC 9457；补全文档化的 24h 窗口与并发策略。
- [x] `ruoyi-fastapi-backend/middlewares/rate_limit_middleware.py` — EDIT — 响应头改为 `RateLimit-Limit/Remaining/Reset` + `Retry-After`；Problem Details body 去除 `data` 扩展。
- [x] `ruoyi-fastapi-backend/module_admin/annotation/log_annotation.py` — EDIT — 移除装饰器内直接构造 `ResponseUtil.failure/error` 响应，改为抛出标准 `AppException` 子类。
- [x] CORS 配置（位于 `server.py` 或 `config/*`） — EDIT — `Access-Control-Expose-Headers` 追加 `X-Request-Id`、`X-Trace-Id`、`Location`、`Retry-After`、`RateLimit-Limit`、`RateLimit-Remaining`、`RateLimit-Reset`。

---

## 3. 后端 P1 控制器迁移（按模块分组）

每条列出文件路径与 `ResponseUtil.*` 调用次数。迁移动作统一：替换为新工厂方法 + 改 `Location` 为绝对 URL + 删除 success message 参数。

### 3.1 modules/system/api（新架构控制器）
- [x] `server_controller.py` (1) — EDIT
- [x] `notice_controller.py` (5) — EDIT
- [x] `resilience_controller.py` (7) — EDIT
- [x] `config_controller.py` (9) — EDIT
- [x] `common_controller.py` (4) — EDIT（含文件下载/上传，非 CRUD 接口保留原状，仅清理旧错误出口）
- [x] `dict_controller.py` (15) — EDIT（字典类型/字典数据含纯集合接口，使用 `ok_collection`）
- [x] `post_controller.py` (6) — EDIT
- [x] `cache_controller.py` (7) — EDIT
- [x] `audit_controller.py` (3) — EDIT
- [x] `dev_menu_sync_controller.py` (4) — EDIT
- [x] `user_controller.py` (17) — EDIT（含导入导出，注意异步受理与批量 `results[]` 处理）
- [x] `event_controller.py` (4) — EDIT
- [x] `role_controller.py` (14) — EDIT（含 `changeStatus` 动作、数据权限分配）
- [x] `menu_controller.py` (5) — EDIT（菜单树为纯集合，用 `ok_collection`）
- [x] `online_controller.py` (2) — EDIT
- [x] `log_controller.py` (9) — EDIT（操作日志、登录日志）
- [x] `dept_controller.py` (8) — EDIT（部门树为纯集合）

### 3.2 modules/identity/api
- [x] `captcha_controller.py` (1) — EDIT
- [x] `security_controller.py` (10) — EDIT
- [x] `login_controller.py` (6) — EDIT

### 3.3 modules/project/api
- [x] `project_version_controller.py` (8) — EDIT
- [x] `project_controller.py` (9) — EDIT

### 3.4 modules/scheduler/api
- [x] `job_controller.py` (12) — EDIT（含调度任务的异步触发、立即执行等动作型接口）

### 3.5 module_admin/controller（旧架构控制器）
- [x] `simulation_controller.py` (28) — EDIT（用法最多，含仿真启动/停止/注入等动作型接口，需区分同步完成与异步受理）
- [x] `device_controller.py` (10) — EDIT
- [x] `device_category_controller.py` (7) — EDIT
- [x] `protocol_controller.py` (11) — EDIT

### 3.6 module_generator/controller
- [x] `gen_controller.py` (11) — EDIT（代码生成本身是动作型，返回 zip 流的下载接口保留非 CRUD 形态）

---

## 4. 后端 P1 分页模型与 service 层

需要把查询参数 `page_num` 对外字段改为 `page`，响应 VO 结构同步到新契约。内部模型可短期保留 alias，对外只暴露 `page/pageSize`。

### 4.1 VO / 分页 schema
- [x] `utils/page_util.py` — EDIT — 修改 `PageResponseModel` 与 `get_page_obj` 输出，产出 `{items,total,page,pageSize}` 形态（保留旧字段 alias 仅供内部迁移，标注 `deprecated`）。
- [x] `module_admin/entity/vo/common_vo.py` — EDIT — `CrudResponseModel` 评估是否删除（前端不再消费其 `message`）。
- [x] `module_admin/entity/vo/role_vo.py` — EDIT — 分页请求模型对外字段改名。
- [x] `module_admin/entity/vo/post_vo.py` — EDIT — 同上。
- [x] `module_admin/entity/vo/config_vo.py` — EDIT — 同上。
- [x] `module_admin/entity/vo/notice_vo.py` — EDIT — 同上。
- [x] `module_admin/entity/vo/log_vo.py` — EDIT — 同上。
- [x] `module_admin/entity/vo/protocol_vo.py` — EDIT — 同上。
- [x] `module_admin/entity/vo/device_category_vo.py` — EDIT — 同上。
- [x] `module_admin/entity/vo/project_version_vo.py` — EDIT — 同上。
- [x] `module_generator/entity/vo/gen_vo.py` — EDIT — 同上。

### 4.2 service / repository 层（仅字段名透传调整）
- [x] `module_admin/repository/base_repository.py` — EDIT — 分页查询字段名透传。
- [x] `module_admin/repository/device_repository.py` — EDIT
- [x] `module_admin/repository/protocol_repository.py` — EDIT
- [x] `module_generator/repository/gen_repository.py` — EDIT
- [x] `module_admin/service/protocol_service.py` — EDIT
- [x] `module_admin/service/device_category_service.py` — EDIT
- [x] `module_generator/service/gen_service.py` — EDIT
- [x] `modules/system/application/services/*.py` — EDIT — 批量检查 `user_service/role_service/dept_service/dict_*/config_service/post_service/audit_log_service/cache_service`（已使用新架构，字段改名即可）。
- [x] `modules/system/application/handlers/query/*.py` — EDIT — 批量检查 `user_query_handlers/dict_query_handlers/config_query_handlers/post_query_handlers`。
- [x] `modules/system/application/read_models/*.py` — EDIT — `user_read_models/role_read_models/dict_read_models/config_read_models`。
- [x] `modules/system/infrastructure/*.py` — EDIT — `dict_repository/config_repository`。
- [x] `modules/project/infrastructure/project_repository.py` — EDIT
- [x] `modules/scheduler/application/job_service.py` — EDIT
- [x] `modules/scheduler/application/job_log_service.py` — EDIT

---

## 5. 后端 P1 生成器模板

- [x] `module_generator/templates/python/controller.py.jinja2` — TEMPLATE — 移除 `ResponseUtil.success(msg=...)`；默认生成 `ok_page/ok_resource/created_resource/no_content`，字典类使用 `ok_collection`。
- [x] `module_generator/templates/vue/index.vue.jinja2` — TEMPLATE — 列表默认消费 `items`；API wrapper 声明 `feedback: { mode: 'auto', key: '...' }`；删除 `msgSuccess('新增成功'/'修改成功')`。
- [x] `module_generator/templates/vue/v3/index.vue.jinja2` — TEMPLATE — 同上；同步清理 `rows` / `pageNum` 字段名。

---

## 6. 后端 P1 测试

### 6.1 更新现有测试
- [x] `tests/unit/test_response_util.py` (5 处 `ResponseUtil.*` 断言) — TEST — 断言不再出现 `message/requestId` 在 body；覆盖新工厂方法全量；断言 `type` 为绝对 URL / `about:blank`；断言 `Location` 为绝对 URL。
- [x] `tests/unit/utils/test_response_naming.py` (1) — TEST — 同步新契约字段命名。
- [x] `tests/integration/test_error_handling_rfc7807.py` — TEST — 改名或内容对齐 RFC 9457 术语；断言扩展字段白名单；断言 `X-Request-Id` 与 body 一致。
- [x] `tests/integration/test_error_handling_critical.py` — TEST — 同步 Problem Details 扩展字段白名单。
- [x] `tests/unit/middlewares/test_idempotency_middleware.py` — TEST — 头名切换为 `Idempotency-Key`；补 24h 窗口、指纹一致性、并发 409 冲突用例。
- [x] `tests/unit/middlewares/test_rate_limit_middleware.py` — TEST — 头名切换为 `RateLimit-*`；断言 Problem Details body 不再出现 `data`。
- [x] `modules/system/tests/test_*_read_queries.py` — TEST — `test_role_read_queries/test_user_read_queries/test_config_read_queries/test_dict_read_queries/test_notice_read_queries/test_post_read_queries`，断言分页字段为 `items/total/page/pageSize`。
- [x] `tests/unit/repositories/test_base_repository.py` / `test_query_builder.py` — TEST — 分页字段同步。
- [x] `tests/integration/test_capability_runtime_gate.py` — TEST — 新 contract 适配。

### 6.2 新增契约测试
- [x] `tests/integration/test_success_contract_responses.py` — CREATE — 以真实业务 router + fake service/container 覆盖 `201/200/批量结果/动作结果/绝对 Location` 等契约回归（项目、公告、生成器、任务、协议导入、用户导入）。
- [x] `tests/integration/test_success_contract_collection.py` — CREATE — 纯集合接口只返 `{items}`。
- [x] `tests/integration/test_success_contract_page.py` — CREATE — offset 分页完整字段断言。
- [x] `tests/integration/test_success_contract_cursor.py` — CREATE — cursor 签名级测试（本轮无业务接口，造桩测试）。
- [x] `tests/integration/test_success_contract_created.py` — CREATE — `201 + 绝对 Location + 完整资源`。
- [x] `tests/integration/test_success_contract_no_content.py` — CREATE — `204`。
- [x] `tests/integration/test_success_contract_accepted.py` — CREATE — `202 + 绝对 Location + job`。
- [x] `tests/integration/test_success_contract_batch.py` — CREATE — `200 + results[] + summary`；`results[i].error` 仅三字段。

---

## 7. 前端 P0 基础设施

- [x] `src/utils/http.ts` — REWRITE — `successResolver` 不再读 `payload.message|msg`；`successCodes` 覆盖全部 2xx；`afterResponseTransform` 不再对 mutation 自动弹 toast；`gridListPlugin.listField = 'items'`；`attachPager` 支持纯集合/offset/cursor 三模式；`204` 显式分支；错误解析只读 RFC 9457；头部读取 `X-Request-Id/X-Trace-Id/Retry-After/RateLimit-*` 并挂到 response。
- [x] `src/utils/request.ts` — EDIT — 新增 `feedback: FeedbackOptions` 请求选项（`mode/key/successContext/validationTarget`）；保留 `skipRelogin`；清理旧 `ElMessage` 直接调用。
- [x] `src/utils/feedback/types.ts` — CREATE — 定义 `FeedbackOptions`、`FeedbackMode`、`FeedbackRegistryEntry`、`ProblemDetails`、`ValidationErrorItem` 等类型。
- [x] `src/utils/feedback/presenter.ts` — CREATE — 实现 `2xx/202/204/422/429/5xx` 策略分发；启动校验缺失 key。
- [x] `src/utils/feedback/registry.ts` — CREATE — 单一真源，key 命名 `{module}.{resource}.{action}`；初版覆盖全量 CRUD 接口。
- [x] `src/types/http-contract.ts` — CREATE — 对外暴露 `CollectionResult<T>/PagedResult<T>/CursorResult<T>/BatchResult<T>/BatchItemError/AcceptedJobResult/ProblemDetails/ValidationErrorItem/FeedbackOptions`。
- [x] `src/api/_shared/http-client.ts` — EDIT — 确保透传 `feedback` 选项到 `request.ts`。
- [x] `src/api/_shared/types/common.ts` — EDIT — 移除以 `rows/pageNum` 为主字段的类型定义，替换为 `items/page/pageSize`。
- [x] `src/api/_shared/index.ts` — EDIT — 统一导出新增类型。
- [x] `src/plugins/modal.js` (7 处 `msg*`) — EDIT — 只保留 `confirm/alert/prompt/loading` 本地交互能力；删除 `msg* / notify*` 废弃消息 API。
- [x] `src/plugins/download.js` (6 处) — EDIT — 保留文件下载能力，但 API wrapper 侧声明 `feedback: { mode: 'silent' }`；错误流读取 Problem Details。
- [x] `src/permission.ts` (1) — EDIT — 移除对旧 `ElMessage` 错误提示的直接依赖。
- [x] `src/main.ts` — EDIT — 初始化 feedback presenter 与 registry；启动校验接入。

---

## 8. 前端 P1 API wrapper 迁移

每个 wrapper 加 `feedback.key`（CRUD 类）或 `feedback.mode: 'silent'`（非 CRUD 类），分页字段从 `pageNum` 改为 `page`，列表解析字段从 `rows` 改为 `items`。

### 8.1 根与通用
- [x] `src/api/login.ts` — EDIT
- [x] `src/api/common.ts` — EDIT
- [x] `src/api/menu.ts` — EDIT（导航菜单树为纯集合）

### 8.2 system
- [x] `src/api/system/user.ts` — EDIT
- [x] `src/api/system/role.ts` — EDIT
- [x] `src/api/system/dept.ts` — EDIT
- [x] `src/api/system/menu.ts` — EDIT
- [x] `src/api/system/post.ts` — EDIT
- [x] `src/api/system/config.ts` — EDIT
- [x] `src/api/system/notice.ts` — EDIT
- [x] `src/api/system/project.ts` — EDIT
- [x] `src/api/system/devMenuSync.ts` — EDIT
- [x] `src/api/system/dict/type.ts` — EDIT
- [x] `src/api/system/dict/data.ts` — EDIT

### 8.3 monitor
- [x] `src/api/monitor/job.ts` — EDIT（含调度任务立即执行等动作型）
- [x] `src/api/monitor/jobLog.ts` — EDIT
- [x] `src/api/monitor/server.ts` — EDIT（查询类，不弹成功 toast）
- [x] `src/api/monitor/cache.ts` — EDIT（清空缓存等动作型）
- [x] `src/api/monitor/operlog.ts` — EDIT
- [x] `src/api/monitor/audit.ts` — EDIT
- [x] `src/api/monitor/logininfor.ts` — EDIT
- [x] `src/api/monitor/online.ts` — EDIT

### 8.4 tool / gen
- [x] `src/api/tool/gen.ts` — EDIT（生成代码为 zip 下载，声明 silent）

### 8.5 业务域 (project/device/protocol/simulation)
- [x] `src/api/project/index.ts` — EDIT
- [x] `src/api/project/project.ts` — EDIT
- [x] `src/api/project/version.ts` — EDIT
- [x] `src/api/project/topology.ts` — EDIT
- [x] `src/api/device/device.ts` — EDIT
- [x] `src/api/device/category.ts` — EDIT
- [x] `src/api/protocol/protocol.ts` — EDIT
- [x] `src/api/simulation/simulation.ts` — EDIT（含仿真启动/停止/注入，动作型为主）

---

## 9. 前端 P1 页面迁移（views）

清理页面内直接弹 `ElMessage.*/$modal.msg*/ElNotification.*`；列表字段从 `rows` 切到 `items`；分页参数从 `pageNum` 切到 `page`。

### 9.1 system
- [x] `src/views/system/user/index.vue` (1 ElMessage + 1 pageNum) — EDIT
- [x] `src/views/system/user/profile/index.vue` — EDIT
- [x] `src/views/system/user/profile/userAvatar.vue` (2) — EDIT
- [x] `src/views/system/user/profile/userInfo.vue` (1) — EDIT
- [x] `src/views/system/user/profile/resetPwd.vue` (1) — EDIT
- [x] `src/views/system/user/authRole.vue` (1) — EDIT
- [x] `src/views/system/user/components/UserFormDialog.vue` (2) — EDIT
- [x] `src/views/system/role/index.vue` (2) — EDIT
- [x] `src/views/system/role/authUser.vue` (2) — EDIT
- [x] `src/views/system/role/selectUser.vue` (2 + 1 pageNum) — EDIT
- [x] `src/views/system/role/components/RoleFormDrawer.vue` (3 + 1 pageNum) — EDIT
- [x] `src/views/system/role/components/RoleDataScopeDrawer.vue` (2) — EDIT
- [x] `src/views/system/dept/index.vue` — EDIT
- [x] `src/views/system/dept/components/DeptList.vue` (1) — EDIT
- [x] `src/views/system/dept/components/DeptDlg.vue` (3) — EDIT
- [x] `src/views/system/menu/index.vue` — EDIT
- [x] `src/views/system/menu/components/MenuList.vue` (2) — EDIT
- [x] `src/views/system/menu/components/MenuDrawer.vue` (3) — EDIT
- [x] `src/views/system/post/index.vue` — EDIT
- [x] `src/views/system/config/index.vue` — EDIT
- [x] `src/views/system/notice/index.vue` — EDIT
- [x] `src/views/system/notice/components/NoticeList.vue` (1) — EDIT
- [x] `src/views/system/notice/components/NoticeDlg.vue` (3) — EDIT
- [x] `src/views/system/dict/index.vue` — EDIT
- [x] `src/views/system/dict/data.vue` (3) — EDIT
- [x] `src/views/system/dict/components/DictList.vue` (2) — EDIT
- [x] `src/views/system/project/index.vue` — EDIT
- [x] `src/views/system/project/components/ProjectList.vue` (3) — EDIT
- [x] `src/views/system/project/components/ProjectDlg.vue` (3 + 1 pageNum) — EDIT

### 9.2 monitor
- [x] `src/views/monitor/server/index.vue` — EDIT
- [x] `src/views/monitor/druid/index.vue` — EDIT
- [x] `src/views/monitor/cache/index.vue` — EDIT
- [x] `src/views/monitor/cache/list.vue` (5 + 1 pageNum) — EDIT
- [x] `src/views/monitor/job/index.vue` (5) — EDIT
- [x] `src/views/monitor/job/log.vue` (2 + 1 pageNum) — EDIT
- [x] `src/views/monitor/logininfor/index.vue` (3) — EDIT
- [x] `src/views/monitor/operlog/index.vue` — EDIT
- [x] `src/views/monitor/audit/index.vue` (2) — EDIT
- [x] `src/views/monitor/online/index.vue` (1 + 1 pageNum) — EDIT

### 9.3 tool
- [x] `src/views/tool/gen/index.vue` (5 + 1 pageNum) — EDIT
- [x] `src/views/tool/gen/importTable.vue` (1) — EDIT
- [x] `src/views/tool/gen/editTable.vue` (1 + 1 pageNum) — EDIT
- [x] `src/views/tool/gen/createTable.vue` (1) — EDIT
- [x] `src/views/tool/gen/basicInfoForm.vue` — EDIT
- [x] `src/views/tool/build/index.vue` (1) — EDIT
- [x] `src/views/tool/swagger/index.vue` — EDIT

### 9.4 project / simulation
- [x] `src/views/project/index.vue` (14 + 1 pageNum) — EDIT
- [x] `src/views/project/topo.vue` (9 + 1 pageNum) — EDIT
- [x] `src/views/project/entry.vue` (1 + 2 pageNum) — EDIT
- [x] `src/views/project/operlog/index.vue` — EDIT
- [x] `src/views/project/components/ProjectFormDialog.vue` (1 + 1 pageNum) — EDIT
- [x] `src/views/project/components/ProjectEditDialog.vue` (3 + 1 pageNum) — EDIT
- [x] `src/views/project/components/ProtocolEditDialog.vue` (1) — EDIT
- [x] `src/views/project/components/ProtocolConfigDrawer.vue` — EDIT
- [x] `src/views/project/components/NodeEditDrawer.vue` (1) — EDIT
- [x] `src/views/project/components/VersionList.vue` (8 + 3 pageNum) — EDIT
- [x] `src/views/project/components/VersionCloneDialog.vue` (1 + 1 pageNum) — EDIT
- [x] `src/views/project/components/VersionExportDialog.vue` (2) — EDIT
- [x] `src/views/project/components/ExportDialog.vue` (2) — EDIT
- [x] `src/views/project/composables/useTopology.js` (5) — EDIT
- [x] `src/views/project/composables/topoExportUtils.ts` — EDIT（git status 显示已修改，一并纳入）
- [x] `src/views/project/simulation/index.vue` (22 + 1 pageNum) — EDIT（用法最多的页面）
- [x] `src/views/project/simulation/backupindex.vue` (11 + 1 pageNum) — DELETE 或 EDIT（若确定废弃则删除）
- [x] `src/views/project/simulation/components/MessageListPanel.vue` (2 + 2 pageNum) — EDIT
- [x] `src/views/project/simulation/components/AlarmPanel.vue` (1) — EDIT
- [x] `src/views/project/simulation/components/DataInjectionPanel.vue` (1) — EDIT
- [x] `src/views/project/simulation/components/SimulationReportDialog.vue` (4 + 2 pageNum) — EDIT
- [x] `src/views/project/simulation/components/ProtocolAnalyzer.vue` (2 pageNum) — EDIT
- [x] `src/views/project/simulation/components/SkeletonLoader.vue` (1 pageNum) — EDIT
- [x] `src/views/project/simulation/composables/useSimulationWebSocket.ts` (4) — EDIT（WebSocket 事件非本轮强制统一，但旧 ElMessage 需清理）
- [x] `src/views/project/simulation/composables/useFaultInjectionUI.ts` (4) — EDIT
- [x] `src/views/project/simulation/composables/useEventTrigger.ts` (2 pageNum) — EDIT
- [x] `src/views/project/simulation/composables/useAlarmManager.ts` (2 pageNum) — EDIT

### 9.5 device / protocol
- [x] `src/views/device/index.vue` (6 + 1 pageNum) — EDIT
- [x] `src/views/device/detail.vue` (6) — EDIT
- [x] `src/views/device/category/index.vue` (1 + 1 pageNum) — EDIT
- [x] `src/views/protocol/index.vue` (11 + 1 pageNum) — EDIT

### 9.6 其他
- [x] `src/views/dashboard/index.vue` — EDIT（若无 CRUD 调用可跳过）
- [x] `src/views/redirect/index.vue` — 不纳入（跳转占位）

---

## 10. 前端 P1 业务/UI 组件

### 10.1 业务组件
- [x] `src/components/business/Device/NodeEditDrawer.vue` (1 + 1 pageNum) — EDIT
- [x] `src/components/business/Device/MessageConfigTab.vue` (2) — EDIT
- [x] `src/components/business/Device/ExportDialog.vue` (2) — EDIT
- [x] `src/components/business/Device/DeviceCloneDialog.vue` (1) — EDIT
- [x] `src/components/business/Device/DeviceClazzDialog.vue` (3 + 1 pageNum) — EDIT
- [x] `src/components/business/Device/DeviceNameDialog.vue` (1 pageNum) — EDIT
- [x] `src/components/business/Device/CategoryFormDialog.vue` (1 pageNum) — EDIT
- [x] `src/components/business/Device/PortEditDialog.vue` (1 pageNum) — EDIT
- [x] `src/components/business/Device/selector/CategorySelector.vue` (1 pageNum) — EDIT
- [x] `src/components/business/Protocol/ProtocolFormDrawer.vue` (1 pageNum) — EDIT
- [x] `src/components/business/Protocol/ImportFileDialog.vue` (7) — EDIT（含文件上传，声明 silent）
- [x] `src/components/business/Protocol/selector/ProtocolTemplateSelector.vue` (1 pageNum) — EDIT
- [x] `src/components/business/Protocol/templates/CANProtocolTemplate.vue` (4 + 2 pageNum) — EDIT
- [x] `src/components/business/Protocol/templates/RS422ProtocolTemplate.vue` (4 + 2 pageNum) — EDIT
- [x] `src/components/business/Protocol/templates/EthernetProtocolTemplate.vue` (6 + 2 pageNum) — EDIT
- [x] `src/components/business/Protocol/templates/Protocol1553BTemplate.vue` (4 + 2 pageNum) — EDIT
- [x] `src/components/business/Protocol/templates/fieldUtils.ts` (2 pageNum) — EDIT
- [x] `src/components/business/Dag/index.vue` (2) — EDIT
- [x] `src/components/business/Dag/components/DagMatrixDialog.vue` (3) — EDIT
- [x] `src/components/business/Dag/components/DagMatrixView.vue` (3 + 1 pageNum) — EDIT
- [x] `src/components/business/Dag/components/DagMatrixViewSimple.vue` (3 + 1 pageNum) — EDIT
- [x] `src/components/business/Monitor/OperlogGrid.vue` (2) — EDIT

### 10.2 UI 基础组件（本轮仅清理错误出口）
- [x] `src/components/ui/RichEditor/src/Editor.vue` (3) — EDIT
- [x] `src/components/ui/Editor/index.vue` (3) — EDIT
- [x] `src/components/ui/ImageUpload/index.vue` (4) — EDIT（含上传，声明 silent）
- [x] `src/components/ui/FileUpload/index.vue` (4) — EDIT（同上）
- [x] `src/components/ui/VxeTableValidation/index.ts` (3) — EDIT
- [x] `src/components/ui/VxeTableValidation/useVxeTableValidation.ts` (1) — EDIT
- [x] `src/components/ui/VxeTableValidation/README.md` (3) — EDIT（文档同步新契约示例）
- [x] `src/components/ui/ContentDetailWrap/index.vue` (1 pageNum) — EDIT

---

## 11. 前端 P1 utils 与 generator

- [x] `src/utils/generator/js.ts` (2) — EDIT — 生成器内嵌代码不再注入 `ElMessage.success`。

---

## 12. 前端 P1 测试

### 12.1 更新现有测试
- [x] `tests/unit/api/role.test.ts` (3 pageNum) — TEST — 分页字段改名，并补齐 wrapper `feedback` 断言。
- [x] `tests/unit/api/dict.test.ts` (2 pageNum) — TEST — 同上。
- [x] `tests/unit/api/config.test.ts` (1 pageNum) — TEST — 同上。
- [x] `src/api/login.test.ts` — TEST — 登录请求保持 `silent`，不再依赖旧 success envelope。
- [x] `src/demo/services/system-admin.test.ts` (4 rows + 3 pageNum) — TEST — demo service 内部分页已切到 `items/page`，HTTP 边界与内部 helper 均不再保留旧字段兼容。
- [x] `src/demo/services/project.test.ts` (2 rows) — TEST — 同上。
- [x] `src/demo/handlers/project.test.ts` (1 rows) — TEST — handler 对外成功契约已切到资源 / 分页对象。
- [x] `src/demo/handlers/http.test.ts` (3 rows) — TEST — catch-all 错误输出已切到 Problem Details。

### 12.2 新增测试
- [x] `src/utils/http.test.ts` — CREATE — 覆盖 `2xx/201/202/204/422/429/5xx` 成功/错误分支、header 提取、不再消费 `payload.message`。
- [x] `src/utils/feedback/presenter.test.ts` — CREATE — `auto/manual/silent` 策略、partial success 展示、422 字段映射。
- [x] `src/utils/feedback/registry.test.ts` — CREATE — 启动校验 dev 抛错、prod 降级 + warn。
- [x] `tests/unit/utils/feedback/gridAdapter.test.ts` — CREATE — 三模式识别已并入 `src/utils/http.test.ts` 的 pager 断言覆盖。

### 12.3 demo / mocks 同步
- [x] `src/demo/handlers/utils.ts` — EDIT — 在 demo HTTP 边界统一输出资源/集合/分页对象，移除 `rows/pageNum` 旧字段映射，错误统一输出 Problem Details。
- [x] `src/demo/handlers/project.ts` / `src/demo/handlers/http.ts` / `src/demo/handlers/simulation.ts` — TEST + VERIFY — 已通过 handler 回归验证对外 success/error 契约，不再依赖旧 envelope。
- [x] `src/mocks/utils/response.ts` — EDIT — mock 成功响应直接输出资源/集合/分页对象，错误输出 Problem Details。
- [x] `src/mocks/handlers/user.ts` / `src/mocks/handlers/monitor.ts` — EDIT — 列表与登录/在线用户等 mock 输出切到新契约并支持 `page` / `pageSize`。
- [x] `src/demo/services/system-admin.ts` / `src/demo/services/project.ts` / `src/demo/repositories/base.ts` — INTERNAL — 内部 helper 已硬切到 `items/page/pageSize`，不再保留 `rows/pageNum` 兼容字段。

---

## 13. P2 CI 与治理

- [x] 等效治理脚本已落地：前端使用 `scripts/check_message_governance_frontend.mjs`，后端使用 `scripts/check_message_governance_backend.py`。
- [x] 前端治理脚本已显式阻断 `$modal.msg* / $modal.notify*` 回流，并继续阻断旧 `rows/pageNum` 契约与缺失 `feedback` 的 mutation wrapper。
- [x] 后端治理脚本已覆盖 service 残留的 `.page_num/.rows` 读取，并将 `modules/system/infrastructure/log_repository.py` 的旧 `next_cursor/page_size` cursor 输出纳入扫描。
- [x] `.github/workflows/ci.yml` 已挂接前后端治理扫描、前端测试与后端测试。
- [x] 代码生成模板与业务回归已纳入 CI 可执行命令集合，作为当前 hard cut 门禁的一部分。

---

## 14. 排除清单（本轮不纳入硬切）

以下链路保留现状，不强制套用新成功响应结构：

- [x] `health` / `metrics` / `docs` 相关端点（如 `/actuator/*`、`/docs`、`/openapi.json`）— 协议型。
- [x] 二进制下载：`common_controller.py` 的文件下载、`gen_controller.py` 的 zip 下载、`project_version_controller.py` 的导出 — 响应流保留。
- [x] 前端文件上传：`ImageUpload/FileUpload/ImportFileDialog` 响应体结构保留原样，仅清理旧错误出口。
- [x] WebSocket / SSE：`src/views/project/simulation/composables/useSimulationWebSocket.ts` 的实时事件不走 HTTP 反馈层，仅清理 `ElMessage` 回流。
- [x] `src/views/redirect/index.vue` — 仅做路由跳转。

---

## 15. 特殊场景登记

以下接口在迁移时需要额外决策（同步/异步/部分成功），在 Task 6 中展开处理：

| 接口 | 所在文件 | 场景 | 目标模式 |
| --- | --- | --- | --- |
| 用户导入 | `modules/system/api/user_controller.py` | 批量 + 异步 | `202 + Location` 或 `200 + results[] + summary`（视行数） |
| 用户导出 | 同上 | 文件下载 | 保留流响应，wrapper `silent` |
| 角色批量删除 | `modules/system/api/role_controller.py` | 批量 | `200 + results[] + summary` |
| 角色状态切换 | 同上 | 单资源动作 | `200 + 完整资源` |
| 字典刷新缓存 | `modules/system/api/dict_controller.py` | 动作型 | `200 + 动作结果对象` 或 `204` |
| 缓存清空 | `modules/system/api/cache_controller.py` | 动作型 | `204` |
| 调度任务立即执行 | `modules/scheduler/api/job_controller.py` | 异步受理 | `202 + Location` |
| 代码生成 zip 下载 | `module_generator/controller/gen_controller.py` | 文件下载 | 保留流响应 |
| 项目版本导出 | `modules/project/api/project_version_controller.py` | 文件下载 / 异步 | 同步流 or `202 + Location` |
| 仿真启动/停止/注入 | `module_admin/controller/simulation_controller.py` | 动作型 + 实时事件 | `202 + Location`（启动/停止），`200 + 动作结果`（注入） |
| 协议模板导入 | `components/business/Protocol/ImportFileDialog.vue` | 文件上传 | wrapper `silent`；后端返回 `200 + results[]` |

---

## 16. 合入前验收

全部条目勾选后，追加以下最终验收：

- [x] 后端治理扫描通过：`python3 scripts/check_message_governance_backend.py`。
- [x] 前端治理扫描通过：`node scripts/check_message_governance_frontend.mjs`。
- [x] 后端定向契约回归通过：`cd ruoyi-fastapi-backend && ./.venv/bin/python -m pytest tests/unit/services/test_project_service.py tests/unit/services/test_project_version_service.py tests/integration/test_success_contract_responses.py -q`，结果 `23 passed`。
- [x] 前端 type-check 通过：`cd ruoyi-fastapi-frontend && yarn type-check`。
- [x] 前端 feedback / HTTP 回归通过：`cd ruoyi-fastapi-frontend && yarn test:run src/utils/http.test.ts src/utils/feedback/presenter.test.ts src/utils/feedback/registry.test.ts`，结果 `16 passed`。
- [x] 当前仓库内仍允许保留的直接消息调用仅限本地交互、上传下载、WebSocket 等非服务端 CRUD 默认反馈；`pageNum/rows` 旧分页契约已被治理脚本阻断，不再作为业务 JSON HTTP contract 暴露。

# Backend Architecture P0 Acceptance Review (R1-R15)

## 评估信息

- 评估日期：2026-02-11
- 评估范围：`docs/specs/backend-architecture-p0-foundation/requirements.md`
- 评估方法：
  - 代码静态核查（service/controller/middleware/repository/CI）
  - 目标回归测试执行（见“测试执行记录”）

## 总体结论

- 结论：**部分通过（可进入持续收敛阶段，不建议定义为“全部完成”）**
- 要点：
  - API 安全与观测主干能力（R8-R11、R13）已可用，测试覆盖较完整。
  - Repository-only 已收敛，依赖注入与薄控制器（R3-R5）一致性较前一轮明显提升，但仍未全模块统一。
  - CI 门禁以 GitLab 为准，迁移漂移与架构回归已纳入 GitLab pipeline。

## R1-R15 逐条评估

| Requirement | 状态 | 证据 | 说明 |
| --- | --- | --- | --- |
| R1 新增数据访问只走 repository，不新增 DAO | 通过 | `ruoyi-fastapi-backend/scripts/check_no_dao_imports.py`；`dao-import-check` in `.gitlab-ci.yml` | DAO 退役检查脚本可执行且通过。 |
| R2 现有 service 持久化访问只走 repository | 通过 | 已整改：`module_admin/service/project_service.py`、`module_admin/service/protocol_service.py`、`module_admin/service/common_service.py`、`module_admin/service/project_version_service.py`、`module_admin/service/device_service.py`、`module_admin/service/device_category_service.py`、`module_admin/service/job_log_service.py`；规则扫描：`rg ... module_admin/service` 无命中 | service 层已清零直连 `query_db/db` 持久化调用。 |
| R3 service 依赖走构造注入 + FastAPI provider | 部分通过 | 正向样例：`module_admin/service/dict_service.py:38` + `module_admin/controller/dict_controller.py`；新增：`module_admin/service/project_service.py` + `get_project_service`、`module_admin/service/protocol_service.py` + `get_protocol_service`、`module_admin/service/project_topology_service.py` + `get_project_topology_service`；反例：`module_admin/service/simulation_service.py` 仍以 `@classmethod + query_db` 为主 | 已扩展 provider 覆盖面，但仍存在“实例化 DI”与“classmethod + query_db 参数”混用。 |
| R4 controller 保持薄边界 | 部分通过 | 已改进：`module_admin/controller/project_controller.py`、`module_admin/controller/protocol_controller.py`、`module_admin/controller/simulation_controller.py`（故障参数解析/校验下沉到 service） | 控制器仍有部分业务参数组装逻辑（如 websocket 推送聚合逻辑）。 |
| R5 controller 业务决策下沉 service | 部分通过 | 已改进：`module_admin/controller/simulation_controller.py` 的故障请求解析由 `SimulationService.build_fault_injection_request_services` 承担；`create_session` 创建人决策下沉到 `SimulationService.create_session_services` | 业务决策大幅减少，但尚未实现全控制器统一。 |
| R6 仿真会话状态共享存储 | 通过 | `module_admin/service/simulation_runtime_state.py`；`tests/unit/services/test_simulation_runtime_state.py`；`tests/unit/services/test_simulation_multi_worker_smoke.py` | Redis-first + 本地兜底实现存在且有跨进程 smoke。 |
| R7 WS 单会话单生产者模型 | 通过 | `module_admin/service/simulation_runtime_state.py`（producer owner claim/release）；`module_admin/controller/simulation_controller.py`（push loop owner claim + shared fallback）；`tests/unit/services/test_simulation_runtime_state.py` | 已补齐跨 worker 显式 owner 协调，非 owner worker 走 shared stream 消费。 |
| R8 幂等：同 key 同 payload 复用响应 | 通过 | `middlewares/idempotency_middleware.py`；`tests/unit/middlewares/test_idempotency_middleware.py` | 命中缓存回放逻辑已验证。 |
| R9 幂等：同 key 不同 payload 返回冲突 | 通过 | `middlewares/idempotency_middleware.py`；`tests/unit/middlewares/test_idempotency_middleware.py` | 409 `application/problem+json` 已覆盖。 |
| R10 限流超限返回 429 + retry metadata | 通过 | `middlewares/rate_limit_middleware.py`；`tests/unit/middlewares/test_rate_limit_middleware.py` | `Retry-After` 与 `X-RateLimit-*` 可用。 |
| R11 结构化请求日志字段完整 | 通过 | `middlewares/request_logging_middleware.py`；`utils/log_util.py`；`tests/unit/middlewares/test_request_logging_middleware.py` | 已包含 `request_id/trace_id/user_id/path/method/status/duration`。 |
| R12 HTTP/DB/Redis OTel spans 关联 | 通过 | `utils/otel_tracing.py` + `server.py` 初始化；`tests/unit/utils/test_otel_tracing.py`；`tests/integration/test_otel_trace_correlation.py` | 启动链路与端到端 trace 关联均有自动化验证证据。 |
| R13 暴露 Prometheus `/metrics` | 通过 | `server.py:324`；`middlewares/prometheus_middleware.py`；`utils/prometheus_metrics.py`；`tests/unit/middlewares/test_prometheus_middleware.py` | 请求与依赖指标可抓取。 |
| R14 ORM/Alembic 漂移前置拦截 | 通过 | `migration-drift-check` in `.gitlab-ci.yml` + `scripts/check_migration_drift.py` | 以 GitLab CI 为发布门禁，漂移检查可阻断合并。 |
| R15 状态/删除标志不用魔法值 | 部分通过 | 正向：`module_admin/entity/do/project_version_do.py`、`module_admin/service/project_version_service.py` 使用枚举；范围外未做全仓硬约束 | 变更模块基本达成，但缺少全局 lint 规则约束。 |

## 覆盖质量评估

- 单元测试覆盖：**中高**
  - 幂等、限流、日志、指标、仿真共享状态均有针对性用例。
  - 新增仓储迁移路径已补充单测（project/protocol/common/project_version/device/device_category）。
- 集成测试覆盖：**中**
  - 语法兼容问题已清理（Python 3.9 下核心模块可导入）。
  - `tests/integration/test_error_handling_rfc7807.py` 与 `tests/integration/test_otel_trace_correlation.py` 已纳入并通过本地回归。
- CI 约束强度：**中高**
  - GitLab 侧已包含 DAO 检查、迁移漂移检查、架构回归测试集合。

## 关键风险（按优先级）

1. **P1：R3/R4/R5 架构一致性未收口**
   - 影响：后续新增功能易回到旧模式，评审和测试成本上升。
2. **P2：R15 全仓魔法值约束仍未彻底统一**
   - 影响：后续增量改动可能重新引入字符串字面量，导致语义不一致与审查成本上升。

## 测试执行记录

- `python3 -m pytest -q -n 0 --no-cov tests/unit/services/test_project_service.py tests/unit/services/test_protocol_service.py tests/unit/services/test_common_service.py tests/unit/middlewares/test_idempotency_middleware.py tests/unit/middlewares/test_request_logging_middleware.py`
  - 结果：35 passed
- `python3 -m pytest -q -n 0 --no-cov tests/unit/middlewares/test_rate_limit_middleware.py tests/unit/middlewares/test_prometheus_middleware.py tests/unit/utils/test_otel_tracing.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/unit/services/test_simulation_service.py`
  - 结果：19 passed
- `python3 -m pytest -q -n 0 --no-cov tests/unit/middlewares/test_idempotency_middleware.py tests/unit/middlewares/test_rate_limit_middleware.py tests/unit/middlewares/test_request_logging_middleware.py tests/unit/middlewares/test_prometheus_middleware.py tests/unit/utils/test_otel_tracing.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/unit/services/test_simulation_service.py tests/unit/services/test_project_service.py tests/unit/services/test_project_version_service.py tests/unit/services/test_protocol_service.py tests/unit/services/test_common_service.py tests/unit/services/test_device_service.py tests/unit/services/test_device_category_service.py`
  - 结果：67 passed
- `python3 -m pytest -q -n 0 --no-cov tests/unit/services/test_simulation_service.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_project_service.py tests/unit/services/test_protocol_service.py tests/integration/test_core_modules.py`
  - 结果：60 passed
- `python3 -m pytest -q -n 0 --no-cov tests/integration/test_error_handling_rfc7807.py`
  - 结果：16 errors（`ModuleNotFoundError: aiosqlite`）
- `python3 scripts/check_no_dao_imports.py`
  - 结果：passed

## 增量复审（2026-02-11，continue）

### 本轮结论

- R3（依赖注入）从“部分通过”继续收敛：
  - `simulation_controller` 的 HTTP 路由已统一改为 `Depends(get_simulation_service)` + 实例方法调用。
  - `simulation_service` 增补实例包装方法（create/start/stop/read/fault/event/runtime stream），避免 controller 直接调用 `*_services` 类方法。
- R4/R5（薄控制器与业务下沉）继续收敛：
  - 故障注入参数解析已统一走 `SimulationService.build_fault_injection_request(...)`。
  - 事件/故障/状态/数据读取路由均改为 service 实例入口。
  - 仍有保留项：WebSocket push 协调逻辑仍在 controller（已改为通过 service 实例访问 runtime API）。
- R12（trace 关联证据）补强：
  - 新增 `tests/unit/middlewares/test_request_logging_middleware.py::test_request_log_prefers_otel_trace_id`，
    验证存在有效 OTel span 时日志 `trace_id` 与 span trace id 对齐。
- R15（魔法值治理）补强：
  - `login_service` 的 `status == '1'` 已替换为 `StatusEnum.DISABLED.value`。
  - 新增 CI 检查脚本 `scripts/check_magic_flag_literals.py`，并在 GitLab CI 增加 `magic-flag-literal-check` job。

### 本轮测试记录

- `python3 -m pytest -q -n 0 --no-cov tests/unit/services/test_simulation_service.py tests/unit/middlewares/test_request_logging_middleware.py tests/integration/test_core_modules.py`
  - 结果：31 passed
- `python3 -m pytest -q -n 0 --no-cov tests/unit/middlewares/test_idempotency_middleware.py tests/unit/middlewares/test_rate_limit_middleware.py tests/unit/middlewares/test_prometheus_middleware.py tests/unit/utils/test_otel_tracing.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py`
  - 结果：21 passed
- `python3 -m pytest -q -n 0 --no-cov tests/unit/services/test_login_service_core.py`
  - 结果：17 passed
- `python3 ruoyi-fastapi-backend/scripts/check_magic_flag_literals.py`
  - 结果：passed
- `python3 -m pytest -q -n 0 --no-cov tests/integration/test_error_handling_rfc7807.py`
  - 结果：16 errors（本地环境缺失 `aiosqlite`）

## 增量复审（2026-02-11，continue-2）

### 本轮结论

- R4/R5（薄控制器与业务下沉）进一步收口：
  - `simulation_controller.push_simulation_data` 已降级为单一转调。
  - 会话级推送编排（owner 协调、增量采集、节流广播、动画事件合成）集中至
    `SimulationService.stream_session_updates(...)`。
  - `simulation_controller` 不再持有推送主循环与动画构建逻辑，实现边界更清晰。

### 本轮测试记录

- `python3 -m pytest -q -n 0 --no-cov tests/unit/controllers/test_simulation_controller.py`
  - 结果：2 passed（含“controller 委托 service 编排”断言）
- `python3 -m pytest -q -n 0 --no-cov tests/unit/controllers/test_simulation_controller.py tests/unit/services/test_simulation_service.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/integration/test_core_modules.py`
  - 结果：37 passed

## 增量复审（2026-02-11，continue-3）

### 本轮结论

- R7（WS 单会话单生产者）稳定性补强：
  - `SimulationService.stream_session_updates(...)` 增加 `alarms` 独立限额，不再复用 `bandwidth` 限额。
  - owner worker 本地采集分支对 `bandwidth/alarms/faults` 统一做尾部裁剪，避免突发批量事件导致共享流写入与内存缓冲放大。
  - `alarms` 广播也按限额截断，和消息/带宽/故障事件策略保持一致。
- RFC7807 集成回归阻塞项解除：
  - 本地虚拟环境已确认 `aiosqlite` 可用，`tests/integration/test_error_handling_rfc7807.py` 从依赖错误恢复到可稳定执行。

### 本轮测试记录

- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/services/test_simulation_service.py`
  - 结果：16 passed（含新增 owner 分支裁剪与 shared 分支 alarms 限额断言）
- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/controllers/test_simulation_controller.py tests/unit/services/test_simulation_service.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/integration/test_core_modules.py tests/integration/test_error_handling_rfc7807.py`
  - 结果：58 passed

## 增量复审（2026-02-11，continue-4）

### 本轮结论

- R4/R5（薄控制器与业务决策下沉）继续收敛：
  - `get_simulation_messages/get_simulation_bandwidth/get_simulation_alarms` 的“本地实时优先 + 共享流回退 + 端口过滤”逻辑已从 controller 下沉到 `SimulationService`。
  - controller 侧三条读取接口均收敛为单一 service 转调，边界职责更清晰（解析/鉴权/响应映射）。
- R3（service 能力聚合）增量改善：
  - `SimulationService` 新增 `read_messages_with_fallback/read_bandwidth_with_fallback/read_alarms_with_fallback`，将读取策略集中在 service 层，便于复用与测试。

### 本轮测试记录

- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/services/test_simulation_service.py tests/unit/controllers/test_simulation_controller.py`
  - 结果：24 passed（含新增 6 条“下沉与转调”用例）
- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/controllers/test_simulation_controller.py tests/unit/services/test_simulation_service.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/integration/test_core_modules.py tests/integration/test_error_handling_rfc7807.py`
  - 结果：64 passed

## 增量复审（2026-02-11，continue-5）

### 本轮结论

- R4/R5（controller 业务决策下沉）继续收口到故障接口：
  - `inject_fault/upsert_fault` 的“请求解析 + 会话ID兜底 + 调用注入”流程已合并到 `SimulationService.apply_fault_injection(...)`。
  - `query_faults/delete_fault` 的 `sessionId` 校验与标准化已下沉到 `SimulationService.require_session_id(...)`。
  - controller 中移除了 `query_faults` 里的内联 `ValidationException` 组装逻辑。
- R3（service 职责聚合）继续提升：
  - `SimulationService` 新增统一故障编排入口，controller 仅保留路由参数接收、鉴权、响应映射与日志。

### 本轮测试记录

- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/services/test_simulation_service.py tests/unit/controllers/test_simulation_controller.py`
  - 结果：31 passed（新增故障编排/会话ID校验下沉测试）
- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/controllers/test_simulation_controller.py tests/unit/services/test_simulation_service.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/integration/test_core_modules.py tests/integration/test_error_handling_rfc7807.py`
  - 结果：71 passed

## 增量复审（2026-02-11，continue-6）

### 本轮结论

- R12（trace 关联证据）补强到“端到端可执行验证”：
  - 新增集成测试 `tests/integration/test_otel_trace_correlation.py`，在真实 FastAPI OTel instrumentation 下验证：
    - 上游 `traceparent` 可贯穿到 server span。
    - 请求日志 `trace_id` 与链路 span `trace_id` 一致。
    - 业务子 span（模拟 db/redis 操作）与 HTTP server span 具备父子关系，且共享同一 trace。
- 请求日志中间件容错增强：
  - 当 OTel 当前 span 不可用时，`RequestLoggingASGIMiddleware` 增加 `traceparent` 解析回退，
    避免日志 `trace_id` 退化为随机 request_id 导致跨系统追踪断链。

### 本轮测试记录

- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/middlewares/test_request_logging_middleware.py`
  - 结果：4 passed（新增 `traceparent` 回退断言）
- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/integration/test_otel_trace_correlation.py`
  - 结果：1 passed
- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/middlewares/test_request_logging_middleware.py tests/integration/test_otel_trace_correlation.py tests/unit/controllers/test_simulation_controller.py tests/unit/services/test_simulation_service.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/integration/test_core_modules.py tests/integration/test_error_handling_rfc7807.py`
  - 结果：76 passed

## 增量复审（2026-02-11，continue-7）

### 本轮结论

- R4/R5（controller 业务决策下沉）继续收敛到仿真控制参数接口：
  - `set_simulation_speed` 不再在 controller 内部做默认值/类型解释；统一改为 `SimulationService.resolve_speed_input(...)`。
  - `set_simulation_duration` 的入参标准化逻辑统一改为 `SimulationService.resolve_duration_input(...)`。
  - controller 保持“路由参数接收 + service 转调 + 响应映射”边界，减少接口行为分散。
- R3（service 能力聚合）增量改善：
  - `SimulationService` 新增通用输入解析方法（speed/duration），为后续 DI 和跨入口复用提供统一落点。

### 本轮测试记录

- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/services/test_simulation_service.py tests/unit/controllers/test_simulation_controller.py`
  - 结果：37 passed（新增 speed/duration 输入解析与 controller 转调断言）
- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/middlewares/test_request_logging_middleware.py tests/integration/test_otel_trace_correlation.py tests/unit/controllers/test_simulation_controller.py tests/unit/services/test_simulation_service.py tests/unit/services/test_simulation_runtime_state.py tests/unit/services/test_simulation_multi_worker_smoke.py tests/integration/test_core_modules.py tests/integration/test_error_handling_rfc7807.py`
  - 结果：82 passed

## 增量复审（2026-02-11，continue-8）

### 本轮结论

- GitLab CI 门禁覆盖面补齐：
  - `architecture-regression-tests` 已追加 `tests/unit/controllers/test_simulation_controller.py` 与 `tests/integration/test_otel_trace_correlation.py`。
  - 新增/下沉后的控制器边界验证与 OTel 端到端关联验证将由 GitLab pipeline 持续阻断回归。
- R12 在验收矩阵中从“部分通过”更新为“通过”，证据改为“初始化 + 单测 + 端到端集成测试”闭环。

### 本轮测试记录

- `./venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/controllers/test_simulation_controller.py tests/integration/test_otel_trace_correlation.py`
  - 结果：12 passed

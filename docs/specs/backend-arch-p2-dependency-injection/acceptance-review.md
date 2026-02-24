# 依赖注入容器 P2 最终验收（本轮范围）

## 评估信息

- 评估日期：2026-02-21
- 评估对象：`docs/specs/backend-arch-p2-dependency-injection/requirements.md`
- 评估范围：非暂缓模块（排除 `simulation`、`protocol`、`device*` 的迁移收尾）
- 结论：**Task 1-8（按本轮范围）已完成，可进入后续里程碑**

## 任务完成状态

- Task 1 组合根与容器：完成
- Task 2 Service 构造器注入（按本轮范围）：完成
- Task 3 Repository 生命周期装配（按本轮范围）：完成
- Task 4 基础设施 Provider 生命周期：完成
- Task 5 控制器统一容器注入：完成
- Task 6 测试替换机制：完成
- Task 7 CI 防回退门禁：完成
- Task 8 迁移收敛与验收：完成

## 迁移里程碑（本轮）

1. 组合根与容器落地：`container/app_container.py`、`container/wiring.py`、`container/providers.py`
2. 控制器全量切换：`module_admin` 与 `module_generator` 控制器统一 `Depends(service_provider(...))`
3. Service/Repository 收敛：核心管理域（`user/dept/config/common/dict/job/log/menu/post/notice/role`）完成构造器注入与仓储工厂化
4. CI 治理落地：classmethod 与业务层即时实例化门禁脚本接入流水线
5. Task 8 收口：注入链路回归、事务边界回归、性能基线归档、依赖图刷新

## 关键实现增量（本轮收口）

1. `module_admin/service/audit_log_service.py`
   - 改为构造器注入仓储工厂，移除业务方法内即时仓储构造。
2. `module_admin/service/user_service.py`
   - 改为通过构造器注入 `user/user_role/user_post` 仓储工厂，移除业务方法内即时实例化。
3. `tests/conftest.py`
   - 新增 ORM 模型自动导入，确保测试建表阶段完整注册 `*_do.py` 元数据。
4. `utils/transaction_manager.py`
   - 已有事务场景默认使用 savepoint 执行嵌套事务，并统一支持 timeout。
5. `tests/unit/utils/test_transaction_manager.py`
   - 移除局部 `db_session` 覆写，统一复用全局测试会话夹具。
6. `tests/integration/test_dict_config_management.py`
   - `config delete` 用例补充 `409` 期望（内置配置不可删除的业务语义）。

## 验收证据

### 1) 架构门禁脚本

- `cd ruoyi-fastapi-backend && venv/bin/python scripts/check_no_new_service_classmethods.py`
  - 结果：passed（0 tracked entries）
- `cd ruoyi-fastapi-backend && venv/bin/python scripts/check_no_new_service_instantiations.py`
  - 结果：passed（15 tracked entries，均位于暂缓 `simulation` 模块）
- `cd ruoyi-fastapi-backend && venv/bin/python scripts/check_protocol_updates.py`
  - 结果：passed
- `cd ruoyi-fastapi-backend && venv/bin/python scripts/check_protocol_coverage.py --format=json`
  - 结果：coverage 100%（63/63）
- `cd ruoyi-fastapi-backend && venv/bin/python scripts/check_resilience_policy_bindings.py`
  - 结果：passed（14 operations discovered）

### 2) 注入链路 + 事务边界回归

- `cd ruoyi-fastapi-backend && venv/bin/python -m pytest -q -n 0 --no-cov tests/unit/container/test_app_container.py tests/unit/container/test_container_fixtures.py tests/unit/utils/test_transaction_manager.py tests/integration/test_core_modules.py tests/integration/test_dict_config_management.py tests/integration/test_user_management.py tests/integration/test_dept_management.py`
  - 结果：`76 passed`
- 其中事务边界专项：
  - `cd ruoyi-fastapi-backend && venv/bin/python -m pytest -q -n 0 tests/unit/utils/test_transaction_manager.py`
  - 结果：`14 passed`

### 3) 容器依赖图

- `cd ruoyi-fastapi-backend && venv/bin/python scripts/export_container_graph.py --format dot --output ../docs/specs/backend-arch-p2-dependency-injection/container-graph.dot`
- `cd ruoyi-fastapi-backend && venv/bin/python scripts/export_container_graph.py --format text --output ../docs/specs/backend-arch-p2-dependency-injection/container-graph.txt`

产物已更新：
- `docs/specs/backend-arch-p2-dependency-injection/container-graph.dot`
- `docs/specs/backend-arch-p2-dependency-injection/container-graph.txt`

### 4) 性能基线

- 基线文档：`docs/specs/backend-arch-p2-dependency-injection/baselines/performance-baseline-2026-02-21.md`
- 基准脚本与产物：
  - `cd ruoyi-fastapi-backend && venv/bin/python scripts/benchmark_container_bootstrap.py --iterations 1000 --warmup 20 > ../docs/specs/backend-arch-p2-dependency-injection/baselines/di-bootstrap-benchmark-2026-02-21.json`
  - `cd ruoyi-fastapi-backend && venv/bin/python scripts/benchmark_di_resolution.py --iterations 50000 --warmup 2000 > ../docs/specs/backend-arch-p2-dependency-injection/baselines/di-resolution-benchmark-2026-02-21.json`
- 快照结论：
  - 容器 build+validate：`total p95 = 0.003ms`
  - 服务解析额外开销（`resolve_service` 对比 direct call）：`avg_overhead_p95_us = 0.041`，`max_overhead_p95_us = 0.167`

## 风险与遗留

1. 暂缓域（`simulation`、`protocol`、`device*`）未纳入本轮迁移收尾，相关门禁清零与全量重构在后续里程碑执行。
2. 测试输出中偶发 OTel `SpanExporter` 关闭后写入告警（stderr），不影响本轮用例退出码与结论；建议后续在测试配置中统一禁用该 exporter。
3. NFR2（接口级 P95 回退阈值）需通过端到端压测进一步确认；当前基线为 DI 层微基准，主要用于框架开销对比。

## 结论

- P2 在本轮范围内满足 R1-R7 的验收口径。
- 架构、任务、验证与基线文档已同步；Task 8 可判定完成。

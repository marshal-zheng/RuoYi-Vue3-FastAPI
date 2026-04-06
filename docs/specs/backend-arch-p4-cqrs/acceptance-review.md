# CQRS P4 验收记录

## 评估信息

- 评估日期：2026-02-22
- 评估范围：`docs/specs/backend-arch-p4-cqrs/requirements.md`
- 验收结论：系统管理域 CQRS 切换与验收项已完成

## 已实现能力

1. 控制器切换收敛
   - 系统管理域控制器读路径统一 `mediator.query(...)`
   - 写路径统一 `mediator.send(...)`
   - 导出接口统一先走 QueryHandler，再执行导出映射
2. 防回退门禁
   - 新增历史控制器切换治理脚本（已移除）
   - 已接入 `.gitlab-ci.yml` 与 `.github/workflows/ci.yml`
3. 端到端验收覆盖
   - 新增 `ruoyi-fastapi-backend/tests/integration/test_system_cqrs_cutover.py`
   - 覆盖系统读接口契约、写接口命令链路、Query/Command pipeline 触发
4. 性能基线归档
   - 新增历史 CQRS 查询派发微基准脚本（已移除）
   - 归档 `docs/specs/backend-arch-p4-cqrs/baselines/cqrs-query-dispatch-benchmark-2026-02-22.json`
   - 归档 `docs/specs/backend-arch-p4-cqrs/baselines/performance-baseline-2026-02-22.md`

## 验证记录

- `cd ruoyi-fastapi-backend && venv/bin/python -m ruff check tests/integration/test_system_cqrs_cutover.py`
  - 结果：passed
- 历史控制器切换治理脚本（已移除）
  - 结果：passed（8 files scanned）
- `cd ruoyi-fastapi-backend && venv/bin/python -m pytest -q -n 0 --no-cov tests/integration/test_system_cqrs_cutover.py`
  - 结果：11 passed
- `cd ruoyi-fastapi-backend && venv/bin/python -m pytest -q -n 0 --no-cov modules/system/tests/test_command_pipeline_behaviors.py modules/system/tests/test_query_pipeline_behaviors.py`
  - 结果：8 passed
- 历史 CQRS 查询派发微基准脚本（已移除）
  - 结果：成功输出基线 JSON

## 备注

- 测试结束后存在 OpenTelemetry 控制台 exporter 的 `I/O operation on closed file` 噪声日志，不影响断言结果与用例通过状态。

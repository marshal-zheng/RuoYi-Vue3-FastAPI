# No-op 回归基线（2026-04-06）

本基线记录 capability-state-governance 在无差异场景下必须保持的行为。

## `dev-sync` 无差异

目标：

- 第二次对同一 capability target state 执行 `dev-sync` 时，不应重复写受管对象
- postcondition verify 必须继续返回 `clean`
- no-op 路径耗时不能明显高于首次有差异同步

当前回归守护：

- `managed_data_applied_operations == 0`
- `metadata_updated_objects == 0`
- `metadata_deactivated_objects == 0`
- `affected_objects == ()`
- `residual_objects == ()`
- `postcondition_verify.result == "clean"`
- `duration_ms <= first_run.duration_ms + 100`

对应回归：

- `tests/unit/scripts/test_dev_sync_service.py::test_execute_dev_sync_noop_path_stays_clean_and_fast`

## `deploy` 无新 bundle

目标：

- `db_artifacts/releases/` 下没有待部署 bundle 时，`deploy` 必须保持成功 no-op
- 不应写 artifact history
- 不应把 no-op 误报成失败或 clean replay

当前回归守护：

- `managed_data.result == "no-op"`
- `release_manifest.result == "no-op"`
- `postcondition_verify.result == "no-op"`
- `applied_bundle_ids == ()`
- `skipped_bundle_ids == ()`
- CLI `python scripts/db.py deploy --revision head` 也输出同样的 no-op 结果

对应回归：

- `tests/unit/scripts/test_deploy_release_service.py::test_execute_release_deploy_returns_noop_when_no_bundle_exists`
- `tests/unit/scripts/test_db_workflow.py::test_deploy_command_keeps_no_bundle_path_idempotent`

## 统一入口守护

`scripts/start.sh` 仍然只能依赖 `db.py` 入口，不允许重新引入旁路脚本。

对应回归：

- `tests/unit/scripts/test_workflow_verify_service.py::test_inspect_release_workflow_detects_bypass_entrypoint`

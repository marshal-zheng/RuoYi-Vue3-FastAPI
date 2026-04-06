# AI Harness 输出契约基线（2026-04-06）

本基线记录 capability-state-governance 稳态下，AI harness 需要依赖的 CLI 输出字段。

## `python scripts/db.py status --format json`

稳定 JSON 顶层键：

```text
allowed_actions
db_dev_sync_engine
db_target
deploy_path
dev_sync_path
finalize_path
last_successful_action
managed_data_drift
managed_scope
pending_release_bundle
schema_drift
startup_action
status_path
verify_path
visibility_drift
workflow_mode
workflow_stage
```

约束：

- JSON 使用稳定键名
- 当前实现按键名字典序输出
- `allowed_actions` 与 `managed_scope` 是数组，不是逗号拼接字符串

对应回归：

- `tests/unit/scripts/test_db_workflow.py::test_status_command_json_contract_keys_are_stable`

## `python scripts/db.py verify --ci`

稳定 shell 风格字段：

```text
workflow_mode
db_dev_sync_engine
db_target
startup_action
deploy_path
workflow_stage
allowed_actions
managed_scope
status_path
dev_sync_path
finalize_path
verify_path
schema_drift
managed_data_drift
visibility_drift
pending_release_bundle
last_successful_action
workflow_command
verify_ci
verify_scope
declaration_verify_status
declaration_verify_result
declaration_verify_details
compiled_checksum
release_plan_checksum
artifact_validation_status
artifact_validation_result
artifact_validation_details
schema_verify_status
schema_verify_result
bundle_chain_verify_status
bundle_chain_verify_result
bundle_chain_verify_details
bypass_verify_status
bypass_verify_result
managed_data_verify_status
managed_data_verify_result
visibility_verify_status
visibility_verify_result
failed_step
verify_result
```

补充规则：

- drift 或失败场景会追加 `*_error` / `*_details`，但上述字段集合必须稳定存在
- 对象级差异通过 `managed_data_verify_details`、`visibility_verify_details`、`declaration_verify_details` 透出
- `compiled_checksum` 与 `release_plan_checksum` 是 capability 编译和发布选择的稳定 checksum

对应回归：

- `tests/unit/scripts/test_db_workflow.py::test_verify_command_ci_output_contract_is_stable`
- `tests/unit/scripts/test_db_workflow.py::test_verify_command_fails_on_managed_data_drift`

## Legacy 阻断

AI harness 可以依赖下面语义判断旧入口回流：

- 如果 `menus.registry.yaml` 或 `base/*.yaml` 残留非空内容，`verify` 链路会把 `declaration_validation` 标成 `invalid`
- 错误文本包含 `legacy declaration file is no longer supported`

对应回归：

- `tests/unit/scripts/test_workflow_verify_service.py::test_inspect_release_workflow_blocks_legacy_declarations_from_formal_chain`

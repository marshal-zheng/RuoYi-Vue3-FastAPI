# DAO Decommission & Repository Migration Notes

## 评估时间

- 2026-02-11

## 结论摘要

- DAO 目录级退役已完成：`module_admin/dao`、`module_generator/dao` 不在仓库中；当轮历史 DAO 导入治理脚本校验通过，该脚本现已移除。
- Repository-only 改造已覆盖 P0 重点链路（`ProjectService`、`ProtocolService`、`CommonService`）的服务层直连 SQLAlchemy 会话调用。
- 全仓仍存在部分 service 直接调用 `flush/commit`，说明 R2 在“全量后端范围”下仍为部分达成。

## 本次补齐改造

- `ruoyi-fastapi-backend/module_admin/service/project_service.py`
  - `_generate_project_code` 改为调用 `ProjectRepository.get_max_project_code_by_prefix`。
  - `edit_project_services` 改为调用 `ProjectRepository.update`。
- `ruoyi-fastapi-backend/module_admin/service/protocol_service.py`
  - `edit_protocol_services` 改为调用 `ProtocolRepository.update`。
  - `delete_protocol_batch_services` 改为调用 `ProtocolRepository.commit`。
  - 同步修复 `model_dump(by_alias=True)` 导致字段别名无法回写 DO 的风险，改为 `model_dump()`。
- `ruoyi-fastapi-backend/module_admin/service/common_service.py`
  - `get_table_names_services` 改为调用新建 `CommonRepository.list_sys_tables`。
- 新增仓储：
  - `ruoyi-fastapi-backend/module_admin/repository/common_repository.py`

## 验证结果

- DAO 退役检查：
  - 命令：历史 DAO 导入治理脚本（已移除）
  - 结果：`DAO decommission check passed`
- 回归单测（35 条）：
  - `tests/unit/services/test_project_service.py`
  - `tests/unit/services/test_protocol_service.py`
  - `tests/unit/services/test_common_service.py`
  - `tests/unit/middlewares/test_idempotency_middleware.py`
  - `tests/unit/middlewares/test_request_logging_middleware.py`
  - 结果：全部通过

## 当前状态（2026-02-11 更新）

- 通过规则扫描确认：`module_admin/service` 中已无 `query_db.execute/query_db.flush/query_db.commit/db.flush/db.commit` 直连持久化调用。
- 相关迁移覆盖：
  - `project_version_service`：更新路径改为 `ProjectVersionRepository.update(...)`
  - `device_category_service`：写路径统一走 repository + `@transactional`
  - `device_service`：接口重建与导入提交改为 repository 方法（`update/delete_by_device_id/add_all/commit`）
  - `job_log_service`：同步提交改为 `JobLogRepository.commit_sync(...)`

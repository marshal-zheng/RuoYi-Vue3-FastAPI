# Release Bundles

正式数据库产物统一存放在 `db_artifacts/releases/<bundle_id>/`。

`bundle_id` 约定格式：
- `YYYYMMDD_NNN_<slug>`

每个 bundle 目录固定包含：
- `bundle.yaml`
- `managed-data.yaml`
- `release.manifest.yaml`

文件职责：
- `bundle.yaml` 记录 `bundle_id`、`schema_revision`、`release_key`、产物 checksum 和 bundle 级 `idempotency_key`
- `managed-data.yaml` 冻结受管数据操作序列
- `release.manifest.yaml` 冻结本次允许生效的菜单、角色菜单、字典和配置可见性范围

Checksum 约束：
- 三个文件都基于其 YAML payload 的 canonical JSON 表示计算 SHA-256
- `bundle.yaml` 保存 `managed-data.yaml` 与 `release.manifest.yaml` 的 checksum
- 同一个 `bundle_id` 下，如果已有文件内容与新 payload checksum 不一致，生成过程必须失败

幂等约束：
- `bundle_id` 一旦落盘即视为不可变
- `sys_db_workflow_artifact` 通过 `UNIQUE(bundle_id, artifact_type)` 约束 deploy 重放
- `sys_db_workflow_object` 通过 `UNIQUE(object_type, object_key)` 约束受管对象所有权

首个 baseline bundle 可通过：

```bash
cd ruoyi-fastapi-backend
python scripts/manual/generate_baseline_bundle.py \
  --bundle-id 20260402_001_datasource-baseline \
  --schema-revision 20260402_workflow_metadata
```

默认会基于当前受管声明生成全量 baseline scaffold，并写入 `db_artifacts/releases/<bundle_id>/` 供后续人工复核。

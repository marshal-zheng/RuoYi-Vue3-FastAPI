# 文件资产硬切换：非生产执行与旧路径收缩（任务 16）

日期：2026-10-27。范围：本机开发环境（Docker MySQL `ruoyi-mysql-local`、非生产 MinIO `ruoyi-minio-local`）。不涉及生产，生产切换仍需另行授权（任务 19、`TBD-PROD-01`）。

## 1. 决定

用户于 2026-10-27 选择硬切换：不迁移历史头像、公告图片和生成器历史文件列，不保留双轨（requirements.md R13 与 Clarifications Session 2026-10-27）。依据之一是任务 1 的本地盘点：唯一的头像引用属于已软删除用户，且对应文件已缺失；公告 0 条；生成器无文件字段（`inventory.md` §5）。

## 2. 切换实现

| 项 | 位置 |
| --- | --- |
| 唯一正式版本 | `ruoyi-fastapi-backend/alembic/versions/20261024_file_assets.py`（Revises `20261022_remark_v2`，downgrade 拒绝） |
| 冻结 DDL | `ruoyi-fastapi-backend/scripts/data_migrations/file_assets_v1.py`：建表 → 加 `gen_table.asset_fields` → 公告内容就地转 UTF-8 → 删除 `sys_user.avatar` → 登记维护任务；各步幂等 |
| 开发环境 | `scripts/db.py dev-sync`：Atlas 按 ORM 收敛，后置步骤只登记维护任务 |

已删除的迁移专用代码：历史迁移器 `modules/file_assets/application/legacy_migration.py` 及其测试，迁移台账表 `sys_file_asset_migration`，公告临时列 `notice_content__text_v2`，两阶段版本 `20261024_file_assets_expand/contract`，收缩门禁与 dev-sync 迁移前置，CLI `inventory/migrate/verify`，生成器历史列（`legacyColumn`），迁移主体 `MIGRATION_UPLOADER_ID`。

## 3. 本机开发库终态（只读查询，2026-10-27）

| 检查 | 结果 |
| --- | --- |
| `sys_user.avatar` | 不存在 |
| `sys_notice.notice_content` | `mediumtext`，`utf8mb4` |
| `gen_table.asset_fields` | `json` |
| 资产表 | `sys_file_asset`、`sys_file_binding`；无迁移台账表 |
| 维护任务 | job 9/10/11：`maintain`（每分钟）、`sweep_orphans`（03:30）、`purge_tombstones`（04:00），均 `concurrent='1'` |
| 切换前备份 | 2026-10-24 由实施会话导出 `ruoyi-fastapi-pre-file-assets-20261024T172353.sql.gz`（会话临时目录，非长期存储） |
| 退役上传目录 | `ruoyi-fastapi-backend/vf_admin/upload_path` 原样保留（1 个无引用的历史文件） |

本机开发库在 2026-10-24 已按当时的两阶段流程到达同一目标模式；改为单一版本后，目标模式不变，因此没有再次执行破坏性变更。新的单一版本在真实 MySQL 一次性库上按旧结构验证（见 §5）。

## 4. 旧路径收缩

| 旧路径 | 状态与证据 |
| --- | --- |
| `POST /common/upload`、`GET /common/download`、`GET /common/download/resource` | 已从 `common_controller.py`/`common_service.py` 删除；`shared/openapi.json` 与生成 SDK 中无对应端点 |
| `/profile` 静态挂载 | `sub_applications/handle.py`、`staticfiles.py` 已删除，`server.py` 不再挂载 |
| `UploadSettings`/`UploadConfig`、`DOWNLOAD_PATH` | 已从 `config/env.py` 删除 |
| 前端 `VITE_APP_BASE_API + /profile/...` 拼接 | 头像、上传组件、编辑器均改用资产 ID 与 `/file-assets/<id>/content` |
| mock 覆盖登记 | `/common/upload`、`/common/download*` 条目已删除，文件资产端点登记为 real-only；`yarn mock:contracts` 通过 |

全仓检索（后端 Python、前端 ts/vue、模板、`shared/openapi.json`）对上表旧标识及迁移代码标识无运行路径命中；仅剩生成器测试中“页面不得包含 `/common/upload`”的反向断言。

## 5. 验证

| 验证 | 命令 | 结果 |
| --- | --- | --- |
| 单一版本在旧结构上执行 | `RUN_FILE_ASSETS_MYSQL=1 RUN_FILE_ASSETS_S3=1 ./venv/bin/python -m pytest -n 0 --no-cov modules/file_assets/tests/test_mysql_minio_integration.py` 中 `test_hard_cutover_upgrade_on_the_legacy_shape_is_idempotent_and_fails_loudly` | 通过：无效 UTF-8 时失败且头像列仍在；修正后重跑完成建表、加列、公告内容一致转换、删头像列、登记 3 个任务；第二次执行无变更 |
| Alembic head | `./venv/bin/python -m alembic heads` | `20261024_file_assets (head)`，单一 head |
| 冻结 generator 结构与 ORM | `tests/unit/scripts/test_remark_postgresql.py` | 通过（补入本版本新增的 `asset_fields` 后与 ORM 一致） |
| 真实链路冒烟 | 开发后端（8088）+ MinIO，上传/头像/公告三个冒烟脚本 | 全部符合预期（详见 `integration.md` §4） |

## 6. 可见影响与回退

- 历史头像回落为默认头像。
- 历史公告中的旧 `/profile` 图片不再显示；编辑这类公告时须删除或重新上传图片才能保存。
- 已生成应用中的历史文件地址列不再由生成代码读写；生成配置不能再把 imageUpload/fileUpload 物理列当作文件字段。
- 回退：恢复切换前的数据库备份并部署旧版本；切换后新上传的资产随之丢弃。不提供 downgrade。

## 7. 未验证

- PostgreSQL 分支的公告转换（`convert_from(..., 'UTF8')`）只做了代码审读，未在真实 PostgreSQL 上执行。
- 生产或共享环境的切换未执行（需授权，`TBD-PROD-01` 未决）。
- 部署编排跟进（任务 19）：`docker-compose*.yml` 仍把旧上传卷挂到 `/app/vf_admin/upload_path`，且尚无 S3 端点与 `FILE_ASSET_*` 配置。应用已不读写该目录；保留卷即保留历史文件备份。在确定生产发行版后一并补齐存储配置并移除该挂载（移除挂载不删除卷数据）。Dockerfile 已不再创建上传/下载目录。

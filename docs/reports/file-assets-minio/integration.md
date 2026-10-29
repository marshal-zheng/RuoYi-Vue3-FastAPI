# 文件资产：集成验证报告（任务 15）

日期：2026-10-27。环境：本机开发机，Docker MySQL 8 `ruoyi-mysql-local`（127.0.0.1:3306）、非生产 MinIO `ruoyi-minio-local`（127.0.0.1:19000，镜像 `minio/minio@sha256:14cea493…936e`，RELEASE.2025-09-07，仅测试夹具，不代表生产选型）、Redis 127.0.0.1:6379。生产发行版 `TBD-PROD-01` 未决。

证据按层级区分：静态与契约、假存储注入（内存 SQLite + FakeStorage，不声称证明真实 S3 行为）、真实 MySQL、真实 S3、真实后端链路与前端组件。

## 1. 静态与契约

| 检查 | 命令（工作目录） | 结果 |
| --- | --- | --- |
| 后端 lint / format（文件资产相关全部路径） | `ruff check` / `ruff format --check`：`modules/file_assets`、`scripts/file_assets.py`、`scripts/data_migrations/file_assets_v1.py`、`scripts/internal/db_workflow/dev_sync_service.py`、`alembic/versions/20261024_file_assets.py`、`module_generator/asset_fields.py`、`modules/system/application/{file_asset_policies,notice_content,user_avatars}.py`、`container/file_asset_policies.py`、`middlewares/{upload_limit_middleware,route_path}.py` 及相关测试 | 通过（50 个文件） |
| Alembic | `./venv/bin/python -m alembic heads` | 单一 head `20261024_file_assets` |
| OpenAPI 导出与 SDK 生成 | `scripts/export_openapi.py --output ../shared/openapi.json`；`yarn api:generate` | 重复生成结果一致；无 `/common/upload`、`/common/download*`、`legacyColumn` |
| mock 契约覆盖 | `yarn mock:contracts` | 通过（critical 75，failures 0） |
| 生成器表单规范 | `yarn ui:standards` | 通过 |
| 前端生产构建 | `yarn build:prod` | 通过 |
| 前端类型检查 | `yarn type-check` | 1 个错误，位于 `src/api/_generated/sdk.gen.ts` 的 AI 文本字段 SSE 函数；换成 HEAD 的生成文件同样出现，属已有问题，与文件资产无关 |
| 前端 lint | `yarn lint:check` | 1 条警告，位于未改动的生成文件 `src/api/_generated/client/types.gen.ts`（与 HEAD 相同） |

## 2. 假存储注入与单元

| 套件 | 命令 | 结果 |
| --- | --- | --- |
| 文件资产 | `./venv/bin/python -m pytest -p no:cacheprovider --no-cov modules/file_assets/tests` | 163 通过，13 跳过（真实集成需显式开启） |
| 生成器 | `... tests/unit/module_generator` | 111 通过 |
| 后端全量 | `... tests modules` | 2146 通过，63 跳过，4 失败 |

后端 4 个失败在 HEAD 工作树上同样失败，与文件资产无关：`test_migrations_have_create_date`（备注迁移缺 Create Date）、`test_current_user_resolution_requires_enabled_account[enabled]`、`test_export_role_list_maps_status_before_export`（`text_columns` 参数）、`test_user_detail_query_handler_keeps_camel_case_for_nested_option_models`（岗位 `remark_text`）。

覆盖的故障与边界（选列，均有命名测试）：上传提交前取消转 FAILED、READY 提交结果不明时按已提交状态判定、回收后的迟到 PUT 不复活 READY、认证 401 在任何行和对象之前、配额（数量与含本次文件的字节）、限流档、Office 宏/加密/损坏/伪装样本、图片转正去元数据与降级、绑定替换/重排/清空/释放与回滚、软删除释放、删除租约与两类失败退避、单对象 5xx 不中断本轮、连续连接级错误结束本轮、归属在本轮中途变为无效即停止删除、NoSuchBucket 归为存储错误、孤儿清扫判定/预算/游标/开关、墓碑清除、归属三态与 403/桶缺失判无效、健康探测反映存储不可达、投影分批（500 一批）。

## 3. 真实 MySQL 8 与 MinIO

命令（`ruoyi-fastapi-backend/`，凭据取自不入库的 `.env.dev.local`）：

```bash
RUN_FILE_ASSETS_MYSQL=1 RUN_FILE_ASSETS_S3=1 ./venv/bin/python -m pytest -n 0 --no-cov \
  modules/file_assets/tests/test_mysql_minio_integration.py
```

结果：13 通过（每个测试使用一次性库与一次性桶）。

| 测试 | 证明 |
| --- | --- |
| `test_competing_owners_bind_exactly_once` | 两个业务对象并发绑定同一资产，只成功一个 |
| `test_a_held_asset_row_is_skipped_by_cleanup_and_bound_drafts_never_expire` | SKIP LOCKED 跳过被持有的行；已绑定资产不会过期 |
| `test_cleanup_claim_first_makes_binder_conflict` | 清理先认领时绑定得到冲突，不会绑到待删资产 |
| `test_two_deletion_workers_claim_disjoint_rows_and_lease_expiry_reclaims` | 两个删除执行者认领互不重叠；租约到期后可重新认领 |
| `test_late_failure_writeback_never_overrides_deleted` | 迟到的失败回写不覆盖已 DELETED 的行 |
| `test_business_rollback_on_mysql` | 业务、绑定与旧资产释放同事务回滚 |
| `test_notice_content_mediumtext_round_trips_large_multibyte_html` | 约 293 KiB 多字节 HTML 在 MEDIUMTEXT 中完整往返 |
| `test_hard_cutover_upgrade_on_the_legacy_shape_is_idempotent_and_fails_loudly` | 旧结构上执行切换：非严格 sql_mode 下无效 UTF-8 仍在破坏性变更前失败；修正后完成；重复执行无变更 |
| `test_s3_put_stream_list_delete_semantics` | 单次 PUT、分块读取、列举分页与 LastModified、删除不存在对象 |
| `test_s3_ownership_states` | 安装标识缺失/不一致/一致的三态 |
| `test_bootstrap_refuses_to_take_over_without_confirmation` | bootstrap 不覆盖不一致的标识 |
| `test_late_write_after_reclamation_is_swept_by_the_orphan_sweep` | 回收后迟到写入的对象在宽限期后被清扫删除 |
| `test_http_chain_against_minio_streams_and_revalidates` | HTTP 流式读取、ETag 与 304 |

## 4. 真实后端链路（开发后端 8088 + MinIO）

启动：`./venv/bin/python app.py --env=dev`。`/health/file-assets` 返回 `available`、归属 `confirmed`、`storage.reachable=true`；聚合 `/health` 的 `fileAssets` 为 `available`。

| 冒烟 | 结果 |
| --- | --- |
| 上传 | 200；EXIF 方向转正（64×48 → 48×64）且 EXIF 去除；批量元数据对未知 ID 返回 `unavailableIds`；内容响应带 `ETag`、`private, no-cache`、`nosniff`、沙箱 CSP；`If-None-Match`（含 `W/` 与列表）返回 304；`download=true` 为 attachment；匿名 401；重复丢弃 204/204，之后 404；通用入口传头像用途 422 `PURPOSE_ENTRY_MISMATCH`；JPEG 冒充 PNG 415；SVG 415；未认证上传 401 |
| 头像 | 无扩展名 422；替换成功并规范化为 512 像素 PNG；`getInfo`/`profile`/用户列表返回新投影，无 `avatar` 字段；旧头像 404；GIF 415；操作日志记录为 `multipart（上传内容不记录）`，表单不在鉴权前预解析 |
| 公告 | 创建 201 并绑定（重复图片只绑一次）；详情与列表内容为字符串；编辑后旧图 404、新图 200；外链图片 422；新建意图的草稿不能绑定到已有公告 422；跨公告复用 409；删除后图片 404；超过 1 MiB 422 |

本地开发库终态见 `cutover.md` §3。

## 5. 前端

| 检查 | 结果 |
| --- | --- |
| `yarn test:run` | 156/163 个文件、1514/1547 项通过；7 个文件 33 项失败，与 HEAD 工作树逐项一致（mock 覆盖、字典弹窗、编辑读取生命周期、角色表单、开发菜单热同步、仿真 WebSocket），与文件资产无关 |
| 文件资产相关测试 | `FileAssetEditor.test.ts` 13 项（粘贴/拖放上传、data: 图片按真实类型命名、Office 粘贴保留 HTML、编辑器内复制的同源绝对地址还原为稳定路径、多图顺序、外链与未完成上传阻止保存、纯文本模式、图片一次性恢复）；`UserSecondaryWrites.test.ts` 7 项（头像命名、旧会话不写回、上传途中关闭对话框仍同步已提交的新头像）；`AuthenticatedUpload.test.ts`、`session.test.ts` 等覆盖 ID 数组契约与写入前 401 单次重发 |

## 6. 未验证

- 浏览器中的人工交互（按用户规则，未主动打开浏览器）：头像裁剪、公告编辑器的撤销/重做与保存后重开、生成页面实际操作。
- 并发负载下按 worker 数的上传/下载容量与事件循环响应；当前只有槽位与时限的单元测试，没有压测。
- 多实例部署与 nginx 容器代理链路（配置已审读，未运行）。
- 切换的 PostgreSQL 分支、TLS 下的存储连接。
- 生成器运行时只在服务层用 SQLite 验证 crud + element-plus；未跑 HTTP、树/主子表或 MySQL 运行时，element-ui 模板只渲染未编译。
- 生产发行版兼容（`TBD-PROD-01`）与生产切换（任务 19）。

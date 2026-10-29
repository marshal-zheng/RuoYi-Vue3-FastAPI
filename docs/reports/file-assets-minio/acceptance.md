# 文件资产与 MinIO 接入：开发验收报告（任务 17）

日期：2026-10-27。规格：`docs/specs/file-assets-minio/`（79 条验收标准，R1–R16）。范围：开发任务 1–17。生产发行版 `TBD-PROD-01`（任务 18）与生产切换（任务 19）未开始，本报告不构成生产接入完成。

## 1. 结论

开发范围完成：任务 1–17 的产物与验证均已交付。79 条验收标准中 61 条有实现与命名测试，13 条为实现加文档、静态检查或真实链路冒烟（无直接自动化测试），3 条部分验证（见 §4），2 条属生产范围。

实施方式：2026-10-24 由另一会话在 `std` 当前分支实施；2026-10-27 用户决定硬切换（不迁移历史数据），本会话据此删除迁移专用代码并收敛规格，随后由独立只读评审逐条核对。评审发现 5 个 P2 与若干 P3，均已修复并补回归测试（§3）。

## 2. 验收矩阵

状态：**通过** = 实现且有命名测试；**实现** = 实现，证据为文档、静态检查或真实链路冒烟；**部分** = 见 §4；**生产** = 留给任务 18/19。

| AC | 状态 | 证据 |
| --- | --- | --- |
| R1.AC1 | 通过 | `test_avatar_purpose_is_dedicated_and_self_only`、策略登记测试 |
| R1.AC2 | 通过 | `test_unavailable_storage_or_ownership_blocks_uploads`；`/profile` 挂载与本地写入已删除（`cutover.md` §4） |
| R1.AC3 | 通过 | 清理测试；维护任务经 sys_job 调度 |
| R1.AC4 | 实现 | `inventory.md`、`cutover.md` |
| R2.AC1 | 通过 | `test_upload_commits_ready_with_server_hash_and_immutable_key` |
| R2.AC2 | 通过 | 同上；对象键 `assets/YYYY/MM/<asset_id>` |
| R2.AC3 | 通过 | `test_ready_commit_failure_is_resolved_from_committed_state` |
| R2.AC4 | 通过 | `test_cancel_before_ready_commit_marks_failed`、`test_reclaimed_upload_is_not_resurrected_by_late_put` |
| R2.AC5 | 通过 | `test_unauthorized_rejection_happens_before_rows_and_objects`、`session.test.ts` |
| R3.AC1 | 通过 | 请求体上限、流式与慢速请求测试；头像接口不再在鉴权前预解析表单 |
| R3.AC2 | 通过 | 图片转正/去元数据/头像缩放/降级测试；冒烟验证 EXIF 去除 |
| R3.AC3 | 通过 | `test_full_pipeline_for_each_attachment_type`、生成器类型测试 |
| R3.AC4 | 通过 | MIME 别名与文件名测试；冒烟 415 |
| R3.AC5 | 通过 | `test_precheck_failures_create_no_rows`、`test_problem_details_carry_reason_codes` |
| R3.AC6 | 通过 | `test_office_samples`（OLE/OOXML、VBA/XLM、加密、损坏、伪装） |
| R4.AC1 | 通过 | `test_metadata_visibility_rules` |
| R4.AC2 | 通过 | `test_304_never_touches_storage`、`test_http_chain_against_minio_streams_and_revalidates` |
| R4.AC3 | 通过 | `test_invisible_and_unknown_assets_are_indistinguishable` |
| R4.AC4 | 通过 | `test_attachment_disposition_for_file_purposes` |
| R4.AC5 | 通过 | `test_released_assets_stop_serving_immediately` |
| R5.AC1 | 通过 | `test_business_rollback_on_mysql` |
| R5.AC2 | 通过 | `test_draft_rules_on_first_bind`；生成编辑在记录被并发删除时拒绝绑定（`test_generated_edit_never_binds_to_an_owner_deleted_concurrently`） |
| R5.AC3 | 通过 | `test_competing_owners_bind_exactly_once`（真实 MySQL） |
| R5.AC4 | 通过 | `test_bind_replace_reorder_release_and_clear` |
| R5.AC5 | 通过 | `test_failed_notice_save_keeps_previous_content_and_bindings`；前端只丢弃本次会话的草稿 |
| R5.AC6 | 通过 | `test_user_soft_delete_releases_avatar_and_projection` |
| R6.AC1 | 通过 | `UserSecondaryWrites.test.ts`；后端接口经真实链路冒烟 |
| R6.AC2 | 通过 | 上传途中关闭对话框仍同步已提交头像（`UserSecondaryWrites.test.ts`）；响应丢失时重读资料 |
| R6.AC3 | 通过 | `tests/unit/stores/user.test.ts`；冒烟验证投影字段 |
| R6.AC4 | 通过 | 头像登录可读测试；切换测试验证删除 avatar 列 |
| R7.AC1 | 通过 | 公告 HTML 净化与绑定测试 |
| R7.AC2 | 通过 | `test_cross_owner_and_cross_field_reuse_conflicts`；冒烟 409 |
| R7.AC3 | 部分 | 粘贴/拖放、data: 图片命名、Office 粘贴、同源地址还原、多图顺序、阻止未完成保存均有测试；撤销/重做与保存后重开未自动化 |
| R7.AC4 | 通过 | query-only 读者测试；list 与 query 走同一“任一权限”判定 |
| R7.AC5 | 通过 | `test_hard_cutover_upgrade_on_the_legacy_shape_is_idempotent_and_fails_loudly`；保存失败保旧 |
| R8.AC1 | 通过 | `AuthenticatedUpload.test.ts` |
| R8.AC2 | 通过 | 同上；上传 5xx/429/413/超时不重发 |
| R8.AC3 | 通过 | 会话切换与卸载取消测试 |
| R8.AC4 | 通过 | `FileAssetEditor.test.ts` 图片一次性恢复 |
| R8.AC5 | 实现 | `vite.config.ts`、`nginx.conf` 的 `/file-assets/` 同源代理（审读，nginx 未运行） |
| R9.AC1 | 通过 | `test_declaration_errors_fail_generation`（含标签字符、用途长度） |
| R9.AC2 | 通过 | `test_generated_crud_binds_projects_replaces_clears_and_releases` |
| R9.AC3 | 部分 | 四套模板渲染测试；运行时只在服务层用 SQLite 验证 crud + element-plus |
| R9.AC4 | 通过 | 物理上传列被拒绝的生成测试 |
| R10.AC1 | 通过 | `test_uploading_rows_inside_recovery_margin_are_kept` |
| R10.AC2 | 通过 | `test_cleanup_claim_first_makes_binder_conflict`（真实 MySQL） |
| R10.AC3 | 通过 | `test_two_deletion_workers_claim_disjoint_rows_and_lease_expiry_reclaims` |
| R10.AC4 | 通过 | 两类失败退避、单对象 5xx、连续连接错误、归属中途失效即停测试 |
| R10.AC5 | 通过 | `test_orphan_sweep_rules`、`test_late_write_after_reclamation_is_swept_by_the_orphan_sweep` |
| R10.AC6 | 通过 | `test_tombstones_purge_only_old_deleted_rows` |
| R10.AC7 | 通过 | `test_sweep_respects_switch_ownership_and_budget`、`test_check_consistency_reports_missing_and_unowned`；连续截断告警 |
| R11.AC1 | 通过 | `test_upload_metadata_content_and_revalidation` |
| R11.AC2 | 实现 | OpenAPI 由后端导出、SDK 由 `yarn api:generate` 重复生成一致；`yarn mock:contracts` 通过 |
| R11.AC3 | 实现 | 旧入口删除的检索证据（`cutover.md` §4） |
| R11.AC4 | 通过 | `test_discard_semantics` |
| R12.AC1 | 实现 | SecretStr 凭据、仅后端端点；凭据不入库（`.env.<env>.local`） |
| R12.AC2 | 通过 | `test_bootstrap_refuses_to_take_over_without_confirmation`；`print-app-policy` 最小权限 |
| R12.AC3 | 实现 | `scripts/minio-local.sh`（19000/19001、按 digest 固定镜像） |
| R12.AC4 | 通过 | 503 测试；`test_health_reports_a_storage_outage_even_with_confirmed_ownership` |
| R12.AC5 | 生产 | 私有桶、同源交付、无存储 CORS 已实现；TLS 在生产环境核验（任务 19） |
| R12.AC6 | 通过 | `test_s3_ownership_states`、`test_ownership_guard_transitions`、`test_missing_bucket_marks_ownership_invalid` |
| R13.AC1 | 通过 | 硬切换测试（真实 MySQL） |
| R13.AC2 | 通过 | 同上：非严格 sql_mode 下无效 UTF-8 仍在破坏性变更前失败 |
| R13.AC3 | 实现 | `cutover.md` §4；迁移代码无残留 |
| R13.AC4 | 实现 | `runbook.md` §6–7；downgrade 拒绝 |
| R13.AC5 | 生产 | 生产切换需授权（任务 19） |
| R14.AC1 | 通过 | `integration.md` §2 列出的故障测试 |
| R14.AC2 | 通过 | 13 项真实 MySQL/MinIO 测试，镜像按 digest 固定 |
| R14.AC3 | 部分 | 头像替换、会话切换、生成 CRUD 有测试；公告保存后重开与撤销未自动化 |
| R14.AC4 | 实现 | 本报告与 `integration.md` |
| R14.AC5 | 通过 | 各类格式样本、图片规范化、孤儿清扫测试 |
| R15.AC1 | 通过 | 解析时限与上限测试 |
| R15.AC2 | 通过 | 接收时限与断开测试 |
| R15.AC3 | 实现 | 结构化日志与 `/metrics` 指标（`runbook.md` §8） |
| R15.AC4 | 通过 | `test_projection_bounds_each_owner_query`（每 500 个归属一批） |
| R15.AC5 | 通过 | `test_draft_quota_rejects_without_creating_rows`、`test_draft_byte_quota_counts_the_incoming_file`、`test_upload_tier_is_stricter_and_identifiable` |
| R16.AC1 | 实现 | 规格与任务 18 记录 `TBD-PROD-01` |
| R16.AC2 | 实现 | 测试镜像说明（`minio-local.sh`、`integration.md`） |
| R16.AC3 | 实现 | 任务 19 门禁 |

统计：通过 61，实现 13，部分 3，生产 2，合计 79。

## 3. 独立评审发现与处理（2026-10-27）

| 级别 | 问题 | 处理 |
| --- | --- | --- |
| P2 | MySQL 非严格模式下，切换会把无效 UTF-8 公告截断而不报错 | 切换前用 Python 严格解码预扫描，失败即停；MySQL 会话另加 `STRICT_ALL_TABLES`；回归测试在 `sql_mode=''` 下验证 |
| P2 | 生成的编辑接口在记录被并发删除后仍绑定文件 | 锁定 owner 返回空时报“不存在”；回归测试 |
| P2 | 粘贴的 JPEG/WebP data 图片被命名为 `.png`，后端 415 | 按 MIME 取扩展名，兼容非 base64 data URL；回归测试 |
| P2 | 头像上传途中关闭对话框，已提交的新头像不写回 store，界面显示旧图 404 | 已提交即更新 store；回归测试 |
| P2 | Office 粘贴的 HTML 被图片取代；编辑器内复制的图片变成绝对地址被当外链 | 剪贴板有 HTML 时交给 Quill；同源绝对地址还原为 `/file-assets/<id>/content`；多图按顺序插入；回归测试 |
| P3 | `@Log` 在头像接口鉴权前按默认限制解析 multipart | `Log(capture_form=False)`，日志记录占位说明；真实链路验证 |
| P3 | 草稿字节配额未计入本次文件 | 计入；回归测试 |
| P3 | 健康检查在存储故障时仍报 available | 带 10 秒缓存的存储可达探测；回归测试 |
| P3 | 归属变为无效后本轮删除/清扫仍继续；缺少无效、长期未确认、连续截断告警 | 每次删除前检查归属；补齐三类告警；回归测试 |
| P3 | NoSuchBucket 被当作对象已删除 | 归为对象级错误，读标识时判无效；回归测试 |
| P3 | 生成器：用途可能超过 64 字符、标签未转义、大小提示向下取整、配置页行键随输入变化 | 生成时校验长度与标签字符；大小提示向上取整；去掉行键；回归测试 |
| P3 | 批量投影的 IN 列表随导出行数无限增长 | 每 500 个归属分批；回归测试 |
| 残留 | 空目录 `sub_applications/`、未使用的旧上传适配器 `RichEditor/upload.ts` | 已删除 |

未处理（记录在案）：生成业务的写接口不在 CSRF 保护路径中，这与项目现有其他业务写接口一致，不属于文件资产引入的问题；`FileUpload` 与 `ImageUpload` 共用加载遮罩、图片重试标记按元素而非按地址，属界面细节。

## 4. 部分验证与未验证

- R7.AC3 / R14.AC3：公告编辑器撤销/重做与保存后重开没有自动化测试，未在浏览器中人工验证。
- R9.AC3：生成器运行时只在服务层用 SQLite 验证 crud + element-plus；HTTP、树/主子表、MySQL 运行时与 element-ui 编译未验证。
- 负载下的容量与事件循环响应、多实例部署、nginx 容器链路、PostgreSQL 切换分支未验证（`integration.md` §6）。

## 5. 质量门禁

| 门禁 | 结果 |
| --- | --- |
| 后端 ruff check / format（文件资产相关路径） | 通过 |
| 后端 pytest 全量 | 2146 通过，4 失败（HEAD 上同样失败，与本功能无关） |
| 真实 MySQL/MinIO 集成 | 13 通过 |
| 前端 `yarn lint:check` | 1 条警告，位于未改动的生成文件（与 HEAD 相同） |
| 前端 `yarn type-check` | 1 个错误，位于 AI 文本字段的生成 SDK（HEAD 上同样存在） |
| 前端 `yarn test:run` | 1514 通过，33 失败（与 HEAD 逐项一致） |
| `yarn mock:contracts`、`yarn ui:standards`、`yarn build:prod` | 通过 |

## 6. 需求与任务一致性

79 个唯一 AC 均出现在 tasks.md 的需求追溯中，无未知引用；19 个任务的依赖只指向先行任务；`TBD-PROD-01` 只阻塞任务 18/19。

## 7. 交付物

- 规格：`docs/specs/file-assets-minio/{requirements,design,tasks,runbook,ssd-review}.md`
- 报告：`docs/reports/file-assets-minio/{inventory,cutover,integration,acceptance}.md`
- codemap：`docs/codemaps/{backend,data,frontend}.md`

## 8. 跟进项（不阻塞开发完成）

- `TBD-PROD-01`：决定生产对象存储发行版、镜像来源与维护责任（任务 18）。
- 部署编排：`docker-compose*.yml` 补 S3 配置并移除已退役的上传卷挂载（任务 19，`cutover.md` §7）。
- 每分钟维护任务使 sys_job_log 每天增加约 1,440 行，按现有日志清理策略处理。
- 与本功能无关、在实施中发现：`ruoyi-fastapi-frontend/.env.development` 有明文 `VITE_DEEPSEEK_API_KEY`（未入库，但 `VITE_` 前缀会进入前端包）。

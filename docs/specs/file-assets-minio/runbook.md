# 文件资产运维手册

配套：[需求规格](./requirements.md)、[技术设计](./design.md)、[实现任务](./tasks.md)。本手册覆盖开发与非生产环境；生产发行版仍为 `TBD-PROD-01`，生产部署需另行授权。

命令均在 `ruoyi-fastapi-backend/` 下执行，`--env` 选择 `.env.<env>` 与 `.env.<env>.local`（后者不入库，放凭据）。

## 1. 配置

非秘密项见 `.env.example` 的「文件资产」一节；凭据只放 `.env.<env>.local` 或由部署系统注入。

| 变量 | 说明 |
| --- | --- |
| `FILE_ASSET_S3_ENDPOINT` / `FILE_ASSET_S3_BUCKET` / `FILE_ASSET_S3_REGION` / `FILE_ASSET_S3_ADDRESSING_STYLE` | 仅后端可达的存储端点与私有专用桶；跨主机时用 TLS |
| `FILE_ASSET_S3_ACCESS_KEY` / `FILE_ASSET_S3_SECRET_KEY` | 应用账户（最小权限，见 `print-app-policy`） |
| `FILE_ASSET_S3_ADMIN_ACCESS_KEY` / `FILE_ASSET_S3_ADMIN_SECRET_KEY` | 只给 `bootstrap-storage` 使用的管理员凭据，Web 进程从不读取 |
| `FILE_ASSET_INSTALLATION_ID` | 每个部署环境唯一；复制环境时必须换新 ID 和新桶 |
| `FILE_ASSET_DRAFT_QUOTA_COUNT` / `FILE_ASSET_DRAFT_QUOTA_BYTES` | 每用户未绑定草稿上限，默认 50 个 / 200 MiB |
| `RATE_LIMIT_UPLOAD_IP` / `RATE_LIMIT_UPLOAD_USER` | 上传限流档，默认每分钟 60 / 30 |
| `FILE_ASSET_ORPHAN_SWEEP_ENABLED` | 孤儿清扫开关 |

未配置时 `/health/file-assets` 报 `unavailable`，上传、读取、元数据返回 503（`file-assets-unavailable`），其他业务照常。

## 2. 本机非生产 MinIO

```bash
../scripts/minio-local.sh up      # 独立容器 ruoyi-minio-local，127.0.0.1:19000/19001，镜像按 digest 固定
../scripts/minio-local.sh status
../scripts/minio-local.sh down    # 删除容器，保留卷
```

脚本生成 `.env.dev.local`（含应用与管理员凭据），不占用 steamer-plane 的 9000/9090。该镜像只是测试夹具，不代表生产选型。

## 3. 初始化与核对存储

```bash
./venv/bin/python scripts/file_assets.py --env dev print-app-policy          # 应用账户最小权限 JSON
./venv/bin/python scripts/file_assets.py --env dev bootstrap-storage         # 建私有桶、核对设置、写 _meta/installation.json
./venv/bin/python scripts/file_assets.py --env dev check-storage --write-probe
```

`bootstrap-storage` 遇到不一致的安装标识会拒绝覆盖。确需把桶转交给新环境（例如恢复演练）时：

```bash
./venv/bin/python scripts/file_assets.py --env <env> bootstrap-storage --take-over --confirm-installation <桶内现有ID>
```

应用进程处于「无效」状态时每分钟复核，标识修正后无需重启即恢复。

## 4. 代理与安全

- Vite 与 nginx 都把 `/file-assets/` 同源转发到后端（`vite.config.ts`、`nginx.conf`）；该段只承担内容读取，开启响应缓冲、关闭网关压缩。上传经 API 前缀代理段提交，其 `client_max_body_size 21m` 与 20 MiB 附件上限匹配。
- 浏览器从不直连存储，不需要存储 CORS，也不为文件新增 CSP 来源。
- 写接口 `/file-assets`、`/system/user/profile/avatar`、`/system/notice` 纳入 CSRF 校验；CSRF 与限流按去掉 `root_path`（`/dev-api`、`/prod-api`）后的路径匹配。

## 5. 维护任务

切换后 sys_job 中有三条禁止并发的任务（可在定时任务页面暂停或恢复）：

| 任务 | 调用目标 | 周期 |
| --- | --- | --- |
| 文件资产-回收与删除 | `modules.file_assets.jobs.maintain` | 每分钟 |
| 文件资产-孤儿对象清扫 | `modules.file_assets.jobs.sweep_orphans` | 每日 03:30 |
| 文件资产-墓碑清除 | `modules.file_assets.jobs.purge_tombstones` | 每日 04:00 |

每分钟任务会在 sys_job_log 中每天新增约 1,440 行，按现有任务日志清理策略处理。

### 删除重试

删除失败没有终止状态：存储不可用类失败不计次数，按持续失败时长从 1 分钟近似翻倍，最长间隔 15 分钟；对象级失败（如 403）计入尝试次数，最长间隔 6 小时。修复存储或权限后可立即重试：

```bash
./venv/bin/python scripts/file_assets.py --env dev retry-deletes                 # 全部失败中的行
./venv/bin/python scripts/file_assets.py --env dev retry-deletes --asset-id <ID>
```

它只把失败过的行提前，不缩短业务释放后的 24 小时宽限期。

### 一致性与孤儿

```bash
./venv/bin/python scripts/file_assets.py --env dev check-consistency [--prefix assets/2026/10/]   # 只报告
./venv/bin/python scripts/file_assets.py --env dev sweep-orphans --prefix assets/2026/08/          # 默认 dry-run
./venv/bin/python scripts/file_assets.py --env dev sweep-orphans --prefix assets/2026/08/ --apply
```

- 定时清扫只处理当前月与上一月前缀；暂停超过一个月后，用 `sweep-orphans --prefix` 补扫更早的月份。
- 无主对象（桶里有、库里完全没有记录）从不自动删除，意味着误配置、恢复或越界写入。确认原因后才可 `--apply --include-unowned`。
- 所有 `--apply` 都要求存储归属已确认。

## 6. 备份与恢复

- 数据库与桶分别按独立副本备份。恢复前先在定时任务页面暂停「孤儿对象清扫」，并停止写入。
- 数据库按快照恢复后，比快照新的对象在库中没有记录，会被报告为无主对象；先用 `check-consistency` 核对，再决定是否清理，最后恢复清扫。
- 不要在运行中的应用桶上覆盖已有 key。

## 7. 硬切换（2026-10-27 决定）

不迁移历史头像、公告图片和生成器历史文件列。步骤见 design.md「硬切换步骤」，要点：

1. 备份数据库；退役的 `vf_admin/upload_path` 原样保留。
2. 初始化并核对存储（第 3 节）。
3. 正式环境 `./venv/bin/python scripts/db.py deploy` 升级到 `20261024_file_assets`；开发环境 `dev-sync`。公告内容含无效 UTF-8 时在任何破坏性变更前失败，修正数据后重跑。
4. 发布新版本与代理配置，确认 `/health/file-assets` 为 available、归属为 confirmed。

可见影响：历史头像回落默认头像；历史公告中的旧 `/profile` 图片不再显示，编辑这类公告时须删除或重新上传图片才能保存。回退只能恢复切换前的数据库备份并部署旧版本，不提供 downgrade。

## 8. 排障

| 现象 | 含义与处理 |
| --- | --- |
| 503 `file-assets-unavailable` | 未配置、启动后尚未确认归属，或安装标识缺失/不一致/403；查看 `/health/file-assets` 的 `ownership.reason`，必要时 `check-storage` |
| 503（单次请求） | 存储暂时不可用或下载槽位等待 5 秒仍无空位；对象缺失时同时计入 `missing_object` |
| 429 | 上传限流档超限，或该用户未绑定草稿超出配额；问题类型区分两者 |
| 413 / 415 / 422 | 字节上限 / 类型不允许或内容与声明冲突 / 格式损坏、宏、加密不可验证、解析超时或图片规范化后仍超限 |

主要指标（`/metrics`，前缀 `file_assets_`）：`delete_backlog`、`oldest_delete_due_age_seconds`、`delete_retrying`、`max_delete_attempts`、`longest_delete_failing_seconds`、`binding_invariant_violation`、`storage_ownership_mismatch`，以及 `orphan_found_total`、`orphan_deleted_total`、`orphan_sweep_truncated_total`、`unowned_object_total`、`unexpected_key_total`、`missing_object_total`、`upload_quota_rejected_total` 等计数。

# 通用备注数据库演练

日期：2026-10-22。结果：本次转换器、门禁、正式 revision、MySQL 恢复和独立交付副本链路通过；原工作区历史发布包的既有异常仍阻断原目录正式交付。没有操作日常 `ruoyi-fastapi` 数据库、生产数据库或共享 Redis，没有发布或提交代码。

## 证据与环境

- 应用工作区：`/Users/hqz/dev/RuoYi-Vue3-FastAPI/.worktrees/generic-remark-rich-text`，分支 `codex/generic-remark-rich-text`。
- MySQL：本机 Docker `ruoyi-mysql-local`，8.0.46，回环地址 3306。Python 3.13.12，SQLAlchemy 2.0.48，Alembic 1.18.1；驱动发行版详见版本 JSON。
- 旧库测试只创建随机 `ruoyi_remark_*` 目标及相配 `_restore` 数据库，每例结束删除这两个测试库。备份真实执行 mysqldump，并恢复到第二个库后比对全部七表摘要；备份正文位于仓库外受限测试目录。
- [数据库测试日志](database-evidence/pytest-database.log)：69 passed，包含 20 个真实 MySQL 集成用例及 49 个单元/编译/内存用例。
- 正式旧库元数据专项复验：`pytest tests/integration/test_remark_mysql_migration.py -k formal_revision -q -n0 --no-cov`，1 passed，见 [专项日志](database-evidence/pytest-formal-metadata.log)。
- [受管数据测试日志](database-evidence/pytest-managed.log)：33 passed，覆盖声明编译、加载、计划、发布包、快速对齐和 Atlas 适配器。
- [分阶段报告、计数、原文/文档摘要和版本](database-evidence/mysql-cases.json)、[统一 CLI 退出码与脱敏指标](database-evidence/cli-results.json)、[实现文件 SHA-256](database-evidence/implementation-hashes.json)。这些报告不包含备注正文、SQL dump 或凭据。
- 恢复操作顺序与失败处理见 [升级恢复手册](upgrade-recovery.md)。

## 真实 MySQL：旧纯文本与恢复

普通 fixture 对七表各放 9 行，共 63 行：SQL NULL、空串、前后空白、中英文/emoji、空行、CRLF/CR、HTML 外观、JSON 外观、公式外观和 tab。每次实际备份恢复后才允许迁移。每表转换后 2 个 SQL NULL（原 NULL 与空串），其余内容逐行核对字面文本，检查 native JSON、块身份与完整规范文档。

| 场景 | 实际检查结果 |
| --- | --- |
| 正常转换 | 七表全部 complete、无临时列；原文 `literalDigest` 与完整 `canonicalDocumentDigest` 前后相等。 |
| 加列后中断 | 原字符串与临时 JSON 列保留；按物理状态重跑成功。 |
| 首批回填后中断 | 已提交批次保留，重新执行核对非空目标后继续。 |
| 单表切换后中断 | JSON remark 与字符串旧列保留，后续全局核验和清理成功。 |
| 旧列清理中断 | 已完成 JSON 表不被旧快照覆盖，剩余表恢复完成。 |
| 超过 500 行、有间隔主键 | sys_user 514 行，首批恰好写入 500 行（498 个非空目标、2 个 SQL NULL）；中断恢复后 514 行，字面/文档摘要均一致。其他六表各 9 行。 |
| 恢复新写入后的重复执行 | 每个普通成功用例再写入新文档，重跑后逐表确认新内容仍在；无 JSON→字符串或旧文本重写。 |
| 旧候选注释缺失 | backfilling、switched、complete 三种物理状态分别抹去目标 JSON 注释，重跑后七列均恢复为“备注文档”，正文和规范文档摘要不变。正式 revision 另逐列核对 native JSON、nullable、SQL NULL default 和 comment 与当前 ORM 一致。 |
| 只读预检失败 | control、budget、目标 conflict、错误版本四种真实故障均返回非零并原子落盘失败报告，含目标 hash、表、主键、failedPhase；私有正文标记不出现在 report/stdout/stderr，所有原列和原值保持不变。 |
| 新写入后停写/当前备份/前修 | 先保存带 bold 的新 Document v2，停止唯一写入者，将当前 JSON 库真实 dump 并恢复至第三个隔离库，逐表核对摘要和新富文本。随后故意破坏该新行版本，当前真实校验明确失败；只从已验证的当前 JSON 备份取该行定向修复，七表摘要及该新文档完整保留。未恢复升级前快照，列始终为 JSON。 |
| 缺真实停写声明/备份 | 在 DDL、Atlas 和受管写入之前拒绝；保留原列与源数据。 |
| 其他库的 manifest、无效恢复时间、源摘要变化 | 拒绝，记录 preflight 失败与定位，不进入改列。 |
| 另一个迁移持锁 | 第二连接立即拒绝，未将锁当作停写替代品。 |
| 正文超限/已有目标冲突 | 定位到表、主键与阶段，原 5001 字原文仍在，未切换或截断。 |
| JSON null、不可空 JSON | 结构/内容预检拒绝；SQL NULL 与 JSON null 分别检查。 |
| 正式 revision | 缺上下文直接 upgrade 拒绝，甚至不补建生成器子表；补齐目标绑定备份与停写上下文后 upgrade 到 `20261022_remark_v2`。 |
| 统一 CLI | `remark-migration-check` 的前后七表结构/数据摘要相同；`db.py deploy` 正确拒绝缺前提、正确传递满足条件的转换上下文。原目录后续独立发布包校验失败被保留。 |

执行命令（后端工作区）：

```bash
RUN_REMARK_MYSQL=1 ./venv/bin/python -m pytest tests/integration/test_remark_mysql_migration.py tests/unit/scripts/test_remark_bootstrap.py tests/unit/scripts/test_initial_migration.py tests/unit/scripts/test_remark_migration.py tests/unit/scripts/test_alembic_revision_ids.py tests/unit/scripts/test_alembic_defaults.py tests/unit/scripts/test_remark_postgresql.py tests/unit/scripts/test_dev_sync_service.py tests/unit/scripts/test_workflow_verify_service.py tests/unit/scripts/test_deploy_release_service.py tests/unit/scripts/test_finalize_release_service.py tests/unit/scripts/test_db_workflow.py -q -n0 --no-cov --basetemp /tmp/remark-mysql-final-20261022
./venv/bin/python -m pytest tests/unit/scripts/test_capability_declaration_compiler.py tests/unit/scripts/test_managed_data_declaration_loader.py tests/unit/scripts/test_managed_data_workflow.py tests/unit/scripts/test_release_bundle_service.py tests/unit/scripts/test_managed_data_fast_reconcile_service.py tests/unit/scripts/test_schema_apply_atlas.py -q -n0 --no-cov
```

## 真实 MySQL：空库与完整统一流程

原工作区正式 schema 链在新隔离库 `ruoyi_remark_cli_f4fed6f27940` 回放成功，七列直接为 nullable JSON。bootstrap 后用户、角色、岗位备注均为对象/SQL NULL；两次 dev-sync 分别应用 293 和 0 项，第二次元数据更新也是 0。该库随后供主代理的七资源 ORM/API 关联验证使用，相关结果单列在总验收报告。

为隔离原发布目录已有异常，又在仓库外临时副本创建新的空库和新的正式受管发布包；没有复写原发布文件。最新副本目录为 `/var/folders/80/8sfxkvmx2l755p0cgcrkv3740000gn/T/remark-delivery-jr1b1e4_`，目标为 `ruoyi_remark_delivery_5c3b721c90`。

| 统一入口 | 退出码/结果 |
| --- | --- |
| `db.py finalize --message 备注文档JSON交付演练` | 0；迁移校验成功、临时库清理成功、新发布包生成成功。 |
| `db.py deploy --revision head` | 0；正式 schema、受管产物、发布后置校验成功。 |
| `db.py bootstrap-seed --env dev` | 0；只初始化 bootstrap 领域。 |
| 第一次 `db.py dev-sync` | 0；业务数据应用 0，元数据按 dev-full 所有权调整 293。 |
| 第二次 `db.py dev-sync` | 0；业务数据应用 0、元数据更新 0，结果稳定。 |
| `db.py verify --ci` | 0；remark complete、schema/managed/visibility clean、pending bundle none。 |

副本内 finalize 为既有全局漂移生成了临时 revision `d72f1e1f6df8`。它包含本功能之外的历史索引/无 ORM 表等差异，仅用于演练副本，**没有带回本任务工作区，也不是本功能交付物**。本功能正式 revision 仍是 `20261022_remark_v2`。

演练中定位并窄修了统一入口的必要缺口：初始建表改按外键依赖排序、已有 dashboard 建表幂等、既有超 32 字符 revision 使用公共版本表 hook、Ruff module 格式化 hook、bootstrap 用户 overlay 的明确纯文本转换、bootstrap 角色回退路径、verify 入口目录解析，以及 MySQL `NOW()/CURRENT_TIMESTAMP`、布尔 `FALSE/0` 的同义默认值比较。没有忽略真实精度、ON UPDATE 或整数默认值差异。

MySQL 同义规则依据 [官方时间函数文档](https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html)；Alembic 复用现有公共 `version_table_impl` 与 `compare_server_default` 扩展点，没有重写迁移框架。

## 原发布目录的明确阻塞

[基线字节证据](database-evidence/historical-artifact-baseline.json) 证明：`20260404_001_initial-baseline/managed-data.yaml` 当前字节与初始 `262ec420` 完全相同，SHA-256 均为 `5058ec23008784044302d57c6a143e89e32cacb4875303adf8dee3dcc6058b21`。

但其 bundle 声明的规范内容 hash 为 `7cc63022…`，按仓库既有算法计算实际为 `e45f4dd6…`；文件还缺现工作流要求的 capability metadata。因此原目录 deploy、finalize/verify 仍会明确拒绝，不能将这些异常视为本次 JSON 转换造成，也不能修改旧文件或重算历史 checksum 来掩盖。

既有正式链另包含 sys_datasource/性能索引等全局漂移；本轮未将其额外 migration 带入交付。后续实际交付必须先按独立工作流审查/修复原发布链。这一限制与“转换器和新产物链路在隔离副本已通过”分别报告。

## PostgreSQL 与未验证项

`test_remark_postgresql.py` 有 5 个单元/编译/内存用例：使用实际 MySQL/PG dialect 检查 JSON 参数绑定、整个对象只编码一次和 `none_as_null=True` 的 SQL NULL；PostgreSQL 在 Alembic autocommit 中显式将两次改名包在同一事务，第二次失败发出 ROLLBACK 并恢复原物理状态；冻结的生成器缺表定义逐字段匹配当前 ORM 并编译为 PG DDL。没有真实 PostgreSQL 服务，**未宣称真实 PG 升级或驱动事务行为已验证**。

本轮真实备份恢复校验了旧 schema 与数据，未启动旧版本应用做恢复冒烟。新写入后的恢复已覆盖明确的停写、当前 JSON 备份、第三库恢复验证、实际版本损坏拒绝及单行定向向前修复，并额外保留幂等不覆盖检查；未执行真实生产事故恢复。UI、中文输入、弹框浮层和人工业务流程不属于数据库测试证据，仍须总验收单独记录。

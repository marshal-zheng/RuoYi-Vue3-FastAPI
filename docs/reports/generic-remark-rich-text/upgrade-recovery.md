# 通用备注 JSON 升级与恢复手册

本手册只覆盖 `sys_user.user_id`、`sys_role.role_id`、`sys_post.post_id`、`sys_dict_type.dict_id`、`sys_dict_data.dict_code`、`sys_config.config_id`、`gen_table.table_id` 的 `remark`。正式 revision 为 `20261022_remark_v2`，前置 revision 为 `20261017_dashboard`。正文使用冻结的 `remark-a-v1` codec，完整 Document v2 或 SQL NULL；禁止将 JSON 列直接改回字符串列。

本轮授权仅包含隔离库演练，未执行生产升级。每个实际环境都必须重新执行自己的预检、备份恢复和停写核对。仓库当前旧 baseline 发布包存在既有校验/元数据异常，详见 [演练报告](migration-rehearsal.md)；原目录的正式 deploy/finalize 不可据临时副本演练成功而放行。

## 1. 确认目标与版本

在后端目录执行统一入口，使用该环境已确认的配置；先核对 `db_target`，不得将日常库或其他环境当作演练目标。凭据只放环境配置或受限凭据系统，不写命令日志、报告或 Git。

```bash
./venv/bin/python scripts/db.py status
./venv/bin/python scripts/db.py remark-migration-check --report /restricted/remark/preflight.json
```

预检是只读操作。内容/预算/列状态失败也会生成脱敏失败报告，命令返回非零；报告明确记录表、主键、失败阶段，不能把报告文件存在当作预检通过。成功报告应列出七表状态、实际列类型/可空/default/comment、行数、SQL NULL/空串数、最大正文字符数、原值摘要、保真文本摘要和规范文档摘要，以及目标数据库标识和 schema 指纹。缺表、异常列组合、超预算或损坏 JSON 不等于可迁移通过。正文上限为 5000 Unicode 码点；JSON 紧凑 UTF-8 上限 262144 字节、节点 2000、正文树深 12、列表深 3、原始容器深 32。

先修复或由数据所有者明确处理异常值，再重跑预检。不得截断、用 NULL 兜底、放宽在线契约或手工先执行 ALTER TYPE。纯文本中的 HTML、JSON、Markdown 和公式外观都按字面保存；CRLF/CR 只统一为 LF，其他空白保留。

## 2. 真实停止所有相关写入

停写责任由操作者承担，`--remark-writers-stopped` 只是声明，不会停止进程。逐项确认并记录实际服务名称、实例、停止时间和恢复负责人：

1. 所有旧 FastAPI/Uvicorn/Gunicorn 实例、容器副本、reload 进程及会自动拉起它们的 supervisor/systemd/容器重启策略；入口保持维护状态。
2. 平台任务调度器及后台 worker、出站事件消费或会触发系统管理写入的任务；停止重试队列继续投递。
3. 开发菜单/受管配置热同步、文件 watcher、启动自动 dev-sync，以及其他机器上连接同一库的开发进程。
4. Excel 导入、生成器导入/同步、人工 SQL、CI/CD、定时 shell、seed、bootstrap、发布包应用等脚本。
5. 管理 API 调用方和其他持有同一数据库写权限的外部集成。

仅暂停前端或持有迁移 advisory lock 不构成停写。确认没有仍会写七字段的连接；备份后和迁移锁内会再次扫描，摘要变化会停止迁移。

## 3. 备份并在独立库恢复验证

备份目录在仓库之外且权限受限，例如先 `umask 077`。备份必须是该目标数据库的完整一致快照，包含 schema、原始数据、Alembic 与工作流元数据；仅导出 Excel 或七列文本不满足恢复要求。MySQL 使用环境认可的逻辑/物理备份方式；本机隔离演练使用 Docker 内的 mysqldump。不要将密码写入可共享脚本。

将备份恢复到另一个已明确允许覆盖的隔离库，使用与旧数据结构匹配的工具和旧版本代码。对恢复库执行统一只读预检，对比七表 `sourceDigest`、结构、主键/行数、NULL/空串和最大长度。数据库标识本来就不同，不能用恢复库标识替换原目标库标识。记录恢复时间、备份 SHA-256、实际恢复命令和旧版本代码 revision。尚未验证旧应用冒烟时应明确记录，不能只凭 dump 文件存在宣称可回退。

备份 manifest 为 JSON，最小格式如下；`sourceDigests` 必须来自已停写的原目标库预检，不是恢复库的新标识：

```json
{
  "databaseIdentifier": "<原目标 preflight.databaseIdentifier>",
  "restoreVerifiedAt": "2026-10-22T10:00:00+00:00",
  "backupFile": "/restricted/remark/full-backup.sql",
  "backupSha256": "<备份文件 SHA-256>",
  "sourceDigests": {
    "sys_user": "<sourceDigest>",
    "sys_role": "<sourceDigest>",
    "sys_post": "<sourceDigest>",
    "sys_dict_type": "<sourceDigest>",
    "sys_dict_data": "<sourceDigest>",
    "sys_config": "<sourceDigest>",
    "gen_table": "<sourceDigest>"
  }
}
```

实际不存在的表不填伪造摘要。恢复证明时间必须带时区。manifest 不会自动执行或验证恢复操作，操作者必须先完成真实恢复；执行器核对目标绑定、备份文件 hash 与源摘要。已有数据缺凭据会阻断；真正空库不要求历史数据备份。

## 4. 升级顺序

正式环境保持停写，以已核对的正式迁移和受管产物执行：

```bash
./venv/bin/python scripts/db.py deploy --revision head --remark-backup-manifest /restricted/remark/manifest.json --remark-writers-stopped
./venv/bin/python scripts/db.py verify --ci
```

仅开发环境可通过 `dev-sync` 使用同样的 manifest/停写参数。其顺序固定为：声明验证 → 备注预检与必要转换 → Atlas schema apply → 受管目标态对齐 → 备注后置验证。正式环境不得运行开发态 Atlas 快速同步。

转换器固定按主键 keyset 每批 500 行处理：建立 `remark__json_v2` → 冻结转换/批次事务 → 全行核对 → 切换并保留 `remark__text_v1` → 七表全局验证 → 报告原子落盘和 fsync → 清理旧列 → 再次校验。MySQL 每表切换是一条 ALTER；PostgreSQL 两次改名属于同一显式事务。MySQL DDL 本身仍不能整体回滚。

纯文本转换的块 ID 绑定最终表名、主键、段落序号与完整规范化原文；不会随机生成或反复包装。校验覆盖每行主键、NULL/空串映射、字面正文、规范文档和有序摘要，不只比较总行数。

正式 `finalize` 在独立临时库回放正式链并检查差异，然后产生新受管产物；不要将数据库临时副本中为既有无关漂移生成的 revision 带入本功能。发现七列字符串→JSON 的自动裸 ALTER 时会明确拒绝，必须使用本次手工数据迁移。

## 5. 缓存、只读冒烟与恢复写入

verify 必须同时核对七列 native JSON/SQL NULL、文档接纳、无临时列，以及 schema、受管目标态和发布可见性。任一失败，保持停写并保留报告。

用新版本应用在维护入口下启动，只放行必要的认证和只读检查。现有 `RedisUtil.init_sys_dict/init_sys_config` 启动流程会重建各自命名空间缓存；字典缓存保存完整文档及 `remarkText`，禁止 `FLUSHALL`。必要时使用现有字典/参数的授权刷新接口，只刷新相关命名空间。

依次读取用户、角色、岗位、字典类型、字典数据、参数和生成器表配置，检查完整 `remark`、派生 `remarkText`、NULL 与损坏值的区分。只读冒烟通过后再恢复新版本写入、后台任务和外部集成。不要让旧版本实例重新连接 JSON 结构。

## 6. 分阶段恢复

| 失败阶段 | 保留状态 | 恢复动作 |
| --- | --- | --- |
| 预检/备份/加列之前 | 原列 | 保持停写，处理报告中的表、主键、阶段和前提；重新预检。 |
| 加列后/回填中 | 原字符串 + 部分 JSON | 使用同一目标备份和统一入口重跑；非空目标先核对，冲突会停止；不要清空新列重做。 |
| 部分表切换 | JSON remark + 字符串旧列，或尚在回填 | 保持停写，按物理列状态恢复并完成全行/全局核对；不以日志文件单独决定进度。 |
| 全局验证后/清理中 | 外部备份 + 已完成 JSON + 部分旧列 | 先保存报告，继续清理和验证。已清理表按完整 JSON 校验，不用旧文本重写。 |
| 受管同步/缓存/新应用只读冒烟 | 已迁移 JSON 与备份 | 优先向前修复并重跑统一流程；已成功产物按原 checksum 幂等跳过。 |
| 已恢复写入后 | 新富文本已产生 | 立刻停写并备份当前完整库，保留新数据，向前修复。禁止恢复升级前快照覆盖新增写入，禁止 JSON→VARCHAR。 |
| 必须整体回退旧代码 | 经验证的一致快照 | 先保护当前完整库和新数据，再按审查后的数据恢复方案还原完整旧快照与相配旧代码；本次 downgrade 明确拒绝自动有损回退。 |

错误报告只保留表/主键/阶段、计数、摘要和安全错误类型，不包含备注正文；数据库 StatementError 的绑定文档参数不会写入报告或 CLI。外部私有诊断日志仍应按该环境的数据权限保管。不存在横跨 DDL、七表回填、缓存及发布产物的自动全局回滚保证。

## 7. 放行限制

真实 MySQL 隔离升级、备份恢复、失败恢复与 CLI 交付副本已演练。另已实测新富文本写入后的“停写 → 备份当前 JSON 库 → 第三库恢复验证 → 注入实际校验故障 → 从当前已验证备份定向修复损坏行 → 验证七表摘要和新文档保持”链路；这不授权生产自动修复或恢复旧快照。PostgreSQL 仅有实际 dialect 编译、参数绑定/SQL NULL 和事务改名内存分支测试，未进行真实 PG 演练。UI 尚未取得 computer use 授权；本手册不把编译、内存或数据库测试替代真实界面验收。

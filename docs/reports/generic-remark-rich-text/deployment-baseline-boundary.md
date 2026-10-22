# 数据库基线与代码交付边界

结论：`F_DELIVERY_BASELINE` 的原目录发布链异常在输入 HEAD 已存在，有原始字节和既有校验代码证据；本轮没有改写历史产物。已验证的备注机制、有效受管 fixture、真实旧库转换和独立副本六步 CLI 可以支持将本轮**代码**交付到源分支，但不能据此声称原目录可部署、生产迁移通过或真实 UI 通过。UI 按用户最新指令由用户自行测试，本任务不使用 computer use。

本报告为只读归因，未修改代码、历史产物、数据库或发布状态；不替代独立 reviewer 的最终判定。完整机器可核对证据见 [deployment-baseline-boundary.json](database-evidence/deployment-baseline-boundary.json)。

## 1. 历史产物已在输入 HEAD 异常

比较对象为原 source HEAD `262ec420`、实施输入快照 `de5a9993f17f0a2d38d46e0d1c8b5dc8a982dda9` 和当前实施工作区。以下三个文件在三者之间逐字节相同：

| baseline 文件 | 三者相同的文件 SHA-256 |
| --- | --- |
| managed-data.yaml | `5058ec23008784044302d57c6a143e89e32cacb4875303adf8dee3dcc6058b21` |
| release.manifest.yaml | `1783c71b94ddb4be104cc8f30bd9edcefea1223311e6eede669f5fab22b1c7ab` |
| bundle.yaml | `fee305d2eeb5564db462e6aef1028cb043a2e6b02cecd3182ca976f0e434735d` |

目录均为 `ruoyi-fastapi-backend/db_artifacts/releases/20260404_001_initial-baseline/`。按输入 HEAD 已有的 `compute_payload_checksum` 算法，即 `json.dumps(ensure_ascii=False, sort_keys=True, separators=(',', ':'))` 再取 SHA-256：

| 精确字段 | bundle 声明 | 实际规范内容 checksum |
| --- | --- | --- |
| artifacts[managed-data].checksum | `7cc63022f35a8ee16528e3b605c45a10a8a115ebac7bc8bae8b0581b35df1b62` | `e45f4dd6b6020ce89371b64213dbda26fe2dc2bb569375589467d1ae4514dbfd` |
| artifacts[release-manifest].checksum | `40bab74288b419686b3aa166dafcf9125c984c85c0c119c071bf8eb987380c00` | `4cffe9a5c02e589e4e8c4d717d4f81e258100ef6731b72287a404f35e8515d12` |

两个 payload 的顶层 `capability` 字段均缺失；这也不是本轮删除的字段。

输入 HEAD、输入快照及当前以下函数的 AST hash 完全相同，排除仅由代码格式变化造成的误判：

- `deploy_release_service._discover_bundle_files`：先核对两份内容 checksum，再调用 `load_capability_payload`，之后才把 payload 交给计划执行。
- `release_bundle_service.load_capability_payload`：要求 `capability`、模块及编译/发布选择校验字段。
- `release_bundle_service.compute_payload_checksum`：规范内容算法不变。
- `workflow_verify_service._validate_latest_bundle_payload`：要求上述 capability 与正式目标态。

因此，输入 HEAD 的 deploy 已会拒绝这些不一致 checksum，verify 已会拒绝缺失 capability；本轮 JSON 转换不是这些异常的成因。证据 JSON 同时记录各函数在三个版本中的行号与 AST hash，可用 `git show <ref>:<path>` 独立复核。

## 2. 本轮确实新增了哪些行为

本轮新建七列冻结转换器、正式 revision、备份/停写前置门禁、JSON/SQL NULL 校验、只读失败报告，以及在明确历史发布输入边界将纯文本转为文档的适配。

**finalize 的历史输入校验是本轮新增。** `finalize_release_service._load_managed_data_plan` 在适配前核对原 `managed-data.yaml` checksum；输入 HEAD 原来在此处直接读取操作。不能把这一条 finalize 行为变化说成“完全未变”。它按已确认设计让既有损坏产物更早停止，避免先转换内容后再重算旧 checksum；没有制造该产物的原始损坏。deploy/verify 对同一产物的拒绝早已存在。

有效历史 fixture 的 checksum/capability 按原文件生成，随后才进行备注适配，部署和重复回放测试通过；任意字符串仍不能通过在线 API。真实旧库的正式 revision、七列 JSON/nullable/default/comment 与当前 ORM 的一致性，以及当前 JSON 备份恢复后保留新富文本的向前修复均有实际 MySQL 证据，详见 [迁移演练](migration-rehearsal.md)。

## 3. 全局 schema 漂移的归因

独立交付副本在正式备注 head 后生成的临时 revision 还处理了 `sys_datasource`、历史性能索引、`sys_logininfor.create_time`、工作流注释和事件默认值等差异。这些与七列 JSON 变更分开核对：

- `20260226_add_datasource_table.py`、`20260127_performance_indexes.py`、`20260127_add_create_time_to_logininfor.py`、`20260405_extend_db_workflow_object_capability_metadata.py` 的当前字节均与原 HEAD、输入快照相同。
- `module_admin/entity/do/db_workflow_do.py`、`module_admin/entity/do/log_do.py`、`events/models.py` 的当前字节也与两份输入相同。
- 七个目标 ORM 类排除其已授权 `remark` 字段后，剩余 class AST 与输入快照完全相同；未借备注任务删除其他索引、修改事件默认值或改动其他列。
- 临时额外 revision 中没有再对七个 `remark` 做类型变更。本轮新增的生成器 metadata 登记和缺表创建由本功能正式 revision 承担，已验证；不归入“历史异常”以豁免本轮责任。

这些证据支持将剩余全局 schema 差异归于输入链与输入 metadata 的既有不一致。未对原 HEAD 的完整外部环境重新部署，不宣称所有原环境已经复现或放行。

## 4. 为何不修改旧 checksum/capability

历史 bundle 的 checksum 参与不可变产物身份、idempotency_key 和数据库 artifact ledger。把 bundle.yaml 的声明改成当前计算值，只能让当前文件“自洽”，无法证明它仍是当时已部署的内容；还可能与已有环境的原 artifact checksum、所有权和发布选择记录冲突。补造 capability 也需要真实历史目标态和所有权依据，不能凭当前声明反填。

已确认设计要求先校验原文件，再在内存中适配历史备注，并保留原文件名和 checksum。本次代码交付因此保留拒绝行为。若要治理原发布链，需要独立审查历史已部署状态，形成经过核对的新基线/修复产物及其迁移方案；不能用重算旧 hash 代替该工作。

## 5. 独立副本证明了什么

[CLI 证据](database-evidence/cli-results.json) 的六步均退出 0：finalize → deploy → bootstrap → dev-sync → dev-sync → verify。该副本：

1. 位于仓库外，使用唯一隔离数据库和新生成的有效受管产物。
2. 在副本中额外收敛既有全局漂移；该额外 revision 未带回源分支，本功能正式 revision 仍为 `20261022_remark_v2`。
3. 只证明当前机制能生成/应用/验证有效产物、原生 JSON 初始化和稳定重复同步；没有修复原目录旧发布链。

用户现授权的交付对象是本轮代码。依据以上边界，可以保留 `F_DELIVERY_BASELINE` 为已归因的既有部署限制，将本轮实现交付到源分支，报告未发布、未执行生产迁移、原发布目录未放行、真实 PG 未演练、真实 UI 由用户自测。不能将源分支交付写成“全部部署验收通过”，也不能将副本的额外 migration 混入本功能交付。

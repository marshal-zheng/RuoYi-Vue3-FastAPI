# 通用备注富文本规格检查记录

日期：2026-10-22。目标是判断规格可否进入实施，不证明功能已实现、发布或迁移成功。

## 授权与工作边界

- 用户已确认 requirements.md 和 design.md，并要求生成 tasks.md、直接使用 SSD auto；按技能映射为 auto-spec，自动完成规格，终点为 execution_ready。
- 用户常驻指令授权子代理工具使用；SSD 要求的两类只读 gate 据此执行。两次委派都遵守用户要求，继承主代理模型和推理强度。运行时没有可核实的具体配置字段，故实际模型/强度记 unavailable，不声称最高强度。
- 北极星上下文为 docs/README.md 的规格目录约定；没有绑定的 initiative/work-item，不额外创建。
- 本轮开始记录工作区已有 454 项改动；仅写 `docs/specs/generic-remark-rich-text/`。没有修改应用/ZXUI 代码、启动服务、操作数据库、使用 computer use、发布包或提交 Git。

## 只读澄清 gate

- 模式：read-only-subagent；代理 `/root/remark_spec_clarify`。
- 绑定：`docs/specs/generic-remark-rich-text/requirements.md`；同时只读已批准设计以核对设计负责确定的规则。
- 结论：NO_CRITICAL_AMBIGUITY；核心目标、范围、角色、完整性、可测试性、边界/失败、安全、数据、依赖、迁移和术语 11 类均明确。
- 建议：无；初次澄清回写 0；未解决高影响歧义 none。主代理复核并接受，形成进入 design_tasks 的证据。
- 限制：纯规格审查；不验证实现、真实 UI 或数据库。

## 独立设计 evaluator

模式：read-only-subagent；代理 `/root/remark_design_evaluator`。主代理负责写作与修正，独立代理没有写文件或提问用户。

| 轮次 | 结果 | 覆盖与处理 |
| --- | --- | --- |
| 1 | FAIL | 58/59 完整，R8.AC2 部分；发现 GEN-01 生成器 Vue2/主子表能力边界遗漏 |
| 2 | PASS | 59/59 完整；GEN-01 关闭；七个必需章节完整，无剩余阻塞 |

GEN-01 的实际证据：`ruoyi-fastapi-frontend/src/views/tool/gen/genInfoForm.vue:19` 仍提供 Vue2，`ruoyi-fastapi-backend/utils/template_util.py:168` 按前端版本路由、`:183` 将 sub 交给普通模板；`module_generator/templates/vue/v3/index.vue.jinja2:260` 有独立子表控件循环，Python DO/VO 亦有子表循环；ZXUI text-editor 的公开包声明 Vue3。

主代理采用默认决定并回写需求 Clarifications 与设计：Vue3 crud/tree/sub 的主、子字段全覆盖，子表摘要与按需编辑；Vue2 + remark 在保存、预览、下载、生成处拒绝，其他 Vue2 行为保持既有契约。它属于自动采用的模板边界决定，不记为用户逐条确认；若需要 Vue2 富文本生成，需另行明确其接入范围。本决定已在 SSD pending_review 留作一次性告知，不阻断 auto-spec。

修正未改动已批准的 59 条 AC 正文或编号；复审补充了唯一缺项，其余映射保持成立：

| 需求 | AC 数量 | 设计覆盖位置 |
| --- | --- | --- |
| R1 | 4 | 七字段清单、路径族、显式语义、范围外消费者 |
| R2 | 6 | 基础内容配置、粘贴/输入、清空、资源预算 |
| R3 | 5 | 公开出口、源码/候选包、字段适配、主题与轻量渲染 |
| R4 | 5 | 原生/Schema 值所有权、会话、dirty、提交反馈 |
| R5 | 6 | 封套、空值、严格结构、JSON 替换、读写与生成契约 |
| R6 | 6 | Python A 模型、链接、前置预算、权限/事务、版本样例 |
| R7 | 6 | 摘要/只读、Excel、字面导入、JSON 备份、缓存 |
| R8 | 5 | gen_table、版本/主子表矩阵、种子/受管声明、稳定校验和 |
| R9 | 6 | 每环境预检、确定性转换、逐行等价、物理状态与恢复 |
| R10 | 5 | 空库、Atlas 前转换、正式 revision/finalize/deploy/verify、方言演练 |
| R11 | 5 | 共享向量、七入口、真实数据库、证据层级、实施依赖 |

## 任务与依赖检查

任务作者读取了已批准的需求/设计，并定向核对实施顺序：

- `ruoyi-fastapi-backend/scripts/internal/db_workflow/dev_sync_service.py:107` schema runner 在受管同步前，因此任务 7 的前置保护先于任务 8 的 ORM 类型修改，任务 6–10 共同构成启动门槛。
- `ruoyi-fastapi-backend/scripts/db.py:528` deploy 先 upgrade；`:551` finalize 临时库升级；`:555` 会自动生成 revision，因此任务 8–10 同时交付正式迁移与裸 ALTER 防护。
- `ruoyi-fastapi-frontend/src/views/system/post/components/post-form.ts:17` 及 schema/initialPost 仍使用字符串，任务 4、17 覆盖库适配探针和业务完整值链路。
- `scripts/generate-api-types.sh` 默认读取 shared/openapi.json，任务 13 在后端契约后生成客户端；live 验证需显式传 8088。

本轮规格验证命令及结果：

| 检查 | 结果 |
| --- | --- |
| 三份规格存在、中文规范标题、design 七必需章节 | PASS |
| tasks.md 23 个连续且未勾选的任务，每项恰好一个末尾追溯字段 | PASS |
| 任务依赖只引用此前有效编号，因而无环 | PASS |
| rg 提取两侧 AC，comm 双向差集均为空 | PASS：缺失 0、未知 0，59/59 |
| 逐任务解析需求追溯、覆盖集合与 Markdown 围栏检查 | PASS |
| 59 条批准 AC 正文摘要不变 | PASS：SHA-256 `6008ed33245ff7bafe8f0831c89dc6ff96f9c63324ea957ec605d009f5f0865a` |
| 需求 Clarifications 仅一条默认决定，审核状态无重复章节 | PASS |

这些均为文档静态检查。前后端质量门禁、ZXUI 候选包、真实七入口、真实 MySQL/PostgreSQL 演练仍是 tasks.md 中的待执行工作，未标为通过。`.ssd-run.json` 仅记录流程状态，不能代替这些证据。

## 下游交接

- 规格状态：execution_ready；任务数 23；验收追溯 59/59；全部实施复选框仍未勾选。
- 下一技能：`executing-task docs/specs/generic-remark-rich-text`。
- 下一动作：实施从任务 1 的两仓基线与消费者复核开始。
- Writing-specs 完成信号：Implementation tasks have been generated. You can start executing Task 1 when ready.

# ZXUI schema 任务作者文档与 AI/token 对照

文档已落地并通过包交付验证。四次原样生成均通过固定功能检查和人工复核；任务文档组平均输入减少 **4.51%**，平均总 token 仅减少 **0.71%**，两对总量变化方向相反，耗时平均增加约 **19.33 秒**。本轮没有证明稳定的总 token 节省或加速，也不将功能通过等同于交互质量完全一致。

## 实现与长期收益

修改集中在 ZXUI `packages/schema-form`。README 成为任务路由，按真实需要组合阅读五类指南：

| 作者要完成的任务 | 文档 |
| --- | --- |
| 新增、编辑记录或表单弹框 | [CRUD](/Users/hqz/Downloads/element-plus/packages/schema-form/docs/authoring/crud.md) |
| JSON、上传、自定义对象输入 | [复合字段](/Users/hqz/Downloads/element-plus/packages/schema-form/docs/authoring/composite-fields.md) |
| 明细增删排序、嵌套错误与焦点 | [明细与错误](/Users/hqz/Downloads/element-plus/packages/schema-form/docs/authoring/nested-errors.md) |
| 已有 draft/history 的 Vue Flow、DAG、Dashboard 面板 | [受控配置面板](/Users/hqz/Downloads/element-plus/packages/schema-form/docs/authoring/controlled-fields.md) |
| 读取持久化 JSON 定义 | [JSON 导入](/Users/hqz/Downloads/element-plus/packages/schema-form/docs/authoring/json-import.md) |

[完整契约参考](/Users/hqz/Downloads/element-plus/packages/schema-form/docs/authoring/reference.md) 保留全部行为边界，公开类型仍是签名的权威来源。复杂业务可以组合 CRUD、复合字段和明细指南；任务路由没有限制字段数量、嵌套、联动、异步资源或宿主架构。

收益来自阅读范围明确、状态所有权清楚、复杂需求有入口，以及文档能随实际包交付。代价是维护更多短文档；通过完整参考、公共声明链接和复用原始 recipe 控制重复。没有新 DSL、AI 专用 API、检索平台或文档框架，也没有以更短输入替代必要业务约束。

这个组织方式借鉴 [Diátaxis 的任务指南](https://diataxis.fr/how-to-guides/) 与 [技术参考](https://diataxis.fr/reference/) 分工：操作流程围绕用户任务，完整契约独立可查。这是设计依据，不是 token 节省的证据。

## 通用与复杂业务能力保留证据

- 22 个 schema 运行时源文件的集合及 SHA-256 均未变化。
- 新包与 oracle 使用的当前包相比，21 份声明、9 份 JS/CSS 文件的集合及字节一致。
- 独立审查映射了 18 类能力。原 README 的核心行为正文迁入完整参考，忽略排版后逐字一致。
- 原通用 name/sort 示例迁到 CRUD；没有写入本次岗位评测的领域答案。
- 复合字段继续保留 raw/canonical、完整 edit-state、pending/blocking、异步验证、取消与焦点；嵌套错误继续保留稳定行身份、重排/删除、摘要降级和 ARIA；独立宿主继续拥有 draft/history。
- 修正初稿的两处不准确表述：其他 Vue Flow 宿主不必使用 X6；fieldPending 本身不阻断，但 submit 仍检查重复提交、blocked 和校验。

详见 [能力覆盖审查](evidence/schema-task-authoring-2026-10-20/coverage-review.md) 和 [新包声明/运行文件一致性](evidence/schema-task-authoring-2026-10-20/ai-authoring/checker-artifact-admission.json)。

## 实际包交付与验证

沿用 `scripts/copy-examples.mjs` 构建步骤，把 Markdown 源码链接改写为包内声明和示例链接。原始 Markdown 只维护一份，recipe 继续从已有 pilot 复制。未交付的本地链接使构建失败，避免只在仓库里能读、安装后断链。

| 验证 | 结果 |
| --- | --- |
| schema `typecheck` | 通过 |
| schema `build` | 通过 |
| 既有复杂场景 pilot | 14/14，通过 |
| 改动文档/脚本 Prettier 与脚本 ESLint | 通过 |
| 实际 tarball 文档 | 7 份完整交付，除链接目标外与源码一致 |
| 实际 tarball 本地链接 | 56 个均能解析到包内目标；独立复核锚点可达 |
| 实际 tarball recipe | 5 份与原文件字节一致，相对依赖齐全 |

本地 tarball SHA-256：`25ea9886e966d3fe8b036421073f344d72ca65949c93cbc590ca47053905319b`。

这是构建、静态契约和内存集成证据，未做浏览器或读屏验证。没有修改业务运行时代码、更新消费者依赖、提交 Git 或发布 npm。

## AI 对照设计

本轮比较同一个 schema API 的两种作者材料：

- A：修改前完整 README。
- B：新版 README 任务路由 + CRUD 指南。
- 两组附带逐字相同的五份公开类型，使用同一份实际包声明。
- 原样沿用上一轮任务、领域模型和输出结构；模型 `gpt-6-astra`、推理 `xhigh`、CLI 二进制与配置不变。
- ABBA 顺序、每组两次，独立空目录、无工具、单次最多 600 秒。失败保留，不重跑，不人工修补作者代码。
- 模型前冻结输入、runner、事件分类和经过合法/非法 oracle 检查的质量评分器。按 [OpenAI 评估指南](https://developers.openai.com/api/docs/guides/evaluation-best-practices) 的任务质量原则，把实际用量与可执行正确性分开判断。

区别是文档内容、组合与长度整体，不能把其中某一项独立归因为 token 变化。README 导航计入输入，但路由由实验预选，因此不测自动检索、沿链接读取或完整开发流程成本。普通 CRUD 的两次重复不能证明复杂业务或多模型普遍提效。

固定验收检查功能合同，不保证交互方案完全一致。任务文档组两份生成都把状态枚举实现为文本框加枚举校验，完整文档组两份都使用下拉框；原任务没有指定该控件，所以按相同标准验收，额外记录交互差异。第三份还使用任务允许的原生 `Rule.col`，没有采用 `columns/fullWidth`。短 CRUD 示例只演示 Input/InputNumber，完整参考仍保留 Select 示例，但两个样本不足以确认示例分布造成了控件选择变化。真实业务任务应明确输入方式和交互要求。

原始协议、冻结材料与执行记录位于 [本轮 AI 证据目录](evidence/schema-task-authoring-2026-10-20/ai-authoring/protocol.md)，上一轮不利结果完整保留。

## AI 实际结果

| 样本 | input | output | reasoning（已含于 output） | total | 秒 |
| --- | ---: | ---: | ---: | ---: | ---: |
| A1 完整文档 | 17,327 | 3,849 | 2,442 | 21,176 | 119.586 |
| B1 任务文档 | 16,545 | 4,241 | 2,899 | 20,786 | 129.541 |
| B2 任务文档 | 16,545 | 4,616 | 3,106 | 21,161 | 139.350 |
| A2 完整文档 | 17,327 | 3,744 | 2,254 | 21,071 | 110.648 |
| A 均值 | 17,327 | 3,796.5 | 2,348 | 21,123.5 | 115.117 |
| B 均值 | 16,545 | 4,428.5 | 3,002.5 | 20,973.5 | 134.4455 |

四次 cached input 与 cache write 均为 0，所以 uncached input 等于 input。总量为 **84,194 tokens = 67,744 input + 16,450 output**；10,701 reasoning tokens 已含于 output。合计运行 499.125 秒；这只统计四次正式作者调用，不包含当前开发对话或子代理工作，不估算账户费用。

| B−A | 第 1 对 | 第 2 对 | 均值 |
| --- | ---: | ---: | ---: |
| input | −782 | −782 | −782（−4.51%） |
| output | +392 | +872 | +632 |
| total | −390 | +90 | −150（−0.71%） |
| 秒 | +9.955 | +28.702 | +19.3285 |

无工具协议 **4/4** 通过，零模型重试、零人工改源。完整文档组 **2/2**、任务文档组 **2/2** 首次通过；每份均通过冻结评分器的 **30/30** 检查和独立人工审查。类型检查使用同一实际包声明，行为与 SFC 检查使用内存环境；没有把它当成浏览器或完整引擎验证。评分器和协议在看到本轮输出后均未修改。

本次结果支持“给定任务材料的输入量减少”，不支持“稳定降低总 token、推理成本或开发耗时”。输出增长主要来自 reasoning 子集，不能进一步归因到某一句指引或示例。文档和类型之外仍有相同 CLI 上下文，实际 input 不等于 Markdown 自身 token 数。

保留这次文档组织，理由是任务入口、完整参考和示例交付的维护价值，以及能力未被裁掉的直接证据。没有依据继续删约束、弱化复杂能力或为追求短提示而改变公共 API。后续只有真实作者任务暴露缺口时，才补对应指引与等价质量案例；不要把这个普通 CRUD 结果推广成复杂业务总体效率结论。

可复核数据：[usage-summary.json](evidence/schema-task-authoring-2026-10-20/ai-authoring/usage-summary.json)、[质量分析](evidence/schema-task-authoring-2026-10-20/ai-authoring/quality-analysis.md)、[冻结 manifest](evidence/schema-task-authoring-2026-10-20/ai-authoring/manifest.json)、[原始 run-summary](evidence/schema-task-authoring-2026-10-20/ai-authoring/run-summary.json)。四份完整原始事件、输出代码、调用参数与质量回执都保留在同目录 `runs/`。

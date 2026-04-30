# Demo Offline Semantic Blueprint Generation 需求规格

## 简介

`demo-offline-semantic-blueprint-generation` 是 `Demo Offline Semantic Data Platform` 的第一份实现 spec，父级总纲为 `demo-offline-semantic-data-platform`。本 spec 的 `platformLayer` 是 `Business Blueprint`，上游依赖为已完成的 `demo-offline-runtime-scenario-package` P0 runtime JSON package 能力，以及 Spec 0 对 AI/MCP/compiler/runtime/MSW/IndexedDB 边界的约束。

本 spec 要解决的问题是：当前 MCP 能在 build 后生成并激活 v1 `active.json`，但行业数据仍容易像模板换壳。现状中 `createDeterministicIndustryDraft()` 主要依靠有限阶段、风险、负责人和指标模板生成 `project` 与 `simulation` 数据；`compileScenarioPackage()` 再按固定公式推导 ID、时间、`createBy`、版本、拓扑和仿真记录。这能保证结构可用，却不足以保证不同业务主题之间具有真实语义差异。

本 spec 的目标是在继续输出 v1 `active.json`、不修改 runtime package 格式、不修改 Vue 页面、MSW handler、service/repository、IndexedDB schema 或后端 API 的前提下，为现有 `project + simulation` 生成链路新增 Business Blueprint 中间层、seed-aware 确定性语义生成、DiversityValidator、SemanticCoverageValidator 和语义质量报告，让主演示列表、详情、拓扑与仿真数据能体现行业对象、角色、部门、流程阶段、风险、指标和故事线差异。

本 spec 新增或强化的 `qualityGates` 为 `blueprint-schema`、`blueprint-semantic-minimum`、`diversity`、`semantic-coverage`、`v1-runtime-validation` 和 `import-dry-run`。它不实现 v2 manifest/slices/pointer，不实现 DOMC registry，不实现完整 Scenario Graph 或 Generator Recipes，也不新增未知业务模块接入。

## 需求列表

### R1: 建立 Business Blueprint 作为语义生成中间层
**用户故事:** 作为 demo-offline 数据生成维护者，我希望 MCP 先生成可校验的 Business Blueprint，再编译为现有 `IndustryDataDraft`，以便最终表数据不再直接来自少量模板字段填充。
**验收标准 (EARS):**
- R1.AC1: WHEN Spec A 实现生成流程时 THEN 必须在 `IndustryDataDraft` 之前新增 Business Blueprint 中间层，且 Blueprint 不得直接作为最终 runtime package 或 IndexedDB 数据。
- R1.AC2: WHEN 定义 Business Blueprint schema 时 THEN 必须至少覆盖行业名称、行业关键词、业务对象、组织/部门、persona/角色、流程阶段、风险类型、指标定义和 story beats，且语义最小集必须满足业务对象 >=5、persona >=3、部门 >=2、流程阶段 >=5、风险类型 >=4、指标定义 >=4、story beats >= `projectCount`。
- R1.AC3: WHEN MCP 从 `topic` 和 `businessDescription` 生成 Blueprint 时 THEN 必须同时支持本地 deterministic fallback，不得要求 AI provider、API key 或联网能力才能通过测试和 CI。
- R1.AC4: IF 外部 AI 参与生成或修复 Blueprint THEN MCP 必须对 AI 输出执行 schema 与语义最小集校验，失败时返回结构化 issue，而不是直接编译为表数据。
- R1.AC5: WHEN Blueprint 校验通过后 THEN compiler 或 generator 必须由 Blueprint 推导现有 `IndustryDataDraft` 所需字段，并继续复用 v1 编译链路。

### R2: 限定 Spec A 只覆盖现有 project 与 simulation 生成模块
**用户故事:** 作为项目负责人，我希望第二个 spec 聚焦当前可见数据质量问题，以便快速提升 demo-offline 演示可信度而不扩散到未知模块平台化。
**验收标准 (EARS):**
- R2.AC1: WHEN Spec A 定义实现范围时 THEN 只能覆盖现有 `project` 和 `simulation` 两个 generatable slices。
- R2.AC2: WHEN 生成计划包含 `auth` 或 `system` 时 THEN 它们必须继续按 P0 规则从 default scenario 复制，不得由 Blueprint 改写。
- R2.AC3: IF 用户输入的业务主题暗示新业务模块 THEN Spec A 不得新增模块、页面、MSW handler、IndexedDB table 或后端 API。
- R2.AC4: WHEN 后续需要支持未知业务模块时 THEN 必须留给 DOMC registry 和 generator adapters 相关 spec，而不是在 Spec A 中通过 prompt 自由生成最终表数据。
- R2.AC5: WHEN 生成项目、版本、拓扑、仿真会话、消息、告警、故障、事件或 stream frame 时 THEN 数据仍必须落入现有 `DemoScenarioPackage` v1 结构。

### R3: 通过语义蓝图驱动项目数据差异化
**用户故事:** 作为售前演示负责人，我希望不同业务主题的项目列表能呈现不同业务对象、负责人、部门、阶段、风险和指标，以便客户一眼感到这是自己的业务场景。
**验收标准 (EARS):**
- R3.AC1: WHEN 从 Blueprint 生成 `project.projects` 时 THEN 项目名称、描述、region、businessStage、owner、riskLevel、risk、remark 和 keyMetrics 必须来源于业务对象、persona、流程阶段、风险类型、指标定义或 story beat。
- R3.AC2: WHEN 同一场景生成多条主项目记录时 THEN 每条主记录必须绑定不同 story beat、业务对象、persona、风险或指标中的至少一种语义来源。
- R3.AC3: IF 多条项目记录只改变编号、少量关键词或 stage 顺序 THEN DiversityValidator 必须产生 warning；主演示链路达到模板化阈值时应产生 error。
- R3.AC4: WHEN 生成 owner 或部门相关字段时 THEN 不得无业务原因全部使用同一个 `createBy`、ownerRole、ownerName 或 department 语义来源。
- R3.AC5: WHEN 生成 keyMetrics 时 THEN 指标名称和值的口径必须与 Blueprint 的行业指标定义相关，不得只使用通用 `处理量`、`闭环率` 作为唯一指标集合。

### R4: 通过语义蓝图驱动 simulation 数据差异化
**用户故事:** 作为演示使用者，我希望仿真消息、告警、事件和故障能解释项目列表摘要，以便从列表进入详情、拓扑或仿真页面时数据是同一个业务故事。
**验收标准 (EARS):**
- R4.AC1: WHEN 生成 `simulation.sessions` 时 THEN session 的 stage、riskLevel 和状态必须能追溯到对应项目记录的 Blueprint story beat 或流程阶段。
- R4.AC2: WHEN 生成 `simulation.messages` 时 THEN 消息内容必须包含业务对象、角色动作、风险进展、指标变化或处理结果中的至少一种语义事实。
- R4.AC3: WHEN 生成 `simulation.alarms` 和 `simulation.faults` 时 THEN 告警或故障描述必须与对应项目风险类型一致，不能只复用项目风险原句作为全部仿真解释。
- R4.AC4: WHEN 生成 `simulation.events` 时 THEN 事件名称和 message 必须体现流程推进或角色处理动作，而不是仅使用 `${stage}节点更新` 这类通用句式。
- R4.AC5: IF 仿真数据无法解释列表摘要或项目详情中的风险、阶段、指标 THEN SemanticCoverageValidator 必须返回结构化 issue。

### R5: 保持 seed-aware 可复现与跨主题语义差异
**用户故事:** 作为维护者，我希望同一输入可稳定复现，不同业务主题又有明显差异，以便演示数据既可信又可排障。
**验收标准 (EARS):**
- R5.AC1: WHEN 生成 Blueprint 或由 Blueprint 生成 `IndustryDataDraft` 时 THEN 必须使用 `topic`、`businessDescription`、`topicKey`、`seed`、`contractFingerprint` 和 `generatorVersion` 参与确定性生成。
- R5.AC2: WHEN 同一输入组合未变化时 THEN Blueprint、Draft 和最终 v1 package 的核心语义结果必须保持稳定可复现。
- R5.AC3: WHEN `businessDescription` 变化但 `topic` 相同 THEN Blueprint 应体现业务描述中的对象、流程、风险或指标变化。
- R5.AC4: WHEN 不同业务主题生成数据时 THEN 项目标题、描述、负责人语义、阶段、风险、指标和仿真事件必须呈现可观察差异。
- R5.AC5: IF locale-aware faker 或同类能力被引入 THEN 它必须接入 seed，不得导致同一输入每次生成不同人员、组织或时间线。

### R6: 新增 DiversityValidator 检测同质化数据
**用户故事:** 作为质量负责人，我希望生成前后能自动识别模板化和重复度过高的数据，以便 official runtime package 不会把低质量主演示数据激活给客户。
**验收标准 (EARS):**
- R6.AC1: WHEN DiversityValidator 执行时 THEN 必须检查 project 主列表字段中的 name/title、description/remark、owner、department/persona、stage、risk、keyMetrics 和时间推进线索。
- R6.AC2: WHEN 文本相似度、重复字段比例、模板句式或单一分布超过阈值时 THEN validator 必须返回包含 `path`、`code`、`severity`、`actual`、`expected` 和 `fixHint` 的结构化 issue；默认阈值为关键维度 normalized duplicate ratio >=75% 或模板相似度 >=0.85 记为 error，50%-75% 记为 warning。
- R6.AC3: IF 主演示项目记录在 description/remark、risk、stage 或 owner/createBy 任一关键维度出现高度重复且无法由 Blueprint 业务事实解释 THEN DiversityValidator 必须返回 error 并阻止 active package 覆盖。
- R6.AC4: IF 非主演示字段或关键维度的轻度重复仍可由 Blueprint 业务事实解释 THEN DiversityValidator 应返回 warning，且 warning 必须进入语义质量报告。
- R6.AC5: WHEN validator 识别出可修复问题时 THEN issue 的 `fixHint` 必须能指导 AI Agent 或人工回到 Blueprint 层修复，而不是要求手改最终 `active.json`。

### R7: 新增 SemanticCoverageValidator 校验通用语义锚点范式
**用户故事:** 作为架构负责人，我希望所有由 Blueprint 派生的主演示记录都能绑定通用语义锚点，以便当前和未来模块都能用同一套范式证明列表、详情、拓扑和仿真不是互相孤立的假数据。
**验收标准 (EARS):**
- R7.AC1: WHEN 定义 SemanticCoverageValidator 时 THEN 必须采用跨模块通用语义锚点范式，锚点类型至少包含 `storyBeat`、`domainObject`、`persona`/`role`、`processStage`、`riskType` 和 `metricDefinition`。
- R7.AC2: WHEN 任一主演示主记录由 Blueprint 派生时 THEN 它必须绑定至少 3 类语义锚点，且其中必须包含 `storyBeat` 或 `domainObject` 中的至少一种。
- R7.AC3: WHEN Spec A 首批落地 `project + simulation` 时 THEN validator 只需要实现这些现有 slices 到通用语义锚点的映射，不得把语义覆盖规则写死为仅适用于项目管理模块的特殊规则。
- R7.AC4: IF 主记录摘要中的风险、阶段、指标或角色动作无法在其关联详情、拓扑、仿真或等价支撑记录中找到同一语义锚点 THEN validator 必须返回 warning；主演示链路可配置为 error。
- R7.AC5: WHEN coverage 通过时 THEN MCP 结果必须能输出每条主记录的 coverage summary，说明已绑定的语义锚点类型、锚点 ID 或可读标签，并将语义锚点绑定结果保存为 MCP artifact、meta 或 quality report，不作为浏览器 runtime 必需输入。
- R7.AC6: IF coverage 缺失是由 Blueprint 信息不足导致 THEN issue 必须指向 Blueprint path；IF 缺失是由 slice 映射丢失导致 THEN issue 必须指向对应生成映射或 package path。

### R8: 扩展 MCP 结果中的语义质量报告
**用户故事:** 作为 AI Agent 或人工修复者，我希望 MCP 在生成后返回语义质量报告，以便知道当前数据是否已经摆脱模板化，以及下一步应该修复哪里。
**验收标准 (EARS):**
- R8.AC1: WHEN MCP 生成或 dry-run runtime package 时 THEN 返回结果必须包含 Blueprint 摘要、diversity summary、semantic coverage summary、语义锚点绑定摘要和结构化 issue 列表。
- R8.AC2: WHEN runtime validation summary 仍包含 schema、contract、invariant 或 dry-run 结果时 THEN 语义质量报告不得替代这些 P0 校验结果。
- R8.AC3: IF semantic quality gate 出现 error THEN MCP 不得覆盖 active package 或 active meta。
- R8.AC4: WHEN semantic quality gate 只有 warning 时 THEN MCP 可以写入 candidate 或按既有流程继续，但必须在结果中保留 warning 与 fixHint。
- R8.AC5: WHEN 输出 artifacts 时 THEN 必须能定位生成的 candidate、active 或 meta 文件，同时避免要求用户人工编辑最终 JSON 来修复语义问题。

### R9: 保持 v1 runtime package 和现有运行时边界
**用户故事:** 作为离线包交付负责人，我希望 Spec A 提升生成质量但不改变 runtime 消费方式，以便已有 build 后替换数据能力继续稳定。
**验收标准 (EARS):**
- R9.AC1: WHEN Spec A 实现完成时 THEN `offline-static` 目标必须继续输出 v1 `active.json`、`previous.json` 和 `active.meta.json` 兼容结构。
- R9.AC2: WHEN 浏览器启动 demo-offline runtime 时 THEN runtime loader 仍只需要消费 v1 package，不得要求解析 Blueprint 文件。
- R9.AC3: WHEN 页面、MSW handler、service 或 repository 读取演示数据时 THEN 它们必须继续从 IndexedDB 或既有服务层读取，不得直接读取 Blueprint、AI 输出或 MCP 中间产物。
- R9.AC4: IF Spec A 需要持久化 Blueprint 或语义锚点绑定结果用于审计或报告 THEN 该文件只能作为 MCP artifact、meta 或 quality report 附属信息，不得成为浏览器运行时必需输入。
- R9.AC5: WHEN `real`、`fallback`、`build:prod` 或普通开发模式运行时 THEN Spec A 不得改变真实后端访问、fallback mock、生产构建或 source-generated 开发流程边界。

### R10: 建立可验证的对比验收与测试矩阵
**用户故事:** 作为验收负责人，我希望有可重复的主题对比和自动化测试，以便确认这个 spec 真正解决数据同质化，而不是只增加更多字段。
**验收标准 (EARS):**
- R10.AC1: WHEN 编写测试矩阵时 THEN 必须至少包含两个差异明显的业务主题，例如 `无人机巡检任务管理` 与 `二手电脑回收管理`。
- R10.AC2: WHEN 对比两个主题生成结果时 THEN 测试必须验证 Blueprint、project 主记录、keyMetrics 和 simulation 事件之间存在主题相关差异。
- R10.AC3: WHEN 对同一主题重复生成时 THEN 测试必须验证 seed-aware 输出稳定，不产生无原因漂移。
- R10.AC4: WHEN 运行现有 P0 质量门禁时 THEN schema validation、contract validation、invariant validation 和 import dry-run 必须继续通过。
- R10.AC5: WHEN Spec A 进入实现任务拆分时 THEN tasks 必须标注任务类别，至少覆盖 MCP generation、contract/schema、validator 和 test matrix。

## 非目标

- 不实现 v2 `active.pointer.json`、`previous.pointer.json`、manifest、release 目录或 slices。
- 不实现 DOMC registry、generator adapter registry 或缺失 DOMC blocker。
- 不实现完整 Scenario Graph、Generator Recipes、recipe expansion runtime 或少物化引擎。
- 不新增业务模块、页面、MSW handler、service/repository、IndexedDB table、后端 API 或真实生产 seed target。
- 不要求浏览器 runtime 加载 MCP server、AI provider SDK、API key 或联网生成逻辑。
- 不要求人工直接编辑最终 `active.json` 来修复语义问题；修复应回到 Blueprint 或生成规则层。
- 不替代 `demo-offline-runtime-scenario-package` P0；Spec A 只在 P0 v1 runtime package 上提升语义生成质量。

## Clarifications

### Session 2026-04-29

- Q: 第二个 spec 是否应该先做 v2 manifest/slices？ -> A: 否。先做 Spec A，解决用户可见的数据同质化；v2 manifest/slices 属于 Spec B。
- Q: Spec A 是否覆盖所有未来未知业务模块？ -> A: 否。只覆盖现有 `project + simulation` 生成模块；未知模块接入属于 DOMC registry 和 generator adapters 的后续 spec。
- Q: Spec A 是否可以依赖外部 AI？ -> A: 不可以作为必需依赖。AI 可以参与 Blueprint 生成或修复，但必须有本地 deterministic fallback，测试和 CI 不能依赖 API key 或联网。
- Q: Spec A 是否改变 runtime package 格式？ -> A: 不改变。继续输出 v1 `active.json`，页面、MSW、service/repository 和 IndexedDB 消费路径不变。
- Q: 本 spec 的主要成功标准是什么？ -> A: 同一输入可复现，不同业务主题有明显语义差异，主演示列表不再出现模板化同质数据，并且质量报告能指出可修复问题。
- Q: Business Blueprint 的语义最小集应该量化到什么程度？ -> A: 采用平衡阈值：业务对象 >=5、persona >=3、部门 >=2、流程阶段 >=5、风险类型 >=4、指标定义 >=4、story beats >= projectCount。
- Q: DiversityValidator 的 error 阈值应该多严格？ -> A: 采用平衡策略：主演示项目中 description/remark、risk、stage 或 owner/createBy 任一关键维度高度重复时 error；非关键或可解释的轻度重复保留为 warning。
- Q: DiversityValidator 中的“高度重复”默认如何量化？ -> A: 采用平衡量化规则：关键维度 normalized duplicate ratio >=75% 或模板相似度 >=0.85 记为 error；50%-75% 记为 warning。
- Q: SemanticCoverageValidator 应该采用哪种范式边界？ -> A: 采用通用语义锚点范式：所有主演示主记录都应绑定 `storyBeat`、`domainObject`、`persona`、`processStage`、`riskType`、`metricDefinition` 等语义锚点；Spec A 只实现 `project + simulation` 的首个映射。
- Q: 语义锚点绑定结果应该保存在哪里？ -> A: 保存为 MCP artifact、meta 或 quality report，不作为浏览器 runtime 必需输入；后续是否进入 manifest、DOMC 或 graph 由后续 specs 决定。

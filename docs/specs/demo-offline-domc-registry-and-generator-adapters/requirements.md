# Demo Offline DOMC Registry and Generator Adapters 需求规格

## 简介

`demo-offline-domc-registry-and-generator-adapters` 是 `Demo Offline Semantic Data Platform` 的第四个正式 spec，也是第三个实现 spec。父级总纲为 `demo-offline-semantic-data-platform`，`platformLayer` 是 `DOMC`。上游依赖为已完成的 `demo-offline-semantic-blueprint-generation` 语义生成能力和已完成的 `demo-offline-runtime-package-v2-manifest-slices` v2 Release Store 能力；历史 P0 `demo-offline-runtime-scenario-package` 中的 module contract、IndexedDB mapping、handler coverage、invariants 和 generator adapter 版本是本 spec 的迁移来源。

当前实现已经具备 `DemoOfflineContractManifest`、`DEMO_INDEXED_DB_MAPPING`、`DEMO_MODULE_CONTRACTS`、handler coverage、semantic quality report 和 v2 manifest/provenance，但“哪些业务模块可以生成、为什么可以生成、由哪个生成器生成、缺什么必须 blocker”仍散落在硬编码类型、扫描结果和 `project + simulation` 专用编译链路里。`tools/demo-offline-mcp/src/offline-static/generate.ts` 仍固定生成 `project`、`simulation` 并复制 `auth`、`system`；`tools/demo-offline-mcp/src/types.ts` 仍把 `DemoGeneratableSlice` 固定为 `project | simulation`；`ruoyi-fastapi-frontend/src/demo/scenarios/contract.ts` 中的 module contract 还偏摘要，尚未表达字段语义、UI journey、adapter capability、diversity rules、materialization policy 和缺失接入 blocker。

本 spec 的目标是把 P0 contract summary 升级为版本化、机器可读、可 fingerprint、可随 dist 导出的 DOMC Registry，并把现有 `project + simulation` 生成链路迁移为第一批正式 Generator Adapter。DOMC Registry 的源码事实源采用 curated TypeScript，放在 `ruoyi-fastapi-frontend/src/demo/domc/**` 或等价前端源码目录中，由 build/exporter 导出 JSON 到 `demo-contract/**`；浏览器 runtime 不加载 TypeScript registry 或 adapter 实现。Generator Adapter 的输出边界采用 sourcePath 级 materializations 与 semantic bindings，由共享 assembler 组装 `DemoScenarioPackage`，不得让每个 adapter 直接拼完整 runtime package。Generator Adapter 的实现代码限定在 MCP 侧，例如 `tools/demo-offline-mcp/src/adapters/**`；前端 DOMC 只声明 adapter id、version 和 capability。之后新增业务模块不再通过 prompt 或硬编码白名单伪装支持，而必须先交付 DOMC、IndexedDB mapping、handler/service/repository 证据、UI journey、invariants、diversity rules 和 generator adapter；缺任一关键能力时 MCP 必须返回结构化 blocker。

本 spec 新增或强化的 `qualityGates` 为 `domc-schema`、`domc-registry-integrity`、`domc-fingerprint`、`adapter-registry`、`adapter-capability`、`module-blocker`、`ui-journey-coverage`、`handler-mapping-coverage`、`contract-drift`、`domc-provenance` 和 `adapter-regression`。它不重新定义 v2 pointer/manifest/slices 文件格式，不实现完整 Scenario Graph，不实现 Generator Recipes 展开引擎，不新增真实后端 seed target，不要求浏览器 runtime 加载 MCP、AI provider 或 adapter 代码。

## 需求列表

### R1: 建立版本化 DOMC Registry 作为模块接入事实源
**用户故事:** 作为 demo-offline 架构负责人，我希望业务模块接入能力由版本化 DOMC Registry 表达，以便 MCP 不再依赖硬编码 safe slices 或 prompt 判断模块是否可生成。
**验收标准 (EARS):**
- R1.AC1: WHEN Spec C 实现 DOMC Registry 时 THEN 必须新增以 `ruoyi-fastapi-frontend/src/demo/domc/**` 或等价前端源码目录为事实源的 curated TypeScript registry，并至少包含 registry schemaVersion、registryVersion、generatedAt、domcFingerprint、module contracts、adapter references、quality gates 和迁移来源信息。
- R1.AC2: WHEN registry 描述模块时 THEN 每个模块必须有稳定 `moduleId`、`moduleVersion`、`lifecycle`、`capability`、`sourcePaths`、`indexedDbTables`、`handlerCoverage`、`uiJourneys`、`entities`、`invariants`、`diversityRules` 和 `adapterId` 或明确的 `copyOnly`/`unsupported` 状态。
- R1.AC3: WHEN 构建 `dist-demo-offline` 时 THEN DOMC Registry 必须从 curated TypeScript 源码导出为 JSON 到 `demo-contract/**` 或等价 contract 输出中，并参与 demo-offline contract fingerprint 计算。
- R1.AC4: IF DOMC Registry schema、moduleId、sourcePath、table mapping 或 adapter reference 无效 THEN build/exporter 或 MCP contract reader 必须返回 error 级结构化 issue。
- R1.AC5: WHEN DOMC Registry 与现有 `DemoOfflineContractManifest` 共存时 THEN registry 必须从 P0 `moduleContracts`、IndexedDB mapping、handler coverage 和 invariants 演进，不得另起一套与 runtime contract 冲突的 prompt 约定。

### R2: 定义 DOMC 模块契约的最小完整内容
**用户故事:** 作为业务模块开发者，我希望 DOMC 明确写出页面、接口、数据、状态和语义约束，以便新增模块是否能生成 demo-offline 数据可以被稳定审查。
**验收标准 (EARS):**
- R2.AC1: WHEN DOMC 描述实体时 THEN 必须至少包含 entity 名称、sourcePath、IndexedDB table、primaryKey、requiredFields、nullable/optional 字段边界、references、minItems 和 record ownership 规则。
- R2.AC2: WHEN DOMC 描述字段语义时 THEN 必须区分 identifier、displayName、description、status、enum、timestamp、owner/persona、department、metric、risk、money、quantity、foreignKey 和 opaque payload 等语义类别。
- R2.AC3: WHEN DOMC 描述状态机或枚举时 THEN 必须包含允许状态、状态转移、默认状态、终态、非法组合和缺省修复策略。
- R2.AC4: WHEN DOMC 描述 UI journey 时 THEN 必须至少列出主演示入口、列表字段、详情支撑数据、关键操作的 demo 行为、空态/错误态和最低可演示链路。
- R2.AC5: IF 某模块缺少实体、sourcePath、handler coverage、UI journey、invariants 或 adapter capability 中任一关键字段 THEN 该模块不得标记为 `generatable`。

### R3: 将现有 project 和 simulation 迁移为第一批正式 DOMC
**用户故事:** 作为当前 demo-offline 维护者，我希望先把已经可生成的 project 和 simulation 变成正式 DOMC，以便 Spec C 不扩大模块范围也能建立长期扩展骨架。
**验收标准 (EARS):**
- R3.AC1: WHEN Spec C 首批落地时 THEN `project` 和 `simulation` 必须作为第一批 `generatable` DOMC，从现有 `DEMO_MODULE_CONTRACTS`、`DEMO_INDEXED_DB_MAPPING`、handler coverage、runtime invariants 和 semantic anchor bindings 迁移。
- R3.AC2: WHEN 迁移 `project` DOMC 时 THEN 必须覆盖 `project.projects`、`project.versions`、`project.topologies` 的主键、引用、最小记录量、页面 journey、字段语义、diversity rules 和 adapter 输出边界。
- R3.AC3: WHEN 迁移 `simulation` DOMC 时 THEN 必须覆盖 `simulation.sessions`、`simulation.messages`、`simulation.bandwidth`、`simulation.alarms`、`simulation.faults`、`simulation.events`、`simulation.streamFrames` 的 session 引用、时间线顺序、风险解释和详情支撑关系。
- R3.AC4: WHEN `auth` 和 `system` 模块进入 registry 时 THEN 它们应默认标记为 `copyOnly` 或等价状态，并继续从 bundle default/default scenario 复制，不得由 Spec C 伪装成语义生成模块。
- R3.AC5: IF 迁移后的 project/simulation DOMC 与当前 contract manifest、scenario schema、handler coverage 或 import dry-run 不一致 THEN adapter-regression 或 contract-drift gate 必须失败。

### R4: 建立 Generator Adapter 注册和选择机制
**用户故事:** 作为 MCP 工具维护者，我希望每个可生成模块都有明确 adapter，以便生成逻辑可以按模块扩展，而不是继续把所有逻辑写进一个 project/simulation 专用 compiler。
**验收标准 (EARS):**
- R4.AC1: WHEN 定义 Generator Adapter 接口时 THEN 必须至少包含 adapterId、adapterVersion、supportedModules、supportedDomcVersions、capabilities、inputKinds、outputSourcePaths、canGenerate、plan、compile、validate 和 explainBlocker 或等价职责，且 `compile` 输出必须是 sourcePath 级 materializations 与 semantic bindings。
- R4.AC2: WHEN MCP 根据用户输入和 DOMC Registry 创建生成计划时 THEN 必须通过 adapter registry 选择可用 adapter，而不是只读取硬编码 `DemoGeneratableSlice = 'project' | 'simulation'`。
- R4.AC3: WHEN 一个 adapter 生成多个 sourcePath 时 THEN 它必须声明输出顺序、跨 sourcePath 引用规则、最小记录量和可复现 seed 输入；共享 assembler 负责把 materializations 组装为 `DemoScenarioPackage` 或等价 importer 输入。
- R4.AC4: IF 多个 adapter 声明支持同一 module/sourcePath THEN MCP 必须按显式优先级或版本约束选择，并在结果中记录选择原因；无法唯一选择时返回 blocker。
- R4.AC5: WHEN adapter 版本、DOMC fingerprint 或 contract fingerprint 变化时 THEN v2 release provenance 必须记录对应版本和 fingerprint，便于复现和回滚。
- R4.AC6: IF adapter 试图直接输出完整 `DemoScenarioPackage`、直接写 v2 release 文件或绕过共享 assembler THEN adapter-registry gate 必须返回 error。
- R4.AC7: WHEN adapter 实现代码被组织时 THEN 它必须位于 MCP 侧，例如 `tools/demo-offline-mcp/src/adapters/**`；前端 DOMC 只能声明 adapter 引用和能力，不得包含可执行生成器实现。

### R5: 用 DOMC 驱动生成计划和缺失能力 blocker
**用户故事:** 作为 AI Agent 使用者，我希望 MCP 能明确告诉我哪些模块可生成、哪些只能复制、哪些缺能力被阻止，以便我不会误以为任意业务主题都能被自由生成。
**验收标准 (EARS):**
- R5.AC1: WHEN 用户要求生成 demo-offline runtime package 时 THEN MCP 生成计划必须从 DOMC Registry 读取模块状态，并输出 `generate`、`copy`、`unsupported` 或 `blocked` 的模块级 trace。
- R5.AC2: WHEN 用户要求“全量”、“全模块”、“整站”或暗示未接入业务模块时 THEN MCP 不得自由编造最终表数据，必须返回包含缺失 DOMC、缺失 adapter、缺失 handler、缺失 IndexedDB mapping 或缺失 UI journey 的结构化 blocker。
- R5.AC3: IF 一个目标模块存在 DOMC 但缺少兼容 generator adapter 且不属于 `copyOnly` THEN MCP 必须执行 strict blocker，禁止生成、发布和激活，并说明必须先实现 adapter。
- R5.AC4: IF 一个目标模块存在 adapter 但 DOMC lifecycle 不是 `active` 或 adapter capability 不满足目标 target THEN MCP 必须执行 strict blocker，禁止生成、发布和激活，并给出 fixHint。
- R5.AC5: WHEN blocker 返回给用户或 AI Agent 时 THEN blocker 必须包含 path、code、severity、actual、expected、fixHint、missingArtifacts 和 nextActions，不得只输出自然语言失败原因。
- R5.AC6: IF 某模块无兼容 adapter THEN MCP 不得使用 generic fallback adapter、低置信模板数据或 warning-only 继续生成该模块；唯一允许的非阻塞路径是该模块明确声明为 `copyOnly` 并从已验证默认场景复制。

### R6: 扩展 contract/schema 校验以覆盖 DOMC 完整性和漂移
**用户故事:** 作为质量负责人，我希望 DOMC 与代码、schema、handler 和 IndexedDB mapping 之间的漂移能自动发现，以便模块契约不会逐渐失真。
**验收标准 (EARS):**
- R6.AC1: WHEN build/exporter 生成 demo contract 时 THEN 必须校验 DOMC sourcePath 均能映射到 `DemoScenarioPackage` schema 和 IndexedDB table mapping，且 adapter materialization 输出只能落在这些声明过的 sourcePath 中。
- R6.AC2: WHEN DOMC 声明 handler coverage 时 THEN 必须校验 handler source、apiPrefix、coveredRoutes 和 unsupportedBehavior 与现有 demo handler 约定可对齐。
- R6.AC3: WHEN DOMC 声明 UI journey 时 THEN 必须至少校验 journey 引用的 module、sourcePath、primary entity 和 required support entity 存在。
- R6.AC4: WHEN MCP 读取离线壳的 `demo-contract/**` 时 THEN 必须重新校验 DOMC Registry fingerprint、contract fingerprint 和 adapter registry compatibility。
- R6.AC5: IF DOMC 与 scenario schema、contract manifest、v2 slice descriptor sourcePath 或 import dry-run 结果发生漂移 THEN contract-drift gate 必须返回 error 并禁止发布或激活 release。

### R7: 统一 DOMC 与 Spec A 语义锚点、diversity 和 coverage 规则
**用户故事:** 作为语义质量维护者，我希望 DOMC 能承接 Spec A 的通用语义锚点范式，以便未来新增模块也能证明列表、详情和支撑记录是同一个业务故事。
**验收标准 (EARS):**
- R7.AC1: WHEN DOMC 定义 semantic anchors 时 THEN 必须支持 `storyBeat`、`domainObject`、`persona`、`role`、`processStage`、`riskType`、`metricDefinition` 等 Spec A 已定义的通用锚点类型。
- R7.AC2: WHEN DOMC 定义 diversity rules 时 THEN 必须能按模块指定主记录字段、关键维度、重复阈值、模板相似度阈值、warning/error 级别和可解释重复例外。
- R7.AC3: WHEN adapter 生成主记录和支撑记录时 THEN 必须随 sourcePath materializations 输出或保存符合 DOMC 的 anchor binding summary，供 SemanticCoverageValidator 或后续 validator 使用。
- R7.AC4: IF 某模块的主记录不能绑定 DOMC 要求的最低语义锚点数量或支撑记录类别 THEN semantic-coverage 或 ui-journey-coverage gate 必须返回结构化 issue。
- R7.AC5: WHEN DOMC 被用于非 project/simulation 模块时 THEN validation 规则必须保持跨模块通用，不得把锚点校验写死为项目管理专用路径。

### R8: 保持 v2 Release Store 边界并扩展 provenance 记录
**用户故事:** 作为离线包交付负责人，我希望 DOMC 与 adapter 信息进入 v2 release 的审计链路，但不改变浏览器 runtime 的数据读取模型。
**验收标准 (EARS):**
- R8.AC1: WHEN MCP 写入 v2 release 时 THEN manifest/provenance 必须记录 domcRegistryFingerprint、moduleContractFingerprints、adapterVersions 和 adapter capability summary 或等价审计信息。
- R8.AC2: WHEN v2 release materialize slices 时 THEN descriptor 的 sourcePath、module、materializationReason 必须能追溯到 DOMC module contract 或 copyOnly 规则。
- R8.AC3: WHEN runtime loader 加载 v2 release 时 THEN 页面、MSW、service、repository 仍不得直接读取 DOMC Registry、adapter 代码、Blueprint、graph 或 recipe 文件。
- R8.AC4: IF release 中的 DOMC fingerprint 与当前离线壳 contract 不兼容 THEN MCP validate/dry-run/activate 必须失败；runtime 对已发布 release 的处理应遵循现有 contract/hash/import fallback 机制。
- R8.AC5: WHEN DOMC 信息作为 artifact 写入 release 时 THEN 不得写入本机绝对路径、API key、私密数据或远程 `$ref`，并必须通过现有 release export safety gate。

### R9: 明确不实现 Scenario Graph 和 Generator Recipes
**用户故事:** 作为项目负责人，我希望 Spec C 只解决模块接入契约和 adapter 扩展点，以便不会再次变成跨 Blueprint、v2、DOMC、Graph、Recipes 的巨型 spec。
**验收标准 (EARS):**
- R9.AC1: WHEN Spec C 定义 DOMC 时 THEN 可以引用 semantic anchors、UI journey 和 support relationships，但不得要求实现完整 Scenario Graph 数据结构或图查询引擎。
- R9.AC2: WHEN Spec C 定义 adapter 时 THEN adapter 可以物化当前必要 slices，但不得实现 Generator Recipes 展开 runtime 或低物化引擎。
- R9.AC3: WHEN manifest 为未来 graph/recipe artifact 预留 descriptor 时 THEN Spec C 不得改变 Spec B 已批准的 v2 pointer、manifest、slice 和 fallback 文件格式。
- R9.AC4: IF 某项需求需要跨模块业务关系图、recipe expansion dry-run 或 MCP/runtime 展开等价性 THEN 必须推迟到 `demo-offline-scenario-graph-and-recipes` 或新的后续 spec。
- R9.AC5: WHEN tasks 拆分时 THEN 不得要求新增 Vue 页面、真实后端 seed target、生产模式数据生成或浏览器端 AI/adapter 执行能力。

### R10: 建立新增业务模块 Definition of Done
**用户故事:** 作为业务模块开发者，我希望新增模块有明确 demo-offline 接入完成标准，以便以后支持未知业务时不靠临时约定和口头判断。
**验收标准 (EARS):**
- R10.AC1: WHEN 新业务模块希望成为 `generatable` THEN 必须提交 DOMC、scenario slice/schema、IndexedDB mapping、repository/service 读取链路、MSW handler coverage、UI journey、invariants、diversity rules 和 generator adapter。
- R10.AC2: WHEN 新业务模块只希望保留默认数据 THEN 可以声明 `copyOnly`，但必须说明复制来源、最小记录量、handler coverage 和不允许语义生成的原因。
- R10.AC3: WHEN 新业务模块暂不支持 demo-offline 生成 THEN 必须在 registry 或扫描诊断中表现为 `unsupported`/`blocked`，并说明接入缺口。
- R10.AC4: IF 模块 DOMC 或 adapter 未通过 schema、contract、invariant、ui journey、semantic coverage 和 import dry-run 相关 gate THEN 不得把该模块加入 generatedModules。
- R10.AC5: WHEN Definition of Done 通过时 THEN docs/specs 或模块文档必须说明该模块 DOMC 的 owner、维护路径、adapter id、测试证据和回归命令。

### R11: 建立 DOMC 和 adapter 的测试矩阵
**用户故事:** 作为验收负责人，我希望 Spec C 的测试能证明 registry、adapter、blocker 和 v2 provenance 都稳定工作，以便后续模块扩展不会破坏现有 demo-offline。
**验收标准 (EARS):**
- R11.AC1: WHEN 编写 contract/schema tests 时 THEN 必须覆盖 DOMC Registry schema、fingerprint 稳定性、sourcePath/table mapping 对齐、handler coverage 对齐和 invalid DOMC error。
- R11.AC2: WHEN 编写 adapter registry tests 时 THEN 必须覆盖 adapter 注册、版本兼容、capability 匹配、多 adapter 冲突、缺 adapter blocker 和 copyOnly 模块处理。
- R11.AC3: WHEN 编写 MCP generation tests 时 THEN 必须覆盖 project/simulation 通过 DOMC adapter 生成、auth/system copyOnly、全模块请求 blocker、未知模块 blocker 和结构化 nextActions。
- R11.AC4: WHEN 编写 v2 release tests 时 THEN 必须覆盖 provenance 中 DOMC/adapter fingerprint 记录、descriptor sourcePath 追溯、contract drift 阻止 activation 和 warning-only gate 保留。
- R11.AC5: WHEN 本 spec 完成实现验收时 THEN 必须至少运行 `cd tools/demo-offline-mcp && npm test -- --run`、受影响的 frontend contract/runtime tests，以及类型检查；若上游已有 MCP 编译阻塞，必须先修复再记录 Spec C 验收。

### R12: 保持安全、离线和运行时隔离边界
**用户故事:** 作为安全维护者，我希望 DOMC 与 adapter 只在构建/MCP 侧运行，以便客户浏览器离线包不携带生成器、密钥或远程依赖。
**验收标准 (EARS):**
- R12.AC1: WHEN 浏览器运行 `demo-offline` runtime 时 THEN 不得加载 MCP server、Generator Adapter 实现、AI provider SDK、API key、远程 registry 或需要联网的 schema 引用；build 产物不得把 `tools/demo-offline-mcp/src/adapters/**` 或等价 adapter 实现打入浏览器 bundle。
- R12.AC2: WHEN DOMC、adapter result、quality report 或 provenance 被写入 release artifact 时 THEN 必须复用或强化现有 export safety 检查，拒绝本机绝对路径、secret-like 值和远程 `$ref`。
- R12.AC3: WHEN adapter 接收 Business Blueprint、topic 或 businessDescription 时 THEN 不得把未经校验的 AI 输出直接写入最终 table record，必须通过 DOMC schema、adapter validation 和质量 gate。
- R12.AC4: IF adapter 需要非确定性 faker、随机数或时间 THEN 必须接入 seed、contractFingerprint、domcFingerprint 和 adapterVersion，保证同一输入可复现。
- R12.AC5: WHEN `real`、`fallback`、`build:prod` 或普通开发模式运行时 THEN DOMC Registry 和 adapter 改造不得改变真实后端访问、fallback mock、生产构建和非 demo-offline 行为。

## 非目标

- 不重新定义 v2 `active.pointer.json`、`previous.pointer.json`、manifest、release 目录、slice descriptor、timeline 或 bundle-default fallback 格式。
- 不实现完整 Scenario Graph、Generator Recipes、recipe expansion runtime、少物化展开引擎或 MCP/runtime 展开等价校验。
- 不新增真实后端 API seed target，不把 demo-offline 生成能力扩展到生产数据初始化。
- 不要求浏览器 runtime 加载 MCP server、AI provider SDK、API key、Generator Adapter 实现或远程 registry。
- 不一次性要求所有现有业务模块都完成 DOMC；首批只把 project/simulation 迁移为 generatable DOMC，把 auth/system 标记为 copyOnly，并为其他模块提供 blocker/unsupported 机制。
- 不通过 prompt 自由生成缺 DOMC 或缺 adapter 的模块最终表数据。
- 不要求人工直接编辑 v2 release slice 或最终 JSON 来修复契约问题；修复应回到 DOMC、adapter、Blueprint 或生成规则层。
- 不替代 Spec A 的 Business Blueprint 和语义质量报告；Spec C 只承接其锚点范式和质量门禁扩展点。
- 不替代 Spec B 的 Release Store；Spec C 只把 DOMC/adapter fingerprint 和审计信息接入已批准的 v2 release 链路。

## Clarifications

### Session 2026-04-29

- Q: Spec C 是否要一次性支持所有未知业务模块？ -> A: 否。首批只正式接入已有 project/simulation 生成能力，auth/system 保持 copyOnly，其他模块缺 DOMC 或缺 adapter 时必须 blocker。
- Q: DOMC Registry 是不是从零开始的新契约？ -> A: 否。它必须从 P0 `DemoOfflineContractManifest`、module contract summary、IndexedDB mapping、handler coverage 和 invariants 演进。
- Q: Spec C 是否改变 v2 runtime package 文件格式？ -> A: 不改变。只在 contract/provenance/artifact 层记录 DOMC/adapter 信息，并保持页面、MSW、service/repository 继续消费 IndexedDB。
- Q: Spec C 是否实现 Scenario Graph 或 Recipes？ -> A: 不实现。DOMC 可以描述 UI journey 和 support relationships，但完整 graph/recipe 能力留给 Spec D。
- Q: 缺少 DOMC 的模块能不能让 AI 直接补最终 JSON？ -> A: 不能。必须返回结构化 blocker，指出缺 contract、mapping、handler、repository/service、UI journey、invariant 或 adapter。
- Q: 当前 MCP 全套测试已有编译阻塞怎么办？ -> A: 该阻塞不是 Spec C 的功能范围，但进入 Spec C 实现验收前必须先修复，否则无法用 MCP 回归结果证明 adapter-regression gate。
- Q: DOMC Registry 的源码事实源应该放在哪里？ -> A: 采用 curated TypeScript + JSON export；源码放在 `ruoyi-fastapi-frontend/src/demo/domc/**` 或等价前端源码目录，build 导出机器可读 registry 到 `demo-contract/**`。
- Q: Generator Adapter 的输出边界应该是什么？ -> A: Adapter 输出 sourcePath 级 materializations 和 semantic bindings，由共享 assembler 组装 `DemoScenarioPackage`；不得让 adapter 直接拼完整 runtime package。
- Q: Generator Adapter 的实现代码应该放在哪里？ -> A: Adapter 实现只放 MCP 侧，例如 `tools/demo-offline-mcp/src/adapters/**`；前端 DOMC 只声明 adapter id、version 和 capability。
- Q: MCP 侧 adapter 未覆盖某模块时，默认响应策略应该是什么？ -> A: 采用 strict blocker；除明确 `copyOnly` 模块可复制默认数据外，无兼容 adapter 或 capability 不匹配时禁止生成、发布和激活。

# Demo Offline Semantic Data Platform 需求规格

## 简介

当前 `demo-offline-runtime-scenario-package` 已经把客户行业数据从编译期 TS scenario 推进到 build 后可替换的 runtime JSON package，解决了“通用 `dist-demo-offline` 程序壳 + 现场替换 `demo-scenarios/active.json`”的交付问题。但该能力仍停留在“生成最终表数据 JSON”的阶段，长期会暴露两个核心风险：

1. 数据规模继续增长后，单个 `active.json` 难以 review、局部更新、局部回滚和定位差异。
2. 业务数据仍容易同质化，表现为标题和编号变化，但描述、人员、时间、流程阶段、风险和指标仍像模板换壳。

本需求定义 `Demo Offline Semantic Data Platform` 的架构治理基线。它不是一次产品代码实现大包，而是为后续正式 specs 约束共同语言、演进顺序、兼容策略、质量闸门和职责边界。后续 `Business Blueprint`、`Runtime Package v2 Manifest/Slices`、`DOMC Registry`、`Scenario Graph/Recipes` 等能力必须在本总纲约束下分别拆分为独立 spec。

Spec 0 的交付成果是 `requirements.md`、`design.md`、`tasks.md` 三件套及必要的 specs 索引更新；它不直接实现 MCP v2、不改 runtime loader、不新增 DOMC registry、不引入 recipe 展开引擎。

## 需求列表

### R1: 建立 semantic data platform 总纲和治理边界
**用户故事:** 作为 demo-offline 架构负责人，我希望有一份轻量但正式的总纲 spec，以便后续数据生成、分片、契约和质量校验能力不会各自演进成互相冲突的方案。
**验收标准 (EARS):**
- R1.AC1: WHEN 创建 `demo-offline-semantic-data-platform` spec 时 THEN 必须按仓库规范生成 `requirements.md`、`design.md`、`tasks.md` 三件套。
- R1.AC2: WHEN 编写 Spec 0 内容时 THEN 必须明确它是架构治理基线，而不是 MCP/runtime/DOMC/recipe 的产品代码实现 spec。
- R1.AC3: WHEN 后续 demo-offline semantic specs 被创建时 THEN 它们必须引用 Spec 0 并说明自身在总纲中的位置、上游依赖和非目标。
- R1.AC4: IF 后续 spec 需要改变 Spec 0 已批准的架构边界 THEN 必须先修订 Spec 0 或在新 spec 中记录明确的兼容例外。
- R1.AC5: WHEN Spec 0 完成时 THEN 必须能作为 Spec A/B/C/D 的共同术语表和顺序基线使用。

### R2: 保持 v1 runtime package 兼容并定义 v2 旁路演进原则
**用户故事:** 作为离线演示交付负责人，我希望长期平台化改造不推翻现有 runtime JSON package，以便已完成的 build 后换数据能力可以继续稳定交付。
**验收标准 (EARS):**
- R2.AC1: WHEN 后续 specs 设计 v2 runtime package 时 THEN 必须保留 v1 `active.json` 作为兼容输入格式。
- R2.AC2: WHEN v2 manifest/slices/pointer 能力被设计时 THEN 它必须作为旁路新增能力接入，不得要求页面、MSW handler 或 service 直接消费 v2 文件。
- R2.AC3: IF v2 pointer、manifest、slice 或 recipe 展开失败 THEN runtime fallback 策略必须继续覆盖 previous v2、v1 previous、bundle default 或等价安全降级路径。
- R2.AC4: WHEN `real`、`fallback`、`build:prod` 或普通开发模式运行时 THEN semantic data platform 不得改变真实后端访问、开发态 fallback mock 或生产构建行为。
- R2.AC5: WHEN `source-generated` 开发流程仍被使用时 THEN 它必须作为开发测试、场景固化和回归入口保留，不得被 Spec 0 或后续 v2 方案强制移除。

### R3: 明确 AI、MCP、compiler、runtime、MSW 和 IndexedDB 的职责边界
**用户故事:** 作为系统维护者，我希望每一层只承担适合自己的职责，以便离线演示数据既能语义丰富，又不会把 AI 生成风险带入浏览器运行时或页面代码。
**验收标准 (EARS):**
- R3.AC1: WHEN AI Agent 参与生成流程时 THEN 它只能生成业务语义层输入，例如 Business Blueprint、语义事实、故事线、术语或修复建议。
- R3.AC2: WHEN 最终 runtime package 或 IndexedDB 记录被生成时 THEN ID、时间、状态、跨表引用、默认字段、hash 和可复现性必须由 compiler、adapter、recipe 或 validator 控制。
- R3.AC3: WHEN runtime 启动演示数据时 THEN 它必须继续通过场景导入路径写入 IndexedDB，页面、service 和 repository 不得直接解析 AI 输出。
- R3.AC4: WHEN MSW handler 处理 demo-offline API 请求时 THEN 它必须继续作为薄适配层读取 service/repository，不得读取 `demo-scenarios/**`、manifest、slice、blueprint 或 recipe 文件。
- R3.AC5: WHEN 浏览器运行客户离线包时 THEN 不得加载 MCP server、AI provider SDK、API key 或任何要求联网才能完成生成的逻辑。

### R4: 定义平台核心组件和术语契约
**用户故事:** 作为后续 specs 的作者，我希望有稳定的组件术语和边界，以便 Blueprint、Graph、Recipes、DOMC、Manifest/Slices 和 Quality Gates 不会在不同 spec 中含义漂移。
**验收标准 (EARS):**
- R4.AC1: WHEN Spec 0 进入 design 阶段 THEN 必须定义 DOMC、Business Blueprint、Scenario Graph、Generator Recipes、Runtime Package v2、Quality Gates 的职责边界。
- R4.AC2: WHEN 后续 spec 使用 Business Blueprint 术语时 THEN 它必须表示 AI 可生成的小而精业务语义层，不得表示最终业务表数据。
- R4.AC3: WHEN 后续 spec 使用 Scenario Graph 术语时 THEN 它必须表示角色、流程、对象、事件、风险、指标和 UI journey 之间可验证的关系图。
- R4.AC4: WHEN 后续 spec 使用 Generator Recipes 术语时 THEN 它必须表示可由 seed、blueprint facts、graph facts 和参数确定性展开的派生数据生成规则。
- R4.AC5: WHEN 后续 spec 使用 DOMC 术语时 THEN 它必须表示业务模块接入 demo-offline 数据生成平台的机器可读契约，不得退化为 prompt 约定。
- R4.AC6: WHEN 后续 spec 使用 Quality Gates 术语时 THEN 它必须至少覆盖 schema、contract、invariant、diversity、semantic coverage、UI journey、recipe expansion、import dry-run 和 hash 校验的关系。

### R5: 规定后续 specs 的拆分顺序和范围约束
**用户故事:** 作为项目负责人，我希望平台化能力按收益和风险分层推进，以便先解决用户可见的数据同质化，再处理文件膨胀和长期模块接入。
**验收标准 (EARS):**
- R5.AC1: WHEN Spec 0 记录后续路线时 THEN 必须将 `demo-offline-semantic-blueprint-generation` 定义为第一份实现 spec。
- R5.AC2: WHEN Spec A 被创建时 THEN 它必须优先解决业务语义蓝图、seed-aware 生成、DiversityValidator 和 SemanticCoverageValidator，并继续输出 v1 `active.json`。
- R5.AC3: WHEN Spec B 被创建时 THEN 它必须聚焦 v2 pointer、manifest、slices、hash、release 目录、pointer fallback 和 import dry-run，不得夹带完整 DOMC registry。
- R5.AC4: WHEN Spec C 被创建时 THEN 它必须聚焦 DOMC registry、module contract、generator adapter 和缺失 DOMC blocker，不得重新定义 v2 runtime package 文件格式。
- R5.AC5: WHEN Spec D 被创建时 THEN 它必须聚焦 Scenario Graph、Generator Recipes、少物化策略和 recipe 展开校验，不得阻塞 Spec A 的短期语义质量收益。
- R5.AC6: IF 后续任一 spec 试图同时实现 Blueprint、v2 分片、DOMC registry、Graph 和 Recipes THEN 必须拆分范围，避免形成不可验收的巨型 spec。

### R6: 建立质量闸门族和失败处理原则
**用户故事:** 作为质量负责人，我希望 official runtime package 激活前有分层质量闸门，以便坏数据、模板化数据、跨页面不一致数据和不可导入数据不能进入正式演示。
**验收标准 (EARS):**
- R6.AC1: WHEN 后续 spec 定义 official package 激活流程时 THEN 必须说明 schema validation、contract validation、invariant validation 和 import dry-run 的执行顺序。
- R6.AC2: WHEN 后续 spec 定义语义质量检查时 THEN 必须包含 diversity validation 和 semantic coverage validation，不得只检查字段类型和跨表引用。
- R6.AC3: WHEN 后续 spec 定义 UI journey coverage 时 THEN 必须验证主演示页面链路所需的列表、详情、拓扑、仿真或未来业务页面数据是否彼此支撑。
- R6.AC4: WHEN 后续 spec 定义 recipe 能力时 THEN 必须包含 recipe expansion dry-run 或等价校验，确保 MCP dry-run 与 runtime 导入展开结果一致或可解释等价。
- R6.AC5: IF 任一 error 级质量闸门失败 THEN MCP 或 runtime 不得覆盖 active package 或 active pointer。
- R6.AC6: WHEN 质量闸门产生 warning 时 THEN 必须记录结构化 issue、path、code、severity 和 fixHint，供 AI Agent 或人工修复。

### R7: 管控文件膨胀、物化边界和局部维护能力
**用户故事:** 作为维护者，我希望长期场景包既能承载更大业务数据，又能保持可 review、可局部更新和可回滚，以便离线包不会重新变成一个无法维护的大 JSON。
**验收标准 (EARS):**
- R7.AC1: WHEN 后续 spec 设计 runtime package v2 时 THEN 必须使用 manifest、release、slice 和 pointer 或等价结构支持局部 review 与局部回滚。
- R7.AC2: WHEN 数据可由 seed、blueprint、graph 或 recipe 确定性推导时 THEN 后续 spec 必须优先考虑 recipe 表达，而不是无理由全量物化进 JSON。
- R7.AC3: WHEN 某类数据必须物化时 THEN manifest 或等价元数据必须记录 materialization reason、schemaVersion、hash 和所属模块。
- R7.AC4: WHEN 单个 slice 超过可 review 尺寸时 THEN 后续 spec 必须定义继续按 table、page、journey 或时间窗口拆分的策略。
- R7.AC5: IF 仅通过 gzip、br 或其他压缩方式降低传输体积 THEN 不得视为解决 review、diff、局部修复、局部回滚和生成质量问题。

### R8: 建立语义差异和可复现生成原则
**用户故事:** 作为售前演示负责人，我希望不同业务主题生成出的数据具有真实业务差异，同时同一输入又能稳定复现，以便演示既可信又可排障。
**验收标准 (EARS):**
- R8.AC1: WHEN 后续 spec 定义生成输入时 THEN 必须区分 topic、businessDescription、topicKey、seed、contractFingerprint 和 generatorVersion 的职责。
- R8.AC2: WHEN 同一 topicKey、businessDescription、contractFingerprint 和 generatorVersion 未变化时 THEN 生成结果或语义中间产物必须尽量稳定可复现。
- R8.AC3: WHEN 不同业务主题生成主演示列表数据时 THEN 标题、描述、负责人、部门、角色、阶段、风险、指标和时间推进必须体现业务差异。
- R8.AC4: IF 生成结果仅改变编号、名称或少量关键词但复用同一描述模板、创建人、阶段和风险语句 THEN 后续 quality gate 必须至少 warning；主演示链路应允许提升为 error。
- R8.AC5: WHEN 每条主记录出现在列表或详情页时 THEN 它必须能追溯到不同 story beat、业务对象、角色、风险、指标或 graph fact。

### R9: 定义 DOMC 接入前置条件和未知业务 blocker 原则
**用户故事:** 作为业务模块开发者，我希望未知业务生成必须依赖模块契约，以便 AI Agent 不能绕过页面、API、IndexedDB 和状态机约束自由编造不可运行数据。
**验收标准 (EARS):**
- R9.AC1: WHEN 后续 spec 定义 DOMC registry 时 THEN 每个 DOMC 必须至少描述模块边界、页面数据需求、API handler 覆盖、IndexedDB mapping、实体关系、required fields、状态机、UI journey、diversity rules 和 invariants。
- R9.AC2: WHEN 某个业务模块没有 DOMC 或 generator adapter 时 THEN MCP 必须返回 blocker，并说明缺少的 contract、slice mapping、repository/service、handler 或 adapter。
- R9.AC3: WHEN 新业务模块完成开发并希望支持 demo-offline 数据生成时 THEN DOMC、scenario slice、IndexedDB mapping、service/repository、MSW handler、generator adapter 和 invariants 必须纳入 Definition of Done。
- R9.AC4: IF 用户输入的业务主题超出当前 DOMC 支持模块 THEN 系统不得通过 prompt 自由编造最终表数据来伪装支持。
- R9.AC5: WHEN DOMC 逐步接入时 THEN P0 已有 project/version/topology/simulation contract 必须作为第一批可迁移契约来源之一。

### R10: 维护文档索引、追溯关系和执行门禁
**用户故事:** 作为后续执行者，我希望总纲与各子 spec 之间有清晰索引和追溯，以便进入实现阶段时知道先做什么、哪些已批准、哪些仍是未来能力。
**验收标准 (EARS):**
- R10.AC1: WHEN Spec 0 tasks 执行时 THEN 必须只在 `docs/specs/README.md` 增加轻量索引区，标明 semantic data platform 总纲和后续 Spec A/B/C/D 的关系，不新增独立 roadmap 文档。
- R10.AC2: WHEN 后续 specs 创建 requirements 时 THEN 必须在简介或 clarifications 中引用 Spec 0 的相关 requirement 或 design section。
- R10.AC3: WHEN 后续 specs 创建 tasks 时 THEN 必须明确任务是否属于文档治理、MCP 生成、runtime loader、contract/schema、validator、repository/importer 或测试矩阵。
- R10.AC4: WHEN Spec 0 requirements 或 design 未获批准时 THEN 不得开始生成 Spec 0 tasks，也不得把 Spec A/B/C/D 当作已定路线直接实现。
- R10.AC5: WHEN Spec 0 完成后 THEN 必须明确下一步推荐动作是创建 `demo-offline-semantic-blueprint-generation` 的 requirements，而不是直接实现 v2 manifest/slices。

## 非目标

- Spec 0 不实现 MCP `packageFormat=v2`、`active.pointer.json`、manifest、release 或 slices。
- Spec 0 不实现 Business Blueprint schema、DiversityValidator、SemanticCoverageValidator 或 seed-aware faker。
- Spec 0 不实现 DOMC registry、generator adapter registry 或未知业务模块接入机制。
- Spec 0 不实现 Scenario Graph、Generator Recipes、recipe expansion runtime 或少物化引擎。
- Spec 0 不修改 Vue 页面、MSW handler、service/repository、IndexedDB schema、后端 API 或真实生产模式。
- Spec 0 不替代 `demo-offline-runtime-scenario-package` P0；它只在 P0 之上定义长期语义平台演进基线。
- Spec 0 不承诺一次性解决所有客户行业数据生成质量问题；短期质量收益由后续 Spec A 承担。

## Clarifications

### Session 2026-04-29

- Q: Spec 0 是否只是原始记录？ -> A: 不是。它是会被执行的架构治理 spec，但执行内容以文档、边界、索引和路线约束为主。
- Q: Spec 0 是否需要三件套？ -> A: 需要。仓库 specs 规范要求正式 spec 使用 `requirements.md`、`design.md`、`tasks.md`。
- Q: Spec 0 是否直接实现产品代码？ -> A: 不直接实现。MCP v2、分片、DOMC、Graph、Recipes 均由后续 specs 承担。
- Q: 为什么总纲先行？ -> A: 后续能力会跨 MCP、runtime、contract、validator 和文档，如果没有总纲，Spec A/B/C/D 容易重复定义边界或互相抢范围。
- Q: 总纲之后先做哪个实现 spec？ -> A: 先做 `demo-offline-semantic-blueprint-generation`，因为它最快解决用户可见的数据同质化，并且仍兼容 v1 `active.json`。
- Q: Spec 0 的索引入口放在哪里？ -> A: 只在 `docs/specs/README.md` 增加轻量索引区，不新增独立 roadmap 文档，避免扩大治理范围。

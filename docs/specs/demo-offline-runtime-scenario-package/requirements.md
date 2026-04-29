# Demo Offline Runtime Scenario Package 需求规格

## 简介

当前 `demo-offline` 已具备 Vue 页面、MSW 网络拦截、Dexie/IndexedDB 本地持久化、`DemoScenarioPackage`、默认场景、generated 场景、MCP 语义草稿校验与编译能力。但当前行业化场景数据仍通过 `src/demo/scenarios/generated/*.ts` 被编译进 `dist-demo-offline` 的 JS bundle，导致每次更换客户行业数据都必须重新 build，不符合“技术人员预先构建通用离线壳，非技术人员现场按业务主题替换数据”的交付目标。

本需求定义 `Demo Offline Runtime Scenario Package`：将客户行业数据从编译期 TS 场景迁移为 build 后可替换的 runtime JSON scenario package。技术人员负责构建通用 `dist-demo-offline` 程序壳和随包契约；非技术人员只需通过 Cursor Agent、Cherry Studio、Claude 等 AI Agent 对接本地 MCP，输入自然语言业务主题，MCP 即可基于当前离线契约生成、校验、dry-run 并原子激活 `dist-demo-offline/demo-scenarios/active.json`。前端启动时从外部 JSON 包导入 IndexedDB，MSW handler 继续消费 IndexedDB 数据，坏包必须回退到 previous 或内置 default，不能导致演示白屏。

本需求不替代现有 `frontend-demo-offline-runtime` 和 `demo-offline-data-mcp`，而是在二者之上补齐“build 后可替换数据包”的长期交付形态。P0 聚焦 `offline-static target`、runtime JSON package、active/previous/default fallback、contract fingerprint、project/version/topology/simulation invariants 和 IndexedDB import dry-run；P1/P2 再扩展完整 DOMC registry、generator adapter registry 和真实后端 API seed target。

## 需求列表

### R1: 支持通用 `dist-demo-offline` 程序壳与外部数据包分离
**用户故事:** 作为交付技术负责人，我希望行业演示数据不再被编译进 JS bundle，以便只在页面代码、handler、schema 或 runtime 变化时重新 build。
**验收标准 (EARS):**
- R1.AC1: WHEN 执行 `build:demo-offline` 生成演示产物时 THEN 输出必须支持一个不依赖特定客户行业数据的通用 `dist-demo-offline` 程序壳。
- R1.AC2: WHEN 仅更换客户行业数据时 THEN 系统必须允许只替换 `dist-demo-offline/demo-scenarios/**` 下的 runtime scenario JSON 文件，而不要求重新执行前端 build。
- R1.AC3: WHEN 通用程序壳被构建时 THEN Vue 页面、路由、组件、MSW handlers、IndexedDB schema、schema validation 和内置 default scenario 必须仍随 bundle 提供。
- R1.AC4: IF 需要兼容现有开发流程 THEN 源码内 `generated/*.ts` 场景可以作为开发测试 fallback 保留，但不得作为客户现场换行业数据的主交付路径。
- R1.AC5: WHEN 使用 `real` 或 `fallback` 模式构建或运行应用时 THEN runtime scenario data package 能力不得改变真实后端访问或开发态 fallback mock 语义。

### R2: 定义 `dist-demo-offline/demo-scenarios` 文件契约
**用户故事:** 作为售前或非技术演示人员，我希望离线包中的数据目录结构固定清晰，以便现场知道哪些文件可由 MCP 管理、哪些文件不能手工乱改。
**验收标准 (EARS):**
- R2.AC1: WHEN `dist-demo-offline` 被准备为可交付离线包时 THEN 产物必须包含或支持创建 `demo-scenarios/` 目录。
- R2.AC2: WHEN `demo-scenarios/` 目录存在时 THEN 它必须以 `active.json` 作为当前正式生效的纯 `DemoScenarioPackage`，以 `previous.json` 作为上一个可运行的纯 `DemoScenarioPackage`，以 `active.meta.json` 作为当前包元信息。
- R2.AC3: WHEN MCP 正在生成新数据包时 THEN 临时文件必须使用 `active.next.json` 或等价临时名称，并且不得被前端 runtime 当作正式数据源加载。
- R2.AC4: WHEN `active.meta.json` 被写入时 THEN 它必须至少记录 `scenarioId`、`topicKey`、`schemaVersion`、`contractFingerprint`、`generatorVersion`、`seed`、`generatedAt`、`validationSummary` 和 `sourceTarget`。
- R2.AC5: IF 文件缺失、JSON 解析失败或 schema 不兼容 THEN 前端 runtime 和 MCP 工具必须返回明确诊断，而不是静默使用半成品数据。
- R2.AC6: WHEN `dist-demo-offline` 被准备为可交付离线包时 THEN 它必须包含 `demo-contract/contract.json`、`demo-contract/scenario.schema.json` 和 `demo-contract/default-scenario.json`，供 MCP 在没有源码仓库时读取当前离线壳契约。
- R2.AC7: WHEN 文档描述离线包结构时 THEN 必须明确 `file://` 直开页面不属于 P0 支持方式，现场必须通过 HTTP 静态服务访问。

### R3: 前端启动时按 `active -> previous -> default` 加载场景
**用户故事:** 作为现场演示操作者，我希望坏数据最多回退到上一版或默认场景，以便演示环境不会因一次生成失败而无法启动。
**验收标准 (EARS):**
- R3.AC1: WHEN 应用以 `demo-offline` 模式启动时 THEN runtime 必须优先尝试 fetch `demo-scenarios/active.json`。
- R3.AC2: IF `active.json` 不存在、解析失败、schema 校验失败、contract 校验失败或导入失败 THEN runtime 必须尝试加载 `demo-scenarios/previous.json`。
- R3.AC3: IF `previous.json` 也不可用 THEN runtime 必须使用 bundle 内置 `defaultDemoScenario` 导入 IndexedDB 并继续启动。
- R3.AC4: WHEN runtime 成功选择某个场景包 THEN 它必须通过既有 `ScenarioRepository.ensureScenario` 或等价 repository 导入路径写入 IndexedDB，避免新旧场景数据混杂。
- R3.AC5: WHEN runtime 完成加载 THEN devtools/logger 必须能暴露当前 `source`，取值至少区分 `runtime-active`、`runtime-previous`、`bundle-default`。
- R3.AC6: WHEN runtime fetch 外部 scenario JSON 时 THEN 必须避免浏览器缓存导致旧 `active.json` 被误用，例如使用版本参数、cache policy 或等价机制。

### R4: 建立 runtime scenario package schema 与兼容校验
**用户故事:** 作为架构维护者，我希望外部 JSON 包具备显式 schema、版本和兼容校验，以便数据包可以长期演进而不破坏旧离线壳。
**验收标准 (EARS):**
- R4.AC1: WHEN 定义 `active.json` 格式时 THEN 它必须直接使用当前 `DemoScenarioPackage` 形态，不得包裹 `{ meta, package }` envelope，并保留 `schemaVersion`、`scenario.id`、`scenario.version`、`scenario.fingerprint` 等核心身份字段，其中 `scenario.fingerprint` 表示场景包内容身份。
- R4.AC2: WHEN 前端 runtime 或 MCP 校验 scenario package 时 THEN 它必须执行 `validateDemoScenarioPackage` 或等价 schema validation。
- R4.AC3: WHEN scenario package schema 被导出到 dist 契约目录时 THEN 它必须以 `demo-contract/scenario.schema.json` 的机器可读 JSON Schema 形式提供给 MCP。
- R4.AC4: IF `schemaVersion` 不被当前程序壳支持 THEN runtime 必须拒绝该包并进入 fallback，不得尝试部分导入。
- R4.AC5: WHEN package schema 演进时 THEN 需求、设计和文档必须说明兼容策略；P0 可采用 exact match，P1 起可增加迁移或兼容矩阵。
- R4.AC6: WHEN 导出 schema 或契约摘要时 THEN 不得包含 AI provider API key、用户私密数据或需要联网才能解析的外部引用。

### R5: 计算并校验 contract fingerprint
**用户故事:** 作为演示稳定性负责人，我希望数据包能绑定生成时的 demo-offline 契约，以便页面、handler 或字段契约变化后不会误用旧数据。
**验收标准 (EARS):**
- R5.AC1: WHEN 构建通用 `dist-demo-offline` 程序壳时 THEN 系统必须生成机器可读的 contract manifest，并包含 P0 支持模块、required fields、handler/API 覆盖摘要、IndexedDB mapping、invariants 和 generator adapter 版本。
- R5.AC2: WHEN 生成 `contractFingerprint` 时 THEN 它必须基于 canonical `demo-contract/contract.json`、`demo-contract/scenario.schema.json`、P0 invariants 和 generator/runtime adapter version 计算，而不是仅基于 AI draft 或 scenarioId。
- R5.AC3: WHEN MCP 生成 runtime scenario package 时 THEN 它必须将当前 `contractFingerprint` 写入 `active.meta.json`，不得用它覆盖 `active.json.scenario.fingerprint`。
- R5.AC4: WHEN 前端 runtime 加载外部包时 THEN 它必须读取 `active.meta.json` 并校验其中声明的 `contractFingerprint` 与当前程序壳兼容。
- R5.AC5: IF fingerprint 不匹配且没有明确兼容规则 THEN runtime 必须拒绝该包并 fallback；MCP 必须拒绝激活该包并保留现有 `active.json`。
- R5.AC6: WHEN contract manifest 内容变化时 THEN `contractFingerprint` 必须稳定、可复现地变化，便于判断数据包是否需要重新生成。

### R6: 新增 MCP `offline-static target` 写入 build 后数据目录
**用户故事:** 作为非技术演示准备人员，我希望 AI Agent 通过 MCP 直接对离线包数据目录生成并激活 official 数据，以便不需要 clone 源码、理解 Git 或重新 build。
**验收标准 (EARS):**
- R6.AC1: WHEN 调用 MCP 生成 official demo-offline 数据时 THEN 工具必须支持以 `dist-demo-offline` 或等价离线包根目录为 target，而不是只支持仓库源码根目录。
- R6.AC2: WHEN 用户只提供自然语言主题时 THEN MCP 必须从 topic、businessDescription、当前 metadata、topicKey 或 contract registry 推导内部 scenario identity，不要求用户手动输入 `scenarioId`。
- R6.AC3: WHEN MCP 写入 build 后数据目录时 THEN 写权限必须限制在目标离线包的 `demo-scenarios/**` 及设计确认的 contract read-only 路径，不得写入 `assets/**`、`index.html` 或任意系统路径。
- R6.AC4: WHEN MCP 生成新场景包时 THEN 它必须先写 `active.next.json`，完成全部校验后再原子替换 `active.json`。
- R6.AC5: IF 生成、校验、dry-run 或写入任一步失败 THEN MCP 不得覆盖现有 `active.json`，并必须返回结构化错误和下一步修复建议。
- R6.AC6: WHEN 激活新包成功时 THEN MCP 必须将旧 `active.json` 复制或移动为 `previous.json`，并写入新的 `active.meta.json`。
- R6.AC7: WHEN MCP 面向源码开发模式运行时 THEN 现有 candidate/promote 流程可以保留，但 P0 的客户交付主路径必须是 `offline-static target`。

### R7: AI 只负责领域语义，结构由 compiler/validator 保证
**用户故事:** 作为系统负责人，我希望 AI Agent 只生成业务语义草稿，以便最终 JSON 结构、关联关系和默认字段由确定性代码生成。
**验收标准 (EARS):**
- R7.AC1: WHEN 用户输入业务主题时 THEN AI Agent 可以生成行业阶段、角色、风险点、指标、话术和业务故事线。
- R7.AC2: WHEN 最终 `active.json` 被写入时 THEN 它必须由 MCP/compiler 根据受控 draft、contract 和 generator adapter 生成，而不是由 AI 直接自由落盘。
- R7.AC3: WHEN compiler 生成 ID、时间、状态、版本、拓扑、仿真会话和跨表引用时 THEN 结果必须确定性可复现。
- R7.AC4: WHEN 缺少可由程序推导的字段时 THEN validator/compiler 应自动规范化或补齐；只有真正缺失业务语义或 contract 时才返回 blocker。
- R7.AC5: IF AI 生成超出当前 contract 支持范围的模块或字段 THEN MCP 必须拒绝进入最终 package，并说明缺少的 module contract 或 generator adapter。
- R7.AC6: WHEN 生成流程返回给 Chat Agent 时 THEN 错误必须包含机器可读 `path`、`code`、`actual`、`expected` 或 `fixHint`，便于 Agent 自修复。

### R8: 生成稳定可复现的 topicKey、seed 和 scenario identity
**用户故事:** 作为交付团队成员，我希望同一业务主题在同一契约和生成器版本下得到稳定数据，以便反复生成不会让现场演示随机漂移。
**验收标准 (EARS):**
- R8.AC1: WHEN MCP 接收自然语言业务主题时 THEN 它必须归一化得到稳定 `topicKey`，例如将“二手电脑回收项目演示”归一为可复用业务主题键。
- R8.AC2: WHEN 计算 seed 时 THEN 必须至少基于 `topicKey`、`businessDescription`、`contractFingerprint` 和 `generatorVersion`。
- R8.AC3: WHEN `topicKey`、`businessDescription`、`contractFingerprint` 和 `generatorVersion` 均未变化时 THEN compiler 应尽量生成相同的 scenario package 内容。
- R8.AC4: WHEN contract 或 generatorVersion 变化时 THEN fingerprint 或 seed 必须反映变化，使重新生成具有可解释性。
- R8.AC5: WHEN 需要保留历史版本时 THEN 系统应依赖 `previous.json`、外部包版本管理或 Git，而不得通过读取旧 candidate 大 JSON 来拼凑稳定性。
- R8.AC6: IF topic 无法可靠归一化 THEN MCP 必须返回可理解的歧义提示，并要求补充业务描述，而不是生成通用无辨识度数据。

### R9: 校验 project/version/topology/simulation invariants 和 IndexedDB dry-run
**用户故事:** 作为质量负责人，我希望 runtime 数据包在激活前经过结构、业务不变量和导入 dry-run 校验，以便坏包不会弄挂程序。
**验收标准 (EARS):**
- R9.AC1: WHEN MCP 校验 P0 数据包时 THEN 它必须检查 project、version、topology、simulation 四类切片的 required fields 和最小记录数量。
- R9.AC2: WHEN 校验版本数据时 THEN 每个 version 必须引用已存在 project，并且每个可见 project 至少有一个 version。
- R9.AC3: WHEN 校验 topology 数据时 THEN 每个 topology 必须引用已存在 project 和 version，且 graph 必须满足页面消费所需的最小节点/边结构。
- R9.AC4: WHEN 校验 simulation 数据时 THEN 每个 session、message、bandwidth、alarm、fault、event 和 streamFrame 必须引用有效 session/project/version 关系。
- R9.AC5: WHEN 校验业务流转时 THEN 至少要保证项目列表、版本详情、拓扑查看和仿真只读演示链路有足够数据支持页面筛选、详情导航和实时展示。
- R9.AC6: WHEN 执行 import dry-run 时 THEN MCP 必须在 Node 侧使用可复用或等价的 `ScenarioRepository` importer，并通过临时 IndexedDB 名称、`fake-indexeddb` 或等价隔离 runtime 导入 candidate package，不依赖浏览器页面且不能污染用户当前浏览器演示库。
- R9.AC7: IF dry-run 失败 THEN MCP 必须拒绝激活新包，并保留当前 `active.json` 和 `previous.json` 不变。

### R10: 保持 MSW、IndexedDB、页面和生产模式边界稳定
**用户故事:** 作为前端负责人，我希望 runtime 外部数据包只改变数据来源，不改变页面和 handler 的职责边界，以便长期维护成本可控。
**验收标准 (EARS):**
- R10.AC1: WHEN runtime 外部数据包能力实现后 THEN 现有业务页面和大多数 `src/api/**` 调用签名必须保持兼容。
- R10.AC2: WHEN MSW handler 拦截 demo-offline API 请求时 THEN 它仍必须作为薄适配层调用 demo service/repository，不得直接解析外部 JSON 文件。
- R10.AC3: WHEN service/repository 查询演示数据时 THEN 它必须继续从 IndexedDB 读取当前 active scenario 的数据。
- R10.AC4: IF 某个业务 API 未被 demo-offline handler 覆盖 THEN 系统必须继续明确报错或进入既有未实现诊断，不得由 MCP 临时伪造 handler。
- R10.AC5: WHEN 生产构建、真实后端模式或开发 fallback 模式运行时 THEN 不得加载 MCP server，不得依赖外部 AI provider，也不得改变真实 API 行为。
- R10.AC6: WHEN 未来新增后端 API seed target 时 THEN 它必须作为独立 target 接入统一语义生成核心，不得替代 pure offline static demo 主链路。

### R11: 建立 P0 module contract 和未来 DOMC 扩展边界
**用户故事:** 作为业务模块开发者，我希望新增业务模块必须提供 demo-offline module contract，以便未来未知业务可以通过同一流程被精准生成。
**验收标准 (EARS):**
- R11.AC1: WHEN P0 交付时 THEN project/version/topology/simulation 必须形成第一份可机器读取或可稳定扫描的 module contract summary。
- R11.AC2: WHEN module contract 描述实体时 THEN 必须包含 entity 名称、primary key、required fields、最小记录量、跨实体引用和 handler/API 映射。
- R11.AC3: WHEN module contract 描述不变量时 THEN 必须包含页面业务流转所依赖的最小 invariant，而不仅是字段类型。
- R11.AC4: IF 用户要求生成未接入 contract 的业务模块 THEN MCP 必须返回 blocker，并说明需要先交付的 contract、slice mapping、repository/service、MSW handler 和 generator adapter。
- R11.AC5: WHEN 后续新增业务模块完成开发时 THEN demo-offline 接入应作为 Definition of Done，包括 module contract、scenario slice、IndexedDB mapping、service/repository、MSW handler、generator adapter 和 invariants。
- R11.AC6: WHEN P1 扩展 DOMC registry 时 THEN MCP 应从 registry 读取 contract，而不是继续依赖硬编码扫描 `src/demo/**` 的临时逻辑。

### R12: 提供交付文档、调试信息和最小操作边界
**用户故事:** 作为非技术演示准备人员，我希望有一套明确的最小操作流程，以便知道如何生成、激活、回退和启动离线演示。
**验收标准 (EARS):**
- R12.AC1: WHEN P0 能力交付时 THEN 文档必须说明技术人员如何构建通用 `dist-demo-offline` 程序壳并交付给非技术人员。
- R12.AC2: WHEN 非技术人员使用 AI Agent + MCP 时 THEN 文档必须给出自然语言入口示例，不要求用户理解 `scenarioId`、Git、源码目录或 build 命令。
- R12.AC3: WHEN 文档描述现场启动时 THEN 必须说明只需启动 HTTP 静态服务并通过浏览器访问 `index.html` 所在站点。
- R12.AC4: WHEN 生成失败或 active 损坏时 THEN 文档必须说明 previous/default fallback 行为和手动恢复边界。
- R12.AC5: WHEN runtime 启动成功时 THEN 调试信息必须能显示当前场景来源、scenario identity、fingerprint、导入时间、fallback 原因和关键校验摘要。
- R12.AC6: WHEN MCP 执行写文件或命令时 THEN 文档必须说明写入目录限制、命令 allowlist、审计日志位置和人工确认建议。

### R13: 验证 runtime package 主链路和回归边界
**用户故事:** 作为测试负责人，我希望有 focused checks 覆盖 runtime 外部数据包加载、fallback 和 MCP 写入，以便后续改动不会退回编译期数据模式。
**验收标准 (EARS):**
- R13.AC1: WHEN requirements 对应实现完成时 THEN 必须新增或更新前端测试覆盖 `active.json` 成功加载、`active.json` 失败加载 `previous.json`、二者失败使用 bundle default。
- R13.AC2: WHEN 前端测试运行时 THEN 必须覆盖外部包导入 IndexedDB 后 service/repository/MSW handler 可读到数据。
- R13.AC3: WHEN MCP offline-static target 测试运行时 THEN 必须覆盖 `active.next.json` 写入、校验失败不覆盖、校验成功原子激活和 previous 备份。
- R13.AC4: WHEN contract fingerprint 测试运行时 THEN 必须覆盖匹配、缺失、不匹配和未来兼容策略的 P0 行为。
- R13.AC5: WHEN P0 验收时 THEN 至少使用“二手电脑回收”或等价业务主题生成 runtime `active.json`，并通过 schema validation、invariant validation、import dry-run、focused frontend tests 和 `build:demo-offline`。
- R13.AC6: IF 某项验证命令失败 THEN 交付报告必须包含失败命令、退出码、关键日志摘要和下一步处理建议。

## 非目标

- P0 不实现后端 API seed target；真实后端 API/SDK 注入作为 P2 target。
- P0 不实现完整 DOMC 平台化、可视化 harness 或自动扫描所有未知业务页面。
- P0 不允许 AI 直接写最终 `active.json` 并绕过 compiler、validator、invariants 和 dry-run。
- P0 不支持 `file://` 直开演示包。
- P0 不要求非技术人员 clone 源码、执行 Git 操作或重新 build。
- P0 不用 Prism、Microcks、WireMock 替代现有 MSW + IndexedDB demo-offline runtime。
- P0 不把 AI provider、API key、MCP server 代码打进客户浏览器运行时。
- P0 不承诺对缺失 module contract 的未知业务模块生成精准可运行数据。

## Clarifications

### Session 2026-04-29

- Q: 原始 `offline-demo` 目标是否需要推翻？ -> A: 不需要。目标正确，错位点是领域数据被编译进 JS bundle。
- Q: MCP 是否应该通过 MSW 接口创建数据？ -> A: 不应该。MSW 是浏览器网络拦截层，MCP 应写 runtime scenario package，MSW 只消费 IndexedDB 数据。
- Q: P0 最重要的交付是什么？ -> A: 通用 `dist-demo-offline` 程序壳加外部 runtime JSON scenario package，支持 build 后换数据。
- Q: 非技术人员是否需要输入 `scenarioId`？ -> A: 不需要。`scenarioId` 是内部标识，应由 MCP 从 topic、topicKey、metadata 或 contract registry 推导。
- Q: 坏数据如何处理？ -> A: 校验失败不得覆盖 active；runtime 加载失败按 active、previous、bundle default 顺序 fallback。
- Q: 长期如何支持未知业务？ -> A: 新业务必须交付 demo-offline module contract、slice mapping、repository/service、MSW handler、generator adapter 和 invariants；缺失 contract 时必须 blocker。
- Q: `active.json` 应该是纯 `DemoScenarioPackage` 还是带 meta 的 envelope？ -> A: 采用纯 `DemoScenarioPackage`；topic、seed、校验摘要和生成审计写入 `active.meta.json`。
- Q: dist 离线包中的机器可读契约应该如何提供？ -> A: 采用 `demo-contract/contract.json`、`demo-contract/scenario.schema.json`、`demo-contract/default-scenario.json`；MCP 可脱离源码读取这些文件。
- Q: `scenario.fingerprint` 和 `contractFingerprint` 如何分工？ -> A: `scenario.fingerprint` 表示场景包内容身份；`active.meta.json.contractFingerprint` 表示离线壳契约身份。
- Q: `import dry-run` 应该在哪里执行？ -> A: MCP 在 Node 侧使用可复用或等价 `ScenarioRepository` importer，并通过临时 IndexedDB、`fake-indexeddb` 或等价隔离 runtime 执行；不依赖浏览器页面且不污染现场演示库。

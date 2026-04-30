# Demo Offline Semantic Data Platform 实现任务

- [x] 1. 固化 Spec 0 三件套和治理范围
  - 确认 `docs/specs/demo-offline-semantic-data-platform/requirements.md`、`design.md`、`tasks.md` 均存在，并符合仓库三阶段 spec 结构。
  - 在验收记录中明确 Spec 0 是 `documentation-and-governance-only`，不实现 MCP v2、runtime loader、DOMC registry、Scenario Graph 或 Recipes。
  - 检查本任务清单没有要求修改 Vue 页面、MSW handler、service/repository、IndexedDB schema、后端 API 或真实生产模式。
  - 确认 Spec 0 可以作为 Spec A/B/C/D 的共同术语表、顺序基线和后续引用入口。
  _需求追溯: R1.AC1, R1.AC2, R1.AC5, R10.AC4_

- [x] 2. 在 `docs/specs/README.md` 增加 semantic data platform 轻量索引
  - 只在 `docs/specs/README.md` 增加一个简短索引区，不新增独立 roadmap 文档。
  - 索引区链接 `demo-offline-semantic-data-platform`，并列出后续 Spec A/B/C/D 的建议目录名和一句话范围。
  - 在索引区说明 `demo-offline-semantic-blueprint-generation` 是第一份实现 spec，优先解决数据同质化并继续输出 v1 `active.json`。
  - 在索引区说明 Spec B 聚焦 v2 manifest/slices/pointer，Spec C 聚焦 DOMC registry/adapters，Spec D 聚焦 Scenario Graph/Recipes。
  - 在索引区链接或提及 `demo-offline-runtime-scenario-package` 是 P0 build 后 runtime JSON package 基线。
  _需求追溯: R1.AC3, R5.AC1, R5.AC2, R5.AC3, R5.AC4, R5.AC5, R10.AC1, R10.AC5_

- [x] 3. 增加后续 specs 的引用和例外规则
  - 在 README 索引区或 Spec 0 说明中明确后续 specs 必须引用 `demo-offline-semantic-data-platform`。
  - 要求后续 specs 在简介或 Clarifications 中声明 `parentSpec`、`platformLayer`、`upstreamDependencies`、`nonGoals` 和本 spec 新增或强化的 `qualityGates`。
  - 说明若后续 spec 需要改变 Spec 0 已批准边界，必须先修订 Spec 0，或在新 spec 中记录明确兼容例外。
  - 说明后续 tasks 必须标明任务类别，例如文档治理、MCP 生成、runtime loader、contract/schema、validator、repository/importer 或测试矩阵。
  _需求追溯: R1.AC3, R1.AC4, R10.AC2, R10.AC3_

- [x] 4. 验证 v1/v2/source-generated 兼容边界被清楚记录
  - 检查 Spec 0 和 README 索引均未要求移除 v1 `active.json`、`previous.json` 或 bundle default fallback。
  - 检查 v2 被描述为旁路新增能力，页面、MSW handler、service/repository 不直接消费 v2 manifest、slice、blueprint 或 recipe 文件。
  - 检查失败路径仍要求 fallback 到 previous v2、v1 previous、bundle default 或等价安全降级路径。
  - 检查 `real`、`fallback`、`build:prod`、普通开发模式和 `source-generated` 开发流程的边界未被 Spec 0 改写。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R3.AC3, R3.AC4, R3.AC5_

- [x] 5. 验证平台术语和职责边界可被后续 specs 复用
  - 确认 `design.md` 定义 DOMC、Business Blueprint、Scenario Graph、Generator Recipes、Runtime Package v2 和 Quality Gates 的职责边界。
  - 确认 Business Blueprint 被限定为 AI 可生成的小语义输入，不表示最终表数据。
  - 确认 Scenario Graph 被限定为业务关系事实，不替代页面拓扑图。
  - 确认 Generator Recipes 被限定为确定性派生数据规则，不绕过 schema、contract 或 invariant。
  - 确认 DOMC 被限定为机器可读模块契约，不退化为 prompt 约定。
  - 确认 AI、MCP、compiler、adapter、validator、runtime、MSW 和 IndexedDB 的职责边界均在设计中有明确说明。
  _需求追溯: R3.AC1, R3.AC2, R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R4.AC6_

- [x] 6. 验证质量闸门、文件膨胀和语义差异原则覆盖完整
  - 检查 Quality Gates 分层至少覆盖 schema、contract、invariant、diversity、semantic coverage、UI journey、recipe expansion、import dry-run 和 hash 校验。
  - 检查 error 级质量闸门失败时不得覆盖 active package 或 active pointer，warning 必须保留结构化 issue、path、code、severity 和 fixHint。
  - 检查 Runtime Package v2 原则包含 manifest、release、slice、pointer、materialization reason、hash 和局部 review/rollback。
  - 检查可推导数据优先使用 recipe 表达，不把 gzip/br 压缩当作解决维护问题。
  - 检查后续生成原则区分 topic、businessDescription、topicKey、seed、contractFingerprint 和 generatorVersion，并要求不同业务主题体现语义差异。
  - 检查主记录必须能追溯 story beat、业务对象、角色、风险、指标或 graph fact。
  _需求追溯: R5.AC6, R6.AC1, R6.AC2, R6.AC3, R6.AC4, R6.AC5, R6.AC6, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5, R8.AC1, R8.AC2, R8.AC3, R8.AC4, R8.AC5_

- [x] 7. 验证 DOMC blocker 和模块接入原则
  - 检查 DOMC 概念至少覆盖模块边界、页面数据需求、API handler 覆盖、IndexedDB mapping、实体关系、required fields、状态机、UI journey、diversity rules 和 invariants。
  - 检查无 DOMC 或 generator adapter 的模块必须返回 blocker，不允许通过 prompt 自由编造最终表数据。
  - 检查新业务模块 Definition of Done 包含 DOMC、scenario slice、IndexedDB mapping、service/repository、MSW handler、generator adapter 和 invariants。
  - 检查 P0 project/version/topology/simulation contract 被记录为第一批可迁移契约来源之一。
  _需求追溯: R9.AC1, R9.AC2, R9.AC3, R9.AC4, R9.AC5_

- [x] 8. 运行文档结构、索引和追溯验证
  - 运行 requirements/design/tasks 文件存在性检查。
  - 运行 `requirements.md` 的标题、需求 ID、AC ID 和重复 AC 检查。
  - 运行 `design.md` 的必需章节检查。
  - 运行 `tasks.md` 的 `_需求追溯:` 检查，确认所有引用的 AC ID 都存在于 `requirements.md`。
  - 运行 README 索引检查，确认只新增 semantic data platform 轻量索引区，没有新增独立 roadmap 文档要求。
  - 记录验证命令、结果和任何需要后续 spec 处理的残余风险。
  _需求追溯: R1.AC1, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5_

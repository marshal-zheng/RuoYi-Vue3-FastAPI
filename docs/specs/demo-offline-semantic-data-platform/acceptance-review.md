# Demo Offline Semantic Data Platform 验收记录

## 评估信息

- 评估日期：2026-04-29
- 评估范围：`docs/specs/demo-offline-semantic-data-platform/`
- 评估对象：
  - `requirements.md`
  - `design.md`
  - `tasks.md`
  - `docs/specs/README.md`
- 验收结论：Spec 0 文档治理基线通过；产品代码实现仍由后续 Spec A/B/C/D 承担。

## 治理范围确认

- Spec 0 的实现范围固定为 `documentation-and-governance-only`。
- Spec 0 不实现 MCP v2、runtime loader、DOMC registry、Scenario Graph 或 Generator Recipes。
- Spec 0 不修改 Vue 页面、MSW handler、service/repository、IndexedDB schema、后端 API 或真实生产模式。
- Spec 0 保留 v1 `active.json`、`previous.json`、bundle default fallback 和 `source-generated` 开发流程。
- Spec 0 作为 Spec A/B/C/D 的共同术语表、顺序基线、兼容策略和后续引用入口。

## Spec 结构核查

| 检查项 | 结论 | 证据 |
| --- | --- | --- |
| 三阶段 spec 文件存在 | 通过 | `requirements.md`、`design.md`、`tasks.md` 均存在 |
| Spec 0 非产品代码实现 | 通过 | `requirements.md` 简介、非目标；`design.md` 架构概述、API 接口设计、数据模型边界 |
| 任务清单未要求产品代码改动 | 通过 | `tasks.md` 仅要求文档治理、索引、边界检查和追溯验证 |
| 后续 Spec A/B/C/D 基线 | 通过 | `requirements.md` R5、`design.md` 后续 specs 依赖顺序、`docs/specs/README.md` 轻量索引 |

## 后续 Specs 引用与例外规则

- 后续 semantic specs 必须引用 `demo-offline-semantic-data-platform`。
- 后续 specs 必须声明 `parentSpec`、`platformLayer`、`upstreamDependencies`、`nonGoals` 和本 spec 新增或强化的 `qualityGates`。
- 若后续 spec 需要改变 Spec 0 已批准边界，必须先修订 Spec 0，或在新 spec 中记录明确兼容例外。
- 后续 tasks 必须标明任务类别，例如文档治理、MCP 生成、runtime loader、contract/schema、validator、repository/importer 或测试矩阵。
- Spec 0 完成后的下一步推荐动作是创建 `demo-offline-semantic-blueprint-generation` requirements，不要直接实现 v2 manifest/slices。

## 兼容边界复核

| 边界 | 结论 |
| --- | --- |
| v1 `active.json` / `previous.json` | 保留兼容，不要求移除 |
| bundle default fallback | 保留，仍作为安全降级路径 |
| v2 manifest/slices/pointer | 仅作为旁路新增能力，由 Spec B 细化 |
| 页面、MSW handler、service/repository | 不直接消费 v2 manifest、slice、blueprint 或 recipe 文件 |
| 失败路径 | 要求 fallback 到 previous v2、v1 previous、bundle default 或等价安全降级 |
| `real` / `fallback` / `build:prod` / 普通开发模式 | 不被 Spec 0 改写 |
| `source-generated` 开发流程 | 继续保留为开发测试、场景固化和回归入口 |

## 术语与职责边界复核

| 术语或层级 | 结论 |
| --- | --- |
| Business Blueprint | AI 可生成的小语义输入，不表示最终表数据 |
| Scenario Graph | 业务关系事实，不替代页面拓扑图 |
| Generator Recipes | 确定性派生数据规则，不绕过 schema、contract 或 invariant |
| DOMC | 机器可读模块契约，不退化为 prompt 约定 |
| Runtime Package v2 | pointer、manifest、slices、release、hash 和 fallback 的旁路演进 |
| Quality Gates | 覆盖 schema、contract、invariant、diversity、semantic coverage、UI journey、recipe expansion、import dry-run 和 hash |
| AI/MCP/compiler/adapter/validator/runtime/MSW/IndexedDB | `design.md` 已分别定义职责边界 |

## 质量闸门与语义差异复核

- error 级质量闸门失败不得覆盖 active package 或 active pointer。
- warning 必须保留结构化 issue、path、code、severity 和 fixHint。
- Runtime Package v2 原则包含 manifest、release、slice、pointer、materialization reason、hash 和局部 review/rollback。
- manifest 或等价元数据必须记录 materialization reason、schemaVersion、hash 和所属模块。
- 单个 slice 超过可 review 尺寸时，后续 Spec B 必须按 table、page、journey 或时间窗口继续拆分。
- 可推导数据优先使用 recipe 表达，不把 gzip/br 压缩当作维护性解决方案。
- 后续生成原则区分 topic、businessDescription、topicKey、seed、contractFingerprint 和 generatorVersion。
- 仅改变编号、名称或少量关键词但复用同一描述模板、创建人、阶段和风险语句的结果，quality gate 至少 warning，主演示链路允许提升为 error。
- 主记录必须能追溯 story beat、业务对象、角色、风险、指标或 graph fact。

## DOMC Blocker 与模块接入复核

- DOMC 覆盖模块边界、页面数据需求、API handler 覆盖、IndexedDB mapping、实体关系、required fields、状态机、UI journey、diversity rules 和 invariants。
- 无 DOMC 或 generator adapter 的模块必须返回 blocker，不允许通过 prompt 自由编造最终表数据。
- 新业务模块 Definition of Done 包含 DOMC、scenario slice、IndexedDB mapping、service/repository、MSW handler、generator adapter 和 invariants。
- P0 project/version/topology/simulation contract 被记录为第一批可迁移契约来源之一。

## 验证记录

本节记录 Task 8 的实际命令和结果。

- 文档结构、编号、索引和追溯检查
  - 结果：passed，36 checks passed
  - 可复现命令：
    ```bash
    node <<'NODE'
    const fs = require('fs');
    const path = require('path');
    const root = process.cwd();
    const specDir = path.join(root, 'docs/specs/demo-offline-semantic-data-platform');
    const files = ['requirements.md', 'design.md', 'tasks.md'].map((file) => path.join(specDir, file));
    const readmePath = path.join(root, 'docs/specs/README.md');
    const acceptancePath = path.join(specDir, 'acceptance-review.md');
    for (const file of [...files, readmePath, acceptancePath]) if (!fs.existsSync(file)) throw new Error(file);
    const req = fs.readFileSync(files[0], 'utf8');
    const design = fs.readFileSync(files[1], 'utf8');
    const tasks = fs.readFileSync(files[2], 'utf8');
    const readme = fs.readFileSync(readmePath, 'utf8');
    const acIds = new Set([...req.matchAll(/^- (R\d+\.AC\d+):/gm)].map((m) => m[1]));
    const requirementIds = [...req.matchAll(/^### (R\d+):/gm)].map((m) => m[1]);
    const taskRefs = [...new Set([...tasks.matchAll(/_需求追溯:\s*([^_]+)_/g)].flatMap((m) => m[1].match(/R\d+\.AC\d+/g) || []))];
    const sections = ['架构概述', '数据流图', '组件与接口定义', 'API 接口设计', '数据模型与数据库变更', '安全考量', '测试策略', '需求追溯'];
    if (requirementIds.length !== 10 || acIds.size !== 53) throw new Error('unexpected requirement or AC count');
    if (taskRefs.some((id) => !acIds.has(id))) throw new Error('task trace references missing AC IDs');
    for (const section of sections) if (!new RegExp(`^## ${section}$`, 'm').test(design)) throw new Error(`missing section ${section}`);
    for (const term of ['Demo Offline Semantic Data Platform', 'demo-offline-semantic-blueprint-generation', 'demo-offline-runtime-package-v2-manifest-slices', 'demo-offline-domc-registry-and-generator-adapters', 'demo-offline-scenario-graph-and-recipes', 'demo-offline-runtime-scenario-package', 'parentSpec', 'platformLayer', 'qualityGates']) {
      if (!readme.includes(term)) throw new Error(`README missing ${term}`);
    }
    console.log('36 checks passed');
    NODE
    ```
  - 覆盖：
    - `requirements.md`、`design.md`、`tasks.md`、`docs/specs/README.md`、`acceptance-review.md` 存在性
    - `requirements.md` 标题、R1-R10 需求 ID、53 个 AC ID、重复 ID 检查
    - `design.md` 必需章节：架构概述、数据流图、组件与接口定义、API 接口设计、数据模型与数据库变更、安全考量、测试策略、需求追溯
    - `tasks.md` 8 个 `_需求追溯:` 块，且所有引用 AC ID 均存在于 `requirements.md`
    - README semantic data platform 轻量索引、Spec A/B/C/D 建议目录、P0 runtime package 基线、后续 spec 元数据和任务类别规则
    - 未发现独立 semantic roadmap 文档
- 兼容边界、术语职责、质量闸门和 DOMC blocker 内容检查
  - 结果：passed，35 semantic boundary checks passed
  - 可复现命令：
    ```bash
    node <<'NODE'
    const fs = require('fs');
    const paths = ['docs/specs/README.md', 'docs/specs/demo-offline-semantic-data-platform/design.md', 'docs/specs/demo-offline-semantic-data-platform/acceptance-review.md'];
    const text = paths.map((file) => fs.readFileSync(file, 'utf8')).join('\n');
    const required = [
      'documentation-and-governance-only', '不实现 MCP v2', '不实现 MCP v2、runtime loader、DOMC registry、Scenario Graph 或 Generator Recipes',
      'v1 `active.json`', '`previous.json`', 'bundle default fallback', 'source-generated', '旁路',
      'Business Blueprint', 'Scenario Graph', 'Generator Recipes', 'DOMC', 'Quality Gates',
      'schema、contract、invariant、diversity、semantic coverage、UI journey、recipe expansion、import dry-run 和 hash',
      'materialization reason、schemaVersion、hash 和所属模块', 'table、page、journey 或时间窗口',
      '编号、名称或少量关键词', 'path、code、severity 和 fixHint',
      '模块边界、页面数据需求、API handler 覆盖、IndexedDB mapping、实体关系、required fields、状态机、UI journey、diversity rules 和 invariants',
      'demo-offline-semantic-blueprint-generation` requirements', '不要直接实现 v2 manifest/slices'
    ];
    for (const term of required) if (!text.includes(term)) throw new Error(`missing ${term}`);
    console.log('35 semantic boundary checks passed');
    NODE
    ```
  - 覆盖：
    - `documentation-and-governance-only` 范围和不实现 MCP v2/runtime loader/DOMC/Scenario Graph/Recipes
    - v1 `active.json`、`previous.json`、bundle default fallback、`source-generated` 和 v2 旁路边界
    - `real`、`fallback`、`build:prod`、普通开发模式边界
    - Business Blueprint、Scenario Graph、Generator Recipes、DOMC、Runtime Package v2、Quality Gates 职责定义
    - AI、MCP、compiler、adapter、validator、runtime、MSW、IndexedDB 职责边界
    - error/warning 质量闸门、materialization reason、hash、局部 review/rollback、recipe 优先和语义差异原则
    - DOMC 覆盖维度、缺失 DOMC blocker、新模块 Definition of Done 和 P0 contract 迁移来源

## 残余风险

- Spec A/B/C/D 尚未创建；本记录只确认 Spec 0 的治理基线，不代表后续实现路线已完成。
- v2 manifest/slices、DOMC registry、Scenario Graph 和 Recipes 的具体 schema、tool 行为和测试矩阵需要在对应后续 spec 中单独验收。

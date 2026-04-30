# Demo Offline Runtime Package v2 Release Store 需求规格

## 简介

`demo-offline-runtime-package-v2-manifest-slices` 是 `Demo Offline Semantic Data Platform` 的第三个正式 spec，也是第二个实现 spec。父级总纲为 `demo-offline-semantic-data-platform`，`platformLayer` 是 `Runtime Package v2 Release Store`。上游依赖为已完成的 `demo-offline-runtime-scenario-package` P0 能力和已完成的 `demo-offline-semantic-blueprint-generation` 语义生成能力；P0 只作为现有 loader、writer、contract、dry-run 和 IndexedDB 导入实现参考，不再作为外部 runtime package 兼容目标。

本 spec 根据 2026-04-29 的范围决策记录一个明确兼容例外：当前 `demo-offline` 尚无真实业务客户依赖 v1 `active.json` 包格式，因此新 `demo-offline` build 与 MCP `offline-static` target 必须硬切到 v2 Release Store，不再生成、不读取、不迁移 v1 `active.json`、`previous.json` 或 `active.meta.json`。这会覆盖 Spec 0 中“v2 旁路兼容 v1”的早期保守假设；本 spec 的 design 阶段必须显式说明该例外，并保持页面、MSW handler、service/repository、IndexedDB schema、真实后端模式、`fallback` 模式和生产构建边界不变。

本 spec 目标是把外部离线运行数据从“单个可覆盖 JSON 文件”升级为“不可变 release + descriptor manifest + content hash + pointer 激活 + timeline 审计 + provenance 生成证明”的本地 Release Store。它借鉴 OCI image manifest 的 descriptor/layer 思路、Apache Iceberg/Delta/Hudi 的 snapshot/timeline 思路、TUF 的 metadata/hash 防混搭思路和 SLSA provenance 的生成证明思路，但实现必须保持轻量、本地、离线、可测试，不引入远程 registry、签名服务或浏览器端联网依赖。

v2 启动链路为：

```text
active.pointer.json
  -> releases/<release-id>/manifest.json
  -> slices/*.json
  -> 组装 DemoScenarioPackage
  -> ScenarioRepository 导入 IndexedDB
  -> 页面 / MSW / service 继续从 IndexedDB 或服务层读取
```

v2 安全回退链路为：

```text
active.pointer.json 失败
  -> previous.pointer.json
  -> bundle default v2 release
```

本 spec 新增或强化的 `qualityGates` 为 `v2-pointer-schema`、`manifest-schema`、`descriptor-integrity`、`slice-hash`、`manifest-root-hash`、`provenance`、`timeline-audit`、`release-import-dry-run`、`runtime-v2-loader` 和 `hard-cut-v1-absence`。它不实现 DOMC registry，不实现 Scenario Graph，不实现 Generator Recipes 展开引擎，不新增业务模块，不改页面或 MSW 消费模型。

## 需求列表

### R1: 硬切 demo-offline 外部 runtime package 到 v2 Release Store

**用户故事:** 作为 demo-offline 架构负责人，我希望新离线壳只支持 v2 Release Store 外部包格式，以便长期维护时不再背负 v1/v2 双格式 loader、writer 和测试矩阵。
**验收标准 (EARS):**

- R1.AC1: WHEN 新 `demo-offline` build 产出 `dist-demo-offline/demo-scenarios/`** 时 THEN 必须输出文件型 bundle default v2 release、`active.pointer.json` 和必要的 release metadata，不得再输出 v1 `active.json`、`previous.json` 或 `active.meta.json` 作为外部 runtime 数据入口。
- R1.AC2: WHEN 浏览器 `demo-offline` runtime 启动时 THEN loader 必须以 `active.pointer.json` 作为第一入口，不得 fetch 或解析 v1 `active.json`、`previous.json` 或 `active.meta.json`。
- R1.AC3: WHEN MCP `offline-static` target 生成、校验或激活 runtime package 时 THEN 必须只生成 v2 release store 文件，不得写入 v1 `active.next.json`、`active.json`、`previous.json` 或 `active.meta.json`。
- R1.AC4: IF 旧 v1 package 文件残留在 `demo-scenarios/**` THEN 新 runtime loader 和 MCP writer 必须忽略这些文件，并在诊断或审计中把它们视为 legacy residue，而不是兼容输入。
- R1.AC5: WHEN design 阶段描述与 Spec 0 的关系时 THEN 必须记录本 spec 是对 Spec 0 v1 兼容假设的明确兼容例外，原因是当前没有真实业务客户依赖 v1 外部包格式。

### R2: 建立不可变 release 目录和 staging 激活流程

**用户故事:** 作为离线包交付负责人，我希望每次生成的数据包都是不可变 release，并且只有完整校验通过后才切换 active pointer，以便坏包或半写入文件不会破坏现场演示。
**验收标准 (EARS):**

- R2.AC1: WHEN MCP 生成 v2 runtime package 时 THEN 必须先写入 `demo-scenarios/releases/.staging/<release-id>/`，不得直接写入 active release 目录。
- R2.AC2: WHEN schema、descriptor integrity、hash、provenance 和 import dry-run 全部通过时 THEN MCP 必须通过原子 rename 或等价本地文件系统操作把 staging release 发布为 `demo-scenarios/releases/<release-id>/`。
- R2.AC3: IF 任一 error 级 gate 失败 THEN MCP 必须删除或隔离 staging release，并不得修改 `active.pointer.json` 或 `previous.pointer.json`。
- R2.AC4: WHEN release 已经发布到 `releases/<release-id>/` 后 THEN writer 不得就地修改该 release 下的 `manifest.json`、`provenance.json`、`slices/`** 或已声明 artifact；需要变化时必须创建新 release。
- R2.AC5: IF 发布目标 `releases/<release-id>/` 已存在 THEN MCP 必须返回结构化 blocker，要求换用新 releaseId 或确认该 release 已不可变，不得覆盖旧 release。

### R3: 定义 pointer 文件和 v2 fallback 语义

**用户故事:** 作为现场排障人员，我希望 active/previous 只是一小份可检查的指针文件，以便快速判断当前离线壳正在加载哪个 release，并在 active 坏掉时安全回退。
**验收标准 (EARS):**

- R3.AC1: WHEN 写入 `active.pointer.json` 或 `previous.pointer.json` 时 THEN 文件必须至少包含 `formatVersion`、`releaseId`、`manifestPath`、`manifestSha256`、`activatedAt`、`contractFingerprint` 和 `scenarioFingerprint`。
- R3.AC2: WHEN runtime 读取 pointer 时 THEN 必须校验 pointer schema、releaseId 安全字符集、manifestPath 位于 `demo-scenarios/releases/<release-id>/manifest.json`，并拒绝绝对路径、`..` 路径穿越和跨 release 指向。
- R3.AC3: WHEN active pointer、manifest、slice 读取、hash 校验或 import 失败时 THEN runtime 必须尝试 `previous.pointer.json`，并把 active 失败原因记录为 fallback reason。
- R3.AC4: IF active pointer 和 previous pointer 都不可用或校验失败 THEN runtime 必须回退到随 dist 输出的固定路径文件型 bundle default v2 release：`demo-scenarios/releases/bundle-default/manifest.json`，并通过同一套 manifest/slices/hash/import 流程加载，不得尝试 v1 `previous.json`、`default.pointer.json` 或 JS 内置默认数据旁路。
- R3.AC5: WHEN MCP 激活新 release 时 THEN 必须先把当前 active pointer 复制或写入为 previous pointer，再原子替换 active pointer；如果当前 active pointer 不存在，则 previous pointer 可以不存在但必须记录审计事件。

### R4: 建立 descriptor manifest 和 root hash 校验

**用户故事:** 作为维护者，我希望 manifest 能像内容清单一样描述每个 slice、artifact 和未来 recipe 的 hash、大小和语义，以便 review、diff、局部修复和完整性校验都有稳定根。
**验收标准 (EARS):**

- R4.AC1: WHEN 生成 `manifest.json` 时 THEN 必须包含 `formatVersion: 2`、`releaseId`、`scenarioId`、`schemaVersion`、`contractFingerprint`、`generatorVersion`、`seed`、`generatedAt`、`scenarioFingerprint`、`rootSha256` 和 descriptor 列表。
- R4.AC2: WHEN manifest 记录 descriptor 时 THEN 每个 descriptor 必须至少包含 `kind`、`name`、`mediaType`、`path`、`sha256`、`sizeBytes`、`schemaVersion`，并按 kind 扩展记录 `sourcePath`、`module`、`recordCount` 或 artifact metadata。
- R4.AC3: WHEN 计算 descriptor hash、manifest hash 或 root hash 时 THEN 必须使用 canonical JSON 或等价稳定序列化规则，避免 key 顺序、格式化空白或自引用字段导致不可复现。
- R4.AC4: WHEN runtime 或 MCP dry-run 校验 release 时 THEN 必须重新计算每个 descriptor 的 sha256、sizeBytes 和 manifest root hash；任一不一致必须 error。
- R4.AC5: WHEN manifest 为未来能力预留 descriptor 类型时 THEN 可以声明 `blueprint`、`scenario-graph`、`recipe` 或其他 artifact mediaType，但本 spec 不得要求 runtime 展开 recipe 或解析完整 Scenario Graph。

### R5: 按 table/sourcePath 拆分可导入 slices

**用户故事:** 作为代码审阅者，我希望每个业务数据 slice 都保持在可 review 的文件尺寸内，以便不再面对持续膨胀的单个 `active.json`。
**验收标准 (EARS):**

- R5.AC1: WHEN v2 release materialize 当前场景数据时 THEN 必须至少按 `auth`、`system`、`project.projects`、`project.versions`、`project.topologies`、`simulation.sessions`、`simulation.messages`、`simulation.bandwidth`、`simulation.alarms`、`simulation.faults`、`simulation.events`、`simulation.streamFrames` 拆分 slice 或使用等价 sourcePath 粒度。
- R5.AC2: WHEN slice 对应 IndexedDB mapping sourcePath 时 THEN manifest descriptor 的 `sourcePath` 必须与 `demo-contract/contract.json` 中的 mapping 可对齐，runtime 组装出的 `DemoScenarioPackage` 必须满足现有 schema 和 importer 输入要求。
- R5.AC3: WHEN 某个 slice 超过约 2000 行或 200KB 时 THEN generator 必须按 table、journey、时间窗口或稳定 shard 规则继续拆分，并在 manifest 中记录 shard 顺序和 sourcePath 归属。
- R5.AC4: WHEN slice 被物化而不是由未来 recipe 推导时 THEN descriptor 必须记录 `materializationReason`，例如 `copied-default`、`semantic-generated`、`runtime-required`、`reviewability` 或 `recipe-not-yet-supported`。
- R5.AC5: IF 一个 slice 文件为空但 contract 要求对应 table `minItems` 大于 0 THEN manifest validation 或 import dry-run 必须返回 error，并禁止 pointer 切换。

### R6: 保持内部 DemoScenarioPackage 与 IndexedDB 导入模型稳定

**用户故事:** 作为前端维护者，我希望 v2 只改变外部包格式，不改变页面和 API mock 的数据读取方式，以便 Release Store 改造不会扩散到 UI 和业务服务层。
**验收标准 (EARS):**

- R6.AC1: WHEN runtime 成功读取 v2 release 时 THEN 必须把 manifest/slices 组装成现有 `DemoScenarioPackage` 或等价 importer 输入，再调用 `ScenarioRepository.ensureScenario()` 导入 IndexedDB。
- R6.AC2: WHEN 页面、service、repository 或 MSW handler 读取演示数据时 THEN 它们不得直接读取 `active.pointer.json`、`manifest.json`、`slices/`**、`provenance.json`、`timeline.json`、blueprint、graph 或 recipe 文件。
- R6.AC3: WHEN `real`、`fallback`、`build:prod` 或普通开发模式运行时 THEN v2 Release Store 不得改变真实后端访问、开发态 fallback mock、生产构建或非 demo-offline 行为。
- R6.AC4: WHEN `source-generated` 开发流程被使用时 THEN 它可以继续作为源码场景开发与测试入口，但不得被当作新 `offline-static` 外部 runtime package 兼容格式。
- R6.AC5: IF runtime 组装出的 `DemoScenarioPackage` 无法通过 schema、contract 或 import 校验 THEN loader 必须回退到 previous pointer 或 bundle default v2 release，不能让页面白屏。

### R7: 建立 provenance 生成证明和语义报告 artifact 绑定

**用户故事:** 作为质量负责人，我希望每个 release 都能说明它由什么输入、工具版本、契约和校验结果生成，以便后续审计和复现时不只依赖文件名猜测。
**验收标准 (EARS):**

- R7.AC1: WHEN MCP 写入 release 时 THEN 必须生成 `provenance.json`，记录 `topic` 或 topic 摘要、`businessDescription` hash、`topicKey`、`seed`、`contractFingerprint`、`generatorVersion`、semantic generator/report 版本、生成时间和质量 gate 摘要。
- R7.AC2: WHEN release 包含 Spec A 的 semantic quality report 时 THEN report 必须作为 artifact descriptor 进入 manifest，并记录 `sha256`、`sizeBytes`、`mediaType` 和相对路径。
- R7.AC3: WHEN provenance 引用输入摘要时 THEN 不得写入 API key、本机绝对路径、用户私密数据或需要联网解析的远程 `$ref`。
- R7.AC4: IF provenance 缺失、schema 无效或与 manifest 中记录的 descriptor hash 不一致 THEN MCP activation 必须失败，runtime 对该 release 必须视为不可用。
- R7.AC5: WHEN MCP 返回 customer-facing result 时 THEN 必须包含 releaseId、active pointer path、manifest path、provenance path、semantic report artifact path 和 validation summary，便于 AI Agent 或人工定位。

### R8: 建立 timeline 审计但不让 timeline 进入启动关键路径

**用户故事:** 作为维护者，我希望 release 激活、回退和清理有可审计记录，但浏览器启动不被审计日志损坏拖累，以便可靠性和可追溯性同时成立。
**验收标准 (EARS):**

- R8.AC1: WHEN MCP staging、verify、activate、rollback 或 future GC release 时 THEN 必须向 `demo-scenarios/timeline.json` 或等价 timeline 日志追加结构化事件。
- R8.AC2: WHEN 写 timeline 事件时 THEN 事件必须至少包含 `eventId`、`eventType`、`releaseId`、`time`、`actor`、`manifestSha256` 和结果摘要。
- R8.AC3: WHEN runtime 启动时 THEN 不得依赖 timeline 文件完成 active release 加载；timeline 缺失或损坏不得导致演示回退或失败。
- R8.AC4: IF timeline 写入失败但 release、manifest、provenance、hash 和 dry-run 已通过 THEN MCP 可以激活 release，但必须在返回结果和审计日志中记录 timeline warning。
- R8.AC5: WHEN future rollback 或 GC 能力被设计时 THEN 必须基于 pointer 和 manifest 完整性判断，不得只信任 timeline 事件。

### R9: 强化 MCP v2 writer、validator 和 import dry-run

**用户故事:** 作为 MCP 工具使用者，我希望生成、校验、激活 v2 release 的每一步都有结构化结果，以便 AI Agent 能自动修复可修复问题，而不是手改 JSON。
**验收标准 (EARS):**

- R9.AC1: WHEN `demo_offline_generate_demo` 或 runtime 专用生成工具接收 `target.kind=offline-static` 时 THEN 必须默认生成 v2 release store；如保留 `packageFormat` 参数，则唯一允许值必须是 `v2` 或省略。
- R9.AC2: WHEN v2 writer 写入文件时 THEN 写权限必须继续限制在 `demo-scenarios/`**，且必须拒绝 index.html、assets、绝对路径、路径穿越和 symlink escape。
- R9.AC3: WHEN validate/dry-run 工具校验 v2 release 时 THEN 必须覆盖 pointer schema、manifest schema、descriptor hash、provenance schema、slice schema、invariants、semantic quality issue summary 和 IndexedDB import dry-run。
- R9.AC4: IF 任一 error 级校验失败 THEN MCP 必须返回包含 `path`、`code`、`severity`、`actual`、`expected` 和 `fixHint` 的结构化 issue，并不得切换 active pointer。
- R9.AC5: WHEN 只有 warning 级 issue 时 THEN MCP 可以发布和激活 release，但 warning 必须进入 result、provenance 或 timeline，且不允许被静默丢弃。

### R10: 输出 bundle default v2 release 并取消 v1 默认包骨架

**用户故事:** 作为离线壳构建维护者，我希望新 build 自带一个可运行的 default v2 release，以便即使客户尚未通过 MCP 生成行业数据，离线壳也能稳定启动。
**验收标准 (EARS):**

- R10.AC1: WHEN `build:demo-offline` 或等价构建流程完成时 THEN `dist-demo-offline/demo-scenarios/`** 必须包含固定路径 `releases/bundle-default/manifest.json` 对应的文件型 bundle default v2 release、`active.pointer.json` 和完整 manifest/slices/provenance。
- R10.AC2: WHEN default v2 release 生成时 THEN 它必须来自现有 `defaultDemoScenario` 或等价默认场景，并通过 v2 manifest、descriptor hash 和 import dry-run 校验。
- R10.AC3: WHEN default v2 release 被 runtime 作为 fallback 使用时 THEN selection source 必须能区分 `runtime-active-v2`、`runtime-previous-v2` 和 `bundle-default-v2` 或等价诊断值，且 `bundle-default-v2` 必须来自 dist 中 `demo-scenarios/releases/bundle-default/manifest.json` 指向的 release 文件而不是 JS 内置默认数据或 `default.pointer.json`。
- R10.AC4: IF 构建产物仍包含 v1 `active.json`、`previous.json` 或 `active.meta.json` THEN hard-cut-v1-absence 检查必须失败，除非这些文件位于测试 fixture 或历史文档目录而非新 dist 输出。
- R10.AC5: WHEN default v2 release 的 contractFingerprint 与当前 shell 不一致 THEN runtime 必须拒绝该 release 并输出结构化错误；构建测试必须覆盖该场景。

### R11: 管控 release store 增长和未来 GC 边界

**用户故事:** 作为长期维护者，我希望 release store 可以不断追加不可变 release，同时有清晰保留和清理规则，以便 v2 不会从单文件膨胀变成无限目录膨胀。
**验收标准 (EARS):**

- R11.AC1: WHEN 本 spec 设计 release retention 时 THEN 必须规定不得删除 active pointer 或 previous pointer 当前指向的 release。
- R11.AC2: WHEN future GC 被实现时 THEN 默认至少保留最近 N 个 verified release 或最近一段时间内的 release，具体 N 和时间窗口必须可配置并有安全默认值。
- R11.AC3: IF 某个 release 被 manifest、pointer、timeline 或 provenance 引用且仍在保留策略内 THEN GC 不得删除该 release。
- R11.AC4: WHEN release store 大小超过建议阈值时 THEN MCP 可以返回 warning 和 cleanup hint，但不得在本 spec 中自动删除 release，除非 future GC 任务被单独批准。
- R11.AC5: WHEN 本 spec 的 tasks 拆分时 THEN GC 只需要完成规则、诊断或轻量 warning，不得阻塞 v2 loader/writer 主路径。

### R12: 建立 v2-only 自动化测试矩阵

**用户故事:** 作为验收负责人，我希望第三个 spec 的测试能证明新格式确实硬切 v2，并且完整覆盖 loader、writer、hash、fallback 和无 v1 行为，以便后续实现不会悄悄退回双格式兼容。
**验收标准 (EARS):**

- R12.AC1: WHEN 编写前端 runtime tests 时 THEN 必须覆盖 active v2 成功、active v2 hash 失败回退 previous v2、previous v2 失败回退 bundle default v2、timeline 损坏不影响启动、v1 文件存在但被忽略。
- R12.AC2: WHEN 编写 MCP offline-static tests 时 THEN 必须覆盖 staging 写入、release 发布、manifest/root hash 校验、pointer 原子切换、previous pointer 保留、provenance 缺失失败、semantic report artifact hash 失败。
- R12.AC3: WHEN 编写构建或 contract exporter tests 时 THEN 必须验证新 dist 输出 default v2 release store，并验证 v1 `active.json`、`previous.json`、`active.meta.json` 不存在于新外部 runtime package 输出。
- R12.AC4: WHEN 运行回归命令时 THEN 必须至少运行 `cd tools/demo-offline-mcp && npm test -- --run` 以及受影响的 frontend runtime/scenario tests；如类型定义变更，则必须运行 `cd ruoyi-fastapi-frontend && yarn type-check`。
- R12.AC5: WHEN 本 spec 完成验收记录时 THEN 必须说明 hard-cut v2-only、no v1 migration、no v1 fallback、IndexedDB 导入稳定、页面/MSW 不感知 v2、release immutability 和 pointer fallback 的验证结果。

## 非目标

- 不兼容 v1 `active.json`、`previous.json`、`active.meta.json` 外部 runtime package。
- 不提供 v1 -> v2 migration 工具，因为当前没有真实业务客户依赖 v1 外部包格式。
- 不维护 v1/v2 双格式 runtime loader、MCP writer 或测试矩阵。
- 不实现 DOMC registry、generator adapter registry 或缺失 DOMC blocker。
- 不实现完整 Scenario Graph、Generator Recipes、recipe expansion runtime 或少物化展开引擎；本 spec 只预留 descriptor/mediaType 扩展点。
- 不新增业务模块、Vue 页面、MSW handler、service/repository、IndexedDB table、后端 API 或真实生产 seed target。
- 不要求浏览器 runtime 加载 MCP server、AI provider SDK、API key、远程 registry、签名服务或联网生成逻辑。
- 不把 timeline 作为 runtime 启动必需输入；timeline 只用于审计、诊断和未来 rollback/GC 参考。
- 不把 gzip、br 或其他压缩视为解决 review、diff、局部修复、局部回滚和生成质量问题的核心方案。
- 不改变 `real`、`fallback`、`build:prod`、普通开发模式或 `source-generated` 开发流程的职责边界。

## Clarifications

### Session 2026-04-29

- Q: 第三个 spec 是否继续兼容 v1 `active.json`？ -> A: 否。当前没有真实业务客户依赖 v1 外部包格式，因此新 `demo-offline` 外部 runtime package 硬切到 v2 Release Store。
- Q: 是否需要 v1 -> v2 migration 工具？ -> A: 不需要。没有业务使用就不做迁移；v1 P0 只作为实现参考和历史基线。
- Q: 硬切是否意味着页面、MSW、service/repository 也要改？ -> A: 否。硬切只发生在外部 runtime package 格式边界；内部仍组装为 `DemoScenarioPackage` 并导入 IndexedDB。
- Q: 是否保留 previous fallback？ -> A: 保留，但只保留 v2 `previous.pointer.json`，不保留 v1 `previous.json` fallback。
- Q: timeline 是否参与浏览器启动？ -> A: 不参与。runtime 启动只依赖 pointer、manifest、slices 和 bundle default v2 release；timeline 损坏只影响审计诊断。
- Q: 是否在本 spec 实现 Recipes？ -> A: 不实现。manifest descriptor 预留 recipe mediaType，但 recipe 展开属于后续 Scenario Graph/Recipes spec。
- Q: 为什么要求 provenance？ -> A: release store 长期可维护不只需要 hash，还需要能说明输入、seed、contract、generator 版本和质量 gate 结果，便于复现与审计。
- Q: 研究参考是什么？ -> A: 参考 OCI Image Spec 的 descriptor/layer、Apache Iceberg/Delta/Hudi 的 snapshot/timeline、TUF 的 metadata/hash 防混搭和 SLSA provenance 的生成证明；本实现保持本地离线轻量化，不引入远程 registry 或签名体系。
- Q: bundle default v2 release 是外部 release 文件还是 JS 内置 fallback？ -> A: 选择外部默认 release 文件。`build:demo-offline` 必须随 dist 输出 default v2 release，runtime fallback 仍通过 manifest/slices/hash/import 同一流程加载。
- Q: active/previous pointer 都坏掉时如何定位 bundle default v2 release？ -> A: 使用固定 releaseId/path：`demo-scenarios/releases/bundle-default/manifest.json`。不新增 `default.pointer.json`，也不从构建注入配置读取。


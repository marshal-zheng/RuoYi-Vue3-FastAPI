# Demo Offline Runtime Package v2 Release Store 实现任务

- 1. 建立 v2 Release Store 类型、常量和 canonical hash 基础
  - 类别：contract/schema。
  - 在前端新增 `src/demo/scenarios/release-store.ts` 或等价模块，定义 `RuntimePackagePointer`、`RuntimePackageV2Manifest`、slice/artifact/provenance descriptor、v2 source/load stage 类型。
  - 在 MCP 侧新增 `tools/demo-offline-mcp/src/offline-static/release-store.ts` 或等价模块，镜像 v2 文件模型，避免直接跨 workspace 运行时依赖。
  - 定义固定路径常量：`demo-scenarios/active.pointer.json`、`previous.pointer.json`、`releases/bundle-default/manifest.json`、`releases/.staging/<release-id>/`。
  - 复用并扩展现有 canonical JSON / SHA-256 工具，支持 descriptor hash、manifest root hash、pointer manifest hash 和 canonical sizeBytes。
  - 实现 releaseId、manifestPath、descriptor path、mediaType、rootSha256 的基础校验函数。
  *需求追溯: R3.AC1, R3.AC2, R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R7.AC4*
- 1. 实现 DemoScenarioPackage 与 v2 slices 的拆分和组装器
  - 类别：contract/schema。
  - 实现 `splitScenarioPackageToSlices()`，按 contract sourcePath 生成 `auth`、`system`、`project.`*、`simulation.*` slices，并记录 sourcePath、module、recordCount、materializationReason 和 order。
  - 实现 `assembleScenarioPackageFromRelease()`，按 manifest descriptor 读取 slices，校验 hash/size/path 后组装回现有 `DemoScenarioPackage`。
  - 支持同一 sourcePath 的多 shard 按 order 稳定拼接，为超过 2000 行或 200KB 的 slice 预留拆分策略。
  - 组装后必须调用现有 `validateDemoScenarioPackage()` 或 MCP 侧等价 schema validation。
  - 对 minItems > 0 但 slice 为空、sourcePath 缺失、重复 shard order、未知 module 或未知 kind 返回结构化 issue。
  *需求追溯: R5.AC1, R5.AC2, R5.AC3, R5.AC4, R5.AC5, R6.AC1, R6.AC5*
- 1. 将前端 RuntimeScenarioPackageLoader 硬切为 v2-only
  - 类别：runtime loader。
  - 重构 `src/demo/runtime/scenario-package-loader.ts`，移除 v1 `active.json`、`active.meta.json`、`previous.json` 读取路径和 meta 校验路径。
  - 实现 active pointer -> previous pointer -> fixed bundle default manifest 的加载顺序。
  - 对 pointer schema、manifest path、contractFingerprint、scenarioFingerprint、manifest rootSha256、descriptor hash/size 和 import failure 分阶段产生 `RuntimeScenarioLoadIssue`。
  - v1 残留文件存在时不得 fetch、parse 或 fallback；只在诊断中允许标记 legacy residue。
  - 确保 timeline 缺失或损坏不参与 loader 决策。
  *需求追溯: R1.AC2, R1.AC4, R3.AC2, R3.AC3, R3.AC4, R6.AC1, R6.AC5, R8.AC3, R10.AC3, R12.AC1*
- 1. 更新 runtime state、repository import context 和显式 reset 边界
  - 类别：repository/importer。
  - 更新 `RuntimeScenarioSource`、`RuntimeScenarioLoadStage`、`RuntimeScenarioSelection` 和 `DemoScenarioImportContext`，支持 `runtime-active-v2`、`runtime-previous-v2`、`bundle-default-v2`。
  - 确认 `ScenarioRepository.ensureScenario()` 只接收组装后的 `DemoScenarioPackage`，不感知 pointer、manifest 或 slices。
  - 调整 `initializeDemoRuntimeState()` 传递 v2 source、contract fingerprint、fallback reason 和 validation summary。
  - 处理 `resetDemoRuntimeScenario()`：在 demo-offline 中应通过 fixed bundle default v2 release 重置，或明确仅测试/开发工具可使用源码 `defaultDemoScenario`，不得成为 runtime fallback 旁路。
  - 保持页面、service、repository、MSW handler 不直接读取 release store 文件。
  *需求追溯: R6.AC1, R6.AC2, R6.AC3, R6.AC4, R10.AC3, R12.AC5*
- 1. 重构 build:demo-offline contract exporter 输出 bundle-default v2 release
  - 类别：build/exporter。
  - 更新 `vite/plugins/demo-offline-contract.ts`，继续输出 `demo-contract/contract.json`、`scenario.schema.json`、`default-scenario.json`。
  - 移除对 `demo-scenarios/active.json` 和 `active.meta.json` 的写入。
  - 使用 v2 release builder 将 `defaultDemoScenario` 写入 `demo-scenarios/releases/bundle-default/*`*，生成 manifest、provenance 和 slices。
  - 写入 `active.pointer.json` 指向 `bundle-default`，并校验 pointer.manifestSha256 与 manifest.rootSha256。
  - 增加 hard-cut-v1-absence 构建检查，确保新 dist runtime 输出不存在 v1 `active.json`、`previous.json`、`active.meta.json`。
  *需求追溯: R1.AC1, R1.AC2, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5, R12.AC3*
- 1. 扩展 MCP offline-static 路径模型和写入安全边界
  - 类别：MCP writer。
  - 更新 `tools/demo-offline-mcp/src/offline-static/paths.ts`，新增 active/previous pointer、timeline、releasesRoot、stagingRoot、failedRoot、bundleDefaultManifestPath 等路径。
  - 删除或废弃 offline-static v1 专用 `activePath`、`activeMetaPath`、`previousPath`、`activeNextPath`、`activeNextMetaPath` 对新流程的依赖。
  - 扩展 path guard，继续只允许写 `demo-scenarios/*`*，拒绝 `index.html`、`assets/**`、绝对路径、`..`、跨 release path 和 symlink escape。
  - 对已存在 `releases/<release-id>/` 返回 blocker，不允许覆盖不可变 release。
  - 对 legacy v1 residue 只返回 warning 或审计信息，不作为读取输入。
  *需求追溯: R1.AC3, R1.AC4, R2.AC1, R2.AC4, R2.AC5, R3.AC2, R9.AC2, R11.AC1*
- 1. 实现 MCP v2 release writer、staging 发布和 pointer 激活
  - 类别：MCP writer。
  - 新增 `release-writer.ts` 或重构现有 offline-static writer，实现 `.staging/<release-id>` 写入、校验通过后 rename 到 `releases/<release-id>`。
  - 发布前写入 manifest、provenance、slices 和可选 semantic report artifact。
  - 任一 error gate 失败时删除或隔离 staging release，不修改 active/previous pointer。
  - 激活时先把当前 active pointer 复制或写为 previous pointer，再原子替换 active pointer；没有当前 active 时记录审计事件。
  - 发布后 release 目录不可变；任何变化必须生成新 releaseId。
  *需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R3.AC1, R3.AC5, R9.AC4*
- 1. 实现 provenance、semantic report artifact 和 timeline 审计
  - 类别：contract/schema。
  - 为每个 release 生成 `provenance.json`，记录 topic/topic summary、businessDescription hash、topicKey、seed、contractFingerprint、generatorVersion、semantic report hash、materials 和 validation summary。
  - 将 Spec A semantic quality report 作为 artifact descriptor 写入 manifest，校验 sha256、sizeBytes 和 mediaType。
  - 校验 provenance schema、descriptor hash 和敏感信息安全，不允许 API key、本机绝对路径、私密数据或远程 `$ref`。
  - 写入 `timeline.json` 或 JSONL timeline，记录 staged、verified、activated、warning 等事件。
  - timeline 写入失败只能产生 warning，不得阻塞已经通过 gates 的 release activation。
  *需求追溯: R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5, R8.AC1, R8.AC2, R8.AC3, R8.AC4, R8.AC5*
- 1. 重构 MCP validate/dry-run/activate tools 为 v2-only
  - 类别：MCP tools。
  - 更新 `demo_offline_generate_demo`、`demo_offline_generate_runtime_demo`、`demo_offline_validate_runtime_package`、`demo_offline_dry_run_runtime_package`、`demo_offline_activate_runtime_package` 的 offline-static 分支。
  - `target.kind=offline-static` 默认 v2；如保留 `packageFormat`，只允许省略或 `v2`，其他值返回 blocker。
  - validate/dry-run 从 pointer、releaseId 或 staging release 读取 v2 release，组装 package 后复用 schema、contract、invariant 和 IndexedDB import dry-run。
  - customer-facing result 返回 releaseId、activePointerPath、previousPointerPath、manifestPath、provenancePath、semanticReportPath、validationSummary、dryRunSummary、warnings 和 artifacts。
  - 更新错误文案，不再出现 “active.json was not changed” 作为 v2 激活主信息。
  *需求追溯: R1.AC3, R7.AC5, R9.AC1, R9.AC3, R9.AC4, R9.AC5, R12.AC2*
- 1. 建立 release retention 与 GC warning 边界
  - 类别：MCP diagnostics。
  - 在 manifest/pointer/timeline 诊断中实现 retention 规则校验：active/previous 指向的 release 不得删除。
  - 定义安全默认值，例如保留最近 N 个 verified release 或最近一段时间内的 release；本任务只写规则和 warning，不自动删除。
  - 当 release store 超过建议阈值时，MCP 返回 cleanup hint 和可审计 warning。
  - future rollback/GC 设计必须基于 pointer 和 manifest 完整性，不得只信任 timeline。
  - 在 tasks 和结果说明中明确 GC 不阻塞 v2 loader/writer 主路径。
  *需求追溯: R8.AC5, R11.AC1, R11.AC2, R11.AC3, R11.AC4, R11.AC5*
- 1. 增加前端 v2 runtime 和 build/exporter 测试矩阵
  - 类别：test matrix。
  - 更新 `scenario-package-loader.test.ts` 覆盖 active v2 成功、active hash 失败回退 previous、previous 失败回退 fixed bundle-default、timeline 损坏不影响启动、v1 文件存在但未被 fetch。
  - 更新 runtime state/repository 相关测试，覆盖 v2 source 诊断值和 fallback reason。
  - 更新 contract/exporter 测试，验证 `build:demo-offline` 产物包含 `active.pointer.json`、`releases/bundle-default/manifest.json`、provenance 和 slices。
  - 增加 hard-cut-v1-absence 测试，验证新 dist 不输出 v1 `active.json`、`previous.json`、`active.meta.json`。
  - 覆盖 bundle-default contractFingerprint mismatch 被拒绝。
  *需求追溯: R1.AC1, R1.AC2, R1.AC4, R3.AC3, R3.AC4, R6.AC5, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5, R12.AC1, R12.AC3*
- 1. 增加 MCP v2 release store 测试矩阵
  - 类别：test matrix。
  - 更新 `tools/demo-offline-mcp/tests/offline-static.test.ts`，覆盖 staging 写入、release 发布、已存在 releaseId blocker、pointer 原子切换、previous pointer 保存。
  - 覆盖 manifest root hash、descriptor hash、provenance hash、semantic report artifact hash 错误失败。
  - 覆盖 schema/contract/invariant/import dry-run 任一 error 不切 active pointer。
  - 覆盖 warning-only release 可以激活且 warning 进入 result/provenance/timeline。
  - 覆盖 path guard 拒绝 `assets/*`*、`index.html`、绝对路径、`..`、symlink escape 和跨 release descriptor path。
  - 覆盖 legacy v1 residue ignored/warning，不作为 v2 输入。
  *需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R3.AC1, R3.AC2, R3.AC5, R4.AC4, R7.AC4, R9.AC2, R9.AC3, R9.AC4, R9.AC5, R12.AC2*
- 1. 更新旧 v1 命名、提示和文档索引中的实现边界
  - 类别：documentation governance。
  - 更新 MCP README、tool 描述、错误文案和 runbook 中 offline-static v1 `active.json` 相关描述，改为 v2 Release Store。
  - 保留 P0 spec 作为历史文档，不回写修改已完成 P0 spec；在当前 spec 验收记录中说明 hard-cut 例外。
  - 如 `docs/specs/README.md` 仍把 Spec B 描述为 v1 旁路兼容，应追加当前 spec 的 hard-cut v2-only 决策说明。
  - 将 semantic validator fixHint 中 “editing/regenerating active.json” 的面向 v2 用户文案改为 “regenerate v2 release” 或等价表达。
  - 不新增迁移文档，不承诺 v1 -> v2 migration。
  *需求追溯: R1.AC5, R6.AC4, R9.AC1, R12.AC5*
- 1. 执行回归命令并记录验收结果
  - 类别：test matrix。
  - 运行 `cd tools/demo-offline-mcp && npm test -- --run`。
  - 运行受影响的前端 runtime/scenario tests，例如 `cd ruoyi-fastapi-frontend && yarn test:run src/demo/runtime/scenario-package-loader.test.ts src/demo/scenarios/contract.test.ts`。
  - 如类型定义、runtime source 类型或 build 插件变更，运行 `cd ruoyi-fastapi-frontend && yarn type-check`。
  - 记录 hard-cut v2-only、no v1 migration、no v1 fallback、IndexedDB 导入稳定、页面/MSW 不感知 v2、release immutability、fixed bundle-default fallback 和 pointer fallback 验证结果。
  - 确认最终产物没有半写入 staging release、坏 pointer 或 v1 runtime package 回退路径。
  *需求追溯: R12.AC1, R12.AC2, R12.AC3, R12.AC4, R12.AC5*
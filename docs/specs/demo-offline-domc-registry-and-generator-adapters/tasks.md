# Demo Offline DOMC Registry and Generator Adapters 实现任务

## 任务列表

- [x] 1. 修复 MCP 测试编译阻塞并建立实现前基线
  - 删除或合并 `tools/demo-offline-mcp/src/offline-static/writer.ts` 中 `activateRuntimePackage()` 的重复 `loaded` 声明，确保 esbuild transform 不再因重复符号失败。
  - 运行 `cd tools/demo-offline-mcp && npm test -- --run`，记录修复后的基线结果；若仍有非本 spec 失败，先区分 blocker 与后续任务可处理失败。
  - 运行当前受影响的前端 contract/runtime 测试，确认进入 DOMC 改造前 v2 release store 和 runtime loader 基线稳定。
  _需求追溯: R11.AC5_

- [x] 2. 建立前端 DOMC Registry 类型、fingerprint、schema 和基础校验
  - 新增 `ruoyi-fastapi-frontend/src/demo/domc/**`，定义 `DemoDomcRegistry`、module contract、entity、field semantics、UI journey、adapter reference、copyOnly policy、quality gate 等类型。
  - 实现 DOMC canonical fingerprint，排除 `generatedAt` 等非稳定字段，保留 registry/module/adapter 能力变化对 fingerprint 的影响。
  - 新增本地 `domc.registry.schema.json` 生成源与 `validateDemoDomcRegistry()`，拒绝无效 schemaVersion、moduleId、sourcePath、table mapping、adapter reference、远程 `$ref` 和 unsafe export 值。
  - 让 DOMC registry 从现有 `DemoOfflineContractManifest`、IndexedDB mapping、handler coverage、module contracts 和 invariants 演进，避免与 runtime contract 形成第二套事实源。
  _需求追溯: R1.AC1, R1.AC2, R1.AC4, R1.AC5, R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R6.AC1, R6.AC3, R12.AC2_

- [x] 3. 迁移首批 `project`、`simulation`、`auth`、`system` DOMC 模块
  - 为 `project` 编写 DOMC，覆盖 `project.projects`、`project.versions`、`project.topologies` 的主键、字段语义、引用、minItems、页面 journey、invariants、diversity rules 和 adapter 输出边界。
  - 为 `simulation` 编写 DOMC，覆盖 sessions、messages、bandwidth、alarms、faults、events、streamFrames 的 session 引用、时间线顺序、风险解释、详情支撑关系和 semantic anchors。
  - 为 `auth`、`system` 编写 `copyOnly` DOMC，声明默认场景复制来源、最低记录量、handler coverage、UI navigation 支撑关系和不允许语义生成的原因。
  - 增加 DOMC 与现有 contract manifest、scenario schema、handler coverage 和 import dry-run 的漂移校验 fixture。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R7.AC1, R7.AC2, R10.AC2_

- [x] 4. 接入 demo-offline contract exporter 和 contract fingerprint
  - 扩展 `createDemoOfflineContractManifest()`，记录 `domcRegistryFingerprint`、`domcRegistryPath`、`moduleContractFingerprints` 和 `adapterReferences`。
  - 扩展 `ruoyi-fastapi-frontend/vite/plugins/demo-offline-contract.ts`，在 `build:demo-offline` 时输出 `demo-contract/domc.registry.json` 和 `demo-contract/domc.registry.schema.json`。
  - 将 DOMC fingerprint 和 adapter references 纳入 `contractFingerprint` 稳定输入，确保 DOMC/adapter 能力变化会阻止旧 release 与新 shell 混用。
  - 验证 `build:prod`、普通开发、`real` 和 `fallback` 模式不运行 DOMC exporter，也不把 MCP adapter 实现打入浏览器 bundle。
  _需求追溯: R1.AC3, R1.AC4, R1.AC5, R8.AC1, R8.AC5, R12.AC1, R12.AC5_

- [x] 5. 扩展 MCP contract reader 与 DOMC 完整性校验
  - 扩展 `readOfflineStaticContract()` 返回 `domcRegistry`，并校验 registry fingerprint、contract fingerprint、schemaVersion、module fingerprints 和 adapter references。
  - 增加 DOMC sourcePath/table mapping、handler coverage、UI journey、entity/reference/minItems 与 scenario schema 的一致性检查。
  - 定义 `DemoOfflineBlockerIssue`，在现有 `ValidationIssue` 基础上增加 `gate`、`missingArtifacts` 和 `nextActions`，并保持旧 `ToolEnvelope` 兼容。
  - 对缺 DOMC、缺 handler mapping、缺 UI journey、contract drift、DOMC fingerprint mismatch 输出 error 级结构化 blocker。
  _需求追溯: R5.AC3, R5.AC4, R5.AC5, R6.AC2, R6.AC3, R6.AC4, R6.AC5, R12.AC2_

- [x] 6. 建立 MCP 侧 Generator Adapter 接口、注册表和选择机制
  - 新增 `tools/demo-offline-mcp/src/adapters/types.ts` 和 `registry.ts`，定义 adapterId、adapterVersion、supportedModules、supportedDomcVersions、capabilities、inputKinds、outputSourcePaths、canGenerate、plan、compile、validate、explainBlocker。
  - 实现 adapter resolver，按 DOMC adapterRef、版本范围、capability、priority 选择 adapter；多 adapter 冲突或无法唯一选择时返回 blocker。
  - 增加 registry gate，禁止 adapter 直接输出完整 `DemoScenarioPackage`、直接写 v2 release 文件或写入未声明 sourcePath。
  - 保证 adapter 实现只位于 MCP 侧 `tools/demo-offline-mcp/src/adapters/**`，前端 DOMC 仅声明 adapter id/version/capability。
  _需求追溯: R4.AC1, R4.AC2, R4.AC4, R4.AC6, R4.AC7, R5.AC3, R5.AC4, R5.AC6, R11.AC2, R12.AC1_

- [x] 7. 将现有 `project + simulation` 生成链路迁移为首个正式 adapter
  - 新增 `project-simulation` adapter，复用 Spec A 的 Business Blueprint、deterministic seed、`compileBlueprintToIndustryDraft()` 和 semantic anchor binding 能力。
  - 将 adapter 输出改为 sourcePath 级 `AdapterMaterialization[]` 与 `SemanticAnchorBinding[]`，覆盖 project 和 simulation 的全部首批 sourcePath。
  - 在 adapter validate 中校验输出顺序、跨 sourcePath 引用、minItems、primaryKey、requiredFields、semantic anchors 和 DOMC diversity rules。
  - 确保同一 topic/businessDescription/contractFingerprint/domcFingerprint/adapterVersion 输入可复现，且未经校验的 AI 输出不能直接进入最终 records。
  _需求追溯: R3.AC2, R3.AC3, R4.AC1, R4.AC3, R4.AC6, R4.AC7, R7.AC3, R7.AC4, R7.AC5, R12.AC3, R12.AC4_

- [x] 8. 建立共享 assembler 并改造 MCP generation planner
  - 新增或拆分 shared assembler，从 default scenario 复制 `copyOnly` sourcePath，并按 DOMC/adapter order 合并 generated materializations。
  - 禁止 assembler 写入 DOMC 未声明 sourcePath；对 minItems、primaryKey、references、requiredFields、copyOnly policy 和 sourcePath ownership 执行统一校验。
  - 将 `createOfflineStaticPlan()` 与 `createGenerationPlan()` 过渡到 DOMC-driven planner，输出模块级 `generate`、`copy`、`blocked`、`unsupported` trace。
  - 对“全量/全模块/整站”或未知模块请求执行 strict blocker，不使用 generic fallback adapter 或低置信模板数据继续生成。
  - 保持最终产物仍是 `DemoScenarioPackage` 进入既有 schema、contract、invariant、semantic、import dry-run 和 v2 release flow。
  _需求追溯: R4.AC2, R4.AC3, R5.AC1, R5.AC2, R5.AC6, R8.AC2, R8.AC3, R8.AC4, R10.AC3, R10.AC4, R12.AC5_

- [x] 9. 扩展 v2 release provenance、manifest 审计和 export safety
  - 扩展 MCP 与前端两份 release-store 类型，支持 provenance materials 中的 `domc-registry`、`domc-module-contract`、`generator-adapter`。
  - 在 v2 manifest/provenance 中记录 `domcRegistryFingerprint`、`moduleContractFingerprints`、`adapterVersions` 和 adapter capability summary。
  - 让 descriptor 的 sourcePath、module、materializationReason 能追溯到 DOMC module contract 或 copyOnly 规则。
  - 强化 release export safety，拒绝 DOMC/provenance/quality artifact 中的本机绝对路径、secret-like 值、路径穿越和远程 `$ref`。
  - 保持 v2 pointer、manifest、slice、fallback 文件格式语义不被 Spec C 重定义。
  _需求追溯: R4.AC5, R8.AC1, R8.AC2, R8.AC3, R8.AC4, R8.AC5, R9.AC3, R12.AC2_

- [x] 10. 建立新增业务模块 Definition of Done、unsupported/blocker 诊断和文档
  - 在 docs/specs 或 demo-offline 文档中新增业务模块接入 DoD，明确 DOMC、scenario slice/schema、IndexedDB mapping、repository/service、MSW handler、UI journey、invariants、diversity rules、adapter、测试证据和维护 owner。
  - 为未来 `generatable`、`copyOnly`、`unsupported` 模块分别定义完成标准、复制来源、缺口说明和禁止语义生成的规则。
  - 在 MCP scan/planner 诊断中显示 unsupported/blocked 模块缺口，并给出 missingArtifacts 与 nextActions。
  - 明确 Scenario Graph、Generator Recipes、真实后端 seed target、生产数据生成、浏览器端 AI/adapter 执行均不属于本 spec。
  _需求追溯: R5.AC2, R5.AC5, R9.AC1, R9.AC2, R9.AC3, R9.AC4, R9.AC5, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5_

- [x] 11. 补齐前端 contract/exporter/runtime 自动化测试
  - 增加 DOMC registry schema、fingerprint 稳定性、sourcePath/table mapping、handler coverage、invalid DOMC、copyOnly policy 单元测试。
  - 扩展 `src/demo/scenarios/contract.test.ts`，覆盖 DOMC 参与 contract fingerprint、project/simulation generatable、auth/system copyOnly、adapter references 和 module fingerprints。
  - 增加 build/exporter fixture 或测试，验证 `build:demo-offline` 输出 DOMC registry/schema，且无远程 `$ref`、无 adapter 代码进入浏览器 bundle。
  - 扩展 runtime/release-store tests，验证 DOMC/adapter provenance 字段不要求 runtime 读取 DOMC，且 existing v2 fallback/import 行为不变。
  _需求追溯: R1.AC3, R3.AC4, R8.AC3, R11.AC1, R11.AC4, R12.AC1, R12.AC2, R12.AC5_

- [x] 12. 补齐 MCP adapter/planner/generation/release 自动化测试
  - 增加 adapter registry tests：注册、版本兼容、capability 匹配、多 adapter 冲突、缺 adapter blocker、copyOnly 模块处理、adapter 输出未声明 sourcePath blocker。
  - 增加 MCP generation tests：project/simulation 通过 DOMC adapter 生成、auth/system copyOnly、全模块请求 blocker、未知模块 blocker、结构化 `missingArtifacts` 和 `nextActions`。
  - 增加 release/provenance tests：DOMC/adapter fingerprint 记录、descriptor sourcePath 追溯、contract drift 阻止 activation、warning-only gate 保留、export safety。
  - 增加 adapter regression tests：同一输入可复现，不同主题仍保留 Spec A 的 diversity 与 semantic coverage 差异。
  _需求追溯: R3.AC5, R5.AC1, R5.AC2, R5.AC5, R6.AC4, R6.AC5, R11.AC2, R11.AC3, R11.AC4, R12.AC3, R12.AC4_

- [x] 13. 执行最终验收命令并记录实现证据
  - 运行 `cd tools/demo-offline-mcp && npm test -- --run`，确保 MCP 全套通过并覆盖 DOMC/adapter/provenance/blocker 回归。
  - 运行 `cd ruoyi-fastapi-frontend && yarn test:run src/demo/runtime/scenario-package-loader.test.ts src/demo/scenarios/contract.test.ts src/demo/repositories/scenario.test.ts src/demo/runtime/devtools.test.ts`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn type-check`，必要时补充 `yarn build:demo-offline` 验证 dist contract artifacts。
  - 在实现总结中记录 hard boundaries：browser runtime 不加载 DOMC/adapter、no graph/recipes、no backend seed、no production/fallback 行为变化。
  _需求追溯: R10.AC5, R11.AC5, R12.AC5_

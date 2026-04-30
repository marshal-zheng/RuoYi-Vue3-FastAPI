# Demo Offline Runtime Scenario Package 实现任务

- [x] 1. 抽取前端 runtime package 契约、JSON Schema 和 contract 基础常量
  - 在 `ruoyi-fastapi-frontend/src/demo/scenarios/` 下新增静态 `scenario-json-schema.ts`，导出可写入 `demo-contract/scenario.schema.json` 的 JSON Schema Draft 2020-12 对象。
  - 把 `DemoScenarioPackage`、`RuntimeScenarioMeta`、`RuntimeValidationSummary`、`RuntimeScenarioLoadIssue`、module contract、IndexedDB mapping 和 handler coverage 类型集中到可复用模块。
  - 提供 canonical JSON、package sha256、`scenario.fingerprint` 和 `contractFingerprint` helper，确保 `scenario.fingerprint` 只表示数据包内容身份。
  - 保持 `active.json` 格式为纯 `DemoScenarioPackage`，不新增 `{ meta, package }` envelope。
  - 禁止 schema/contract 输出包含 API key、私密数据、绝对路径或远程 `$ref`。
  _需求追溯: R1.AC3, R4.AC1, R4.AC2, R4.AC3, R4.AC5, R4.AC6, R5.AC1, R5.AC2, R5.AC6, R11.AC1, R11.AC2, R11.AC3_

- [x] 2. 在 `build:demo-offline` 中导出通用离线壳随包契约和默认 runtime 数据目录
  - 新增 Vite plugin 或构建后脚本，只在 `mode=demo-offline` 构建时写入 `dist-demo-offline/demo-contract/**` 与 `dist-demo-offline/demo-scenarios/**`。
  - 生成 `demo-contract/contract.json`、`demo-contract/scenario.schema.json`、`demo-contract/default-scenario.json`。
  - 初始化 `demo-scenarios/active.json` 为 bundle default scenario 的纯 JSON 包，并写入对应 `active.meta.json`。
  - 确认 `dist-demo-offline` 的 JS bundle 不再依赖特定客户行业 generated scenario 作为现场换数据主路径。
  - 保持 `build:prod`、`real`、`fallback` 输出和行为不受 runtime package 目录影响。
  _需求追溯: R1.AC1, R1.AC2, R1.AC3, R1.AC5, R2.AC1, R2.AC2, R2.AC4, R2.AC6, R4.AC3, R12.AC1, R12.AC3_

- [x] 3. 实现前端 `RuntimeScenarioPackageLoader` 与 active/previous/default fallback
  - 新增 `src/demo/runtime/scenario-package-loader.ts`，在 `demo-offline` 启动时按 `active.json -> previous.json -> defaultDemoScenario` 选择场景包。
  - fetch 外部 JSON 时使用 `cache: 'no-store'` 或等价版本参数，避免浏览器缓存旧 `active.json`。
  - 对 active 执行 JSON parse、`validateDemoScenarioPackage`、schemaVersion、`active.meta.json.contractFingerprint` 和 package hash 校验。
  - active 任一步失败时记录结构化 fallback reason 并加载 previous；previous 失败时使用 bundle default。
  - 确保 loader 失败不会让页面白屏，最终总能返回可导入的场景包或明确诊断。
  _需求追溯: R2.AC2, R2.AC5, R3.AC1, R3.AC2, R3.AC3, R3.AC5, R3.AC6, R4.AC2, R4.AC4, R5.AC4, R5.AC5, R12.AC5, R13.AC1_

- [x] 4. 扩展 `ScenarioRepository` 导入上下文和 runtime 调试信息
  - 扩展 `ScenarioRepository.ensureScenario()` / `importScenario()`，接收 `source`、`contractFingerprint`、`fallbackReason`、`validationSummary`。
  - 在 Dexie `meta` 表保存当前场景来源、scenario identity、fingerprint、导入时间、contract fingerprint 和 fallback reason。
  - 保持 Dexie transaction 全量清空再写入，避免 active/previous/default 切换后新旧数据混杂。
  - 更新 `initializeDemoRuntimeState()` 使用 `RuntimeScenarioPackageLoader` 结果，而不是直接从编译期 registry 取客户场景。
  - 更新 `window.__DEMO_RUNTIME__`、logger 和相关测试，让现场能看到 `runtime-active`、`runtime-previous`、`bundle-default`。
  _需求追溯: R3.AC4, R3.AC5, R10.AC3, R12.AC5, R13.AC2_

- [x] 5. 保持 MSW、页面 API 和生产模式边界稳定
  - 确认 `src/api/**` 调用签名和业务页面不因 runtime JSON package 引入而变化。
  - 保持 MSW demo handler 为薄适配层，只调用 demo service/repository，不直接解析 `demo-scenarios/*.json`。
  - 保持未覆盖 `/api/**` 的 `DEMO_API_NOT_IMPLEMENTED` 或既有未实现诊断，不允许 MCP 临时伪造 handler。
  - 确认 `real`、`fallback`、`build:prod` 不加载外部 runtime package、MCP server 或 AI provider 逻辑。
  - 在 target adapter 设计中保留未来 backend-api seed target 插槽，但不让它替代 offline-static 主链路。
  _需求追溯: R1.AC5, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5, R10.AC6_

- [x] 6. 新增 MCP offline-static target 路径解析与 contract reader
  - 在 `tools/demo-offline-mcp/src/targets/` 下新增 `source-generated` 与 `offline-static` target adapter 抽象。
  - 为 offline-static target 解析 `targetRoot`、`demo-scenarios/`、`demo-contract/`、`active.json`、`active.meta.json`、`previous.json`、`active.next.json`。
  - 读取 `demo-contract/contract.json`、`scenario.schema.json`、`default-scenario.json`，缺失或不兼容时返回 blocker。
  - 写入权限只允许 `targetRoot/demo-scenarios/**`，拒绝 `assets/**`、`index.html`、任意系统路径、`..` 和 symlink escape。
  - 保留当前源码仓库 candidate/promote 路径作为 `source-generated` target，不破坏开发模式。
  _需求追溯: R2.AC3, R2.AC6, R4.AC3, R4.AC6, R5.AC1, R5.AC2, R5.AC6, R6.AC1, R6.AC3, R6.AC7, R10.AC5, R11.AC4, R11.AC6_

- [x] 7. 扩展 MCP 生成核心以支持 topicKey、seed 和 offline-static 编译
  - 从自然语言 topic、businessDescription、当前 metadata 或 contract registry 推导 `topicKey` 和内部 scenario identity，不要求用户输入 `scenarioId`。
  - 基于 `topicKey + businessDescription + contractFingerprint + generatorVersion` 计算稳定 seed。
  - 复用现有 draft validator/compiler，让 AI 只生成业务语义草稿，最终 `DemoScenarioPackage` 由代码确定性生成。
  - 让 compiler 在可推导字段缺失时自动规范化或补齐，在缺少业务语义或 contract 时返回 blocker。
  - 同一 topic、businessDescription、contractFingerprint、generatorVersion 下尽量生成相同 package；contract 或 generatorVersion 变化时 seed/fingerprint 可解释变化。
  _需求追溯: R6.AC2, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5, R7.AC6, R8.AC1, R8.AC2, R8.AC3, R8.AC4, R8.AC6, R11.AC4_

- [x] 8. 实现 project/version/topology/simulation invariant validator
  - 新增 `tools/demo-offline-mcp/src/offline-static/invariants.ts`，校验 P0 `project`、`version`、`topology`、`simulation` required fields 和最小记录数。
  - 校验每个 version 引用存在 project，每个可见 project 至少有一个 version。
  - 校验 topology 引用存在 project/version，graph 满足最小节点/边结构。
  - 校验 session、message、bandwidth、alarm、fault、event、streamFrame 均引用有效 session/project/version 关系。
  - 校验项目列表、版本详情、拓扑查看、仿真只读演示链路至少有一条完整可运行数据链。
  - 所有错误返回机器可读 `path`、`code`、`actual`、`expected`、`fixHint`。
  _需求追溯: R7.AC5, R7.AC6, R9.AC1, R9.AC2, R9.AC3, R9.AC4, R9.AC5, R11.AC1, R11.AC2, R11.AC3_

- [x] 9. 实现 Node 侧 IndexedDB import dry-run
  - 在 MCP package 中接入 `dexie` 与 `fake-indexeddb`，或通过等价隔离 runtime 提供 Node 侧 IndexedDB。
  - 新增 `tools/demo-offline-mcp/src/offline-static/import-dry-run.ts`，使用临时 DB 名称导入 candidate package。
  - dry-run 复用或等价实现前端 `ScenarioRepository` 的导入路径和 IndexedDB table mapping。
  - dry-run 成功返回表级写入数量、active scenario 摘要和耗时；失败返回结构化 issue。
  - dry-run 结束后关闭并删除临时 DB，不依赖浏览器页面，不污染用户当前演示库。
  _需求追溯: R3.AC4, R6.AC5, R9.AC6, R9.AC7, R13.AC3, R13.AC5_

- [x] 10. 实现 offline-static writer、active.next 和原子激活
  - 新增 `OfflineStaticWriter`，先写 `active.next.json` 和 `active.next.meta.json`，且 runtime 不把 next 文件当正式数据源。
  - 激活前从磁盘重读 next 文件，依次执行 JSON parse、schema validation、contract validation、invariant validation 和 import dry-run。
  - 任一步失败时不覆盖 `active.json`、`previous.json` 或 `active.meta.json`，返回结构化错误和下一步修复建议。
  - 成功时把旧 `active.json` 复制或移动为 `previous.json`，再原子替换 `active.json` 并写入新的 `active.meta.json`。
  - `active.meta.json` 写入 `scenarioId`、`topicKey`、`schemaVersion`、`contractFingerprint`、`generatorVersion`、`seed`、`generatedAt`、`validationSummary`、`sourceTarget`、package hash。
  - 历史保留依赖 `previous.json`、外部包版本管理或 Git，不通过读取旧 candidate 大 JSON 拼凑稳定性。
  _需求追溯: R2.AC2, R2.AC3, R2.AC4, R2.AC5, R5.AC3, R5.AC5, R6.AC4, R6.AC5, R6.AC6, R8.AC5, R9.AC7, R13.AC3, R13.AC6_

- [x] 11. 扩展 MCP tools、结构化输出和 allowlist 检查
  - 扩展 `demo_offline_generate_demo` 输入，支持 `target.kind = source-generated | offline-static` 和离线包 `target.root`。
  - 新增或扩展 `demo_offline_validate_runtime_package`、`demo_offline_dry_run_runtime_package`、`demo_offline_activate_runtime_package`。
  - 保持所有工具返回统一 `ToolEnvelope`，并在失败时给 Chat Agent 可修复的 `path/code/actual/expected/fixHint`。
  - 保持命令执行只通过 named check profiles，不提供任意 shell 工具。
  - 在 offline-static 成功链路中返回 `activated`、`contractFingerprint`、`validationSummary`、`dryRunSummary`、changed paths 和审计摘要。
  _需求追溯: R6.AC1, R6.AC5, R6.AC7, R7.AC6, R10.AC6, R12.AC6, R13.AC3, R13.AC5, R13.AC6_

- [x] 12. 保留并回归 source-generated 开发流程
  - 保持现有 `generated/*.ts`、candidate registry、`writeCandidateScenario()`、`runChecks()`、`promoteCandidateScenario()` 可用。
  - 确认源码开发模式仍可用 candidate-focused-tests、type-check 和 `build:demo-offline` 验证 generated 场景。
  - 确认 source-generated 场景可以作为开发测试 fallback，但客户现场换行业数据主路径改为 offline-static。
  - 通过 focused tests 证明新增 offline-static target 不破坏现有 generated registry、MSW handler 和 service/repository 读取路径。
  _需求追溯: R1.AC4, R6.AC7, R10.AC1, R10.AC2, R10.AC4, R13.AC2, R13.AC5_

- [x] 13. 编写离线包交付文档、操作边界和未来模块接入规范
  - 更新或新增 runbook，说明技术人员如何构建通用 `dist-demo-offline` 并交付给非技术人员。
  - 给出非技术人员通过 AI Agent + MCP 输入自然语言主题的示例，不要求理解 `scenarioId`、Git、源码目录或 build 命令。
  - 明确现场必须通过 HTTP 静态服务访问，不支持 `file://` 直开。
  - 说明 active 损坏、生成失败、previous/default fallback 和手动恢复边界。
  - 说明 MCP 写入目录限制、命令 allowlist、审计日志位置和人工确认建议。
  - 写入未来业务模块 Definition of Done：module contract、scenario slice、IndexedDB mapping、repository/service、MSW handler、generator adapter 和 invariants。
  _需求追溯: R2.AC7, R11.AC5, R12.AC1, R12.AC2, R12.AC3, R12.AC4, R12.AC5, R12.AC6_

- [x] 14. 补齐前端 runtime package 测试矩阵
  - 新增 loader 测试覆盖 active 成功、active 失败回 previous、active/previous 都失败回 bundle default。
  - 新增 active/meta fingerprint、contractFingerprint、package hash 缺失和不匹配测试。
  - 新增外部 runtime package 导入 IndexedDB 后 project/simulation service、repository、MSW handler 可读数据测试。
  - 新增 `real`、`fallback`、`build:prod` 不读取 `demo-scenarios/**` 的边界测试。
  - 覆盖 `DEMO_API_NOT_IMPLEMENTED` 未覆盖 API 诊断不被 MCP 临时 handler 改写。
  _需求追溯: R1.AC5, R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R3.AC6, R5.AC4, R5.AC5, R10.AC4, R10.AC5, R13.AC1, R13.AC2, R13.AC4_

- [x] 15. 补齐 MCP offline-static 测试矩阵
  - 新增 target path 测试，覆盖允许写 `demo-scenarios/**` 和拒绝 `assets/**`、`index.html`、绝对路径、`..`、symlink escape。
  - 新增 contract 读取和 `contractFingerprint` 测试，覆盖匹配、缺失、不匹配、schema/invariant/adapter 变化。
  - 新增 invariant validator 测试，覆盖 project/version/topology/simulation 跨引用失败。
  - 新增 import dry-run 测试，覆盖 `fake-indexeddb` 临时 DB 成功导入、失败不覆盖 active、结束后清理。
  - 新增 writer 测试，覆盖 `active.next.json` 写入、校验失败不覆盖、成功原子激活和 previous 备份。
  _需求追溯: R5.AC2, R5.AC5, R5.AC6, R6.AC3, R6.AC4, R6.AC5, R6.AC6, R9.AC1, R9.AC2, R9.AC3, R9.AC4, R9.AC5, R9.AC6, R9.AC7, R13.AC3, R13.AC4_

- [x] 16. 完成 P0 端到端验收和交付报告
  - 执行 `yarn build:demo-offline`，确认 `dist-demo-offline/demo-contract/**`、`demo-scenarios/active.json`、`active.meta.json` 存在。
  - 使用 MCP offline-static target 以“二手电脑回收”或等价业务主题生成 runtime `active.json`，并确认不需要重新 build。
  - 验证 schema validation、contract fingerprint、invariant validation、import dry-run、focused frontend tests、MCP tests、`type-check` 和 `build:demo-offline`。
  - 通过 `yarn preview:demo-offline` 或等价静态 HTTP 服务验证 runtime 来源为 `runtime-active`，项目列表、版本详情、拓扑查看和仿真只读链路可读到新数据。
  - 记录命令、退出码、关键日志、生成路径、fallback/恢复验证和失败项下一步建议。
  _需求追溯: R1.AC1, R1.AC2, R2.AC1, R2.AC6, R9.AC5, R12.AC3, R13.AC1, R13.AC2, R13.AC3, R13.AC4, R13.AC5, R13.AC6_

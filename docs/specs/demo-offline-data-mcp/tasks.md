# Demo Offline Data MCP 实现任务

- [x] 1. 搭建仓库级 TypeScript MCP 工具包骨架
  - 在 `tools/demo-offline-mcp/` 新建独立 TypeScript package，包含 `package.json`、`tsconfig.json`、`src/index.ts`、`tests/` 和 `README.md`。
  - 使用 MCP TypeScript SDK 初始化本地 `stdio` server，并约定 server 只向 `stderr` 输出日志。
  - 添加 build/test/dev 脚本，但不把该 package 接入前端 Vite 运行时、后端 FastAPI 服务或生产构建入口。
  - 确认 MCP server 不读取、不要求、不保存任何 DeepSeek、Kimi、OpenAI、Gemini 等 provider API key。
  - 为工具返回值建立统一 `ToolEnvelope`、artifact 和错误类型。
  _需求追溯: R1.AC1, R1.AC2, R1.AC4, R2.AC1, R2.AC2, R2.AC4_

- [x] 2. 实现路径解析、安全边界和基础错误模型
  - 实现 `ProjectPaths`，解析 `repoRoot`、`frontendRoot`、`demoRoot`、`generatedRoot` 和 `candidateRoot`。
  - 对所有读取路径做仓库根校验，对所有写入路径做 `ruoyi-fastapi-frontend/src/demo/scenarios/generated/**` allowlist 校验。
  - 拒绝 `..`、绝对路径注入、符号链接逃逸和 generated 目录外写入。
  - 实现 `ValidationIssue`、`ToolError`、`CheckResult` 等结构化错误模型，确保错误能给出 `path`、`code`、`actual`、`expected`、`fixHint` 和 `autoRepairable`。
  - 为路径守卫和错误格式补充单元测试。
  _需求追溯: R1.AC3, R6.AC1, R7.AC1, R9.AC1, R10.AC4, R10.AC6_

- [x] 3. 一次性接入 generated scenario registry
  - 新增 `ruoyi-fastapi-frontend/src/demo/scenarios/generated/index.ts`，导出 `generatedScenarioRegistry`。
  - 新增 `ruoyi-fastapi-frontend/src/demo/scenarios/generated/candidates/index.ts`，为候选场景验证保留独立注册入口。
  - 调整 `src/demo/scenarios/index.ts`，只做一次性合并默认场景与正式 generated registry，避免后续 MCP 反复修改主入口。
  - 增加候选场景验证模式的受控加载方式，确保 candidate 未 promote 前不影响默认正式 scenario。
  - 不新增 `dev:demo-offline` 或等价 dev server 入口，并确认 `yarn dev`、`yarn dev:fallback`、`yarn build:prod`、`yarn build:demo-offline` 行为不变。
  _需求追溯: R1.AC5, R7.AC3, R7.AC5, R7.AC7, R9.AC2, R9.AC4_

- [x] 4. 实现 demo-offline 扫描能力与 `demo_offline_scan_context`
  - 扫描 `src/demo/scenarios/schema.ts`、`default.ts`、`index.ts`、`generated/**`、`repositories/scenario.ts`、`handlers/**` 和前端 demo 相关脚本。
  - 输出 `DemoOfflineContext`，包含 safe slices、copied slices、handler 覆盖、现有 scenarios、候选 scenarios、可用脚本和风险列表。
  - 明确 P0 safe slices 仅为 `project + simulation`，`auth/system` 仅从默认场景复制。
  - 对扫描结果做摘要化，返回 evidence path 与关键结构，不把大文件全文塞入工具输出。
  - 对未在 `src/demo/**` 中发现覆盖依据的切片标记为不可安全生成，并保留 `DEMO_API_NOT_IMPLEMENTED` 风险说明。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R3.AC6, R9.AC3_

- [x] 5. 实现生成计划能力与 `demo_offline_create_generation_plan`
  - 定义 `GenerationPlan` 类型，包含 scenario 信息、行业 brief、scope、target counts、copied slices 和 trace。
  - 基于扫描上下文生成默认计划：未指定 scope 时固定为 `project + simulation`，`auth/system` 标记为 copied。
  - 支持局部范围选择，并校验依赖切片不会断裂。
  - 对全亮诉求只纳入扫描判定安全的切片，对 P0 不支持模块输出 `unsupported` 与 trace 原因。
  - 为 brief、scenarioId、数量目标和 unsupported 分支补充单元测试。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R4.AC6, R5.AC1_

- [x] 6. 实现通用 `IndustryDataDraft` schema 与 validator
  - 使用 Zod 定义跨行业 `IndustryDataDraft`，首个验收样例覆盖房地产语境，但 schema 不绑定房地产专属字段。
  - 实现结构校验、上下文校验、关系校验和语义质量校验。
  - 检测非法枚举、占位词、高重复内容、行业语境不匹配、scope 不匹配和项目 key 冲突。
  - 实现可自动修复分支，支持 trim、默认 version、缺失 ownerName 补齐等低风险修复，并返回修复摘要。
  - 确保校验失败时不写 candidate、不启用 scenario，只返回结构化修复报告给 Chat Agent。
  _需求追溯: R5.AC1, R5.AC4, R5.AC6, R5.AC7, R6.AC1, R6.AC2, R6.AC3, R6.AC4, R6.AC5_

- [x] 7. 实现确定性 scenario compiler
  - 从 `defaultDemoScenario` 复制 `auth` 与 `system` 数据。
  - 根据 plan + draft 确定性生成 `DemoScenarioPackage` 的 `project.projects`、`project.versions`、`project.topologies` 和 `simulation.*` 数据。
  - 使用固定 seed 生成稳定 ID、时间、状态、版本、拓扑、session、message、bandwidth、alarm、fault、event 和 stream frame。
  - 自动补齐 AI 草稿中可确定性推导的字段，避免让 AI 直接猜最终结构。
  - 输出后执行结构校验，确保满足 `DemoScenarioPackage`，且不生成 MSW handler、Vue 页面、路由、真实 API 或 IndexedDB 写库脚本。
  - 为相同输入输出稳定性、关联关系和最终数组结构补充单元测试。
  _需求追溯: R5.AC2, R5.AC3, R5.AC5, R5.AC6, R5.AC7, R9.AC1, R9.AC2_

- [x] 8. 实现 candidate 写入与显式 promote
  - 实现 `demo_offline_write_candidate`，只写入 `generated/candidates/<scenario-id>.candidate.ts` 与候选 metadata。
  - 实现候选冲突检测，默认拒绝覆盖已有 candidate，只有显式 `overwriteCandidate` 才覆盖候选。
  - 实现 `demo_offline_promote_candidate`，要求传入 `checksRunId` 和 `confirm: true`，并在检查通过后才写入正式 `generated/<scenario-id>.ts`。
  - 更新 `generated/index.ts` 注册正式 scenario，保持主 `scenarios/index.ts` 不被 MCP 反复改动。
  - 对同名正式 scenario 默认拒绝覆盖，只有显式 `replaceExisting` 才替换。
  - 确保 candidate 通过检查但未 promote 时，当前正式 scenario 保持不变。
  _需求追溯: R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5, R7.AC6, R7.AC7, R9.AC1_

- [x] 9. 实现固定 allowlist 检查执行器与 `demo_offline_run_checks`
  - 定义 named check profiles：`candidate-focused-tests`、`frontend-type-check`、`candidate-demo-offline-build`、`promoted-demo-offline-build`。
  - 使用 `child_process.spawn` 的数组参数和 env 参数执行命令，不接受 Chat Agent 传入任意 shell 字符串。
  - 在 `ruoyi-fastapi-frontend/` 下运行 focused tests、`yarn type-check` 和 `yarn build:demo-offline`。
  - 失败时返回命令 profile、退出码、关键错误片段、日志摘要和下一步建议。
  - 成功时返回 scenario ID、运行模式、推荐预览命令、构建证据，并提醒仍需显式 promote。
  - 拒绝 allowlist 外 profile，并返回允许范围和替代建议。
  _需求追溯: R8.AC1, R8.AC2, R8.AC3, R8.AC4, R8.AC5, R8.AC6, R8.AC8, R10.AC3, R10.AC4, R10.AC6_

- [x] 10. 注册完整 MCP tools 并完善工具契约
  - 使用 `registerTool` 注册 `demo_offline_scan_context`、`demo_offline_create_generation_plan`、`demo_offline_validate_draft`、`demo_offline_compile_scenario`、`demo_offline_write_candidate`、`demo_offline_run_checks`、`demo_offline_promote_candidate`。
  - 为每个 tool 定义 Zod input schema、结构化输出、tool description 和 annotations。
  - 保证只读工具、写文件工具、执行命令工具在 annotations 和文档中可区分。
  - 确保需要 AI 修复时，工具只返回上下文、错误和修复提示，不在项目内调用模型 API。
  - 使用 MCP Inspector 或等价本地方式验证 stdio server 能正常列出和调用 tools。
  _需求追溯: R1.AC1, R2.AC3, R10.AC1, R10.AC2, R10.AC3, R10.AC4_

- [x] 11. 编写 MCP 客户端接入文档与推荐工作流
  - 在 `tools/demo-offline-mcp/README.md` 中说明 build、启动、stdio 配置和推荐使用流程。
  - 给出 Cherry Studio 或通用 MCP client 配置示例。
  - 标注各工具的只读、写文件、执行命令能力，以及写入目录、命令 allowlist、显式 promote 的人工确认边界。
  - 说明后续 Workbench、CLI 或 AI provider 扩展必须复用 MCP core 能力，并保持 API key 不进入浏览器运行时和客户离线包。
  - 说明未配置 MCP client 时，现有开发与构建命令仍可继续使用。
  _需求追溯: R1.AC5, R9.AC5, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5_

- [x] 12. 补齐 MCP 与前端集成测试
  - 为 `ProjectPaths`、`DemoScanner`、`GenerationPlanner`、`DraftValidator`、`ScenarioCompiler`、`ScenarioWriter` 和 `CheckRunner` 编写单元测试。
  - 为 generated scenario registry、candidate registry 和 promote 行为编写前端测试。
  - 使用 `fake-indexeddb` + `ScenarioRepository.ensureScenario()` 验证生成场景能导入 IndexedDB。
  - 复用或新增 project/simulation service 与 handler focused tests，确认生成数据能被现有 demo handlers 读取。
  - 验证 real、fallback、prod 构建语义不被 MCP 和 generated registry 改变。
  _需求追溯: R1.AC4, R1.AC5, R7.AC3, R8.AC1, R9.AC2, R9.AC4_

- [x] 13. 完成房地产 P0 验收样例
  - 准备房地产行业 brief，调用 scan、plan、validate、compile、write candidate、run checks、promote 的完整工作流。
  - 确认 draft 校验失败时可返回明确修复报告，修复后可稳定编译。
  - 生成 `project + simulation` candidate，并通过 generated scenario test、ScenarioRepository 导入测试、project/simulation focused tests。
  - promote 后使用正式 scenario ID 运行 `yarn type-check` 和 `VITE_APP_RUNTIME_MODE=demo-offline VITE_DEMO_SCENARIO_ID=<scenario-id> yarn build:demo-offline`。
  - 检查 `dist-demo-offline` 不包含 AI provider 配置、API key、MCP server 代码或模型调用能力。
  _需求追溯: R2.AC4, R5.AC6, R6.AC1, R6.AC3, R8.AC1, R8.AC2, R8.AC3, R8.AC7, R9.AC2, R9.AC3_

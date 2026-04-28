# Demo Offline Data MCP 需求规格

## 简介

当前项目已经具备 `demo-offline` 运行时、标准 `DemoScenarioPackage`、IndexedDB 导入、MSW demo handlers、场景选择和 `build:demo-offline` 静态演示包能力。后续业务分支会持续新增不确定的菜单、列表、详情、图表和业务 API，演示数据需要在开发者打包 offline demo 前按行业语境快速生成，同时不得污染生产模式、不得把 AI API key 放入项目运行时、不得让 AI 直接改 MSW handler 或浏览器 IndexedDB。

本需求定义一个仓库级本地 MCP server：`Demo Offline Data MCP`。该 MCP 以 TypeScript 实现，放在仓库根目录的开发工具区域，面向 Cherry Studio、Codex、Claude、Cursor 等外部 Chat Agent 暴露受控工具。MCP 不负责调用大模型，不保存 provider/API key；它负责扫描当前 demo-offline 上下文、向 AI 提供稳定生成上下文、校验 AI 生成的语义草稿、编译成候选 `DemoScenarioPackage`、受限写入 generated scenario、运行验证命令，并在全部检查通过后启用候选场景。长期目标是让外部 Chat Agent 能通过标准 MCP 协议生成高质量行业化离线演示数据，同时保持现有 Vue3、MSW、demo-offline runtime 和生产构建链路稳定。

## 需求列表

### R1: 提供仓库级本地 MCP 开发工具
**用户故事:** 作为开发者，我希望通过本地 MCP server 将 Chat Agent 接入当前仓库的 demo-offline 数据生成能力，以便在不改生产应用架构的前提下生成行业化离线演示数据。
**验收标准 (EARS):**
- R1.AC1: WHEN 开发者配置 MCP 客户端时 THEN 系统必须能够以本地 `stdio` MCP server 形式启动 `Demo Offline Data MCP`。
- R1.AC2: WHEN MCP 工具被实现时 THEN MCP 源码必须位于仓库级开发工具目录，而不得放入 `ruoyi-fastapi-frontend/src/**` 或 `ruoyi-fastapi-backend/**` 业务运行时目录。
- R1.AC3: IF MCP server 需要读取项目上下文 THEN 它必须以当前仓库路径为边界解析 `ruoyi-fastapi-frontend/src/demo/**`、前端脚本和相关测试文件。
- R1.AC4: WHEN 正常生产构建或后端服务启动时 THEN MCP server 不得被生产构建、客户离线包或 FastAPI 后端运行时加载。
- R1.AC5: IF 开发者未配置 MCP 客户端 THEN 现有 `yarn dev`、`yarn dev:mock`、`yarn build:prod`、`yarn build:demo-offline` 行为必须保持可用。

### R2: 不在项目内集成 AI provider 与 API key
**用户故事:** 作为项目负责人，我希望模型调用和 API key 管理由外部 Chat Agent 负责，以便项目内不新增 DeepSeek、Kimi、OpenAI 等 provider 配置并避免密钥泄漏。
**验收标准 (EARS):**
- R2.AC1: WHEN MCP server 启动时 THEN 它不得要求配置 DeepSeek、Kimi、OpenAI、Gemini 或其他模型 provider 的 API key。
- R2.AC2: WHEN Chat Agent 需要生成数据时 THEN 模型调用必须发生在 MCP 客户端或外部 Agent 环境中，而不是发生在前端浏览器、客户离线包或后端业务服务中。
- R2.AC3: IF MCP 工具需要让 AI 继续生成或修复数据 THEN 它必须通过结构化工具结果返回上下文、错误和修复提示，而不得在项目内自行调用模型 API。
- R2.AC4: WHEN 构建 `dist-demo-offline` 时 THEN 输出产物不得包含 AI provider 配置、API key、MCP server 代码或模型调用能力。

### R3: 扫描现有 demo-offline 能力并输出生成上下文
**用户故事:** 作为 Chat Agent，我希望通过 MCP 获得当前项目已经支持的 demo-offline 场景、schema、数据切片和 handler 覆盖面，以便只针对可运行的离线演示能力生成数据。
**验收标准 (EARS):**
- R3.AC1: WHEN 调用扫描工具时 THEN MCP 必须读取 `DemoScenarioPackage` schema、默认场景、场景注册入口、ScenarioRepository 导入逻辑和 demo handlers 覆盖面。
- R3.AC2: WHEN 扫描完成时 THEN MCP 必须返回结构化上下文，至少包含可生成切片、默认数据来源、现有 scenario 列表、支持的运行命令和已知未覆盖风险。
- R3.AC3: WHEN P0 扫描 demo-offline 能力时 THEN 扫描范围必须限定为 `ruoyi-fastapi-frontend/src/demo/**` 及场景相关前端脚本，不要求扫描 `src/views/**`、`src/api/**` 或后端业务代码。
- R3.AC4: WHEN 扫描结果返回给 Chat Agent 时 THEN 结果必须足够精简，避免把大体量源码全文塞入模型上下文。
- R3.AC5: IF 项目中已有 generated scenario THEN MCP 扫描结果必须区分默认场景、正式 generated 场景和候选 generated 场景。
- R3.AC6: IF P0 扫描结果没有发现某个业务切片的 demo-offline 依据 THEN MCP 必须将该切片视为不可安全生成，而不得通过扫描页面或真实 API 来推断补齐。

### R4: 基于 brief 生成可审阅的生成计划
**用户故事:** 作为开发者，我希望只输入行业、客户语境和演示目标，由 MCP/Agent 生成可审阅计划，以便不用手动指定内部模块名或数据切片。
**验收标准 (EARS):**
- R4.AC1: WHEN 开发者提供行业 brief THEN MCP 必须支持生成一份结构化计划，说明哪些数据切片生成、哪些沿用默认、哪些缺覆盖、哪些需要人工确认。
- R4.AC2: WHEN 计划涉及“全亮”生成时 THEN MCP 必须仅把已被扫描判定为安全可生成的切片纳入计划。
- R4.AC3: IF 某些业务模块尚未出现在 P0 的 `src/demo/**` 扫描结果中 THEN 计划必须明确说明该模块不在 P0 可生成范围内，而不得承诺生成可运行数据。
- R4.AC4: WHEN 计划返回给 Chat Agent 和开发者时 THEN 计划必须保留与扫描结果的 trace 信息，以便追溯某个切片为什么可生成或不可生成。
- R4.AC5: IF 开发者选择仅生成部分业务范围 THEN 计划必须支持局部范围，同时保证依赖切片不会断裂。
- R4.AC6: WHEN P0 生成计划未显式指定范围时 THEN 默认生成范围必须限定为 `project + simulation`，并沿用默认场景中的 `auth` 与 `system` 数据。

### R5: AI 只产出语义草稿，结构由确定性 compiler 生成
**用户故事:** 作为演示稳定性负责人，我希望 AI 只负责行业语义内容，最终场景包结构由程序生成，以便避免 AI 直接输出结构错误的 `DemoScenarioPackage`。
**验收标准 (EARS):**
- R5.AC1: WHEN Chat Agent 生成行业数据时 THEN 它必须优先生成受控的 `IndustryDataDraft` 语义草稿，而不是直接写最终 `DemoScenarioPackage`。
- R5.AC2: WHEN MCP 编译草稿时 THEN 程序必须确定性生成 ID、时间、状态、版本、拓扑、关联关系和默认字段。
- R5.AC3: IF AI 草稿缺少可由程序确定性补齐的结构字段 THEN compiler 必须自动补齐或规范化，而不是把该问题交给 AI 反复猜测。
- R5.AC4: IF AI 草稿包含非法枚举、占位词、高重复内容或不符合行业语境的文本 THEN MCP 必须通过 validator 返回错误和修复提示。
- R5.AC5: WHEN compiler 输出候选场景时 THEN 输出必须满足 `DemoScenarioPackage` 的统一结构，且不得直接生成 MSW handler、Vue 页面、路由或 IndexedDB 写库脚本。
- R5.AC6: WHEN P0 定义 `IndustryDataDraft` 时 THEN schema 必须采用可复用于多行业的通用语义结构，并以房地产行业作为首个验收样例。
- R5.AC7: IF 后续接入制造、教育、外卖等行业 THEN 不应要求重写 P0 的核心 draft 校验和 compiler 主流程。

### R6: 校验失败时向 AI 返回结构化修复报告
**用户故事:** 作为 Chat Agent，我希望 MCP 在数据不合格时返回明确错误路径、错误代码和修复建议，以便我能按报告修复而不是重新随机生成。
**验收标准 (EARS):**
- R6.AC1: WHEN `IndustryDataDraft` 校验失败时 THEN MCP 必须返回结构化错误列表，包含 `path`、`code`、`actual`、`expected` 或 `fixHint`。
- R6.AC2: WHEN 错误属于程序可修复类型时 THEN MCP 必须标记可自动修复并尽量提供修复后的草稿或修复摘要。
- R6.AC3: WHEN 错误属于行业语义质量问题时 THEN MCP 必须提供面向 AI 的具体修复提示，例如合法阶段、推荐岗位、禁止占位词和重复度说明。
- R6.AC4: IF AI 多次修复仍未通过基础校验 THEN MCP 必须保持候选场景未写入或未启用，并返回剩余错误，而不得把失败数据推进到正式场景。
- R6.AC5: WHEN validator 发现草稿与当前扫描上下文不匹配 THEN 错误报告必须指出缺失的 demo-offline 覆盖前提。

### R7: 受限写入 generated scenario 并支持 candidate/promote
**用户故事:** 作为代码库维护者，我希望 MCP 只能写入 demo-offline generated 场景区域，并通过候选文件和提升流程保护当前可演示场景，以便避免误改生产代码或破坏已可用演示。
**验收标准 (EARS):**
- R7.AC1: WHEN MCP 写入文件时 THEN 写权限必须限制在 `ruoyi-fastapi-frontend/src/demo/scenarios/generated/**` 或设计阶段确认的等价 demo-only generated 目录。
- R7.AC2: WHEN MCP 生成新场景时 THEN 它必须先写入 candidate 场景，而不是直接覆盖当前正式场景。
- R7.AC3: IF candidate 场景未通过校验和检查 THEN MCP 不得将其注册为正式可选场景。
- R7.AC4: WHEN candidate 通过全部检查后 THEN MCP 必须提供显式 promote 工具或步骤，并且只有在该工具或步骤被明确调用时才能将候选场景提升为正式 generated scenario。
- R7.AC5: WHEN 前端场景注册入口集成 generated 场景时 THEN 主注册入口应只需要一次性接入 generated registry，后续 MCP 不应频繁修改主场景入口文件。
- R7.AC6: IF generated registry 或正式场景已存在 THEN MCP 必须避免无提示覆盖，并返回冲突信息或要求显式确认。
- R7.AC7: IF candidate 通过检查但尚未显式 promote THEN 当前正式 scenario 必须保持不变。

### R8: 运行项目内确定性验证命令
**用户故事:** 作为演示交付人员，我希望 MCP 能在写入候选场景后运行必要检查，以便确认场景包能被 demo-offline 导入、查询和构建。
**验收标准 (EARS):**
- R8.AC1: WHEN candidate 场景写入后 THEN MCP 必须支持运行场景校验、场景导入测试和相关 focused tests。
- R8.AC2: WHEN 项目要求类型安全时 THEN MCP 必须支持运行前端 `type-check` 或等价检查。
- R8.AC3: WHEN 开发者准备生成客户离线包时 THEN MCP 必须支持运行 `build:demo-offline` 并返回成功、失败和关键日志摘要。
- R8.AC4: IF 验证命令失败 THEN MCP 必须把失败命令、退出码、关键错误片段和建议下一步返回给 Chat Agent。
- R8.AC5: WHEN 验证命令通过 THEN MCP 必须返回可用于开发者确认的场景 ID、运行模式、推荐预览命令和构建证据。
- R8.AC6: WHEN 验证命令通过 THEN MCP 必须提示仍需显式 promote 才能启用正式场景，而不得把通过检查等同于自动发布。
- R8.AC7: WHEN P0 验收生成效果时 THEN 必须至少使用房地产行业 brief 生成 `project + simulation` candidate，并通过校验、focused tests 和 `build:demo-offline`。
- R8.AC8: WHEN P0 MCP 执行项目命令时 THEN 命令执行必须限制在固定 allowlist 内，且 allowlist 仅覆盖 focused tests、`type-check`、`build:demo-offline` 及其设计阶段确认的等价验证命令。

### R9: 保持现有 demo-offline/MSW/生产模式不被污染
**用户故事:** 作为前端负责人，我希望 MCP 只是开发期数据生产辅助，不改变现有 demo-offline runtime 与 MSW handler 职责，以便长期维护成本可控。
**验收标准 (EARS):**
- R9.AC1: WHEN MCP 生成或写入数据时 THEN 它不得修改 `src/mocks/handlers/**`、`src/demo/handlers/**`、Vue 路由、业务页面或真实 API 调用代码。
- R9.AC2: WHEN demo-offline 运行时读取 generated 场景时 THEN 它必须继续通过 `getDemoScenarioPackage`、`ScenarioRepository.ensureScenario`、IndexedDB、demo service/repository 和 demo handlers 既有链路工作。
- R9.AC3: IF 某个业务 API 未被 demo-offline handler 覆盖 THEN 系统必须继续保持明确的 `DEMO_API_NOT_IMPLEMENTED` 行为或覆盖报告，而不是由 MCP 临时伪造 handler。
- R9.AC4: WHEN 使用 `real` 或 `fallback` 模式运行应用时 THEN MCP 生成能力不得改变真实后端访问、fallback mock 或生产构建语义。
- R9.AC5: IF 后续新增 dev-only 页面或 CLI THEN 它们必须复用 MCP core 能力或同等 core 能力，而不得形成第二套数据生成规则。

### R10: 提供可接入外部 MCP 客户端的文档和安全边界
**用户故事:** 作为开发者，我希望有清晰的 MCP 客户端配置、工具说明和安全边界，以便在 Cherry Studio 或其他 Chat Agent 中可靠使用。
**验收标准 (EARS):**
- R10.AC1: WHEN P0 能力交付时 THEN 文档必须说明如何在本地构建和启动 MCP server。
- R10.AC2: WHEN 开发者使用 Cherry Studio 或其他 MCP 客户端时 THEN 文档必须给出 stdio server 配置示例和推荐工作流。
- R10.AC3: WHEN 描述 MCP 工具时 THEN 文档必须明确哪些工具只读、哪些工具会写文件、哪些工具会执行命令。
- R10.AC4: IF 工具具有写文件或执行命令能力 THEN 文档必须说明写入目录限制、命令 allowlist 和人工确认建议。
- R10.AC5: WHEN 后续扩展页面 Workbench、CLI 或 AI provider 时 THEN 文档必须要求保持 API key 不进入浏览器运行时和客户离线包。
- R10.AC6: IF Chat Agent 请求执行 allowlist 之外的命令 THEN MCP 必须拒绝执行，并返回允许的命令范围和替代建议。

## 非目标

- 本期不实现内置 DeepSeek、Kimi、OpenAI、Gemini provider。
- 本期不在前端浏览器页面内存储或调用 AI API key。
- 本期不实现 dev:demo-offline 可视化 Workbench 页面。
- 本期不自动生成或修改 MSW handler、Vue 路由、真实业务 API 或后端代码。
- 本期不把仓库或前端改造成 monorepo。
- 本期默认不生成 `auth` 与 `system` 数据，仅沿用默认场景中的账号、角色、菜单、字典、组织和用户。
- 本期不扫描 `src/views/**`、`src/api/**` 或后端代码来发现业务模块缺口；页面/API 与 demo-offline 覆盖差异报告作为后续阶段能力。
- 本期不允许 MCP 执行任意 shell 命令，也不提供由 Chat Agent 自由传入命令的通用执行工具。
- 本期不承诺对未接入 demo-offline 的业务模块生成可运行离线数据。

## Clarifications

### Session 2026-04-28

- Q: MCP 是否负责调用 DeepSeek/Kimi/OpenAI？ -> A: P0 不负责，模型调用由外部 Chat Agent/MCP 客户端负责，项目内只提供上下文、校验、编译、写入和验证工具。
- Q: MCP 应该放前端、后端还是根目录？ -> A: 放仓库根目录的 `tools/demo-offline-mcp/`，作为开发工具，不放入前端 `src` 或后端业务服务。
- Q: MCP 使用 TypeScript 还是 Python？ -> A: 使用 TypeScript，便于对齐前端 `DemoScenarioPackage`、Vite、MSW 和 TypeScript MCP SDK。
- Q: 是否需要把前端改成 monorepo？ -> A: P0 不需要，独立 tools package 即可。
- Q: 如何处理 AI 输出不稳定？ -> A: AI 只输出语义草稿，MCP validator 返回结构化错误和修复提示，compiler 确定性生成最终场景结构，失败 candidate 不提升为正式场景。
- Q: P0 的默认生成范围应该锁定到哪一级？ -> A: 采用 `project + simulation`，`auth/system` 沿用默认场景。
- Q: candidate 通过检查后，是否允许 MCP 自动提升为正式 scenario？ -> A: 不允许自动提升，checks 通过后仍需显式调用 promote。
- Q: P0 是否需要支持“覆盖面扫描发现页面/API 缺口”，还是只扫描 demo-offline 已有能力？ -> A: P0 只扫描 `src/demo/**` 已有 demo-offline 能力，页面/API 缺口扫描延后到 P1。
- Q: P0 的 `IndustryDataDraft` 是否只定义房地产行业字段，还是定义通用行业字段？ -> A: 定义通用 draft schema，并以房地产作为首个验收样例。
- Q: MCP 的命令执行权限在 P0 应该多严格？ -> A: 只允许固定 allowlist：focused tests、type-check、build:demo-offline。

# Mock Runtime Legacy 退场需求规格

## 简介

目标前端 mock 主线必须收敛为 `src/mocks/**`：以 FastAPI OpenAPI artifact 和生成类型约束 API 形状，以单套 typed dataset 表达业务事实，以 Dexie store 支撑 demo-offline 持久写，以 MSW 作为开发、测试和离线演示共用的网络虚拟化层。

本规格按从零实施基线定义第一阶段目标：完整覆盖旧 demo/scenario/runtime package 主线的迁移、删除、替换和验证闭环，确保应用启动、路由、mock runtime、Vite 构建、demo-offline 产物、文档和 CI 门禁最终都只承认 `src/mocks/**` 为当前 mock runtime。历史多场景 runtime、scenario package、active pointer、candidate/promote、旧环境变量和旧构建产物不得再影响当前应用运行或后续开发判断。

## Clarifications

### Session 2026-05-01

- Q: 这份 spec 的实施基线应该按哪种状态写？ -> A: 从零实施；假设 legacy 仍存在，design/tasks 必须完整描述迁移、删除、替换全过程。
- Q: 旧 `src/demo/**` 代码的最终处理策略是什么？ -> A: 硬删除；删除旧源码、旧插件、旧 runbook，只允许历史 spec 和 git history 保留背景。
- Q: `demo-offline` 未覆盖 API 的失败范围应如何定义？ -> A: 关键 `/api/**` 未覆盖才返回确定性 501，其他静态资源或非业务请求按正常规则处理。
- Q: `src/views/demo/**` 这类 demo-offline 页面壳是否属于 legacy 删除范围？ -> A: 保留页面壳；只要不依赖旧 runtime/scenario，就允许保留 demo-offline UI 或占位页。

## 需求列表

### R1: 统一运行模式配置归属
**用户故事:** 作为前端维护者，我希望应用运行模式只由当前 mock runtime 模块解析，以便启动链路不再依赖旧 demo runtime。
**验收标准 (EARS):**
- R1.AC1: WHEN 应用启动并解析运行模式 THEN `resolveRuntimeConfig`、`RuntimeConfig` 和 mode normalization 必须由 `src/mocks/runtime/mode.ts` 或等价当前主线模块提供，不得从旧 demo runtime 路径导入。
- R1.AC2: WHEN `VITE_APP_RUNTIME_MODE` 未显式设置 THEN 运行模式必须默认为 `real`，并且不得因为旧 mock 环境变量被设置而启动 MSW。
- R1.AC3: WHEN `VITE_APP_RUNTIME_MODE` 为 `real` THEN 应用不得初始化 MSW handler、mock store 或 demo-offline devtools。
- R1.AC4: WHEN `VITE_APP_RUNTIME_MODE` 为 `fallback` 或 `demo-offline` THEN 应用必须通过同一套当前 mock runtime 入口启动 MSW。
- R1.AC5: IF 运行模式值不是 `real`、`fallback` 或 `demo-offline` THEN 系统必须 fail fast，并给出明确错误信息。
- R1.AC6: IF 代码新增 `VITE_ENABLE_MOCK`、`VITE_DEMO_SCENARIO_ID` 或 `VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS` 对当前运行模式的影响 THEN 该改动必须被门禁拒绝。

### R2: 删除旧 demo/scenario runtime 运行面
**用户故事:** 作为项目负责人，我希望旧 demo/scenario runtime 不再存在于活跃前端源码中，以便新人和 AI Agent 不会继续沿旧主线扩展。
**验收标准 (EARS):**
- R2.AC1: WHEN 检查活跃前端源码 THEN `ruoyi-fastapi-frontend/src/demo` 不得存在。
- R2.AC2: WHEN 检查 `src`、`tests`、`vite`、`vite.config.ts` 和 `package.json` 的当前运行面 THEN 不得出现指向旧 demo runtime、scenario package、release pointer、candidate registry 或 MCP 工具链的依赖。
- R2.AC3: IF 某个历史实现仍需考古 THEN 只能通过历史 spec 或 git history 查阅，不得把旧源码移动到 `archive/**`、`docs/archive/**` 或其他仓库内源码归档目录。
- R2.AC4: WHEN 删除旧 runtime 面后 THEN 旧 `__DEMO_RUNTIME__` 全局调试入口不得作为当前 runtime API 保留；当前调试入口只能是 `__MOCK_RUNTIME__` 或后续明确命名的 mock 主线 API。
- R2.AC5: IF `src/views/demo/**` 或其他 demo-offline UI 页面不依赖旧 runtime、scenario package、release pointer 或旧环境变量 THEN 它们不属于本规格的删除范围，可以作为离线演示页面壳或占位页保留。

### R3: demo-offline 构建不再产出旧 scenario artifacts
**用户故事:** 作为交付负责人，我希望 demo-offline 构建产物只反映当前 MSW + dataset + store 主线，以便离线演示包不会继续传播旧 scenario package 心智模型。
**验收标准 (EARS):**
- R3.AC1: WHEN 执行 `yarn build:demo-offline` THEN Vite 构建不得注册旧 demo-offline contract 插件或读取旧 scenario/release-store 数据。
- R3.AC2: WHEN 检查 `dist-demo-offline` THEN 构建产物不得包含 `demo-contract/`、`demo-scenarios/` 或等价旧 scenario package 发布目录。
- R3.AC3: IF demo-offline 构建需要公开 mock 诊断信息 THEN 诊断信息必须来自当前 `src/mocks/**` runtime、handler metadata 或 debug header，不得恢复旧 release pointer。
- R3.AC4: WHEN 生产构建执行 `yarn build:prod` THEN 生产产物必须保持 `real` 模式语义，不得因为 demo-offline 退场改动而默认启动 MSW。

### R4: 统一 runtime 启动和网络语义
**用户故事:** 作为前端开发者，我希望 `fallback`、`demo-offline`、Vitest 和后续页面验收复用同一套 handler 注册入口，以便不同环境不会重新分叉。
**验收标准 (EARS):**
- R4.AC1: WHEN 应用处于 `fallback` 模式 THEN runtime 必须使用当前 handler 集合并采用真实后端优先、约定失败条件下回退 mock 的策略。
- R4.AC2: WHEN 应用处于 `demo-offline` 模式 THEN runtime 必须使用当前 handler 集合并采用纯 MSW 策略，不得访问真实后端来补齐关键 `/api/**`。
- R4.AC3: WHEN `demo-offline` 模式遇到未覆盖的关键 `/api/**` 请求 THEN runtime 必须返回确定性 `501 MOCK_API_NOT_IMPLEMENTED` 响应，确保缺口能被测试或演示验收发现。
- R4.AC4: WHEN Vitest 或应用入口启动 mock runtime THEN 它们必须复用当前 `setupMockRuntime`、handler 聚合或等价主线入口，不得直接 mock 请求适配层来绕过 HTTP 合约。
- R4.AC5: IF 需要新增 runtime debug 能力 THEN 必须挂在当前 mock runtime devtools 上，并且不得暴露旧 scenario、candidate、promote 或 active pointer 概念。
- R4.AC6: IF `demo-offline` 模式遇到静态资源、开发服务器资源或非业务请求 THEN 这些请求不得因为关键 `/api/**` 缺口规则而被强制转换为 501。

### R5: 建立防回潮静态门禁
**用户故事:** 作为质量负责人，我希望 legacy 退场不是一次性清理，而是由脚本和测试持续约束，以便后续 PR 不能悄悄恢复双主线。
**验收标准 (EARS):**
- R5.AC1: WHEN 执行 `scripts/check-mock-mainline.sh` THEN 脚本必须在 `src/demo` 存在时失败。
- R5.AC2: WHEN 当前前端运行面出现旧 demo/scenario import、旧环境变量、旧构建插件名、旧发布产物名、旧 runtime package 类型或旧 MCP 工具链标识 THEN `scripts/check-mock-mainline.sh` 必须失败并打印具体命中位置。
- R5.AC3: WHEN 执行 `scripts/check-mock-mainline.sh --require-dist` THEN 脚本必须要求 `dist-demo-offline/index.html` 存在，并扫描 demo-offline 构建产物中是否出现旧 scenario artifacts。
- R5.AC4: WHEN 执行 mock invariant 测试 THEN 必须有测试断言旧 runtime 源码树不存在，并扫描当前 mock 源码不得引用 legacy 标识。
- R5.AC5: IF 某些 legacy 字符串只出现在专门的门禁测试、历史文档或归档说明中 THEN 门禁必须通过明确例外范围控制这些命中，避免扩大到当前运行面。

### R6: 同步文档和 spec 索引边界
**用户故事:** 作为团队协作者，我希望文档明确旧方案已退场，以便后续新增 mock 能力时直接进入当前 `src/mocks/**` 主线。
**验收标准 (EARS):**
- R6.AC1: WHEN 阅读 `src/mocks/README.md` THEN 文档必须说明当前主线是 OpenAPI artifact、生成类型、单套 typed dataset、Dexie store 和 MSW handler。
- R6.AC2: WHEN 文档描述旧多场景 runtime、MCP、candidate/promote、active pointer 或 runtime package writer THEN 必须明确其历史、冻结、暂停或已退场状态，不得作为当前验收路径出现。
- R6.AC3: WHEN 历史 runbook 会误导开发者恢复旧 demo/scenario 主线 THEN 该 runbook 必须删除、归档或重写为历史说明。
- R6.AC4: WHEN 更新 `docs/specs/README.md` 或相关索引 THEN 必须让读者能区分已完成的单套 mock 主线、已退场的旧方案和下一阶段治理 specs。

### R7: 固化验证命令和测试覆盖
**用户故事:** 作为代码审查者，我希望 legacy 退场有可重复验证证据，以便审查不依赖人工搜索记忆。
**验收标准 (EARS):**
- R7.AC1: WHEN runtime mode 解析逻辑变更 THEN 必须有单元测试覆盖默认 `real`、合法模式、非法模式和策略映射。
- R7.AC2: WHEN 应用入口或 mock 入口变更 THEN 必须有测试覆盖 `real` 不启动 mock，以及 `fallback`/`demo-offline` 通过统一 runtime 启动。
- R7.AC3: WHEN router history 或 demo-offline 特例依赖运行模式 THEN 必须有测试覆盖该行为从当前 runtime mode 模块读取。
- R7.AC4: WHEN 完成 legacy 退场实现 THEN 必须通过 `yarn lint:check`、`yarn type-check`、相关 mock/runtime 测试、`yarn build:prod`、`yarn build:demo-offline` 和 `scripts/check-mock-mainline.sh --require-dist` 或等价 CI 门禁。
- R7.AC5: IF 因环境限制无法运行某个验收命令 THEN 交付报告必须明确说明缺口、原因和后续补跑命令。

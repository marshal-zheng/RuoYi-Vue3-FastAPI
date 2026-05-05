# Mock Runtime Legacy 退场实现任务

- [x] 1. 建立 legacy 运行面 inventory 和删除边界
  - 扫描 `ruoyi-fastapi-frontend/src`、`tests`、`vite`、`vite.config.ts`、`package.json` 中的旧 demo runtime、scenario package、release pointer、candidate registry、MCP 工具链和旧环境变量引用。
  - 输出必须硬删除的源码、插件、runbook 和构建产物清单；不得规划 `archive/**`、`docs/archive/**` 或其他源码归档目录。
  - 单独标注可保留的 demo-offline UI 页面壳，例如不依赖旧 runtime/scenario 的 `src/views/demo/**`。
  - 记录旧 `__DEMO_RUNTIME__` 只能作为清理目标，不得作为当前 debug API 保留。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R5.AC2_

- [x] 2. 迁移并收口 runtime mode 模块
  - 在 `src/mocks/runtime/mode.ts` 建立 `RuntimeMode`、`MockRuntimeMode`、`RuntimeConfig`、`resolveRuntimeConfig()` 和 mode normalization。
  - 只读取 `VITE_APP_RUNTIME_MODE`、`VITE_APP_BASE_API`、`VITE_DEMO_RUNTIME_DEBUG`，默认模式为 `real`。
  - 移除旧 `scenarioId`、`allowCandidateScenarios`、`mockMode` 和旧 mock 环境变量兼容逻辑。
  - 对非法运行模式执行 fail fast，并提供明确错误信息。
  _需求追溯: R1.AC1, R1.AC2, R1.AC5, R1.AC6_

- [x] 3. 更新应用启动和运行模式引用面
  - 将 `src/main.ts` 改为从 `@/mocks/runtime/mode` 读取配置，并通过 `setupAppRuntimeMocks()` 启动 mock runtime。
  - 将 `src/mocks/index.ts`、`src/mocks/runtime/app-entry.ts`、router history、topology、monitor/druid 等运行模式引用迁到当前 mock runtime 模块。
  - 确保 `real` 模式不加载 `setupMockRuntime()`，不初始化 MSW、mock store 或 mock devtools。
  - 确保 `fallback` 和 `demo-offline` 通过同一当前 runtime 入口启动。
  _需求追溯: R1.AC1, R1.AC3, R1.AC4, R2.AC2, R4.AC4, R7.AC2, R7.AC3_

- [x] 4. 统一 mock runtime setup 和 debug API
  - 在 `src/mocks/runtime/setup.ts` 中按 mode 映射网络策略：`fallback` -> `fallback`，`demo-offline` -> `pure`。
  - 统一初始化 `src/mocks/store/**` data source，并通过 `createMockHandlers()` 聚合当前主线 handler。
  - 在 app runtime 入口启动前清理旧 `__DEMO_RUNTIME__` 和当前 `__MOCK_RUNTIME__`。
  - 只在允许的 debug 场景暴露 `window.__MOCK_RUNTIME__`，并限制能力为 mode、datasetVersion、resetDataset、exportDatasetSnapshot。
  _需求追溯: R2.AC4, R4.AC1, R4.AC2, R4.AC4, R4.AC5, R7.AC2_

- [x] 5. 实现 demo-offline 未覆盖 API 的确定性响应
  - 在 `src/mocks/runtime/unhandled.ts` 或等价当前 runtime 模块中实现关键 `/api/**` 匹配逻辑。
  - 在 `demo-offline` handler 聚合时注入缺口 handler，返回 HTTP `501`、`code: 501`、`MOCK_API_NOT_IMPLEMENTED` 消息和 mock debug headers。
  - 保证静态资源、Vite 开发资源和非业务请求不被强制转换为 501。
  - 保证 `fallback` 模式未覆盖请求按真实后端优先或 passthrough 语义处理。
  _需求追溯: R3.AC3, R4.AC1, R4.AC2, R4.AC3, R4.AC6_

- [x] 6. 删除旧 `src/demo/**` runtime 源码和旧 runbook
  - 删除旧 `src/demo/**` runtime、scenario package、generated scenarios、release pointer、repository/service 等源码树。
  - 删除或重写会误导恢复旧主线的 runbook；不得把旧源码转存到仓库内归档目录。
  - 保留历史 spec 和 git history 作为考古来源。
  - 删除旧源码后确认保留的 demo-offline 页面壳不引用旧 runtime、旧环境变量或旧 scenario 资产。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC5, R6.AC2, R6.AC3_

- [x] 7. 清理 Vite demo-offline 构建链路和 package scripts
  - 删除旧 demo-offline contract/scenario Vite 插件，并从 `vite.config.ts` 或 plugin 聚合入口移除注册。
  - 确保 `build:demo-offline` 只构建当前应用和当前 mock 主线，不读取旧 scenario/release-store 数据。
  - 确保 `dev:fallback` 只设置 `VITE_APP_RUNTIME_MODE=fallback`，不再设置旧 mock 环境变量。
  - 构建后检查 `dist-demo-offline` 不包含 `demo-contract/`、`demo-scenarios/` 或 release pointer 资产。
  - 运行 `build:prod` 确认生产构建仍保持默认 `real` 语义。
  _需求追溯: R1.AC2, R1.AC6, R3.AC1, R3.AC2, R3.AC4, R5.AC3, R7.AC4_

- [x] 8. 强化静态门禁脚本
  - 扩展 `scripts/check-mock-mainline.sh`，在 `src/demo` 存在时失败。
  - 扫描当前运行面中的旧 import、旧环境变量、旧 plugin 名称、旧 artifact 名称、旧 runtime package 类型和旧 MCP 工具链标识。
  - 增加 `--require-dist` 行为：要求 `dist-demo-offline/index.html` 存在，并扫描旧 scenario artifacts。
  - 为专门门禁测试、历史 spec 和明确历史说明保留最小例外范围，避免误伤但不扩大到运行面。
  _需求追溯: R1.AC6, R2.AC1, R2.AC2, R3.AC2, R5.AC1, R5.AC2, R5.AC3, R5.AC5_

- [x] 9. 增加 runtime 和 legacy 边界测试
  - 为 `src/mocks/runtime/mode.ts` 增加默认 `real`、合法模式、非法模式和 strategy 映射测试。
  - 为 app runtime 入口增加 `real` 不启动 mock、清理旧 devtools、`fallback`/`demo-offline` 统一启动测试。
  - 为 unhandled API handler 增加关键 `/api/**` 501 和非业务请求例外测试。
  - 为 router history 或其他 demo-offline 特例增加从当前 runtime mode 读取模式的测试。
  - 增加或更新 mock invariant 测试，断言 `src/demo` 不存在且当前 mock 源码不引用 legacy 标识。
  _需求追溯: R1.AC2, R1.AC3, R1.AC4, R1.AC5, R2.AC1, R2.AC4, R4.AC3, R4.AC4, R4.AC6, R5.AC4, R7.AC1, R7.AC2, R7.AC3_

- [x] 10. 更新当前 mock 文档和 specs 索引
  - 更新 `src/mocks/README.md`，说明当前主线是 OpenAPI artifact、生成类型、单套 typed dataset、Dexie store 和 MSW handler。
  - 更新 `docs/specs/README.md` 或相关索引，区分当前单套 mock 主线、已退场旧方案和下一阶段治理 specs。
  - 删除或改写仍把旧多场景 runtime、MCP、candidate/promote、active pointer、runtime package writer 描述为当前路径的文档。
  - 文档中如需提及旧概念，必须明确历史、冻结、暂停或已退场状态。
  _需求追溯: R6.AC1, R6.AC2, R6.AC3, R6.AC4, R5.AC5_

- [x] 11. 执行完整质量门禁和构建验收
  - 运行 `cd ruoyi-fastapi-frontend && yarn lint:check`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn type-check`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn test:run src/mocks`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn build:prod`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn build:demo-offline`。
  - 运行 `scripts/check-mock-mainline.sh` 和 `scripts/check-mock-mainline.sh --require-dist`。
  - 对当前运行面执行 legacy pattern 搜索，确认无旧路径、旧 env、旧 plugin、旧 artifact 或旧 runtime 类型命中。
  _需求追溯: R2.AC2, R3.AC2, R3.AC4, R5.AC1, R5.AC2, R5.AC3, R5.AC4, R7.AC4_

- [x] 12. 形成退场验收记录和残余风险说明
  - 汇总删除清单、迁移清单、保留页面壳清单、测试命令和构建命令结果。
  - 明确任何未运行命令的原因和补跑命令；不得把未验证项包装成已完成。
  - 标注本 spec 不处理的下一阶段事项，例如 contract coverage matrix、overlay harness、demo-offline E2E。
  - 确认后续新增 mock 能力应进入 `src/mocks/**`，不得恢复旧 scenario/runtime package 主线。
  _需求追溯: R2.AC5, R6.AC4, R7.AC4, R7.AC5_

# Mock Scenario Overlay 与页面状态 Harness 实现任务

- [x] 1. 建立 overlay registry 基础结构
  - 新增 `src/mocks/overlays/types.ts`、`index.ts`、`registry.schema.json` 和 `registry/**` 目录。
  - 定义 overlay id、状态类型、目标 method/path/handlerTag、页面范围、owner、tests、Core matrix、resetStrategy 和 composition 元数据。
  - 增加 registry loader，按稳定顺序加载并导出 overlay summary。
  - 增加 registry 单元测试，覆盖 schema 校验、id 唯一、必填字段、非法字段拒绝。
  _需求追溯: R1.AC1, R1.AC2, R1.AC5, R9.AC1_

- [x] 2. 接入 contract registry 与 OpenAPI 对齐校验
  - 在 overlay loader 或独立校验模块中读取 `src/mocks/contracts/coverage/registry/*.json` 和 `shared/openapi.json`。
  - 校验 overlay 目标 endpoint 能映射到 contract registry entry；拒绝 `missing`、`real-only` 或未登记 endpoint，除显式 `unhandled-api` 501 探测例外。
  - 校验 handler tag、method/path、测试文件路径和 schema-unavailable/local contract 标记。
  - 为 contract 漂移、handler tag 失效、test 文件缺失输出可定位错误。
  _需求追溯: R1.AC2, R1.AC3, R1.AC4, R9.AC1, R9.AC4, R9.AC5_

- [x] 3. 实现 overlay runtime 状态与组合规则
  - 新增 `src/mocks/overlays/runtime.ts`，维护 `MockOverlayState`、active ids、source 和当前 registry entry。
  - 实现 `activateOverlays()`、`resetOverlays()`、`getOverlayState()`、`listOverlays()` 的核心逻辑。
  - 实现 Compatible composition：只允许 registry 声明可组合的 overlay 同时激活；同 endpoint、同 handler tag 或同状态语义冲突整体 fail fast。
  - 确保激活失败时保留请求前 active state，不留下部分激活状态。
  _需求追溯: R4.AC5, R5.AC2, R5.AC3, R5.AC4, R5.AC7_

- [x] 4. 实现 read-only projection 与 overlay handler factory
  - 新增 `src/mocks/overlays/handlers.ts` 和 `response.ts`，生成可放在基础 handlers 前面的 MSW overlay handlers。
  - 为空态、慢加载、429/5xx/timeout、403、unsupported 501、只读/禁用状态提供统一 handler factory。
  - 复用 `error-common` problem 语义和当前 response helper，避免测试目录维护并行业务错误契约。
  - 提供只读 data source projection wrapper，只允许读取并返回投影、过滤或替代响应，不暴露 Dexie 写接口。
  - 所有 overlay 响应保留 `X-Mock-Response`、`X-Mock-Handler`，并新增 `X-Mock-Overlay`。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R3.AC6, R4.AC2, R4.AC3, R4.AC4, R4.AC6, R6.AC1, R6.AC2, R6.AC5_

- [x] 5. 集成 `createMockHandlers()` 和 runtime debug API
  - 扩展 `CreateMockHandlersOptions`，新增可选 `overlays` 参数，默认调用行为保持不变。
  - 在 handler 聚合时将 overlay handlers 放在基础业务 handlers 前面，未激活 overlay 时不改变现有 handler 列表。
  - 扩展 `MockRuntimeDevtools`，增加 `listOverlays()`、`getOverlayState()`、`activateOverlays()`、`resetOverlays()`。
  - 在 `setupMockRuntime()` 中限制 overlay API 只在 demo-offline debug/test 模式暴露，`real` 模式不初始化、不读取、不应用 overlay。
  - 页面加载后激活 overlay 时重新生成 handlers 并调用当前 MSW worker `resetHandlers(...)`。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R4.AC1, R4.AC2, R5.AC1, R5.AC2, R5.AC3, R10.AC4_

- [x] 6. 实现 Playwright/Vitest 受控 test bootstrap
  - 定义并实现 `window.__MOCK_RUNTIME_BOOTSTRAP__`，支持 Playwright/Vitest 在首屏请求前注入 overlay ids。
  - `setupMockRuntime()` 只在允许环境读取 bootstrap，并在初始化后删除 bootstrap 对象。
  - 明确拒绝 URL query、普通环境变量或客户可见 UI 激活 overlay。
  - 增加测试覆盖首屏前 bootstrap、页面加载后 runtime API 激活、bootstrap 清空和不兼容 mode 失败。
  _需求追溯: R2.AC2, R2.AC5, R2.AC6, R5.AC4, R7.AC2, R7.AC7_

- [x] 7. 建立 Core matrix overlay registry 条目
  - 为项目列表空态、项目写入错误、版本列表空态或错误、拓扑加载或保存错误、simulation 只读或 unsupported 控制状态新增首批 registry entries。
  - 每个 entry 绑定目标 handler tag、method/path、页面范围、owner、测试文件、e2eEnabled、coreMatrix 和组合元数据。
  - 对 `unsupported` overlay 区分显式验收状态与主线缺口 fallback。
  - 保持非 Core matrix critical endpoint 只输出 warning，不阻断首期验收。
  _需求追溯: R1.AC1, R1.AC5, R3.AC1, R3.AC5, R3.AC6, R6.AC5, R7.AC3, R9.AC2, R9.AC3_

- [x] 8. 新增 `mock:overlays` 本地门禁
  - 新增 `scripts/mock-overlays-core.mjs` 和 `scripts/check-mock-overlays.mjs`，复用 contract check 的 root 解析、稳定排序、JSON schema 校验和报告格式思路。
  - 支持 `--strict`、`--format=summary|json|markdown`、可选 `--write-report`。
  - strict 模式下 Core matrix 缺失、registry 漂移、冲突元数据错误、目标测试文件缺失必须失败。
  - 对非 Core matrix critical endpoint overlay 缺失输出 warning 和后续补齐建议。
  - 在 `package.json` 增加 `mock:overlays`、`mock:overlays:report` 和可选 JSON 输出脚本。
  _需求追溯: R1.AC5, R9.AC1, R9.AC2, R9.AC3, R9.AC4, R9.AC5, R10.AC5_

- [x] 9. 建立 Vitest/API overlay harness 与 targeted 测试
  - 新增 `tests/mocks/overlays.ts`，复用 `setupMainlineMockHandlers()` 的独立 `MockDemoDb` 与 `MockDataSource`。
  - 提供 `setupOverlayMockHandlers()`、`activateOverlayHandlers()`、`resetOverlayHandlers()`。
  - 补充 `src/mocks/overlays/*.test.ts`，覆盖 registry、runtime、handler factory、read-only projection、冲突组合、header 和 reset 行为。
  - 在 API/composable 相关测试中通过真实 API function、`@/utils/request` 或 MSW request path 进入 overlay。
  - 更新 mock standards 检查，发现未登记的测试私有 HTTP 契约 handler 时失败或输出可审查警告。
  _需求追溯: R5.AC1, R5.AC3, R5.AC5, R5.AC6, R6.AC1, R6.AC4, R8.AC1, R8.AC2, R8.AC3, R8.AC4, R8.AC5_

- [x] 10. 扩展 demo-offline E2E runner 与 Playwright 配置
  - 修改 `scripts/run-demo-offline-e2e.mjs`，支持 `--config <path>` 和 `--suite-name <name>`，默认仍运行 `playwright.demo-offline.config.ts`。
  - 新增 `playwright.demo-offline-page-state.config.ts`，使用独立 testDir、report/output 目录、Chromium、单 worker 和失败 artifact 策略。
  - 在 `package.json` 增加 `e2e:demo-offline:page-state`，复用现有 build/preview runner。
  - 确保默认 `yarn e2e:demo-offline` 不运行 page-state suite。
  _需求追溯: R7.AC1, R7.AC5, R7.AC8, R10.AC6_

- [x] 11. 扩展 Playwright runtime 与 network helpers
  - 在 `tests/e2e/demo-offline/runtime.ts` 新增 `bootstrapOverlays()`、`activateOverlays()`、`resetOverlays()`、`expectOverlayState()`。
  - 在 `tests/e2e/demo-offline/network.ts` 记录 `X-Mock-Overlay`，扩展失败摘要包含 step、method、path、status、handler tag 和 overlay id。
  - 增加 `waitForOverlayResponse()`、`assertOverlayResponsesTagged()`，并区分主线缺口 fallback 与显式 overlay 501。
  - 确保 artifact 和网络摘要不输出 token、账号密码、cookie、真实后端地址或密钥。
  _需求追溯: R6.AC1, R6.AC2, R6.AC3, R6.AC4, R6.AC5, R7.AC2, R7.AC5, R7.AC7_

- [x] 12. 实现 Core matrix page-state E2E
  - 新增 `tests/e2e/demo-offline/page-state/specs/project-page-state.spec.ts`，覆盖项目列表空态和项目写入错误。
  - 新增 `version-topology-page-state.spec.ts`，覆盖版本列表空态或错误、拓扑加载或保存错误。
  - 新增 `simulation-page-state.spec.ts`，覆盖 simulation 只读或 unsupported 控制状态。
  - 所有 page-state E2E 必须运行在 `dist-demo-offline` 静态 preview，通过 bootstrap/runtime API 激活 overlay，从真实页面和真实请求链路进入。
  - 若页面缺少稳定错误态、空态或禁用态信号，补充最小必要 UI 状态、role、label 或 `data-testid`。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R3.AC6, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC6, R9.AC3_

- [x] 13. 更新文档与防回潮说明
  - 更新 `src/mocks/README.md`，说明 overlay registry、状态类型、激活方式、reset 边界、read-only projection、Core matrix 和 `mock:overlays`。
  - 更新 `tests/README.md`，说明 Vitest/API harness、page-state E2E 命令、失败 artifact 和默认成功链路 E2E 的职责差异。
  - 更新 `docs/specs/README.md`，登记 `mock-scenario-overlays-and-page-state-harness` 为 P1 mock/page-state 验收 spec。
  - 明确旧 demo runtime、多场景 package、MCP package writer、active pointer、candidate/promote 和旧环境变量仍为非目标或已退场状态。
  _需求追溯: R2.AC4, R10.AC1, R10.AC2, R10.AC3, R10.AC5, R10.AC6_

- [x] 14. 执行最终本地验收
  - 运行 `yarn mock:contracts`，确认 contract registry 基线仍通过。
  - 运行 `yarn mock:overlays`，确认 overlay registry、Core matrix、warning/fail 规则通过。
  - 运行 targeted Vitest：`yarn test:run src/mocks/overlays tests/unit/api` 或等价最小集合。
  - 运行 `yarn build:demo-offline`。
  - 运行 `yarn e2e:demo-offline --skip-build`，确认默认成功链路未被 overlay 污染。
  - 运行 `yarn e2e:demo-offline:page-state --skip-build`，确认 page-state suite、network overlay 诊断和 artifact 正常。
  - 若某命令因环境限制无法运行，交付记录必须写明原因、影响和补跑命令。
  _需求追溯: R2.AC5, R4.AC1, R5.AC1, R6.AC3, R7.AC1, R7.AC5, R7.AC8, R8.AC3, R9.AC1, R10.AC1_

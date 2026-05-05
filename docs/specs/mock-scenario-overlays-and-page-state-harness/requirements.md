# Mock Scenario Overlay 与页面状态 Harness 需求规格

## 简介

`mock-runtime-legacy-retirement`、`mock-contract-coverage-and-schema-gates` 和 `demo-offline-e2e-validation` 完成后，当前前端 mock 主线已经收敛到 `src/mocks/**`，并具备 OpenAPI coverage registry、handler metadata、schema gate、Dexie 持久 store、demo-offline 纯 MSW 模式和 build 后 Playwright 黑盒验收。

本规格把默认成功链路之外的页面状态纳入可治理验收：通过受控 scenario overlay 和 page-state harness，让空态、慢加载、429/5xx/timeout、403 权限不足、unsupported 501、只读/禁用状态等可被 Vitest、Playwright 和 demo-offline debug/test 模式稳定触发、诊断、复位和审查。

本规格采用“测试/验收专用 overlay + page-state harness”方案。Overlay 只能叠加在当前 `src/mocks/**` 主线 handler、contract registry 和 Dexie data source 之上，不得恢复旧 `src/demo/**`、旧环境变量、多场景 runtime package、active pointer、candidate/promote、MCP runtime package writer、独立 mock server 或客户演示中的场景切换 UI。

非目标：

- 不恢复旧 demo/scenario runtime、`VITE_DEMO_SCENARIO_ID`、scenario package、release pointer、candidate/promote 或 active pointer。
- 不提供面向客户或售前演示操作者的可视化场景切换 UI。
- 不引入 Prism、Microcks、WireMock 或真实后端作为 overlay 执行层。
- 不替换现有 `src/mocks/handlers/**`、contract registry、schema gate、Dexie store 或 demo-offline E2E。
- 不要求一次性覆盖全部后台管理页面、全部 OpenAPI operations 或全部异常组合。
- 不把页面状态验收写成直接改 mock store、直接调用 handler 或 mock `@/utils/request` 的白盒捷径。
- 不在本规格内接入 GitLab/GitHub CI；本阶段先交付本地可重复命令和测试入口。

## Clarifications

### Session 2026-05-02

- Q: 第四个 spec 采用哪种范围？ -> A: 采用“测试/验收专用 overlay + page-state harness”；不做面向客户的场景切换 UI。
- Q: overlay 与旧多场景 runtime 的关系是什么？ -> A: overlay 是当前 `src/mocks/**` 主线上的受控测试叠加层，不恢复旧 runtime package、active pointer、candidate/promote 或旧环境变量。
- Q: 第四个 spec 与第三个 E2E spec 的边界是什么？ -> A: 第三个 spec 验证默认成功主链路；本规格专门覆盖错误、空态、慢接口、权限和只读/unsupported 页面状态。
- Q: 首批 overlay/page-state 的门禁姿态怎么定？ -> A: 采用 Core matrix；项目、版本、拓扑、simulation 主链路必须有代表状态覆盖，其他 critical endpoint 先 warning。
- Q: Playwright 侧 overlay 激活机制是否需要支持首屏请求前生效？ -> A: 采用 Test bootstrap + runtime API；首屏前用受控测试 bootstrap 注入，页面加载后用当前 mock runtime API 激活/复位。
- Q: overlay 是否允许改写 Dexie/seed 数据？ -> A: 采用 Read-only projection；overlay 可读取 dataSource 并返回投影、过滤或替代响应，但不得写 Dexie 或修改 seed。
- Q: 多个 overlay 同时激活时的冲突策略怎么定？ -> A: 采用 Compatible composition；允许 registry 声明的可组合 overlay，同时激活同 endpoint 或同状态语义冲突必须 fail fast。
- Q: page-state E2E 的本地命令入口怎么定？ -> A: 新增独立 `yarn e2e:demo-offline:page-state`，复用现有 build/preview runner，不并入默认成功链路 E2E。

## 需求列表

### R1: 建立受控 Overlay Registry
**用户故事:** 作为 mock 平台维护者，我希望所有页面状态 overlay 都有机器可读 registry，以便异常状态不再散落在测试私有 handler 或临时数据修改中。
**验收标准 (EARS):**
- R1.AC1: WHEN 新增页面状态 overlay THEN 必须声明稳定 overlay id、名称、状态类型、目标 handler tag、method/path、适用页面、owner、测试文件、风险说明、复位策略和可组合性元数据。
- R1.AC2: WHEN overlay registry 被加载 THEN 系统必须校验 overlay id 唯一、目标 handler tag 存在、method/path 能映射到 contract registry 或明确本地契约例外。
- R1.AC3: IF overlay 目标 endpoint 属于 OpenAPI operation THEN overlay registry 必须能追溯到对应 coverage registry entry，不得只依赖源码正则或测试命名推断。
- R1.AC4: IF overlay 目标 endpoint 是 `missing`、`real-only` 或未登记 endpoint THEN registry 必须拒绝启用，除非该 overlay 明确用于未覆盖 501 探测并绑定 `unhandled-api` 语义。
- R1.AC5: WHEN 生成 overlay 摘要或检查报告 THEN 输出必须稳定排序，并包含 overlay id、状态类型、目标 handler、页面范围、测试证据和是否可用于 demo-offline E2E。

### R2: 限制 Overlay 激活边界
**用户故事:** 作为质量负责人，我希望 overlay 只能在测试和受限 debug 环境中启用，以便生产、正常开发和客户演示包不会被异常状态污染。
**验收标准 (EARS):**
- R2.AC1: WHEN 应用运行在 `real` 模式 THEN 系统不得初始化、读取或应用任何 overlay。
- R2.AC2: WHEN 应用运行在普通 `fallback` 或默认 `demo-offline` 成功链路 THEN overlay 必须默认关闭，除非测试 harness 或受限 debug API 显式激活。
- R2.AC3: WHEN overlay 在页面加载后被激活 THEN 激活入口必须挂在当前 `window.__MOCK_RUNTIME__` 或等价当前 mock 主线 debug API 上，不得新增旧 `__DEMO_RUNTIME__` 或旧 scenario 全局入口。
- R2.AC4: IF 有代码重新引入 `VITE_DEMO_SCENARIO_ID`、`VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS`、active pointer 或 candidate/promote 作为 overlay 激活机制 THEN 静态门禁必须失败。
- R2.AC5: WHEN demo-offline 静态包交付给默认成功链路 E2E THEN 未显式激活 overlay 时必须保持第三个 spec 的默认主链路行为不变。
- R2.AC6: WHEN 测试需要 overlay 在首屏 `/api/**` 请求前生效 THEN 只能通过 Playwright/Vitest 受控 test bootstrap 注入，不得通过公开 URL query、普通环境变量或客户可见 UI 激活。

### R3: 支持首批页面状态类型
**用户故事:** 作为前端测试维护者，我希望常见页面状态有统一 overlay 类型，以便项目、版本、拓扑和 simulation 页面能被稳定验收。
**验收标准 (EARS):**
- R3.AC1: WHEN 测试激活空态 overlay THEN 目标列表或只读数据接口必须通过只读投影返回结构合法的空数据，并保留分页、总数、字段类型和 schema 兼容性，不得通过写 Dexie 或改 seed 制造空态。
- R3.AC2: WHEN 测试激活慢加载 overlay THEN 目标请求必须按 registry 声明延迟响应，并且页面 harness 必须验证加载态出现和消失，不得依赖裸 `sleep` 作为主要同步机制。
- R3.AC3: WHEN 测试激活 429、5xx 或 timeout overlay THEN 响应必须使用统一 problem/error 结构、稳定 HTTP 状态、可定位 handler tag 和 overlay 诊断 header。
- R3.AC4: WHEN 测试激活 403 权限 overlay THEN 页面必须进入权限不足、按钮隐藏/禁用或路由拒绝等可观察状态，并且不得通过修改真实用户权限代码绕过正常鉴权流程。
- R3.AC5: WHEN 测试激活 unsupported 501 overlay THEN 响应必须与当前 `unsupported-501` 或 `MOCK_API_NOT_IMPLEMENTED` 语义一致，并输出可定位 handler tag 和原因。
- R3.AC6: WHEN 测试激活只读/禁用 overlay THEN 页面必须展示只读、禁用操作或受控提示状态，且不得尝试访问真实后端补齐写操作。

### R4: 保持 Overlay 与当前 Handler 主线叠加
**用户故事:** 作为 mock runtime 维护者，我希望 overlay 只覆盖目标响应或状态差异，以便不会分叉出第二套业务 handler。
**验收标准 (EARS):**
- R4.AC1: WHEN overlay 未激活 THEN `createMockHandlers()`、demo-offline E2E 和 contract schema tests 的默认行为必须保持不变。
- R4.AC2: WHEN overlay 激活 THEN 系统必须优先复用当前 handler metadata、response helper、schema validator 和 data source，只替换 registry 声明的目标行为。
- R4.AC3: IF overlay 需要返回业务成功响应 THEN 响应 body 必须保持 OpenAPI schema 或本地契约兼容，不得为测试方便返回页面私有假结构。
- R4.AC4: IF overlay 需要错误响应 THEN 它必须复用或扩展当前 `error-common` 语义，不得在测试目录维护并行业务错误契约。
- R4.AC5: WHEN 多个 overlay 同时被请求激活 THEN 只有 registry 明确声明可组合的 overlay 可以合成；同 endpoint、同 handler tag 或同状态语义冲突必须 fail fast，不得通过隐式优先级或 handler 注册顺序覆盖。
- R4.AC6: IF overlay 需要基于现有业务数据生成响应 THEN 它可以读取当前 data source 并返回投影、过滤或替代响应，但不得写入 Dexie、修改 seed dataset 或绕过现有 repository 持久写边界。

### R5: 提供确定性激活、复位和隔离能力
**用户故事:** 作为 E2E 维护者，我希望每个测试能独立激活和复位 overlay，以便连续运行、多 worker 或失败重试不会相互污染。
**验收标准 (EARS):**
- R5.AC1: WHEN Vitest 或 Playwright 测试开始 THEN 默认 overlay 集合必须为空，并且不受前一个测试、浏览器 context、IndexedDB、localStorage、sessionStorage 或 cookie 残留影响。
- R5.AC2: WHEN 测试调用 overlay 激活 API THEN 系统必须返回当前已激活 overlay 列表或可验证状态，方便断言激活成功。
- R5.AC3: WHEN 测试调用 overlay reset API THEN 所有 overlay 必须被清空，且不隐式 reset seed dataset，除非测试显式调用 `resetDataset()`。
- R5.AC4: IF overlay 激活失败、overlay id 不存在或 overlay 与当前 runtime mode 不兼容 THEN API 必须 fail fast，并返回可定位错误信息。
- R5.AC5: WHEN Playwright 使用多个 browser context 或后续并行 worker THEN overlay 状态必须按 context、worker 或测试实例隔离，不得使用跨测试全局可变状态造成串扰。
- R5.AC6: WHEN overlay reset 完成 THEN Dexie 数据、seed dataset 和测试已显式创建的业务数据不得因为 overlay reset 被隐式回滚；业务数据回滚只能通过现有 `resetDataset()` 或测试清理流程完成。
- R5.AC7: IF 一次激活请求包含冲突 overlay THEN 系统必须整体拒绝该请求，并保持请求前已激活 overlay 状态不变，不得留下部分激活状态。

### R6: 增加 Overlay 诊断 Header 与网络记录
**用户故事:** 作为代码审查者，我希望 overlay 响应能被网络日志直接识别，以便失败报告能定位到具体状态叠加而不是只看到 HTTP 错误。
**验收标准 (EARS):**
- R6.AC1: WHEN overlay 修改 `/api/**` 响应 THEN 响应必须保留 `X-Mock-Response` 和 `X-Mock-Handler`，并新增或等价提供 `X-Mock-Overlay` 诊断信号。
- R6.AC2: WHEN overlay 响应由状态类型驱动 THEN 诊断信息必须包含 overlay id 或稳定状态类型，且不得输出 token、真实账号、密钥或后端连接信息。
- R6.AC3: WHEN Playwright network recorder 捕获 overlay 响应 THEN 失败摘要必须包含页面步骤、method、path、status、handler tag 和 overlay id。
- R6.AC4: IF overlay 响应缺少 mock debug header 或 overlay 诊断 header THEN 相关测试必须失败，而不是只通过页面文本断言。
- R6.AC5: WHEN overlay 触发未覆盖 501 或 unsupported 501 THEN 诊断输出必须能区分“主线缺口 fallback”和“显式 overlay 验收状态”。

### R7: 建立 Page-State Playwright Harness
**用户故事:** 作为 demo-offline 验收维护者，我希望页面级状态测试复用已有 build 后 E2E 入口，以便异常状态也能在真实浏览器和静态包上验证。
**验收标准 (EARS):**
- R7.AC1: WHEN 执行 `yarn e2e:demo-offline:page-state` 或等价 page-state E2E 命令 THEN 测试必须运行在 `dist-demo-offline` 静态 preview 上，并复用现有 demo-offline build/preview runner，不得使用 `yarn dev`、`file://` 或 Computer Use。
- R7.AC2: WHEN Playwright 激活 overlay THEN 首屏请求前必须通过受控 test bootstrap 完成，页面加载后必须通过当前 mock runtime debug API 完成，不得直接导入 handler 或修改源码内存对象。
- R7.AC3: WHEN 验证页面状态 THEN 首批必须覆盖 Core matrix：项目列表空态与写入错误、版本列表空态或错误、拓扑加载或保存错误、simulation 只读或 unsupported 控制状态；这些主链路代表状态缺失时本地 page-state 验收必须失败。
- R7.AC4: WHEN 页面状态需要定位控件或状态区域 THEN 测试必须优先使用 role、label、稳定文本或 `data-testid`，不得依赖随机 class、构建 hash、深层 DOM 层级或截图像素作为主要判断。
- R7.AC5: WHEN page-state E2E 失败 THEN artifact 必须保留 trace、screenshot、network log 或等价报告，并且报告不得包含敏感凭据。
- R7.AC6: IF 某个页面缺少可稳定观察的错误态、空态或禁用态信号 THEN 实现必须补充最小必要 UI 状态或 selector，而不是让测试只断言请求已失败。
- R7.AC7: IF test bootstrap 预置了 overlay THEN 测试必须能在当前 browser context 内读取、断言和清空该预置状态，避免影响后续页面或测试。
- R7.AC8: WHEN 执行默认 `yarn e2e:demo-offline` 成功链路验收 THEN page-state overlay suite 不得默认并入该命令，除非开发者显式运行 page-state 命令或后续 CI 单独接入。

### R8: 建立 Vitest/API Page-State Harness
**用户故事:** 作为单元和合约测试维护者，我希望 API 与组件层也能复用 overlay 语义，以便错误和空态不必全部依赖慢速 E2E。
**验收标准 (EARS):**
- R8.AC1: WHEN Vitest 验证 API contract 或 composable 错误路径 THEN 测试必须优先通过真实 API function、`@/utils/request` 或 MSW request path 进入 overlay，不得直接 mock `@/utils/request` 逃避 HTTP 契约。
- R8.AC2: WHEN 测试需要空态、403、429、5xx、timeout 或 unsupported 501 THEN 应复用 overlay registry 或统一 overlay handler factory，不得在测试文件内复制业务响应结构。
- R8.AC3: WHEN overlay 用于组件或 composable 测试 THEN harness 必须能在每个测试后重置 MSW handlers 和 overlay 状态。
- R8.AC4: WHEN overlay response body 属于核心 OpenAPI JSON 响应 THEN schema gate 或 targeted test 必须能验证响应结构兼容，除非 registry 标记 schema-unavailable 或 problem-response 例外。
- R8.AC5: IF 测试新增了私有 HTTP 契约 handler 而没有登记 overlay 或说明非 HTTP 合约测试原因 THEN mock standards 检查必须失败或输出可审查警告。

### R9: 同步 Contract Coverage 与 Overlay 治理
**用户故事:** 作为 PR reviewer，我希望 overlay 覆盖关系能和 contract coverage 一起审查，以便异常状态不是隐藏在测试里的隐性能力。
**验收标准 (EARS):**
- R9.AC1: WHEN 执行 mock contract 或 overlay 检查命令 THEN 系统必须校验 overlay registry 中引用的 handler tag、operation、测试文件和状态类型仍然有效。
- R9.AC2: WHEN coverage report 或 overlay report 输出 endpoint 明细 THEN 它必须能显示该 endpoint 是否存在 overlay 覆盖，以及覆盖了哪些页面状态类型。
- R9.AC3: IF Core matrix 覆盖的 endpoint 缺少对应错误态、空态或 unsupported 状态测试证据 THEN 本地 overlay/page-state 门禁必须失败；IF 其他 critical endpoint 暂无 overlay 覆盖 THEN 报告必须输出 warning 和后续补齐建议，但首期不阻断验收。
- R9.AC4: WHEN OpenAPI operation、handler tag 或 contract registry entry 变更 THEN 失效 overlay 必须被门禁发现，并输出具体 overlay id、method/path 和失效原因。
- R9.AC5: IF overlay 覆盖的是本地临时契约或 schema-unavailable endpoint THEN 报告必须明确标注，不得把它计入 OpenAPI schema-validated overlay coverage。

### R10: 保持安全、文档和 Definition of Done
**用户故事:** 作为团队协作者，我希望 overlay/page-state 能力有清晰使用边界和完成标准，以便后续新增 mock 能力不会重新走向多主线。
**验收标准 (EARS):**
- R10.AC1: WHEN 阅读 `src/mocks/README.md`、`tests/README.md` 或 mock DoD THEN 文档必须说明 overlay registry、激活方式、复位方式、支持状态类型、测试命令和默认关闭边界。
- R10.AC2: WHEN 新增或修改 demo-offline 主链路页面、handler、API wrapper 或 critical endpoint THEN DoD 必须包含是否需要新增 page-state overlay 和对应 Playwright/Vitest 覆盖。
- R10.AC3: IF 文档提到旧 demo runtime、多场景 package、MCP package writer、active pointer、candidate/promote 或旧环境变量作为当前 overlay 能力 THEN 必须明确其非目标、历史或已退场状态。
- R10.AC4: WHEN overlay debug API 暴露给浏览器测试 THEN 它必须限制在 demo-offline debug/test 环境，且只能暴露 overlay 列表、激活、复位和诊断读取等最小能力。
- R10.AC5: WHEN 本规格 requirements 被批准后 THEN 后续 design 必须明确本地命令、首批页面矩阵、门禁严格度和与 `demo-offline-e2e-validation` 的执行顺序。
- R10.AC6: WHEN 文档描述 page-state 验收入口 THEN 必须说明 `yarn e2e:demo-offline:page-state` 与默认 `yarn e2e:demo-offline` 的职责差异，以及它们复用同一 build/preview 基础设施。

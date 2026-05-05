# Demo Offline E2E 验证需求规格

## 简介

`mock-runtime-legacy-retirement` 和 `mock-contract-coverage-and-schema-gates` 完成后，当前 mock 主线已经收敛到 `src/mocks/**`，并具备 OpenAPI coverage registry、handler metadata、核心 schema gate、Dexie 持久 store 和 demo-offline 纯 MSW 运行模式。

本规格把 demo-offline 从“构建能通过、handler 测试能通过”升级为“构建后的静态演示包可被真实浏览器黑盒验证”。目标是在 `yarn build:demo-offline` 之后，通过静态 preview 和 Playwright E2E 覆盖核心演示闭环：登录、菜单加载、项目列表、新增/编辑项目、克隆/固化版本、保存拓扑、查看 simulation 只读页、验证持久写、执行 reset dataset 并确认恢复初始状态。

本规格不是替代现有 Vitest、mock contract coverage 或 schema gate，而是在它们之后增加页面级交付验收。E2E 必须继续复用当前 `src/mocks/**` runtime、MSW Service Worker、Dexie store、contract registry 和 debug header，不得恢复旧 `src/demo/**`、多场景 runtime package、active pointer、candidate/promote、MCP runtime package writer 或独立 mock server。

非目标：

- 不使用 Computer Use、人工浏览器操作或截图巡检作为自动化门禁。
- 不引入 Prism、Microcks、WireMock 或真实后端来补齐 demo-offline 缺口。
- 不恢复旧 `src/demo/**`、scenario package、release pointer、candidate/promote 或 active pointer。
- 不在本规格内建设 scenario overlay/page-state harness；错误、空态、慢接口和权限状态留给 `mock-scenario-overlays-and-page-state-harness`。
- 不要求覆盖全部后台管理页面、全部 OpenAPI operations 或完整仿真启动/暂停/停止控制链路。
- 不把 E2E 测试写成直接操作 mock store 或直接调用 handler 的白盒测试；页面验收必须从真实浏览器页面和真实请求链路进入。
- 不在本规格内接入 GitLab/GitHub CI、scheduled job 或 MR gate；本阶段只交付本地 CLI/脚本入口，CI 后续单独接入。

## Clarifications

### Session 2026-05-02

- Q: 第三个 spec 的范围基线采用哪种方案？ -> A: 采用“核心演示闭环”，覆盖 build 后 preview、登录、菜单、项目/版本/拓扑/simulation 只读、持久写和 reset。
- Q: 第三个 spec 是否按 Playwright 作为 E2E runner 来写？ -> A: 可以，采用 Playwright 路线。
- Q: E2E 与后续 overlay spec 的边界是什么？ -> A: 本规格只验证默认 demo-offline 主链路，不引入页面状态 overlay；overlay 作为第四个 spec 后续处理。
- Q: demo-offline E2E 首次接入 CI 时，默认门禁姿态应该是哪一种？ -> A: 本规格暂不考虑 CI；先交付本地 CLI/脚本入口，CI 后续单独接入。
- Q: Playwright 首期浏览器覆盖范围选哪种？ -> A: 首期只覆盖 Chromium；Firefox 和 WebKit 留作后续扩展。
- Q: 拓扑保存 E2E 的首期深度要到哪一层？ -> A: 首期只验证打开已有拓扑并触发保存、保存请求成功、刷新后可读回，不要求图形编辑。

## 需求列表

### R1: 建立 build 后 demo-offline 黑盒 E2E 入口
**用户故事:** 作为演示交付负责人，我希望 E2E 验证运行在 `dist-demo-offline` 静态 preview 上，以便证明交付包本身可用，而不是只证明源码开发模式可用。
**验收标准 (EARS):**
- R1.AC1: WHEN 执行 demo-offline E2E 命令 THEN 系统必须先生成或要求已存在 `dist-demo-offline`，并且该产物必须来自 `yarn build:demo-offline` 或等价 demo-offline 构建命令。
- R1.AC2: WHEN E2E 启动被测应用 THEN 必须通过静态 HTTP preview 服务访问 `dist-demo-offline/index.html`，不得通过 `yarn dev`、源码 Vite dev server 或 `file://` 直开页面完成验收。
- R1.AC3: WHEN 本地开发者运行 E2E THEN 必须存在一个稳定脚本或命令入口，例如 `yarn e2e:demo-offline` 或等价命令，能够完成 preview 启动、测试执行和进程清理。
- R1.AC4: IF `dist-demo-offline` 缺失、preview 端口不可用、Service Worker 无法注册或测试浏览器缺失 THEN E2E 命令必须 fail fast，并输出明确修复提示。
- R1.AC5: WHEN 选择 E2E runner THEN 本规格必须采用 Playwright 或等价真实浏览器自动化能力，首期浏览器覆盖范围为 Chromium；不得使用 Computer Use、人工点击流程或仅 Vitest unit/browser test 代替 build 后黑盒验收。

### R2: 验证 demo-offline 启动、登录和菜单加载
**用户故事:** 作为售前演示人员，我希望静态演示包保留真实登录和菜单初始化流程，以便客户看到的入口与实际产品行为一致。
**验收标准 (EARS):**
- R2.AC1: WHEN Playwright 打开 demo-offline preview 根路径 THEN 页面必须进入登录页或等价未登录入口，并且不得自动绕过登录流程。
- R2.AC2: WHEN 测试使用 mock dataset 中声明的演示账号登录 THEN 登录必须成功，并写入与现有前端鉴权流程兼容的 token/session 状态。
- R2.AC3: WHEN 登录后加载用户信息和路由 THEN 页面必须通过当前 MSW handler 获取 `getInfo`、`getRouters` 或等价系统接口，并渲染可导航菜单。
- R2.AC4: WHEN 登录后首次进入业务页面 THEN 默认 landing 必须可稳定到达首页、项目入口或当前 demo-offline 主链路入口，不得停留在空白页、404、401 或无限 redirect。
- R2.AC5: WHEN demo-offline debug 能力开启 THEN E2E 必须能确认 `window.__MOCK_RUNTIME__` 或等价当前 mock runtime devtools 暴露的 mode 为 `demo-offline`，不得依赖旧 `__DEMO_RUNTIME__`。

### R3: 覆盖项目列表、新增、编辑和持久写链路
**用户故事:** 作为演示操作者，我希望项目核心写操作在离线包中可用并可持久化，以便客户操作后刷新页面仍能看到一致结果。
**验收标准 (EARS):**
- R3.AC1: WHEN E2E 进入项目列表页 THEN 页面必须展示来自单套 mock dataset/Dexie store 的种子项目数据，并且列表请求必须走当前 MSW handler。
- R3.AC2: WHEN 用户通过页面新增一个项目 THEN 新项目必须在项目列表中可见，并且对应 API 响应必须通过 `project:create` 或等价当前 handler tag 可定位。
- R3.AC3: WHEN 用户通过页面编辑刚新增或已有项目 THEN 更新后的项目名称、描述或等价关键字段必须在列表或详情中可见。
- R3.AC4: IF 页面刷新、重新进入项目列表或在同一浏览器上下文中新开页面 THEN E2E 创建或编辑的数据必须仍然可读，证明写入已进入 IndexedDB/Dexie 持久层而不是仅存在于内存状态。
- R3.AC5: IF 项目写操作失败 THEN E2E 失败报告必须能定位到失败的页面步骤、请求 URL、HTTP 状态和 `X-Mock-Handler` 或 missing endpoint 信息。

### R4: 覆盖版本克隆、固化和拓扑保存链路
**用户故事:** 作为产品演示设计者，我希望版本和拓扑设计的关键操作在离线演示中可闭环，以便演示不止停留在列表浏览。
**验收标准 (EARS):**
- R4.AC1: WHEN E2E 打开某个项目详情或版本列表 THEN 页面必须能够展示该项目下的版本数据，并且版本列表请求必须走当前 mock runtime。
- R4.AC2: WHEN 用户执行克隆版本操作 THEN 新克隆版本必须在版本列表中可见，并且响应必须通过 `project:version:clone` 或等价当前 handler tag 可定位。
- R4.AC3: WHEN 用户执行固化版本操作 THEN 版本固化状态必须在页面中可观察，并且响应必须通过 `project:version:lock` 或等价当前 handler tag 可定位。
- R4.AC4: WHEN 用户进入拓扑设计页并对已有拓扑执行保存 THEN 保存请求必须走当前拓扑保存 handler，并且保存后的拓扑数据必须能在刷新或重新打开拓扑页后读回；首期不要求通过 E2E 执行图形拖拽、节点编辑或拓扑结构变更。
- R4.AC5: IF 页面当前缺少稳定交互定位点导致版本或拓扑 E2E 只能依赖脆弱 CSS selector THEN 实现必须补充稳定的 role、label 或 `data-testid`，不得把脆弱 selector 作为长期验收路径。

### R5: 验证 simulation 只读演示页可访问
**用户故事:** 作为客户演示操作者，我希望 simulation 只读页在无真实后端时仍可打开并展示预置数据，以便演示核心实时/仿真视图不会中断。
**验收标准 (EARS):**
- R5.AC1: WHEN E2E 从项目或版本链路进入 simulation 页面 THEN 页面必须成功渲染主视图，不得出现空白页、401、404、未捕获异常或无限 loading。
- R5.AC2: WHEN simulation 页面加载状态、消息、带宽、告警、事件或等价只读数据 THEN 请求必须由当前 simulation mock handlers 响应，并能通过 `simulation:*` handler tag 诊断。
- R5.AC3: IF 页面暴露启动、暂停、停止、故障注入或事件写入等控制入口 THEN 本规格不要求这些控制真正执行；若被测试探测到对应请求，必须返回明确的 unsupported 501 语义和可定位 handler tag，而不得访问真实后端。
- R5.AC4: WHEN simulation 只读页完成加载 THEN E2E 必须至少断言一个业务可见信号，例如项目名、拓扑画布、状态摘要、消息列表、带宽图表、告警区域或等价稳定 UI 状态。

### R6: 增加 demo-offline 网络隔离和诊断断言
**用户故事:** 作为质量负责人，我希望 E2E 能证明 demo-offline 不会偷偷访问真实后端，以便静态交付包在无后端环境中可靠运行。
**验收标准 (EARS):**
- R6.AC1: WHEN E2E 运行期间发生 `/api/**` 请求 THEN 测试必须记录请求和响应，并断言关键业务 API 不访问真实后端域名、真实后端端口或独立 mock server。
- R6.AC2: WHEN 关键 API 由 mock handler 处理 THEN 响应必须携带 `X-Mock-Response`、`X-Mock-Handler` 或等价当前 debug 信号，确保失败可追溯到 handler metadata。
- R6.AC3: WHEN E2E 主动探测一个未覆盖的关键 `/api/**` 请求 THEN demo-offline runtime 必须返回确定性 `501 MOCK_API_NOT_IMPLEMENTED`，并携带 `X-Mock-Handler: unhandled-api` 或等价 debug header。
- R6.AC4: IF 任一关键 API 返回 404、500、CORS 错误、网络错误或缺少 mock debug header THEN E2E 必须失败并输出 method、URL、status、handler tag 和页面步骤。
- R6.AC5: IF 测试发现 E2E 消费了未在 contract registry 中标记为 critical 的 demo-offline 主链路 API THEN 测试或辅助审计必须提示补充 registry，而不得静默扩大 E2E 覆盖范围。

### R7: 验证 reset dataset 和测试隔离
**用户故事:** 作为 E2E 维护者，我希望测试能重置离线数据并隔离每次运行，以便本地结果稳定可重复，并为后续 CI 复用留出隔离基础。
**验收标准 (EARS):**
- R7.AC1: WHEN E2E 已经创建或修改项目、版本或拓扑数据 THEN 测试必须通过 `window.__MOCK_RUNTIME__.resetDataset()`、页面重置入口或等价当前 mock runtime API 执行 dataset reset。
- R7.AC2: WHEN reset dataset 完成并刷新页面 THEN 测试创建或修改的数据必须消失，初始 seed 数据必须恢复到确定性状态。
- R7.AC3: WHEN E2E 在本地连续运行多次，或后续 CI 复用同一本地命令时 THEN IndexedDB、localStorage、sessionStorage、cookie 和 token 状态不得造成跨运行污染。
- R7.AC4: IF reset API 不存在、不可调用或返回失败 THEN E2E 必须失败并提示当前 demo-offline runtime 缺少可自动化重置能力。
- R7.AC5: WHEN 测试需要隔离多个 spec 或 worker THEN 必须使用独立浏览器 context、显式清理存储或等价机制，避免并行测试竞争同一个 Dexie 数据库状态。

### R8: 建立稳定选择器、等待策略和失败 artifact
**用户故事:** 作为前端测试维护者，我希望 E2E 不依赖脆弱 DOM 结构，以便页面样式调整不会频繁打断演示验收。
**验收标准 (EARS):**
- R8.AC1: WHEN E2E 定位关键控件和断言关键状态 THEN 必须优先使用 role、label、可访问名称、稳定文本或 `data-testid`，不得依赖随机 class、构建 hash、深层 DOM 层级或截图像素作为主要判断。
- R8.AC2: IF 现有页面缺少稳定定位点 THEN 实现必须为登录、菜单、项目列表、项目表单、版本操作、拓扑保存和 simulation 主视图补充最小必要的稳定定位点。
- R8.AC3: WHEN E2E 等待异步加载或保存结果 THEN 必须等待明确 UI 状态、路由状态、网络响应或 IndexedDB 可读结果，避免使用裸 `sleep` 作为主要同步机制。
- R8.AC4: WHEN E2E 失败 THEN 必须保留可审查 artifact，例如 trace、screenshot、video、network log 或等价报告，并且 artifact 不得包含 token、真实凭据或敏感后端配置。
- R8.AC5: WHEN 正常本地环境执行已构建产物的 demo-offline E2E THEN 测试本体应保持在可接受反馈时间内；若超出目标时间，必须拆分 smoke 与 full suite 或调整后续运行策略。

### R9: 建立本地 CLI 入口并预留 CI 接入
**用户故事:** 作为项目维护者，我希望 demo-offline E2E 先通过本地 CLI/脚本稳定落地，以便在不引入 CI 波动的前提下验证离线演示包。
**验收标准 (EARS):**
- R9.AC1: WHEN 本规格实施完成 THEN `package.json` 或等价脚本必须提供本地可重复运行的 demo-offline E2E 命令，并在文档中说明依赖安装、浏览器安装和常见失败处理。
- R9.AC2: WHEN 本地 demo-offline E2E 命令执行 THEN 默认流程必须覆盖构建或校验 `dist-demo-offline`、启动静态 preview、运行 Playwright 测试和清理 preview 进程。
- R9.AC3: IF 开发者需要复用已有 `dist-demo-offline` 或已有 preview 服务 THEN 命令可以提供显式参数或独立脚本，但默认入口必须保持自包含且可重复。
- R9.AC4: WHEN 本规格验收完成 THEN 不要求修改 GitLab CI、GitHub workflow、scheduled job 或 MR gate，也不得把 CI 结果作为本阶段完成条件。
- R9.AC5: WHEN 后续单独接入 CI 或扩展浏览器矩阵 THEN CI job 必须复用本规格沉淀的本地命令或薄包装命令，避免 CI 与本地验收口径分叉。
- R9.AC6: WHEN 文档描述完整本地验收顺序 THEN demo-offline E2E 应位于 `yarn build:demo-offline`、mock mainline bundle scan 和 contract gate 之后，避免用页面测试掩盖更早的构建或契约失败。

### R10: 同步文档和 demo-offline 验收 Definition of Done
**用户故事:** 作为团队协作者，我希望 demo-offline 的完成标准包含页面级 E2E，以便后续新增演示链路时不再只靠人工点击确认。
**验收标准 (EARS):**
- R10.AC1: WHEN 阅读 `src/mocks/README.md`、测试 README 或 demo-offline runbook THEN 文档必须说明 demo-offline E2E 的本地命令、后续 CI 接入边界、支持的部署方式和不支持 `file://` 直开的原因。
- R10.AC2: WHEN 新增或修改 demo-offline 主链路页面、API wrapper、handler 或持久写能力 THEN DoD 必须包含是否需要更新 Playwright E2E、稳定定位点、network assertions 和 reset 覆盖。
- R10.AC3: WHEN 更新 `docs/specs/README.md` 或相关索引 THEN 必须把 `demo-offline-e2e-validation` 标记为 P1 demo-offline 交付验收 spec，并说明它依赖前两个 P0 mock specs。
- R10.AC4: IF 文档提到旧 demo runtime、多场景 scenario package、MCP package writer、独立 mock server 或人工浏览器操作作为当前 E2E 验收路径 THEN 必须明确其非目标、历史状态或不作为自动化门禁。

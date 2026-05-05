# Demo Offline E2E 验证实现任务

- [x] 1. 接入 Playwright Chromium 基础工具链
  - 在 `ruoyi-fastapi-frontend` 增加 Playwright 依赖和浏览器安装说明，首期只启用 Chromium。
  - 新增 `playwright.demo-offline.config.ts`，配置 `tests/e2e/demo-offline`、`workers: 1`、`baseURL`、trace/screenshot/video artifact 和报告输出目录。
  - 确保 Playwright 配置不启动源码 dev server，不把 Vitest browser 或 WebdriverIO 作为本阶段默认 runner。
  - _需求追溯: R1.AC2, R1.AC5, R8.AC4, R9.AC1_

- [x] 2. 实现 demo-offline 本地 runner 和 package 脚本
  - 新增 `scripts/run-demo-offline-e2e.mjs`，默认执行 `yarn build:demo-offline`、校验 `dist-demo-offline/index.html`、启动静态 preview、等待 HTTP 可访问、运行 Playwright 并清理 preview 进程。
  - 支持 `--skip-build`、`--base-url`、`--port`、`--headed`、`--debug`、`--grep` 等显式参数；默认入口保持自包含。
  - 在 `package.json` 增加 `e2e:demo-offline` 和复用已有 preview 的辅助脚本。
  - 对缺失构建产物、端口不可用、Service Worker 注册失败、浏览器缺失等情况输出明确失败信息。
  - _需求追溯: R1.AC1, R1.AC2, R1.AC3, R1.AC4, R9.AC1, R9.AC2, R9.AC3_

- [x] 3. 建立 E2E helper、fixture 和网络诊断层
  - 新增 `tests/e2e/demo-offline/fixtures.ts`，集中维护演示账号、唯一名称生成和 hash route 导航辅助。
  - 新增 `tests/e2e/demo-offline/network.ts`，记录 `/api/**` 请求/响应，提供 `waitForMockResponse`、mock debug header 断言、真实后端访问拦截和 missing probe。
  - 新增 `tests/e2e/demo-offline/runtime.ts`，封装 `window.__MOCK_RUNTIME__` mode 断言、dataset reset 和受控 snapshot 读取。
  - 新增 `tests/e2e/demo-offline/selectors.ts`，只维护稳定 selector 映射，避免测试散落深层 DOM selector。
  - _需求追溯: R2.AC5, R6.AC1, R6.AC2, R6.AC3, R6.AC4, R6.AC5, R7.AC1, R7.AC4, R8.AC1, R8.AC3, R8.AC4_

- [x] 4. 补充核心页面稳定定位点
  - 为 `src/views/login.vue` 增加登录用户名、密码和提交按钮的稳定定位点。
  - 为 `src/views/project/index.vue` 和 `ProjectFormDialog.vue` 增加项目列表、添加、项目卡片、编辑入口、表单字段和确认按钮定位点。
  - 为 `VersionList.vue` 和相关版本操作入口增加版本列表、版本行、克隆、固化、仿真、拓扑入口定位点。
  - 为 `topo.vue` 和 simulation 主视图增加拓扑页、保存按钮、拓扑可见区域、simulation 页面和主要业务可见区域定位点。
  - 不引入无关 DOM 重构；ZxUI 无法透传时优先用包裹元素或 `aria-label`。
  - _需求追溯: R2.AC1, R3.AC1, R4.AC5, R5.AC4, R8.AC1, R8.AC2, R8.AC3_

- [x] 5. 编写启动、登录、菜单和 landing E2E 场景
  - 新增 `tests/e2e/demo-offline/specs/demo-offline-core.spec.ts` 的首段流程：打开 preview 根路径、确认登录页、使用 `admin/admin123` 登录。
  - 等待 `captchaImage`、`login`、`getInfo`、`getRouters` 等当前 MSW 响应，并断言关键响应带 mock debug header。
  - 登录后断言 `window.__MOCK_RUNTIME__.getMode()` 为 `demo-offline`。
  - 断言默认 landing 能进入项目或当前 demo-offline 主链路入口，不出现空白页、401、404 或无限 redirect。
  - _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R6.AC1, R6.AC2, R6.AC4_

- [x] 6. 编写项目列表、新增、编辑和持久写 E2E 场景
  - 从登录后的主链路进入项目列表，断言 seed 项目可见并等待 `project:list` 响应。
  - 通过页面新增唯一命名项目，等待 `project:create`，并断言新项目在列表中可见。
  - 编辑该项目的名称或描述，等待 `project:update`，并断言更新后字段在列表或详情中可见。
  - 刷新或重新进入项目列表，确认新增/编辑结果仍可读，证明写入 Dexie 持久层。
  - 失败时输出当前步骤、请求 URL、HTTP 状态和 handler tag。
  - _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R6.AC2, R6.AC4, R8.AC3_

- [x] 7. 编写版本克隆、固化和拓扑保存 E2E 场景
  - 打开项目详情或版本列表，等待版本列表请求并断言版本数据可见。
  - 通过页面执行克隆版本，等待 `project:version:clone`，断言克隆版本出现在列表。
  - 对克隆版本执行固化，等待 `project:version:lock`，断言页面可观察到固化状态。
  - 进入拓扑页，对已有拓扑执行保存，等待 `project:topology:save`；首期不执行图形拖拽、节点编辑或拓扑结构变更。
  - 刷新或重新打开拓扑页，断言拓扑页可加载并能读回保存后状态。
  - _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R6.AC2, R6.AC4, R8.AC3_

- [x] 8. 编写 simulation 只读页 E2E 场景
  - 从项目或版本链路进入 simulation 页面，断言主视图可见且没有空白、401、404、未捕获异常或无限 loading。
  - 等待至少一个 `simulation:*` mock 响应，断言页面出现项目名、拓扑画布、状态摘要、消息列表、带宽图表、告警区域中的至少一个稳定业务信号。
  - 不主动执行启动、暂停、停止、故障注入或事件写入；如果页面自动触发控制类请求，断言返回 unsupported 501 且携带可定位 handler tag。
  - _需求追溯: R5.AC1, R5.AC2, R5.AC3, R5.AC4, R6.AC2, R6.AC4_

- [x] 9. 实现 reset dataset、隔离和未覆盖 API 探测
  - 在核心 E2E 流程末尾调用 `window.__MOCK_RUNTIME__.resetDataset()`，刷新后确认 E2E 创建或编辑的数据消失，初始 seed 数据恢复。
  - 确保每次运行使用独立 browser context，并显式清理 localStorage、sessionStorage、cookie 和 token 状态。
  - 在页面上下文主动请求未覆盖 `/api/**` 探测路径，断言返回 `501 MOCK_API_NOT_IMPLEMENTED` 和 `X-Mock-Handler: unhandled-api`。
  - 保持单 worker 或显式串行，避免多个 spec 竞争同一个 Dexie 状态。
  - _需求追溯: R6.AC3, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5, R8.AC4_

- [x] 10. 完成报告、文档和后续 CI 边界说明
  - 配置 Playwright 失败 artifact，并确保网络摘要不输出 Authorization、Cookie、CSRF token 或完整敏感 header。
  - 更新 `src/mocks/README.md`、`tests/README.md` 或 demo-offline runbook，说明本地命令、浏览器安装、复用已有 preview、失败 artifact、`file://` 不支持和后续 CI 接入边界。
  - 更新 `docs/specs/README.md`，把 `demo-offline-e2e-validation` 标记为 P1 demo-offline 交付验收 spec，并说明依赖前两个 P0 mock specs。
  - 明确本阶段不修改 `.gitlab-ci.yml`、`.github/workflows/ci.yml`、scheduled job 或 MR gate；后续 CI 必须复用本地命令。
  - _需求追溯: R8.AC4, R8.AC5, R9.AC4, R9.AC5, R9.AC6, R10.AC1, R10.AC2, R10.AC3, R10.AC4_

- [x] 11. 执行本地验收并修复发现的问题
  - 运行 `yarn mock:contracts`，确认 contract registry 和 critical API 基线可用。
  - 运行 `yarn build:demo-offline` 和 `scripts/check-mock-mainline.sh --require-dist`，确认构建产物和 legacy 防回潮扫描通过。
  - 运行 `yarn e2e:demo-offline --skip-build`，确认本地 CLI、preview、Chromium E2E、网络断言、持久写和 reset 全部通过。
  - 若验收失败，优先修复稳定定位点、等待策略、mock handler tag、路由或 reset 隔离问题，不通过直接 mock store 或跳过页面流程规避。
  - 在交付说明中记录实际运行命令、结果和任何环境限制。
  - _需求追溯: R1.AC1, R1.AC3, R1.AC4, R3.AC5, R6.AC4, R8.AC5, R9.AC1, R9.AC2, R9.AC6_

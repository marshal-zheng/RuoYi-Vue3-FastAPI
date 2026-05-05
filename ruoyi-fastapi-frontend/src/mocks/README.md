# Contract-first 单套 Mock 主线

当前前端 mock 主线是：FastAPI OpenAPI artifact -> 生成 API 类型 -> `src/mocks/data/**` 单套 typed dataset -> `src/mocks/store/**` Dexie 持久 store -> `src/mocks/handlers/**` MSW 网络层。

`fallback` 和 `demo-offline` 复用同一套 handler、同一套 typed data、同一套 store seed/reset 与同一套测试门禁。生产 `real` 模式不启动 MSW，不初始化 mock store。

## 运行模式

业务级运行模式优先由 `VITE_APP_RUNTIME_MODE` 控制：

```bash
VITE_APP_RUNTIME_MODE=real|fallback|demo-offline
```

| 运行模式 | MSW 行为 | 数据来源 | 未覆盖 API |
| --- | --- | --- | --- |
| `real` | 不启动 | 真实后端 | 不适用 |
| `fallback` | 真实后端优先；`404` 或网络异常时回退到 mock | 真实后端 + 单套 typed dataset/store 派生响应 | 非 mock 请求旁路 |
| `demo-offline` | 纯 MSW；不得访问真实后端 | `src/mocks/store/**` 从 `src/mocks/data/**` seed，写操作持久化到 `ruoyi-mock-demo` | 关键 `/api/**` 返回确定性 `501 MOCK_API_NOT_IMPLEMENTED` |

常用命令：

```bash
yarn dev
yarn build:prod
yarn build:demo-offline
yarn preview:demo-offline
yarn e2e:demo-offline
yarn e2e:demo-offline:page-state
yarn api:generate
```

## 已退场边界

历史多场景方案、旧 mock 环境变量（例如 `VITE_DEMO_SCENARIO_ID`、`VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS`）、外部 runtime package writer、active pointer、candidate/promote、MCP 工具链以及旧 demo 运行时代码已从当前主线移除。新增 mock 能力不得恢复这些路径或环境变量。

当前主线新增能力必须进入 `src/mocks/**`，并通过 OpenAPI/type-check/invariant/handler/build 门禁。

## 契约覆盖与 Schema 门禁

契约治理层位于 `src/mocks/contracts/coverage/`：

- `registry/**/*.json` 是已提交的 endpoint 分类与 handler metadata 基线。
- `registry.schema.json` 和 `types.ts` 定义 registry 数据契约。
- `scripts/check-mock-contracts.mjs` 从 `../shared/openapi.json` 生成稳定覆盖矩阵摘要；完整 report 只在显式 `--write-report` 时写入生成路径，不作为默认提交基线。

覆盖分类固定为 `mock-handled`、`real-only`、`unsupported-501`、`legacy-local-contract` 和 `missing`。新增或修改 API 时必须同步 OpenAPI artifact、coverage registry、handler tag、critical 标记、schema 状态和测试证据。OpenAPI response schema 为空、二进制响应或本阶段不可靠时，registry 必须显式写 `schema-unavailable` 或 `binary-response`，并说明原因。

当前方案不引入 Prism、Microcks、WireMock、旧 demo runtime、多场景 runtime package 或 MCP 作为运行时契约覆盖层；这些路径属于非目标、历史或暂停状态。

## Page-State Overlay

页面状态 overlay 位于 `src/mocks/overlays/`，用于测试和验收空态、错误态、慢加载、权限不足、timeout、unsupported 501 和只读/禁用状态。它是当前 `src/mocks/**` 主线 handler 的前置叠加层，不是新的业务 handler 分支。

- `registry/**/*.json` 是事实源，必须声明 overlay id、状态类型、目标 method/path/handlerTag、页面范围、owner、测试文件、risk、Core matrix、resetStrategy 和 composition。
- `registry.schema.json` 与 `types.ts` 限制字段，禁止临时私有属性进入 registry。
- `runtime.ts` 负责激活、复位、冲突检查和状态隔离；冲突激活整体失败，不留下部分状态。
- `handlers.ts` 生成前置 MSW handler，使用 read-only projection wrapper 读取当前 data source，不写 Dexie、不改 seed。
- 所有 overlay 响应都保留 `X-Mock-Response`、`X-Mock-Handler`，并增加 `X-Mock-Overlay`。

Overlay 默认关闭。`real` 模式不启动 mock runtime，因此不会初始化或读取 overlay；默认成功链路 `yarn e2e:demo-offline` 不激活 overlay。首屏前激活只能由 Playwright/Vitest 注入 `window.__MOCK_RUNTIME_BOOTSTRAP__`，页面加载后只能通过 demo-offline debug/test 下的 `window.__MOCK_RUNTIME__.activateOverlays()` 与 `resetOverlays()` 操作。不得通过 URL query、普通环境变量或客户可见 UI 激活。

本地治理命令：

```bash
yarn mock:overlays
yarn mock:overlays:report
yarn test:run src/mocks/overlays tests/unit/api
yarn e2e:demo-offline:page-state
```

`yarn e2e:demo-offline:page-state` 复用 demo-offline build/preview runner，但运行独立 Playwright config 和报告目录，专门覆盖 Core matrix 页面状态；它不会并入默认成功链路 `yarn e2e:demo-offline`。

## 目录结构

```text
src/mocks/
  contracts/             # OpenAPI 尚未覆盖时的临时本地契约与响应辅助类型
  data/                  # 单套 typed mock dataset，按业务域和聚合拆分
  factories/             # seed/refDate 受控的确定性生成工具
  handlers/              # auth/system/project/version/topology/simulation MSW handlers
  invariants/            # 领域数据自洽测试
  runtime/               # setupMockRuntime、demo-offline 501 未覆盖 API 处理、app entry
  overlays/              # page-state overlay registry、runtime、handler factory
  store/                 # Dexie DB、seed/reset、MockDataSource 和 repositories
  utils/                 # 请求读取、响应包装、withBackendFallback
```

`index.ts` 只做轻量聚合导出，不承载大段业务记录或生成逻辑。

## 新增业务 Mock DoD

新增或修改业务模块时，至少交付：

- OpenAPI artifact 同步，或在 `contracts/` 标注临时本地契约和后续迁移动作。
- coverage registry 同步，包含 endpoint 分类、critical 评估、owner、handler tag、schema 状态、测试文件和迁移动作。
- typed mock data/factory，使用固定 seed、固定 reference time，不使用未受控随机数或动态时钟。
- MSW handler，通过真实 API 函数或请求兼容层进入 HTTP 链路测试。
- 核心 JSON 响应通过 OpenAPI/AJV runtime schema validation，或在 registry 中写明 `schema-unavailable` 例外；binary/file download endpoint 使用 `binary-response`。
- 错误场景使用 `handlers/error-common.ts` 与 `scenarios/error.ts`，覆盖 `error-timeout`、`error-5xx`、`error-429`；测试不得维护并行 HTTP 契约。
- 页面状态验收需要评估是否新增 `src/mocks/overlays/registry/**` 条目、Vitest/API overlay 覆盖和 page-state Playwright 覆盖；默认成功链路不能被 overlay 污染。
- invariant 测试，覆盖外键、唯一键、枚举、必填展示字段和核心业务关系。
- 持久写边界：核心演示写操作进入 `store/`；只读展示接口保持可预测。
- demo-offline 验收说明，包含 Playwright E2E、稳定定位点、关键 `/api/**` mock header 覆盖、reset dataset 和未覆盖 501 行为。

## 测试与门禁

Vitest 在 `tests/setup.ts` 统一接入 MSW Node server。API 合约测试必须走真实 API 函数或请求兼容层，禁止直接 mock `@/utils/request` 来替代 HTTP 合约。

常用检查：

```bash
cd ../ruoyi-fastapi-backend
.venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json --check

cd ../ruoyi-fastapi-frontend
yarn api:generate
yarn type-check
yarn test:run src/mocks
yarn mock:contracts
yarn test:run src/mocks/contracts src/mocks/handlers/api-contract-schema.test.ts
yarn mock:overlays
yarn test:run src/mocks/overlays tests/unit/api
yarn build:demo-offline
yarn e2e:demo-offline --skip-build
yarn e2e:demo-offline:page-state --skip-build

cd ..
scripts/check-mock-mainline.sh
```

完整验收还应运行：

```bash
cd ruoyi-fastapi-frontend
yarn lint:check
yarn type-check
yarn type-check:strict
yarn mock:contracts
yarn mock:overlays
yarn test:run
yarn build:prod
yarn build:demo-offline

cd ..
scripts/check-mock-mainline.sh --require-dist

cd ruoyi-fastapi-frontend
yarn e2e:demo-offline --skip-build
```

## demo-offline 页面级 E2E

`yarn e2e:demo-offline` 是本地默认入口：先运行 `yarn build:demo-offline`，校验 `dist-demo-offline/index.html`，启动 Vite 静态 preview，再用 Playwright Chromium 执行 `tests/e2e/demo-offline`，结束后清理 preview 进程。首次运行前安装浏览器：

```bash
cd ruoyi-fastapi-frontend
yarn playwright install chromium
```

可复用已有构建或 preview：

```bash
yarn e2e:demo-offline --skip-build
yarn e2e:demo-offline:reuse
yarn e2e:demo-offline --skip-build --base-url=http://127.0.0.1:4173
```

E2E 只支持 HTTP preview，不支持 `file://` 直开，因为 MSW Service Worker、hash 路由、IndexedDB 持久写和 `/api/**` mock header 都需要同源 HTTP 环境。失败 artifact 输出到 `tests/reports/demo-offline-e2e*`，网络摘要只保留 method、URL、status 和 mock 诊断 header。本阶段不修改 GitLab/GitHub CI；后续 CI 接入必须复用上述本地命令或薄包装命令。

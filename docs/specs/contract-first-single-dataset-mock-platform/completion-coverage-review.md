# 完成度评估

评估日期：2026-04-30  
范围：`requirements.md`、`design.md`、`tasks.md` 全部显式条目。  
结论：全部条目为 `covered`。

## Requirements

| 条目 | 状态 | 证据 |
| --- | --- | --- |
| R1.AC1 | covered | `src/mocks/data/index.ts` 聚合唯一 `mockDataset`；`src/mocks/runtime/setup.ts` 为 fallback/demo-offline 共用入口；`src/mocks/store/seed.ts` 从同一 dataset seed。 |
| R1.AC2 | covered | `src/mocks/data/**` 使用 `satisfies`；`src/mocks/handlers/api-contract.test.ts` 通过前端 API 函数进入 HTTP 链路；`yarn type-check` 通过。 |
| R1.AC3 | covered | `scripts/check-mock-mainline.sh` 禁止当前文档把 MCP/candidate/promote 当主线；`src/demo/runtime/mode.ts` 不再读取 legacy active pointer。 |
| R1.AC4 | covered | project/version/topology/simulation 数据在 `src/mocks/data/project/**` 和 `src/mocks/data/simulation/**` 单源维护，handler 通过 `src/mocks/handlers/projections.ts` 派生响应。 |
| R2.AC1 | covered | `src/mocks/{data,factories,handlers,invariants,store,contracts,runtime}` 已按职责分层。 |
| R2.AC2 | covered | 工程项目域拆为 `projects.ts`、`versions.ts`、`topologies.ts`；simulation 拆为 `sessions.ts`、`frames.ts`、`messages.ts`、`events.ts`。 |
| R2.AC3 | covered | auth/system 小域保持域内文件拆分且可继续扩展；`src/mocks/data/auth/index.ts`、`src/mocks/data/system/index.ts` 只聚合。 |
| R2.AC4 | covered | `src/mocks/data/index.ts`、`src/mocks/index.ts` 仅聚合导出；无大段业务记录。 |
| R3.AC1 | covered | `ruoyi-fastapi-backend/scripts/export_openapi.py`、`shared/openapi.json`、`scripts/generate-api-types.sh`、`src/api/_generated/**`；mock contracts/data/handler 已绑定生成类型；OpenAPI check 和 `yarn api:generate` 通过。 |
| R3.AC2 | covered | `export_openapi.py --check` 比对 artifact 并漂移返回非 0；命令输出 `OpenAPI artifact is up to date`。 |
| R3.AC3 | covered | `src/mocks/contracts/local.ts` 声明临时本地契约并注明迁移到 `shared/openapi.json` 生成类型。 |
| R3.AC4 | covered | `src/mocks/contracts/response.ts`、`src/mocks/utils/response.ts`、`project.ts` 导出占位和错误响应；API contract tests 覆盖分页、导出、错误和 501。 |
| R4.AC1 | covered | `src/mocks/utils/with-backend-fallback.ts`；`with-backend-fallback.test.ts` 和 `fallback.integration.test.ts` 覆盖成功透传、404 和网络异常回退。 |
| R4.AC2 | covered | `setupMockRuntime()` 在 demo-offline 使用 `pure` strategy；`api-contract.test.ts` 覆盖关键 API 由 MSW 返回。 |
| R4.AC3 | covered | `src/mocks/runtime/unhandled.ts` 返回 `MOCK_API_NOT_IMPLEMENTED`；`unhandled.test.ts` 和 `api-contract.test.ts` 覆盖确定性 501。 |
| R4.AC4 | covered | `src/mocks/browser.ts`、`src/mocks/server.ts`、`tests/mocks/lifecycle.ts` 共用 handler 入口；API tests 不 mock 请求适配层。 |
| R5.AC1 | covered | `src/mocks/README.md`、runbook 和 retirement checklist 标记旧 `src/demo/**` 与 MCP 为 legacy/paused；首批范围已限于 auth/system/project/version/topology/simulation read。 |
| R5.AC2 | covered | `src/main.ts` 通过 `src/mocks/runtime/app-entry.ts` 启动当前主线；auth/system/project/version/topology handler/store tests 覆盖。 |
| R5.AC3 | covered | 旧分页、导出占位、锁定、拓扑保存等行为落入 `src/mocks/handlers/project.ts` 与 store repositories，而非扩展旧 runtime。 |
| R5.AC4 | covered | `legacy-runtime-retirement-checklist.md` 拆分删除 `src/demo/scenarios/**`、`ScenarioRepository`、generated tests 等后续任务。 |
| R6.AC1 | covered | `src/mocks/data/_shared/constants.ts` 固定 seed/reference time；`factories/_shared/faker.ts` 设置 seed/refDate。 |
| R6.AC2 | covered | `scripts/check-mock-mainline.sh` 扫描 data/factories 中 `Date.now()`、`Math.random()`、未固定 faker relative date；当前通过。 |
| R6.AC3 | covered | session/token 写入 `src/mocks/store/repositories/auth.ts` 和运行时 store，不进入稳定 dataset。 |
| R6.AC4 | covered | `src/mocks/invariants/*.test.ts` 与静态门禁可复现校验；`yarn test:run` 通过。 |
| R7.AC1 | covered | auth/system/project/simulation invariant tests 覆盖外键、唯一键、枚举、权限菜单。 |
| R7.AC2 | covered | `project.test.ts` 和 `simulation.test.ts` 验证 project/version/topology/simulation 引用可追溯。 |
| R7.AC3 | covered | invariant tests 对孤儿引用、重复 key、缺失展示字段会失败；当前完整测试通过。 |
| R7.AC4 | covered | `module-definition-of-done.md` 要求新增业务域同步 invariant；当前首批域均已有 invariant。 |
| R8.AC1 | covered | simulation repository 和 handler 只读查询；`simulation.test.ts` 覆盖展示接口。 |
| R8.AC2 | covered | auth/project/version/topology 写操作进入 Dexie store；`datasource.test.ts`、`project.test.ts` 验证刷新后仍可读。 |
| R8.AC3 | covered | `src/mocks/store/db.ts` 定义独立 `ruoyi-mock-demo`，不复用 `DemoScenarioPackage` 或 `ScenarioRepository`。 |
| R8.AC4 | covered | auth session 等临时数据在 store/auth repository，不替代 project/version/topology 持久写。 |
| R8.AC5 | covered | `reset.ts`、`seed.ts`、metadata、schema/dataset version tests；simulation 控制写操作返回不支持。 |
| R9.AC1 | covered | `yarn lint:check`、`yarn type-check`、`yarn type-check:strict`、`yarn test:run` 均通过；lint 为 0 errors、既有 warnings。 |
| R9.AC2 | covered | `yarn build:prod` 和 `yarn build:demo-offline` 通过；`app-entry.ts` 在 real 模式直接返回，mock setup 懒加载。 |
| R9.AC3 | covered | `scripts/check-mock-mainline.sh` 检查 `@ts-nocheck`、legacy import、OpenAPI 类型绑定、动态数据、文档主线漂移和 demo-offline dist 敏感内容；当前通过。 |
| R9.AC4 | covered | `module-definition-of-done.md` 明确 OpenAPI、typed data、MSW handler、invariant、demo-offline 验收。 |
| R10.AC1 | covered | `src/mocks/README.md`、`docs/specs/README.md`、runbook 均说明当前主线为单套 typed dataset + MSW + Dexie。 |
| R10.AC2 | covered | 文档中 MCP/candidate/promote/active pointer 均标注 legacy/paused 或历史/退场语义；静态门禁覆盖。 |
| R10.AC3 | covered | `docs/demo-offline-runtime-scenario-package-runbook.md` 标为 legacy/paused，不再作为当前主路径。 |
| R10.AC4 | covered | `src/mocks/README.md` 和 `module-definition-of-done.md` 给出放置、类型约束、测试和 demo-offline 命令。 |

## Design

| 条目 | 状态 | 证据 |
| --- | --- | --- |
| 架构 1 OpenAPI artifact | covered | `export_openapi.py` 导出 `shared/openapi.json`；backend check 通过。 |
| 架构 2 前端从 artifact 生成 | covered | `generate-api-types.sh` 默认读取 `shared/openapi.json`；`yarn api:generate` 通过。 |
| 架构 3 单套 dataset/factories | covered | `src/mocks/data/**`、`src/mocks/factories/**` 和 deterministic constants。 |
| 架构 4 handlers 唯一网络层 | covered | `createMockHandlers()` 和 browser/server/lifecycle 共用入口。 |
| 架构 5 demo-offline Dexie store/reset | covered | `src/mocks/store/{db,seed,reset,datasource}.ts`；store tests 通过。 |
| 架构 6 legacy 不扩展 | covered | docs 标记 legacy/paused；`scripts/check-mock-mainline.sh` 防回流。 |
| Runtime setup API | covered | `src/mocks/runtime/setup.ts` 提供 `setupMockRuntime(options)`。 |
| real/fallback/demo-offline 边界 | covered | `app-entry.test.ts`、`setup.test.ts` 验证 real 不启动、fallback/pure strategy。 |
| Data source interface | covered | `src/mocks/store/datasource.ts` 定义 `MockDataSource` 与各域 repository。 |
| Repository 首批能力 | covered | auth/system/project/version/topology/simulation repositories 与 handler tests 覆盖。 |
| 禁止 legacy imports | covered | `no-legacy-import.test.ts` 和 `check-mock-mainline.sh`。 |
| 契约生成命令 | covered | backend check 与 `yarn api:generate` 已执行并通过。 |
| Handler API and fallback semantics | covered | `handlers/index.ts` 和 `with-backend-fallback.test.ts`。 |
| Demo-offline devtools API | covered | `setup.ts` 暴露 `__MOCK_RUNTIME__` 的 mode/version/reset/export；仅 demo-offline 或 test debug。 |
| 未覆盖 API 501 | covered | `runtime/unhandled.ts` 和 tests。 |
| IndexedDB schema | covered | `MockDemoDb` tables/indexes 覆盖 meta、auth、system、project、simulation、sequences。 |
| Meta records and startup/reset | covered | `reset.ts` 写入 schemaVersion/datasetVersion/fingerprint/seededAt/lastResetAt；`seed.ts` 兼容判断。 |
| Deterministic factory context | covered | `factories/_shared/faker.ts` 和 `sequence.ts`，静态门禁防动态漂移。 |
| 安全 1 prod 不启动 MSW/store | covered | `app-entry.ts` real return；`build:prod` 通过。 |
| 安全 2 演示凭据仅本地 | covered | auth session/token 位于 mock store/repository，未进入生产 API。 |
| 安全 3 IndexedDB 不含真实 secret | covered | typed dataset 为演示数据；bundle sensitive scan 通过。 |
| 安全 4 OpenAPI artifact 无 secret | covered | artifact 来自 FastAPI schema；backend check 通过。 |
| 安全 5 MCP 不进入 bundle | covered | dist-demo-offline sensitive scan 已加入 `check-mock-mainline.sh` 并通过。 |
| 安全 6 debug reset/export 非生产 | covered | `setup.ts` 仅 demo-offline 或 test debug 暴露；prod real 不执行 mock setup。 |
| 安全 7 dist-demo-offline sensitive scan | covered | `check-mock-mainline.sh` 扫描 MCP、AI provider、API key/model config 字符串；当前通过。 |
| 契约与类型测试策略 | covered | backend check、`api:generate`、`type-check` 通过。 |
| Dataset invariant 策略 | covered | `src/mocks/invariants/{dataset,auth,system,project,simulation}.test.ts`。 |
| Store 测试策略 | covered | `src/mocks/store/{db,datasource}.test.ts`。 |
| Handler 测试策略 | covered | auth/system/project/simulation/api-contract/fallback tests。 |
| 构建验收策略 | covered | `yarn build:prod`、`yarn build:demo-offline` 通过。 |
| 静态规则策略 | covered | `scripts/check-mock-mainline.sh` 通过。 |

## Tasks

| 任务 | 状态 | 证据 |
| --- | --- | --- |
| Task 1 | covered | OpenAPI export script、artifact、type generation、backend script tests；backend check 和 `api:generate` 通过。 |
| Task 2 | covered | `src/mocks` 目标目录、核心类型、轻量 index、network strategy 类型。 |
| Task 3 | covered | deterministic typed dataset、fixed constants、seeded factories、生成 OpenAPI 类型约束、`satisfies` 类型约束、static gate。 |
| Task 4 | covered | Dexie `MockDemoDb`、首批 tables、seed/reset、metadata、legacy import gate。 |
| Task 5 | covered | `MockDataSource` 与 auth/system/project/version/topology/simulation repositories。 |
| Task 6 | covered | `setupMockRuntime()`、unhandled 501、browser/server shared handlers、fallback tests、`__MOCK_RUNTIME__` debug。 |
| Task 7 | covered | auth/system handlers 读取 data source；auth-system tests 覆盖登录、未登录、token、菜单权限。 |
| Task 8 | covered | project/version/topology handlers 和 store 持久写；project handler tests 覆盖 CRUD/clone/lock、锁定拒绝和 topology 归属规则。 |
| Task 9 | covered | simulation read handlers 和 unsupported writes；simulation tests 覆盖。 |
| Task 10 | covered | `src/main.ts` 和 `runtime/app-entry.ts` 切到当前主线；real/fallback/demo-offline tests 覆盖。 |
| Task 11 | covered | invariant tests、store seed/reset tests、schema/dataset metadata tests、no-legacy-import test。 |
| Task 12 | covered | `api-contract.test.ts`、`fallback.integration.test.ts` 和 handler tests 覆盖真实 API path、fallback、demo-offline 501。 |
| Task 13 | covered | `scripts/check-mock-mainline.sh` 覆盖 TypeScript disable、legacy import、OpenAPI binding、dynamic data、docs drift、dist sensitive scan。 |
| Task 14 | covered | `src/mocks/README.md`、runbook、specs index、module DoD 更新。 |
| Task 15 | covered | backend check、`api:generate`、lint/type/test、prod/demo builds、bundle/static evidence 均通过。 |
| Task 16 | covered | `legacy-runtime-retirement-checklist.md` 完成能力盘点、legacy 标记和后续删除任务拆分。 |

## Verification Evidence

- `ruoyi-fastapi-backend/.venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json --check` -> passed, artifact up to date.
- `yarn api:generate` -> passed, generated from `shared/openapi.json`.
- `yarn lint:check` -> passed with 0 errors and existing warnings.
- `yarn type-check` -> passed.
- `yarn test:run` -> passed: 74 files passed, 1 skipped; 684 tests passed, 1 skipped.
- `yarn build:prod` -> passed.
- `yarn build:demo-offline` -> passed.
- `scripts/check-mock-mainline.sh` and `scripts/check-mock-mainline.sh --require-dist` -> passed.
- `rg -l "ruoyi-mock-demo|__MOCK_RUNTIME__|MOCK_API_NOT_IMPLEMENTED|mock-session|setupMockRuntime" dist-demo-offline` -> matched current mock runtime chunks.
- `rg -l "defense-software-delivery-qm-demo|Generated by Demo Offline Data MCP|activeGeneratedScenarioId" dist dist-demo-offline` -> no matches.

## Remaining Gaps/Risks

无未覆盖 spec 条目。残余风险仅为仓库既有 ESLint warnings 和 Vite chunk-size warnings；两者当前均不导致质量门禁失败。

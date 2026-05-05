# Contract-first 单套 Mock 数据平台实现任务

- [x] 1. 建立确定性 OpenAPI artifact 流程
  - 新增 `ruoyi-fastapi-backend/scripts/export_openapi.py`，从 `server.app.openapi()` 导出稳定排序的 OpenAPI JSON。
  - 新增 `shared/openapi.json` 作为仓库内提交的契约 artifact。
  - 支持 `--check` 模式，比对当前后端契约与 `shared/openapi.json`，漂移时返回非 0。
  - 调整 `scripts/generate-api-types.sh`，默认从 `shared/openapi.json` 生成 `ruoyi-fastapi-frontend/src/api/_generated/**`，live `BACKEND_URL` 只保留为显式本地调试路径。
  - 补充后端脚本测试或轻量 smoke check，验证 artifact 存在且包含 `openapi`、`paths`。
  _需求追溯: R3.AC1, R3.AC2, R9.AC1_

- [x] 2. 搭建 `src/mocks` 目标态目录和核心类型
  - 新增 `runtime/`、`data/`、`store/`、`contracts/`、`invariants/` 目录骨架。
  - 定义 `MockDataset`、`MockNetworkStrategy`、`MockDataSource`、各域 repository interface 和响应契约辅助类型。
  - 将现有 `MockScenario = 'default' | 'pure'` 的业务场景语义降级或移除，保留网络策略语义。
  - 确保 `index.ts` 只做轻量聚合导出，不承载大段记录或生成逻辑。
  _需求追溯: R1.AC1, R1.AC3, R2.AC1, R2.AC4, R4.AC4_

- [x] 3. 构建单套 deterministic typed mock dataset
  - 在 `src/mocks/data/_shared/` 定义固定 `datasetVersion`、`referenceTime`、ID 常量和公共枚举。
  - 按 `auth`、`system`、`project`、`simulation` 域拆分 typed data；工程项目域继续拆为 `projects`、`versions`、`topologies`。
  - 在 `src/mocks/factories/_shared/` 建立 seed/refDate 受控的 faker 和 sequence 工具。
  - 清理稳定 dataset/factory 中未受控的 `Date.now()`、未固定 reference time 的相对日期和未 seed 随机数。
  - 使用 TypeScript `satisfies` 或等价方式让 dataset 编译期受本地契约或生成类型约束。
  _需求追溯: R1.AC1, R1.AC2, R1.AC4, R2.AC2, R2.AC3, R6.AC1, R6.AC2, R6.AC4_

- [x] 4. 实现轻量 Dexie/IndexedDB mock store
  - 新增 `src/mocks/store/db.ts`，定义独立 `MockDemoDb` 和 `ruoyi-mock-demo` 数据库名，不复用旧 `DemoOfflineDb`。
  - 新增 `meta`、`accounts`、`authSessions`、`roles`、`menus`、`dicts`、`departments`、`projects`、`projectVersions`、`topologies`、`simulation*`、`sequences` 等首批表。
  - 新增 `seed.ts`，首次启动时从 typed dataset 导入 store。
  - 新增 `reset.ts`，清空首批表并恢复初始 typed dataset。
  - 记录 `schemaVersion`、`datasetVersion`、`datasetFingerprint`、`seededAt`、`lastResetAt`。
  - 明确禁止 `src/mocks/store/**` import `@/demo/scenarios`、`DemoScenarioPackage`、`ScenarioRepository`。
  _需求追溯: R5.AC2, R8.AC2, R8.AC3, R8.AC5_

- [x] 5. 实现 mock data source 与 repository 层
  - 新增 `src/mocks/store/datasource.ts`，提供 `init()`、`reset()` 和各域 repository。
  - 实现 auth repository，支持账号读取、session/token 保存、logout 清理。
  - 实现 system repository，支持菜单、角色权限、字典、部门树只读查询。
  - 实现 project/version/topology repository，支持列表、详情、CRUD、克隆、锁定、解锁、拓扑保存。
  - 实现 simulation read repository，支持首批只读会话、状态、消息、带宽、告警、事件数据。
  _需求追溯: R1.AC4, R5.AC1, R5.AC2, R7.AC2, R8.AC1, R8.AC2, R8.AC4_

- [x] 6. 统一 MSW runtime 启动入口
  - 新增 `src/mocks/runtime/setup.ts`，以 `setupMockRuntime()` 统一启动 `fallback` 和 `demo-offline`。
  - 新增 `src/mocks/runtime/unhandled.ts`，实现 demo-offline 关键 `/api/**` 未覆盖请求的确定性 `501` 响应。
  - 调整 `src/mocks/index.ts`、`browser.ts`、`server.ts`，让浏览器和 Vitest 共用目标态 handler 注册入口。
  - 保留并测试 `withBackendFallback()` 的真实后端优先、404 回退、网络异常回退语义。
  - 在 debug 条件下暴露 `window.__MOCK_RUNTIME__`，提供 mode、datasetVersion、resetDataset、exportDatasetSnapshot。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4, R8.AC5_

- [x] 7. 迁移 auth 与 system 菜单 handler 到新主线
  - 将登录、验证码、getInfo、logout、csrf/refresh 等 auth handler 改为读取新 data source。
  - 将 getRouters、字典、部门树、角色权限相关只读 handler 改为读取新 data source。
  - 保证 demo-offline 不访问真实后端，fallback 保持真实后端优先。
  - 补充 auth/system handler 测试，覆盖成功、未登录、token 失效和菜单权限引用。
  _需求追溯: R1.AC1, R4.AC1, R4.AC2, R5.AC1, R5.AC2, R7.AC1_

- [x] 8. 迁移 project/version/topology handler 到持久 store
  - 新增或重写 project handler，覆盖列表、详情、新增、编辑、删除、导出占位。
  - 新增或重写 version handler，覆盖列表、详情、克隆、锁定、解锁、删除、导出占位。
  - 新增或重写 topology handler，覆盖按 project/version 读取和保存拓扑。
  - 写操作必须进入 `src/mocks/store`，刷新或重建 data source 后仍可读。
  - 迁移旧 demo service 中仍有价值的分页、过滤、导出占位、锁定规则和拓扑规则，但不复用旧 runtime 架构。
  _需求追溯: R1.AC4, R3.AC4, R5.AC2, R5.AC3, R7.AC2, R8.AC2, R8.AC5_

- [x] 9. 迁移 simulation 只读展示 handler
  - 新增或重写 simulation handler，覆盖首批只读会话状态、消息、带宽、告警、事件接口。
  - 对启动、暂停、停止、恢复、步进、速度调整、故障注入、事件编辑等控制写操作返回明确不支持响应。
  - 确保 simulation 数据引用存在的 project/version，且 UI 只读展示链路可用。
  - 补充 simulation handler 测试，覆盖只读成功和控制写操作不支持。
  _需求追溯: R4.AC2, R4.AC3, R5.AC1, R7.AC2, R8.AC1, R8.AC5_

- [x] 10. 将 demo-offline 入口切换到统一 mock 主线
  - 修改 `src/main.ts` 的 `setupRuntimeMocks()`，demo-offline 不再动态导入 `@/demo/runtime/bootstrap`。
  - 确保 demo-offline 启动 `setupMockRuntime({ mode: 'demo-offline' })`，fallback 启动同一入口的 fallback 策略。
  - 保留 real 模式不启动 MSW、不初始化 mock store。
  - 移除或隔离旧 `__DEMO_RUNTIME__` 对新主线的影响，改用 `__MOCK_RUNTIME__`。
  - 增加 runtime setup 测试，验证 real/fallback/demo-offline 三种模式边界。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R5.AC2, R8.AC3, R9.AC2_

- [x] 11. 建立 dataset invariant 与 store 测试矩阵
  - 新增 auth/system/project/simulation invariant 测试，覆盖外键、唯一键、枚举、权限菜单、必填展示字段。
  - 新增 store seed/reset 测试，覆盖首次 seed、刷新后持久读取、reset 后恢复初始 dataset。
  - 新增 datasetVersion/schemaVersion 测试，覆盖兼容更新、不兼容迁移或 reset 路径。
  - 新增静态测试或脚本，确认 `src/mocks/**` 不 import 旧 scenario runtime。
  _需求追溯: R6.AC3, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R8.AC5, R9.AC1, R9.AC3_

- [x] 12. 强化 handler 合约测试与 fallback 测试
  - 为 auth/system/project/version/topology/simulation handlers 增加 MSW Node 测试。
  - API 合约测试必须通过真实 API 函数或请求兼容层进入 HTTP 链路，不直接 mock 请求适配层。
  - 覆盖 fallback 上游成功透传、上游 404 回退、网络异常回退。
  - 覆盖 demo-offline 关键 `/api/**` 全由 MSW 处理，未覆盖 API 返回确定性 `501`。
  _需求追溯: R3.AC3, R3.AC4, R4.AC1, R4.AC2, R4.AC3, R4.AC4, R9.AC1_

- [x] 13. 增加 mock 主线静态门禁脚本
  - 新增 `scripts/check-mock-mainline.sh`。
  - 检查 `src/mocks/**` 不包含 `@ts-nocheck`。
  - 检查 `src/mocks/**` 不 import `@/demo/scenarios`、`ScenarioRepository`、`DemoScenarioPackage`、`tools/demo-offline-mcp`。
  - 检查稳定 data/factory 中不存在未封装的 `Date.now()`、未受控随机数和未固定 reference time 的相对日期。
  - 检查新文档没有把 MCP、candidate、promote 写成当前主线验收路径。
  _需求追溯: R1.AC3, R6.AC1, R6.AC2, R9.AC3, R10.AC2, R10.AC3_

- [x] 14. 更新文档和 Definition of Done
  - 更新 `src/mocks/README.md`，说明当前主线是单套 typed mock dataset + MSW + Dexie store。
  - 更新 demo-offline 相关 runbook，标记 MCP、多场景、runtime package writer、active/candidate/promote 为 legacy/paused。
  - 在 specs 索引或相关文档中记录本 spec 是当前 demo/mock 主线。
  - 为新业务模块补充 DoD：OpenAPI 契约、typed mock data、MSW handler、invariant、demo-offline 验收。
  _需求追溯: R5.AC4, R9.AC4, R10.AC1, R10.AC2, R10.AC3, R10.AC4_

- [x] 15. 执行质量门禁和构建验收
  - 运行 `cd ruoyi-fastapi-backend && python scripts/export_openapi.py --output ../shared/openapi.json --check`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn api:generate`，确认生成产物与 artifact 同步。
  - 运行 `cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check && yarn test:run`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn build:prod && yarn build:demo-offline`。
  - 记录验收证据：prod 不启动 mock，demo-offline 使用 `src/mocks/store`，核心链路 auth/system/project/version/topology 可持久写，simulation 只读可展示。
  - 验收证据（2026-04-30）：
    - `ruoyi-fastapi-backend/.venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json --check` 通过。
    - `yarn api:generate`、`yarn lint:check`、`yarn type-check`、`yarn type-check:strict`、`yarn test:run`、`bash scripts/check-mock-mainline.sh` 通过；完整测试结果为 74 files passed、1 skipped，687 passed、1 skipped。
    - `yarn build:prod` 和 `yarn build:demo-offline` 通过；构建后 `bash scripts/check-mock-mainline.sh --require-dist` 通过；`src/mocks/runtime/app-entry.ts` 在 `mode === 'real'` 时返回，mock setup chunk 仅按需动态导入。
    - `dist-demo-offline` 中可定位 `setupMockRuntime`、`ruoyi-mock-demo`、`__MOCK_RUNTIME__`、`MOCK_API_NOT_IMPLEMENTED`；`src/mocks/store/db.ts` 定义独立 Dexie store，handler/store 测试覆盖 auth/system/project/version/topology 持久写与 simulation 只读链路。
  _需求追溯: R3.AC1, R3.AC2, R4.AC2, R5.AC2, R9.AC1, R9.AC2_

- [x] 16. 制定旧 scenario runtime 退场清单
  - 盘点仍被 `src/demo/**` 承担的能力和新主线覆盖状态。
  - 对已迁移的 auth/system/project/version/topology 能力移除 demo-offline 对旧 handler/runtime 的依赖。
  - 标记 `tools/demo-offline-mcp/**`、generated scenarios、candidate registry、active pointer 文档为暂停或历史方案。
  - 在核心链路验收稳定后，拆分后续删除旧 `src/demo/scenarios/**`、`ScenarioRepository`、相关 generated tests 的收尾任务。
  - 退场清单见 `docs/specs/contract-first-single-dataset-mock-platform/legacy-runtime-retirement-checklist.md`。
  _需求追溯: R5.AC1, R5.AC2, R5.AC4, R10.AC2, R10.AC3_

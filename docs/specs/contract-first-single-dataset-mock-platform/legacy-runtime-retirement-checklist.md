# 旧 scenario runtime 退场清单

本清单用于记录 legacy/paused `src/demo/**` scenario runtime、`tools/demo-offline-mcp/**`、generated scenarios、candidate/promote 和 active pointer 相关能力的退场边界。当前 demo/mock 主线已经切换为 `src/mocks/**` 单套 typed dataset + MSW + Dexie store；本文件只描述历史能力盘点与后续删除任务，不作为新增能力路径。

## 当前覆盖状态

| 能力域 | legacy/paused 旧路径 | 当前主线覆盖 | 退场状态 |
| --- | --- | --- | --- |
| auth 登录、会话、getInfo、logout | `src/demo/handlers/auth.ts`、`src/demo/services/auth.ts`、`src/demo/repositories/auth.ts`、`src/demo/scenarios/**` | `src/mocks/data/auth/**`、`src/mocks/store/repositories/auth.ts`、`src/mocks/handlers/user.ts`、auth handler 测试 | 已迁移到当前主线；旧路径冻结，后续删除 |
| system 菜单、角色、字典、部门树 | `src/demo/handlers/system.ts`、`src/demo/handlers/system-admin.ts`、`src/demo/services/system*.ts`、`src/demo/repositories/system*.ts` | `src/mocks/data/system/**`、`src/mocks/store/repositories/system.ts`、`src/mocks/handlers/system.ts`、system invariant/handler 测试 | 已迁移核心只读能力；旧路径冻结，后续删除 |
| project 列表、详情、新增、编辑、删除、导出占位 | `src/demo/handlers/project.ts`、`src/demo/services/project.ts`、`src/demo/repositories/project.ts` | `src/mocks/data/project/projects.ts`、`src/mocks/store/repositories/project.ts`、`src/mocks/handlers/project.ts`、project handler/store 测试 | 已迁移到持久 store；旧路径冻结，后续删除 |
| version 列表、详情、克隆、锁定、解锁、删除、导出占位 | `src/demo/repositories/project-version.ts`、旧 project service/handler | `src/mocks/data/project/versions.ts`、`src/mocks/store/repositories/version.ts`、`src/mocks/handlers/project.ts`、project handler/store 测试 | 已迁移到持久 store；旧路径冻结，后续删除 |
| topology 读取与保存 | `src/demo/repositories/topology.ts`、旧 project service/handler | `src/mocks/data/project/topologies.ts`、`src/mocks/store/repositories/topology.ts`、`src/mocks/handlers/project.ts`、topology store/handler 测试 | 已迁移到持久 store；旧路径冻结，后续删除 |
| simulation 只读展示 | `src/demo/handlers/simulation.ts`、`src/demo/services/simulation.ts`、`src/demo/repositories/simulation.ts` | `src/mocks/data/simulation/**`、`src/mocks/store/repositories/simulation.ts`、`src/mocks/handlers/simulation.ts`、simulation invariant/handler 测试 | 已迁移只读展示；控制写操作保持明确不支持 |
| scenario package、generated scenarios、active pointer | `src/demo/scenarios/**`，尤其 `generated/active.ts`、`generated/index.ts` | 当前主线不使用 scenario registry、active pointer 或多场景切换 | legacy/paused；待核心链路稳定后整体删除或归档 |
| runtime bootstrap/devtools | `src/demo/runtime/bootstrap.ts`、`src/demo/runtime/devtools.ts`、`src/demo/runtime/scenario-package-loader.ts` | `src/mocks/runtime/app-entry.ts`、`src/mocks/runtime/setup.ts`、`window.__MOCK_RUNTIME__` | demo-offline 入口已切到当前主线；旧 runtime 冻结 |
| IndexedDB scenario DB | `src/demo/db/**`、旧 repository import 模型 | `src/mocks/store/db.ts` 的 `ruoyi-mock-demo` 独立 Dexie DB | 已替换为轻量 store；旧 DB 不再扩展 |
| DOMC/MCP 生成与发布工具 | `tools/demo-offline-mcp/**` | 当前主线不通过 MCP 生成或激活数据 | legacy/paused；不得被前端 runtime import 或进入验收路径 |

## 已完成的主线切换

- `src/main.ts` 通过 `src/mocks/runtime/app-entry.ts` 启动 runtime；`real` 模式直接返回，不加载 `setupMockRuntime()`。
- `demo-offline` 和 `fallback` 共用 `src/mocks/runtime/setup.ts`、`src/mocks/handlers/**` 和 `src/mocks/store/**`。
- `src/mocks/store/db.ts` 使用独立数据库名 `ruoyi-mock-demo`，并记录 `schemaVersion`、`datasetVersion`、`datasetFingerprint`、`seededAt`、`lastResetAt` 等 meta。
- `scripts/check-mock-mainline.sh` 阻止 `src/mocks/**` 引入 legacy scenario runtime、`@ts-nocheck`、未受控动态时间/随机值，以及文档把 legacy/paused MCP、candidate/promote 当作当前主线。
- `src/mocks/README.md`、`docs/specs/README.md`、`docs/demo-offline-runtime-scenario-package-runbook.md` 已标注 current mainline 与 legacy/paused 边界。

## 删除前置条件

删除旧路径前必须同时满足：

- `yarn lint:check`、`yarn type-check`、`yarn test:run`、`yarn build:prod`、`yarn build:demo-offline` 均通过。
- auth、system、project、version、topology 的 handler/store 测试覆盖成功、失败、持久写和 reset 关键路径。
- simulation 只读 handler 测试覆盖首批展示接口，控制写操作返回明确不支持。
- `scripts/check-mock-mainline.sh` 通过，且 `src/mocks/**` 无 legacy scenario runtime import。
- demo-offline 静态构建中能定位到当前主线的 `setupMockRuntime`、`ruoyi-mock-demo`、`__MOCK_RUNTIME__` 或 `MOCK_API_NOT_IMPLEMENTED`。
- prod 构建在 `real` 模式不执行 mock runtime；允许存在懒加载 mock chunk，但入口必须在 `mode === 'real'` 时返回。

## 后续删除任务拆分

1. 删除或归档 `src/demo/scenarios/**` 和 generated scenario tests；移除 legacy/paused `generatedScenarioRegistry`、active pointer 相关导出。
2. 删除 `src/demo/repositories/scenario.ts`、`ScenarioRepository` 测试和 scenario package loader。
3. 删除 `src/demo/runtime/bootstrap.ts`、`src/demo/runtime/devtools.ts`、`src/demo/runtime/scenario-package-loader.ts`，保留 `src/demo/runtime/mode.ts` 直到运行模式解析迁移到 `src/mocks/runtime/mode.ts` 或等价位置。
4. 删除已由当前主线覆盖的旧 `src/demo/handlers/**`、`src/demo/services/**`、`src/demo/repositories/{auth,system,system-admin,project,project-version,topology,simulation}.ts`。
5. 删除旧 `src/demo/db/**` 和 DOMC import 相关代码，确认没有页面或测试仍依赖旧 IndexedDB schema。
6. 将 `tools/demo-offline-mcp/**`、candidate/promote、runtime package writer 和 offline-static release store 文档迁到历史归档，或在仓库治理层决定是否整体移除。
7. 收尾更新 `eslint.config.js`：旧 `src/demo/**` 删除后移除 legacy ignore。
8. 收尾更新文档：删除 legacy/paused 入口引用，只保留一页历史说明和当前 `src/mocks/**` 新增模块 DoD。

## 暂不删除的残留

- `src/demo/runtime/mode.ts` 仍被 `src/main.ts` 和 `src/mocks/runtime/app-entry.ts` 用于解析 `real`、`fallback`、`demo-offline`，删除前需要迁移运行模式类型与解析函数。
- `src/demo/**` 目前被 ESLint legacy ignore 覆盖；在正式删除或迁移前，不应继续在旧路径上修复格式来制造额外 churn。
- `tools/demo-offline-mcp/**` 包含历史测试、dist 和 node_modules；本规格只冻结和标记退场，不在当前任务中删除。

# Mock Runtime Legacy 退场验收记录

验收日期: 2026-05-01

## 退场结论

当前前端 mock runtime 已收敛到 `ruoyi-fastapi-frontend/src/mocks/**` 单主线。旧 `src/demo/**` runtime、scenario package、release pointer、candidate/promote、旧环境变量和旧 demo-offline contract/scenario 构建产物不再属于当前运行面。

## 删除清单

已从当前运行面删除或确认不存在:

- `ruoyi-fastapi-frontend/src/demo/**`
- `ruoyi-fastapi-frontend/vite/plugins/demo-offline-contract.ts`
- `docs/demo-offline-runtime-scenario-package-runbook.md`
- `dist-demo-offline/demo-contract/**`
- `dist-demo-offline/demo-scenarios/**`

旧源码不转存到 `archive/**`、`docs/archive/**` 或其他源码归档目录；历史背景只通过历史 specs、`docs/raw/**` 和 git history 考古。

## 迁移清单

当前运行面已迁到:

- `src/mocks/runtime/mode.ts`: 解析 `real | fallback | demo-offline`，默认 `real`，通过显式 allowlist 只读取 `VITE_APP_RUNTIME_MODE`、`VITE_APP_BASE_API`、`VITE_DEMO_RUNTIME_DEBUG`，不把完整 `import.meta.env` 传入 runtime config。
- `src/mocks/runtime/app-entry.ts`: `real` 不加载 mock setup；`fallback` 和 `demo-offline` 统一动态进入 `setupMockRuntime()`；启动前清理旧 `__DEMO_RUNTIME__` 和当前 `__MOCK_RUNTIME__`。
- `src/mocks/runtime/setup.ts`: `fallback -> fallback`、`demo-offline -> pure`，统一初始化 Dexie data source、MSW handlers 和受限 `__MOCK_RUNTIME__` debug API。
- `src/mocks/runtime/unhandled.ts`: demo-offline 未覆盖关键 `/api/**` 返回确定性 `501 MOCK_API_NOT_IMPLEMENTED` 和 mock debug headers。
- `src/main.ts`、`src/mocks/index.ts`、`src/router/history.ts`、`src/views/project/topo.vue`、`src/views/monitor/druid/index.vue`: 从当前 mock runtime mode 模块读取运行模式。
- `vite.config.ts`、`vite/plugins/index.ts`、`package.json`: demo-offline 构建不注册旧 scenario/contract 插件；`dev:fallback` 只设置 `VITE_APP_RUNTIME_MODE=fallback`。
- `.env.demo-offline`、`.env.development`、`.env.production`: 已移除旧 `VITE_ENABLE_MOCK`、`VITE_DEMO_SCENARIO_ID` 以及 MCP promote / generated active scenario 说明。

## 保留边界

保留页面壳:

- `ruoyi-fastapi-frontend/src/views/demo/offline-module.vue`

该页面壳只用于离线导航占位，不依赖旧 runtime、旧环境变量、旧 scenario package 或旧构建产物。

## 验证结果

已运行并通过:

- `cd ruoyi-fastapi-frontend && yarn lint:check`
  - 结果: 通过，退出码 0。
  - 备注: 当前仓库仍有既有 ESLint warnings，例如 `no-explicit-any`、未使用变量和 chunk 相关无关提示；本命令未产生 blocking error。
- `cd ruoyi-fastapi-frontend && yarn type-check`
  - 结果: 通过。
- `cd ruoyi-fastapi-frontend && yarn test:run src/mocks`
  - 结果: 通过，23 个测试文件，61 个测试。
- `cd ruoyi-fastapi-frontend && yarn build:prod`
  - 结果: 通过。
  - 备注: Vite 输出 chunk size 和 `src/mocks/store/reset.ts` 动静态 import 混用提示，不影响构建退出码。
- `cd ruoyi-fastapi-frontend && yarn build:demo-offline`
  - 结果: 通过，生成 `dist-demo-offline/index.html`。
  - 备注: Vite 输出同类构建提示，不影响构建退出码。
- `scripts/check-mock-mainline.sh`
  - 结果: 通过。
  - 备注: 当前脚本同时扫描前端 `.env*`、当前运行面、`dist-demo-offline` 和已存在的 `dist`，阻断旧 mock env、旧 scenario/MCP 标识和旧构建产物回流。
- `scripts/check-mock-mainline.sh --require-dist`
  - 结果: 通过。
- legacy pattern 搜索:
  - 命令: `rg -n "@/demo|src/demo|VITE_ENABLE_MOCK|VITE_DEMO_SCENARIO_ID|VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS|demo-offline-contract|demo-contract|demo-scenarios|DemoScenarioPackage|ScenarioRepository|release-store" ruoyi-fastapi-frontend/src ruoyi-fastapi-frontend/tests ruoyi-fastapi-frontend/vite ruoyi-fastapi-frontend/vite.config.ts ruoyi-fastapi-frontend/package.json --glob '!**/no-legacy-import.test.ts' --glob '!tests/reports/**'`
  - 结果: 无命中。
- env / dist 旧标识搜索:
  - 命令: `rg --no-ignore -n -o 'VITE_ENABLE_MOCK|VITE_DEMO_SCENARIO_ID|VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS|demo-contract|demo-scenarios|demo-offline-contract|tools/demo-offline-mcp|DemoScenarioPackage|ScenarioRepository|release-store|generatedScenarioRegistry|candidateScenarioRegistry|activeGeneratedScenarioId' ruoyi-fastapi-frontend/.env* ruoyi-fastapi-frontend/dist ruoyi-fastapi-frontend/dist-demo-offline`
  - 结果: 无命中。
- `dist-demo-offline` 旧 artifact 搜索:
  - 结果: 无 `demo-contract/**` 或 `demo-scenarios/**`。

未运行命令: 无。

## 残余风险与后续事项

本 spec 不处理以下下一阶段事项:

- contract coverage matrix。
- overlay harness。
- demo-offline E2E。
- 更细粒度的 bundle chunk 拆分和构建 warning 治理。
- 仓库既有 ESLint warnings 的全局清理。

后续新增 mock 能力必须进入 `ruoyi-fastapi-frontend/src/mocks/**`，不得恢复旧 `src/demo/**`、scenario runtime package、candidate/promote、active pointer 或旧 MCP 工具链主线。

# Mock Runtime Legacy Inventory

生成日期: 2026-05-01

## 扫描范围

Task 1 的当前运行面扫描范围:

- `ruoyi-fastapi-frontend/src`
- `ruoyi-fastapi-frontend/tests`
- `ruoyi-fastapi-frontend/vite`
- `ruoyi-fastapi-frontend/vite.config.ts`
- `ruoyi-fastapi-frontend/package.json`

扫描 legacy 标识:

- 旧路径: `@/demo`, `src/demo`, `../demo`
- 旧环境变量: `VITE_ENABLE_MOCK`, `VITE_DEMO_SCENARIO_ID`, `VITE_DEMO_ALLOW_CANDIDATE_SCENARIOS`
- 旧 runtime/debug: `__DEMO_RUNTIME__`
- 旧 artifact/plugin: `demo-offline-contract`, `demo-contract`, `demo-scenarios`
- 旧 scenario 类型和 registry: `DemoScenarioPackage`, `ScenarioRepository`, `generatedScenarioRegistry`, `candidateScenarioRegistry`, `activeGeneratedScenarioId`, `release-store`
- 旧 MCP 工具链: `tools/demo-offline-mcp`

当前运行面扫描结果:

- `ruoyi-fastapi-frontend/src/demo` 当前不存在。
- `ruoyi-fastapi-frontend/vite/plugins/demo-offline-contract.ts` 当前不存在。
- `ruoyi-fastapi-frontend/dist-demo-offline` 当前不存在 `demo-contract/**` 或 `demo-scenarios/**`。
- legacy 标识只命中专门门禁测试和旧 devtools 清理逻辑:
  - `ruoyi-fastapi-frontend/src/mocks/invariants/no-legacy-import.test.ts`
  - `ruoyi-fastapi-frontend/src/mocks/runtime/app-entry.ts`
  - `ruoyi-fastapi-frontend/src/mocks/runtime/app-entry.test.ts`

## 必须硬删除的运行面

以下旧运行面不得保留、移动到 `archive/**`、`docs/archive/**` 或其他仓库内源码归档目录:

- `ruoyi-fastapi-frontend/src/demo/**`
  - `db/**`
  - `domc/**`
  - `handlers/**`
  - `realtime/**`
  - `repositories/**`
  - `runtime/**`
  - `scenarios/**`
  - `services/**`
- `ruoyi-fastapi-frontend/vite/plugins/demo-offline-contract.ts`
- `docs/demo-offline-runtime-scenario-package-runbook.md`
- demo-offline 构建产物中的旧发布目录:
  - `dist-demo-offline/demo-contract/**`
  - `dist-demo-offline/demo-scenarios/**`

后续新增 mock 能力必须进入 `ruoyi-fastapi-frontend/src/mocks/**` 单主线，不得恢复旧 scenario runtime、candidate/promote、active pointer 或 runtime package writer。

## 可保留边界

允许保留不依赖旧 runtime/scenario 的 demo-offline 页面壳:

- `ruoyi-fastapi-frontend/src/views/demo/offline-module.vue`

该页面只依赖 Vue Router 与 Element Plus 展示离线占位导航，不导入旧 `src/demo/**`、旧环境变量、旧 scenario artifact 或旧 MCP 工具链。

历史 spec、`docs/raw/**` 和 git history 可保留旧方案背景，但不得作为当前验收路径或运行面依赖。

## Debug API 边界

旧 `window.__DEMO_RUNTIME__` 只能作为清理目标出现，不能作为当前 debug API、测试入口或文档入口保留。

当前允许位置:

- `ruoyi-fastapi-frontend/src/mocks/runtime/app-entry.ts`: 启动前删除旧 `__DEMO_RUNTIME__` 和当前 `__MOCK_RUNTIME__`。
- `ruoyi-fastapi-frontend/src/mocks/runtime/app-entry.test.ts`: 验证旧 devtools 会被清理。

当前公开 debug API 只能是 `window.__MOCK_RUNTIME__` 或后续明确命名的 mock 主线 API。

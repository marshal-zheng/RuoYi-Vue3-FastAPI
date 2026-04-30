# Demo Offline DOMC 模块接入 Definition of Done

## 目标

新增业务模块不能只靠 prompt 或最终 JSON 样例进入 demo-offline 生成链路。模块必须先证明它的页面、接口、IndexedDB 数据、UI journey、质量门禁和 MCP adapter 都具备可审计事实源。

## `generatable` 模块

模块标记为 `generatable` 前必须同时提交：

- DOMC module contract：`ruoyi-fastapi-frontend/src/demo/domc/modules/<module>.domc.ts`
- scenario slice/schema：`DemoScenarioPackage` schema 与 sourcePath 数组结构
- IndexedDB mapping：`DEMO_INDEXED_DB_MAPPING.tables[]`
- repository/service 读取链路：页面数据只从 IndexedDB、service 或 MSW handler 读取
- MSW handler coverage：handler source、apiPrefix、coveredRoutes、unsupportedBehavior
- UI journey：入口、列表字段、详情支撑数据、关键操作 demo 行为、空态和错误态
- invariants：主键、引用、minItems、状态机和最低可演示链路
- diversity rules：主记录字段、关键维度、重复阈值、模板相似度阈值和例外说明
- generator adapter：`tools/demo-offline-mcp/src/adapters/**` 中的 MCP 侧实现
- 测试证据：DOMC schema/fingerprint、adapter registry、planner blocker、import dry-run、release provenance
- 维护信息：owner、DOMC 维护路径、adapter id/version、回归命令

## `copyOnly` 模块

模块只保留默认数据时可以标记为 `copyOnly`，但必须声明：

- 复制来源：`demo-contract/default-scenario.json` 或 bundle-default v2
- copyOnly sourcePaths 和每个 sourcePath 的 minItems
- handler coverage 和 UI navigation 支撑关系
- 不允许语义生成的原因
- 复制记录不能被 adapter 改写

当前 `auth` 与 `system` 属于 `copyOnly`。认证、权限、菜单、用户、字典、部门、岗位等运行时支撑记录继续从默认场景复制。

## `unsupported` / `blocked` 模块

模块缺 DOMC、IndexedDB mapping、handler、UI journey、invariants 或 adapter 任一关键能力时，MCP 必须返回结构化 blocker：

- `path`
- `code`
- `severity`
- `actual`
- `expected`
- `fixHint`
- `gate`
- `missingArtifacts`
- `nextActions`

不得使用 generic fallback adapter、低置信模板数据或 warning-only 方式继续生成该模块。

## 明确非目标

本 spec 不实现完整 Scenario Graph、Generator Recipes、真实后端 seed target、生产数据生成、浏览器端 AI/adapter 执行，也不改变 v2 pointer、manifest、slice 和 fallback 文件格式语义。若需求需要这些能力，应进入后续 `demo-offline-scenario-graph-and-recipes` 或新的 spec。

## 回归命令

```bash
cd tools/demo-offline-mcp && npm test -- --run
cd ruoyi-fastapi-frontend && yarn test:run src/demo/runtime/scenario-package-loader.test.ts src/demo/scenarios/contract.test.ts src/demo/repositories/scenario.test.ts src/demo/runtime/devtools.test.ts
cd ruoyi-fastapi-frontend && yarn type-check
```

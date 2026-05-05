# MSW Mock Platform 下一阶段 Spec 上下文记录

日期：2026-05-01

状态：原始记录（用于后续分别产出正式 specs）

目的：沉淀本轮关于现有 MSW mock 流程、架构成熟度、长期优化方向和 spec 拆分边界的关键上下文。本文不是正式 spec，不定义最终任务清单；后续正式 specs 应基于本文拆分 requirements / design / tasks。

## 1. 当前结论

现有 mock 主线已经明显高于普通项目里的零散假数据，接近成熟团队的 contract-first mock runtime：

```text
FastAPI OpenAPI artifact
  -> generated API types
  -> src/mocks/data/** single typed dataset
  -> src/mocks/store/** Dexie persistent store
  -> src/mocks/handlers/** MSW network virtualization
  -> Vitest/API contract/invariant/CI gates
```

整体成熟度评估约为 7.5/10 到 8/10。主要差距不在 MSW 基础用法，而在长期平台治理：

- legacy `src/demo/**` / scenario package / active pointer 还没有完全退场。
- OpenAPI 约束已经接入类型层，但还没有形成完整 endpoint coverage matrix 和运行时响应 schema validation。
- error scenario 已有基础，但还没有发展成可被 Vitest、页面预览、Storybook/Playwright 复用的轻量 overlay 体系。
- demo-offline 构建可以通过，但还缺少 build 后 preview + E2E smoke 来证明真实演示链路稳定。

长期收益最大的方案是：

```text
彻底清理双主线
  -> 建立机器可执行契约覆盖门禁
  -> 增加轻量 scenario overlay
  -> 增加 demo-offline 页面级 E2E 验收
```

不要恢复旧 MCP / 多场景 runtime package，也不要直接引入 Prism/Microcks/WireMock 替代现有 MSW + Dexie。当前项目更需要“前端业务状态 + 本地持久写 + API 漂移防护”的组合能力。

## 2. 本地证据

### 2.1 当前主线已成立

关键文件：

- `ruoyi-fastapi-frontend/src/mocks/README.md`
  - 明确当前主线是 `FastAPI OpenAPI artifact -> generated API types -> typed dataset -> Dexie store -> MSW handlers`。
  - 明确 `real` 不启动 MSW，`fallback` 真实后端优先并回退 mock，`demo-offline` 纯 MSW。
  - 明确 legacy/paused：MCP、多场景 runtime package、runtime package writer、active pointer、candidate/promote、旧 `src/demo/**` scenario runtime 不再是当前主线验收路径。
- `ruoyi-fastapi-frontend/src/mocks/runtime/setup.ts`
  - `setupMockRuntime()` 统一启动 fallback 与 demo-offline。
  - demo-offline 下 `onMissingCapability: 'error'`，未覆盖关键 API 走 deterministic 501。
  - debug 条件下暴露 `window.__MOCK_RUNTIME__`，支持 mode、datasetVersion、resetDataset、exportDatasetSnapshot。
- `ruoyi-fastapi-frontend/src/mocks/handlers/index.ts`
  - 统一聚合 system/user/project/simulation/test/monitor handlers。
  - 支持 `onMissingCapability: 'error'` 注入 unhandled API handler。
- `ruoyi-fastapi-frontend/src/mocks/utils/with-backend-fallback.ts`
  - `pure` 直接 mock。
  - `fallback` 先 `fetch(bypass(request))` 访问真实后端，非 404 透传，404 或网络错误回退 mock。
- `ruoyi-fastapi-frontend/src/mocks/store/**`
  - 独立 Dexie DB：`ruoyi-mock-demo`。
  - `meta` 记录 schemaVersion、datasetVersion、datasetFingerprint、seededAt、lastResetAt。
  - dataset 兼容升级时记录 pending upgrade，不直接覆盖用户 demo edits。
- `ruoyi-fastapi-frontend/src/mocks/contracts/openapi.ts`
  - 从 `@/api/_generated/types.gen` 派生 mock contract 类型。
- `ruoyi-fastapi-frontend/tests/mocks/**`
  - Vitest 全局 MSW Node server。
  - API 合约测试通过真实 API 函数或请求兼容层，不直接 mock `@/utils/request`。

### 2.2 质量门禁已有效

本轮实际验证结果：

```bash
scripts/check-mock-mainline.sh
# passed

cd ruoyi-fastapi-frontend
yarn test:run src/mocks
# 21 files passed, 53 tests passed

yarn test:run tests/mocks src/api/login.test.ts tests/unit/api
# 7 files passed, 29 tests passed

yarn type-check:strict
# passed

cd ../ruoyi-fastapi-backend
.venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json --check
# OpenAPI artifact is up to date
```

CI 已包含关键门禁：

- `.gitlab-ci.yml`
  - `openapi-artifact-drift-check`
  - `frontend-quality-gates`
  - `yarn api:generate`
  - generated client drift check
  - `yarn type-check:strict`
  - `scripts/check-mock-mainline.sh`
  - `yarn build:demo-offline`
  - `scripts/check-mock-mainline.sh --require-dist`
- `.github/workflows/ci.yml`
  - 同类手动 workflow 检查，用于 GitHub 侧辅助。

### 2.3 最大架构债

虽然文档把旧 runtime 标为 legacy/paused，但仍有代码残留：

- `ruoyi-fastapi-frontend/src/main.ts`
  - 仍从 `@/demo/runtime/mode` 导入 `resolveRuntimeConfig` 和 `RuntimeConfig`。
- `ruoyi-fastapi-frontend/src/mocks/index.ts`
  - 仍从 `@/demo/runtime/mode` 读取 legacy mock mode。
- `ruoyi-fastapi-frontend/vite/plugins/demo-offline-contract.ts`
  - build/dev server 仍会生成或提供 `demo-contract/`、`demo-scenarios/`、release pointer 相关资产。
  - 仍 import `../../src/demo/scenarios/default` 和 `../../src/demo/scenarios/release-store`。

这会制造两个长期问题：

1. 新人或 AI Agent 容易误判当前主线，继续扩展旧 `src/demo/**` / scenario package。
2. 后续契约覆盖矩阵、bundle scan、demo-offline E2E 会被旧产物干扰，导致“主线已切换”的口径和构建行为不一致。

## 3. 长期方案原则

### 3.1 应坚持的方向

- MSW 继续作为唯一网络虚拟化层。
- OpenAPI artifact 继续作为 API 事实源。
- `src/mocks/data/**` 继续作为单套 typed dataset。
- Dexie store 继续只服务 demo-offline/fallback mock，不复用旧 scenario DB。
- handler 复用必须覆盖 dev fallback、demo-offline、Vitest、未来 E2E/Storybook。
- 错误、空态、慢接口、权限失败等状态应通过 lightweight overlay 表达，而不是恢复多场景 runtime package。

### 3.2 明确非目标

- 不恢复 MCP、candidate/promote、active pointer 作为当前主线。
- 不把 AI 生成的 runtime scenario package 作为下一阶段主路径。
- 不直接用 Prism/Microcks/WireMock 替代当前 MSW + Dexie。
- 不把每个业务状态都复制一套 dataset。
- 不把页面测试变成 mock 行为测试；页面和 API 测试必须继续走真实 API 函数或真实请求链路。

## 4. 推荐 Spec 拆分

不建议用一个巨大 spec 覆盖全部下一阶段。一个 spec 可以描述方向，但不适合同时承载 legacy 退场、契约覆盖、scenario overlay 和 E2E 验收。

推荐拆成 1 个总纲上下文 + 4 个正式 specs。

### 4.1 Spec 1: `mock-runtime-legacy-retirement`

优先级：P0，最先做。

目标：彻底清掉旧 demo/scenario/runtime package 主线残留，让当前 `src/mocks/**` 成为唯一 demo/mock runtime。

核心范围：

- 将 `resolveRuntimeConfig`、`RuntimeConfig`、runtime mode normalization 从 `src/demo/runtime/mode.ts` 迁到 `src/mocks/runtime/mode.ts` 或 shared runtime 目录。
- 更新 `src/main.ts`、`src/mocks/index.ts`、`src/mocks/runtime/app-entry.ts` 引用，不再依赖 `@/demo/runtime/mode`。
- 处理 `vite/plugins/demo-offline-contract.ts`：
  - 若当前主线不需要 `demo-contract/` 和 `demo-scenarios/`，删除插件或禁用 demo-offline 构建输出。
  - 若暂时保留历史兼容，必须改名/标注 legacy，并确保 CI 不把它当主线验收。
- 增加 static gate：
  - runtime 主线不得 import `@/demo/scenarios`、`release-store`、`DemoScenarioPackage`、`ScenarioRepository`。
  - `dist-demo-offline` 不应包含 active pointer / scenario package 主线产物，除非明确标为 legacy artifact。
- 收尾更新 README/runbook/spec 索引。

验收锚点：

- `rg -n "@/demo/runtime/mode|@/demo/scenarios|release-store|DemoScenarioPackage|ScenarioRepository" ruoyi-fastapi-frontend/src/mocks ruoyi-fastapi-frontend/src/main.ts ruoyi-fastapi-frontend/vite`
  - 主线代码无命中，或命中只在明确 legacy 归档路径。
- `yarn build:prod`
- `yarn build:demo-offline`
- `scripts/check-mock-mainline.sh --require-dist`
- runtime tests 覆盖 `real` 不启动 mock、`fallback`/`demo-offline` 走统一 runtime。

长期收益：

```text
消除双主线判断成本，是后续所有治理工作的前置条件。
```

### 4.2 Spec 2: `mock-contract-coverage-and-schema-gates`

优先级：P0，紧随 legacy retirement。

目标：把 OpenAPI 契约从“生成类型”升级为“可执行覆盖矩阵 + 响应 schema 校验 + CI 漂移门禁”。

核心范围：

- 新增 OpenAPI path coverage matrix 脚本。
- 对每个 OpenAPI endpoint 分类：
  - `mock-handled`
  - `real-only`
  - `unsupported-501`
  - `legacy-local-contract`
  - `missing`
- 从 MSW handlers 中提取或显式注册 endpoint metadata，避免只靠 regex 猜测。
- CI 规则：
  - 新增 OpenAPI path 必须被分类。
  - `missing` 在 demo-offline critical API 中失败。
  - `legacy-local-contract` 必须有迁移说明。
- 对核心 handler 响应增加 schema validation：
  - 可从 OpenAPI generated schema 或轻量 adapter schema 派生。
  - 优先覆盖 auth/system/project/version/topology/simulation 主链路。
- 输出可读报告，便于 PR reviewer 判断新增接口是否接入 mock 主线。

验收锚点：

- coverage report 能列出每个 API endpoint 的 owner、mock status、handler tag、测试文件。
- 改动 `shared/openapi.json` 新增路径但不分类时，门禁失败。
- handler 返回结构与 OpenAPI response schema 不兼容时，测试失败。
- `contracts/local.ts` 中历史契约必须出现在 coverage report 中，并标注迁移目标。

长期收益：

```text
把 API/mock 漂移从人工经验问题变成机器可发现问题。
这是 mock 平台从“可维护”走向“可治理”的关键步骤。
```

### 4.3 Spec 3: `mock-scenario-overlays-and-page-state-harness`

优先级：P1。

目标：在不恢复旧多场景 runtime 的前提下，支持常见页面状态和故障状态。

核心范围：

- 保留单套 dataset。
- 新增 lightweight overlay system，只覆盖 handler behavior，不复制整套业务数据。
- 内置 overlays：
  - `empty`
  - `slow`
  - `error-5xx`
  - `error-429`
  - `timeout`
  - `network-error`
  - `permission-denied`
  - `large-list`
- 支持局部 endpoint overlay，例如只让 `/api/project/list` 为空态。
- 提供统一选择机制：
  - test helper
  - URL query 或 localStorage dev-only switch
  - `window.__MOCK_RUNTIME__` debug API
- 为后续 Storybook/Playwright 预留同一 handler 注册入口。

验收锚点：

- 不新增多套 dataset。
- overlay 不 import legacy scenario runtime。
- Vitest 能在同一个测试文件中切换 endpoint overlay。
- 页面或 API 测试能覆盖 empty/slow/error/permission-denied。

长期收益：

```text
提升 UI 状态覆盖和研发体验，同时避免旧多场景架构复杂度回潮。
```

### 4.4 Spec 4: `demo-offline-e2e-validation`

优先级：P1，可在 Spec 2 后并行或随后做。

目标：证明 build 后 demo-offline 真实可用，而不仅是 handler/unit tests 通过。

核心范围：

- `yarn build:demo-offline`
- `yarn preview:demo-offline`
- Playwright 或 Vitest browser smoke：
  - 打开 demo-offline preview。
  - 登录。
  - 加载菜单。
  - 查看项目列表。
  - 新增/编辑项目。
  - 克隆/锁定版本。
  - 保存拓扑。
  - 查看 simulation 只读页。
  - reset dataset 后恢复初始状态。
- 网络断言：
  - demo-offline 不访问真实后端。
  - 未覆盖关键 `/api/**` 返回 deterministic 501。
  - mock 响应带 `X-Mock-Response` / `X-Mock-Handler` 等 debug header。
- CI 可以先作为 nightly/manual，再提升为 MR gate。

验收锚点：

- e2e smoke 可在本地和 CI 稳定运行。
- 失败报告能定位到 handler tag 或 missing endpoint。
- preview 构建后的 IndexedDB store 可 reset、可持久写。

长期收益：

```text
从“测试里 mock 对”升级为“离线演示真的对”。
这是 demo-offline 作为交付能力的最终闭环。
```

## 5. 推荐实施顺序

```text
1. mock-runtime-legacy-retirement
2. mock-contract-coverage-and-schema-gates
3. demo-offline-e2e-validation
4. mock-scenario-overlays-and-page-state-harness
```

理由：

1. 不先退场 legacy，coverage matrix 和 E2E 会被旧产物干扰。
2. 不先做 coverage/schema gate，后续新增 overlay 和 E2E 只能发现问题，不能从源头防漂移。
3. E2E 可以尽早证明 demo-offline 主链路，降低后续清理风险。
4. overlay 是体验增强，不应先于架构收口和契约治理。

如果只能先写一个正式 spec，优先写：

```text
docs/specs/mock-runtime-legacy-retirement/
```

如果能连续写两个，第二个写：

```text
docs/specs/mock-contract-coverage-and-schema-gates/
```

## 6. 新窗口生成 Spec 时的建议提示

可直接给新窗口如下指令：

```text
请基于 docs/raw/2026-05-01-msw-mock-platform-next-spec-context.md，
为 mock-runtime-legacy-retirement 生成正式 spec 三件套：
requirements.md、design.md、tasks.md。

目标是彻底清理旧 src/demo runtime/scenario package 在当前 mock 主线中的残留，
让 src/mocks/** 成为唯一 demo/mock runtime。

请先读现有 docs/specs/contract-first-single-dataset-mock-platform/**、
src/mocks/**、src/main.ts、vite/plugins/demo-offline-contract.ts、
scripts/check-mock-mainline.sh、.gitlab-ci.yml，
然后生成中文 requirements.md，并等待确认。
```

第二个 spec 可用：

```text
请基于 docs/raw/2026-05-01-msw-mock-platform-next-spec-context.md，
为 mock-contract-coverage-and-schema-gates 生成正式 spec 三件套。

目标是建立 OpenAPI endpoint coverage matrix、handler metadata、
核心 mock response schema validation 和 CI drift gate。

请先读 shared/openapi.json、src/mocks/handlers/**、src/mocks/contracts/**、
scripts/generate-api-types.sh、backend export_openapi.py、CI 配置，
然后生成中文 requirements.md，并等待确认。
```

## 7. 风险与取舍

### 7.1 删除旧插件的风险

`vite/plugins/demo-offline-contract.ts` 可能仍被某些历史文档、测试或人工流程依赖。正式 spec 不应直接假设无用，应先做 usage scan 和 dist 产物确认。

推荐做法：

- 先把插件产物和 import 关系纳入 inventory。
- 若无运行时消费，删除或禁用。
- 若存在历史消费，迁移到 `docs/archive` 或明确 legacy build flag，不进入默认 `build:demo-offline`。

### 7.2 Coverage matrix 的复杂度风险

从 MSW handler 自动解析 path 可能不稳定。更稳的做法是建立显式 metadata registry，例如：

```ts
{
  method: 'GET',
  path: '/project/list',
  tag: 'project:list',
  status: 'mock-handled',
  owner: 'project',
  contract: 'openapi',
}
```

handler 注册可以从 metadata 旁路生成，或者至少让测试校验 metadata 与 handler tag 一致。

### 7.3 Schema validation 的落地风险

OpenAPI 生成的 TS type 不等于 runtime schema。可以分阶段：

1. P0 先做 endpoint coverage matrix。
2. P0/P1 对核心接口使用轻量 runtime schema 或 generated JSON schema。
3. P1 再扩大覆盖。

不要一开始要求所有历史接口 100% runtime schema validation，否则 spec 容易过大。

### 7.4 Overlay 的边界风险

Overlay 必须是 handler behavior layer，不是第二套 dataset。否则会回到旧 scenario 分叉问题。

建议约束：

- overlay 不允许定义完整业务实体副本。
- overlay 只能 patch response、delay、status、network behavior、page slicing 或权限状态。
- 需要业务数据变化时，优先回到 single typed dataset 或 repository seed。

## 8. 后续 Specs 与现有 Spec 的关系

现有 spec：

```text
docs/specs/contract-first-single-dataset-mock-platform/
```

已完成第一阶段：建立 contract-first 单套 mock 主线。

下一阶段 specs 不应重写它，而应作为增量：

- `mock-runtime-legacy-retirement`：收尾清债。
- `mock-contract-coverage-and-schema-gates`：治理升级。
- `mock-scenario-overlays-and-page-state-harness`：状态覆盖与开发体验。
- `demo-offline-e2e-validation`：演示验收闭环。

这些 specs 的共同前提是：

```text
src/mocks/** 是当前主线；
src/demo/** 是 legacy/paused；
OpenAPI artifact 是 API 事实源；
MSW 是唯一网络虚拟化层；
Dexie store 是 demo-offline 持久写边界。
```

# Mock 契约覆盖与 Schema 门禁需求规格

## 简介

`mock-runtime-legacy-retirement` 完成后，当前 mock 主线已经收敛到 `src/mocks/**`：FastAPI OpenAPI artifact 是 API 事实源，前端生成类型约束 handler 与 dataset，MSW 是开发、测试和 demo-offline 的唯一网络虚拟化层，Dexie store 支撑离线演示持久写。

本规格把 OpenAPI 契约从“生成 TypeScript 类型”升级为“可执行覆盖矩阵、显式 handler metadata、核心响应 schema 校验和 CI 漂移门禁”。目标不是替换现有 MSW runtime，而是在当前 `src/mocks/**` 主线旁增加可治理的 contract layer，让新增或变更 API 能被机器发现、分类、验证和审查。

非目标：

- 不引入 Prism、Microcks、WireMock 或独立 mock server 替代现有 MSW + Dexie。
- 不恢复旧 `src/demo/**`、MCP、多场景 runtime package、active pointer、candidate/promote 或 runtime package writer。
- 不要求一次性为全部历史接口生成或替换现有业务 handlers。
- 不要求全部 OpenAPI operations 在本阶段都具备 runtime schema validation；OpenAPI response schema 为空或不可靠的接口必须显式标记。
- 不修改后端业务 API、`shared/openapi.json` 的事实源地位、当前 API 调用兼容层或 demo-offline 运行模式语义。

## Clarifications

### Session 2026-05-01

- Q: 第二个 spec 采用哪种总体方案？ -> A: 采用“显式 contract registry + coverage matrix + 核心 schema gate”的增量治理方案。
- Q: 是否联网对标后引入 Prism/Microcks/WireMock？ -> A: 不引入替代 mock server；只吸收 OpenAPI 元数据、响应校验和报告门禁做法。
- Q: handler 覆盖关系应该如何识别？ -> A: 以显式 metadata registry 为准，不依赖 regex 静态猜测作为唯一事实源。
- Q: endpoint 覆盖分类有哪些？ -> A: `mock-handled`、`real-only`、`unsupported-501`、`legacy-local-contract`、`missing`。
- Q: schema validation 的首批范围是什么？ -> A: 优先覆盖 auth、system、project、version、topology 等 demo-offline 主链路；OpenAPI response schema 为 `{}` 或不可靠时必须标记 `schema-unavailable`，不得假装已校验。
- Q: coverage report 是否作为提交到仓库的基线文件，还是只作为命令输出临时生成？ -> A: 只提交 registry/metadata；完整 coverage report 由命令稳定生成，CI 输出摘要和失败明细，不提交完整报告基线。
- Q: strict gate 对 `missing` 的失败范围怎么定？ -> A: critical `missing` 立即失败；non-critical `missing` 可作为受控债务存在，但必须声明 owner、原因和迁移动作，否则失败。
- Q: runtime schema validation 的 schema 来源优先级是什么？ -> A: P0 优先使用 `shared/openapi.json` 加 AJV 做本地 schema resolver，不改 `api:generate` 主链路；后续需要时再评估 Hey API schemas plugin。
- Q: critical API 清单的事实源放在哪里？ -> A: contract registry 显式维护 `critical` 标记作为事实源，同时用 `src/api/**`、demo-offline 页面入口和后续 E2E 作为辅助审计信号，发现新增调用漏标。
- Q: 本地 contract coverage check 的性能目标要不要写进 requirements？ -> A: 写入 10 秒软门槛；正常仓库状态下单独 coverage check 应在 10 秒内完成，schema-heavy 测试可放到 targeted Vitest suite。

## 需求列表

### R1: 建立 OpenAPI endpoint 覆盖矩阵
**用户故事:** 作为全栈维护者，我希望每个 OpenAPI operation 都在 mock 平台中有机器可读状态，以便后端接口变更不会靠人工记忆判断 mock 是否漂移。
**验收标准 (EARS):**
- R1.AC1: WHEN 执行契约覆盖检查 THEN 系统必须从 `shared/openapi.json` 枚举所有 HTTP operations，并记录 method、OpenAPI path、operationId、tags、summary、response schema 可用性和来源 artifact fingerprint。
- R1.AC2: WHEN OpenAPI operation 出现在 `shared/openapi.json` 中 THEN 覆盖矩阵必须为该 operation 提供且只提供一个覆盖分类：`mock-handled`、`real-only`、`unsupported-501`、`legacy-local-contract` 或 `missing`。
- R1.AC3: IF 新增、删除或修改 OpenAPI operation 后覆盖矩阵未同步 THEN 本地门禁和 CI 必须失败，并输出具体 method、path 和 operationId。
- R1.AC4: WHEN 生成覆盖报告 THEN 报告必须按 method/path 稳定排序，并包含 owner、覆盖分类、handler tag、测试文件、schema 校验状态、风险说明和后续动作。
- R1.AC5: IF OpenAPI operation 没有可靠 response schema THEN 覆盖矩阵必须标记 `schema-unavailable` 或等价 schema 状态，并说明原因，不得计入已完成 runtime schema validation。

### R2: 建立显式 handler metadata registry
**用户故事:** 作为 mock 平台维护者，我希望 MSW handler 与 OpenAPI operation 的绑定显式可查，以便 coverage gate 不依赖脆弱的源码正则推断。
**验收标准 (EARS):**
- R2.AC1: WHEN 新增或维护 `mock-handled` endpoint THEN 必须声明 handler metadata，至少包含 method、OpenAPI path、MSW path、handler tag、owner、critical 标记、覆盖分类和测试文件。
- R2.AC2: WHEN metadata 声明 path 参数 THEN 系统必须能规范化 OpenAPI `{param}` 与 MSW `:param` 的等价关系，并拒绝无法匹配到 OpenAPI operation 的 metadata。
- R2.AC3: WHEN `createMockHandlers()` 聚合 handlers THEN metadata registry 必须能覆盖当前聚合入口中的业务 handlers，并检测重复 method/path、重复 handler tag 或孤儿 metadata。
- R2.AC4: WHEN mock 响应被标记为 `mock-handled` 或 `unsupported-501` THEN 响应头 `X-Mock-Handler` 必须与 metadata 中的 handler tag 一致，文件下载等非 JSON 响应也必须保留可定位 tag。
- R2.AC5: IF 仅通过扫描 `http.get(createApiPath(...))`、`withBackendFallback()` 或字符串路径推断覆盖关系 THEN 该结果只能作为辅助审计，不得作为 coverage matrix 的唯一事实源。

### R3: 固化覆盖分类语义和失败规则
**用户故事:** 作为质量负责人，我希望每种 endpoint 覆盖分类都有明确门禁语义，以便 `missing`、只走真实后端和确定性 501 不会混在一起。
**验收标准 (EARS):**
- R3.AC1: WHEN endpoint 标记为 `mock-handled` THEN 它必须有可执行 MSW handler、handler metadata、至少一个测试证据和明确 schema 校验状态。
- R3.AC2: WHEN endpoint 标记为 `real-only` THEN 报告必须说明该接口不属于 demo-offline 关键链路，并且 demo-offline critical endpoint 不得使用该分类。
- R3.AC3: WHEN endpoint 标记为 `unsupported-501` THEN 对应 handler 必须返回确定性 `501` 语义、带 `X-Mock-Handler` debug header，并在报告中说明暂不支持原因。
- R3.AC4: WHEN endpoint 标记为 `legacy-local-contract` THEN 该 endpoint 必须指向 `src/mocks/contracts/local.ts` 或等价本地契约声明，并包含迁移到 OpenAPI schema 的目标和条件。
- R3.AC5: WHEN endpoint 标记为 `missing` THEN 报告必须包含 owner、原因、影响范围和迁移动作；IF 该 endpoint 属于 demo-offline critical API THEN strict gate 必须失败。
- R3.AC6: IF endpoint 未出现在覆盖矩阵或分类值不属于允许集合 THEN 本地门禁和 CI 必须失败。
- R3.AC7: IF non-critical endpoint 标记为 `missing` 但缺少 owner、原因或迁移动作 THEN strict gate 必须失败；否则允许作为显式技术债通过门禁。

### R4: 明确 demo-offline critical API 边界
**用户故事:** 作为演示交付负责人，我希望 demo-offline 关键链路接口有更严格契约门禁，以便离线演示不会在构建后才暴露 API 缺口。
**验收标准 (EARS):**
- R4.AC1: WHEN endpoint 被当前 demo-offline 主链路消费 THEN 覆盖矩阵必须将其标记为 critical，首批至少覆盖 auth、system menu、dict、role、dept、project、version、topology 和 simulation read model。
- R4.AC2: WHEN critical endpoint 出现在覆盖矩阵 THEN 它的覆盖分类只能是 `mock-handled` 或有明确业务说明的 `unsupported-501`，不得是 `real-only` 或 `missing`。
- R4.AC3: WHEN critical endpoint 是页面可写链路的一部分 THEN 必须声明持久化边界或只读/不支持原因，并与现有 Dexie store 或确定性 501 语义一致。
- R4.AC4: IF 前端 `src/api/**` 新增 demo-offline 页面会调用的 API wrapper THEN 对应 OpenAPI operation 必须被纳入 critical 覆盖评估。
- R4.AC5: WHEN strict gate 运行 THEN critical endpoint 的 missing、未注册 metadata、handler tag 不一致或测试证据缺失必须导致失败。
- R4.AC6: WHEN 判定 critical API 清单 THEN contract registry 中的 `critical` 标记必须作为事实源；`src/api/**`、demo-offline 页面入口和后续 E2E 覆盖只能作为辅助审计信号，用于发现漏标并提示补充 registry。

### R5: 增加核心响应 schema validation
**用户故事:** 作为代码审查者，我希望核心 mock response 在运行时按 OpenAPI schema 校验，以便 TypeScript 静态约束无法发现的响应漂移能被测试捕获。
**验收标准 (EARS):**
- R5.AC1: WHEN 核心 `mock-handled` endpoint 返回 JSON 响应 THEN 测试必须能对响应 body 执行 runtime schema validation；P0 schema 来源必须优先为 `shared/openapi.json`，并通过 AJV 或等价本地 resolver 解析 `$ref` 与 response schema。
- R5.AC2: WHEN 响应 body 与 OpenAPI 200 response schema 不兼容 THEN schema gate 必须失败，并输出 method、path、handler tag、失败字段和实际响应摘要。
- R5.AC3: WHEN OpenAPI response schema 为 `{}`、`unknown`、二进制下载或不适合本阶段校验 THEN endpoint 必须标记 `schema-unavailable`、`binary-response` 或等价状态，并说明不计入 schema coverage 的原因。
- R5.AC4: WHEN endpoint 使用本地临时契约 THEN schema validation 可以使用本地 adapter schema，但报告必须把该结果归类为 `legacy-local-contract`，不得冒充 OpenAPI schema 已覆盖。
- R5.AC5: WHEN 首批 schema gate 完成 THEN 至少 auth、system、project、version、topology 主链路的 JSON 响应必须有 runtime schema validation 或明确 schema-unavailable 例外。

### R6: 治理临时本地契约
**用户故事:** 作为 mock 数据维护者，我希望历史本地契约被显式追踪，以便它们不会长期隐藏在 `contracts/local.ts` 中。
**验收标准 (EARS):**
- R6.AC1: WHEN `src/mocks/contracts/local.ts` 或等价本地契约被引用 THEN 覆盖报告必须列出契约名称、使用 endpoint、owner、当前原因和迁移目标。
- R6.AC2: IF OpenAPI artifact 已经为某 endpoint 提供可靠 schema THEN 不得继续把该 endpoint 归类为 `legacy-local-contract`，除非报告中记录明确兼容例外。
- R6.AC3: WHEN 新增本地契约 THEN 必须同时新增覆盖矩阵条目、测试证据和迁移说明。
- R6.AC4: WHEN 本地契约已迁移到 OpenAPI schema THEN 对应 `legacy-local-contract` 分类和迁移说明必须删除或更新为 `mock-handled`。

### R7: 输出可审查的契约覆盖报告
**用户故事:** 作为 PR reviewer，我希望看到稳定、可读、可 diff 的 mock 契约覆盖报告，以便审查新增接口时能快速判断影响面。
**验收标准 (EARS):**
- R7.AC1: WHEN 执行覆盖报告命令 THEN 系统必须从已提交的 registry/metadata 与 `shared/openapi.json` 生成机器可读报告和人类可读摘要，至少包含总 operations 数、各分类数量、critical 缺口数量、schema coverage 数量和 local contract 数量。
- R7.AC2: WHEN 报告列出 endpoint THEN 每行必须包含 method、OpenAPI path、owner、分类、critical、handler tag、schema 状态、测试文件和迁移/风险说明。
- R7.AC3: WHEN 报告内容因 OpenAPI 或 metadata 变化而改变 THEN 命令输出必须稳定可 diff，不得包含时间戳、随机值、绝对临时路径或环境特定噪音。
- R7.AC4: IF 报告发现失败项 THEN 命令必须返回非 0，并在终端输出能直接定位的失败列表。
- R7.AC5: IF 报告可能包含敏感配置或 provider 信息 THEN 系统必须只输出 endpoint metadata 和 schema 状态，不得输出密钥、token、真实账号凭据或后端内部连接信息。
- R7.AC6: IF 需要保存完整 coverage report 文件 THEN 只能通过显式命令参数写入生成产物路径；默认门禁不得要求提交完整报告基线文件。

### R8: 接入本地与 CI 门禁
**用户故事:** 作为项目维护者，我希望契约覆盖与 schema 校验进入现有质量门禁，以便 API/mock 漂移在合并前被拦截。
**验收标准 (EARS):**
- R8.AC1: WHEN 执行前端质量门禁 THEN 必须运行 mock contract coverage check，并在 OpenAPI artifact、coverage matrix、handler metadata 或 schema gate 漂移时失败。
- R8.AC2: WHEN GitLab CI 执行 `frontend-quality-gates` THEN 必须在 `yarn api:generate` 和 mock/runtime 测试之后运行契约覆盖门禁或等价命令。
- R8.AC3: WHEN GitHub 手动 CI 执行前端检查 THEN 必须包含同等的契约覆盖检查，避免 GitHub 辅助 workflow 与 GitLab 主门禁口径分叉。
- R8.AC4: WHEN 开发者仅修改 mock handlers、contracts、OpenAPI artifact 或 `src/api/**` wrappers THEN 本地命令必须能独立运行并给出足够快的反馈，不强制依赖 `build:demo-offline`。
- R8.AC5: IF 环境缺少 schema validation 依赖、OpenAPI artifact 或必要生成产物 THEN 命令必须 fail fast 并提示安装/生成步骤，不得静默跳过。
- R8.AC6: WHEN 在正常本地仓库状态下单独执行 contract coverage check THEN 命令应在 10 秒内完成；schema-heavy 的实际响应校验可以放入 targeted Vitest suite，不得拖慢快速覆盖矩阵门禁。

### R9: 保持测试从真实请求链路进入
**用户故事:** 作为前端测试维护者，我希望契约测试继续通过真实 API function 或请求兼容层触发 MSW，以便 schema gate 验证的是实际调用行为而不是手写假响应。
**验收标准 (EARS):**
- R9.AC1: WHEN contract handler 测试验证 `mock-handled` endpoint THEN 测试必须优先通过 `src/api/**` API function、真实 `fetch`/request 兼容层或 MSW request path 触发 handler，不得直接 mock `@/utils/request` 逃避 HTTP 契约。
- R9.AC2: WHEN schema validation 测试运行 THEN 它必须验证实际 handler 返回的响应 body 和 debug headers，而不是只验证 TypeScript 类型或静态对象。
- R9.AC3: WHEN coverage matrix 引用测试文件 THEN 测试文件必须存在，并至少覆盖 handler tag 或 endpoint 响应的可定位证据。
- R9.AC4: IF 新增 handler 没有测试证据 THEN strict gate 必须失败或把 endpoint 标记为非完成状态。

### R10: 维护文档和模块 Definition of Done
**用户故事:** 作为团队协作者，我希望新增 mock API 的完成标准明确包含契约覆盖与 schema gate，以便后续开发不再只靠“handler 能跑”判断完成。
**验收标准 (EARS):**
- R10.AC1: WHEN 阅读 `src/mocks/README.md` 或 mock module DoD THEN 文档必须说明新增/修改 API 需要同步 OpenAPI artifact、coverage matrix、handler metadata、schema 状态和测试证据。
- R10.AC2: WHEN 新业务模块声明 mock 已完成 THEN DoD 必须包含 endpoint 分类、critical 评估、schema validation 或明确 schema-unavailable 例外。
- R10.AC3: IF 文档提到外部 mock server、旧 demo runtime、多场景 package 或 MCP 作为当前契约覆盖方案 THEN 必须明确其非目标、历史或暂停状态。
- R10.AC4: WHEN 本规格实施完成 THEN `docs/specs/README.md` 或相关索引必须把 `mock-contract-coverage-and-schema-gates` 标记为当前 mock 主线的 P0 治理升级 spec。

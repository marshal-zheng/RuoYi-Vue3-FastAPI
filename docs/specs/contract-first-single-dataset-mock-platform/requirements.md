# Contract-first 单套 Mock 数据平台需求规格

## 简介

当前主线从 MCP、多场景、runtime scenario package 收敛为一条更轻、更稳的 Mock-as-Code 路线：使用同一套 MSW handlers、同一套 typed mock data、同一套 factories 和测试门禁，同时支撑本地 `fallback` 开发和 `demo-offline` 静态演示。现有仓库已经有 `src/mocks/**` 与 `src/demo/**` 两套能力，但职责分叉明显：`fallback` 主要走 `src/mocks`，`demo-offline` 主要走 `src/demo` 的 IndexedDB、ScenarioRepository、DemoScenarioPackage 和 generated scenarios。

本需求定义目标态：以 FastAPI OpenAPI 契约为 API 事实源，以 `src/mocks` 为统一 mock 主线，以单套领域化 typed mock dataset 为数据事实源，以 MSW 作为网络虚拟化层，以测试和契约检查防止漂移。MCP、scenario registry、active pointer、candidate/promote、runtime package writer 不再作为本主线能力扩展；已有代码先冻结保留，待新主线覆盖后再按模块退场。

## 需求列表

### R1: 建立单套 typed mock dataset
**用户故事:** 作为前端研发负责人，我希望 dev fallback 与 demo-offline 共享同一套 typed mock dataset，以便功能开发、测试和演示数据长期不分叉。
**验收标准 (EARS):**
- R1.AC1: WHEN 应用运行在需要 mock 数据的模式下 THEN 系统必须从统一的 typed mock dataset 获取业务数据，而不得在 fallback 与 demo-offline 各自维护独立业务数据副本。
- R1.AC2: WHEN 新增或修改业务 API mock THEN 对应的数据、factory、handler 和测试必须进入同一套 mock 主线，并在编译期保持类型可检查。
- R1.AC3: IF 实现方案为当前主线新增 `scenarioId`、scenario registry、active pointer、candidate、promote 或多场景切换机制 THEN 该方案必须被拒绝。
- R1.AC4: WHEN 某个业务实体被多个接口使用时 THEN 该实体必须在 dataset 中只有一个事实源，接口响应只能派生或投影该事实源。

### R2: 按职责分层并按业务域组织文件
**用户故事:** 作为 mock 数据维护者，我希望 mock 文件既不全打平也不过度碎片化，以便工程项目、系统管理、仿真等复杂域长期可维护。
**验收标准 (EARS):**
- R2.AC1: WHEN 创建或迁移 mock 数据文件 THEN 必须按 `data`、`factories`、`handlers`、`invariants` 等职责分层组织。
- R2.AC2: WHEN 某个业务域包含多个聚合或超过一个接口族 THEN 该业务域必须在 `data/<domain>/` 下按聚合拆分文件，而不得把所有记录塞入单个大文件。
- R2.AC3: WHEN 业务域只包含少量稳定记录且无跨实体关系 THEN 允许在域内保持单文件，但不得影响后续按聚合拆分。
- R2.AC4: IF `index.ts` 被用于导出 mock 数据 THEN 它只能做聚合导出和轻量组装，不得承载大段业务记录或复杂生成逻辑。

### R3: 以 OpenAPI 契约约束 mock API 形状
**用户故事:** 作为全栈维护者，我希望 mock 响应结构跟随 FastAPI OpenAPI 契约，以便后端接口演进时前端 mock 能及时暴露漂移。
**验收标准 (EARS):**
- R3.AC1: WHEN 后端 OpenAPI 契约可用时 THEN 后端必须通过确定性脚本导出仓库内 OpenAPI artifact，前端必须从该 artifact 生成或更新 TypeScript API 类型，并让 mock data 或 handler 响应受这些类型约束。
- R3.AC2: WHEN 后端当前 OpenAPI 契约与仓库内 artifact 不一致 THEN CI 或本地门禁必须失败，并提示需要同步导出 artifact、API 调用层和 mock 数据。
- R3.AC3: IF 某个历史接口暂时没有可靠 OpenAPI 类型 THEN 该接口必须在 mock 平台中声明临时本地契约，并标注迁移到 OpenAPI 类型的后续动作。
- R3.AC4: WHEN API 响应包含分页、错误码、文件下载或二进制响应 THEN mock handler 必须保持与真实调用层兼容的响应包装和状态语义。

### R4: 让 MSW 成为唯一网络虚拟化层
**用户故事:** 作为前端开发者，我希望开发、测试和离线演示通过同一套 MSW handlers 表达网络行为，以便减少“测试通过但演示失败”的差异。
**验收标准 (EARS):**
- R4.AC1: WHEN 应用运行在 `fallback` 模式 THEN 系统必须优先访问真实后端，并仅在约定失败条件下回退到统一 MSW handler。
- R4.AC2: WHEN 应用运行在 `demo-offline` 模式 THEN 所有关键 `/api/**` 请求必须由统一 MSW handler 处理，不得访问真实后端。
- R4.AC3: IF `demo-offline` 模式出现未覆盖的关键 API 请求 THEN 系统必须返回确定性错误并让测试或验收暴露缺口。
- R4.AC4: WHEN Vitest、页面预览或后续浏览器测试需要 mock 网络 THEN 它们必须复用同一套 handler 注册入口，而不得直接 mock 请求适配层替代 HTTP 合约。

### R5: 支持 demo-offline 从旧 scenario runtime 平滑切换
**用户故事:** 作为项目维护者，我希望 demo-offline 能逐步从旧 `src/demo/**` scenario runtime 切换到统一 `src/mocks` 主线，以便降低一次性迁移 2 万行旧代码的风险。
**验收标准 (EARS):**
- R5.AC1: WHEN 新 mock 主线尚未覆盖全部 demo-offline 能力 THEN 旧 `src/demo/**` 代码必须冻结为 legacy fallback，不再扩展 MCP、多场景或 runtime package 能力；首批迁移范围限定为 auth、system 菜单、project、version、topology 和 simulation 只读展示。
- R5.AC2: WHEN auth、system 菜单、project、version、topology 在新 mock 主线中达到数据、handler、持久可写 store、测试和演示验收覆盖 THEN demo-offline 对这些业务域必须切换到新主线，不再依赖对应旧 scenario 数据源。
- R5.AC3: IF 迁移过程中发现旧 demo service 行为仍有业务价值 THEN 必须将该行为转化为新 mock handler、store 或 invariant，而不是继续扩大旧 runtime 架构。
- R5.AC4: WHEN 新主线覆盖既定 demo-offline 核心链路后 THEN 必须制定删除旧 scenario runtime、generated scenarios 和相关文档的收尾任务。

### R6: 保证 mock 数据确定性与可复现
**用户故事:** 作为质量负责人，我希望 mock 数据生成结果稳定可复现，以便测试、演示截图和问题复盘不随时间随机漂移。
**验收标准 (EARS):**
- R6.AC1: WHEN factory 使用 faker、随机数或时间 THEN 必须通过统一 seed、固定 reference time 或等价机制保证同一输入产生同一输出。
- R6.AC2: IF mock dataset 中出现 `Date.now()`、未固定 reference time 的相对日期或未受控随机数 THEN 质量门禁必须失败。
- R6.AC3: WHEN 需要模拟运行态 token、会话或临时票据 THEN 可以使用运行时动态值，但这些值不得进入稳定 dataset 或验收快照。
- R6.AC4: WHEN AI Agent 或开发者更新 mock 数据 THEN 更新结果必须能通过同一套 deterministic 生成与 invariant 检查复现。

### R7: 用领域 invariant 保护数据自洽
**用户故事:** 作为业务演示负责人，我希望 mock 数据之间的角色、菜单、部门、项目、版本、拓扑和仿真关系自洽，以便演示像真实业务系统而不是随机样例。
**验收标准 (EARS):**
- R7.AC1: WHEN mock dataset 被构建或测试加载 THEN 必须执行领域 invariant 检查，覆盖外键引用、唯一键、枚举值、权限菜单和核心业务关系。
- R7.AC2: WHEN 工程项目域包含项目、版本、拓扑、文档或仿真引用 THEN invariant 必须验证这些记录能互相追溯，且列表、详情和关联接口返回一致。
- R7.AC3: IF mock 数据中存在孤儿记录、重复关键标识、无效状态流转或缺失必填展示字段 THEN 测试必须失败。
- R7.AC4: WHEN 新增业务域 mock 数据 THEN 必须同步新增至少一组该域 invariant，不能只依赖 TypeScript 结构检查。

### R8: 明确只读数据、可写行为和持久化边界
**用户故事:** 作为演示能力设计者，我希望明确哪些 mock 行为只是展示、哪些需要持久可写，以便 demo-offline 能完成客户演示闭环且避免无意识重建旧 IndexedDB scenario 平台。
**验收标准 (EARS):**
- R8.AC1: WHEN 某个 demo-offline API 只用于展示 THEN handler 应以只读 typed dataset 为事实源，并保持刷新后可预测。
- R8.AC2: WHEN auth、project、version 或 topology 的 demo-offline API 需要新增、编辑、删除、状态切换或保存拓扑 THEN 目标态必须使用浏览器本地持久 store，并在刷新后保留用户演示修改。
- R8.AC3: WHEN 实现浏览器本地持久 store THEN 必须在 `src/mocks/store/**` 下建立轻量 Dexie/IndexedDB schema，只服务单套 typed dataset，不得复用旧 `DemoScenarioPackage`、`ScenarioRepository` 或 active/candidate/promote 模型。
- R8.AC4: IF 某个写操作仅属于会话 token、临时票据、一次性上传占位等非业务持久数据 THEN 可以使用内存 store，但不得替代核心业务写操作的持久化要求。
- R8.AC5: WHEN 设计持久可写行为 THEN 必须定义重置 dataset 机制、持久化边界、数据版本迁移策略和对应测试覆盖；simulation 首批只要求只读展示，不要求启动、暂停、停止等控制写操作。

### R9: 固化质量门禁和迁移验收
**用户故事:** 作为项目维护者，我希望新 mock 主线拥有稳定质量门禁，以便长期防止 API、数据和演示链路再次分叉。
**验收标准 (EARS):**
- R9.AC1: WHEN 提交修改 mock data、factory、handler 或 API 契约相关代码 THEN 必须运行前端类型检查、mock/invariant 测试和相关 handler 测试。
- R9.AC2: WHEN demo-offline 主链路发生变更 THEN 必须运行 `build:demo-offline` 或等价构建验收，确认生产构建仍不启动 mock。
- R9.AC3: IF `src/mocks/**` 中新增 TypeScript 检查禁用注释、漂移数据源或未覆盖 handler THEN 门禁必须失败。
- R9.AC4: WHEN 新业务模块完成开发 THEN 其 Definition of Done 必须包含 API 契约、typed mock data、MSW handler、invariant 测试和 demo-offline 覆盖说明。

### R10: 同步文档与旧主线降级说明
**用户故事:** 作为团队协作者，我希望文档明确当前主线和 legacy 边界，以便后续开发不再回到 MCP 或多场景设计。
**验收标准 (EARS):**
- R10.AC1: WHEN 本规格进入实施 THEN `src/mocks/README.md`、相关 runbook 或 specs 索引必须说明当前主线是单套 typed mock dataset，而不是 MCP 或多场景 runtime package。
- R10.AC2: WHEN 文档提到 `scenario`、MCP、active pointer、candidate 或 promote THEN 必须标注其 legacy/paused 状态或迁移计划，避免被误认为新主线验收路径。
- R10.AC3: IF 文档仍要求 demo-offline 数据通过 MCP 生成并激活作为当前主路径 THEN 该文档必须被更新或标记为历史方案。
- R10.AC4: WHEN 团队成员按文档新增 mock 能力 THEN 应能从文档直接判断文件放置、类型约束、测试要求和 demo-offline 验收命令。

## Clarifications

### Session 2026-04-30

- Q: 是否保留 MCP 和多场景作为当前主线？ -> A: 不保留。MCP 暂停/冻结，当前主线回到 MSW + typed mock data + tests。
- Q: 是否需要 typed scenario 或多套业务场景？ -> A: 不需要。只有一套演示数据，typed 只表示 mock 数据受 TypeScript/API 契约约束。
- Q: dev 和 demo-offline 是否复用同一套 mock？ -> A: 是。`fallback` 真实后端优先并由 MSW 兜底，`demo-offline` 全部走 MSW，`prod` 不启动 MSW。
- Q: mock 数据文件是否全打平？ -> A: 不全打平。按职责分层，再按业务域和聚合拆分，工程项目等复杂域必须建域目录。
- Q: 是否立即删除旧 `src/demo/**` 和 MCP 代码？ -> A: 不立即删除。先建立新主线并逐域切换，旧体系冻结保留，覆盖足够后再删除。
- Q: demo-offline 的写操作目标态是什么？ -> A: 持久可写。demo-offline 写操作刷新后仍保留，必须提供重置机制。
- Q: OpenAPI 契约事实源采用哪种目标态？ -> A: 导出 + 提交 + CI 比对。后端脚本导出确定性 OpenAPI artifact，前端从 artifact 生成类型，CI 检查后端当前契约与 artifact 是否漂移。
- Q: 首批迁移覆盖范围怎么定？ -> A: 核心演示链路。首批覆盖 auth、system 菜单、project、version、topology；simulation 只读展示。
- Q: 浏览器本地持久 store 的技术边界是什么？ -> A: 新轻量 IndexedDB。新建 `src/mocks/store`，用轻量 Dexie/IndexedDB schema，只服务单套 dataset，不复用旧 `DemoScenarioPackage` 或 `ScenarioRepository`。

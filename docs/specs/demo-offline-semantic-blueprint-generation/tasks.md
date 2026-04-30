# Demo Offline Semantic Blueprint Generation 实现任务

- [x] 1. 建立 Business Blueprint 与语义质量基础类型
  - 类别：contract/schema。
  - 新增 MCP 侧 `BusinessBlueprint`、语义实体、语义锚点、锚点绑定、`SemanticQualityIssue`、`SemanticQualitySummary` 和 `SemanticQualityReport` 类型。
  - 新增 Blueprint schema，覆盖行业名称、关键词、业务对象、部门、persona、流程阶段、风险类型、指标定义和 story beats。
  - 实现 `blueprint-schema` 与 `blueprint-semantic-minimum` 校验，强制业务对象 >=5、persona >=3、部门 >=2、流程阶段 >=5、风险类型 >=4、指标定义 >=4、story beats >= `projectCount`。
  - 校验失败时返回结构化 issue，并保留 `path`、`code`、`severity`、`actual`、`expected`、`fixHint`。
  _需求追溯: R1.AC1, R1.AC2, R1.AC4, R7.AC1, R8.AC1_

- [x] 2. 实现 seed-aware Business Blueprint deterministic generator
  - 类别：MCP generation。
  - 新增本地 deterministic Blueprint 生成器，输入 `topic`、`businessDescription`、`topicKey`、`seed`、`contractFingerprint`、`generatorVersion` 和 `projectCount`。
  - 确保测试和 CI 不依赖 AI provider、API key 或联网能力。
  - 当 `businessDescription` 变化时，业务对象、流程、风险或指标能发生可观察语义变化。
  - 保持 Spec A 范围只生成 `project` 与 `simulation` 语义，不新增未知模块能力。
  _需求追溯: R1.AC3, R2.AC1, R2.AC3, R2.AC4, R5.AC1, R5.AC2, R5.AC3, R5.AC4, R5.AC5_

- [x] 3. 实现 Blueprint 到 IndustryDataDraft 的编译与锚点绑定
  - 类别：MCP generation。
  - 新增 `compileBlueprintToIndustryDraft()`，在现有 `IndustryDataDraft` 之前插入 Blueprint 编译层。
  - 让项目名称、描述、region、stage、owner、risk、remark、keyMetrics、topology 和 simulation 草稿都由 Blueprint 语义推导。
  - 为每条主演示主记录生成通用语义锚点绑定，至少包含 3 类锚点，且包含 `storyBeat` 或 `domainObject` 中至少一种。
  - 保持 `auth`、`system` 从 default scenario 复制，最终数据仍进入现有 `DemoScenarioPackage` v1。
  _需求追溯: R1.AC5, R2.AC2, R2.AC5, R3.AC1, R3.AC2, R3.AC4, R3.AC5, R4.AC1, R4.AC2, R4.AC3, R4.AC4, R7.AC2, R7.AC3_

- [x] 4. 新增 DiversityValidator 并接入结构化 issue
  - 类别：validator。
  - 检查主列表与用户可见字段中的 name/title、description/remark、owner、department/persona、stage、risk、keyMetrics 和时间推进线索。
  - 实现 normalized duplicate ratio 与模板相似度检测：关键维度 >=75% 或相似度 >=0.85 为 error，50%-75% 为 warning。
  - 支持可由 Blueprint 业务事实解释的轻度重复降级为 warning。
  - issue 的 `fixHint` 必须指向 Blueprint 或生成规则修复路径，不要求手改最终 `active.json`。
  _需求追溯: R3.AC3, R6.AC1, R6.AC2, R6.AC3, R6.AC4, R6.AC5_

- [x] 5. 新增 SemanticCoverageValidator 通用语义锚点校验
  - 类别：validator。
  - 基于通用语义锚点范式校验主记录 coverage，不把规则写死为项目管理模块特例。
  - 检查 `project + simulation` 首批映射是否能用同一锚点支撑主记录摘要、版本、拓扑、仿真消息、告警、故障和事件。
  - coverage 缺失来自 Blueprint 时 issue 指向 Blueprint path；来自映射或 package 时 issue 指向生成映射或 package path。
  - 输出每条主记录的 coverage summary，包含锚点类型、锚点 ID 或可读标签。
  _需求追溯: R4.AC5, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5, R7.AC6_

- [x] 6. 实现 SemanticQualityReport 与 report artifact 写入
  - 类别：contract/schema。
  - 生成 `SemanticQualityReport`，包含 Blueprint 摘要、diversity summary、semantic coverage summary、语义锚点绑定摘要和结构化 issue 列表。
  - 将 Blueprint 或语义锚点绑定结果持久化为 MCP artifact、meta 或 quality report，不作为浏览器 runtime 必需输入。
  - report 文件只写入 `demo-scenarios/**`，并复用 offline-static 写路径安全校验。
  - 保持 P0 `RuntimeValidationSummary` 的 schema、contract、invariant、dry-run 结果不被 semantic report 替代。
  _需求追溯: R7.AC5, R8.AC1, R8.AC2, R8.AC4, R8.AC5, R9.AC4_

- [x] 7. 将 Blueprint 与 semantic gates 接入 offline-static 生成激活链路
  - 类别：MCP generation。
  - 在 `generateOfflineStaticRuntimePackage()` 中改为 Blueprint -> Draft -> v1 package 的流程，保留现有 `compileScenarioPackage()`、schema validation、contract validation、invariant validation、writer 和 activation 机制。
  - semantic quality gate 出现 error 时不得写入或覆盖 `active.json`、`active.meta.json`、active report 或 active package。
  - warning only 时允许写 candidate 或继续激活，但 MCP 返回结果必须保留 warning、fixHint、semantic summary 和 report artifact。
  - 保持 `offline-static` 输出 v1 `active.json`、`previous.json`、`active.meta.json` 兼容结构。
  _需求追溯: R1.AC5, R8.AC2, R8.AC3, R8.AC4, R8.AC5, R9.AC1, R9.AC2, R9.AC4_

- [x] 8. 扩展 MCP customer-facing 输出并保持 runtime 边界不变
  - 类别：repository/importer。
  - 扩展 `OfflineStaticActivationResult` 和 `demo_offline_generate_runtime_demo` customer-facing result，返回 semantic quality summary、semantic report path 和 artifacts。
  - 不新增浏览器 API，不要求 runtime loader 读取 Blueprint、semantic report 或语义锚点文件。
  - 确认 Vue 页面、MSW handler、service/repository、IndexedDB schema、后端 API、`real`、`fallback`、`build:prod` 和普通开发模式不因 Spec A 改变。
  - 保持 `source-generated` 开发流程边界；如复用 semantic generator，也必须继续输出现有 v1 scenario 结构。
  _需求追溯: R8.AC1, R8.AC5, R9.AC2, R9.AC3, R9.AC5_

- [x] 9. 增加语义层单元测试矩阵
  - 类别：test matrix。
  - 覆盖 Blueprint schema 缺字段、语义最小集不足、无效锚点 ID、外部 AI 候选结构不合格等失败场景。
  - 覆盖 deterministic generator 同输入稳定、`businessDescription` 变化导致语义变化、locale-aware faker 或同类能力接入 seed。
  - 覆盖 BlueprintDraftCompiler 生成 project/simulation draft 与锚点绑定。
  - 覆盖 DiversityValidator 的 error/warning 阈值和可解释重复。
  - 覆盖 SemanticCoverageValidator 的锚点不足、支撑记录缺失、Blueprint path 与 package path issue。
  _需求追溯: R1.AC2, R1.AC3, R1.AC4, R3.AC3, R5.AC2, R5.AC3, R5.AC5, R6.AC2, R6.AC3, R6.AC4, R7.AC2, R7.AC4, R7.AC6, R10.AC3_

- [x] 10. 增加 offline-static 集成验收测试
  - 类别：test matrix。
  - 使用至少两个主题，例如 `无人机巡检任务管理` 与 `二手电脑回收管理`，验证 Blueprint、project 主记录、keyMetrics 和 simulation events 存在主题相关差异。
  - 对同一主题重复生成，验证 semantic summary 和核心 v1 package 稳定可复现。
  - 验证 semantic error 不写 `active.next.json`、不激活 `active.json`、不覆盖 active meta 或 active report。
  - 验证 warning only 时可以生成 candidate/active，并返回 semantic report artifact。
  - 验证 schema validation、contract validation、invariant validation 和 import dry-run 仍通过。
  _需求追溯: R5.AC2, R5.AC4, R8.AC3, R8.AC4, R9.AC1, R10.AC1, R10.AC2, R10.AC3, R10.AC4_

- [x] 11. 执行回归命令并记录实现验收结果
  - 类别：test matrix。
  - 运行 MCP 测试，例如 `cd tools/demo-offline-mcp && npm test -- --run`。
  - 如类型或前端 runtime 契约受影响，运行 `cd ruoyi-fastapi-frontend && yarn type-check` 和 targeted runtime/scenario tests。
  - 在任务完成记录中说明 semantic gates、v1 runtime compatibility、report artifact 和 no-runtime-dependency 边界的验证结果。
  _需求追溯: R8.AC2, R9.AC2, R9.AC3, R9.AC5, R10.AC4, R10.AC5_

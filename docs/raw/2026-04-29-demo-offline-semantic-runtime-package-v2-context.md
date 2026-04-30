# Demo Offline Semantic Runtime Package v2 上下文记录

日期：2026-04-29

状态：原始记录（用于后续分别产出正式 specs）

目的：沉淀本轮关于 `demo-offline` 长期数据生成范式的关键上下文。本文不是正式 spec，不定义最终任务清单；后续正式 specs 应基于本文拆分 requirements / design / tasks。

## 1. 背景

当前 `demo-offline-runtime-scenario-package` 已经把客户行业数据从编译期 TS scenario 推向 build 后可替换的 runtime JSON package。这个方向解决了：

```text
技术人员 build 通用 dist-demo-offline
  -> 非技术人员通过 AI Agent + MCP 生成行业数据
  -> MCP 写 dist-demo-offline/demo-scenarios/active.json
  -> 浏览器启动时导入 IndexedDB
  -> MSW handler / service / repository 继续从 IndexedDB 读数据
```

但用户进一步指出两个长期问题：

1. 现在只生成一个 project/version 就已经接近 2000 行 JSON；如果未来生成完整项目或更多业务模块，单个 `active.json` 会持续膨胀。
2. 当前数据存在同质化：标题和编号不同，但描述、创建人、创建时间、负责人等字段高度重复。用户关注的不是项目管理模块本身，而是后续未知业务生成的数据不能都只是模板换壳。

这两个问题说明：P0 的 runtime JSON package 只解决了“build 后换数据”，还没有解决“长期高质量、可扩展、可维护地生成未知业务 offline demo 数据”。

## 2. 当前实现问题的本地证据

本轮检查到的关键实现点：

- `tools/demo-offline-mcp/src/offline-static/generate.ts`
  - `createDeterministicIndustryDraft()` 只按 topic/topicKey 生成很少的 stage/risk/owner 模板。
  - 对多数未知业务使用通用阶段：`需求识别`、`方案设计`、`执行跟踪`、`风险复核`、`交付验收`。
  - 默认风险语句也很模板化：`关键流程进度偏慢。`、`跨角色协同信息不完整。`、`现场验收材料待补齐。`
- `tools/demo-offline-mcp/src/compiler.ts`
  - `projectId = 7001 + projectIndex`
  - `versionId = 8001 + projectIndex * 10`
  - `createBy = ${plan.industry}演示团队`
  - 许多时间、描述、拓扑、仿真字段由固定公式或 fallback 模板推导。
- 当前 `dist-demo-offline/demo-scenarios/active.json`
  - 行数约 1839 行，体积约 56K。
  - 当前体积不是浏览器性能瓶颈，但暴露了长期全量单文件不可维护的问题。

结论：

```text
当前重复不是 UI 偶然，也不是单个字段 bug，而是生成范式仍停留在“模板字段填充”。
```

## 3. 核心判断

长期收益最大的方案，不是“让 MCP 更会生成一个更大的 JSON”，而是把 demo-offline 升级成一套：

```text
业务语义蓝图
  -> 场景知识图
  -> 模块契约
  -> 确定性编译/展开
  -> 分片 runtime package
  -> 多层质量闸门
```

最终目标不是生成表数据 JSON，而是生成一个：

```text
可验证
可展开
可回滚
可复现
可局部更新
能表达真实业务差异
的离线业务场景包
```

关键原则：

- AI 不直接写最终 `active.json` 或最终业务表数据。
- AI 只生成业务语义层的小而精蓝图。
- compiler / generator adapter / validator 负责最终结构、ID、时间、关系、状态机、跨表引用和可复现性。
- 页面、API、MSW handler、service/repository 尽量不改，仍然只消费 IndexedDB。
- `real`、`fallback`、`build:prod` 不受影响。
- `source-generated` 开发流程保留。
- v1 `active.json` 保留兼容；v2 旁路新增，不推翻现有成果。

## 4. 推荐总架构

建议总方向命名：

```text
Demo Offline Semantic Data Platform
```

核心组件：

```text
DOMC 模块契约
+ Business Blueprint 业务语义蓝图
+ Scenario Graph 场景知识图
+ Generator Recipes 生成配方
+ Manifest/Slices/Pointer runtime package
+ Quality Gates 质量闸门
```

### 4.1 DOMC: Demo Offline Module Contract

DOMC 是每个业务模块接入 demo-offline 数据生成平台的契约。未来“未知业务”不能靠 prompt 瞎猜，必须先成为“可接入业务”。

每个 DOMC 应至少描述：

- 模块名称和业务边界
- 页面需要哪些数据
- API handler 覆盖哪些接口
- IndexedDB table mapping
- 实体、主键、外键、枚举、状态机
- required fields
- 字段语义要求
- 最小记录数
- 跨实体引用规则
- UI journey 最小可演示链路
- 允许复制的默认 slice
- 必须生成的业务 slice
- generator adapter 名称和版本
- diversity rules
- invariant rules

没有 DOMC 的模块，MCP 必须返回 blocker，而不是自由编造。

### 4.2 Business Blueprint

Business Blueprint 是 AI 主要参与的层，不是最终业务表数据。

Blueprint 应表达：

- 行业词汇
- 客户业务对象
- 组织/部门/角色/persona
- 流程阶段
- 关键事件类型
- 风险类型
- 指标口径
- 状态变化
- 典型故事线
- 客户可理解的话术

示意：

```json
{
  "industry": "无人机巡检",
  "domainObjects": ["巡检任务", "航线", "杆塔", "缺陷", "复核单"],
  "personas": [
    { "role": "巡检调度员", "department": "生产指挥中心" },
    { "role": "缺陷复核员", "department": "设备运维部" }
  ],
  "processStages": ["计划编排", "航线审核", "现场巡检", "缺陷识别", "复核闭环"],
  "riskTypes": ["禁飞区冲突", "图像回传延迟", "缺陷等级争议", "天气窗口不足"],
  "metricDefinitions": ["准点起飞率", "缺陷识别率", "复核闭环时长"],
  "storyBeats": [
    "调度员在大风前重新编排航线",
    "AI 识别疑似绝缘子破损后提交人工复核",
    "运维班组根据缺陷等级安排消缺"
  ]
}
```

### 4.3 Scenario Graph

Scenario Graph 把 blueprint 转成可验证的业务关系图。

它表达：

```text
角色 -> 负责流程 -> 处理对象 -> 产生事件 -> 触发风险 -> 影响指标 -> 出现在页面链路里
```

目的：

- 防止列表数据只是孤立文案。
- 保证详情页、拓扑页、仿真页能解释列表摘要。
- 保证跨页面数据一致。
- 为 generator recipes 提供可展开事实。

### 4.4 Generator Recipes

Recipes 用于避免全量物化所有可推导数据。

不要把每一条消息、时间线、指标、事件、告警都直接存入 `active.json`。可推导数据应存成：

```text
seed
+ blueprint facts
+ scenario graph
+ recipe parameters
```

然后在 MCP dry-run 或浏览器启动导入时确定性展开进 IndexedDB。

示意：

```json
{
  "recipeId": "simulation.timeline.v1",
  "inputs": {
    "storyBeatId": "drone-defect-review",
    "sessionCount": 3,
    "eventsPerSession": 8,
    "timeWindow": "2026-04-20..2026-04-28"
  },
  "seed": "..."
}
```

### 4.5 Runtime Package v2

v2 不再要求所有数据放在一个 `active.json` 中。

推荐结构：

```text
dist-demo-offline/demo-scenarios/
  active.json
  active.meta.json
  previous.json

  active.pointer.json
  previous.pointer.json
  releases/
    <release-id>/
      manifest.json
      blueprint.json
      graph.json
      recipes.json
      slices/
        auth.json
        system.json
        project.projects.json
        project.versions.json
        project.topologies.json
        simulation.sessions.json
        simulation.messages.json
        simulation.metrics.json
```

兼容策略：

```text
runtime loader 启动
  -> 如果 active.pointer.json 存在，走 v2 manifest/slices
  -> 否则走现有 v1 active.json
  -> v2 失败可 fallback 到 previous.pointer.json
  -> 再失败可 fallback 到 v1 previous.json
  -> 再失败使用 bundle default scenario
```

页面和 MSW 不直接消费 v2 文件。v2 文件仍然只是导入源；运行阶段依然从 IndexedDB 读取。

## 5. 如何解决文件爆炸

仅使用 `manifest + slices` 可以解决：

- 单文件过大
- diff 难看
- 局部更新困难
- 局部回滚困难
- 人工 review 不清晰

但它不能彻底解决“总数据量不断变大”。真正的长期方案必须加：

```text
Business Blueprint
+ Scenario Graph
+ Generator Recipes
+ Materialized Critical Slices
```

原则：

- 不要全量物化所有可推导数据。
- 关键业务事实和人工可审字段要物化。
- 大量派生数据、时间线、消息流、指标序列、仿真帧尽量由 recipes 确定性展开。
- MCP dry-run 与浏览器 runtime 使用同一套或等价展开逻辑。
- manifest 记录每个 slice / blueprint / graph / recipe 的 hash。
- root fingerprint 基于 manifest + slice hashes + recipe hashes + contract fingerprint 计算。

建议验收指标：

- 小场景可以继续使用 v1 `active.json`。
- 大场景必须走 v2 release。
- v2 release 的 `manifest.json` 应能定位每个 slice。
- 单个 slice 文件建议保持在可 review 尺寸内，例如小于 2000 行或小于约 200K；超过时继续按 table/page/journey 拆分。
- 可推导数据不得无理由全量写入 JSON；需要在 manifest 中说明 materialization reason。
- 激活 v2 release 只切换 pointer，不覆盖旧 release 目录。

不建议只靠 gzip/br 压缩解决。压缩只能减少传输体积，不能解决生成、diff、review、局部修复、局部回滚的问题。

## 6. 如何解决数据同质化

必须新增 `Diversity Contract` 和 `Semantic Coverage Validator`。

同一列表内应检查：

- `name/title` 相似度不能过高。
- `description` 不能复用同一模板句式。
- `createBy` / `owner` / `department` / `role` 不能无业务原因全部相同。
- `createTime` / `updateTime` 必须符合业务阶段推进，而不是固定日期。
- `status` / `riskLevel` / `stage` 应有业务分布。
- 每条主记录必须绑定不同 story beat、对象、角色、风险或指标。
- 详情页、拓扑、仿真事件必须能解释列表摘要。
- 相同 topic + seed 下可复现，不同 topic 下语义显著变化。

建议新增 validator：

```text
DiversityValidator
  -> 字段重复度
  -> 文本相似度
  -> 模板句式检测
  -> persona/department/stage/status 分布

SemanticCoverageValidator
  -> 每条列表记录是否绑定 story beat
  -> 详情页是否有支撑事实
  -> 事件/指标/风险是否对应业务对象

UIJourneyCoverageValidator
  -> 项目列表
  -> 详情页
  -> 版本页
  -> 拓扑页
  -> 仿真页
  -> 未来其他模块页面
```

同质化失败示例：

```text
4 条记录 createBy 全部为“无人机巡检任务管理演示团队”
4 条 description 前半句完全相同
4 条 createTime 完全相同
4 条只是编号不同、业务对象不同不明显
```

这种情况应至少 warning；如果是主演示列表，应 error，禁止激活 official runtime package。

## 7. MCP 改造边界

改造主战场是 MCP，但不能只改 MCP。

| 层 | 改造程度 | 是否侵入现有流程 |
| --- | --- | --- |
| MCP 生成器 | 最大 | 新增 v2 target / packageFormat，不破坏 v1 |
| runtime loader | 中等 | 只在 `demo-offline` 模式生效，兼容 v1 |
| contract/schema | 中等 | 新增 manifest/slice/blueprint/DOMC schema |
| ScenarioRepository | 小到中等 | 继续只负责导入 IndexedDB，可增加 recipe 展开入口 |
| 页面/API/MSW | 基本不动 | 继续从 IndexedDB 读 |
| backend/real/fallback/prod | 不动 | 不加载外部 runtime package / MCP / AI |
| source-generated 开发流程 | 不动或小改 | 继续保留 |

建议输入参数：

```json
{
  "topic": "无人机巡检任务管理演示",
  "businessDescription": "面向电力园区和应急场景，突出航线编排、缺陷识别、复核闭环和风险预警。",
  "target": {
    "kind": "offline-static",
    "root": "/path/to/dist-demo-offline",
    "packageFormat": "v2"
  },
  "activate": true
}
```

v1 兼容输入继续有效：

```json
{
  "target": {
    "kind": "offline-static",
    "root": "/path/to/dist-demo-offline",
    "packageFormat": "v1"
  }
}
```

## 8. 建议拆分 specs

不建议写成一个巨型 spec。推荐：

```text
0. demo-offline-semantic-data-platform
1. demo-offline-semantic-blueprint-generation
2. demo-offline-runtime-package-v2-manifest-slices
3. demo-offline-domc-registry-and-generator-adapters
```

### 8.1 总纲：demo-offline-semantic-data-platform

定位：长期架构总纲，不直接作为一次实现大包。

内容：

- 为什么从 `active.json` 表数据生成升级为 semantic data platform
- v1/v2 兼容策略
- AI / MCP / compiler / runtime / MSW 边界
- DOMC、Blueprint、Scenario Graph、Recipes、Manifest/Slices、Quality Gates 的关系
- 不侵入现有开发流程的原则
- 后续 specs 的拆分边界

### 8.2 Spec A：demo-offline-semantic-blueprint-generation

优先级最高，最快解决数据同质化。

目标：

- MCP 生成 Business Blueprint。
- 扩展 `IndustryDataDraft`，让创建人、负责人、部门、描述、时间、状态、指标、事件都从业务语义推导。
- 引入 seed-aware RNG 和 locale-aware faker。
- 新增 DiversityValidator / SemanticCoverageValidator。
- 仍然输出现有 v1 `active.json`，不改 runtime package 格式。

这一步主要改 `tools/demo-offline-mcp/**`，收益快、风险低。

### 8.3 Spec B：demo-offline-runtime-package-v2-manifest-slices

优先级第二，解决文件爆炸和局部维护。

目标：

- 新增 `active.pointer.json`
- 新增 `releases/<id>/manifest.json`
- 新增 slices 目录
- manifest 记录 slice hash、schemaVersion、contractFingerprint、recipe hash、root fingerprint
- runtime loader 支持 v1/v2 双格式
- MCP writer 支持 release 目录、pointer 原子切换、previous pointer
- import dry-run 支持 v2 release

这一步改 MCP writer、runtime loader、contract/schema，页面/MSW/service 不动。

### 8.4 Spec C：demo-offline-domc-registry-and-generator-adapters

优先级第三，解决长期未知业务精准接入。

目标：

- 建立 DOMC registry。
- 每个业务模块必须注册 module contract。
- 每个模块有 generator adapter。
- 没有 DOMC 的未知模块必须 blocker。
- DOMC 描述 UI journey、API handler、IndexedDB mapping、状态机、字段语义、diversity rules、invariants。
- MCP 基于 DOMC 选择可生成模块和不可生成模块。

这一步会提升长期平台化能力，但不应阻塞前两步收益。

## 9. 推荐实施顺序

推荐顺序：

```text
总纲 -> Spec A -> Spec B -> Spec C
```

如果时间紧：

```text
Spec A 先行
  -> 立刻修复同质化
  -> 仍然保持 active.json 兼容
  -> 再补总纲
  -> 再做 Spec B / C
```

原因：

- 数据同质化是用户马上能看到的质量问题。
- 文件爆炸是长期维护问题，但可以先通过 v2 分片解决。
- DOMC registry 是长期平台能力，收益最大但改造更深。

## 10. 质量闸门建议

未来 official runtime package 激活前应执行：

```text
schema validation
contract validation
invariant validation
diversity validation
semantic coverage validation
UI journey coverage validation
recipe expansion dry-run
IndexedDB import dry-run
runtime package hash validation
```

失败处理：

- validation error 不得覆盖 active。
- v2 release 写入失败不得切 pointer。
- active pointer 指向坏 release 时 runtime 必须 fallback previous pointer。
- previous pointer 也坏时 fallback v1 previous / bundle default。

## 11. 研究参考与启发

本轮方案参考的外部范式：

- OpenAI Structured Outputs
  - 用 JSON Schema 约束模型输出结构。
  - 启发：结构化输出适合生成 Blueprint，不适合直接自由生成最终业务表。
- JSON Schema Draft 2020-12
  - 适合作为 manifest、slice、blueprint 的基础结构约束。
- SDV / Synthetic Data Vault constraints 和 multi-table metadata
  - 启发：多表合成数据必须显式声明关系、约束和业务规则；约束不是后置装饰，而是生成过程的一部分。
- Faker / seeded generation
  - 启发：人名、组织、时间、地址、编号等基础字段应由 seed-aware deterministic generator 生成，而不是手写模板。
- fast-check / property-based testing
  - 启发：数据质量可以用“性质”验证，例如关系一致、状态流转合法、文本重复度不过高。
- W3C SHACL
  - 启发：跨实体业务图可以用 shape/constraint 思想表达，验证的不只是字段类型，而是关系和语义约束。

## 12. 明确非目标

这些事情不应作为第一阶段目标：

- 不要推翻现有 v1 `active.json`。
- 不要让页面或 MSW 直接解析 v2 manifest/slices。
- 不要把 AI provider、MCP server、API key 打进浏览器 runtime。
- 不要为缺失 DOMC 的模块自由编造精准数据。
- 不要只靠压缩解决文件爆炸。
- 不要一次性要求所有现有模块都完成 DOMC。
- 不要把这个方向做成后端真实数据 seed target；后端 API seed 是未来独立 target。

## 13. 最终一句话

长期方案应从：

```text
生成 active.json 表数据
```

升级为：

```text
生成可验证、可展开、可回滚、可复现的业务场景模型，
再由 MCP/runtime 确定性编译或展开为 IndexedDB 可消费的 demo-offline 数据。
```


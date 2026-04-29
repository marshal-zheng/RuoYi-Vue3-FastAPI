# Demo Offline Runtime Scenario Package 上下文记录

日期：2026-04-29

状态：原始记录（用于后续新开窗口生成正式 spec）

目的：沉淀本轮关于 `demo-offline`、AI Agent + MCP 生成领域化演示数据、运行时外部数据包、业务契约和长期工程范式的关键上下文。本文不是正式 spec，不定义最终任务清单；正式 spec 应基于本文再拆 requirements / design / tasks。

## 1. 已确认的核心目标

用户做的是真实业务系统，不是简单 demo。`demo-offline` 的目标是给客户现场演示真实业务流程，并且尽量不让非技术人员参与源码、Git、build。

理想交付方式：

```text
技术人员预先 build 一个通用 dist-demo-offline 程序壳
  -> 非技术人员拿到离线包目录
  -> 通过 Cursor Agent / Cherry Studio / Claude 等 AI Agent 对接 MCP
  -> MCP 根据一句业务主题生成领域化 demo-offline 数据文件
  -> 现场只启动 HTTP 静态服务
  -> 浏览器访问 index.html
  -> 页面按预期业务流转
```

用户认可的自然语言入口示例：

```text
基于当前 demo-offline 契约，重新全量生成二手电脑回收项目的 official demo-offline 数据，覆盖旧版本，检查通过后激活。
```

用户不应知道也不应输入 `scenarioId`。`scenarioId` 是 MCP / runtime 内部标识，应该从业务主题、现有数据包元信息、topicKey 或 contract registry 推导。

## 2. 当前实现的主要错位点

当前实现大体是：

```text
MCP 生成 src/demo/scenarios/generated/*.ts
  -> 前端 import 这些 TS scenario
  -> yarn build:demo-offline
  -> 数据被编译进 JS bundle
```

这适合“技术人员每次生成后重新 build 一个固定客户离线包”，但不适合“build 后现场按行业主题替换数据”。

本轮确认的关键判断：

```text
原始 offline-demo 目标没错，错位点是领域数据被编译进包里了。
```

如果数据被编译进 JS bundle，则每次 MCP 生成新行业数据都必须重新 build。对于非技术人员现场换数据、售前快速试不同业务主题，这个模型不合适。

## 3. 最佳长期方向

推荐方向：

```text
通用 dist-demo-offline 程序壳
  + 外部 runtime scenario data package
```

“通用”不是没有业务系统，也不是空白 demo，而是：

```text
通用 dist-demo-offline =
  固定的离线演示程序壳
  + 固定的 Vue 页面、路由、组件
  + 固定的 demo-offline runtime
  + 固定的 MSW handlers
  + 固定的 IndexedDB 导入/查询逻辑
  + 固定的 schema 校验逻辑
  + 内置兜底 default scenario
  - 不把客户行业领域数据编译进 JS bundle
```

领域数据由 MCP 在 build 后写到 dist 目录：

```text
dist-demo-offline/
  index.html
  assets/
  demo-scenarios/
    active.json
    active.meta.json
    previous.json
```

前端启动链路：

```text
浏览器访问 dist-demo-offline
  -> app 启动
  -> fetch /demo-scenarios/active.json
  -> 校验 DemoScenarioPackage / contractFingerprint / schemaVersion
  -> 导入 IndexedDB
  -> MSW handler 拦截页面 API
  -> demo service / repository 从 IndexedDB 返回数据
  -> 页面展示领域化业务流转
```

这样只有页面代码、handler、schema、runtime 改动时才需要 rebuild；单纯换行业数据不需要 rebuild。

## 4. MSW 和后端 API MCP 的定位

MSW 不是问题。MSW 仍然是合适的浏览器网络拦截层，适合：

```text
前端页面请求 API
  -> MSW handler 拦截
  -> handler 调 demo service / repository
  -> 从 IndexedDB 读取 scenario data
  -> 返回页面期待的 API 响应
```

但 MSW 不适合作为：

```text
MCP -> 调 MSW 接口 -> 创建 demo 数据
```

因为 MSW 运行在浏览器 / Service Worker 中，不是稳定的后端服务进程。MCP 应写入 runtime scenario data package，MSW 只消费数据。

后端 API MCP 是另一条有价值的 target：

```text
AI Agent -> MCP -> 后端 API/SDK -> 真实数据库
```

例如 Plane 官方 MCP 方向就是封装 Plane SDK/API，服务真实后端业务操作。这对真实系统、dev/staging 数据注入有价值，但它不能替代 pure offline static demo，因为它要求后端、数据库、账号、网络、权限和环境初始化。

长期可以设计两个 target，但 P0 不要混在一起：

```text
统一领域数据生成核心
  -> offline-static target: 写 dist-demo-offline/demo-scenarios/active.json
  -> backend-api target: 调真实后端 API/SDK 创建数据
```

P0 优先 `offline-static target`，因为它直接解决“build 后不重打包也能换领域数据”的目标。

## 5. AI Agent + MCP 的边界

必须坚持：

```text
AI Agent 负责业务语义
本地 MCP/compiler/validator 负责结构正确
```

AI 可以生成：

- 行业阶段
- 业务角色
- 风险点
- 指标名称
- 场景故事线
- 客户可理解的话术

AI 不应该直接写最终大 JSON 并落盘。最终 `active.json` 必须由代码生成、校验、编译、dry-run 后写入。

安全生成流程：

```text
用户一句业务主题
  -> MCP 扫描/读取当前 demo-offline 契约
  -> 生成 contract summary + contractFingerprint
  -> AI 生成领域语义草稿
  -> compiler 生成 DemoScenarioPackage
  -> schema validate
  -> invariant validate
  -> import dry-run
  -> 写 active.next.json
  -> 原子替换 active.json
```

坏数据不能导致程序跑不起来。校验失败时不能覆盖当前 `active.json`。

## 6. 稳定性要求

领域数据要精准稳定，不能每次随机变化。

建议 seed：

```text
seed = hash(topicKey + businessDescription + contractFingerprint + generatorVersion)
```

其中：

- `topicKey`：从自然语言主题归一化得到，例如“二手电脑回收”
- `businessDescription`：用户可选业务描述
- `contractFingerprint`：当前 demo module contract / schema / handler / required fields / invariants 的摘要指纹
- `generatorVersion`：MCP 生成器版本，生成算法变更时显式影响结果

同一业务主题 + 同一 contract + 同一 generatorVersion 应尽量生成相同数据。contract 变了，相关数据才合理变化。

不要通过读取旧 candidate 或旧大 JSON 维持稳定。旧版本历史交给 Git 或业务数据包版本管理，MCP 负责生成当前可运行数据包。

## 7. active / previous / fallback 生命周期

推荐 dist 数据目录：

```text
dist-demo-offline/demo-scenarios/
  active.json        # 当前正式生效数据包
  active.meta.json   # 当前数据包元信息、fingerprint、seed、生成时间、校验结果
  previous.json      # 上一个可运行数据包，用于坏包回退
  active.next.json   # 生成过程临时文件，成功后原子 rename
```

MCP 写入规则：

```text
生成 active.next.json
  -> JSON parse 校验
  -> schemaVersion 校验
  -> validateDemoScenarioPackage
  -> contractFingerprint 兼容校验
  -> project/version/topology/simulation invariants 校验
  -> IndexedDB import dry-run
  -> old active.json 复制为 previous.json
  -> active.next.json 原子替换 active.json
  -> 写 active.meta.json
```

前端加载规则：

```text
尝试 active.json
  -> 成功：导入 IndexedDB 并启动 demo
  -> 失败：尝试 previous.json
  -> previous 失败：使用 bundle 内置 default scenario
```

这保证非技术人员现场生成失败时，程序最多回到旧数据或 default，不应白屏。

## 8. 未知业务复杂性的真实边界

必须明确：没有任何方案能在完全没有契约的情况下精准支持所有未知业务。

能做到的是：

```text
任何新业务只要按规范交付 demo-offline module contract
  -> MCP 就能用同一流程精准生成领域数据
```

没有 contract 的未知模块必须返回 blocker，不能硬编数据。

后续所有业务开发必须把 demo-offline 接入作为 Definition of Done：

```text
业务模块完成 =
  页面/API 完成
  + demo module contract 完成
  + DemoScenarioPackage slice / IndexedDB mapping 完成
  + repository / service 完成
  + MSW handler 覆盖真实页面 API
  + generator adapter 可生成
  + invariants 校验通过
  + demo-offline runtime check 通过
```

## 9. Demo Module Contract 范式

建议后续把当前 `project + version + topology + simulation` 沉淀为第一个显式 contract。

概念名称：

```text
Demo Offline Module Contract
```

简称可用：

```text
DOMC
```

示例形态（正式 spec 可再调整）：

```ts
defineDemoModuleContract({
  module: 'project',
  displayName: '项目管理',
  routes: ['/project', '/project/detail', '/project/topo'],
  entities: {
    projects: {
      primaryKey: 'projectId',
      requiredFields: [
        'projectId',
        'projectName',
        'status',
        'owner',
        'businessStage',
        'riskLevel',
        'updateTime'
      ],
      minimumRecords: 6
    },
    versions: {
      primaryKey: 'versionId',
      requiredFields: [
        'versionId',
        'projectId',
        'versionName',
        'locked',
        'status',
        'updateTime'
      ],
      minimumRecordsPerProject: 1
    },
    topologies: {
      primaryKey: 'id',
      requiredFields: ['id', 'projectId', 'versionId', 'graph', 'updateTime'],
      minimumRecordsPerProject: 1
    }
  },
  handlers: [
    { method: 'GET', path: '/project/list', returns: 'projects' },
    { method: 'GET', path: '/project/version/list', returns: 'versions' },
    { method: 'GET', path: '/project/topology/:projectId', returns: 'topologies' }
  ],
  invariants: [
    'every version references an existing project',
    'every project has at least one version',
    'every topology references an existing project and version',
    'locked version cannot be modified by demo write flows',
    'visible project list contains enough loaded rows for filtering and detail navigation'
  ],
  generator: {
    adapter: 'project-version-topology',
    semanticSlots: ['industryStage', 'ownerRole', 'risk', 'metric', 'region']
  }
});
```

P0 仍以项目和版本做实验，但设计时要保证模块 contract 可扩展到未来未知业务。

## 10. P0 建议范围

P0 只做：

- runtime scenario JSON package
- dist-demo-offline 外部数据目录
- active / previous / fallback
- MCP 写 `active.json` 的 offline-static target
- project / version / topology / simulation 的 contract summary 和 invariants
- 数据包 schema validation
- IndexedDB import dry-run
- 成功原子替换，失败保留现有 active

P0 不做：

- harness
- 后端 API seed target
- 所有未知业务模块
- 完整 DOMC 平台化
- AI 直接写最终 JSON
- 非 HTTP 的 file:// 支持

## 11. P1 / P2 建议方向

P1：

- 把 project/version/topology/simulation 的 contract 正式沉淀为 DOMC
- MCP 扫描 DOMC registry，而不是只扫 `src/demo/**`
- 增加 `contractFingerprint`
- 增加 generator adapter registry
- 新增业务模块必须交付 contract，否则 demo-offline check 失败

P2：

- 增加 backend-api target
- 允许同一领域语义草稿输出到 offline-static 或真实后端 API
- 可对接真实业务 SDK，例如 Plane MCP 类似方式
- 后续再接 harness，harness 只产出页面/接口最小 contract，不负责业务语义

## 12. 外部调研结论

调研参考显示，成熟方案的共识是 contract-as-code / schema-aware generation / validation gate，而不是让 AI 直接自由写 mock 数据。

有参考价值的外部方向：

- GitHub REST API 使用 OpenAPI 作为机器可读契约，用于生成 SDK、文档和测试集成。
  - https://docs.github.com/rest/overview/openapi-description
- TypeSpec 是 Microsoft 推动的 schema-first/API-first 语言，可生成 OpenAPI、client、server code。
  - https://learn.microsoft.com/en-us/azure/developer/typespec/overview
- Prism / Microcks / Specmatic 体现“API spec as executable contract”，从契约生成 mock、做 contract testing、service virtualization。
  - https://stoplight.io/open-source/prism
  - https://microcks.io/
  - https://docs.specmatic.io/contract_driven_development/central_contract_repository.html
- MSW / Storybook 的成熟用法是复用网络层 mock 于开发、测试、演示，而不是把假数据写死在页面。
  - https://mswjs.io/
  - https://storybook.js.org/docs/writing-stories/mocking-data-and-modules/mocking-network-requests
- Schemathesis 证明 schema-aware property-based data generation 能更系统地发现结构和契约问题。
  - https://schemathesis.io/
- Local-first / offline-first 研究强调程序壳和本地数据分离、数据可本地持有、可校验、可迁移。
  - https://www.inkandswitch.com/essay/local-first/

对本项目的落地判断：

```text
不要直接引入 Prism/Microcks/WireMock 替代现有 demo-offline。
应该借鉴 contract-as-code 和 validation gate，
把现有 MSW + IndexedDB + DemoScenarioPackage 投放方式升级为 runtime external data package。
```

## 13. 正式 spec 应回答的问题

新窗口生成 spec 时应重点回答：

1. `dist-demo-offline/demo-scenarios` 的目录和文件契约是什么？
2. `active.json` 和 `active.meta.json` 的 JSON schema 是什么？
3. 前端启动时如何选择 active / previous / default？
4. contractFingerprint 如何计算，哪些输入会影响它？
5. MCP 如何从自然语言主题推导 topicKey 和内部 scenario identity？
6. MCP 如何保证原子写入和失败不覆盖？
7. import dry-run 如何实现，是否需要临时 IndexedDB 名称？
8. project/version/topology/simulation 的 P0 invariants 是哪些？
9. 生成成功后是否仍需要 candidate？如果需要，应是 dist 外的临时文件还是 active.next.json？
10. 非技术人员使用时的最小操作边界是什么？
11. 新业务模块如何按 DOMC 接入，缺失 contract 时如何 blocker？
12. 是否保留源码 generated TS scenario 作为开发 fallback，还是逐步迁移到 runtime JSON？

## 14. 推荐最终结论

长久收益最大的方案：

```text
AI Agent + MCP 作为主入口
  -> contract-as-code 约束可生成业务
  -> AI 生成领域语义
  -> MCP/compiler 生成结构化 DemoScenarioPackage
  -> validator / invariants / dry-run 保证不会弄挂程序
  -> runtime JSON scenario package 投放到 dist-demo-offline
  -> 前端 runtime 加载 active.json，失败 fallback
  -> MSW/IndexedDB 继续作为纯前端离线演示主链路
```

这条方案同时满足：

- 非技术人员不用 git clone 项目
- 只替换指定目录的数据文件，不要求 rebuild
- 数据结构精准稳定
- 业务可以按预期流转
- 坏数据不覆盖现有可运行数据
- 后续未知业务通过 module contract 扩展
- 后续真实后端 API MCP 可作为第二 target 接入，而不是替代 offline-static


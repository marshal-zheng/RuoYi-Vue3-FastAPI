# 行业化演示数据与 demo-offline 接入上下文

日期：2026-04-27

状态：原始记录（用于后续拆分 specs）

目的：记录本轮关于 AI 生成行业化演示数据、现有 MSW/mock/demo-offline 体系接入方式、以及后续必须固化到开发流程中的长期方案。本文不是正式 spec，不定义最终任务清单，只沉淀上下文与决策。

## 1. 核心场景

用户主要通过 Codex / Claude 等 AI 编码工具开发业务功能。很多时候不是“接口还没做完，需要临时 mock”，而是：

- 业务功能已经开发完成
- 前端页面可以使用
- 后端接口已经可用
- demo-offline/MSW 体系也希望可以演示
- 但要面向不同行业客户做洽谈、演示、共创和交付验收

真实痛点不是“有没有假数据”，而是“数据是否贴近客户行业，让客户一眼觉得这是自己的业务”。

同一个项目管理模块，在不同客户行业中应该呈现不同语境：

- 外卖客户：城市运营、商户入驻、骑手运力、履约时效、高峰补贴、活动上线
- 房地产客户：拿地、规划报批、工程施工、预售筹备、开盘营销、交付整改
- 制造客户：订单交付、产线改造、物料齐套、质量追溯、设备维保
- 教育客户：校区筹建、招生转化、课程排期、教师培训、家校服务

字段结构可能一致，但项目名称、负责人、部门、阶段、风险、备注、客户名称、指标和故事线都应该行业化。

## 2. 已澄清的误区

### 2.1 不是 AI mock 平台

目标不是替代 MSW，也不是让 AI 生成 handler。MSW 仍是稳定的网络拦截层，AI 只生成数据资产。

禁止方向：

```text
AI 生成 MSW handler
AI 直接写浏览器 IndexedDB
AI 直接改前端运行时代码
AI 生成一堆不可校验的临时 JSON
```

正确方向：

```text
AI 生成行业化数据草稿
  -> 校验
  -> 编译成 DemoScenarioPackage
  -> 由现有 demo-offline runtime 导入 IndexedDB
  -> 由现有 MSW demo handlers 读取
```

### 2.2 不是 spec 生成器

用户开发时已经会用 Codex/Claude 生成 specs。不要再设计一个“AI 生成 spec”的新流程。

本方案只关注功能完成后的行业化演示数据生产：

```text
已完成业务模块
  -> 行业/客户语境
  -> 行业化演示数据
  -> demo-offline 可运行场景包
```

### 2.3 YAML 不是必需项

`module-profile.yaml` / `industry-profile.yaml` 不是开发门槛，也不是和 MSW 接入的必要条件。

真正必须的是：

```text
生成数据最终能进入 DemoScenarioPackage
DemoScenarioPackage 能被 demo-offline runtime 导入
MSW handler 能从 repository/service/IndexedDB 读到这些数据
```

Profile 只是提高生成质量和复用经验的一种可选形式。它可以是 YAML、JSON、TypeScript、数据库配置，也可以是后续页面表单。第一阶段可以只用一句 brief 生成数据。

## 3. 当前项目已有基础

当前项目已经具备 demo-offline 的关键基础，不应该另起一套 mock 系统。

相关路径：

- `ruoyi-fastapi-frontend/src/mocks/**`
  - 负责传统 MSW fallback、测试 MSW server、handler 组合
  - 适合开发兜底和测试
- `ruoyi-fastapi-frontend/src/demo/**`
  - 负责 demo-offline runtime、IndexedDB、scenario、repository、service、handler
  - 适合无后端静态演示和客户离线包
- `ruoyi-fastapi-frontend/src/demo/scenarios/schema.ts`
  - 定义 `DemoScenarioPackage`
- `ruoyi-fastapi-frontend/src/demo/repositories/scenario.ts`
  - 负责校验和导入场景包到 IndexedDB
- `ruoyi-fastapi-frontend/src/demo/runtime/state.ts`
  - 按 `VITE_DEMO_SCENARIO_ID` 加载场景
- `ruoyi-fastapi-frontend/src/demo/scenarios/index.ts`
  - 当前 scenario 注册入口
- `ruoyi-fastapi-frontend/src/demo/handlers/**`
  - demo-offline 下的 MSW handlers

现有运行模式：

```text
VITE_APP_RUNTIME_MODE=real          -> 不启动 MSW，访问真实后端
VITE_APP_RUNTIME_MODE=fallback      -> 真实后端优先，404/网络异常时 fallback mock
VITE_APP_RUNTIME_MODE=demo-offline  -> 纯前端离线演示，禁止穿透后端
```

行业化演示数据应该优先接入 `demo-offline`。

## 4. 最终方案

最终方案名称建议：

```text
行业化演示数据生产线
```

也可以在英文文档中称为：

```text
Industry Demo Data Pipeline
```

核心定位：

```text
让同一个已完成业务模块，可以快速生成外卖、房地产、制造、教育等行业客户看得懂的数据，并最终进入现有 demo-offline/MSW/IndexedDB 交付链路。
```

总体链路：

```text
业务模块已经完成
  -> 用户输入行业/客户 brief
  -> 可选读取模块字段画像和行业画像
  -> AI 生成行业化数据草稿
  -> validator 校验字段、枚举、数量、关联和占位词
  -> compiler 编译成 DemoScenarioPackage
  -> 注册 scenario
  -> VITE_DEMO_SCENARIO_ID 选择场景
  -> build:demo-offline 产出 dist-demo-offline
```

运行时链路保持不变：

```text
demo-offline runtime
  -> ScenarioRepository 导入 DemoScenarioPackage
  -> IndexedDB 持久化
  -> MSW demo handler 拦截 API
  -> demo service
  -> demo repository
  -> 页面展示行业化数据
```

关键原则：

- AI 只发生在开发机、CLI、内部工具或后端 dev-only 服务中
- AI API key 不能进入浏览器运行时，不能进入客户离线包
- `dist-demo-offline` 必须可以无后端、无数据库、无 AI API key 运行
- 客户现场只消费已经生成好的场景包
- MSW handler 不感知 AI，不读取 profile，不直接写行业逻辑

## 5. 与现有 MSW/demo-offline 的平滑接入

平滑接入的核心不是 YAML，而是 `DemoScenarioPackage`。

AI 生成数据不能直接对接：

```text
src/mocks/handlers/*
src/demo/handlers/*
IndexedDB runtime
页面组件
```

它只能对接：

```text
scenario compiler
```

compiler 的输出必须是：

```text
DemoScenarioPackage
```

然后沿用现有机制：

```text
src/demo/scenarios/generated/food-delivery-project-demo.ts
  -> src/demo/scenarios/index.ts 注册
  -> VITE_DEMO_SCENARIO_ID=food-delivery-project-demo
  -> ScenarioRepository.ensureScenario()
  -> IndexedDB
  -> demo handlers
```

示例命令形态：

```bash
yarn demo-data:generate \
  --module project-management \
  --industry food-delivery \
  --brief "华东区域外卖城市运营，重点演示商户入驻、骑手运力、午高峰履约提升，生成 50 条项目数据" \
  --scenario food-delivery-project-demo
```

本地预览：

```bash
VITE_APP_RUNTIME_MODE=demo-offline \
VITE_DEMO_SCENARIO_ID=food-delivery-project-demo \
yarn dev
```

静态演示包：

```bash
VITE_APP_RUNTIME_MODE=demo-offline \
VITE_DEMO_SCENARIO_ID=food-delivery-project-demo \
yarn build:demo-offline
```

交付形态：

```text
dist-demo-offline-food-delivery/
dist-demo-offline-real-estate/
dist-demo-offline-manufacturing/
```

限制：

- `dist-demo-offline` 仍需 HTTP(S) 静态服务访问，不能直接 `file://` 打开
- 这是 MSW service worker 的运行边界，不是本方案新增限制

## 6. 对 Codex/Claude 开发流程的强制约束

用户主要用 Codex/Claude 做业务开发，所以必须把 demo-offline 接入变成开发交付要求。

以后新增任何有页面/API/列表/表单的业务模块，不应只交付：

```text
前端页面
后端接口
数据库表
接口联调
```

还必须交付：

```text
demo-offline 数据切片
IndexedDB 表或持久化映射
demo repository
demo service
demo MSW handler
默认 seed 数据
scenario compiler adapter
demo-offline smoke 测试
```

硬规则建议：

```text
任何新增业务模块，只要有前端页面和 API，就必须接入 demo-offline：
扩展 DemoScenarioPackage、IndexedDB repository、demo service、MSW handler、默认 seed、场景 compiler，并补 smoke 测试。
```

这样以后 AI 行业化数据就可以统一进入 compiler，而不是每个模块临时找地方塞数据。

## 7. Profile 的真实作用

Profile 不是必须，但长期会有价值。

第一阶段可以无 profile：

```bash
yarn demo-data:generate \
  --module project \
  --industry 房地产 \
  --brief "住宅项目交付、营销开盘、工程整改场景，生成 50 条项目数据"
```

系统可以从现有代码或 compiler adapter 中推断字段：

```text
projectName
owner
status
createTime
remark
```

当生成质量不稳定时，再补 profile：

```text
projectName = 行业化项目名称
owner = 该行业常见岗位负责人
remark = 业务进展或风险说明
status = 必须使用系统枚举
```

Profile 可选形态：

```text
YAML
JSON
TypeScript
数据库配置
内部页面表单
```

推荐演进：

```text
P0：无 profile 也能生成
P1：支持可选 module/industry profile 提升质量
P2：做页面维护 profile，让售前/实施人员不用写配置文件
```

## 8. AI Provider 边界

用户提到的 AI 是 DeepSeek、Kimi、ChatGPT/OpenAI、Gemini 等 API。

建议抽象：

```ts
interface DemoDataAiProvider {
  generateIndustryData(input: DemoDataGenerationRequest): Promise<IndustryDataDraft>;
}
```

原则：

- provider 可替换
- 输出统一成内部 `IndustryDataDraft`
- 不把 provider 原始输出直接当最终数据
- 所有输出必须经过 validator 和 compiler
- API key 只存在于 CLI、内部后端或本地环境变量
- 客户离线包不包含任何 AI 调用能力

第一版不必同时实现所有 provider。可以先实现一个 provider，再保留扩展点。

## 9. Validator 必须覆盖的风险

AI 生成数据必须经过治理，否则会退化成“看起来像，但不能交付”的临时数据。

基础校验：

- JSON 格式合法
- 字段完整
- 类型正确
- 枚举值合法
- 必填字段存在
- 数量满足要求
- ID 唯一
- 关联完整性正确

行业质量校验：

- 禁止“测试项目 1”“示例数据”“张三”“李四”等占位词
- 名称必须贴近目标行业
- 负责人、部门、角色必须符合行业语境
- 风险、备注、进展说明必须有业务含义
- 不同行记录之间不能高度重复

demo-offline 校验：

- 能编译成 `DemoScenarioPackage`
- 能通过 `validateDemoScenarioPackage`
- 能导入 IndexedDB
- 列表接口能返回数据
- 详情/新增/编辑/删除等核心接口能跑
- 未覆盖接口返回明确 `DEMO_API_NOT_IMPLEMENTED`

## 10. 内部页面化方向

后续可以做 `Scenario Workbench`，但它应该是内部工具，不是客户离线包的一部分。

内部页面能力：

- 选择模块
- 选择行业
- 填写客户语境
- 选择生成数量
- 选择 AI provider
- 点击生成
- 预览数据
- 运行校验
- 导出 `DemoScenarioPackage`
- 注册 scenario
- 触发或提示 `build:demo-offline`

客户离线包能力：

- 不调用 AI
- 不配置 API key
- 只切换已内置 scenario
- 可以展示当前场景名称、版本和导入状态

如果后续要支持离线包内切换多个行业场景，可以基于现有 `ScenarioRepository.switchScenario()` 扩展场景切换 UI。

## 11. 开源调研结论

已调研到的相关方向，没有一个完整覆盖本项目场景，但可以借鉴做法。

### 11.1 Metabase dataset-generator

项目：[metabase/dataset-generator](https://github.com/metabase/dataset-generator)

启发：

- 不让 LLM 直接吐最终海量数据
- 先让 LLM 生成 dataset spec、业务规则和字段含义
- 再用本地 generator/Faker 稳定生成数据
- 新业务类型需要补业务指令、范围和校验规则

对本项目的启发：

```text
AI 负责行业语义和生成规则
程序负责稳定批量造数、校验和编译
```

### 11.2 MOSTLY AI mostlyai-mock

项目：[mostly-ai/mostlyai-mock](https://github.com/mostly-ai/mostlyai-mock)

启发：

- 支持按表、字段、类型、规则、上下文生成数据
- 字段 prompt 很重要

对本项目的启发：

```text
projectName 不能只是 string
必须知道它是“贴近目标行业的项目名称”
```

### 11.3 msw-auto-mock / Prism / Mockoon

项目：

- [msw-auto-mock](https://github.com/zoubingwu/msw-auto-mock)
- [Stoplight Prism](https://stoplight.io/open-source/prism)
- [Mockoon](https://github.com/mockoon/mockoon)

启发：

- 从 API contract 生成 mock 是成熟方向
- Faker 和模板可以解决一部分动态数据
- 但它们更偏“接口未完成时的 mock”，不是“行业化客户演示数据”

对本项目的启发：

```text
不要改 MSW handler 生成方式
应该保持 contract 稳定，只替换数据来源和场景包
```

### 11.4 MSW / Storybook / @msw/data

参考：

- [MSW](https://github.com/mswjs/msw)
- [Storybook mocking network requests](https://storybook.js.org/docs/writing-stories/mocking-data-and-modules/mocking-network-requests)
- [@msw/data](https://github.com/mswjs/data)

启发：

- 网络层 mock 不应污染应用代码
- Story/场景级别的数据切换是常见做法
- 数据层和 handler 分离是正确方向

对本项目的启发：

```text
现有 src/demo/** + IndexedDB + DemoScenarioPackage 方向是对的
不需要另建一套 AI mock runtime
```

### 11.5 Neosync

项目：[nucleuscloud/neosync](https://github.com/nucleuscloud/neosync)

启发：

- 对已有生产数据做脱敏、同步和 synthetic data
- 强调 schema、引用完整性和低环境 seed

对本项目的启发：

```text
如果客户能提供样例数据，未来可走“脱敏真实样本 + AI 扩展”的增强路线
但售前阶段通常没有真实客户数据，所以不能把它作为第一依赖
```

## 12. 后续建议拆分的 specs

建议拆成 3 个核心 specs，避免一次做成过大的平台。

### 12.1 demo-offline-module-contract

目标：把“新增业务模块必须接入 demo-offline”变成开发契约。

应覆盖：

- `DemoScenarioPackage` 如何扩展模块数据切片
- IndexedDB 表和序列如何扩展
- demo repository/service/handler 的标准分层
- 默认 seed 数据要求
- scenario compiler adapter 的模块接入口
- smoke 测试要求
- 未覆盖接口的 `DEMO_API_NOT_IMPLEMENTED` 行为

这是最重要的基础 spec。没有它，AI 生成的数据没有稳定落点。

### 12.2 industry-demo-data-generator

目标：定义 AI 行业化数据生成器。

应覆盖：

- CLI 命令形态
- provider 抽象
- API key 边界
- 输入 brief
- 可选 profile
- AI 输出草稿结构
- validator 规则
- 占位词治理
- 行业语义质量检查
- 失败重试和人工修正流程

注意：第一版可以只支持一个 provider，但必须保留 provider 抽象。

### 12.3 scenario-compiler-and-packaging

目标：定义生成数据如何编译、注册、切换并打包成 demo-offline 静态产物。

应覆盖：

- `IndustryDataDraft -> DemoScenarioPackage` 编译流程
- `src/demo/scenarios/generated/*` 生成规范
- `src/demo/scenarios/index.ts` 注册策略
- `VITE_DEMO_SCENARIO_ID` 切换方式
- `build:demo-offline` 产物命名
- 多行业包输出
- 产物验证
- 场景 fingerprint/version 规则

### 12.4 scenario-workbench（可选后置）

目标：内部页面化工具，降低售前/实施人员使用门槛。

应覆盖：

- 模块/行业/brief 表单
- provider 选择
- 生成进度
- 数据预览
- 校验报告
- 导出/注册场景
- 触发打包或生成打包说明

注意：这是后置增强，不是第一阶段必须项。

## 13. 推荐实施顺序

推荐顺序：

```text
P0：demo-offline-module-contract
P1：scenario-compiler-and-packaging
P2：industry-demo-data-generator
P3：scenario-workbench
```

原因：

- 先确保每个业务模块都有 demo-offline 数据落点
- 再确保行业化数据能编译成现有场景包
- 然后再接 AI provider
- 最后才做页面化

如果先做 AI，会生成很多看似有趣但无法稳定导入和交付的数据。

## 14. 最终定案

最终定案如下：

```text
本项目不做独立 AI mock 平台。
本项目要做行业化演示数据生产线。
AI 只负责生成行业化数据草稿。
所有数据必须经过校验和 compiler。
compiler 的唯一正式运行时出口是 DemoScenarioPackage。
demo-offline/MSW/IndexedDB 仍是演示运行时主链路。
Codex/Claude 开发任何新业务模块时，必须同步交付 demo-offline 数据切片、默认 seed 和 compiler adapter。
YAML/profile 不是必需项，只是后期提升质量和沉淀经验的可选工具。
```

这套方案的长期收益是：

```text
同一个业务模块可以快速换行业语境。
同一套演示数据可以用于售前洽谈、开发验证、QA 回归和离线交付。
AI 生成能力不会污染运行时。
现有 MSW/demo-offline 投资继续复用。
```

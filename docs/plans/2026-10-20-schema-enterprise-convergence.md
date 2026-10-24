# Schema Enterprise Convergence Implementation Plan

**Goal:** 优先完成 ZXUI schema package 的代码定义与复杂编辑公共能力优化，以 RuoYi 与 DAG 为业务实验场，保持每个宿主唯一的编辑值所有权。
**Inputs:** [评估报告](../reports/schema-package-enterprise-assessment-2026-10-20.md)、本会话已确认的架构方案与执行授权。
**Scope Boundaries:** 包括错误生命周期、类型、嵌套路径与数组身份、复杂字段接入、异步与提交阻断、权威保存值、布局和无障碍、DAG 契约、真实业务迁移、规模和交付验证、AI 效率对照。排除设计器、动态发布平台、多引擎框架、协作系统、仿真页面、外部发布及无关工作区改动。
**Assumptions:** 在现有工作区中实施；不提交或推送；不使用 computer use 或浏览器自动化。保留已有改动，只对受影响契约做完整迁移。没有实际测量的 AI/token 收益不作结论。

**Scope clarification (2026-10-20):** 用户明确 RuoYi 与 Vue Flow 只是实验场。主要交付属于 ZXUI schema package；不要求整页迁移用户/协议或重写领域逻辑。消费者只作新公开契约所必需的迁移，复杂业务结构用真实调用和字段作为验证依据。

## Architecture Contract

- 保留根入口、`/fields`、`/form-create`。CRUD 继续采用 FormCreate 原生 Rule，公共字段不引入另一份 values。
- FormCreate 管可写表单值与客户端校验；DAG 管 draft、raw、history、commit；Dashboard 管配置、预览和持久化。业务管 API、DTO、权限、记录身份和冲突决策。
- 编辑值类型贯穿 initial/read/save/saved；代码组件注册与 JSON 导入白名单分离。
- 错误属于产生错误的会话；引擎字段错误是受控投影，保留作者配置。reset、记录替换、成功保存、卸载清理一致。
- 嵌套错误使用分段路径；数组身份独立于索引。服务端位置错误以提交快照定位，无法可靠对应的错误保留为可见摘要。
- 复合字段以受控值、消息、focus、pending/blocking 接入既有宿主；阻断覆盖中央提交入口。选项刷新不自动等同于禁止提交。
- 成功结果允许可选的权威编辑值；接纳时同时更新引擎和保存基线。只返回成功的 API 不被强迫额外 GET。
- 记录资源与单次提交的取消生命周期分开；过期结果不得写入当前记录。
- 隐藏、删除、缺省、null 与忽略提交保持明确语义，复用引擎能力，不创建第二套联动 DSL。
- FormCreate 若必须长期使用私有 API 才能支持核心语义，先报告证据并重新选型，不靠业务补丁掩盖。

## Task List

### Task 1: Record baseline and preserve existing work

**Files:**
- Read: 三仓库 `AGENTS.md`、相关 package manifest、当前真实消费者。
- Create: `docs/reports/evidence/schema-enterprise-convergence-2026-10-20/baseline.json`

**Steps:**
1. 记录各仓库 HEAD、当前相关文件状态和内容指纹。
2. 核对已有测试、源码直连、构建与打包入口。
3. 确认真实用户编辑和协议字段明细的调用链。

**Verification:**
- Run: `git status --short -- <affected-paths>`（各仓库）。
- Expect: 本轮开始前的改动有清晰记录；不回退已有内容。

**Dependencies:**
无。

**Output:**
基线清单及确定的改动边界。

### Task 2: Make FormCreate session and types reliable

**Files:**
- Modify: ZXUI `packages/schema-form/src/session.ts`
- Modify: ZXUI `packages/schema-form/src/SchemaForm.vue`
- Modify: ZXUI `packages/schema-form/src/form-create/types.ts`
- Modify: ZXUI `packages/schema-form/src/form-create/index.ts`
- Modify: ZXUI `packages/schema-form/src/types.ts`、`src/definition.ts`、`src/zxui/index.ts`
- Test: ZXUI `packages/schema-form/__tests__/session.test.ts`

**Steps:**
1. 用必要回归复现错误 reset 残留及 wrap 覆盖。
2. 实现有所有权的错误投影和清理。
3. 贯通编辑值泛型、机器状态、可选权威保存结果。
4. 分开记录资源和提交请求的取消范围，守住记录和提交代次。
5. 分开代码 bindings 与 JSON 导入准入。

**Verification:**
- Run: `pnpm -C packages/schema-form test`
- Run: `pnpm -C packages/schema-form typecheck`
- Expect: 必要回归由失败转为通过；旧接口真实调用同步迁移。

**Dependencies:**
Task 1。

**Output:**
可靠的表单会话与类型契约。

### Task 3: Complete nested addressing and composite field contracts

**Files:**
- Create/Modify: ZXUI `packages/schema-form/src/form-create/` 下的路径与错误适配模块。
- Modify: ZXUI `packages/schema-form/src/fields/types.ts`、`fields/Field.vue`、`fields/index.ts`
- Modify: ZXUI `packages/schema-form/src/SchemaForm.vue`、`src/style.css`
- Test: 既有包测试与 `docs/research/schema-form-pilot/pilot/pilot.test.ts`

**Steps:**
1. 通过原生 group/subForm API 定位嵌套字段。
2. 建立稳定行身份与提交快照错误映射，处理移动、删除及无法归属的错误。
3. 接入复合字段阻断、异步状态和 focus，中央提交入口统一检查。
4. 接通 columns/整行布局；增加复合组标签、帮助及错误关联语义。
5. 明确隐藏、缺省、null、删除与提交行为。

**Verification:**
- Run: `pnpm -C packages/schema-form test`
- Run: `pnpm -C packages/schema-form typecheck`
- Run: `node docs/research/schema-form-pilot/pilot/run.mjs test`
- Expect: 真实引擎下错误、值、身份、提交保持一致；只补关键边界回归。

**Dependencies:**
Task 2。

**Output:**
嵌套数据与复合字段的最小稳定公共契约。

### Task 4: Open DAG field extension and converge its public contract

**Files:**
- Modify: DAG `packages/dag/src/zxui/contract.ts`、`DagSchemaFields.vue`、`DagSchemaField.vue`、`useFieldEditor.ts`、入口。
- Modify: DAG `packages/dag/src/contracts/capabilities/authoring/contract.ts` 及受影响真实调用。
- Modify: DAG 对应官方示例与中英文文档。

**Steps:**
1. 开放有类型的逐字段扩展，包含嵌套字段。
2. 将复杂字段的编辑状态接入现有 raw/blocker/commit owner。
3. 保持 history、stale 和数组编辑状态映射。
4. 收窄未实现的多选策略，同步真实调用和文档。
5. 消费公共组语义及一个真实复用字段。

**Verification:**
- Run: `pnpm exec eslint <changed-dag-and-docs-source-paths>`
- Run: `pnpm -C packages/dag build`
- Run: `pnpm --dir docs check:examples-i18n`（修改官方示例时）。
- Expect: 构建和公共契约检查通过；按图仓库规则不新增或运行未授权测试，不使用浏览器自动化。

**Dependencies:**
Task 1；公共字段接入依赖 Task 3 的契约。

**Output:**
可局部替换的 DAG 字段及与实现一致的公开契约。

### Task 5: Validate package contracts with minimal RuoYi integration

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/views/system/post/components/PostDlg.vue`、`post-form.ts`（契约迁移需要时）。
- Modify: `ruoyi-fastapi-frontend/src/components/ui/FormDialog/index.ts`
- Inspect: `ruoyi-fastapi-frontend/src/views/system/user/components/UserFormDialog.vue`
- Inspect: `ruoyi-fastapi-frontend/src/components/business/Protocol/ProtocolFormDrawer.vue` 及其实际模板字段编辑器。
- Modify: ZXUI 既有 protocol/inspection pilot（按真实业务结构验证公共接入）。
- Maintain: `ruoyi-fastapi-frontend/tests/unit/components/PostSaveFeedback.test.ts` 及相关布局/领域契约回归。

**Steps:**
1. 完成岗位对新错误路径、类型及布局契约的最小迁移。
2. 以真实用户关系字段和协议明细结构检查库的能力，不重写现有业务查询/领域模板。
3. 使用同一受控 JSON 编辑字段在 CRUD 适配和 DAG 中验证原始输入、阻断及错误接入。
4. 在既有协议/巡检 pilot 验证复合字段与嵌套明细，明确业务 API 与替身服务的验证边界。
5. 更新受影响契约回归；不能将 pilot 冒称为真实页面浏览器验收。

**Verification:**
- Run: `yarn test:run tests/unit/components/PostSaveFeedback.test.ts`
- Run: `yarn type-check`
- Run: `yarn ui:standards`
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod`
- Expect: 原有业务行为保留，源码构建消费新契约；失败明确区分本轮与基线。

**Dependencies:**
Tasks 2、3；跨域复用依赖 Task 4。

**Output:**
真实消费者的公开契约迁移，以及基于真实业务结构的库能力验证。

### Task 6: Verify distribution, scale and schema authoring efficiency

**Files:**
- Modify: ZXUI `packages/schema-form/README.md`、既有 pilot 示例与受影响文档。
- Modify: 必要的消费者 schema 包依赖与锁文件（仅同步本地产物，不发布）。
- Create: `docs/reports/schema-enterprise-convergence-2026-10-20.md`
- Create: `docs/reports/evidence/schema-enterprise-convergence-2026-10-20/` 下的验证记录。

**Steps:**
1. 构建 schema 产物并检查三个入口、类型、CSS 和 peer 外置。
2. 在源码直连之外验证本地打包消费者，生成产物只通过其构建脚本更新。
3. 复测真实规模下编辑、校验和错误定位；区分内存测量与浏览器表现。
4. 提供普通 CRUD、复杂字段、嵌套明细三个可运行入口，详细语义集中在包文档。
5. 对固定 schema 编写任务做有边界的前后对照；仅在可获得真实模型用量时记录 token，代理指标与 token 分开报告。
6. 逐项审查计划覆盖和代码质量，修复发现的问题，再更新完成状态。

**Verification:**
- Run: `pnpm -C packages/schema-form build`
- Run: `pnpm -C packages/schema-form typecheck`
- Run: `pnpm -C packages/schema-form test`
- Run: `node docs/research/schema-form-pilot/pilot/run.mjs test`
- Run: RuoYi 受影响测试、检查和源码构建；DAG lint/build。
- Expect: 报告包括准确命令、结果、限制、未验证项及 AI 对照结论，不把未测量收益写成已证实。

**Dependencies:**
Tasks 2–5。

**Output:**
完整交付、证据与范围明确的推广结论。

## Progress

- [x] Task 1 — baseline（相关文件快照与 SHA 已保存）
- [x] Task 2 — FormCreate session and types（二次复审后 19 项包回归、泛型检查与声明构建通过）
- [x] Task 3 — nested data and composite fields（源码/产物集成链通过；路径、行身份、阻断、焦点与布局已收敛）
- [x] Task 3 无障碍依赖闭环 — ZXUI 自有数值渲染边界接通实际 input；组件 10/10、pilot 14/14、stock EP 消费的真实 tarball 与类型验证通过，tooltip 不再覆盖业务描述；SSR ID 与读屏验收边界见[闭环报告](../reports/schema-aria-ai-closeout-2026-10-20.md)。
- [x] Task 4 — DAG adapter（扩展接口、类型收窄、lint/build/parity/i18n 通过）
- [x] Task 5 — RuoYi consumers（仅最小接入；98 项回归、规范、类型和源码构建通过）
- [x] Task 6 — distribution, scale, examples and review（工程交付与规模记录完成，第二轮复审修复见下）
- [x] Task 6.5 — 有效 AI/token 对照（同模型 xhigh、ABBA 四次真实生成；两版均 2/2 首次质量通过，无修补/重试。新版总 token 均值 +5.22%，不支持节省声明；完整协议、原始记录、评估器纠正与限制见[闭环报告](../reports/schema-aria-ai-closeout-2026-10-20.md)）

## Verification Boundaries

自动化验证使用源代码、真实引擎内存/模拟 DOM、构建和本地打包消费。屏幕阅读器体验、浏览器帧率与人工交互不在禁止 computer use 时冒领为通过。若实际发现缺失的关键业务信息，先推进独立任务并把具体差异记录在本计划，不静默缩减目标。

## Delivery

完整结果与限制见[初次交付报告](../reports/schema-enterprise-convergence-2026-10-20.md)、[二次审查](../reports/schema-enterprise-review-2026-10-20.md)与[最终两项闭环报告](../reports/schema-aria-ai-closeout-2026-10-20.md)。工程实现与有效 AI/token 对照已完成；当前普通 CRUD 样本没有证明节省 token，不把测量完成等同于节省目标达成。未使用 computer use、未发布 npm、未提交或推送。


## Second review (2026-10-20)

再次按任务和架构契约核对，未把已有勾选当作完成证据。修复响应式配置复制、原生初始化基线、动态无包装错误投影、上传取消退休、JSON 枚举准入、安装包示例链接和声明构建失败门禁。方案继续复用 FormCreate 公开生命周期/computed，保留单一编辑值 owner；未引入规则同步框架或新的业务迁移。

本轮结果、逐项覆盖、独立审查及新产物验证见 [二次审查报告](../reports/schema-enterprise-review-2026-10-20.md)。AI/token 有效对照保持未完成；此前实验失败不算已证实节省。真实浏览器、读屏与生产网络验收仍在明确的验证边界外。


## Final closure (2026-10-20)

在 ZXUI 内建立数值输入的稳定属性通路，不使用业务补丁；组件 10/10、pilot 14/14、未打补丁 EP 消费的实际 tarball/类型及 RuoYi 源码构建通过。AI 对照使用同模型与设置进行 ABBA 四次首次生成，两版各 2/2 通过；原始记录和两项评估器纠正保留。新版平均总 token 增加 5.22%，仅能确认测量已完成，不能宣称稳定省 token。后续优化优先针对按任务读取的权威作者入口，不扩展运行时架构。

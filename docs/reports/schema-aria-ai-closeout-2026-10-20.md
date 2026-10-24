# Schema 剩余事项闭环：数值 ARIA 与 AI/token 对照

日期：2026-10-20。两项已闭环：ZxInputNumber 的错误 ARIA 通路已修复，有效 AI/token 对照已完成；本次实测不支持节省 token 的声明。承接[二次审查](./schema-enterprise-review-2026-10-20.md)与[实施计划](../plans/2026-10-20-schema-enterprise-convergence.md)。本轮修复主目标在 ZXUI；没有修改 RuoYi 或图业务代码，没有发布或提交。

## 数值组件修复

原缺陷已在 `ZxInputNumber` 修复。调用方原本传入的 `aria-invalid`、`aria-describedby`、`aria-labelledby`、`aria-errormessage` 现在进入实际输入框，更新与移除同步生效。tooltip 的描述与业务错误 ID 合并、去重，关闭提示不会删除业务错误关联。spinbutton 的值、范围与禁用状态声明式更新；编辑草稿中的合法数值也更新 `aria-valuenow`。

### 为什么选择这个边界

Element Plus 2.13 的 `ElInputNumber` 没有公开的内部输入属性通路；它作为 ZXUI 的 peer dependency 外置，根工作区 pnpm patch 不会自动随包交付给其他业务。只改业务规则、补 DOM 查询或劫持内部渲染，不能形成可靠公共契约。

因此 ZXUI 拥有内部数值控件的渲染与属性路由；数值算法基于 Element Plus 2.13 MIT 源码，继续复用公开 `ElInput`、表单 hooks、locale/namespace 和长按指令。外壳继续负责 tooltip 与公开事件。内部 `nativeAttrs` 仅用于保护输入属性不被 tooltip 的 trigger clone 覆盖，不增加消费者配置。公共 props 显式列出已实现能力，避免 peer 升级自动承诺尚未实现的新行为。

收益是所有后续消费者共享可测试、可分发的输入通路；代价是 ZXUI 需要维护数值内核与上游的差异。没有引入新依赖、第二套表单状态、通用适配框架或兼容模式。完整 MIT 许可与来源保留在代码及产物。

实现：[内部控件](/Users/hqz/Downloads/element-plus/packages/components/input-number/src/number-control.vue)、[组件边界](/Users/hqz/Downloads/element-plus/packages/components/input-number/src/input-number-core.vue)、[公开契约](/Users/hqz/Downloads/element-plus/docs/zh-CN/component/input-number.md)。设计核对了 [WAI spinbutton 语义](https://www.w3.org/WAI/ARIA/apg/patterns/spinbutton/) 与 [Element Plus 2.13 源码](https://github.com/element-plus/element-plus/blob/2.13.0/packages/components/input-number/src/input-number.vue)。

### 验证与边界

- 原实现的新增回归有 6 项失败；修复后组件 10/10 通过。包含实际输入属性、增删更新、真实主题宿主下 tooltip 显示/关闭、SSR、键盘与范围、清空、focus/blur、Form/Provider。
- 巡检 pilot 14/14 通过；对已有稳定行身份回归增加数值字段分支，验证服务端错误、移动后定位、焦点及修正后的清除。
- ZXUI 模块、全量、声明构建、隔离 pilot 类型、精准 lint/格式检查通过。
- RuoYi 源码直连构建通过，岗位既有 5 项回归通过。图仓没有实际 ZxInputNumber 消费者，本轮未运行图仓测试或进行无关迁移。
- 真实 tarball 配合未打补丁的 EP 2.13，公开 CJS 与 ES SSR bundler 入口均通过属性、步进、边界、禁用及 SSR 验证；同环境原生 EP 重现旧问题。公共声明拒绝错误模型、未实现的新 prop 和内部 nativeAttrs。ES/CJS 与四种全量 bundle 均保留 MIT 许可。证据见 [artifact-validation.json](./evidence/schema-aria-ai-closeout-2026-10-20/artifact-validation.json)。本地包 SHA256：`a6481059e23e4f9661e70a1dadecfbb2eb1d28e967c94de7aaabf8a398950664`。
- 没有 computer use、浏览器或读屏验收。模拟 DOM 与 SSR 的结果不等于完整无障碍认证。
- 原生对照确认 EP 2.13 的 input ID 在 mounted 才建立，显式 ID 的 SSR 标签关联不在本次闭环中；本轮 SSR 保证所测 ARIA 属性、错误描述与 name。相邻 Provider/Form 的模拟 DOM 卸载异常也可由原生 EP 重现，测试使用普通布局 div 保留真实继承与标签断言，没有生产补丁。

命令与日志见 [verification.json](./evidence/schema-aria-ai-closeout-2026-10-20/verification.json)，上游边界见 [原生对照](./evidence/schema-aria-ai-closeout-2026-10-20/aria-upstream-probes.json)。

## AI/token 实验

四次正式生成均已完成并返回真实 usage。**本次没有验证出 token 节省：新版平均总 token 为 21,650.5，旧版为 20,575.5，增加 1,075（约 5.22%）。** 这是普通 CRUD、全量公开作者材料和本次模型设置下的结果，不能推广为所有 schema 业务的效率结论。

| 首次生成 | 输入 token | 输出 token（含推理） | 其中推理 token | 总 token | 用时（秒） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 旧版 A1 | 15,571 | 5,611 | 4,142 | 21,182 | 171.176 |
| 新版 B1 | 17,320 | 3,706 | 2,225 | 21,026 | 113.874 |
| 新版 B2 | 17,318 | 4,957 | 3,462 | 22,275 | 148.996 |
| 旧版 A2 | 15,569 | 4,400 | 2,900 | 19,969 | 139.743 |
| 旧版均值 | 15,570 | 5,005.5 | 3,521 | 20,575.5 | 155.460 |
| 新版均值 | 17,319 | 4,331.5 | 2,843.5 | 21,650.5 | 131.435 |

- 新版每次输入均多 1,749 token，符合完整 README 与公共类型上下文变长的事实。输入包括客户端共同上下文，不能用 README 字节数替代它。
- 第一对新版少 156 token，第二对多 2,306 token；用时差分别为 −57.302 秒、+9.253 秒。均值用时较短也不足以证明稳定加速。
- 输出均值减少主要来自推理；非推理输出均值旧版 1,484.5、新版 1,488，基本相同。没有证据把结果解释成生成代码显著缩短。
- 四次 cached input 与 cache write 均为 0，uncached input 等于 input。总量按 input + output 计算，推理不重复相加。
- 正式实验共消耗 84,452 token（65,778 输入 + 18,674 输出），不含先前最小 CLI smoke、当前会话或子代理用量；没有推算未知账户费用。

**质量结果：旧版 2/2、新版 2/2 首次通过；四份均通过统一修正版的 30 项检查及人工审查，没有修改生成代码，没有模型重试。** 因此本次既没有观察到首轮成功率提升，也没有总 token 节省。见 [质量汇总](./evidence/schema-aria-ai-closeout-2026-10-20/ai-authoring/quality-summary.json)。

原始 usage、逐对差值和审计见 [usage-summary.json](./evidence/schema-aria-ai-closeout-2026-10-20/ai-authoring/usage-summary.json)。

使用同一普通岗位 CRUD 任务、同一模型 `gpt-6-astra`、同一推理强度 `xhigh`、同一客户端，按旧/新/新/旧串行生成。每次独立空目录，禁止工具；两版分别使用各自完整 README 与相同规则提取的公共类型。两版共有能力才进入任务，旧版可使用原生布局及宽值类型的合法收窄。

评分器在正式输出前冻结，使用各版真实发行声明，检查类型、DTO 白名单、身份、无效值、服务端错误、signal、原生校验及组件动作/布局。合法手写 oracle 两版均 30/30，错误 oracle 被正确拒绝。生成代码不人工修补、不补跑、不挑结果；最后逐份人工核对单一编辑值所有权和实际请求行为。

CLI 的预检 feature warning 被原 runner 过宽的分类器当成非消息 item。原记录保留；[补充协议](./evidence/schema-aria-ai-closeout-2026-10-20/ai-authoring/protocol-amendment-1.json)按真实时间冻结，仅统一豁免启动前完全相同的这条客户端告警。它不是模型工具调用，不改变质量要求或允许其他错误。

首次评分还发现一个评估器缺陷：ElCol 的 `md:12` 在更宽断点继续生效，旧评分器错误回退到 `span:24`。修正版仅更正断点累积判断，保留原评分与冻结文件，统一重评全部样本；合法、错误及 md-only oracle 均复核。未修改任何生成代码或其它质量条件。

完整实验结果见 [results.md](./evidence/schema-aria-ai-closeout-2026-10-20/ai-authoring/results.md)。协议、输入和评分器见 [实验目录](./evidence/schema-aria-ai-closeout-2026-10-20/ai-authoring/protocol.md)。整份 README 的比较包含当前文档体量，不能把差值全部归因于 API；两个重复样本只支持这个任务的局部结果，不足以证明复杂业务或总体生产率收益。


## 对长期方案的影响

这轮完成的是输入公共契约修复和可信测量，不能将“做了类型与架构优化”直接等同于“AI 更省 token”。后续 AI 优化应优先解决已观察到的上下文成本，同时守住已有的复杂业务能力。

| 优先级 | 下一步优化方向 | 预期收益与验证要求 |
| --- | --- | --- |
| P1 | 在同一权威文档源中提供按任务读取的作者入口：普通 CRUD、复合字段、嵌套明细分别指向相关类型和已验证示例；完整参考继续保留 | 减少普通任务读取无关能力的输入量，避免维护多份失同步说明。需对任务检索流程重新测量后才能承诺 token 降幅；本轮未把这个建议冒称为已实现收益 |
| P1 | 复用这次冻结任务、版本声明检查和原始 usage 记录，在真正改动作者入口后做匹配对照 | 让质量、上下文成本和随机波动可见，避免以字节数、单次输出或社区普遍结论替代本包证据 |
| P2 | 遇到真实复杂业务再增加相应作者任务，例如复合字段阻断、嵌套服务端错误与稳定行身份 | 验证 schema 的主要通用能力能否降低端到端返工成本；旧版无法表达的任务应比较等价手写方案，不能制造不公平的前后对照 |

当前没有证据要求继续扩大运行时抽象、增加 Schema DSL、缓存或调度层。复杂业务能力与 ARIA 修复的工程收益成立；AI/token 节省仍是待进一步优化和验证的目标。

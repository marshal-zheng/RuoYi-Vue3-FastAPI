# ZXUI schema 优化交付报告

日期：2026-10-20。主交付是 `/Users/hqz/Downloads/element-plus/packages/schema-form`，RuoYi 与图仓仅作消费者和业务实验场。依据 [实施计划](../plans/2026-10-20-schema-enterprise-convergence.md) 执行；没有批量迁移用户/协议页面，没有创建另一套 Schema DSL，也没有发布 npm。

## 方案及优先级收益

保留三层边界：纯 JSON 值工具、无引擎的公共字段、可选 FormCreate CRUD 会话。FormCreate 仍独占 CRUD 编辑值；DAG 保留 draft/raw/history/commit；业务保留 DTO、身份、权限、API 和冲突决策。改动集中在公共契约与真实缺陷，收益来自后续业务不再各自处理同样的边界，而不是增加抽象层数。

| 优先级 | 已实现优化 | 长期收益 | 代价与边界 |
| --- | --- | --- | --- |
| P1 | 服务端错误独立管理；保留作者 wrap；reset/成功/销毁清理；隐藏错误可见摘要 | 消除残留错误、覆盖布局、隐藏后无法纠正等跨业务问题 | 与固定 FormCreate 公开 API 适配，升级仍需回归 |
| P1 | 分段 FieldPath、原生 group/subForm 定位、arrayKeys 按提交快照锚定行身份 | 主从表移动/删除后错误不串行；复合控件获得相对错误路径 | 业务声明稳定 key；不确定的映射回摘要，不猜对应行 |
| P1 | 复合字段统一受控值、messages、focus/validate、edit-state | 关系选择、上传、JSON/表达式等控件可以复用同一接入契约 | 控件仍负责自己的领域 UI、raw 与资源取消 |
| P1 | 中央提交检查 blocking；pending 与阻断分开；异步边界检查记录、编辑和控件身份 | 防止保存上一个合法值、防止绕过新控件校验、防止迟到结果污染当前编辑 | 取消客户端结果不等于撤销后端已完成的写入 |
| P2 | Save/BusinessContext/ref 编辑值泛型、phase、可选权威值回填 | 类型贯穿编写与调用；支持保存后继续编辑；减少业务自建基线同步 | 原生 Rule 的全部 props 未复制为另一套类型体系；DTO 转换仍归业务 |
| P2 | 记录资源 signal 与单次提交 signal 分开 | reset 不再意外杀死只初始化一次的字典资源 | 记录更换必须换组件 key；字段资源在卸载清理 |
| P2 | columns/fullWidth 接通原生布局；ZxField group 使用 fieldset/legend | 同一业务布局策略覆盖 Schema；对象/数组组有正确标签语义 | 读屏体验和真实浏览器响应式仍需人工验收 |
| P2 | 代码 bindings 与 JSON 导入 policy 分开；加入公共 JSON 文本控件及可运行 recipe | 代码作者无需维护无关白名单；raw/canonical 的正确做法可直接复用 | JSON 导入仍为受限 profile，不是动态发布平台 |
| P2 | DAG renderField 递归扩展、相对消息、完整 edit-state 快照、过期回调过滤 | 实验场能替换一个复杂字段，保留领域历史、提交和其他默认字段 | 不把 DAG 编辑事务迁入 schema 包 |
| P2 | 收窄 DAG 未实现的多选策略、源码与产物双链验证、规模探针 | 契约与能力一致，减少跨仓接入和发行漂移 | 本轮使用本地快照；未执行外部发布 |

## 本次真实发现并解决的库问题

除原评估的 reset 残留与 wrap 覆盖外，集成和交叉审查还定位了这些问题：

- FormCreate 嵌套数组更新可能只有顶层快照变化，子表单仍保留旧值。运行时规则按官方 Vue 响应式模式实例化，使原生子表单同步；未使用引擎私有 API。
- 提交失败后控件还处于禁用状态就聚焦，导致错误焦点无效。现在解除 pending、完成 Vue 更新后再定位。
- 复合组件经过响应式 props 后触发 Vue 组件代理警告。注册边界按组件本身处理，不把组件对象当编辑状态。
- 原生异步校验期间替换复合控件但 canonical 未变，会绕过新控件验证。提交在各异步边界复查本次已验证控件集合。
- 隐藏祖先子表单时，子字段错误不能留在不可见控件。路径定位与错误投影考虑祖先可见性。
- 构建脚本返回成功不代表声明可用：发现一次 TS2742 私有 `.pnpm/@vue/shared` 路径泄漏，改用显式 Vue 公开类型后重新构建。

必要回归覆盖上述缺陷与关键链路；没有为接入新增大规模业务测试框架。

## 实验场使用方式

RuoYi 仅迁移岗位错误 path、Save/ref 泛型和统一 columns；真实用户关系字段、协议字段明细用于确认边界，未重写页面。既有巡检/协议 pilot 接入 composite、稳定行 ID、错误路径和上传阻断。JSON recipe 通过真实 FormCreate 验证非法 raw、null、pending 非阻断、权威回填、格式保留、reset 和焦点。

图仓目录名是 `vue-flow`，实际消费者为 X6 DAG `/zxui` facet。本次增加逐字段扩展并消费公共 JSON 控件，保留已有 inspector 的 raw/history/commit owner；不将其宣称为所有 Vue Flow 生态场景已验证。

## 验证结果

最终命令、退出码和产物哈希见 [verification.json](./evidence/schema-enterprise-convergence-2026-10-20/verification.json)。

| 检查 | 结果 | 证明范围 |
| --- | --- | --- |
| Schema 包测试 | 4 文件，16/16 | 值/会话边界、真实 FormCreate 内存引擎回归 |
| 源码 pilot | 12/12；最后字段声明收口后受影响 3 链再过 | 真实字段与 FormCreate，模拟 DOM、替身服务 |
| 最终 tarball pilot | 12/12 | 最终发行内容运行相同链路，不只是源码通过 |
| 包及 pilot 类型、精准 lint | 通过 | 泛型公共契约、源码与消费者编译 |
| 包 build | 通过，无 TS 声明诊断 | ESM/CJS、声明、CSS 和 manifest |
| 产物逐文件比较 | 32 个文件在 dist、RuoYi 安装包、DAG 安装包完全一致 | 同一份本地交付；根/fields 运行时与声明不依赖 FormCreate |
| RuoYi 受影响回归 | 6 文件，98/98 | 岗位、布局、编辑生命周期、Dashboard 等已有链路；含组件 mock |
| RuoYi UI 规范 | 528 文件，0 违规；25/25 测试 | 与上述 98 存在交集，不累计成 123 个独立测试 |
| RuoYi 最终包 type-check | 通过，无诊断 | 安装最终声明后的全前端类型检查 |
| RuoYi 源码直连生产 build | 通过，32.92 s | 使用 VITE_ZXUI_LOCAL 与指定 ZXUI 源码；有 Sass 弃用和大 chunk 提示 |
| DAG 精准 lint、类型/两入口 build、public contract parity | 通过 | 最终包类型与构建；生成声明 lint 有 140 个警告、0 错误 |
| DAG 示例双语检查 | 92 bundles × 2 语言、1378 文件通过 | 示例与翻译一致性；不是浏览器交互验收 |

最终本地快照是 `zxio-schema-form-0.1.0-enterprise-final.20261020.tgz`，包内仍为 0.1.0。SHA256：`2cf43a479c4236618eb5523e1c2cd15ca0327dc936bf99c09d775f38889869dc`。只更新了消费者 schema 依赖与对应 lock 条目；本轮中间快照已移除，保留其历史验证记录。

## 规模观察

同机 Node 内存探针，真实 FormCreate group，每行 6 字段：

| 行数 | 编辑一个末行字段并完成 Vue flush，P50 | 读取原生 formData，P50 |
| --- | --- | --- |
| 50 | 6.055 ms | 0.129 ms |
| 200 | 21.463 ms | 0.536 ms |

目标行服务端错误定位及非目标行保持清洁已断言。结构 UI/ElForm 为替身，因此 validate 计时只覆盖原生引擎调度，不包含真实 Element Plus 校验、DOM、布局或网络。不能据此承诺浏览器帧率或大表单生产性能。

observe + dirty 的同机观察为 50/200/1,000 行 P50 0.135/0.302/1.677 ms；与旧测量不是严格随机配对实验，不宣称性能提升百分比。证据：[engine-scale-result.json](./evidence/schema-enterprise-convergence-2026-10-20/engine-scale-result.json)、[session-cost-result.json](./evidence/schema-enterprise-convergence-2026-10-20/session-cost-result.json)。当前证据支持保留简单快照设计；200 行整体编辑成本提示实际大页面仍需按场景测量，不宜许诺无限规模。

## AI 编写效率与 token

已落地的改进是明确入口、贯通类型、减少重复白名单、统一复合字段协议、提供可运行 recipe 和可检查的错误反馈。这些能降低误用的机会，但本次没有取得 token 节省的实测证据。

产物审查消除了一项可量化的接口噪声：本轮中间构建的 JSON 字段声明意外展开底层组件内部类型，达 342,103 字节；通过 callback ref 封口为 607 字节，最终 `/fields` 声明的外部类型依赖仅剩 Vue。这是声明字节量的实测变化，**不是模型 token 降幅**，也不是对任务前旧包的性能比较。见 [public-type-surface.json](./evidence/schema-enterprise-convergence-2026-10-20/public-type-surface.json)。

为避免主观估算，冻结了同一岗位 CRUD 任务、两版 README/公开类型、相同模型设置与输出约束，各实际调用一次 CLI。两次都在生成前被 HTTP 400 拒绝：`codex-cli 0.142.4` 无法调用当前配置的 `gpt-6-astra`，服务要求较新的客户端。无生成代码、无 usage、无 turn.completed，因此 token 为 **null，不是 0**；质量对照也未能执行。没有换模型、升级环境或通过额外重试筛选结果。

[AI 对照记录](./evidence/schema-enterprise-convergence-2026-10-20/ai-authoring/README.md)保存了任务、输入哈希、命令、原始 JSONL 与复跑材料。当前只能称为“有利于 AI 接入的工程改进”，不能称为“已证明降低 token”。

此前研究是设计参考：[Type-Constrained Code Generation](https://doi.org/10.1145/3729274)、[CoCoGen 编译反馈研究](https://aclanthology.org/2024.findings-acl.138/)、[Anthropic Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)。它们不能证明本包、原生 Rule 相对 DSL 或本轮改动的具体 token 收益。下一次有效对照需相同任务/模型/设置，保留失败样本，同时评价类型通过、业务正确性、返工轮次与真实 token。

## 推广判断与保留边界

这轮交付补齐了代码定义复杂表单的主要公共契约，可以作为后续业务接入的基础。尚不能据此宣称所有复杂企业场景已全面验证。没有使用 computer use、没有执行本轮真实业务 API 写入或浏览器验收；模拟 DOM 不能替代浏览器焦点、读屏和真实网络体验。图仓按规则未新增或运行测试套件，验证采用静态审查、lint、声明、构建、公共契约一致性和示例双语检查。

设计器、定义发布/迁移平台、多人协作、审批审计、多选批量事务和多引擎兼容仍需实际产品需求驱动。本轮没有用假设需求增加这些机制，也没有用业务补丁掩盖已确认的 schema 缺陷。

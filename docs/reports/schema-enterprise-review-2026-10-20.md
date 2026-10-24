# ZXUI schema package 二次审查

> 后续状态：本文记录的数值 ARIA 与有效 AI/token 对照两项已由[闭环报告](./schema-aria-ai-closeout-2026-10-20.md)接续完成。AI 实测新版平均总 token +5.22%，未证明节省；以下保留本次审查时的原始状态。

日期：2026-10-20。对象：`/Users/hqz/Downloads/element-plus/packages/schema-form`。本轮按[实施计划](../plans/2026-10-20-schema-enterprise-convergence.md)重新检查源码、公开契约、实际 FormCreate 行为、pilot 和两个安装包消费者；三名子代理分别独立核对架构、会话边界、字段接入。

## 结论

主要通用能力已经实现，架构方向可以继续使用。本轮仍发现并修复了 **7 项具体问题**，说明上一轮通过的测试不足以证明完整落地。修复后支持代码定义 CRUD、复合字段和嵌套明细的依据更充分，但不能把整个 plan 写成“全部效果验收完成”：**AI/token 有效对照未完成；另外确认一项数值步进组件的底层无障碍缺口尚未关闭。**

没有发现需要重新建设 Schema DSL、多引擎框架或另一套编辑状态管理的证据。继续保留根工具、公共字段和可选 FormCreate 会话三个入口；DAG/Dashboard 的领域编辑事务仍属于各自宿主。

## 已修复问题与收益

| 优先级 | 真实问题与触发条件 | 修复 | 长期收益 |
| --- | --- | --- | --- |
| P1 | `copyRules` 深拷贝切断 reactive props/options，并把 ref 复制成不完整对象；原生 group 内还会再复制一次 | 在复制前将显式响应式配置接入原生 computed，递归处理 children/control/group/subForm；作者已有的同路径、祖先或后代 computed 优先 | 异步字典、权限配置和嵌套明细共享同一种接入方式，不必在每个业务补刷新逻辑 |
| P1 | `update:api` 发生在原生规则初始化前；ignore/default 改变引擎投影后，首次打开或 reset 无编辑也 dirty | 使用公开 mounted 生命周期，以完成初始化的 canonical 投影建立基线；旧 API、卸载后的事件不能改当前会话 | 关闭保护、保存按钮和恢复基线更可靠；避免将初始化误判成业务修改 |
| P1 | 声明生成打印 TypeScript 错误，`build` 仍可能 exit 0 | dts `afterDiagnostic` 遇错误直接使构建失败；临时注入类型错误已验证 exit 1，恢复后构建 exit 0 | 防止“构建绿但安装包类型坏”的跨业务传播 |
| P2 | 动态 `wrap:false` 后，已投影的服务端错误不再显示；复合字段也被错误地依赖原生包装 | 可见性观察与投影使用同一资格判断；无包装原生字段转摘要，复合字段继续接收 messages | 布局切换和自带 UI 的复合字段不会丢失错误 |
| P2 | 上传实现忽略 AbortSignal 时，删除附件或权威值替换后仍 pending/blocking；迟到结果可能影响新请求 | recipe 同步退休请求，调用上传组件公开 abort，并按请求身份过滤迟到成功/失败及同 UID 重用 | 给业务提供可直接参考的取消语义，避免永久阻断提交 |
| P2 | JSON profile 用 `String(...)` 验证 type/trigger，错误接纳 `type:['string']`，随后合法字段值也验证失败 | 准入要求精确字符串，再检查枚举；保留受限 profile | 错误定义在导入边界被拒绝，避免用户反复修改合法输入 |
| P2 | README 三个 recipe 链接仅在源码仓有效，安装包中不存在 | 构建复制已验证的示例及必要类型，并改写产物 README 链接 | 后续业务和 AI 可以直接从安装包获取准确示例，无需猜源码路径；不维护第二份手写副本 |

关键实现：[规则适配](/Users/hqz/Downloads/element-plus/packages/schema-form/src/form-create/rules.ts)、[会话](/Users/hqz/Downloads/element-plus/packages/schema-form/src/session.ts)、[错误投影](/Users/hqz/Downloads/element-plus/packages/schema-form/src/form-create/errors.ts)、[声明门禁](/Users/hqz/Downloads/element-plus/packages/schema-form/vite.config.ts)、[上传 recipe](/Users/hqz/Downloads/element-plus/docs/research/schema-form-pilot/pilot/inspection/AttachmentField.vue)。

复用依据同时核对了已安装的 3.3.5 源码与官方资料：[原生 computed](https://www.form-create.com/v3/guide/computed)、[mounted 等公开事件](https://www.form-create.com/en/v3/guide/global-event)、[copyRules](https://www.form-create.com/v3/guide/global-api.html)。没有调用 FormCreate 私有 API，也没有增加规则同步 watcher 框架。

## Plan 覆盖核对

| 计划部分 | 实现与审查结果 |
| --- | --- |
| Task 1：基线及范围 | 本轮重新保存 54 个源文件指纹及临时备份；保留已有脏工作区和旧包 |
| Task 2：会话、错误、类型、取消和权威值 | 已实现；复核 reset、旧请求、权威增行/删行/清空、旧 mounted、默认值与 ignore，修复本轮缺陷 |
| Task 3：嵌套身份、复合状态、布局、无障碍 | 路径和稳定 key、相对消息、中央 blocking、pending 分离、columns/fullWidth、fieldset/legend 已实现；底层数值控件的错误关联例外见下 |
| Task 4：DAG 字段扩展与契约收窄 | 已实现；本轮只更新 schema 产物并重新构建、验证公共契约一致性，未扩大图仓迁移 |
| Task 5：RuoYi 最小接入与真实结构 | 已实现；复跑岗位、布局等 98 项回归、全前端类型及源码直连构建；没有把 pilot 称作真实浏览器验收 |
| Task 6：分发、规模、示例、AI、审查 | 分发和示例已修复并复验；此前规模探针仍只代表内存引擎；有效 AI/token 对照保持未完成，plan 已取消其完成勾选 |

数组身份仍由业务声明稳定 key；无法安全映射时进入摘要。嵌套 arrayKeys 的数字段针对具体提交父行，不承诺任意动态树的路径模板系统。JSON 导入限制不施加于可信代码规则。上传、权限、DTO、服务端冲突与记录身份继续由业务拥有。

## 架构取舍与过度设计检查

- **保留成熟引擎。** 本轮缺陷可以通过公开生命周期、computed 和实例 API 收敛，没有证据要求换引擎。新增规则适配只转换配置资源，不接管编辑值。
- **保留一次规则工厂与独立实例。** 配置资源跨 reset 保留，规则和编辑值不在业务与引擎间双向复制。响应性承诺针对直接 props/resource；动态函数返回的新规则仍按原生引擎语义处理，不宣称任意深层对象自动同步。
- **继续采用简单快照。** 没有引入依赖图、缓存或调度系统。此前 200 行测量不能证明浏览器性能无限扩展；大型明细应针对实际页面测量。
- **保留受限 JSON 导入，但不让代码作者付出同样成本。** policy 与可信 bindings 分离；没有新增版本发布、迁移平台或设计器。
- **示例随包交付，不成为产品 API。** 从已测试源码构建复制，避免示例漂移；不增加业务模型到运行时入口。
- **不把工程代理指标当 AI 效果。** 类型更明确、示例可找到属于已实现能力，token、返工次数和正确率仍需有效实验。

## 验证

命令、退出码、日志与最终包信息见 [verification.json](./evidence/schema-enterprise-review-2026-10-20/verification.json)。本轮补 3 个包回归 case 和 1 个上传 case，并扩展既有准入断言；没有新增业务测试框架。

| 检查 | 本轮结果与边界 |
| --- | --- |
| Schema 包 | 19/19；包括真实 FormCreate 内存引擎，结构 UI/验证器部分为替身 |
| 源码 pilot | 13/13，真实 FormCreate/ZXUI + 模拟 DOM；上传新竞态 case 使用传输组件替身，既有完整上传链保留真实控件 |
| 最终 tarball pilot | 13/13，同一组链路消费最终分发文件 |
| 类型、精准 lint、格式 | 包与隔离 pilot 类型通过，lint/格式通过 |
| 声明门禁 | 故意类型错误被拦截，exit 1；移除探针后正常 build exit 0、无 TS 声明诊断 |
| 发行一致性 | 37 文件在 tarball、dist、RuoYi 和 DAG 安装目录一致；三个 recipe 链接存在，示例与测试源相同 |
| 入口隔离 | 根/fields 的运行时及声明无 FormCreate 依赖，无 `.pnpm` 类型路径；FormCreate 仍为可选 peer |
| RuoYi | 6 文件 98/98；完整 type-check 通过；源码直连 build 成功，Vite 36.28 秒；仅既有 Sass/大 chunk 提示 |
| DAG | 声明、两个入口、公共契约检查通过；生成声明 lint 140 条既有 warning、0 error；未运行图仓测试 |

最终快照：`zxio-schema-form-0.1.0-enterprise-review.20261020.tgz`，包内版本 0.1.0，SHA256：`231de85743ef36ee5aaf664d434b2b5d1c1c8cf9cde7bfa59f16feedc7257a58`。消费者仅更新 schema 依赖及对应锁条目，旧快照保留。

## 仍未关闭的事项

| 优先级 | 事项 | 当前证据与处理边界 |
| --- | --- | --- |
| P2 | ZxInputNumber 实际 input 缺少 aria-invalid/aria-describedby | 已通过真实 Element Plus SSR 确认，属性留在外层 div；schema/MeasurementRows 传参正确。底层 2.13.0 没有公开 inputAttrs 通路。此项属于基础数值步进组件，需要在组件层建立稳定属性通路并验证分发；本轮未修复，未用 schema DOM 查询补丁或重写步进组件掩盖。 |
| P2 | 有效 AI/token 对照 | 旧实验在模型生成前因 CLI 版本被拒绝，无 usage；本轮没有重标为成功，也没有用代码或声明字节数代替 token。 |
| P2 | 浏览器及读屏验收 | 受本会话禁止 computer use 约束，未执行。模拟 DOM、SSR 和源码构建均不能代替焦点体验、读屏、浏览器帧率和生产网络验证。 |

数值组件的责任边界见 [ZXUI wrapper](/Users/hqz/Downloads/element-plus/packages/components/input-number/src/input-number-core.vue)；官方[属性说明](https://github.com/element-plus/element-plus/blob/dev/docs/en-US/component/input-number.md)和[实现](https://github.com/element-plus/element-plus/blob/dev/packages/components/input-number/src/input-number.vue)也未给出所需属性通路。不能因为公共 JSON/普通文本字段的关联测试通过，就推断所有底层控件都通过。

本机可复核证据：[真实 SSR 输出](./evidence/schema-enterprise-review-2026-10-20/input-number-aria-ssr-result.json)、[探针与附件回归索引](./evidence/schema-enterprise-review-2026-10-20/fields-and-upload-evidence.md)。

本轮没有 computer use、真实业务 API 写入、npm 发布、提交或推送。当前适合继续推进新的业务接入；不应宣称所有复杂企业场景、所有无障碍链路或 AI token 收益已全面验收。

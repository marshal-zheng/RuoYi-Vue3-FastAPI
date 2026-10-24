# ZXUI Message：展示、内容契约与业务接入

本轮对应登录失效消息截图：整体表面、黑色正文、状态图标、登录操作和关闭按钮均需评估。
内容支持模板插槽、字符串、VNode、渲染函数、TSX 与 API 插槽，不能按纯文本消息设计。

## 判断与责任

| 问题 | 归属 | 处理 |
| --- | --- | --- |
| 自定义 VNode 绕过原生 `.el-message__content`，正文继承黑色 | ZXUI 的原生 Message 主题适配 | 把浮层表面、前景色和字体放到消息根节点，普通内容继承；旧 `ElMessage` 调用也消费这层样式 |
| 外观过度依赖状态色底，操作和关闭缺乏统一布局 | ZXUI 展示组件 | 增加 `ZxMessage`，默认中性主题浮层，状态由图标表达；统一正文、操作、关闭和焦点样式 |
| “用户token不合法”暴露技术细节；登录操作 5 秒后消失 | 业务反馈语义 | 展示“登录状态已失效 / 重新登录”，持续显示至操作或关闭，保留原错误对象供诊断 |
| HTTP 工具不在 Vue setup 中，需要明确所属应用 | 业务接入 | 根 Provider 绑定 `showMessage`，启动前的调用延迟到 owner 就绪，避免使用最近活跃的库全局 owner |

## 调研依据与选择

- [Fluent 2 Toast](https://fluent2.microsoft.design/components/web/react/core/toast/usage)：消息简短、操作清晰，并区分短暂反馈与必须回应的流程。其通常推荐角落位置；本轮保留现有顶中布局，避免将局部设计优化扩成定位系统改写。
- [Ant Design Message](https://ant.design/components/message/)：轻量反馈、提升表面与简洁层级；推荐能获取 Provider 上下文的 Hook。为现有 `useZxFeedback` 增强内容和展示能力符合当前架构。
- [Radix Toast](https://www.radix-ui.com/primitives/docs/components/toast)：内容、操作和关闭有明确职责；交互消息需要考虑时间与可达性。其焦点/窗口失焦暂停和 viewport 快捷键值得后续考虑，本轮没有声称实现这些能力。
- [WCAG 正文对比度](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)：使用实际前景/背景色计算；常规正文基准为 4.5:1。

选择共享展示组件与既有消息宿主：`ZxMessage` 管单条消息的 UI，现有宿主管定位、堆叠、动画和计时，既有主题反馈层管 owner、app context 与 portal 生命周期。
仅给业务补 CSS 无法覆盖其他消费者；新增完整消息管理器会重复现有成熟能力。因此本轮没有增加第二套全局队列、定位引擎或 contextless 静态库 API。

## 公开契约

- 模板与 TSX 直接使用 `ZxMessage`；它在普通文档流中渲染，父组件通过 `v-if` 和 `close` 事件拥有可见性。
- `default`、`icon`、`action` 插槽优先于相应属性，包括显式空插槽；参数 `{ close, pending }` 中的 pending 描述内置操作，自定义操作自行管理状态。
- `useZxFeedback().message()` 支持字符串、VNode、渲染函数与 options；options 的 `slots` 使用相同命名与参数。无需拼接 HTML。原有显式 HTML 选项仍兼容，默认不启用。
- `action` 要求可读 label，并提供 href 或 onClick。链接保留修饰键导航；异步回调防重复调用，成功默认关闭，`closeOnClick: false` 保留消息，失败由 Vue 的异步事件错误处理接收。
- API 含标准 action 或 action slot 时默认 `duration: 0`、`showClose: true` 并禁用分组。Provider/调用点的显式 duration、showClose 优先；不扫描任意富内容内部是否含按钮。
- 非交互分组继续由原生宿主管计数和时间；适配层按当前 owner、类型和内容身份复用 VNode，保留字符串、VNode 及渲染函数分组行为。
- `message.appearance` 默认 surface，可选 tinted；Provider 的 appearance、closeIcon、customStyle 可由单次 props/options 覆盖。模板响应 Provider 更新，API 读取调用时的配置。
- 六个公开 CSS 变量：background、color、border、radius、shadow、padding，前缀均为 `--zx-message-`。border/shadow 支持完整值 `none`。

## 默认 UI

中性 overlay 表面使用当前主题的 fill、edge、depth、inner、前景色和圆角；状态图标消费 on-surface 角色，正文与标准操作使用可读浮层前景。
图标默认消费 16px 显示角色，关闭复用 Dialog/MessageBox 的常规 SVG。桌面关闭目标为显示尺度的 24px，有独立 hover/focus-visible；触控目标至少 44px。
布局允许富内容和操作换行，内容可收缩与断行，不设固定正文高度。

留白消费 density/display，没有把所有密度锁为 44px。以墨青桌面默认显示尺度、单行 24px 行高和默认边框推算，紧凑/默认/舒适分别约 40/44/48px。
这些是 CSS 配方的名义尺寸；自定义内容、变量、显示尺度和触控目标会影响最终高度。

## 业务接入

`App.tsx` 设置 `message={{ appearance: 'surface' }}`。现有根 `ModalFeedbackProvider` 同时绑定消息发送端；`showMessage` 只负责把非 setup 业务服务交给明确的根 owner。
登录失效提示、HTTP notifier 的 Message 通道以及请求反馈 presenter 的普通成功/错误消息使用该入口。
保留当前页、登录跳转回原路由、静默退出、登录页抑制和旧提示关闭策略。增加版本保护，避免启动时异步返回的旧 handle 或 onClose 干扰新提示。

未全量改写各页面的旧 `ElMessage` 调用；这些调用获得共享主题样式，但 ZXUI 的 action、slots 和 Hook 默认值应通过新入口使用。Notification 与业务反馈 registry 的分类保持现有职责。
必须完成登录等页面级恢复流程，长期可考虑页面提示条；本轮保留既有可关闭提示和登录入口，未用短暂 toast 作为唯一强制回应手段。

## 验证证据

- ZXUI：既有 theme-provider feedback、config-provider feedback、merge 三个文件，13 项通过。
- 业务：既有 http、auth-feedback-boundary、feedback presenter 三个文件，19 项通过。仅更新原有 mock 的发送端，没有添加测试用例。
- 变更库 TS 模块的定向诊断为 0；依赖声明跳过检查，未运行全仓 type-check。
- 临时 Node/JSDOM 源码契约验证通过：真实编译模板、真实编译 TSX/渲染函数、VNode、API 命名插槽、模板配置响应、API 配置捕获、异步操作防重复、三种内容分组、SVG/关闭文案、单一 API live region。使用真实 Vue/Element Plus；配置读取与 portal acquisition 为受控验证接缝。
- 最后补充真实原生宿主验证：同一显式 scope 的不同 Hook/反馈实例共享分组，不同 scope 隔离；内部关闭、清理后重新创建通过。该项用受控展示组件探针隔离分组适配行为。
- 文档演示 SFC 的 script/template 编译通过；结构 CSS 通过 PostCSS 解析，六个变量存在。
- 临时业务源码验证通过：重复提示抑制、旧 handle 清理、旧 onClose 隔离、原路由 redirect/静默退出、登录页抑制、启动前延迟绑定。
- 当前 9 个主题 × 明暗模式的 18 组默认浮层正文对比度最低 10.3590:1；72 组状态色最低 7.7438:1；次要前景/关闭色最低 6.1091:1。计算来自当前生成资产的实色角色，不能替代自定义样式后的检查或浏览器视觉验收。
- localhost 首页、8088/docs、业务 App/HTTP/Provider 和 ZXUI 本地组件/反馈/CSS 共 8 个 HTTP 请求返回 200，并包含对应源码标记。
- 两仓相关变更的 `git diff --check` 通过。

遵照用户要求未运行 lint/build、未增加测试用例、未发布 npm。没有使用 computer use，因此没有做实际浏览器截图和视觉验收。
API 保留原生 `alert` live region，内部不重复声明；独立组件按类型使用 status/alert。原生宿主的焦点暂停、窗口失焦暂停、辅助技术实际播报和全局 max 拒绝行为仍属于后续评估范围，不能声称已对齐所有 Toast 框架能力。

## 源码入口

后续已获得 computer use 授权并完成真实业务验收，发现及修正首行对齐、触控宽度和 API 关闭标签继承，详见 [真实业务视觉与交互验收](2026-10-13-message-visual-validation.md)。

- ZXUI：`packages/components/message/`、config-provider 与 theme-provider feedback、`packages/theme-chalk/src/structural.css`。
- 公开示例：`docs/examples/config-provider/message-content.vue`；中英文 ConfigProvider 文档的 Message 内容与操作章节。
- 业务：`src/utils/feedback/message.ts`、`src/plugins/ModalFeedbackProvider.ts`、`src/utils/http.ts`、`src/utils/feedback/presenter.ts`、`src/App.tsx`。

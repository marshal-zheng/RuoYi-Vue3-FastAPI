# Notification 默认体验与真实业务验证

## 排查结果与实现边界

库此前只有原生 Notification API 转发，缺少与 Message/Dialog 一致的浮层语义、密度排版及关闭控件。业务反馈 presenter 和表单生成器直接调用原生 API，绕过 Provider/Portal，墨青暗色页实际出现白底通知。

在已登录 `/system/user` 使用既有反馈 presenter 连续触发“已受理”和限流提示，还复现了重叠：两条通知的 top 为 16px / 32px，第一条高度 84px。原生队列在 Vue visibility 更新前读取高度为 0。正文 tracking 字符串中的换行被合并，关闭图标是无 tabindex 的 i 元素。

## 契约与设计

- 新增 `ZxNotification` 展示组件，复用 ZxMessage 的状态图标、关闭按钮、标准操作、主题表面与插槽交互。通知使用固定首行、独立正文及右侧操作区，正文可滚动；不增加 Dialog 分隔线或固定正文最小高度。
- 默认宽度 360px（消费 display factor），受视口两侧 16px 边界约束；标题使用现有正文尺度与 600 字重，正文使用次级文字色和现有行高。上下内边距消费同一 density 规则。
- `title`、`message` 支持字符串、VNode、渲染函数与 TSX；title/default/icon/action 为明确的插槽。API 与模板共用展示项。
- Notification Provider 控制 appearance / closeIcon / closeLabel / customStyle；原生 position、offset、duration、onClose、onClick 等继续可用。有 action 或 action slot 时默认不自动关闭，显式 duration 优先。
- API 信息/成功默认 status，警告/错误默认 alert，可用 role 覆盖；内层不重复声明 live region。中英文关闭标签按消息、通知的语义区分，locale 的 zx.message.close / zx.notification.close 可覆盖。
- 原生队列继续管理四角定位、关闭与计时。创建后等待 Vue patch，再调用原生 updateOffsets；ResizeObserver 在内容/密度改变时请求原生重新计算位置，终止后 disconnect。没有新增队列或消息管理器。
- 业务保留原来的内容、持续时间和 Promise 约定，仅把通知入口绑定到根 Provider。启动阶段的延迟发送由 Message/Notification 共用同一业务 channel 实现。

参考 [Ant Notification](https://ant.design/components/notification/) 的复杂内容、具名动作与 Hook/Provider 使用方式，以及 [Fluent Toast](https://fluent2.microsoft.design/components/web/react/core/toast/usage) 的标题、补充信息、可选动作分工。具体尺寸与 density 由 ZXUI 现有主题度量决定。

## 验收清单

| 维度 | 验证 |
| --- | --- |
| 9 主题 × 明暗 × 三档密度 | success / warning / error / title-body-action slots；表面/正文/次级文字/图标，首行对齐，关闭控件，宽度、堆叠间隔 |
| 真实业务 presenter | 202、部分成功、429 tracking 换行；根 Provider 归属 |
| 操作 | 异步防重复/失败恢复、slot 双操作、关闭与 card onClick 的隔离 |
| 原生生命周期 | 自动计时、hover、四角定位、onClose、关闭后重排；密度及内容高度变化 |
| 模板与 API | 标题/body slot 优先、VNode/函数、标题缺省/仅标题、显式 closeLabel / style / role 配置 |
| 窄屏与长内容 | 360px、连续长文件名、长正文滚动，首行和操作区可见；375px 和横屏 |
| 输入与显示 | 键盘焦点/关闭、触控 44px 目标、文字缩放、减少动态效果 |

用户已授权真实业务 computer use。本轮不写新增测试用例、不运行 lint/build、不修改业务数据或发布 npm。

## 接管后的验收结果（2026-10-13）

原会话因模型容量错误中断。本会话接管已有源码与运行服务，完成最新 Notification 任务；没有重新提交旧会话或覆盖其他主题、Dashboard 改动。

在真实 `/system/user` 页面重新采集并审阅 9 个主题 × 明暗 × 紧凑、默认、宽松，共 **54 组、216 个通知画面**。四类通知覆盖成功、警告、错误和 title/body/action Slot。全部宽度受视口约束，首行图标和 X 中心偏差为 0，连续通知与底边的间距均为 16px。标题最小对比度为 10.30，正文及关闭控件为 6.10，状态图标为 7.71。

墨青普通标题/正文通知在三档密度下为 76 / 80 / 84px；带单操作为 110 / 114 / 118px，带两行正文和双操作为 134 / 138 / 142px。Notification 按内容增长，Message 的单行高度约定没有改变。

接管后又复现并修正三处问题，均落实在 ZXUI：

1. 通知原生宿主使用响应式 `currentZIndex`，后来打开的菜单与通知会处于同一层，短窗口中的密度选项被遮挡。现在创建通知时固定层级，Hook 保留所属 Provider 的层级分配器；显式 `zIndex` 覆盖仍可用。修复后在 1440×1000 窗口用正常点击完成密度切换。
2. Notification 纵向布局继承 Message 的 `flex-wrap: wrap`。长正文占满高度后，操作区会换到右侧新列，375px 触控窗口中按钮右边界达 428px。Notification 改为纵向不换列，正文单独滚动；按钮右边界回到 342px，标题、X 和操作区均留在通知内。
3. 系统“减少动态效果”开启后仍有 140ms 位移动画。Notification 补充媒体查询，宿主和展示项的 transition duration 均为 0s。

交互与内容检查也已完成：

- 异步操作双击只调用一次，执行中按钮禁用；操作和 X 不触发通知卡片的 `onClick`。
- 模拟失败后通知保留，按钮恢复可用；第二次成功执行后关闭，`onClose` 仅调用一次。
- 双操作 Slot 和公开 `ZxNotification` 展示组件的 Slot 均能正常关闭；标题/正文 Slot 优先于对应属性。
- 函数标题、VNode 正文、无标题、仅标题、无图标，以及单次 width / role / closeLabel / zIndex 覆盖均正常。
- 自动关闭时长、悬停暂停、离开后重新计时、四角定位和关闭后的重新排布保留原生行为。
- 键盘 Enter 能操作关闭按钮，关闭后剩余通知回到底边 16px；触控关闭按钮为 44×44px，操作按钮为 74×44px。
- 375×667 触控视口和 667×375 横向短视口均通过长正文滚动检查，滚动后操作区位置不变，触控操作成功。
- 真实业务 presenter 的 202 已受理、207 部分成功和 429 提示均继承根主题。Request ID、Trace ID 和重试提示各占一行。
- 原始 `/system/role` 新增操作已复验：菜单树显示系统管理、系统监控、系统工具和工程管理，加载文案消失，保存按钮恢复可用；没有提交角色数据。

现有回归检查 **35 项通过**：ZXUI 的 ThemeFeedback、ConfigProvider feedback/merge 共 13 项；业务 feedback presenter、HTTP 契约、RoleFormDrawer 共 22 项。Structural CSS 解析及本次库文件的 whitespace 检查通过。遵守原会话约束，未新增测试、未跑 lint/build，未提交或发布。文字缩放未作为独立浏览器矩阵验收。

## 截图与测量

- [最终墨青明暗对照](assets/notification-visual-2026-10-13/notification-dark-light.png)
- [54 组结构、颜色及对齐测量](assets/notification-visual-2026-10-13/measurements.json)
- [交互、窄屏、角色菜单及减少动态效果记录](assets/notification-visual-2026-10-13/interactions.json)
- [375px 长正文修复后](assets/notification-visual-2026-10-13/mobile-long-content-after.png)、[滚动到底后](assets/notification-visual-2026-10-13/mobile-long-content-scrolled.png)
- [业务 presenter](assets/notification-visual-2026-10-13/business-presenter.png)、[新增角色菜单](assets/notification-visual-2026-10-13/role-menu-loaded.png)
- 各主题六宫格：`assets/notification-visual-2026-10-13/<theme-id>-matrix.png`，各状态另存完整业务页面截图。

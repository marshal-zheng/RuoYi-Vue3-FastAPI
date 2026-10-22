# 菜单收起动效校正（2026-10-22）

## 根因与责任

真实业务修复前逐帧记录确认：

1. 点击分组标题时已有原生高度过渡，但默认主题只有约 180ms；业务额外添加的上下外边距未参加过渡，末尾直接跳掉 14px。
2. 整栏收起时，业务立即切换 ElMenu 的 collapse 和 key。在宽度仍为 250px 时，428px 的内联子菜单已被移除，下一分组纵坐标从 554px 直接跳到 116px。此前仅补了整栏宽度动画，遗漏了菜单结构切换时序。

责任在业务导航壳。继续复用 [ElMenu 的公开 open/close 能力](https://element-plus.org/en-US/component/menu.html#menu-exposes) 与现有 [ElCollapseTransition](https://github.com/element-plus/element-plus/blob/2.13.0/packages/components/collapse-transition/src/collapse-transition.vue)，不另建高度测量或动画框架。ZXUI 组件、主题颜色和生成资产未改。

参考本地 ThingsBoard `menu/menu-toggle.component.scss`、`src/theme/shell-theme.scss`：子菜单高度使用 `cubic-bezier(.35,0,.25,1)`，默认 450ms；箭头同步旋转。

## 修改

仅修改前端 `src/layout/components/Sidebar/index.vue` 和 `src/assets/styles/sidebar.css`：

- 分组原生高度过渡同时带上上下间距，沿用 ThingsBoard 的节奏曲线；时长消费 ZXUI 现有语义动效令牌，默认主题为 450ms、森绿为 350ms。
- 整栏收起时通过公开 close 关闭已打开分组，保留内联 DOM 至实际 CSS 过渡结束，再切到图标栏。宽度与子菜单高度同步收缩，根图标平滑归位。
- 等待原生动画完成信号，不使用固定延时；短暂的菜单表现状态不替代应用的侧栏状态。
- 快速反向时恢复本次正在收拢的组；完整收起后清空临时记录，避免旧组覆盖当前路由。显式点击其他分组时以该目标为准；卸载或方向改变会使旧异步任务失效。
- 系统减少动态效果和 withoutAnimation 路径立即切换。移动端继续使用原抽屉与展开式菜单。

## 验证

- 本地业务直接加载 `/Users/hqz/Downloads/element-plus` 源码，资源记录见 checks.json。
- 修复前两个动效探针均失败：300ms 后已无有效分组收拢帧，整栏变窄过程中不存在内联子菜单。修复后两个探针均有连续中间帧。
- 默认分组在约 304ms 时仍有 48px 高度和约 1.4px 外边距，随后共同收敛到 0，末尾无 14px 跳变。
- 整栏在约 125px 宽时仍保留正在缩短的内联菜单；完成后宽度为 64px，切换至浮层模式。图标中心从 34px 平滑到 31.5px。
- 共 25 项真实交互检查：分组开合、箭头、间距、整栏同步收起、嵌套 Enter/Space、浮层悬停与叶子路由、跨分组导航、关闭所有组、减少动态效果、移动端分组与 Escape 焦点返回，以及中途反向和连续三次切换。真正的中途反向在宽度约 212px 时发出点击。浏览器运行错误 0。
- 默认浅色与森绿深色的中间状态、完成状态截图已目视检查。
- 独立复核发现的旧分组恢复问题已修正，并验证“由浮层进入在线用户后展开”“收拢途中明确点击工具组”。最终无剩余 P1/P2。
- 既有 Hamburger 与 layout policy 10 项测试通过；目标 Vue 文件 ESLint、前端 type-check、目标 diff 空白检查通过。本轮未新增测试套件。
- 全工作区 convention 脚本仍有既有 3 项问题：缺失 `AlarmPanelFloating.vue`、`FaultBoardPanel.vue` 颜色规范、`session.test.ts` axios 规范；未宣称整个工作区门禁通过。

## 证据

- [修复前帧记录](navigation-menu-motion-2026-10-22/before.json)
- [最终帧、交互、源码资源和错误记录](navigation-menu-motion-2026-10-22/checks.json)
- [默认展开](navigation-menu-motion-2026-10-22/group-default-open.png)
- [默认收起中](navigation-menu-motion-2026-10-22/group-default-middle.png)
- [默认收起完成](navigation-menu-motion-2026-10-22/group-default-closed.png)
- [整栏收拢中](navigation-menu-motion-2026-10-22/rail-fold-middle.png)
- [森绿深色收起中](navigation-menu-motion-2026-10-22/group-fold-army-dark-middle.png)
- [森绿深色收起完成](navigation-menu-motion-2026-10-22/group-fold-army-dark-closed.png)

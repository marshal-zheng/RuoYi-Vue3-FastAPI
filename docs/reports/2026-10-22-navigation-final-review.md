# Header / Sidebar 整体复核（2026-10-22）

结论：发现并修复配置覆盖与交互边界问题。修复均在业务导航内，未修改 ZXUI，未把菜单路由、品牌、单组展开或应用断点规则加入组件库；继续通过 ZXUI 公开语义角色读取主题。未发现需要修改组件库的通用机制缺陷。

## 发现与修复

| 问题 | 证据 / 修复 |
| --- | --- |
| OS 减少动态效果没有覆盖导航浮层 | 修复前捕获侧栏 popup 的 enter-active 仍为 180ms，起始缩放 0.45。在统一入口按系统偏好将导航 fast/control 时长归零，派生时长一起归零；两类浮层及原生箭头都消费导航配置。 |
| 隐藏 header 后，恢复入口绕过配置 | control 改为 48px 后，旧恢复按钮仍为 36px。导航入口复用既有 Hamburger；设置入口消费同一 control、action-icon、圆角、焦点与状态动效配置。修复后按钮 48px，导航图标 28px、设置图标 26px 同步生效。 |
| 全局字体覆盖不完整 | 原来只有 sidebar-menu 读取 app-nav-font-family。现在 header、侧栏品牌、TopNav、两类浮层与恢复入口均接通；浮层普通/选中字重也消费统一配置。 |
| 选中阴影和高光覆盖不完整 | 收起组选中与浮层将 box-shadow 占用于左指示条，覆盖统一选中阴影；收起组还缺高光。指示条改为独立伪元素，三处读取同一 active-shadow/highlight。全局 4px 阴影与渐变探针同时生效。 |
| 单组展开配置无效（既有缺陷） | settings.ts 的 uniqueOpened=true，却读取不存在的 settingsStore.uniqueOpened。实际能同时展开 system 与 monitor。直接消费已有 defaultSettings.uniqueOpened，不增加另一套偏好或库规则；嵌套祖先仍可同时保留。 |
| 叶子链接的 Tab 焦点不可见（既有缺陷） | 实际获焦为外层 a，旧规则只匹配内层 li。导航范围内补 a:focus-visible > .el-menu-item，消费同一焦点宽度/颜色；真实 Tab 验证为 solid 2px。 |
| 导航层级值散落 | header/recovery 的 9、sidebar 的 1001 移到统一入口，保持原有层级关系。 |

保留的 0、100%、旋转方向、SVG viewBox/path、组件局部堆叠上下文属于结构常量；Logo 的 login 变体、布局设置面板、主题选择器自身的内容排版不属于本轮导航尺寸契约。没有把这些无关范围改成导航配置，也没有覆盖核心 --el-* / --zx-* 值。

## 统一入口与职责

- 视觉配置唯一入口：[navigation-tokens.css](../../ruoyi-fastapi-frontend/src/assets/styles/navigation-tokens.css)。原有尺寸、间距、icon、hover/active、圆角、主题映射、动效倍率/时长/曲线保持；新增 header/sidebar layer；OS 减少动态效果也在此收口。
- 交互行为配置继续位于业务已有 [settings.ts](../../ruoyi-fastapi-frontend/src/settings.ts)：uniqueOpened 控制是否只展开一条分组路径。CSS 不承担行为开关。
- 改尺寸默认值在 :root；改主题角色映射在同一入口的 :root 与 theme Host 规则。浮层传送到 body 后仍消费对应主题作用域。不要在各组件重新声明数值。
- 配置总表仍见 [导航统一配置记录](2026-10-22-navigation-contract.md)。

## 新鲜验证证据

- 本地 http://127.0.0.1:80，实际 admin 用户管理页面，资源来自 /@fs/Users/hqz/Downloads/element-plus/ 源码路径。
- [20 项浏览器检查](navigation-final-review-2026-10-22/checks.json)全部通过，运行异常 0。覆盖全局 300/64px 宽度、28px icon、48px 行高、64px header、5px 基础间距；monospace 字族；高光/阴影；两类浮层 OS reduce；隐藏 header 恢复入口和移动焦点；单组/嵌套/折叠反向与连续切换；Logo hover；真实 Tab；森绿深色 hover/active。
- 默认恢复为展开 250px、收起 50px、图标 24px、行高 44px、header 56px。临时 CSS 覆盖全部移除，TopNav 关闭，默认浅色恢复。
- [默认完整页面](navigation-final-review-2026-10-22/final-default.png)、[森绿深色移动菜单](navigation-final-review-2026-10-22/army-dark-mobile.png)、[全局配置浮层](navigation-final-review-2026-10-22/global-popup.png)、[TopNav 减少动态效果](navigation-final-review-2026-10-22/topnav-reduced.png)。截图经过实际查看；移动端所有可见行在 844px 视口内，未以动画中途截图作为验收。
- 目标 Vue 文件 ESLint、yarn type-check、git diff --check 通过。既有 Hamburger/layout policy 共 10 项测试通过；未新增测试套件。
- 独立代码复核通过。全工作区 convention 脚本仍有三个既有问题：缺失 AlarmPanelFloating.vue、FaultBoardPanel.vue 裸色、session.test.ts axios 规范。与本轮导航修复无关，未宣称全工作区门禁通过。

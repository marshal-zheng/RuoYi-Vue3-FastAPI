# 导航折叠品牌与交互校正（2026-10-22）

## 责任与参考

对照本地 ThingsBoard `ui-ngx/src/app/modules/home/home.component.{html,scss,ts}` 与 `menu/menu-toggle.component.{html,ts}`：折叠栏默认呈现品牌图标；悬停或键盘聚焦时淡入展开图标；分组悬停预览、点击或键盘激活展开侧栏；空白栏点击也可展开。

这些属于应用导航壳的品牌和路由组合规则，修改位于业务侧。继续使用 ZXUI 主题、语义动效令牌及 ElMenu/ElDrawer，未修改主题或增加组件库配置。

## 变化

- Hamburger 提供可选 `brand` 插槽：折叠时默认显示 Logo，hover/focus-visible 时与展开图标交叉淡化；展开后显示收起按钮。保持原生按钮、展开状态、可访问名称和焦点提示。
- 侧栏接入现有品牌图片，遵循“显示 Logo”偏好；关闭 Logo 或移动端使用直接的导航按钮。
- 折叠分组悬停只展示浮层；点击、Enter 或 Space 展开侧栏并打开对应分组，保留键盘焦点。展开态各分组可经 Tab 到达，Enter/Space 切换自身。
- 点击折叠栏空白处展开；浮层叶子仍直接导航。右上角用户区保持原位置。
- 交叉淡化与现有展开收起动画共同消费 ZXUI 动效令牌；系统减少动态效果偏好下禁用过渡。

修改文件：前端 `src/components/ui/Hamburger/index.vue`、`src/layout/components/Sidebar/index.vue`、`src/layout/components/Sidebar/SidebarItem.vue`，并在已有 `tests/unit/Hamburger.test.ts` 补充一个品牌插槽回归用例。

## 验证证据

- 本地真实业务 `http://127.0.0.1/system/role`，浏览器资源确认直接加载 `/Users/hqz/Downloads/element-plus` 源码。
- 21 项交互检查通过，包括 Logo/展开图标切换、hover 中间帧、Enter/Space、分组悬停/点击/焦点、空白栏展开、浮层叶子导航、Logo 偏好关闭、减少动态效果、移动抽屉焦点约束及 Escape 返回入口。浏览器运行错误 0。
- 默认浅色与森绿深色截图已检查；使用现有主题颜色。
- `yarn exec vitest run tests/unit/Hamburger.test.ts src/layout/policy.test.ts`：10 项通过。
- `yarn type-check`、4 个目标文件 ESLint、目标文件 `git diff --check`：通过。
- 独立复核发现的展开态分组 Tab 不可达已修正，并用真实键盘验证；最终无剩余 P1/P2。
- 全工作区 convention 脚本仍有既有 3 项问题：缺失的 `AlarmPanelFloating.vue`、`FaultBoardPanel.vue` 颜色规范、`session.test.ts` axios 规范。本次未处理这些无关改动，未宣称全工作区门禁通过。

## 截图与探针

- [默认收起状态](navigation-brand-2026-10-22/collapsed-default.png)
- [默认悬停状态](navigation-brand-2026-10-22/hover-default.png)
- [森绿深色收起状态](navigation-brand-2026-10-22/collapsed-army-dark.png)
- [森绿深色悬停状态](navigation-brand-2026-10-22/hover-army-dark.png)
- [键盘聚焦](navigation-brand-2026-10-22/focus-default.png)
- [移动抽屉](navigation-brand-2026-10-22/mobile-drawer.png)
- [交互、动效中间帧、源码资源与错误记录](navigation-brand-2026-10-22/checks.json)

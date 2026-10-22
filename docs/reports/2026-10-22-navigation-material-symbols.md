# 导航 Material Symbols 实施与验证（2026-10-22）

保留 ZxIcon；header、sidebar、TopNav 的业务图标采用 Material Symbols 标准款实心 SVG，按项目真实需求本地打包。当前主题、导航几何、路由、权限与折叠交互继续沿用原契约。

## 业务与组件库边界

- 业务映射入口：[src/icons/navigation.ts](../../ruoyi-fastapi-frontend/src/icons/navigation.ts)。控制项与现有菜单标识在此统一选择图形；明确的自定义图标继续遵循已有菜单契约，不修改数据库标识。
- 本地资产：[material-symbols/](../../ruoyi-fastapi-frontend/src/assets/icons/svg/material-symbols/)。31 枚 SVG，固定 Google 上游 revision `49d4db35df873165d6bd6ba09b063c7dafbac2f4`；FILL=1、weight=400、optical size=24。来源、变换和 Apache-2.0 许可见 [资产说明](../../ruoyi-fastapi-frontend/src/assets/icons/MATERIAL-SYMBOLS.md)。
- 尺寸、间距、状态色和动效入口仍为 [navigation-tokens.css](../../ruoyi-fastapi-frontend/src/assets/styles/navigation-tokens.css)。没有新增散落尺寸或覆盖核心主题变量。TopNav 明确覆盖原生菜单固定 24px 图标宽度，使全局 28px 探针在根菜单与浮层都生效。
- Sidebar、TopNav、Hamburger、Navbar、主题切换与隐藏 header 恢复入口均使用 ZxIcon；IconSelect、MenuList 与 MenuDrawer 已选图标预览使用同一解析器，保存值与预览保持一致。
- 原生菜单内部箭头、关闭、loading 等组件内部符号保持组件原有实现。本轮没有把组件库所有内置图标整体换成 Material。

ZXUI 仅修通用渲染问题：

1. `packages/components/icon/src/icon-core.vue` 的有/无 tooltip 两条 SVG 路径不再强制加 `stroke=currentColor`，避免 24px 实心图标被加粗。
2. `packages/theme-chalk/src/structural.css` 的 ZxIcon 样式继承父级文字色，不再强制 SVG 填充为正文色或在 hover 时覆盖颜色。真实森绿探针修复前图标 fill 与菜单文字色不一致，修复后相等；线性 SVG 自身的 fill=none 与 stroke=currentColor 也保持有效。
3. 通过 `pnpm -C packages/theme-chalk update:mirror` 生成镜像；修复前 source/mirror 字节一致，未手工编辑生成产物。公开 icon 文档同步更新。

库中没有新增 Material、菜单名称、路由或业务图标映射。两个仓库原有的其他工作区改动均未清扫，也没有自动提交或发布。

## 按需与性能证据

“按需”指只选入该业务所需的 31 枚本地 SVG，不是按当前屏幕可见数量懒加载。现有 sprite 会把已选资产一次注入。

使用项目现有 vite-plugin-svg-icons，启用生产 SVGO/minify，对旧图标目录与新增后的目录分别构建同一个只引入 sprite 的入口：

| 隔离 sprite 构建 | JS 字节 | gzip 字节 | Material Symbols 数量 |
| --- | ---: | ---: | ---: |
| 原有图标 | 90,950 | 35,260 | 0 |
| 原有 + 新增 | 102,037 | 38,592 | 31 |
| 本轮增量 | **11,087** | **3,332** | **31** |

[构建结果](navigation-material-symbols-2026-10-22/sprite-build.json)。这是图标模块增量探针，不是完整应用产物体积或端到端性能基准。没有新增整套 Material 字体、图标集依赖或 Lucide。浏览器链路没有请求 api.iconify.design、Google Fonts 或 gstatic 字体。

当前应用已有旧 SVG sprite、Element Plus 全量注册，以及 ZXUI 便利入口的名称回退；这些是原有开销，本轮没有宣称全项目严格逐图标 tree shaking。

## 验证

- [20 项真实浏览器检查](navigation-material-symbols-2026-10-22/checks.json)全部通过，运行错误 0；资源确认直接来自本地 ZXUI checkout。
- 实际菜单所有已知图标均解析到本地 Material symbol，引用目标存在；24px 图标在 50px 收起栏居中。
- Logo hover、浮层角色路由、嵌套 Enter/Space、折叠中途反向、默认与森绿深色、28px 菜单 / 26px 操作 / 18px 箭头覆盖、TopNav 更多菜单均通过。
- 菜单列表、编辑框、选择器和已选预览一致；验证选择操作未提交菜单数据。
- 隐藏 header 的移动恢复入口、抽屉焦点、Escape 返回与减少动态效果通过。
- 临时尺寸和字体覆盖已移除，TopNav 关闭，默认浅色与 250/50px、24px 图标恢复。
- ZXUI icon 9 项与结构策略 51 项共 60 项测试通过；新增的有/无 tooltip 两条用例先因强制描边失败，再在修复后通过。结构样式校验通过：单一源、三个主题各 162 个变体、确定性构建与 tar 审计。
- 前端既有 Hamburger/layout policy 10 项测试、type-check、目标 lint 通过；未增加业务测试套件。
- 独立复核发现 MenuDrawer 预览遗漏，已修正；最终无确定剩余问题。
- 全工作区 convention 仍有既有三个问题：缺失 AlarmPanelFloating.vue、FaultBoardPanel.vue 裸色、session.test.ts axios 规范；未宣称整个工作区门禁通过。

## 画面

- [默认最终页面](navigation-material-symbols-2026-10-22/final-default.png)
- [森绿深色收起栏](navigation-material-symbols-2026-10-22/army-dark-rail.png)
- [TopNav 与更多菜单的尺寸覆盖](navigation-material-symbols-2026-10-22/topnav-more.png)
- [菜单编辑与选择预览](navigation-material-symbols-2026-10-22/menu-preview.png)
- [移动端](navigation-material-symbols-2026-10-22/army-dark-mobile.png)

## Plan-stage checkpoint

STATUS: PLAN_UPDATED
FILES_WRITTEN: docs/plans/2026-10-22-navigation-material-symbols.md
EVIDENCE: READ public icon and real navigation consumers; SEARCH menu identifiers, preview paths and style owners; COMMAND plan structure checks passed.
PLAN_CHANGES: Include discovered SVG fill/color rendering defect and both menu-preview consumers; use existing sprite with bounded local assets and an isolated production size probe.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: current-session execution (completed with evidence above)
BLOCK_REASON: none
UNBLOCK_ACTION: none

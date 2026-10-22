# Element Plus 图标按需加载（2026-10-22）

后续[整体复核](2026-10-22-icon-review.md)补齐了所有业务视图的静态闭包检查，修复源码根入口辅助函数带入整集的问题和图标名称原型误命中，并验证公开样式入口保留。下文首轮测量仅覆盖初始闭包；当前交付与完整结果以后续复核为准。

业务已移除整集全局注册，改为统一的 46 个实际字符串名称；ZXUI 核心组合不会再通过内部按钮、图标或弹框引回完整名称表。菜单图形选择与动态配置留在业务，组件库没有新增菜单、权限、路由或 Material 映射。

## 配置入口与加载边界

- [业务图标说明与维护方法](../../ruoyi-fastapi-frontend/src/icons/README.md)
- [有限注册表](../../ruoyi-fastapi-frontend/src/icons/element.ts)：原生 Element Plus 字符串和 ZXUI capabilities 共用一份配置。
- [模板自动导入](../../ruoyi-fastapi-frontend/vite/plugins/components.ts)：使用公开 `ZxuiResolver({ entry: 'core' })`；直接的 Button/Icon/Dialog 导入与 ConfirmInput 工厂也改用公开 core。
- [导航映射](../../ruoyi-fastapi-frontend/src/icons/navigation.ts)：保持原有菜单数据、本地 SVG 协议、Material Symbols 和统一尺寸主题策略。
- [设计器目录](../../ruoyi-fastapi-frontend/src/views/tool/build/element-catalog.ts)、[动态预览](../../ruoyi-fastapi-frontend/src/utils/generator/icons.ts)：完整 EP 目录属于设计器的异步能力，不全局注册。

ZXUI 为 ContentWrap、Drawer、FloatingPanel、ActionBar、ConfirmInput 抽取单份 core 实现，原入口薄装配保留完整名称能力。复合 setup 建立 capability context；固定图标传组件引用。Search、Upload、MoreAction 的固定内部图标也不再依赖名称表。ConfirmInput 共用服务不引用默认组件，两个入口各自绑定组件。

完整名称表改用 EP 官方独立 `@element-plus/icons-vue/global` 出口。它与普通的有限具名导入隔离，避免仅增加 `import()` 却仍把全表提升为入口共享依赖。没有引入新的图标库或图标编译框架。

**动态兜底属于功能级加载。** 打开完整选择器，或恢复一个不在有限表中的有效图标，会加载整份目录；不是逐图标下载。未知名称保持空图标。旧设计保留字符串，预览转组件引用，导出的 Vue 文件带明确具名导入和属性绑定。

## 生产交付测量

使用同一套当前业务与 ZXUI 源码构建。对照只把 `main.ts` 的有限表导入恢复为旧式整集命名空间导入，其余代码相同；它是可复现的单变量对照，不是历史 checkout 的整轮前后总收益。

| 静态入口 JS 闭包 | raw 字节 | 按输出文件分别 gzip 后求和 | EP 图标定义 |
| --- | ---: | ---: | ---: |
| 恢复全量注册的对照 | 2,625,503 | 824,934 | 293 |
| 当前有限注册 | 2,498,390 | 790,680 | 85 |
| 减少 | **127,113** | **34,254** | **208** |

入口 JS gzip 减少约 4.15%。85 个定义包含业务有限表和组件自身必需的图标，不等于页面当前可见图标数。完整目录在非初始异步块内，raw 171,666 字节、gzip 44,009 字节。

这些是生产 JS 构建数据，不包含 CSS、主题资产、后续路由请求，也不是 FCP 或端到端耗时基准。安装包包含库发布文件，与浏览器实际下载闭包不同；不能以 node_modules 大小推断首包。

[完整构建结果](element-icons-on-demand-2026-10-22/build-results.json)与[测量脚本](element-icons-on-demand-2026-10-22/build-probe.mjs)。从前端目录分别执行，两个构建使用独立 Node 进程，避免保留上一轮完整构建图：

```sh
NODE_OPTIONS=--max-old-space-size=8192 node ../docs/reports/element-icons-on-demand-2026-10-22/build-probe.mjs full-registration-control
NODE_OPTIONS=--max-old-space-size=8192 node ../docs/reports/element-icons-on-demand-2026-10-22/build-probe.mjs candidate
```

## 验证证据

- [22 项最终浏览器检查](element-icons-on-demand-2026-10-22/checks.json)通过；页面运行错误 0。真实资源来自 `/Users/hqz/Downloads/element-plus`，普通用户页未请求完整业务目录或 ZXUI legacy 图标表。
- 原有菜单 `system` 标识、菜单列表和编辑预览保持一致；自定义 `bug` SVG 可选择并预览，随后取消，没有提交菜单变更。
- 设计器普通打开不请求完整目录；打开选择器后 293 项均有 SVG。非常用 Watermelon 正确预览且未全局登记，未知名称保持空图标。
- 通过真实“导出 vue 文件”操作取得[生成文件](element-icons-on-demand-2026-10-22/generated-form.vue)，SFC 编译确认 Watermelon 是导入绑定，模板使用组件引用。
- 森绿深色下图标 fill 与所在文字颜色一致；TopNav、50px 收起栏、24px 图标、Logo hover、250px 展开栏与全局 28px 尺寸覆盖通过。临时覆盖已移除，最终恢复默认浅色布局。
- 浏览器链路没有请求 Iconify API、Google Fonts 或 gstatic 字体。长时验证中会话失效后已重新登录，最终真实用户数据与操作栏再次确认正常；未改认证逻辑。
- ZXUI 相关 10 个测试文件 **67 项通过**；业务相关 8 个文件 **40 项通过**。新增少量针对嵌套 capability、公开 resolver、非常用图标恢复、导出绑定与 Search loading 的必要回归，未增加批量接入测试。
- 独立复核发现 Search 内置 loading 残留字符串，已修为 Loading 组件引用；该单条回归修复前失败、修复后通过。外置搜索仍用原 EP Search 图形。
- ZXUI 构建、业务类型检查、目标 ESLint 与差异空白检查通过。
- 整个工作区 convention 检查仍未通过：脚本没有排除删除文件，本轮在已删除的 SvgIcon/svgicon.js 处中断（任务前同类问题是 AlarmPanelFloating.vue）；另两项是既有 FaultBoardPanel.vue 裸色和 session.test.ts 的 axios 规范。本轮全部目标文件已单独通过 ESLint，没有宣称整个工作区门禁通过。

## 本地交付与工作区范围

为使公开 core 新导出在源码直连和已安装类型/运行时两条路径一致，构建了本地 ZXUI tar 并更新业务 file 依赖；同时将当前源码所需的同源 constants tar 纳入 resolution，修复旧安装产物缺少 buttonVariantProps 的问题。两个产物都未发布。

首次构建在修改前就因本地主题生成资产与编译器契约不匹配失败。通过库自带 `pnpm theme-compiler:build` 重生成本地资产后，完整源码构建通过；九套主题 `src/theme.ts` 的 SHA-256 均与任务前相同，没有修改主题源色值。

相对任务开始的 package.json 副本，只有 `dependencies.@zxio/zxui` 与 `resolutions.@zxio/constants` 两项变化；其他工作区依赖改动保留。两个仓库其他未提交工作没有清扫，没有自动提交或发布。

## 页面

- [默认用户页](element-icons-on-demand-2026-10-22/user-default.png)
- [森绿深色](element-icons-on-demand-2026-10-22/user-army-dark.png)
- [TopNav](element-icons-on-demand-2026-10-22/topnav-dark.png)
- [自定义菜单图标预览](element-icons-on-demand-2026-10-22/menu-custom-preview.png)
- [设计器非常用图标](element-icons-on-demand-2026-10-22/designer-watermelon.png)

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-22-element-icons-on-demand.md
EVIDENCE: READ application registration, generator and generic core implementations; SEARCH actual icon strings and nested default imports; COMMAND plan structure verified.
PLAN_CHANGES: Keep complete designer catalog isolated through the official separate EP entry; synchronize same-source constants local delivery after installed-package verification.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: current-session execution (completed with evidence above)
BLOCK_REASON: none
UNBLOCK_ACTION: none

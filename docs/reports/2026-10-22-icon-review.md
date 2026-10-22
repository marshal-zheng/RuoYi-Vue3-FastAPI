# 图标改动整体复核（2026-10-22）

后续[隔离提交记录](2026-10-22-icon-commit.md)将图标范围从完整开发工作区拆出，重新构建本地产物，并修复基线 SchemaForm 的默认按钮入口。最终提交产物与配置以该记录为准；下文保留当时联调证据。

本轮复核覆盖导航 Material Symbols、本地 SVG、Element Plus 有限注册、ZXUI core/默认入口、动态菜单、设计器选择/预览/导出及源码直连构建。确认问题已修复；业务映射继续留在业务，没有加入 ZXUI。

## 发现与修复

1. **源码直连的根入口辅助函数仍间接带入整集。** 原来的首页检查没有覆盖所有异步页面。逐视图检查确认 8 个入口的静态闭包会到达完整目录，涉及 SimulationResultDialog 和 simulation 下的辅助函数消费者。没有修改这些仿真页面：修复了库的通用源码解析与副作用契约。
   - Vite 5 的绝对文件解析跳过包的 `sideEffects` 元数据。ZXUI source plugin 的别名改为同目录相对文件委托解析，保留原解析选项、去重、公开入口及 feature 白名单。
   - `packages/components/package.json` 声明组件模块可裁剪，并显式保留 CSS、SCSS 和 style 目录。`packages/zxui/package.json` 保留公开的源样式转接文件。
   - 实际只导入 `useDialog` 和 `useRequiredThemePortalBinding` 的探针，gzip 从 **370,700 B** 降至 **10,384 B**；修复后无图标模块或完整名称表。[探针结果](icon-review-2026-10-22/root-helper-probe.json)
   - 该方法沿用打包器的模块副作用机制，没有新增注册框架或消费方全局裁剪开关。[Rollup 官方机制说明](https://rollupjs.org/configuration-options/#treeshake-modulesideeffects)

2. **图标名称会误命中对象原型属性。** `constructor`、`toString`、`__proto__` 可被误当成组件；导航 resolver 还可能返回非字符串。ZXUI capabilities 的主表和 fallback 表，以及业务 navigation 映射，均改为仅查自有属性。两个边界的参数化回归均先复现失败、修复后通过；显式配置的同名 fallback 仍有效。

3. **副作用元数据修复暴露了 Chart 源样式桥遗漏。** 独立复核的实际构建发现，`@zxio/chart/style` 未声明其 TS 转接入口，新的正常裁剪会丢掉样式。已在拥有该契约的 Chart 包补齐 `**/style/index.ts`；其已发布形式的构建脚本原本就正确保留 mjs/cjs/css，无需改造。真实构建回归同时断言根辅助函数无图标模块，以及 ZXUI、Chart 的 CSS 均保留。其他已接入 feature 的公开样式入口也已核对。

4. **生成表单的运行测试依赖表未同步。** 导出文件已使用 `@zxio/zxui/core`，旧测试还只允许默认入口，因而没有验证实际交付契约。已改为真实 core 组件和独立 ThemeProvider，完整生成表单的挂载、验证、重置和提交通过。

## 构建与加载边界

[修复前](icon-review-2026-10-22/routes-before.json)与[修复后](icon-review-2026-10-22/routes-after.json)使用生产 manifest 遍历静态依赖，覆盖 **115 个业务视图**；完整目录泄漏 **8 → 0**。独立的设计器选择器作为预期异步入口另行检查。

普通入口含 84 个 EP 图标定义，完整目录不在入口闭包。84 包含业务有限表和底层控件的固定图标，并非当前屏幕可见数量。[完整构建结果](icon-review-2026-10-22/build-results.json)

新增业务命令 `yarn icons:check [构建目录]`，检查首页及全部业务视图的静态闭包，检测完整目录引用和整集图标定义。维护入口和源码直连构建命令见 [src/icons/README.md](../../ruoyi-fastapi-frontend/src/icons/README.md)。该业务检查规则没有进入 ZXUI。

完整图形目录仍按功能加载：打开完整选择器或恢复非常用有效图标时加载整份目录。这项边界保持原约定；不是逐图标网络请求。普通业务不安装完整图标插件，构建期组件 resolver 的 namespace 导入仅用于构建。

## 验证

- ZXUI 相关 **25 项通过**，含 source plugin 的真实构建回归、样式桥和 capability 边界。[日志](icon-review-2026-10-22/library-tests.log)
- 业务相关 **28 项通过**，含未知名称、非常用保存图标恢复、原生设计器控件、导出契约及生成表单运行。[日志](icon-review-2026-10-22/business-tests.log)
- ZXUI 聚合构建、业务源码直连生产构建、业务类型检查、theme-compiler 类型检查、目标 ESLint 和差异空白检查通过。未宣称整个工作区的所有门禁通过。
- 本地业务 **14 项浏览器检查通过，页面运行错误 0**：[结果](icon-review-2026-10-22/browser-checks.json)。验证菜单原 `system` 标识、自定义 `bug` SVG、完整选择器 293 项 SVG、Watermelon 预览且未全局注册、无效名称空图形、实际导出组件绑定、默认浅色/森绿深色、折叠尺寸、TopNav，以及真实缓存监控页面的 Chart 样式。
- [实际下载的生成文件](icon-review-2026-10-22/generated-form.vue)经 SFC 编译确认 Watermelon 为 import binding；没有保存菜单变更。浏览器已关闭，开发服务继续运行。

115 个视图的证据是生产依赖闭包检查；浏览器只运行上述受影响页面，没有声称逐页人工验证全部视图。主题源色和尺寸策略未改。

## 交付与责任边界

- 业务：导航映射、自定义 SVG、有限 EP 名称、设计器旧字符串数据与导出规则。
- ZXUI：通用图标解析、能力注入、公开 core/默认入口和源码解析。
- Chart：自身源码样式转接的副作用声明。该包是独立 Git 仓库，本轮只有对应 package.json 声明变更，原有 README 改动保留。
- 本地 ZXUI tar 已更新为 `zxio-zxui-3.0.0-next.0-icons-review.20261022.tgz` 并更新业务 file 依赖，未发布 npm。相对本轮开始的 package.json，仅更新 ZXUI file 依赖并新增 `icons:check`；此前 constants resolution 和其他依赖保持。
- 本轮没有提交、推送或清理无关工作区改动。

## 页面证据

- [默认用户页](icon-review-2026-10-22/user-default.png)
- [森绿深色折叠导航](icon-review-2026-10-22/collapsed-army-dark.png)
- [TopNav 深色](icon-review-2026-10-22/topnav-dark.png)
- [菜单自定义 SVG](icon-review-2026-10-22/menu-custom-preview.png)
- [Watermelon 预览](icon-review-2026-10-22/designer-watermelon.png)
- [缓存监控样式](icon-review-2026-10-22/cache-chart-style.png)

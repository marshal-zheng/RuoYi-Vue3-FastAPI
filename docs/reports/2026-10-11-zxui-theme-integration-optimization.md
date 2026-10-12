# ZXUI 与真实业务主题优化实施记录

日期：2026-10-11。业务：RuoYi Vue3 + FastAPI；组件库：本机 `/Users/hqz/Downloads/element-plus`。

## 结论与责任归属

当前工作区的顶部、Logo、侧栏主背景在修改前已经使用 ZXUI surface，展开状态的明暗切换正常。本轮实际复现的顶部问题来自业务：折叠 Logo 的 `collapse` 状态类与 Tailwind 工具类冲突，计算样式为 `visibility: collapse`，导致整个 Logo 表面被隐藏。ZXUI 的 header token 已经正确切换，无须重做主题配色。

业务改为 `is-collapsed` 后，Logo 恢复可见并与顶部同色。未启用图片 Logo 时，折叠区域展示标题前两个字符，完整标题保留在链接的可访问名称及提示中。

## 已实施

### 业务外壳

- 顶部 hover 文字改用 header 的 on-text；普通侧栏 hover 保持 panel 前景，选中态及折叠选中态使用 selected 前景，避免混用 accent 或其他 surface 的文字颜色。
- 侧栏 hover 圆角复用已有主题圆角变量，移除两处固定 8px。
- 修正 `overlay.css` 位于规则之后而失效的 import；该文件的 split-pane 固定白底同时改为 panel token，避免修复 import 后重新引入白块。
- 移除生产接入中手写的 html 主题属性投影；Provider 和 body 浮层 scope 由 Host 管理。旧 `projectZxThemeScope` 保留为弃用兼容函数，生产不再调用；现有内部调用契约没有强行删除。

### ZXUI 公共接入

- `@zxio/zxui/theme-host` 和 `/theme-host/precompiled` 新增 `createThemePreferenceController`、`bindThemePreferenceController`。
- 公共控制器管理快速请求合并、事务完成后的偏好发布与持久化、更新失败保持和存储失败提示；事务仍由现有 Runtime 执行。
- 业务只保留主题目录校验、偏好迁移、存储 key 及中文提示。删除页面树中的桥接组件，Host bind 后直接绑定公共控制器，并在卸载时清理。
- 公共 `@zxio/theme-compiler/vite/source` 支持 Node 侧工具直接加载同一工作区源码。业务本地模式使用工作区自带的 tsx，正常安装模式继续使用 `/vite`。
- 源码插件将根结构样式入口指向 `packages/theme-chalk/src/structural.css`，不再依赖生成镜像刷新；主题 seed 的编译边界保持原样。

### 元数据压缩

将 docs 已有的字符串、对象形状及 digest 字典编码器移至 Compiler。公共 Vite 插件和 docs 使用同一实现；生成模块自带解码代码，不增加浏览器解码依赖。

| 指标 | 原虚拟模块 | 优化后 | 降幅 |
| --- | ---: | ---: | ---: |
| 原始 JavaScript | 6,744,285 B | 1,478,253 B | 78.1% |
| gzip | 1,022,164 B | 444,744 B | 56.5% |
| Brotli | 429,584 B | 287,217 B | 33.1% |

9 个主题、2934 条部署记录，解码后 `JSON.stringify` 完全相等。所有原有 CSS 路径、SHA-256 和 SRI 字段保留。这是部署虚拟模块的测量，不代表整个应用包或首屏耗时的同比改善。

## 验证证据

- 浏览器实际登录本地后端，页面为 `/system/user`，没有使用 mock 页面替代主题验证。
- 9 个主题 × 明暗两种模式，共 18 组；顶部、Logo、侧栏共 54 个背景采样均匹配对应 surface fill。所有组 Logo 可见，顶部与 Logo 背景相同。
- 核对展开/折叠导航、科技蓝深色下 body 挂载的用户菜单、紧凑/宽松密度与刷新持久化。
- 最终恢复初始的空军深蓝灰、深色、宽松密度及展开侧栏。刷新后状态保持，html 没有额外主题属性，实际加载结构样式的路径为源码 `structural.css`。
- 五个新增/改动 TypeScript 源文件的局部语法与语义诊断为 0；这不是全仓 typecheck。
- 两个仓库 `git diff --check` 通过。遵照用户要求，没有运行 lint/build，没有新增、修改或运行测试用例，没有手改 generated/dist。
- 验证期间出现过后端启动前请求失败、删除旧桥接组件时的瞬时 HMR 错误，以及一次登录 token 失效；完整刷新和重新登录后，最后 18 组主题验证没有新增控制台错误。没有把它们计为主题功能通过的证据。

证据文件：

- [部署模块字节与无损校验](evidence/2026-10-11-zxui-theme-assessment/deployment-optimized.json)
- [18 组浏览器 surface 采样](evidence/2026-10-11-zxui-theme-assessment/browser-theme-matrix.json)
- [科技蓝深色、折叠导航与浮层](evidence/2026-10-11-zxui-theme-assessment/tech-blue-dark-collapsed.jpg)
- [恢复后的空军深蓝灰展开页面](evidence/2026-10-11-zxui-theme-assessment/air-gray-dark-expanded.jpg)

## 本轮边界

保留两个仓库既有修改；没有重写 Kernel、主题 seed 或调色方案，也没有扩大到仿真模块、业务图形分类色及所有历史 Tailwind 工具类。公共源码链路已验证，发布包构建、打包后的消费者链路、故障注入及全量回归尚未验证。

公共 API 及本地源码工具用法已补充到 ZXUI `docs/zh-CN/guide/theme-operations.md` 和 `packages/theme-compiler/README.md`。

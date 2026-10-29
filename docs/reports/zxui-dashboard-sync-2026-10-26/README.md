# RuoYi：ZXUI / Dashboard / Grid 本地配套同步

2026-10-26，本地源码与安装包消费均已验证，最终配套包已装入当前 RuoYi 工作区。此次没有 commit、push 或 npm 发布，也没有关闭 WI-0008。

## 实际改动与选型

- RuoYi 在既有 `src/theme/zx-theme-host.ts` 的 precompiled Host 登记公开 `dashboardThemeBundle`，沿用默认启用登记模块的语义。继续使用现有 Provider、deployment API、偏好控制器及 body portal 镜像。没有新增 Host、复制 Grid token 映射或改写业务布局。
- 同步 **17 个必要配套包**：ZXUI、Dashboard、Grid、tokens、theme-compiler、theme-css-codec、theme-consumer、9 个登记主题和 theme-tailwind。Yarn resolutions 固定核心/协议/编译器/Grid 的传递引用；保留现有 Vite dedupe。Vue **3.5.44**、Element Plus **2.14.7**、Vite **5.4.21**。
- 复用公开入口与既有宿主管理机制，使核心、主题、扩展和构建校验共用当前契约；代价是需要一起交付这组本地包，不能只替换 Dashboard/Grid。Yarn `file:`/resolutions 的用法见[官方说明](https://yarnpkg.com/configuration/manifest#resolutions)，依赖去重沿用 [Vite 既有能力](https://v5.vite.dev/config/shared-options.html#resolve-dedupe)。
- 当前 `package.json` 与权威 **Yarn 4.9.2 yarn.lock** 已更新；`yarn install --immutable` 通过。未将旧 package-lock 作为安装输入。历史 vendor 包作为既有验收证据保留，当前依赖图不选用被替换版本。

### 业务对照发现并修复的构建缺陷

初轮生产包的侧栏子菜单图标与源码模式不同。业务原有 CSS 通过 `navigation-menu-icon` class 隐藏嵌套图标；产物丢失这个 class，因此没有遵守业务规则。

实证归因：Vue 插件虽然配置 `isProduction: true`，仍在通常未预设 NODE_ENV 的 Rollup 构建进程中复用含注释的 SFC AST，生成 `DEV_ROOT_FRAGMENT`。生产 Vue 不执行开发期 Fragment 根查找，导致外部 class、style、aria 等属性无法落到真实节点。官方依据见 [Vue renderComponentRoot](https://github.com/vuejs/core/blob/v3.5.44/packages/runtime-core/src/componentRenderUtils.ts)、[compiler options](https://github.com/vuejs/core/blob/v3.5.44/packages/compiler-core/src/options.ts)；实际版本解析与生产 runtime 探针见 [review-compile-probe.json](review-compile-probe.json)。

ZXUI 新增共享 `internal/build/src/plugins/production-vue.ts`，显式设置 `comments: false`，modules/full-bundle 两入口复用它，保留原 hoist/cache 和 BetterDefine 策略。先用相同注释/条件根模式的两个真实 Rollup→生产 Vue SSR 用例复现 attrs 丢失，再修复通过；独立 reviewer 另用真实 Icon 模板和生产 renderer 验证。最终业务截图与 DOM 确认 class 透传恢复，嵌套图标显示策略与源码一致。没有改业务 CSS 或 Icon 组件来掩盖构建问题。

## 最终身份

| 项目 | 最终值 |
| --- | --- |
| ZXUI | `zxio-zxui-3.0.0-next.0-dashboard-theme.20261026.1.tgz` |
| ZXUI SHA-256 | `451333dc1248cc68cf391a2e6395e24ddd443a9afc76d994d2463530b0f1bbfb` |
| Dashboard | `zxio-dashboard-0.1.0-dashboard-theme.20261026.tgz` |
| Grid | `zxio-vue-grid-layout-1.0.6-theme.20261026.tgz` |
| Grid SHA-256 | `265198c9231d7b6f1001130df11b212f99e892d0e0ffa36dd461b72a5cbbb46d` |
| 核心契约 | `sha256:bb14425c9adb15ad223670c7b84c6ac93f035ec0ad21127a298fba59263b4c37` |

完整 17 包名、版本、来源和 SHA-256 见 [package-identity.json](package-identity.json)。**7,144 个打包文件与实际安装内容全部相同**，主代理和 reviewer 分别复核；可重跑 `python3 docs/reports/zxui-dashboard-sync-2026-10-26/verify-installed.py`。9 个登记主题及 Tailwind adapter 与 Grid 的核心要求一致；Vue、runtime-core、tokens、consumer、codec、Grid 均只有一个物理安装根。见 [安装核验](installed-files-final.json)、[依赖/契约](installed-identity.json)、[独立探针](review-probes.json)。

初轮核心包已被 `.1` 替换并移除本轮废弃 tarball；`baseline/` 和 `packed-before-icon-fix.png` 保留问题证据。`browser-checks.json` / `interactions.json` 中的初轮 packed 记录不是最终产物的验收依据。

## 验证结果

| 检查 | 结果与证据 |
| --- | --- |
| Host 接线先红后绿 | 初次缺少扩展而失败，登记后通过；`logs/host-red.log`、最终消费者测试 |
| 库主题/Host 回归 | 3 文件 **30 项通过**；`logs/library-tests.log` |
| 构建/属性透传/图标回归 | 新模式用例先 **2 项失败**，修复后与 Icon、alias、module-inputs 合计 **17 项通过**；`logs/production-vue-{red,green}.log` |
| ZXUI 构建与构建源码检查 | `pnpm build`、`typecheck:node`、4 文件 ESLint 通过；`logs/zxui-build-final.log`、`build-types.log`、`build-lint.log` |
| 消费者类型与回归 | `vue-tsc --noEmit`；3 文件 **10 项通过**；`logs/consumer-{types,tests}-final.log` |
| 前端规范与生成器 | conventions changed 检查通过；最终 `yarn ui:standards` **25 项通过**；`logs/frontend-conventions.log`、`ui-standards-final.log` |
| 源码直连生产构建 | **42.09 秒**；9,616 模块、1,347 个库源码模块、0 已安装 ZXUI 模块；`logs/source-build.log`、`source-module-summary.json` |
| 最终安装包生产构建 | **38.31 秒**；8,583 模块、**0 库源码模块**、单一 runtime-core；`logs/packed-build-final.log`、`packed-module-summary.json` |
| 锁文件 | Yarn 4 安装及最终 immutable 安装通过；`logs/yarn-{install,immutable}-final.log` |
| 独立复审 | 最终无剩余 P0/P1/P2；独立重跑新构建回归 2 项、消费者 7 项通过；[review.md](review.md) |

构建保留已有的 chunk size、Sass legacy API、Browserslist 和 Vite CJS API 提示；Yarn 有既有 Vitest/coverage、Formily Vue peer 与 testing-library peer 提示。没有将这些提示隐藏或称为全仓零告警。模式回归的极小 fixture 还产生未使用外部 helper 导入提示，不影响生产 runtime 的 attrs 断言。

## 真实业务验收

使用已授权的 **headless Playwright**，访问真实 8088 后端及独立本地前端端口；没有 mock 业务响应。目标为 `/monitor/server` 的现有持久化服务器监控仪表盘。没有修改仿真专用代码，也不据此声称仿真页完成验收。

- **源码直连**：8 个稳定采样，默认浅/深、钢蓝深色、紧凑、导航返回与恢复；真实 Grid 始终 ready，与最近 Provider 同为 `scope:vfadmin:root`。背景、文字、边框按实际计算样式检查。见 [source-browser-checks.json](source-browser-checks.json)。
- **最终 `.1` 安装包**：7 个稳定采样，默认浅/深、钢蓝紧凑、宽松、导航返回、1280×800 和恢复。按钮计算高度 **36 → 32 → 40px**，Grid 公开 toolbar padding token **8 → 6 → 10px**；面板领域尺寸维持原布局，未把 token 值冒充本页未展示的引擎工具条测量。
- 面板最大化/还原、编辑菜单、拖拽草稿、CPU 时序图设置预览后取消、三轮额外明暗切换、ArrowRight 到 memory / Home 回 cpu、在线用户页面往返均通过。拖拽后的 CPU transform 为 y=528，浏览器重新加载丢弃草稿后恢复 y=0。没有点击保存布局/保存设置；最后服务器布局仍为 **版本 11**，CPU trend 草稿已丢弃，捕获到的 Dashboard 写请求为 **0**。
- Grid 面板菜单继承最近 scope，深色钢蓝菜单背景 `color(srgb 0.132508 0.195764 0.26262)`、文字 `color(srgb 0.9152 0.9517 1)`。原生 EP 主题菜单消费现有 Host 镜像到 BODY 的根主题/variant；没有把它误记为含独立 Provider scope 的菜单。
- 最终验收期间 **0 pageerror / console error / warning / Grid 诊断**，只有 1 个 Grid consumer。登录前的预期 401 单独保存在 setupErrors；初轮跨端口复用会话出现 403，独立重新登录后才开始该端口验收。初轮依赖安装时的旧优化缓存错误不计为已冻结候选包的验收结果。
- 已目视复核最终主题、密度、菜单和小视口截图。1440×1000、1280×800 无页面横向溢出；导航、业务控制条和 Designer 工具条均在视口内，菜单无异常裁切或遮挡。监控页面原本纵向滚动，固定面板内部数据和下方表格不保证同时位于首屏。

最终证据：[final-browser-checks.json](final-browser-checks.json)、[验证汇总](verification-summary.json)、`screenshots/final-*.png`。测试脚本采样曾发现过早读过渡样式及页面句柄闭包问题，相关采样已用明确页面参数、稳定截图和 URL 断言覆盖，最终结论只取上述明确分组文件。

## 隔离、清理与边界

两仓起始 HEAD/status、指定文件起点及本轮 diff 保存在 `baseline/`。RuoYi 原有 file-assets/minio、AI、后端、Vite 代理等改动保留；`vite.config.ts.task.diff` 为空，本轮没有覆盖它。库只新增生产模板 helper/测试，并让两构建入口复用；原有未提交修复保留。最终源码哈希见 [source-inputs-final.json](source-inputs-final.json)，原始冻结输入继续保留。

本轮浏览器已显式关闭，3310/3311 服务已停止，仅清理本轮 `.tmp/zxui-dashboard-sync`。原 **80 / 8088 / 5173** 服务仍在，偏好恢复为本轮隔离会话初值，业务布局未保存。临时构建配置已保存在 [acceptance.vite.config.mts](acceptance.vite.config.mts)，生产输出是验证用临时目录，实际交付为 vendor 包、清单/锁文件和源码变更。

未运行全仓所有测试，没有外部发布、正式版本迁移、RuoYi SSR 或新一轮 docs SSR 验收的结论；WI-0008 仍由用户单独验收。下一步是按此报告验收本地配套交付，再单独安排有明确授权的提交/发布。

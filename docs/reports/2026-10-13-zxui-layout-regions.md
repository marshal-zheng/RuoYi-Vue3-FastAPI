# ZXUI 通用区域布局与业务接入

本轮已完成通用布局、业务接入及隔离 Chromium 验证。Tags-Views 默认 `false`；Header 和面包屑默认显示，可分别配置。当前版本保存的用户偏好继续生效；未标版本的旧 Tags-Views 偏好一次迁移为关闭，其他布局偏好保留（见后续修正）。未提交或发布；保留两个仓库的其他已有改动。

## 职责与使用

ZXUI 在 `/Users/hqz/Downloads/element-plus` 提供 `ZxPageLayout`：

- 默认自然高度；`fill` 显式接收确定高度的父 Grid/Flex 剩余空间。
- Header/Footer 按实际内容占位，正文接收剩余高度。
- `scroll="body"` 由正文滚动；`scroll="none"` 将滚动交给表格、Tabs 或编辑器。
- `sticky-header` 为自然高度区域提供 CSS 吸顶；满高区域的 Header 原本就处于正文滚动区之外。
- 满高正文是 `data-zx-fill-root`；组件本身是 fill 链环，嵌套区域接收父正文空间。
- 公开根出口、leaf 出口、安装注册、类型、全局 Vue 类型、独立样式与中英文文档均已接入。

组件不读取路由、应用设置、视口或业务信息，也不创建观察器、全局监听或连续测量任务。

业务负责显隐与页面意图：`src/layout/policy.ts` 处理偏好和当前路由 `meta.layout` 的布尔覆盖，离开路由自动恢复偏好，不将覆盖写入本地存储。应用壳改为正常流 Grid/Flex；Header、Tags、版权区按实际占位分配高度，取消 50/84/94.5px 等应用高度扣减。隐藏 Header 后保留导航与设置入口。原 `fixedHeader` 设置此前没有独立的布局效果，本轮改为 `headerVisible`；应用顶栏保持在内容滚动区之外。

```ts
// 可选的业务路由覆盖
meta: {
  layout: { headerVisible: false, tagsView: false, breadcrumbVisible: false }
}
```

| 页面类型 | 布局与滚动 |
| --- | --- |
| 满高列表 | ContentWrap / GridList fill，表格内部滚动 |
| 普通详情、生成器配置、生成的普通 CRUD | 自然高度，由 AppMain 正文滚动 |
| 摘要 + 列表的详情 | ContentDetailWrap fill，摘要占位，Tabs/列表取得剩余空间 |
| 拓扑、设备图形详情 | 明确 fill 锚点，图形区域接收正文空间 |
| 表单设计器 | CSS 分配各栏与工具条，属性区和画布各自滚动 |
| iframe | 接收 AppMain 正文空间，取消 document 高度测量 |
| 缓存浏览器 | 各原生 Card/Table 接收所在面板空间，表格内部滚动 |

修改了 Vue 3 两个生成器模板的页面外壳，采用自然高度 PageLayout。未修改仿真专用源码。

## ContentWrap 与资源生命周期

旧实现每个已挂载 ContentWrap 都注册 1 个 ResizeObserver、window resize 与 document capture scroll，即使没有启用 footer。现在只有区域外的旧式视口固定底栏启用这些资源；关闭底栏、改为 fill、进入有界布局和卸载时会断开观察器、移除监听、取消 RAF，并使排队的 nextTick 回调失效。

区域内的满高底栏按正常流占位；自然高度底栏用 CSS sticky。为使 sticky 正常工作，仅在该场景取消原生 Card/Body 的滚动裁剪，滚动仍由宿主正文拥有。

验证中还修正了 X6 已有的清理目标不一致：`autoResize: true` 观察父节点，X6 销毁时却清理图容器。本轮捕获原目标，使用公开 `SizeSensor.clear` 清理后再 dispose；保留原有单个传感器与缩放行为。独立复查交替启用/关闭 Scroller 6 次，尺寸响应与卸载回收均通过。

## 已通过的验证

| 验证 | 结果 |
| --- | --- |
| ZXUI PageLayout + ContentWrap 单测 | 27/27 |
| 业务显隐策略与偏好单测 | 5/5 |
| UI standards | 505 文件，0 违规；相关 14 个测试通过 |
| ZXUI 构建 | `pnpm build` 通过 |
| ZXUI/Components 公开包契约及 ZXUI build externals | 聚焦检查通过 |
| 业务生产构建，源码模式 | `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod` 通过 |
| 安装包 fixture 生产构建 | 通过 |
| 业务聚焦 ESLint | 0 errors；保留已有 warnings |
| 后端模板检查 | changed validation 通过；既有生成器测试 4/4；两个 Jinja 模板语法检查通过 |
| diff 空白检查 | 本轮路径通过；混合 CRLF 文件用 `cr-at-eol` 规则检查 |

两种模式各完成 **96 组**：3 个视口（1440×900、1024×768、390×800）× 4 种内容（列表、长详情、混合详情、真实 X6 编辑器）× 8 种 Header/Tags/面包屑显隐组合。额外验证短详情、嵌套区域、sticky 操作栏/摘要、iframe、版权占位、路由覆盖恢复、移动抽屉和真实表单设计器。

夹具使用实际业务壳和实际组件，仅替换登录、菜单目录、主题选择控件及数据来源。未操作现有浏览器窗口，未改业务数据。两种模式浏览器均无 pageerror。

### 性能证据与边界

| 指标 | 源码模式 | 安装包模式 |
| --- | ---: | ---: |
| 布局/ContentWrap 新增观察器 | 0 | 0 |
| 布局/ContentWrap 全局监听注册 | 0 | 0 |
| 布局/ContentWrap DOM 矩形读取 | 0 | 0 |
| 布局/ContentWrap RAF 调度 | 0 | 0 |
| 5 轮列表→编辑器→详情前后活跃观察器 | 6→6 | 6→6 |
| 动画结束后 500ms 空闲 LayoutCount | 0 | 0 |
| 40 次显隐更新 LayoutCount | 40 | 40 |
| 上述布局总耗时 | 6.203ms | 6.256ms |
| 更新到两次 RAF 的 P95 | 16.8ms | 16.7ms |

显隐变化仍会引起必要的浏览器布局；这里验证没有额外测量链和空闲重排循环。耗时是本机带探针的 Chromium 诊断值，不代表所有设备，也不是旧应用壳的帧率对照基准。

探针为检查注册目标而持有观察器实例。5 轮列表切换记录到 10 个脱离文档的 Element Plus Table 观察目标，与不使用本轮布局组件的原生 Table 对照完全相同；活跃文档目标数量没有增加。这不是浏览器垃圾回收结论，未据此声称第三方组件的所有资源均已修复。

独立只读审查发现并已修复：嵌套区域的正文 flex 传递、sticky footer 的原生 Card 裁剪、移动抽屉定位优先级、RightPanel 空 Tabs 占用一半高度、自然详情 sticky header 被包装层限制。所有发现及 X6 修复已通过复查。

## 全项目检查的范围外阻塞

没有将以下失败当作本轮通过：

- 普通安装包生产构建在布局源码处理前被现有 Theme Manifest 的 elementPlus/tailwind adapter identity 校验阻塞。源码模式生产构建与安装包布局夹具构建均通过。
- `yarn type-check`：`src/utils/http.test.ts:31` 调用参数不匹配；`vite/zxui-theme-packages.ts:54` 的现有 featurePackages 类型不接受 theme-tailwind。本轮布局路径没有报错。
- 全量 `yarn test:run`：79 文件通过、7 文件失败；673 测试通过、2 测试失败。失败涉及 theme-host mock 缺少 createThemePreferenceController、4 个 Playwright 文件被 Vitest 收集、数据源测试预期菜单数量和主题切换测试。未修改这些范围外测试。
- 全 changed 前端 validation 的 lint 包含其他已有改动。所改路径与 HEAD 比较没有新增 lint errors；`device/detail.vue` 的 4 个和 `tool/gen/editTable.vue` 的 3 个原有错误仍保留。
- ZXUI 全仓包契约有 drive/chart 范围外失败；全仓 docs-sync 有 dark-mode/chart/keybindings 等已有文档缺片段。
- structural style 测试 4/5 通过；Button 样式闭包的既有体积阈值失败。去除本轮新增布局规则仍失败，Button CSS 字节数未因布局增加。未放宽阈值。

## 交付与复现

业务 vendor 引用本轮 `zxio-zxui-3.0.0-next.0-layout.20261013.tgz`。由于当前 checkout 的组件依赖新增 hooks 导出，配套打包 hooks，并用 Yarn resolution 固定 `zxio-hooks-1.0.5-layout.20261013.tgz`，避免新组件配旧 hooks。没有发布 registry 包。产物来自当前 checkout，保留该 checkout 的已有实现。构建时曾为现有可选 locale 修正共享反馈 helper 的空值回退，以通过库的类型构建。

- [夹具说明](../../ruoyi-fastapi-frontend/tests/fixtures/layout-regions/README.md)
- [浏览器检查脚本](../../ruoyi-fastapi-frontend/scripts/check-layout-regions.mjs)
- [源码模式原始证据](evidence/2026-10-13-zxui-layout-regions/browser.json)
- [安装包模式原始证据](evidence/2026-10-13-zxui-layout-regions/installed/browser.json)
- [隐藏顶部区域后的列表](evidence/2026-10-13-zxui-layout-regions/hidden-list.png)
- [表单设计器](evidence/2026-10-13-zxui-layout-regions/form-builder.png)

## 后续修正：旧缓存覆盖默认隐藏

用户截图显示页签仍然开启。端口 80 的服务已加载 `tagsView: false` 与新布局源码，但 Store 原先直接采用旧 `layout-setting.tagsView: true`，因此改默认值无法影响旧缓存。上一轮保留旧偏好的处理遗漏了这次默认值变更的迁移。

修正完全位于业务层：`LAYOUT_SETTINGS_VERSION = 1`；未标版本的缓存首次启动时只重置 Tags-Views 为当前默认，并写入 `layoutVersion`，其余字段保留。设置面板保存同一版本，所以后续用户主动开启、保存、刷新后仍保持开启。无缓存用户仍默认隐藏。损坏的布尔值与非对象缓存使用默认值；存储无法写入时继续使用迁移后的内存偏好。该处理只有启动时读取，以及旧版本缓存的一次写入，不增加观察器、监听或持续计算。

已先确认两个新增单测失败及浏览器旧缓存场景失败，再验证修正：策略与偏好测试 7/7 通过；真实 Store + 真实 Settings 面板的隔离 Chromium 回归通过迁移、保留其他偏好、手动开启/保存/刷新、新用户默认，以及内容区高度（隐藏 900px，开启 860px + 页签 40px）。验证时仅替换主题适配器和原夹具的身份、目录与数据输入。端口 80 已确认交付新迁移源码；现有页面刷新后应用迁移，不需要清除所有设置。

- [迁移浏览器回归](../../ruoyi-fastapi-frontend/scripts/check-layout-preferences.mjs)
- [原始证据](evidence/2026-10-13-zxui-layout-regions/preferences.json)

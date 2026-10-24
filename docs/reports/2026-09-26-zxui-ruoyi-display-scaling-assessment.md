# RuoYi × ZXUI Display Scaling 评估与方案讨论

日期：2026-09-26。性质：源码评估与设计建议，尚未实施 Display Scaling。

联网调研补充：[企业级产品与项目参考](./2026-09-26-enterprise-display-scaling-research.md)。该补充把下文的倍率公式限定为基准值，并进一步推荐组件尺寸配方、交互下限与内容驱动布局；以补充中的修正说明为准。

结论：建议由 ZXUI 提供可复用的显示缩放契约，由 RuoYi 接入用户偏好并迁移应用布局尺寸。现有 density、组件 size、主题配色都不能替代 Display Scaling。两侧都有工作，但通用组件尺寸的缺口应首先在 ZXUI 解决。

用户补充进一步确定了成功标准：默认大小可以保留；客户觉得整体太小时，可以统一调大；系统应主动适配有限空间，避免意外折行、裁切和操作丢失。长期收益来自「统一显示比例 + 统一布局适配规则 + 统一消费契约」，单独一个倍率参数不够。

## 评估边界与证据

- 业务：`/Users/hqz/dev/RuoYi-Vue3-FastAPI`，当前 HEAD `06859d0`。
- ZXUI：`/Users/hqz/Downloads/element-plus`，当前 HEAD `464f894c`。
- 两个目录都有大量未提交修改；本评估读取当前工作区，没有回退、覆盖或提交已有工作。
- 已检查主题 Kernel、编译器、EP/Tailwind adapter、Host/Provider、结构样式、图标、弹框，以及业务主题登记、偏好、启动、导航布局、表单策略、分页、VXE 接入和仿真表格线索。
- 业务 `.env.development:22–23` 已配置 `VITE_ZXUI_LOCAL=true` 和指定 ZXUI 源码目录；Vite 已有源码 alias 与主题 deployment 更新逻辑。后续可直接复用，不需要先发布 npm。
- 本轮没有运行浏览器交互、截图或新增测试。结论是源码事实与设计推论，不能当作四档缩放已经通过真实页面验证。
- 早先主题审计文档、截图和矩阵是历史材料，不作为本轮缩放功能已验证的证据。

默认建议边界：整个产品的控件和应用外壳缩放；图表标签、图例、工具栏跟随；图表数据、仿真世界坐标、拓扑节点业务坐标、文档内容及导出物不因个人显示偏好发生变化。仿真专用控件是否纳入首批迁移仍需收敛；本轮没有修改这些目录。

## 已确认的缺口及责任

| 发现 | 源码证据 | 对目标的影响 | 责任 |
| --- | --- | --- | --- |
| 当前没有 Display Scaling 请求字段 | ZXUI `packages/zxui/theme-runtime/selection-resolver.ts:15` 只接受 themeId 与五个主题轴，未知字段会被拒绝 | 业务不能直接塞入 `scale` 并假设生效 | ZXUI |
| density 主要改变纵向节奏 | ZXUI `packages/tokens/src/kernel/derivation.ts:1658`；默认主题生成 CSS 三档均为 14px 基础字，control-y 为 6/8/10px | 字体、图标、导航宽度不会按比例改变 | ZXUI 能力扩展，保留 density 原语义 |
| EP adapter 明确放过大量几何尺寸 | ZXUI `packages/theme-compiler/src/adapters/element-plus/passthrough.ts:223` 的 GEOMETRY 列表 | 菜单高度、分页宽高/字体、Tabs 高度、Card padding、Checkbox 尺寸等不会仅靠现有 token 全部缩放 | ZXUI 的 EP 适配层 |
| ZXUI 自身布局也有固定尺寸 | `packages/theme-chalk/src/structural.css:577` 起，弹框边距、标题、正文、页脚等为 px；`packages/components/dialog/src/constants.ts:33` 的预设宽度为 440/640/880/1120 | 光改字体 token 会让弹框拥挤，光改业务无法修复所有消费者 | ZXUI |
| 图标数值 size 是像素语义 | ZXUI `packages/components/icon/src/props.ts:50` 默认 16；`icon-core.vue` 各渲染分支转交 size，iconfont 分支转换为 px | 图标不会自动跟随根字号；改 API 时还要避免破坏既有显式尺寸语义 | ZXUI 定义可缩放默认值；业务迁移 UI 数值调用 |
| RuoYi 外壳尺寸重复声明 | `src/assets/styles/theme.module.css:102`；`src/layout/components/Navbar.vue:2`；`AppMain.vue:41`；`src/assets/styles/sidebar.css:108`；`variables.module.less:24` | Header 50、Tags 合计 84、折叠栏 54、展开栏 200 分别参与宽高和偏移计算，只改一处会错位 | RuoYi |
| 旧组件 size 与 ZXUI 分离 | `src/main.ts:101` 起 EP 读取 size Cookie，ZXUI 固定 default；`src/components/ui/SizeSelect/index.vue:37` 切换后 reload | 不是全局缩放，且同页可能混用不同组件尺寸策略 | RuoYi 偏好接入；ZXUI 支持统一能力 |
| 表单布局策略集中但仍是 px | `src/components/ui/FormDialog/policy.ts:3`，标签 100px、间距 20px、最小列宽 280px | 控件放大后标签和列宽若不跟随，表单会过早挤压 | RuoYi；控件高度仍归 ZXUI |
| Tailwind 有独立主题与尺寸体系 | `src/main.ts:20` 起同时加载 theme.module.css / tailwind.css；两者有自己的 `@theme`；ZXUI Tailwind adapter 目前仅映射有限尺寸角色 | 默认 rem 类、任意 px 类与 ZXUI 可能产生三套尺寸变化路径 | ZXUI 提供正式映射，RuoYi 收敛消费入口 |
| 第三方表格没有统一尺寸投影 | `src/plugins/vxe-table.ts:39` 起仅注册插件、语言、renderer；仿真 `ProtocolAnalyzer.vue:263` 向 el-table-v2 固定传入 `:row-height="36"` | CSS 行高与 JS 计算尺寸必须一致；不能承诺只改 CSS 就覆盖虚拟表格 | 通用协议在 ZXUI，具体 VXE/仿真适配在消费侧 |
| 响应式判定与缩放独立 | `src/layout/index.vue:88` 的 992px；`src/components/ui/Pagination/index.vue` 初始化时读取 body 宽度决定 pagerCount | UI 放大而窗口宽度不变时，现有逻辑不一定减少菜单、分页或表单占用 | RuoYi |

这些是对新功能的阻断项，不代表所有现有设计都属于缺陷。尤其 GEOMETRY 中还包括 z-index、时长等本来就不应该缩放的值，不能整组自动替换。

静态规模扫描：业务扫描 `.vue/.css/.less/.scss/.ts/.tsx`，排除文件名中的 `.test.` / `.spec.`；按 `src/views/project/simulation/` 路径分组。统计数字只表示带数字的 px 字面量，包含注释、0px、边框、业务坐标和潜在未使用样式，也不包含无单位 JS 数值与编译后的 Tailwind 默认值，不能视为缺陷数量或工期。

| 范围 | 扫描文件 | 含 px 的文件 | px 字面量 |
| --- | ---: | ---: | ---: |
| 业务，排除仿真目录（仍包含共享组件） | 435 | 134 | 1,410 |
| 仿真目录 | 57 | 33 | 947 |
| ZXUI structural.css | 1 | 1 | 540（分布于 481 行） |

EP adapter 的 GEOMETRY passthrough 共 165 个 target。默认主题目前有 162 个 variant。

## 与之前主题一致性问题的关系

业务登记的九个主题共用同一套主题消费机制。因此本轮不是找出哪个颜色主题“支持缩放”、哪个“不支持”；当前共享尺寸链路尚未具备完整全局缩放能力，九个主题都会遇到这一限制。

当前工作区中，Sidebar 已声明 `data-zx-surface="panel"`，应用 Header 已声明 `data-zx-surface="header"`，旧导航颜色变量也已映射到 ZXUI surface token。不能再仅凭旧文件名判定它们完全没有接入主题。但尺寸仍大量固定，颜色正确不等于尺寸契约完整。

仍可确认的业务颜色旁路包括：`src/components/ui/Pagination/index.vue` 的 `.pagination-container { background: #fff; }`，以及两套加载中的 Tailwind `@theme` 品牌色/表面色。后者需要继续沿实际 class 使用和 CSS 层叠核对，不能把每个静态色值都判为正在生效的问题。此前侧栏顶部的实时表现，本轮没有重新操作浏览器验证。

建议把颜色所有权问题与尺寸所有权问题记在同一个消费审计清单中，但分别验收；放大界面不会自动修复主题颜色旁路。

## 三种可选方案

| 方案 | 覆盖机制 | 实施量与复杂度 | 风险 | 判断 |
| --- | --- | --- | --- | --- |
| A：ZXUI 统一尺寸 token + scope 内缩放 + 消费者适配 | 字体、间距、控件和布局使用可缩放尺寸；JS 消费有效尺寸 | 高，涉及 Kernel/Compiler/Host/样式/业务；可以逐批交付 | 中高，集中在 EP 局部变量、Portal、JS 测量与旧尺寸兼容 | 推荐，符合后续其他业务复用的目标 |
| B：全局 rem 改造，由 RuoYi 修改根字号 | 把需要缩放的尺寸统一换成 rem，html 根字号控制比例 | 中高；开关很少，完整迁移仍然很多 | 中高，现有 px/JS 不会自动跟随，且全局 rem 难以隔离多个 app/scope | 单一简单应用可行，这个组件库架构下不是首选 |
| C：CSS zoom | 浏览器参与布局的元素缩放，较多旧 px 可被覆盖 | 初始实现低，跨组件验证量高 | 高，混合坐标 API、浮层、拖拽、画布和 iframe 需要逐项核对 | 可研究的备选，不建议作为 ZXUI 的默认设计系统契约 |

`transform: scale()` 整页缩放按需求排除。

CSS zoom 不能被误说成 transform 的同义词：CSSWG 当前编辑草案说明 zoom 参与布局，同时区分缩放与未缩放的几何 API 返回值。这里对 C 的风险判断来自该语义与本项目浮层/画布/JS 尺寸混用的组合，尚未实测其在本项目出现故障。[CSS Viewport 编辑草案](https://drafts.csswg.org/css-viewport/#zoom-property)

## 推荐方案的具体设计

### 1. 分开三种概念

- **Display Scale**：用户感知的整体 UI 大小，90% / 100% / 110% / 125%。
- **Density**：同一显示比例下的排布松紧，如控件纵向 padding。保留 compact/default/comfortable 的现有意义。
- **Component Size**：某个组件在上下文中的语义尺寸，例如工具栏 small 按钮。这个 small 也应随全局 Display Scale 放大，而不是将全局一律切到 large。

建议界面文案用“小（90%）／标准（100%）／大（110%）／特大（125%）”，避免把 Display Scaling 的 Compact 档与 density.compact 混成同一开关。第一版只向普通用户开放显示大小即可，不必同时暴露三组配置。

### 2. 公共缩放能力归 ZXUI，用户偏好归业务

建议在 ZXUI 的 Host/Provider 配置中增加有类型、可校验的显示比例能力，并使它参与 scope 的继承、提交、Portal 投影和有效 revision。确切 API 名称需在设计阶段确定；当前代码没有现成的 `displayScale` API。

不要把新字段直接加入 RuoYi 的 preference 后整个 spread 到现有 ThemeScopeRequest：当前校验会拒绝。应先扩展库公开协议，再经单一业务入口提交。

缩放是一项用户显示偏好，建议独立于五轴主题 variant，不把四档直接乘入预编译主题组合。当前每主题 162 个 variant；增加四档编译轴会变为 648，九主题为 5,832 个组合，且相关 adapter 产物也随之增长。采用一份可参数化尺寸输出，比例由 scope 提供，更适合此处的纯比例变化。

业务本地保存档位与默认值，首屏建立 Provider/Host 时读取，存储损坏回到 100%，存储不可写也要能在当前会话使用。切换主题、明暗模式不重置比例；普通切档不 reload、不清空表单、不换 route key。

旧 size Cookie 应明确迁移或退出全局用户偏好路径。建议迁移规则待真实默认外观核对后确定，不能把 EP large 的非均匀尺寸直接宣称等价于 110%。组件调用点显式 small/large 可以保留，但要使用统一的可缩放尺寸定义。

### 3. 以尺寸 token 参与正常布局，缩放只应用一次

基准公式：`候选 UI 尺寸 = 当前 density 与组件 size 解析后的基准尺寸 × Display Scale`。联网调研后的修正：最终控件尺寸还要满足文字行盒/图标/padding 容纳、交互目标下限以及 viewport 限制；不把候选值硬编码为可能裁切内容的固定高度。

EP 现在的控件高度公式是 `controlY × 2 + offset`。应在完整公式解析后缩放，例如 `(8 × 2 + 16) × 1.25 = 40`；不能仅把 controlY 乘 1.25，后者结果为 36，不是 125%。

以下是设计示意，不是可直接接入的现有 API：

```css
/* ZXUI 在每个受管理 scope/portal 边界生成和提交 */
--zx-display-scale: 1.25;
--zx-ui-unit: calc(0.0625rem * var(--zx-display-scale));
/* 浏览器默认根字号 16px 时，1 个设计单位在 125% 下为 1.25px */
--zx-example-font-base: calc(14 * var(--zx-ui-unit));
--zx-example-control-height: calc(32 * var(--zx-ui-unit));
```

这种方式可保留浏览器默认字体偏好的作用；ZXUI 不需要强行修改整个文档的根字号。不要再同时用 html 字号乘一遍 Display Scale，否则 rem 尺寸会重复缩放。嵌套 scope 的值按绝对比例继承/覆盖，避免 125% × 125%。派生变量必须在对应 scope 边界重新绑定，不能假设继承的 CSS 自定义属性表达式一定会在子 scope 自动重新计算。

Kernel/Compiler 需要能区分可缩放 UI 尺寸与其他 dimension。不能把所有 dimension、所有 px 都机械转换：

| 应跟随 | 应保留或单独定义 |
| --- | --- |
| 字号、行高、UI 图标、控件高度、UI padding/margin/gap、表格行高、菜单与 Tabs 高度、标准弹框宽度 | viewport 的 100%、100dvh，画布世界坐标，图片/文档固有比例，z-index、动画时间 |
| 应用侧栏宽度、Header/Tags 高度、表单标签和最小列宽 | 1px 分隔线、焦点环、阴影、圆角需要明确策略，不必为了严格数学比例让细线变模糊 |

显式数值尺寸的兼容性必须文档化：已有 `ZxIcon size=16`、Dialog width 数值或内容图尺寸，不能在未区分用途时偷偷更改全部含义。优先让默认值、命名预设和 UI 尺寸 token 可缩放，业务 UI 调用点改用这些契约；原始 CSS 长度作为明确的逃生口。

### 4. 补齐 EP、Tailwind 和结构样式

- EP：从 GEOMETRY 清单中逐项提取真正的 UI 尺寸，处理组件局部声明和 size modifier 的优先级；根上写一个同名 `--el-*` 不保证压过组件内部声明。alias 与 resolved 两套编译输出都要一致。
- ZXUI：结构样式中的表单、表格、弹框、菜单、卡片、分页、Tabs、下拉内容等改用相应尺寸；修改源文件再生成结构镜像，不手改 `packages/zxui/style/index.css` 或 theme generated 产物。
- Tailwind：提供正式 spacing/typography/size 映射，业务按受管理 scope 消费。只加 ZXUI scale 变量，现有 `px-4`、`gap-3`、`text-sm` 不会自动按它变化；`h-[50px]` 等任意固定值也需处理。避免全站默认 utilities 因 scope 外变量不可用而失效。
- RuoYi：合并两份 CSS-first theme 入口中重叠的消费规则。业务只能定义自己的布局语义，不接管 ZXUI/EP 核心 token 值。

### 5. 应用布局使用单一尺寸来源

RuoYi 定义应用专属的 sidebar-expanded、sidebar-collapsed、header、tags、content-padding、form-label 等尺寸角色，引用 ZXUI 的有效尺寸能力。Header、侧栏 top、main 偏移、可用高度和 fixed-header 宽度消费同一来源。

能用 Grid/Flex 的布局关系就避免复制 `50 + 34 = 84` 常量；必须保留 fixed 布局时，统一从相同 token 或实际测量获取。表单保留 FormGrid 的响应式降列，缩放列最小宽度和标签宽度；弹框保留 viewport 最大宽高，空间不足时内部滚动，底部操作可达。

UI Scaling 不会自动改变窗口 CSS 宽度。侧栏折叠、分页简化、工具栏换行应按实际可用空间响应，不能指望 `992px` 断点天然识别 125% UI。优先依赖 flex/grid/container 尺寸；确需 JS 时读取共享有效尺寸。

### 6. 「智能」落实为可预测的空间适配规则

同一宽高的屏幕中，字号、控件和间距变大后，同屏容量必然减少。验收目标应是内容完整、操作可达、层级稳定、重排符合规则；不能承诺放大后所有元素位置不变、所有文字永不换行、全部内容仍原屏显示。

系统必须尊重用户选择的倍率。发现空间不足时调整布局，不暗中降低字号、重置倍率，也不把所有文字强制 nowrap 后裁切。保留用户在不同设备上的选择；不按年龄猜测或强制选择大小。

| 区域 | 空间不足时的统一策略 | 需要业务提供的语义 |
| --- | --- | --- |
| 字体、输入、选择、按钮 | 控件容纳字号与行高；标签和错误消息可合理换行；操作文案保持完整 | 正常文本/紧凑操作/内容展示的用途 |
| 表单 | 按缩放后的最小列宽从 3→2→1 列；必要时标签改为上方；错误提示参与高度计算 | 字段顺序、分组、整行字段 |
| 工具栏与 Header | 主操作保留；次要操作按显式优先级进入可访问的更多菜单，或整组换行 | 主次操作优先级；库不能可靠猜测哪个按钮重要 |
| Sidebar | 菜单行允许足够高度；空间不足时使用产品定义的折叠/抽屉策略；恢复空间时保留用户原选择 | 导航层级与折叠偏好 |
| Table | 行高与文字同步；列最小宽度受控；数据密集时在表格内滚动；列取舍需明示 | 核心列、可收起列、固定操作列 |
| Modal/Drawer | 宽高被 viewport 约束；头尾与正文的滚动归属明确；低高度时全部操作仍能到达 | 表单列数、主操作和正文类型 |
| Card/详情 | 内容驱动高度；长字段换行；卡片网格减少列数 | 信息分组、必要的长内容查看入口 |
| Tabs/Pagination | Tabs 可横向浏览或进入更多；分页按容器空间减少页码和辅助项 | 必须保留的导航/跳转能力 |
| 图表/仿真 | 控件和标签适配有效尺寸，绘图容器重新布局，数据坐标保持 | UI 与业务画布的明确边界 |

这些是待设计的共同规则，不表示库现在已全部支持。短操作文案应尽量不在单词/单字中间断开；长标题、表单标签、说明文字可以按语义换行。省略号只能用于已有完整内容查看路径的场景，不能替代关键业务信息。

实现优先复用已有基础：RuoYi FormGrid 已有 auto-fit、minmax、min-width:0 与标签换行；ZXUI 当前满高布局契约使用 `data-zx-fill-root` / `data-zx-fill`，ZxDialog 已有受限高度和正文滚动；ContentWrap 有页脚高度观察。这些应扩展并验证，避免另建逐页测量系统。

不能全局删除 overflow:hidden。它在弹框边界、虚拟列表、滚动容器或视觉隐藏元素中可能必要；应检查其内部是否有正确滚动区和最小尺寸。也不建议运行一个全站脚本扫描 DOM，然后随意改每个元素的字号和高度，故障将难以归因。

后续页面只需声明少量内容语义，例如表单列数、工具栏主次操作、表格列优先级和内容布局类型；ZXUI 的共享组件/布局能力处理重复规则。保留开发期诊断，指出不符合布局契约的消费者。这样长期收益才能延续到新页面和其他业务库。

### 7. Portal 与 JS 消费者必须一起设计

业务 Host 已设置 `portalTarget: document.body` 和 `portalContainerScope: mirrored`，这是可复用的基础。缩放必须跟随相同的归属边界：Select/Dropdown/Tooltip/日期面板、Dialog、MessageBox、Message 和 Notification，都要与触发它的 scope 一致；不能只给 `#app` 设置变量。

ZXUI 已有 `useThemeAdapter`、token snapshot 与 revision 订阅，不必另造全局事件总线。但目前没有有效缩放尺寸契约，应扩展这条链，让 JS 得到实际 CSS 像素尺寸，而不是只读未缩放的基准值。根字号变化、比例变化、容器变化导致的布局重新测量也要有明确路径。

虚拟表格/列表的 itemSize、缓存、滚动位置，VXE 的布局刷新，以及图表字体、图例、tooltip、容器 resize 都需要适配。只改视觉行高而不改 JS 的条目高度会使视口计算失配；这是设计风险，尚未在该业务复现为现存 bug。

图表和仿真：工具控件与文字缩放，绘图容器重新适配，数据值和世界坐标不改。富文本编辑器：工具栏/菜单缩放，用户保存的文档内容不随设置写回。iframe：宿主页不能靠 CSS 变量穿透独立文档；受控同源内容需要显式桥接，第三方页面应标明范围边界。

## 四档预期与验收

以下为当前默认基准在默认浏览器字号下的线性候选值，未做页面测量；最终尺寸还受组件配方与交互下限约束，可用空间不足时需响应式布局，不能将此表作为所有元素严格同比例的验收要求。

| 项目 | 90% | 100% | 110% | 125% |
| --- | ---: | ---: | ---: | ---: |
| 14px 基础字 | 12.6 | 14 | 15.4 | 17.5 |
| 32px 控件 | 28.8 | 32 | 35.2 | 40 |
| 16px UI 图标 | 14.4 | 16 | 17.6 | 20 |
| 50px Header | 45 | 50 | 55 | 62.5 |
| 200px 展开侧栏 | 180 | 200 | 220 | 250 |
| 20px 内容间距 | 18 | 20 | 22 | 25 |

保留分数 CSS 像素由浏览器排版；不要让 CSS 与 JS 用不同取整方式。125% 会减少同屏内容，这是预期；允许表格自身横向滚动，不能让普通表单或页面外壳产生无法到达的内容。

125% 是产品档位上限建议，不等于满足所有低视力需求。仍需兼容浏览器 200% 文本放大与窄视口重排，不能禁用浏览器缩放。W3C 分别说明了 200% 文本尺寸与 320 CSS px 重排的目标，数据表、图形等有相应例外条件；本评估不构成合规通过声明。[Resize Text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html)、[Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)

推荐少量高价值验收，而非建立大量镜像测试：

1. **库契约**：100% 基准不漂移；四档比例；density/size 与 scale 组合只作用一次；无效输入；嵌套 scope 与 body portal 一致；主题变化不丢比例。
2. **真实业务主链**：侧栏展开/收起、Header 与 Tags 开关、用户管理表格、两/三列表单、Modal/Drawer、下拉/日期面板、分页/Tabs、滚动和焦点；切档保留正在编辑的值。刻意放入长中文标题、长姓名、错误提示、空状态和多操作工具栏，检验内容完整性而非只看空白组件截图。
3. **主题覆盖**：九主题 × 明暗 × 四档，先做导航与关键尺寸/浮层的轻量覆盖；复杂交互选择代表主题和尺寸极值验证，避免把所有页面与所有主题机械做全笛卡尔积。
4. **第三方与边界**：真实 VXE 长表、窄窗口、低高度弹框、图表和选定仿真工具；JS 尺寸缓存更新、浮层定位、末行可达、命中区域正确。覆盖普通桌面与较小窗口，验证布局会主动重排，并确认从 125% 返回 100% 不丢状态或遗留错误折叠。
5. **持久化与无障碍**：首次启动、刷新、损坏偏好、主题切换、键盘操作、浏览器缩放；不因切档 reload 或清空业务状态。

先在 ZXUI docs 用现有展示页面核对，再立即用源码直连业务复核。修改 token/compiler 后需要重生成主题；修改结构样式后刷新结构镜像。业务 deployment watcher 已能感知 generated 原子替换，但这不等于主题源文件未经编译就会自动生效。

## 建议交付顺序与待选项

1. 确定 A/B/C 路线与首批仿真边界；把 scale、density、size 语义和显式尺寸兼容策略固定下来。
2. ZXUI 完成公共缩放协议、可缩放尺寸输出、EP/Tailwind 适配与核心控件；docs 与业务最小真实链路同步验证。
3. RuoYi 收敛偏好、外壳、FormDialog 策略、普通页面和共享组件；同时修复确证的主题旁路。
4. 完成 VXE、图表、编辑器、仿真 UI 等 JS/第三方消费者与范围说明，再执行跨主题验收。

这应作为一个跨库特性处理，不是单文件开关。推荐选择 A：先补组件库能力，再让业务消费；实施前需形成跨仓库的 requirements/design/tasks，以防只完成几个演示页面就宣称“全局”。当前文档是该规格的评估输入，不替代正式规格，也没有表示实施已经完成。

# ZXUI 与真实业务主题审计及搜索布局接入

日期：2026-10-12。业务：RuoYi-Vue3-FastAPI；组件库：`/Users/hqz/Downloads/element-plus`。

本次先比较源码、公开主题契约与实际页面，再修改确认的责任方。按用户要求未运行 lint/build，未新增测试用例。仿真专用页面不在本次范围。

## 结论与归属

| 范围 | 判断 | 本次处理 |
| --- | --- | --- |
| 顶部、侧栏、Logo、菜单、主内容区 | 已使用 ZXUI；现有业务没有覆盖其主题填充值 | 实际切换 9 套主题的明暗模式，顶部 `header` 和侧栏 `panel` 填充全部与当前主题变量一致，保留现有实现 |
| 框内搜索按钮 | ZXUI 缺少布局能力，业务不能仅通过原来的隐藏按钮选项实现 Steamer 的交互 | 在组件库新增位置选项和 Provider 默认配置，业务根 Provider 统一启用 |
| 图标选择弹层 | 业务引用了不存在的 `--zx-semantic-surface-sunken`；选中项使用通用 elevated 背景 | 改为公开 hover 与 selected 主题变量 |
| 普通 DAG 端口、默认连线 | 业务将青色、白色、灰色写入默认样式 | 默认端口使用 accent/field，默认连线使用 border 主题变量 |
| 设备拖入拓扑后的端口背景、文字 | 业务默认白底与固定灰字；设备详情已消费 field 变量 | 让四向端口背景、文字与设备详情采用相同公开 field 变量，未知端口边框回退到主题 border |
| CAN/LAN/RS422 等协议端口与连线色 | 业务分类色，承载协议含义 | 保留明确的 `port.color`；连线继续继承源端口协议色 |
| 设备外观与导出白底 | 物理设备外观、导出呈现策略 | 保留设备金属/nameplate 外观与 PNG/PDF 导出白底 |
| 旧保存拓扑的显式颜色 | 样式已经存在于业务保存的 graph JSON，加载时直接回显 | 本次更新默认样式，不批量改写历史 graph JSON 或自定义颜色；旧图显式样式仍可能盖过新默认值 |
| 未挂载的旧样式 | `DagMatrixView`、FloatingPanel、旧 XFlow 样式表、`.sub-navbar` 等存在残留，但当前非仿真页面无有效入口或导入 | 记录为清理项，不将其误判为当前主题运行时缺陷 |

9 套主题为 default、defense-green、army-pine、air-gray、pap-olive、rocket-moss、factory-blue、tech-blue、industrial-blue。组件库 Theme v4 的 header/panel 材质角色均已完整声明；docs 的应用壳也消费这些公开角色。本次没有发现顶部或侧栏所需的库主题变量缺失。

业务通过 `VITE_ZXUI_LOCAL` 与 `VITE_ZXIO_REPO_ROOT` 直连 ZXUI 源码；运行时结构样式实际来自 `packages/theme-chalk/src/structural.css`，主题资产来自公共 deployment/Host 链路。没有在业务里补写核心 `--el-*`/`--zx-*` 值，也没有手改 generated 或 npm 产物。

## 搜索公开接口

```ts
// ZxSearch：省略时继承 Provider
buttonPlacement?: 'outside' | 'inside'

// ZxConfigProvider
zxSearch?: {
  buttonPlacement?: 'outside' | 'inside'
}
```

解析顺序：显式组件 Prop → 最近的 Provider → `outside`。嵌套 Provider 未声明此配置时继承父级，配置变更能响应式更新布局。`show-search-button` 和 `search-mode` 继续决定是否出现点击按钮。

业务在 [App.tsx](/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/App.tsx) 一次性设置：

```tsx
<ZxConfigProvider
  theme={zxThemeConfig.value}
  zxSearch={{ buttonPlacement: 'inside' }}
>
  <RouterView />
</ZxConfigProvider>
```

框内按钮位于输入框 suffix，输入框保留完整边框和圆角；按钮消费主题文字、hover、focus 变量。加载时显示旋转图标并禁用操作，禁用态保留原生按钮语义。可通过 Tab 聚焦，Enter/Space 激活；按钮 Enter 不再冒泡到输入框的 Enter 监听器，避免重复搜索。输入框 Enter、清空事件与 click/input 模式保持原有约定。

组件库中英文 Search/ConfigProvider 文档及 `docs/examples/search/placement.vue` 已补充配置、继承、覆盖、尺寸和状态示例。参考了 Steamer 的 suffix 搜索结构，没有引入 Steamer 自有颜色或复制其业务组件。

## 实际验证

| 验证 | 观察结果 | 证据 |
| --- | --- | --- |
| 真实角色页搜索 | 图标位于 260px 输入框边框内；点击“普通”、Enter“超级”、清空分别请求正确 roleName，均 HTTP 200 | [最终页面](evidence/2026-10-12-zxui-business-theme-parity/tech-blue-dark-role-search.png)、[搜索细节](evidence/2026-10-12-zxui-business-theme-parity/tech-blue-dark-search-detail.png) |
| 9 主题 × 明暗 | 18/18 组合顶部、侧栏 computed background 与当前角色 fill 相同；框内搜索位置不变 | [逐项颜色记录](evidence/2026-10-12-zxui-business-theme-parity/theme-matrix.json) |
| Provider 与键盘 | 未配置仍为框外按钮；嵌套空配置继承 inside；显式 outside 覆盖；动态配置切换成功；按钮 Enter、Space、输入框 Enter 各产生一次 trimmed 搜索 | [运行时示例](evidence/2026-10-12-zxui-business-theme-parity/search-provider-states.png) |
| 三种尺寸与状态 | 小/默认/大框内按钮高度分别 22/30/38px；加载图标旋转、aria-busy 为 true，加载与禁用按钮均原生 disabled | 同上 |
| 新增角色与主题弹层 | 菜单树正常显示，展开顶级后 24 个节点可见，未显示“加载中，请稍候”；弹层使用 industrial-blue dark 作用域 | [角色弹层](evidence/2026-10-12-zxui-business-theme-parity/industrial-blue-dark-role-drawer.png) |
| 折叠与刷新 | 侧栏可折叠；重新展开后刷新保留 tech-blue dark，搜索仍采用 inside | [折叠页面](evidence/2026-10-12-zxui-business-theme-parity/industrial-blue-dark-collapsed.png) |
| 非仿真 CSS 变量引用 | 扫描业务源码的 68 个不同 `--zx-semantic-*` 引用，在实际主题作用域中全部可解析 | [变量核对](evidence/2026-10-12-zxui-business-theme-parity/semantic-reference-audit.json) |
| 拓扑 SVG 默认值 | 在真实工程拓扑的 X6 渲染器中放入临时普通节点/边，field、accent、border 的 SVG fill/stroke 随明暗切换解析到不同主题值 | [SVG 颜色记录](evidence/2026-10-12-zxui-business-theme-parity/topology-svg-theme.json) |

拓扑工程当前没有保存节点，SVG 检查采用未保存的临时画布探针，已移除；这验证的是共享渲染器和新默认值，不是旧 graph JSON 的迁移效果。未保存角色或拓扑，未修改业务记录。文档示例通过现有 Vite 源码链路临时挂载验证，结束后已清理。页面验证未观察到 pageerror。

## 修改入口与边界

- 组件库：`packages/components/search/src/{props.ts,search.vue}`；`packages/components/config-provider/src/{types.ts,props.ts,merge.ts,use-global-config.ts}`；结构 CSS 及中英文文档/示例。
- 业务：`src/App.tsx`；`src/views/tool/build/IconsDialog.vue`；`src/components/business/Dag/{config/portConfig.js,components/DagDnd.vue,shapes/registerDagShapes.js,index.vue}`。
- 两仓库 `git diff --check` 通过。按用户要求不提供 lint/build/测试通过的结论；本次交付与验证为本地源码直连链路。
- 本次审计覆盖源码使用与代表性真实页面，不宣称已逐页人工验收所有业务页面；保留的协议色、物理外观、旧保存样式应按其业务含义另行管理。

## 追加：框内搜索图标比例与位置

用户反馈用户管理页的搜索图标偏小、位置不协调。实际量取为 16px 图标、18px 右边距；垂直中心偏差为 0。原因是输入框右 padding 与按钮自身 padding 叠加，且 suffix 原始顺序把清空图标放在搜索动作之后。

调整集中在 ZXUI Search 与结构 CSS：框内图标小/默认/大尺寸为 16/18/20px；输入框减少末端 padding，动作区域宽度消费实际控件高度及 display factor；按钮位于 suffix 末端，清空图标排在其前面。框外按钮保持原有尺寸和结构，业务继续使用原来的 Provider 配置。

真实用户管理页调整后为 18px 图标、9px 右边距、34×28px 操作区域，垂直中心偏差仍为 0。输入内容显示清空按钮前后，搜索图标中心保持不变。文档示例的小/默认/大图标分别为 16/18/20px，右边距分别为 6/9/12px，全部垂直居中；加载与禁用状态正常。实际清空触发 `/api/system/user/list?userName=&page=1&pageSize=10`，HTTP 200。

证据：[调整后搜索框](evidence/2026-10-12-zxui-business-theme-parity/search-icon-adjusted.png)、[尺寸与位置记录](evidence/2026-10-12-zxui-business-theme-parity/search-icon-geometry.json)。本轮未新增测试、未运行 lint/build；组件库 `git diff --check` 通过。

## 追加：小尺寸搜索图标圆弧

用户反馈圆弧有锯齿。实际页面的 18px SVG 位于整数 CSS 像素坐标，没有额外缩放或小数像素偏移。原 Element Plus 图标将 1024 网格的填充轮廓缩小到 18px，环形线条厚度约为 1.125px，在低像素密度与截图放大时显得较碎。

ZXUI 框内搜索改用内部 `search-icon.vue`：18 网格、1.5px 圆角描边，圆和手柄显式 `fill="none"`，避免通用图标样式的 fill 继承。继续通过 ZxIcon 渲染并继承 currentColor；未修改全局图标、加载图标、公开配置或业务配色。

实际用户管理页在 1× 与 2× 像素密度下均为 18px 图标，垂直中心偏差为 0，右边距仍为 9px；点击搜索返回 HTTP 200，加载结束后正常恢复搜索图标，未观察到 pageerror。像素截图放大仍会显示像素边缘，此次改善的是正常尺寸下的线条均匀性。

证据：[原图标 1×](evidence/2026-10-12-zxui-business-theme-parity/search-glyph-before-1x.png)、[新图标 1×](evidence/2026-10-12-zxui-business-theme-parity/search-glyph-after-1x.png)、[新图标 2×](evidence/2026-10-12-zxui-business-theme-parity/search-glyph-after-2x.png)、[渲染记录](evidence/2026-10-12-zxui-business-theme-parity/search-glyph-rendering.json)。本轮未新增测试、未运行 lint/build。

## 追加：登录页首次进入误触发必填校验

实际页面复现：首次进入时，验证码接口返回 `captchaEnabled: false`，业务 `loginRules` 从含验证码规则变为仅含账号和密码规则。ElForm 默认开启 `validateOnRuleChange`，因此规则更新触发全表单校验，将尚未填写的账号、密码标为必填错误。随后填写内容已经进入表单模型，但原规则仅监听 blur，输入时旧错误仍可能停留。ZXUI ZxInput 的 modelValue 与事件转发正常；归属为业务校验时机。

仅修改 `src/views/login.vue`：表单设置 `validate-on-rule-change="false"`；账号、密码规则同时监听 blur/change，填写后及时更新校验结果。保留登录提交时的完整校验与验证码条件规则。

实际验证：首次进入错误数为 0；空值提交出现两个必填错误；填好账号后仅剩密码错误，填好密码后错误数为 0。读取记住的账号时不标红，缺少密码提交只提示密码。密码显隐保留输入值，密码框回车只发送一次登录请求，HTTP 200 并进入 `/system/user`，未观察到 pageerror。登录卡片完整位于 1440×1000 视口内。

证据：[填写后的登录页](evidence/2026-10-12-zxui-business-theme-parity/login-validation-filled.png)、[校验与登录记录](evidence/2026-10-12-zxui-business-theme-parity/login-validation.json)。本轮未新增测试、未运行 lint/build。

## 追加：表单弹框全屏选项与关闭图标对齐

用户反馈“添加用户”弹框不需要全屏图标，且关闭 X 与标题不齐。实际量取：关闭按钮容器中心与标题中心相同，但其内部 SVG 采用原生按钮的行内排版，中心偏上 2px；全屏图标来自 ZXUI 的 `showFullScreen: true` 默认值。

业务在 `components/ui/FormDialog/index.ts` 的统一入口将 `showFullScreen` 默认设为 false，覆盖调用点仍可显式开启。ZXUI 在结构样式源中让原生关闭按钮与标题容器共同参与 flex 对齐，关闭按钮内部也使用 flex 居中，替代固定 top 偏移；复用主题 hover/focus 变量，小屏幕保留 44×44px 点击区域。自定义 headerPadding 的选择器同步覆盖带关闭按钮的标题栏。

真实添加用户弹框的桌面与 390px 小屏幕全屏图标数量均为 0，关闭 SVG 与标题垂直中心偏差均为 0；桌面和移动端弹框完整处于视口内。点击关闭、空格键关闭、Esc 关闭均有效；双击标题栏没有进入全屏。

在真实弹框 DOM 上做了可逆的 CSS 布局探针：两行标题、自定义 `24px 32px` header padding、含副标题的标题块，其关闭 SVG 与标题块中心偏差均为 0，标题栏没有横向溢出。探针已恢复，未提交用户记录。先前独立验证上下文因同一账号再次登录产生的 token 失效诊断单独记录；最终独立验证页面未观察到 pageerror。

证据：[最终弹框](evidence/2026-10-12-zxui-business-theme-parity/user-dialog-header-adjusted.png)、[标题栏细节](evidence/2026-10-12-zxui-business-theme-parity/user-dialog-header-detail.png)、[小屏幕弹框](evidence/2026-10-12-zxui-business-theme-parity/user-dialog-header-mobile.png)、[对齐与交互记录](evidence/2026-10-12-zxui-business-theme-parity/dialog-header-alignment.json)。本轮未新增测试、未运行 lint/build；未手改结构样式的 generated mirror。

## 追加：Dialog 分隔线统一配置

此前 ZXUI 的 header/footer 在结构样式中固定绘制主题边线，缺少可继承的开关。现在将开关与外观分开：`divider` 控制是否显示，CSS 变量控制已开启线条的外观。配置优先级为组件显式值（包括 `useDialog` 绑定值）→ 最近的 `ZxConfigProvider.zxDialog.divider` → `false`。显式 false 可以覆盖全局 true；省略或 undefined 恢复继承。嵌套 Provider 深度合并原有 `zxDialog` 配置。

公开 CSS 变量为 `--zx-dialog-divider`（共用 border 简写）、`--zx-dialog-header-divider`（标题栏覆盖）、`--zx-dialog-footer-divider`（底部覆盖），依次回退到共用值与当前主题的 `--zx-semantic-surface-header-edge`。可以配置粗细、类型、颜色，或使用 none 单独隐藏一条线；仅设置样式变量不会开启 divider。变量可通过组件 `dialogStyle`、Hook `dialogStyle` 或应用样式传入。沿用现有组件/Provider/Hook 链路，没有新增业务内部开关或独立状态源。

业务在 `src/App.tsx` 的统一 Provider 显式设置 `zxDialog={{ divider: false }}`，保持用户要求的默认不显示。单个业务弹框需要时可设置 `useFormDialog({ divider: true, ... })`，该 Hook 沿用 ZXUI 的 `useDialog` 配置类型与绑定机制。ZXUI 中英文 Dialog/ConfigProvider 文档及 `docs/examples/dialog/divider.vue` 已补齐全局继承、单独开关和 CSS 定制示例；示例的 Vue SFC 解析与脚本/模板编译成功。

真实业务源码链路共检查 18 个运行时配置场景：默认关闭、CSS 不隐式开启、Provider 响应式开关、Hook ref 显式 true/false 与 undefined、`updateOptions` 覆盖与恢复继承、共用 CSS border、头尾独立覆盖、footer=false、自定义 footer、嵌套 Provider 继承及动态更新，以及 default/rocket-moss 的深色主题。共用 CSS 变量实际输出 2px dashed，两区域覆盖输出标题栏 3px solid、底部 0px。默认主题边线随明暗切换变化；传送后的弹框仍在对应主题 overlay host 内，标题与关闭按钮中心偏差为 0。弹框打开时配置切换没有清空输入内容。

最终真实“添加用户”弹框头尾边线均为 0px、全屏按钮数量为 0、关闭 SVG 与标题垂直中心偏差为 0。验证过程使用未保存的临时公开组件探针，已移除，未提交用户记录。前一验证会话在重新调用业务 API 时出现一次“用户token不合法”，单独保留为会话诊断；重新登录后的最终业务检查未观察到 pageerror。

证据：[默认业务弹框](evidence/2026-10-12-zxui-business-theme-parity/user-dialog-no-divider.png)、[启用分隔线](evidence/2026-10-12-zxui-business-theme-parity/dialog-divider-provider-enabled.png)、[CSS 共用样式](evidence/2026-10-12-zxui-business-theme-parity/dialog-divider-css-common.png)、[头尾独立覆盖](evidence/2026-10-12-zxui-business-theme-parity/dialog-divider-css-overrides.png)、[墨青启用](evidence/2026-10-12-zxui-business-theme-parity/dialog-divider-moss-enabled.png)、[墨青关闭](evidence/2026-10-12-zxui-business-theme-parity/dialog-divider-moss-disabled.png)、[配置记录](evidence/2026-10-12-zxui-business-theme-parity/dialog-divider-configuration.json)。本轮未新增测试、未运行 lint/build；未手改结构样式的 generated mirror。

## 追加：Dialog 默认留白、分隔线与操作层级

用户开启业务分隔线后反馈线条不明显，并要求评估标题、关闭按钮、正文及底部操作的留白。对照了 [Atlassian Modal](https://atlassian.design/components/modal-dialog/usage)、[Microsoft Fluent 2 Dialog](https://fluent2.microsoft.design/components/web/react/core/dialog/usage)、[Ant Design Modal 的官方实现](https://github.com/ant-design/ant-design/blob/master/components/modal/style/index.ts) 与 [IBM Carbon Modal 规范](https://www.carbondesignsystem.com/building-blocks/core/components/modal/specifications)。它们的具体密度和 footer 形式各有差异；共同依据是单一任务、清晰的主次操作、系统化留白与可操作的关闭区域。本次数值为 ZXUI 桌面表单场景的设计选择，不将其描述为所有设计系统共用的唯一标准。

实际测量表明标题内层与 title 的 padding 已为 0；单行 header 为 61px（含 1px 分隔线），标题原为 18px/24px、字重 400，关闭按钮为 36×36px。墨青 dark 原边线为品牌绿 28% 不透明度，和弹框底色非常接近。Footer 原 padding 为 12px 20px，按钮为 60×30px；正文最后一行还保留了统一表单校验提示的布局空间。

调整集中在 ZXUI 结构样式源：分隔线默认改用当前 blocking 文字色派生的 18% 不透明度、1px 细线，继续支持三个已有 CSS border 覆盖变量；标题使用公开字体角色与字重角色，默认 18px/28px、字重 500。标题与正文左侧以及正文与 footer 右侧留白统一为 24px，正文 padding 为 24px 24px 16px，footer 为 16px 24px；标题外层上下 12px 保留，内层不叠加 padding。默认 footer 动作最小宽 80px，高度消费主题大尺寸控件轴，按钮间隔仍为 8px。移动端左右留白 16px、footer 上下 12px，默认动作及关闭按钮至少 44px；短屏保持一个正文滚动区域。保留表单错误提示预留空间，避免校验时产生布局跳动。

已有 `--zx-dialog-header-padding`、`--zx-dialog-body-padding`、`--zx-dialog-footer-padding` 现在可直接覆盖默认布局，props 与 Hook 继续复用相同入口。自定义 footer 的按钮尺寸由调用方维护。几何尺寸消费 display factor，按钮高度继续消费 density；组件库 divider 默认仍为 false，业务入口已按用户预览要求设为 true。中英文 Dialog 文档已记录默认视觉节奏及变量回退规则。

交互检查额外确认 ZxButton 的自动加载会短暂禁用按钮并使其失焦，导致异步打开弹框后不能归还入口焦点。在 Button 内记录原本聚焦的点击按钮，加载结束、按钮仍存在且可用、焦点停留在 body 时，等待 DOM 更新后恢复焦点；已有弹框或调用方主动转移到输入框的焦点保持其所有权，不额外点击按钮。

验证结果：9 主题 × 明暗共 18 个组合，分隔线均跟随当前主题，标题与关闭 SVG 中心偏差均为 0，弹框全部处于视口内。墨青默认按钮为 80×38px，紧凑/默认/宽松高度为 34/38/42px；默认浅色主题为 80×40px。390×844 小屏按钮为 158×44px，390×600 短屏的正文可滚动，header/footer 均可见。公开 CSS 覆盖输出 header 24px 32px、body 10px 18px、footer 20px 32px，头部分隔线 2px dashed、底部 none。空格关闭与 Esc 关闭有效；修复后通过 Enter 从“新增用户”打开、Esc 关闭，焦点回到“新增用户”。临时 Button 验证还确认普通操作结束后保持按钮焦点、主动聚焦输入框时不抢焦点、两次操作仅触发两次 click。

验证期间前一会话出现一次 token 失效。新的隔离会话还观察到登录后业务 Router 仅有 8 个静态路由，而 permission 状态已加载 4 个业务根路由，导致 `/system/user` 匹配 404。为继续当前组件验证，仅在该浏览器会话使用 Router 公开 API 注册已加载的业务路由，没有修改路由源码；临时注册与组件探针均已移除，浏览器已关闭。此路由诊断不是本轮样式修复结果，需在其所属业务改动中处理；后续组件验证未观察到 pageerror。未保存用户记录。

证据：[调整前](evidence/2026-10-12-zxui-business-theme-parity/dialog-ux-before.png)、[墨青调整后](evidence/2026-10-12-zxui-business-theme-parity/dialog-ux-moss-after.png)、[浅色调整后](evidence/2026-10-12-zxui-business-theme-parity/dialog-ux-light-after.png)、[移动端](evidence/2026-10-12-zxui-business-theme-parity/dialog-ux-mobile-after.png)、[几何、主题与交互记录](evidence/2026-10-12-zxui-business-theme-parity/dialog-ux-defaults.json)。本轮未新增测试、未运行 lint/build，两仓库 diff 检查通过；未手改 generated mirror。

## 追加：隐藏全屏按钮时保留标题栏双击

用户指出隐藏图标后双击全屏也失效。根因在 ZXUI：`showFullScreen` 同时控制按钮渲染、共享全屏 action 的 enabled 状态和标题栏双击处理。此前业务设为 false 时，一并禁用了双击和公开的 `toggleFullscreen` 调用。

现在 `showFullScreen` 仅控制按钮渲染；弹框可见时全屏 action 可执行，非交互标题区域的双击继续使用该 action。快捷键仍由 `fullscreenShortcut` 单独开启，受控 `fullscreen` 的事件契约保留。业务共享 FormDialog 继续默认隐藏图标，无需调用点补丁，也没有新增配置开关。中英文文档同步明确这些职责。

本轮未使用 computer use、未新增测试、未运行 lint/build。运行现有 Dialog 拖拽/双击、受控全屏及 Dialog/Drawer 快捷键相关检查：3 个文件、5 项通过，其余 37 项按名称筛选跳过；两仓库 `git diff --check` 通过。已检查隐藏图标配置与双击处理不再关联，本轮未重新进行真实业务页面交互验证。

## 追加：Footer 与全局密度统一

用户反馈默认 footer 偏厚，并询问是否与紧凑/疏松模式冲突。此前按钮高度仍随 density 改变，但结构样式额外设置了 `min-height: var(--el-component-size-large)`，将普通按钮提升到大尺寸，并使 ConfigProvider 的 small/default 配置无法完整生效；footer 的上下 16px 留白只跟随 display scale，不随 density 变化。属于 ZXUI 默认结构样式的视觉节奏不一致。

现在桌面默认操作按钮不再覆盖高度，保留原生按钮的 size 解析和主题 density 投影；最小宽度 80px、按钮间距 8px 和右侧对齐保留。Footer 上下留白从公开 display spacing token 派生：`max(8px × display factor, 2 × display control-y − 4px × display factor)`；底部同时避让 safe area。移动端保留至少 44px 点击高度和 12px × display factor 的上下留白。既有 `footerPadding` / `--zx-dialog-footer-padding` 显式配置继续覆盖默认值。业务没有新增密度或尺寸补丁，中英文文档已同步。

在 office 100% 和默认按钮 size 下，按现有主题 token 与样式公式计算（非浏览器实测）：

| 主题 | 密度 | 按钮高度 | Footer 上下留白 | 含 1px divider 的 footer 高度 |
| --- | --- | --- | --- | --- |
| 默认 | compact / default / comfortable | 28 / 32 / 36px | 8 / 12 / 16px | 45 / 57 / 69px |
| 墨青 | compact / default / comfortable | 26 / 30 / 34px | 8 / 10 / 14px | 43 / 51 / 63px |

验证：结构 CSS 经 PostCSS 解析成功，桌面 action 高度覆盖已移除，移动端 44px 下限保留；读取 9 个主题 × 明暗 × 3 个密度共 54 份适配资产，确认按钮投影和留白来源。重启本地前端后，Vite 通过源码直连返回更新后的结构 CSS（HTTP 200）。本轮未使用 computer use、未新增测试、未运行 lint/build，未手改 generated mirror；未进行新的真实页面视觉测量。

## 追加：标题栏 gap 评估与空操作区清理

用户询问标题区域是否应去掉 gap。当前 header 的 flex 方向为横向：外层 gap 分隔标题内容与原生关闭按钮，内层 gap 分隔返回按钮、标题块和右侧操作，title-main 的 gap 分隔标题、标签及附加内容。Gap 不构成标题上下留白；上下空间来自外层 padding、60px 最小高度和内部 36px 对齐区域。直接删除 gap 不能收紧上下空间，会使实际相邻控件缺少隔离。

发现并清理一处冗余：`showFullScreen=false` 且没有 `headerRight` 插槽时，原先仍渲染空的 header-right div，产生额外的 8px 横向 gap。现在仅在全屏按钮或右侧插槽存在时渲染此容器，保留有内容时的必要间距。标题栏上下留白继续为标题/关闭按钮居中和标题栏手势提供空间。

验证：Vue SFC 的 script/template 编译通过；本地 Vite 返回的更新模块包含 `showFullScreen || $slots.headerRight` 条件（HTTP 200）。两仓库 diff 检查通过。本轮未使用 computer use、未新增测试、未运行 lint/build，未重新量取真实页面。

## 追加：默认关闭图标的尺寸与视觉分量

用户要求评估关闭 X 的大小、粗细与标题协调性。原生 Element Plus 默认是 16px SVG 画布，1024 viewBox 中的填充图形实际约占画布六成，因此截图中的可见 X 约为 10px，斜线法向厚度约 1px；font-weight 不会改变此 SVG 填充路径。与 ZXUI 当前 18px 标题相比，主要问题是视觉分量稍弱，而非 bold 过重。

参考 [Carbon Modal 的官方规格](https://www.carbondesignsystem.com/building-blocks/core/components/modal/specifications)（16px 图标、48px 点击按钮）及 [Fluent 图标指南](https://fluent2.microsoft.design/iconography/)（常规图标用于识别操作，尺寸根据交互工具和平台选择）。这些系统没有统一的最优粗细；ZXUI 选择保留 16px 基础画布，将图形适当展开，使用 1.5px 圆头交叉线，加强小尺寸识别同时保持标题为主的层级。

库内部新增 `dialog-close-icon.vue` 作为默认 native closeIcon，不增加公开配置开关；调用方的 `closeIcon` / `close-icon` 透传覆盖仍优先。按钮图标尺寸改为消费公开 `--zx-display-icon-default` 角色，适配 display profile/scale；桌面 36px 与移动端至少 44px 点击区域保留。悬停和 focus-visible 使用 blocking 主文字色，正常状态使用次文字色；既有背景反馈、焦点边框和原生 aria-label/关闭保护继续使用现有实现。业务没有覆盖关闭图标，也未修改其他组件图标。后续整体评估已将该默认 SVG 移至 `_shared/close-icon.vue`，供 Dialog 和 MessageBox 共用，详见 [2026-10-13 系统提示弹框评估](2026-10-13-system-messagebox-review.md)。

验证：Dialog core 与默认 close icon 的 Vue SFC 脚本/模板编译成功，结构 CSS 解析成功，default/rocket-moss 的 icon display 角色存在。本地 Vite 返回三个更新的源码模块（HTTP 200）。运行现有 native close guard 与可访问名称检查，共 4 项通过，其余 34 项按名称筛选跳过。本轮未新增测试、未运行 lint/build、未使用 computer use，未重新量取真实业务页面；未手改 generated mirror。

## 追加：系统 MessageBox 分隔线控制

截图中的“系统提示”来自 `plugins/modal.js` 的原生 `ElMessageBox.confirm`，属于程序化 MessageBox，未读取 ZXUI 的 Provider feedback 配置。主题外观来自现有根主题资产，但缺少 Dialog 已具备的可选头尾分隔线。

ZXUI 在 `ThemeMessageBoxOptions` 中增加 `divider?: boolean`，由 `ZxConfigProvider.modal` 与 `useZxFeedback().modal` 共同消费：单次调用已定义的配置 → 当前最近 Provider 的 modal 默认值 → false。`createZxFeedback` 支持普通配置、ref 和 getter；Hook 读取配置 ref，每次调用时解析当前默认值，不再固定 setup 时的快照。打开后的主题继续由所属 scope 更新，divider 等 MessageBox 默认选项在打开时捕获。

原生 UI feedback 提供 alert/confirm/prompt 三种 MessageBox，共用一处 owner-bound portal/终结清理逻辑，并使用各自原生构造器，保留输入框校验与返回值。新增 `ThemeMessageBoxFeedback` 扩展原有 `ThemeFeedback`，保留已有三通道自定义 adapter 的基础类型；缺少新通道的自定义 adapter 经高层调用时返回明确诊断。已有 customClass 保留，开启 divider 时附加修饰类，专属选项不透传给 Element Plus。

头尾线条复用 `--zx-dialog-divider`、`--zx-dialog-header-divider`、`--zx-dialog-footer-divider` 及 blocking 文字色 18% 的默认细线。边线铺满区域宽度，正文保留呼吸空间；尺寸仍消费 MessageBox 原有密度/显示度量，未强制提升按钮大小。无底部按钮时不绘制 footer 分隔线。CSS 变量单独赋值不会开启 divider。

业务新增薄的 `ModalFeedbackProvider`，位于根 ZxConfigProvider 内，给本 app 的 `$modal` 接入所属作用域的 `useZxFeedback`，并在卸载时恢复之前的入口。App 使用同一份 `overlayDividers` 配置开启 ZxDialog 与 MessageBox。业务 Promise 适配明确将 cancel/close 转为拒绝，只有 confirm 才进入原有 `.then(changeUserStatus)` 分支；alert 类型、prompt 数据、loading 接口保留。原先直接使用 `ElMessageBox` 的其他业务调用点没有在本轮批量迁移，它们不会读取 ZXUI 的 modal 默认选项。

验证：现有 feedback 主题所有权、portal 终结清理、默认配置合并与嵌套配置检查，共 3 个文件、13 项通过；单次终端契约检查确认 cancel/close 拒绝、prompt 对象保留、显式 divider=false 透传、错误提示 type 和失败诊断保留。7 个改动 TS/TSX 文件转译成功（非完整类型检查），结构 CSS 解析成功，共用头尾分隔线规则存在；Vite 返回业务入口/Provider/适配器及库 feedback/CSS 的更新模块（HTTP 200）。两仓库 diff 检查通过。未新增测试文件、未运行 lint/build、未使用 computer use，未执行真实用户停用或重新实测页面。

## 追加：系统 MessageBox 短正文比例与高度下限

用户新截图的正文夹在两条分隔线之间，只有约一行文字加上下原生间距，视觉上近似窄带。源码确认本轮分隔线样式沿用 `--el-messagebox-padding-primary` 作为正文 padding；墨青默认密度该值为 `7px × 1.5 = 10.5px`，24px 行高的单行消息因此约 45px 高。这属于库默认结构布局，业务没有另写正文高度。

调研官方规范：[Carbon Modal specifications](https://www.carbondesignsystem.com/building-blocks/core/components/modal/specifications) 将 header 到正文的间隔设为 16px、正文到操作区的间隔设为 48px；[Fluent 2 Dialog](https://fluent2.microsoft.design/components/web/react/core/dialog/usage) 将 header/body/footer 分开，长正文滚动时保留标题与按钮；[Atlassian Modal dialog](https://atlassian.design/components/modal-dialog/usage) 要求正文简洁、聚焦一个任务，避免复杂滚动体验。没有据此声称这些规范规定了相同的正文最小高度。以下高度是根据现有 ZXUI 密度与紧凑管理端场景做出的设计选择。

ZXUI 的 MessageBox 正文增加包括 padding 在内的高度下限：`64px × display control factor + 4 × display control-y spacing`。在 office / 100% 显示请求下，default 主题紧凑/默认/舒适分别为 88/96/104px，墨青分别为 84/92/100px。上下内边距为 `max(16px × factor, 2 × display control-y spacing)`。短消息的图标与正文作为整体垂直居中；多行消息、VNode 和 prompt 内容自然增长，溢出时安全退回顶部对齐并内部滚动。最小高度受 30dvh 限制，以便矮窗口降低正文高度下限。没有固定整个确认框的高度。

正文布局与 divider 开关独立，移除仅在开启分隔线时追加正文 padding 的规则。保留原有 header/footer 和按钮尺寸，避免再次把操作区做厚。两个可选 CSS 覆盖入口为 `--zx-message-box-body-min-height` 与 `--zx-message-box-body-padding-y`，可通过主题作用域、Provider 的 `modal.customStyle` 或 feedback Hook 的单次 `customStyle` 配置；显式值保留 CSS 原始长度。中英文 ConfigProvider 文档均已补充。业务 `$modal` 已通过根 Provider 直连库源码，本轮业务不再追加样式补丁。

验证：结构 CSS 解析与正文布局契约检查通过；9 个主题 × 2 模式 × 3 密度，共 54 个已有主题变体的源变量解析与数值检查通过，密度下限依次递增。初次检查遇到公开语义变量指向内部变量，修正检查脚本的别名解析后完成上述验证，主题资产未修改。Vite 返回更新的结构 CSS 与业务根组件（HTTP 200），本地源码链路启用。两仓库 diff 检查通过。本轮没有新增测试、没有运行 lint/build、没有使用 computer use，尚未对真实页面进行视觉复测；上述尺寸为已核对的源码配置值。

## 追加：MessageBox 横向边距与统一对齐线

用户新截图显示提示图标贴近左边框。源码确认 MessageBox 根节点之前将 `--el-messagebox-padding-primary` 同时用于四边 padding；该值来自 control-y 密度，墨青 office / 100% 默认密度下为 10.5px，紧凑模式还会降低。容器的横向边距因此误用了控件的纵向密度尺度。

调研：[Carbon Modal specifications](https://www.carbondesignsystem.com/building-blocks/core/components/modal/specifications) 正文左侧为 16px，右侧有专属比例规则；[MUI DialogContent 官方源码](https://github.com/mui/material-ui/blob/master/packages/mui-material/src/DialogContent/DialogContent.js) 普通与分隔线两种布局的正文横向 padding 都是 24px。成熟产品没有共同的唯一边距值；本轮根据 ZXUI 现有 Dialog 桌面 24px / 小屏 16px 的布局选择同一组横向边距。

ZXUI MessageBox 增加 `--zx-message-box-padding-x`，在 office / 100% 显示请求下桌面默认为 24px，视口宽度不超过 768px 时为 16px，并随 display control factor 缩放。横向边距独立于 density，纵向间距与控件尺寸继续消费原有密度规则。根节点、标题、正文图标/无图标文字、prompt 输入框、底部操作共享横向对齐线。开启 divider 时，用同一有效边距计算负 margin 和回填 padding，线条保持铺满宽度，正文位置不变。

保留原生 MessageBox 40px 关闭点击区域，利用实际关闭图标字号计算横向位置，使图标框与共享边距对齐；标题另留按钮区域与 8px 显示尺度的间隔。分隔线开/关时标题保留空间相同，隐藏关闭按钮时不占额外空间。使用逻辑方向属性，移除原生固定 right 定位对方向的干扰。没有增加按钮高度或正文高度。本轮没有修改关闭图标本身。

主题作用域、Provider 的 `modal.customStyle` 和 feedback Hook 的单次 `customStyle` 均可使用新的 CSS 变量覆盖横向边距。`--el-messagebox-padding-primary` 继续控制原有头尾纵向间距与图标间隔；此前用它调整横向边距的调用应使用新的横向变量。中英文 ConfigProvider 文档已明确各自职责。业务无需增加局部样式。

验证：结构 CSS 解析与桌面/小屏/分隔线共用边距契约检查通过；对 0/8/16/24/40/64px 显式边距、两种图标字号和三种显示因子进行 36 组关闭图标位置及长标题留位的源码数值计算，结果通过。Vite 返回更新的结构 CSS（HTTP 200），业务 main 入口明确导入本地 ZXUI 结构源码。两仓库 diff 检查通过。本轮未新增测试、未运行 lint/build、未使用 computer use；未重新实测页面，数值来自源码计算。

## 执行检查点

- Files read：业务入口、主题 catalog/Host/Provider、布局/样式、共享表格/编辑器/图形、ZXUI Theme v4/编译部署/Search/ConfigProvider/docs、Steamer Search。
- Search scope：非仿真业务源码、两仓库公开主题与搜索实现；通过调用点和导入链区分有效样式与旧残留。
- Commands run：源码检索/读取、两仓库 diff 检查；实际页面交互、computed CSS 与 SVG 观察。无 lint/build/新测试。
- Files changed：见上方修改入口；保留既有工作区未提交修改。
- Progress：计划 Task 1–3 与用户追加的框内搜索配置已执行。
- Remaining risks：历史保存 graph JSON 的显式样式继续保留；发布产物未经本次构建验证。
- Next action：用户在现有 `http://localhost/system/role` 刷新即可使用；后续发布按组件库标准构建交付。

# Display Scaling 实施证据索引

日期：2026-09-27。规格是实施输入。任务 1、2 已完成；不将 theme/density 历史报告记为显示比例通过。

| 证据 | 内容与边界 |
| --- | --- |
| [consumer-inventory.md](consumer-inventory.md) | 后端 manifest / 前端路由 / 组件与包版本的源码消费者清单；每项显示比例状态待实施。 |
| [environment-matrix.md](environment-matrix.md) | 当前 Mac/Chrome 设备事实及待补目标设备，未作真机多终端声明。 |
| [用户管理默认 density 截图](evidence/task1-user-office-default.png) | 1728×992 CSS 视口，默认浅色、default density；无 Display Scaling 控件。 |
| [用户管理原偏好截图](evidence/task1-user-office-baseline.png) | 同一页面 comfortable density，切换测量后已恢复。 |
| [任务 1 测量](evidence/task1-office-100.json) | 默认与 comfortable density 下 navbar/sidebar/输入/表格/分页读数；表单运行时未取到。 |
| [VXE 5000 行 100%](evidence/task13-vxe-office-100.png)、[125%](evidence/task13-vxe-office-125.png) | 同一虚拟表、同一滚动锚点的 Chromium 截图；仅为本地样例，不等于真实业务全链验收。 |

完成基准与已知限制：业务前端 `src/main.ts` 通过旧 `size` Cookie 设置 EP small/default/large，ZXUI 安装固定 default；`SizeSelect` 仍有 reload，`src/store/modules/app.ts` 仍读取 Cookie。业务 `FormDialog/policy.ts` 的源码基准为 label 100px、column gap 20px、min column 280px；Header 50px、Sidebar 200px、AppMain 的 50/84px 是当前业务布局值。当前浏览器 default density 的 input wrapper 32px、表格行 49px、分页 32px；comfortable density 对应为 36px、53px、36px。新增用户表单因现有 token 失效无法打开，任务 12/16 的真实链验收须补；该失败发生在本功能实现前。

两仓均已有大量未提交修改：业务仓分支 `std`，ZXUI 根仓在本轮源码修改前从 `main` 创建 `codex/display-scaling`，保留既有 dirty 工作；ZXUI 的 tokens/compiler/Host 部分文件在本轮之前已修改。后续改源码前按现有文件复核，不覆盖其他工作。ZXUI 公开交付链目前由 `src/theme/zx-theme-packages.ts` 的九包登记和 Vite `zxuiSourceIntegrationPlugin` / `zxuiThemeDeploymentPlugin` 驱动；生成资产与结构镜像按 ZXUI `AGENTS.md` 只从拥有者源文件生成。已安装 `@zxio/zxui` 为 3.0.0-next.0，EP 2.13.0，VXE 4.17.15，vue-virtual-scroller 2.0.0-beta.8。

## 任务 2 证据

ZXUI `packages/tokens/src/display/index.ts` 建立公开目录、四档比例、office/distance 初始配方与文字下限、EP 整体高度计算、触控下限、固定/领域分类、旧资产兼容诊断及带哈希的 `display-contract.json` 产物，均经 `@zxio/tokens/display` 正式 exports 交付；`packages/theme-compiler/src/targets/css/display-css.ts` 在正常主题编译中输出未缩放基础值和有效别名，主题 CSS 进入原 manifest/哈希链，五轴变体数量未增加。`packages/tokens/src/extensions/` 通过原扩展链加入可校验 displayMetrics 与生成 refs。旧扩展模块不声明该字段时不新增 refs 内容，模块停用清除对应基础/有效变量。正式主题包的 generated 资产刷新、deployment 接线和 Host 有效投影在任务 3、4、5，任务 2 的源码编译契约完成不代表显示大小已在业务页面生效。

验证：定向 Vitest 5 文件 37 项通过；主题 CSS 目标 3 项和编译器确定性 7 项通过；独立临时目录完成 `@zxio/tokens` ESM/CJS/声明构建，并检查公开 `./display`、`./display-contract.json` 导出及内容哈希。原 `package-exports.test.ts` 需要源码仓库无 `dist/`，当前已有构建产物，故该测试在前置断言处停止，未删除任何既有产物。全仓 `tsc -p tsconfig.node.json --noEmit` 仍有本轮之前的 Vite/docs/Vue 类型错误；新增源文件未出现在该错误列表。

## 任务 3、4 在途证据（尚未关闭）

ZXUI Host/Provider 已接入 `display.profile/scale` 分字段继承、非法值诊断、scope hash/no-op、SSR 及 hydration 属性。Runtime 在显式请求 display 时校验主题 manifest 的 `displayContract`，旧资产默认请求保留兼容，旧资产显式切档返回 `TR_DISPLAY_ASSET_UNSUPPORTED`。Host 受控 composition 样式对每个 scope 投影核心文字/行盒、EP 控件整体高度及已启用扩展模块的尺寸引用。`theme-chalk/src/structural.css` 中部分结构字号与行高接入有效变量，镜像通过拥有者 `scripts/build.ts --update-mirror` 生成。

九个内置主题通过正式 `scripts/theme-compiler/build.ts` 重新生成，均为 162 个原五轴变体，manifest 均携带相同的 Display Contract 哈希 `sha256:49178b3aa8469e5e0b25c156e4e00d5e0ca5260e99b8f9f58e78b4013a8e94b1`；未增加比例维度。定向跨包 Vitest 10 文件 65 项通过。业务本地源码直连生产构建第一次因 `theme-compiler/dist` 的旧 Vite 插件拒绝新 manifest 失败；按 `tokens`、`theme-compiler` 正式 package build 更新其公开产物后，`VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod` 于 2026-09-27 通过。此构建只证明当前业务未显式切档的源码接入/交付链，不能替代真实切档或页面验收。

尚未完成：有效像素测量与布局事务、交互策略、Tailwind/EP 完整尺寸 inventory、核心控件/浮层及业务偏好与页面消费、真机校准。wangEditor 按用户当前要求暂不处理。

后续发现 Tailwind 适配器把字号/行高错误地落在 `font` 命名空间；已在库中调整为 Tailwind v4 的 `text`/`leading`、v3 preset 的 `fontSize`/`lineHeight`，保留字体家族原入口，并使三个 UI 长度目标引用有效 display 变量与旧变量回退。适配映射升到 1.5.0；写入器增加只在旧 manifest 的差异限于 Tailwind 契约且所有旧文件哈希仍匹配时允许生成资产迁移，篡改原文件会拒绝。九主题与 Tailwind 资产由正式脚本重新生成，变体数仍为 162。第二次业务构建曾因构建期从 `@zxio/tokens/display` 源码加载扩展哈希工具时 Node 无法解析无扩展名 TS 相对导入而失败；Display Contract 运行时模块改为自包含，构建脚本核验静态内容哈希后，业务本地源码直连生产构建重新通过。最终受影响 Vitest 11 文件 74 项通过，改动源文件无新增 `tsc` 诊断，`git diff --check` 通过。仍未开放业务显示设置入口，因此不把该构建视为切档验收。

## 2026-09-28：任务 5 首个库侧切片（未完成）

ZXUI Host 新增公开 `useDisplayMetrics()` 与 `displayMetrics` 服务：核心/扩展 UI 长度引用来自正式目录和编译 bundle，扩展模块停用时拒绝读取；浏览器 scope 内使用隐藏块级探针读取计算后的 CSS px，并用独立 `layoutRevision` 标记实际几何变化。根字体探针、scope/文档尺寸观察和字体加载事件触发合帧复测；Host 销毁释放观察器、探针与订阅。SSR 只开放 CSS 引用，不给像素快照。此接口尚未实现候选度量预解析与布局参与者事务，不能据此开放业务切档或把虚拟列表称为安全。

验证：ZXUI Host/Runtime 定向 Vitest 4 文件 20 项通过，其中新增 2 项覆盖计算像素/几何版本与扩展模块启停；修改文件 ESLint 与 `git diff --check` 通过。`vue-tsc -p tsconfig.web.json --moduleResolution bundler --module esnext` 仍有既有 theme-compiler/Vite 插件类型诊断，新增 Host 文件未出现在错误列表。业务通过 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod`，只证明当前默认接入链能构建。真实浏览器像素与业务页面尚待本轮授权及验证。

## 2026-09-28：任务 5 布局事务续做（仍未完成）

ZXUI Runtime 与 Host 新增布局参与者协议：切换主题、density 或 display 前，在候选 scope 上解析正式目录的 CSS 像素；虚拟消费者可以异步准备并在 CSS 提交期间重算。Host 在提交期间保持消费区域占位并标记 busy，全部参与者成功后才发布新的 ready scope；失败按逆序回滚，取消过时切换。候选度量不冒充已提交的 `layoutRevision`。回滚失败时 scope 标记 error，消费读数拒绝继续报告 ready。此协议尚未接入真实 VXE/虚拟列表；busy 失败后的用户可见重试入口也未完成，不能认为任务 5 已关闭。

验证：布局协议 4 项定向测试覆盖异步提交、固定行偏移 fixture、失败回滚、连续切换取消及回滚失败；与 Host/Runtime 回归合计 18 项通过。改动文件 ESLint、`git diff --check` 通过。业务以 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod` 再次构建通过，仅证明现有默认业务链可编译；无真实切档验收。已核对安装的 VXE 4.17.15 公开 `getScrollData`、`getTableData`、`getRowHeight`、`recalculate(true)`、`scrollTo` 等 API，行锚点实现尚未接入，也未验证浏览器行为。

浏览器续验发现并修复库侧缺口：无扩展模块的 Host 原先不安装 composition port，显式 125% 更新虽返回 committed，像素仍停在原值。现 Host 始终安装该 port，因比例可在初始激活后请求；play 源码 Vite 配置补齐 `@zxio/tokens/display` 别名。真实 Chromium 中 ZXUI dogfood scope 在保留原主题五轴的条件下从 office/100 切到 office/125，`text.body` 候选/提交均为 17.5px（原 14px），`spacing.control-y` 候选/提交均为 12.5px（原 10px）；浏览器业务登录页默认 scope 正常存在，未开放切档控件。Host/Runtime/SSR 定向回归 6 文件 29 项通过；新增无扩展 Host 防回归测试。业务源码直连生产构建再次通过；ESLint 与 `git diff --check` 通过。ZXUI web 类型检查仅余原有 theme-compiler/Vite 插件 13 条诊断，改动文件无新增诊断。真实长表、连续点击状态、失败可见重试仍待验收。

## 2026-09-28：任务 13 VXE 适配切片（未完成）

业务 `src/plugins/vxe-layout.ts` 在 VXE 4.17.15 的公开 `created` 拦截点为同一 Vue app 的每张表注册 ZXUI 布局参与者，观察控件纵向间距及 VXE 所用的 body/small/extra-small 字体度量；ZXUI 管通用事务，业务仅管 VXE 版本适配，不向组件库引入 VXE 依赖。`src/assets/styles/vxe-theme.css` 使用 ZXUI 已公开的有效字体、间距和 `--zx-display-control-factor` 映射 VXE UI 变量；不改业务数据和领域导出。参与者在 CSS 提交后调用 VXE 公开 `recalculate(true)`，按稳定 rowid、公开逐行 `getRowHeight()` 与行内像素偏移恢复阅读位置。曾尝试按新 CSS 默认行高推算，截图发现首个可见行漂移两行；VXE 对已渲染过的自动行保留不同高度，故改为逐行公开读数。

Chromium 本地 5000 行虚拟表在 office/100 的 `scrollTop=100000`、首个可见 rowid 2084、行内偏移 16px；切到 office/125 后 `scrollTop=124876`、仍为 rowid 2084/16px，行高 48→60px；切回完全恢复。同一 100% 表在 default→compact→comfortable density 下行高为 48→44→52px，首个可见行始终为 2084。手动把 rowid 2084 设为 70px 后再切档，70px 与锚点均保留；切档后滚动到底，`isBottom=true` 且 rowid 5000 可达。延迟重算期间区域有 `aria-busy`、`inert` 和可见性遮罩；注入一次重算失败后，比例与滚动回滚、busy 清除、区域可见。上述检查没有页面错误，成功切档的截图见索引。

边界：失败时声明式样例选择器仍显示请求值 125%，而 Host 已回滚为 100%；Provider 抛出 `TR_COMPOSITION_INVALID`，尚无统一的可见错误/重试入口。VXE 自动行高虚拟表还有库版本缓存限制：未在新比例下重新渲染的行可保留旧行高，例如滚至末行后 rowid 5000 初次仍为 48px，再 `recalculate(true)` 才变为 60px。当前非仿真业务 VXE 协议模板使用 `show-overflow` 固定行策略，但不能据此宣称任意可变高度虚拟表已支持。任务 5 的失败 UX、任务 10 的提交后偏好同步及任务 13 的真实编辑/选择链和其他消费者仍未完成。

验证：业务前端改动文件 ESLint 无错误（`vxe-table.ts` 保留既有 4 条 warning），`git diff --check` 通过；本地 ZXUI 源码直连 `yarn build:prod` 通过。默认 `yarn type-check` 尚未通过：业务 `node_modules` 中已安装的 ZXUI 包版本没有新公开的 `useDisplayLayoutParticipant`/`ZxDisplayLayoutParticipant` 声明，继发两个隐式 any 诊断；没有在业务补写库类型。需由 ZXUI 正式声明交付与业务依赖更新/本地类型接入闭合该门禁。

## 下一步执行顺序（2026-09-28）

1. 先收口 ZXUI 任务 3、4：核对显式 display 的公开类型/交互策略及模块启停边界，完成 EP 2.13.0 尺寸 inventory 与 Tailwind 实际工具类、嵌套 scope 回退检查。未覆盖的项目继续保持任务未完成。
2. 完成任务 5：在已接入的布局协议和 VXE 样例上补可见失败/重试及请求值回滚，验证取消、busy、逆序回滚及成功后才发布 ready；明确可变高度虚拟表的 VXE 版本边界，不先在业务开放切档入口。
3. 再完成 ZXUI 核心控件/命名预设和浮层更新（任务 6、7），以 docs 代表组件核对 office/100 基准与两场景四档。保留显式原始长度语义。
4. 然后接业务统一显示偏好和旧 size 迁移（任务 10），贯通用户管理操作链与 Header/Sidebar/Tags/FormDialog（任务 11、12）；通过 `VITE_ZXUI_LOCAL` 本地直连刷新验证，问题按拥有者回 ZXUI 或业务修复。切换不能 reload、丢编辑值或把 density 当比例。
5. 首条链稳定后按消费者清单扩展虚拟表、图表、监控展示、键盘/触屏与导出，最后完成公开包和目标设备验收。wangEditor 暂不处理；缺少真实设备证据时，任务 18 保持未完成。

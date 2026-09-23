# 业务主题接入评估与 dialog spec 复核

日期：2026-09-22。业务：RuoYi-Vue3-FastAPI；ZXUI 源码：`/Users/hqz/Downloads/element-plus`。

范围更新：用户明确要求“仿真不用管”。仿真模块及其专用图表、弹窗、暗色样式不纳入本轮后续排查、修改或验收；下面的待处理清单仅保留通用布局与非仿真业务页面。

## 结论

问题主要是**同一业务页面的不同区域采用了不同的配色来源**，并非 ZXUI 缺少顶部或侧边栏皮肤。当前 ZXUI 九个主题均提供完整的 `header / panel / brand` 表面能力；业务当前工作区也已经给主框架接入这些角色，但局部样式仍会覆盖主题。

本轮完成源码审计、确定问题的窄范围修正及真实页面验证。没有将其余页面迁移或现有 dialog spec 标成完成，没有修改 ZXUI 源码，也没有执行表单批量迁移。

## 已修正的业务问题

前端路径均相对于 `ruoyi-fastapi-frontend/`。本轮修改前已存在大量未提交改动，以下仅记录本轮增量。

| 位置 | 已确认问题 | 本轮修正 |
| --- | --- | --- |
| `src/main.ts` | 主题 alias/结构样式在 Element Plus CSS 前加载，违背 ZXUI 的同优先级加载契约 | 调整为 EP 样式 → ZXUI theme/aliases/style；保留 EP 暗色兼容文件，未提前执行 spec R6 |
| `src/theme/zx-theme-packages.ts`、`vite/zxui-theme-packages.ts` | docs 注册九个主题，业务仅八个，遗漏 rocket-moss | 补齐火箭军苔藓绿的菜单、源码资产注册及预览色；同步已有 registry 测试 |
| `src/components/ui/TopNav/index.vue` | 激活/悬停固定白字、白边、白色内发光 | 采用 header/selected 表面；激活项 focus/hover 保持 selected，底线开关仍有效并使用主题 accent |
| `src/layout/components/Sidebar/index.vue` | 将 panel 阴影覆盖成仅 depth，丢失 inner 材质 | 同时保留 panel-depth 与 panel-inner |
| `src/layout/components/TagsView/ScrollPane.vue` | 滚动按钮固定白底灰字灰边 | 改用 panel/hover/border/radius/elevation 语义 |
| `src/views/login.vue` | 主题切换器与固定白色表单并存；input 与 autofill 强制白底 | 左右区域和表单采用 brand/canvas/card，验证码外壳采用 field；移除普通 input 白底；既有 autofill 覆盖改读 field 填充和文字 token |

登录页仍保留原有局部 autofill 处理，只修正其错误配色来源；这不代表 ZXUI 的通用 autofill 能力已经落地。该库级工作仍属于 dialog spec 的候选修订范围。

## 真实页面证据

使用项目约定的 Docker MySQL、FastAPI `8088` 和 Vite `80`，前端保持 `VITE_ZXUI_LOCAL=true`。使用真实登录与用户管理页，未切换到 mock/demo 模式。浏览器验证已获用户明确授权。

- 用户管理页切换 **9 个主题 × light/dark，共 18 个状态**，读取 sidebar panel、Logo brand、header、TagsView panel、内容 canvas 的计算样式。全部状态都取得对应主题的非透明填充和文字颜色。
- 工厂蓝浅色下启用 TopNav，激活文字是主题深色文字，非固定白色；启用底线后，底线颜色与 `--zx-semantic-accent-base` 一致。验证后恢复 TopNav 及底线原设置。
- 工厂蓝登录页明暗验证：深色 card 背景为 `color(srgb 0.0788976 0.161143 0.279045)`，输入背景为 `color(srgb 0.07551 0.15297 0.267234)`；浅色 card 与输入背景同步变亮。浏览器自动填充的 inset 和 text-fill 同样读取 field token。
- 打开「添加用户」：宽 **440px**、高 **600px**；表单标签已经继承工厂蓝文字色。状态字段的 `.el-radio-group` 中 **radio input 数量为 0**。这次现象首先属于未渲染选项的数据链路问题，不能归为“单选控件存在但主题使其不可见”。还需定位业务字典/响应适配的具体故障。
- 本轮遇到一次过期会话，重新登录后成功打开添加用户；未提交用户数据。控制台另有 `deptList.filter is not a function`，属于数据契约线索，没有混入主题修复。

证据文件：

- [18 状态导航计算样式](zxui-theme-audit-2026-09-22/navigation-matrix.json)
- [工厂蓝导航截图](zxui-theme-audit-2026-09-22/navigation-industrial-dark.png)
- [登录页改前](zxui-theme-audit-2026-09-22/login-before.png)、[改后深色](zxui-theme-audit-2026-09-22/login-after-dark.png)、[改后浅色](zxui-theme-audit-2026-09-22/login-after-light.png)
- [登录页深色计算样式](zxui-theme-audit-2026-09-22/login-after-dark.json)
- [当前添加用户弹框](zxui-theme-audit-2026-09-22/dialog-current.png)、[弹框 DOM 记录](zxui-theme-audit-2026-09-22/dialog-dom.json)

这份矩阵证明主框架主题切换链路；不代表所有业务页面、所有交互状态或所有弹层均完成视觉验收。标签溢出按钮本轮完成源码与编译检查，未制造大量页签做交互终验。

## 仍未统一的实际消费范围

| 优先级 | 位置 | 归属与下一步 |
| --- | --- | --- |
| P1 | `src/assets/styles/tailwind.css`、`theme.module.css` | 业务仍维护固定 primary/gray 色板并反向写 `--el-*`；ZXUI scope 会遮蔽部分根变量，但业务 utility 本身仍固定。应让主题拥有颜色，避免直接全局反转所有 gray/slate 而误伤领域配色 |
| P1 | `src/views/project/index.vue` | 项目卡片、标题、图标、hover 仍有固定蓝色和浅色渐变。改用 card/selected/text 语义 |
| P1 | `src/views/project/components/NodeEditDrawer.vue` | 非仿真拓扑页实际使用此组件，内部却依赖固定暗色 fallback。仅针对该页面的表现评估，采用自身主题 scope 的表面与文字 |
| P2 | `src/components/ui/RichEditor/src/Editor.vue` | wangEditor 壳体、光标、标题和背景固定。适配编辑器 UI，保留用户正文中主动保存的颜色 |
| P2 | `src/components/ui/VxeTableValidation/validation.less` | plugins/vxe-table.ts 全局导入，错误面板和 tooltip 固定黑白红；应使用 overlay/status/border 语义 |
| P2 | `src/views/device/detail.vue`、`src/components/business/ZxFlow/` | X6 网格、端口、文字和缩略图颜色固定。这是业务自建组件；程序绘图需要解析主题颜色并随主题变化重绘，不能只把 CSS var 字符串塞入 Canvas |
| P2 | `src/views/project/entry.vue`、`src/views/register.vue`、`src/components/ui/Crontab/index.vue` | 载入页、注册页和 Cron 编辑器仍有固定白底、蓝色、深色文字 |

## ZXUI 责任边界

导航的公开契约见 ZXUI `docs/zh-CN/guide/theming.md` 的“表面角色与业务皮肤”；实现见 `packages/theme-chalk/src/structural.css`。九个主题均存在三种导航角色的七个 facet。本轮没有证据支持为导航另造业务主题或修改库的导航种子。

确认应在 ZXUI 解决、但不属于本轮导航改动的缺口：

1. `packages/components/input/src/input-core.vue` 未透传消费者 slots，仍有 `::icon`，expose 仅 `focus/blur/select`，与 input 文档的完整继承承诺不一致。
2. 通用 autofill 中和未在 ZXUI 落地。业务登录页修正不应作为库能力完成证据。
3. Element Plus adapter 的 density 输出未体现三档差异；ZXUI 核心主题自身已有 6/8/10px 差异。应研究 EP adapter 的度量桥接，不能直接删掉整个 density 轴。

## 对现有 dialog spec 的判断

目标与分层值得保留，**修订前版本不适合原样执行**。2026-09-22 已将下列结论同步至三件套，并增加迁移库存；当前文档是修订后的执行依据，实施仍未开始。位置：[requirements](../specs/zxui-form-dialog-convergence/requirements.md)、[design](../specs/zxui-form-dialog-convergence/design.md)、[tasks](../specs/zxui-form-dialog-convergence/tasks.md)。长期收益优化后为 16 项待执行任务、55 个验收项；本次 spec 修订未将主题局部修复记为任务完成。

本次 spec 已修订以下内容：

1. **纠正 R5 的证据标准。** 没有 `--el-form-*` 专用 alias 不等于无主题。EP 标签通过 `--el-text-color-regular`、星号通过 danger、radio 选中态通过 primary 继承；当前全局 alias 已有这条链。以计算样式、实际状态和对比度验收，而不是变量个数。
2. **纠正 density 的归属。** 54 组 EP density 产物的三档内容相同，但核心 ZXUI 轴并非空转。将需求改为 EP 适配是否体现度量差异，不删除核心主题能力。
3. **先定位状态数据，再修外观。** 本轮 DOM 证明没有 radio 选项；不能把该现象用主题补丁掩盖。
4. **缩小门禁适用边界。** useFormDialog 与纯布局 FormGrid 对普通业务表单有价值；“全仓单一 label-width”“禁止所有调用点宽度/百分比”应限定为表单弹框约定，避免误伤搜索栏、专用编辑器、图像预览等。尺寸档位可有主路径和明确的合理例外。
5. **消除迁移决策冲突。** requirements R10 要求最后交 Cursor 迁 `zx-input`，design 正文仍说不迁，任务 11 仍说只在 tooltip/search 时使用。应统一为已确认的用户决策，并保留先修 R11 的依赖。
6. **重新定义扫描口径。** 后续 AST 复核纠正了文本扫描：全 src 有 200 个 el-input、56 个 el-input-number，另有 1 个注释示例，合计旧前缀数 257。排除仿真目录后候选为 el-input 184 处/68 文件、el-dialog 18 处/16 文件。生成器动态 input 与 dialog 输出单列，不混作真实页面实例；生产可达性另行验证。见 [迁移库存](../specs/zxui-form-dialog-convergence/migration-inventory.md)。
7. **R6 按实际覆盖证据排期。** 不能因标签已继承而仓促删除全部兼容 CSS，也不能以“没有专用 token”为理由永远保留多套色板。先覆盖真实表单状态，再有序消除重复主题来源。

另纠正两处可执行性问题：useDialog 不接受顶层 maxHeight，普通弹框沿用默认限高，特殊场景用 dialogStyle.maxHeight；el-input 的 number/search/动态 type 与 ZxInput 不保证等价，必须先核对库契约。长期优化版进一步保留原生 ElForm/ref 和 ElFormItem，FormGrid 只布局，取消额外的 FormInstance 转发及 FormField 包装。

长期收益优化补充：公开主题接入复用已有 deployment/Host/Provider，主题登记只保留一份；最终移除业务私有 generated 路径和本地类型补丁。ZxInput 原生输入、数值步进和增强搜索职责拆清，明确下一主版本候选及外部迁移说明，不能作为 2.x 兼容补丁暗改。源码联调之后增加一次本地 tarball 的同一样板消费验证，正式 npm 发布不是前置。

推荐顺序：业务数据与样板 → 库通用能力及公开主题接入 → 范围内迁移与源头约束 → Cursor 最后迁输入 → 本地包验证 → 三类证据终验。具体并行依赖以 tasks.md 为准。

## 排除的假阳性

- 主框架 header/panel/brand 已在本轮之前接入，旧 `--top-header-bg`、`--left-menu-header-bg` 无实际消费者，不能直接作为顶部故障的证据。
- `utils/theme.ts::handleThemeStyle` 无调用；`design-tokens.css`、`assets/styles/TagsView.vue` 未导入。
- dashboard 当前只渲染空 ThemeDemo，旧样式没有对应 DOM；FloatingPanel、SimulationResultDialog 等仅找到 barrel export，优先级低于实际页面。
- 图像内容、遮罩、用户正文颜色、协议/故障/图表系列区分色不能机械认定为主题违规。

## 验证结果

- 既有 Vitest：`zx-theme-packages.test.ts`、`zx-theme-host.test.ts`、`theme-export-path.test.ts`，**3 文件、4 用例通过**；未新增测试文件。
- `vue-tsc --noEmit`：**通过，无诊断**。
- 修改的 TS/Vue 文件 ESLint：**0 错误**；5 个既有 unused-vars warning（ScrollPane 4、login 1）。
- 导航三个 SFC 的 script/template/style 编译通过；除格式整理外模板与脚本保持原样；使用的 19 个 semantic token 在 9 个编译主题中均存在。
- 登录页 SFC 编译及实际明暗显示、自动填充显示通过；登录流程复核。
- `git diff --check`：修改的受检 TS/Vue 文件通过。
- 不把上述局部检查解释为全仓测试或 dialog spec 终验完成。

# 业务与 ZXUI 主题接入审计

后续状态：本报告中的非仿真主题待办已在 [2026-09-27 收尾报告](2026-09-27-zxui-remaining-theme-convergence.md)逐项对账，以下内容保留初次审计时的结论与边界。

日期：2026-09-26。业务：RuoYi-Vue3-FastAPI；组件库：`/Users/hqz/Downloads/element-plus`。

## 结论

**九套主题都已接入，尚未统一的是部分业务 UI 的消费方式。与此同时，本次确实复现并修复了一个 ZXUI 公共缺陷。**

- 顶部、侧栏、Logo、页签和内容区分别消费 ZXUI 的 header、panel、brand、panel、canvas 表面。登记、部署和 Host/Provider 链路正常，没有哪一套主题整体未接入。
- ZXUI reset 将所有 `a` 的背景设置为页面底色。Logo 内部的满尺寸 router-link 因此遮住 brand 表面，却继承 brand 的文字色，陆军松枝绿深色下标题几乎消失。这不是业务缺少导航主题，也不能靠业务给 Logo 再叠一层固定色解决。
- 业务仍有固定灰阶、固定白底、仿真暗色 fallback，以及独立第三方 UI 的默认配色。本轮处理已确认的普通 UI 消费点；拓扑绘图、表单设计器等仍需按其实际渲染方式处理，不能宣称全业务已统一。

本次以当前源码和实际浏览器结果为准。9 月 22/23 日报告仅作为排查线索；开始前两边已有大量未提交改动，本报告只归属本轮增量。

## 主题覆盖

| 主题包 ID | 业务标签 | 导航浅色 | 导航深色 |
| --- | --- | --- | --- |
| default | 默认 | 通过 | 通过 |
| defense-green | 军工绿 | 通过 | 通过 |
| army-pine | 陆军松枝绿 | 通过 | 通过 |
| air-gray | 空军深蓝灰 | 通过 | 通过 |
| pap-olive | 武警深橄榄绿 | 通过 | 通过 |
| rocket-moss | 火箭军苔藓绿 | 通过 | 通过 |
| factory-blue | 海军蓝 | 通过 | 通过 |
| tech-blue | 科技蓝 | 通过 | 通过 |
| industrial-blue | 工厂蓝 | 通过 | 通过 |

通过口径：通过页面主题菜单与明暗按钮切换，等待 UI 稳定后读取提交的主题身份和计算样式。18 个状态中，五个外壳表面均非透明；Logo 内链均透明，不再遮盖 brand；侧栏与页签的选中项文字颜色一致。它不代表每个业务页面、全部控件状态或五个主题轴均已视觉验收。

证据：[18 状态计算样式](zxui-theme-audit-2026-09-26/navigation-matrix.json)、[工厂蓝深色](zxui-theme-audit-2026-09-26/navigation-industrial-dark.png)、[工厂蓝浅色](zxui-theme-audit-2026-09-26/navigation-industrial-light.png)、[恢复后的陆军松枝绿深色](zxui-theme-audit-2026-09-26/navigation-army-pine-dark.png)。

## ZXUI 本轮修正

源文件：`packages/theme-chalk/src/structural.css`；生成镜像：`packages/zxui/style/index.css`。

全局 `a` reset 的 `background-color` 从 `var(--zx-semantic-surface-page)` 改为 `transparent`。普通链接由所在表面负责底色，拥有自身背景的组件继续由组件选择器负责。通过 `pnpm build:theme` 生成镜像，没有手改构建产物。

实测工厂蓝深色修复前：Logo 外层品牌底色为 `color(srgb 0.16 0.42 0.96)`，内链却为 `color(srgb 0.03 0.105 0.215)`；修复后内链为 `rgba(0, 0, 0, 0)`，外层品牌色显现。其他八套主题同样受益。

这次没有改主题种子，也没有覆盖业务中的 `--el-*` 或核心 `--zx-*` 定义。

## 业务本轮修正

以下路径相对于 `ruoyi-fastapi-frontend/src/`。

| 位置 | 已确认问题 | 处理与证据 |
| --- | --- | --- |
| `layout/components/Sidebar/index.vue`、`TagsView/index.vue` | 选中项用品牌强调色当正文色，与 selected 表面文字契约不匹配 | 使用 selected 的 fill/on-text/depth/inner；品牌色保留给指示条。18 状态浏览器矩阵通过 |
| `components/business/Monitor/OperlogDetailDialog.vue` | 固定灰字、浅灰代码区、红绿浅色 utility | 改用主题文字、canvas 和状态别名。真实日志详情的工厂蓝明暗模式均验证，正文颜色随模式变化 |
| `components/business/Monitor/OperlogGrid.vue` | 中间包装层未遵守 fill 布局链，表格被挤出可见区，阻断详情验证 | 给已有容器补公开 `data-zx-fill`；浏览器确认表格和查看操作重新可见。此项归属业务布局，独立于主题 |
| `components/ui/Crontab/index.vue` | 表达式标题固定白底，结果边框固定灰色 | 使用 blocking/header 表面和语义边框；真实任务表单中的 Cron 生成器深色验证通过 |
| `views/register.vue` | 注册卡片固定白底，标题/提示固定灰字，与已接入的登录页不一致 | 使用 canvas/card；移除固定背景图，文字读取相应表面；补全视口高度以维持居中。陆军松枝绿深色浏览器验证 |
| `views/system/user/components/UserImportDialog.vue`、`authRole.vue` | 说明文字固定灰阶 | 改用语义次级文字；真实用户导入弹框的深色计算样式已验证；角色分配页为源码/构建验证 |
| `views/project/components/NodeEditDrawer.vue` | 非仿真拓扑复用的抽屉默认回退到固定仿真暗色 | 将 fallback 改为 ZXUI，保留 `--sim-*` 的优先级及仿真域专用材质；源码/构建验证，未声称端口数据交互终验 |
| `components/business/Device/MessageConfigTab.vue` | 协议模板提示固定灰字，空状态固定白底 | 使用语义文字和 card；源码/构建验证 |
| `views/project/entry.vue`、`components/VersionExportDialog.vue`、`views/monitor/druid/index.vue` | 载入卡片、版本名、监控输出使用固定 UI 色 | 使用 card、文字与 accent；源码/构建验证 |
| `components/ui/RichEditor/src/Editor.vue` | wangEditor 默认底色、工具栏、光标、标题、引用与表格样式固定 | 在该业务包装组件内映射第三方公开 CSS 变量并替换默认 UI 色；保留正文中明确保存的 inline 颜色。源码/构建验证，版本预览的浏览器终验尚未完成 |
| `components/ui/VxeTableValidation/validation.less`、`VxeValidationPanel.vue` | 校验浮层固定黑白红，提示色不随主题切换 | 使用 overlay、语义状态色与既有 EP 别名；保留原 simulation-dark 专用规则。源码/构建验证，未制造真实业务错误数据验证浮层 |
| `assets/styles/index.css`、`sidebar.css`、`views/protocol/index.vue` | 通用链接、协议链接和折叠菜单滚动条固定蓝灰色 | 使用 accent 与 scrollbar 语义 token；源码/构建验证 |

真实 Cron 截图：[工厂蓝深色生成器](zxui-theme-audit-2026-09-26/cron-industrial-dark.png)。注册截图：[陆军松枝绿深色](zxui-theme-audit-2026-09-26/register-army-pine-dark.png)。

## 尚未统一的消费范围

这些缺口会横跨多个主题出现，不能按“某个主题包没接入”理解。

| 优先级 | 范围 | 归属与证据 | 后续处理边界 |
| --- | --- | --- | --- |
| P1 | `views/device/detail.vue`、`components/business/ZxFlow/components/`、`components/business/Dag/`、非仿真拓扑页 | 业务自建图编辑器。XFlowGraph 固定 `#fafafa`；设备详情网格传 `#e6e6e6`；端口、选中态及部分文字在 X6 配置中直接写颜色；context menu/minimap/Dag 组件还含固定 UI 色 | 先区分 UI 表面与设备/协议类别色；CSS 部分消费 token，Canvas/图模型中需要实际解析颜色并在切换后重绘。不要把 CSS var 字符串直接当 Canvas 颜色，不要改写用户保存的图数据 |
| P1 | `views/tool/build/index.vue`、`RightPanel.vue` | 业务表单设计器。固定白底、紫色拖拽/选中区域、浅灰文字 | 按工具栏、画布、属性区、拖拽状态逐项适配；同时核对其生成代码，不只改预览截图 |
| P2 | `components/ui/Editor/index.vue` | 公告使用的 Quill 包装组件直接导入 Snow 默认皮肤，尚无完整主题适配；它与本轮修正的 wangEditor 是两个组件 | 只适配工具栏、选择器、tooltip 和编辑器默认表面，保留用户正文与颜色选择器中的真实颜色 |
| P2 | VXE 主表格与第三方浮层的完整覆盖 | 本轮仅修业务已有 validation 适配层，不能据此宣布 VXE 全部主题状态完成 | 补查主表格默认皮肤、编辑态和 portal 作用域；公共库未封装的第三方组件由业务适配层负责 |
| P2 | 剩余 utility 与零散固定 UI 色 | `tailwind.css` 与 `theme.module.css` 仍维护历史色板；file selector、错误页等还有散点固定 UI 色 | 依据实际消费者逐项迁移，不全局翻转 gray/slate，以免改变仿真、类别色或图片内容 |
| 待验证 | 强调色在文字型控件中的对比度 | 工厂蓝深色下 EP 文字按钮、radio 的选中文字仍使用 accent.base；这与 JSX/业务标签名称无关，潜在修正应先检查 ZXUI 公共语义契约 | 本轮未跑这些控件的完整对比度矩阵，不把视觉疑虑当成已证实的库缺陷，也不单点修改主题种子掩盖它 |

低优先级及假阳性：

- `components/ui/FloatingPanel/index.vue` 固定明暗 slate 色，但本次只找到统一 barrel 导出，没有确认活跃页面消费；不能与 ZXUI 同名 FloatingPanel 混为一谈。
- `components/business/ZxFlow/styles/index.scss` 维护独立色板，但当前入口未见直接导入；上表拓扑问题的证据来自实际组件与设备详情，而非仅靠该样式文件。
- `assets/styles/design-tokens.css`、`assets/styles/TagsView.vue` 和 dashboard 的旧样式不可仅凭存在就判断为运行时覆盖。
- 仿真目录及专用组件、图表系列/协议类别色、图片、透明遮罩、正文用户设定的颜色均未机械替换。

## 验证与边界

- 本地 `http://localhost` + 真实 FastAPI，`VITE_ZXUI_LOCAL=true`，源码根目录为用户指定路径。未切换到 demo/mock。
- ZXUI：`pnpm build:theme`、`pnpm theme-consumer:check:structural` 通过，包含确定性生成与 theme-chalk/zxui 打包结构检查。
- 业务：`yarn type-check` 通过；修改 SFC 的 ESLint 无错误，保留 9 项原有 warning（unused-vars/既有正则转义）。
- 现有主题测试：`zx-theme-packages.test.ts`、`zx-theme-host.test.ts`、`zx-theme-deployment.test.ts`，3 文件 11 用例通过；没有增加测试文件。
- 新增差异中引用的 38 个语义 token 在九套生成主题中均存在。导航 JSON 的五表面/透明内链/选中文字断言均通过。
- 普通 `yarn build:prod` 通过，但默认使用 node_modules 安装包；另显式运行 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --outDir /tmp/ruoyi-zxui-theme-audit-build`，用于验证本次库源码和业务的组合。
- 两仓 `git diff --check` 通过。构建仍有既有大 chunk/Browserslist 等提示，未混入本次主题修复。
- ZXUI docs 的当前 `localhost:2000/guide/theme-lab` 服务返回 500（`docs/public/images` 扫描 EPERM）；本轮对照了 docs 公开主题契约及实现，没有冒称完成当前 docs 与业务逐像素对照。
- 过程中开发会话过期一次，按仓库已有本地账号重新登录；未保存任务、日志、用户、工程或协议数据。结束时回到原 `/system/menu`，恢复陆军松枝绿深色。
- 库修复目前在本地源码中；未发布 npm、未替换 vendor 包、未提交 Git。普通安装包生产构建不会自动获得尚未打包的 ZXUI 修复。

## 计划阶段记录

STATUS: PLAN_DRAFTED
FILES_WRITTEN: `docs/plans/2026-09-26-zxui-business-theme-audit.md`
EVIDENCE: 已读取 Host/部署、外壳及两仓主题源码；检索实际消费路径；计划结构检查通过。
PLAN_CHANGES: 新建本次增量审计计划，保留前次记录。
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: 本轮执行与证据已记录；剩余范围按上述优先级继续。
BLOCK_REASON: none
UNBLOCK_ACTION: none

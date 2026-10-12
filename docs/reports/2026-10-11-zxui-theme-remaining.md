# 剩余主题问题：业务 / ZXUI 归属与实施记录

## 本轮结论

普通管理页面的主要缺口在业务旧样式；公共组件也存在表面角色混用和表格状态覆盖问题。没有新增第二套主题系统：业务使用 `@zxio/theme-tailwind/v4.css`，VXE 使用可选的 `@zxio/zxui/style/vxe-table.css`，图表沿用既有主题投影。

| 范围 | 归属与处理 |
| --- | --- |
| Tailwind | 业务的两个全局入口重复声明主色、状态色和灰阶；按钮配方又出现蓝/绿/黄/红固定色。移除重复声明，按钮、卡片、输入框与滚动条改为 ZXUI 语义角色；移除全局 `.el-card` 外观覆盖，由库负责材质。 |
| 公共 Tailwind 契约 | ZXUI 已有完整 `@theme inline` 映射，无需另造适配器。业务新增公开依赖并转换 6 个 Vue 消费文件的语义工具类；表单提示和代码块分别使用 blocking / canvas 配套文字。源码插件增加 Tailwind 包的公共导出解析。 |
| 业务兼容变量 | 旧的页面背景、表头、阴影等变量改读 ZXUI，并在 Host scope 处求值。删除没有消费方的 CSS Module 导出及未定义的颜色引用。 |
| VXE | 原业务桥接具有跨应用复用价值，迁入 ZXUI 可选 CSS 导出。包含密度、显示字号、表格/浮层颜色；表头改用 panel 配套文字，字体跟随主题。业务保留旧样式路径作为兼容入口，运行时插件直接导入公共入口。 |
| ZxDialog / ZxDrawer | 透明标题栏/正文依附 blocking 背景，却使用 header 或通用文字角色。库结构样式统一到 blocking 主次文字；有独立背景的 descriptions 单元格保持原有角色。 |
| ZxGridList | 条纹单元格规则排在交互状态后，可能覆盖悬停/当前行。调整为条纹、悬停、当前行的顺序及匹配优先级，同时支持 EP 的 `.hover-row`。保持已有选中填充与固定列不透明合成方案一致。 |
| ECharts | 缓存监控已经使用 `ZxChart` 和 `useZxChartThemeProjection`。实页显示饼图、仪表盘、文字、提示层均随主题切换，本轮不改图表独立仓。 |
| SVG 设备图 | 业务端口仍把背景/文字写死为白/灰/浅蓝；改用 SVG 可直接解析的 field / selected 角色变量，选中更新也使用同一角色。总线类型描边仍保留领域颜色。无需通过重建图表响应主题。 |
| 其他遗漏 | 头部搜索边框、全屏图标及旧 dashboard 的文字/分隔线/阴影收敛到语义角色。旧 dashboard 路由目前被注释，仅做源码修正，不计入页面验证。 |

## 验证链路与观察

- 本地 Vite：`VITE_ZXUI_LOCAL=true`，`VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus`。
- 使用已有主题生成资源；结构样式直连 owning source。新增公开 CSS export 后完整重启 Vite，让源码插件重新读取导出表。
- Tailwind 仅将现有包内容本地打包为 vendor 依赖，安装时使用 `--mode=skip-build`，没有编译/发布主题。
- VXE 实际版本：Table 4.17.15、PC UI 4.10.27。

| 页面 / 状态 | 本次浏览器观察 |
| --- | --- |
| 用户管理、空军深蓝灰 dark | 初始新增用户弹窗正常，记录 blocking 背景与文字基线。 |
| 用户管理、科技蓝 dark | 表头/正文随品牌变化；实际悬停行颜色为 `color(srgb 0.13 0.47 0.98 / 0.07)`，与主题 hover token 一致。用户页未启用 stripe/current-row，相关组合修正只做源码级复核，不冒充浏览器覆盖。 |
| 用户导入、科技蓝 dark | 公共 Tailwind 工具类生成生效；弹窗 blocking 背景、拖放区与提示文字没有固定白底。 |
| 新增用户、陆军松枝绿 light | 背景 `color(srgb 0.963769 0.969662 0.960859)`，标题 `color(srgb 0.1179 0.125 0.1143)`，匹配 blocking 角色。未提交用户。 |
| 缓存监控、空军深蓝灰 dark | 真实 Redis 数据的饼图与仪表盘正常；提示层背景 `rgb(38,49,68)`，文字 `rgb(234,242,255)`。 |
| 缓存监控、科技蓝 dark → light | 图表重绘且各有一个 canvas；浅色提示层背景 `rgb(249,253,255)`，文字 `rgb(27,31,39)`；图表数据不变。 |
| 设备端口 → 报文配置、科技蓝 light / dark | 真实抽屉内的 VXE 配置表、字段表、空态、校验面板跟随模式；暗色表格背景 `color(srgb 0.05 0.14 0.36)`，文字 `color(srgb 0.9217 0.9491 1)`。仅创建页面内草稿并取消，没有保存设备。 |

设备 SVG 端口补充验证：空军深蓝灰 dark 时填色/文字分别为 `color(srgb 0.1474 0.1938 0.2684)` / `color(srgb 0.9185 0.9504 1)`；切换 light 后变为 `color(srgb 0.974442 0.977474 0.983374)` / `color(srgb 0.1189 0.1224 0.1295)`，SVG 属性仍为 `var(--zx-semantic-surface-field-*)`。选中态代码使用 selected 配对，但此次点击未触发选中属性变化，不将其计为已验证。

## 截图

- [设备 SVG 端口暗色](evidence/2026-10-11-zxui-theme-assessment/device-port-air-gray-dark.jpg)
- [科技蓝浅色图表及提示层](evidence/2026-10-11-zxui-theme-assessment/charts-tech-blue-light.jpg)
- [科技蓝浅色 VXE 抽屉](evidence/2026-10-11-zxui-theme-assessment/vxe-tech-blue-light.jpg)
- [科技蓝暗色 VXE 抽屉与校验反馈](evidence/2026-10-11-zxui-theme-assessment/vxe-tech-blue-dark.jpg)
- [科技蓝暗色用户导入](evidence/2026-10-11-zxui-theme-assessment/import-tech-blue-dark.jpg)
- [陆军松枝绿浅色表单](evidence/2026-10-11-zxui-theme-assessment/dialog-army-pine-light.jpg)

## 保留边界与后续发布

- 按用户约束，没有运行 lint/build、没有新增或执行测试；两仓 `git diff --check` 通过。浏览器验证是开发态证据，不是生产发布验收。
- `packages/zxui/style/index.css`、主题 generated 和 dist 均未手工改动。正式发布时应正常生成结构样式并更新业务 ZXUI 包；当前旧 vendor ZXUI 包尚不含新的 VXE export，因此此轮继续依赖源码直连。
- `simulation-palette.css` / `simulation-utilities.css` 明确保存原有仿真固定色阶与工具类，它们仍是全局兼容词汇，并非已完成所有仿真主题迁移。没有把 gray/slate 全局重新定义成明暗语义色。
- 仿真专用页面、仿真结果图表、仅供仿真使用的旧 FloatingPanel 固定色及头像图片遮罩没有改造。跨仿真/普通页面的 NodeEditDrawer 现有 `--sim-*` 分支继续保留。
- 本地会话在跨页期间多次失效，恢复登录后继续验证；另观察到既有 provide 覆盖、GridList fill chain、EP type=text 警告及 keybindings `getModifierState` 错误。它们未作为主题修复处理，也不能声称控制台完全无错误。
- 未提交或推送，保留两仓既有未提交改动。验证结束恢复空军深蓝灰 dark / 宽松密度。

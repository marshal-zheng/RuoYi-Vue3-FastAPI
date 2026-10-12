# 仿真页面主题约定

仿真沿用应用的 ZXUI Host、主题目录和偏好控制器，随品牌、明暗模式与密度切换。根容器使用 `simulation-shell`，不再依赖 `simulation-dark` 或 `body.simulation-active`。

- 普通背景、文字、边框、阴影及交互色使用 `@zxio/theme-tailwind/v4.css` 的 `zx-*` utilities 或公开 `--zx-semantic-*` 变量。背景与文字应使用同一个 surface 的配套角色。
- `variables.css` 只把现有 `--sim-*` 名称映射到公开语义，在 Host/Portal scope 处求值；不得反向定义 `--el-*`、`--zx-*` 或 VXE 核心变量。
- ZxFloatingPanel、Dialog、Drawer、原生 Element Plus 控件及 VXE 公共桥负责组件外观。业务不再用全局 `!important` 深色规则覆盖它们。`global-popper-dark.css` 仅保留兼容说明；旧 `sim-*-dark` 类不决定明暗模式。
- `aviation-dark-theme.less` 仅保留业务内容布局。`simulation-dialog-theme.less` 只提供业务卡片和滚动条配方。
- 协议类型、故障原因/等级、发送/接收及曲线序列的分类色属于业务。固定分类色可以保留；状态数值文字使用可读的 status-on-surface 角色。SVG/Canvas 线条和序列颜色不按品牌机械替换。

## 图表与浮层

`src/theme/useChartTheme.ts` 只装配本应用的 manifest 查询，复用 `useZxChartThemeProjection` 和 `@zxio/chart` 的 `createChartEChartsTheme`。投影身份和颜色转换由库负责，业务不读取内部包路径或另写 sRGB 解析器。

- ECharts 初始化使用公共主题，切换时仅更新外观配置，保留数据和图例选择。
- 带宽和时序 Canvas 保留数据绘制及领域色，图表背景、文字和网格使用同一投影；空态和静止图表也随主题更新。
- 手绘图表的 tooltip 通过公开 `useRequiredThemePortalBinding` 挂载，跟随发起组件的 scope。Element Plus 的 body Popper 由应用已有 Host mirrored container 接管。

## 活跃入口与兼容边界

`simulation/index.vue` 直接使用 ZxFloatingPanel。`components/ui/FloatingPanel/index.vue` 只有公共 barrel 导出，没有活跃调用；它和 `backupindex.vue` 不作为当前页面的验收入口。旧面板没有存储持久化，当前页面 Dock 关闭/打开会重新挂载对应面板；主题切换不应重置几何或数据。

`BandwidthDashboard.vue`、`SimulationResultDialog.vue` 等导出但未接入当前路由的组件已收敛源码外观，不代表本次实际页面已覆盖。完整验证边界见仓库 `docs/reports/2026-10-11-zxui-simulation-theme.md`。

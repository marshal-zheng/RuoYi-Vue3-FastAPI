# 仿真页面 ZXUI 主题接入记录

日期：2026-10-11。实现与浏览器检查已完成，实时仿真业务验收受当前空工程限制。

本轮直接使用两个现有工作区和已启动的服务，保留原有未提交改动；没有创建线程、worktree、提交或推送，没有安装依赖、修改生成物或运行 lint、构建、类型检查和自动化测试。

## 结果与归属

| 层级 | 本轮处理 | 保留边界 |
| --- | --- | --- |
| ZXUI 公共结构样式 | 移除未分层的 `main { display: block }` 重置，避免压过业务 Tailwind `flex`；FloatingPanel 标题、正文、按钮使用 blocking 表面的配套前景色 | 同文件此前的 Dialog、Drawer、GridList 改动继续保留，不计为本轮新增 |
| ZXUI FloatingPanel | 将 attrs 显式绑定到真实面板根元素，关闭隐式继承，使 class、style、自定义属性和原生事件能越过 Teleport 根节点；补充组件文档 | 几何位置、拖动和状态仍由已有公共组件控制 |
| 公共 Chart | 复用 `useZxChartThemeProjection` 与 `@zxio/chart` 的 `createChartEChartsTheme` | 独立 chart 仓库没有改动；已有颜色适配器能处理编译器的 `color(srgb ...)` |
| 业务主题接入 | 新增 `src/theme/useChartTheme.ts`，只负责本应用 manifest 查询；移除仿真的全局固定深色覆盖层、重复核心变量和中性调色板 | 不新增业务主题引擎，不把内部组件路径变成公共 API |
| 业务页面 | 壳、Header、Dock、面板、空态、筛选控件、详情及弹窗改用公开表面／文字／边框／阴影角色；时序面板初始 top 随视口调整 | 协议、故障原因／等级、发送／接收、曲线序列等领域颜色保留 |
| 手绘图表 | 带宽、时序的中性背景、网格、标签与 tooltip 读取公共投影；tooltip 挂到公共主题 Portal | 不更改采样、数据、曲线分类色或绘制业务逻辑 |
| 导出型 ECharts 组件 | 初始化使用公共主题，品牌／模式变化时只更新外观配置 | 不因主题变化重建实例或重置图例选择；本轮只检查源码，未在活动路由挂载 |

源码联调继续使用业务 Vite 的 `zxuiSourcePlugin`，其中 `featurePackages` 包含 `@zxio/chart` 和 `@zxio/theme-tailwind`。没有为了联调重新打包或替换 vendor 包。

## 入口与旧实现对比

活动入口为 `src/views/project/simulation/index.vue`，其面板已使用 `ZxFloatingPanel`。`src/components/ui/FloatingPanel/index.vue` 只有 barrel 导出，没有发现活动调用；旧实现和 `simulation/backupindex.vue` 保持不动。

旧业务面板没有 localStorage 几何持久化。活动页面通过 Dock 隐藏／显示时会重新挂载面板，这个既有行为保留。已验证不重新挂载的主题切换保持位置；本轮不宣称新增跨刷新持久化。

当前活动面板隐藏公共折叠按钮，也没有启用 resize。实际验证覆盖 Dock 隐藏／显示、鼠标拖动与方向键移动，不包含未暴露的 resize 或面板原生折叠控件。

`BandwidthDashboard.vue`、`SimulationResultDialog.vue` 是导出但未进入当前仿真路由的组件。它们的 ECharts 更新逻辑经过源码检查，不能视为带真实数据的浏览器验收。

## 实际浏览器证据

复用前端端口 80、后端端口 8088，以现有验收账号打开工程“ZXUI 本地布局验收”：`/project/simulation/index/1?versionId=1`。没有创建工程、设备、拓扑或注入策略，也没有保存业务数据。

| 检查 | 观察结果 | 证据 |
| --- | --- | --- |
| 科技蓝浅色／深色 | 壳、面板、图表、文字与 tooltip 随模式变化；业务曲线和等级颜色保留 | [浅色最终截图](evidence/2026-10-11-zxui-simulation-theme/panels-tech-blue-light-final.jpg)、[深色最终截图](evidence/2026-10-11-zxui-simulation-theme/panels-tech-blue-dark-final.jpg) |
| 空军灰深色、宽松密度 | 面板表面和前景配套，最终恢复此偏好 | [最终截图](evidence/2026-10-11-zxui-simulation-theme/panels-air-gray-dark-final.jpg) |
| 陆军松枝绿浅色、1280×900 | 三个主要面板都在视口内；时序面板 bottom 为 808.5px；较小视口下允许浮动面板相互覆盖并拖动 | [小视口截图](evidence/2026-10-11-zxui-simulation-theme/panels-army-pine-light-1280.jpg) |
| 面板交互 | 最终鼠标拖动从 (88,174) 到 (138,204)，ArrowRight 再到 (146,204)；尺寸保持 520×390.5；Dock 收起／展开正常 | [结构化记录](evidence/2026-10-11-zxui-simulation-theme/browser-observations.json) |
| 切换主题保持几何 | 科技蓝浅色转深色的三个面板几何相同（默认密度下记录） | 同上 |
| 图表视图与悬停 | 汇总／按端口、时序／带宽分组可以切换；空缓冲区悬停显示 0.00 Mbps | 同上及浅色最终截图；不是实时采样证据 |
| 健康检查 | 浅色、深色弹窗可读，返回 2 通过、0 警告、2 错误；错误为缺少设备节点和通信连接 | [浅色](evidence/2026-10-11-zxui-simulation-theme/health-army-pine-light.jpg)、[深色](evidence/2026-10-11-zxui-simulation-theme/health-tech-blue-dark.jpg) |
| 注入策略浮层 | 保持注入面板打开时从科技蓝切为空军灰，面板和下拉浮层继承主题；五个策略选项显示正常，未确认保存 | [稳定态最终截图](evidence/2026-10-11-zxui-simulation-theme/injection-air-gray-dark-final.jpg)、[浅色截图](evidence/2026-10-11-zxui-simulation-theme/injection-dropdown-tech-blue-light.jpg) |
| 报告入口 | 提示“当前无仿真会话，无法生成报告” | 结构化记录 |

`*-final.jpg` 为最后版本截图；更早截图用于对应交互和视口证据，其中带宽网格尚未进行最后一次中性色收敛。截图已人工查看；下拉框最终截图在动画结束后重新保存。

## 检查与限制

- Vue SFC 解析和模板编译检查：25 个业务文件加 1 个公共 FloatingPanel，共 26 个，未发现语法错误。这里只做语法检查，不代表类型检查或构建成功。[源码记录](evidence/2026-10-11-zxui-simulation-theme/source-syntax.json)
- 静态 CSS 变量检查：43 个相关文件引用 46 个公开变量，均能在已有 theme-default 生成结果找到；只读比较，没有重新生成主题。[变量记录](evidence/2026-10-11-zxui-simulation-theme/public-variable-check.json)
- 两个仓库 `git diff --check` 均通过。独立 chart 仓库 `git status --short` 为空。
- 本轮浏览器会话捕获的 `pageerror` 为空；这不等同于宣称所有控制台 warning 或后端日志均为空。检查期间一次跳转登录页后重新登录，没有归因为主题错误。
- 当前工程无设备、连接、报文及仿真会话，未验证运行／暂停／单步、实时曲线数据、故障执行、设备／报文详情抽屉、事件触发和生成报告内容；没有用伪造数据替代这些验收。
- 公共 reset 与 FloatingPanel 会影响其他消费者。本轮只以实际业务页、源码检查和主题证据验证，未按要求之外扩大到全库回归。
- 两个工作区本来已有大量未提交修改，交付仍保持未提交。不能把整个工作区 diff 或其他既有删除项归为本轮产出。

## 计划阶段记录

实施计划：[2026-10-11-zxui-simulation-theme.md](../plans/2026-10-11-zxui-simulation-theme.md)。计划已在当前会话继续实施，没有创建独立工作项。

```text
STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-11-zxui-simulation-theme.md
EVIDENCE:
- READ: 两个仓库 AGENTS.md、主题 codemap、三份前序主题报告、活动仿真入口及面板／图表公共契约
- SEARCH: 活动调用、旧 FloatingPanel、固定深色样式和公共投影能力
- COMMAND: git diff --check 通过；语法与公开变量检查通过
PLAN_CHANGES: chart 已有公开能力足够，无需修改独立 chart 仓库；新增公共 attrs 和 main reset 修复
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: review
BLOCK_REASON: none
UNBLOCK_ACTION: none
```

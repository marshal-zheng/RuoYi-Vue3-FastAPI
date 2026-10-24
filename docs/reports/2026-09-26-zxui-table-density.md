# ZXUI 与 RuoYi：表格主题和密度收敛

本轮已完成表格密度接入，并修复验证中发现的固定列透字问题。RuoYi 移除全局固定表头、行高和重复颜色覆盖；ZXUI 为原生 ElTable 与 GridList 提供同一套密度和固定列状态样式。业务通过现有主题菜单选择紧凑、默认或宽松，偏好继续交给现有 Host / Provider。

## 问题归属

| 问题 | 归属 | 处理 |
| --- | --- | --- |
| 主题变化后，表头仍为 60px、表格行和行高仍为 56px | RuoYi 全局 components.less | 删除固定高度、字号和重复颜色覆盖；操作列只保留布局与主题间距 |
| 去掉业务覆盖后，原生表格 padding 仍来自 Element Plus 的固定 Sass 值 | ZXUI 的 Element Plus 适配层 | 单元格 spacing、文本 line-height 消费主题语义值，保留 small/default/large 偏移 |
| 半透明条纹、悬停、选中背景让横向滚动的文字透过固定列 | ZXUI 主题结构层 | 固定列使用不透明表面加主题状态层；原生表格使用 body，GridList 使用 elevated |
| 已有 density 偏好没有正常页面入口 | RuoYi 主题菜单 | 添加三档密度项，沿用 setZxThemePreference，不引入第二套状态 |

最初怀疑条纹覆盖选中行，核对 Element Plus 选择器及浏览器计算样式后排除了该问题，没有为这个假设调整 GridList 既有状态顺序。实际修复的是固定列的背景合成，以及选中后悬停的整行一致性。

## 实现边界

- 库的源文件是 `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`，位于现有 element-plus-skin 区段。没有新建表格包装组件，也没有新增主题 token。gutter、展开内容单元格保留原有垂直几何；选择与展开列保留横向特殊布局。业务列宽和对齐仍由调用方决定。
- 固定列使用相同主题变量的纯色渐变作为状态层。结构样式规则只为这一用途开放受限表达式，仍拒绝字面颜色和其他选择器复用；新增一条聚焦回归测试。
- `packages/zxui/style/index.css` 通过 `pnpm build:theme` 生成，没有手改产物；GridList 中英文文档说明密度与表面归属。
- 业务改动限于 `src/assets/styles/components.less`、`src/theme/ZxThemePresetSwitch.vue`、本地依赖及验收夹具。未改请求、权限、数据库或各页面列定义。
- 验收夹具在 `tests/fixtures/table-density/`，仅两个文件，使用本地内存数据检验多行、固定列和尺寸组合；没有增加自动化浏览器测试套件。它不是生产路由。
- 未迁移仿真专用页面，也未覆盖 TableV2。删除全局旧样式会作用于其共享 ElTable 消费者，本轮不把仿真页面列为已验收。

## 浏览器验证

真实后端页面验证用户、角色和登录日志。下表是组件默认 size 下的实测值，单位 px；内容和控件可以继续撑高行。

| 页面与主题 | 紧凑：表头 / 行 | 默认：表头 / 行 | 宽松：表头 / 行 |
| --- | --- | --- | --- |
| 用户，陆军松枝绿暗色 | 35 / 43 | 39 / 47 | 43 / 51 |
| 角色，默认浅色 | 37 / 45 | 41 / 49 | 45 / 53 |

默认主题与陆军主题的 spacing 本就不同，因此不强行统一成同一个像素高度。角色勾选普通角色后，工具栏修改按钮启用；取消后恢复禁用，未执行修改或删除。登录日志默认密度下切换明暗模式，表头保持 41px，背景随主题切换；实测行约 42.38px。

独立夹具验证原生 ElTable / GridList × 三档密度 × 三档组件尺寸，共 18 组。每组记录实际 DOM 是否存在 GridList、主题 variant 和 size class；文本行高 24px，多行内容实际高度与 scrollHeight 相同，没有截断。固定列横向滚动 188px 后，左右边界仍与表格边界相齐；选中、选中悬停及条纹的底层文字不再透出。

证据整理时发现浏览器工具的取消勾选动作没有切换包裹模式，已通过实际点击、读取 DOM 并重跑原生表格九组纠正。最终矩阵只保留真实模式匹配的结果。

本轮重点验证默认浅色 / 暗色、陆军松枝绿暗色；另外记录过火箭军苔藓绿暗色默认密度。没有重跑九主题全模式矩阵。最终页面恢复用户管理、陆军松枝绿暗色、默认密度、展开侧栏；未设置临时 viewport override，最终可视区 1728 × 936。

证据：

- [真实业务测量](evidence/2026-09-26-zxui-table-density/business-receipts.json)、[密度与尺寸矩阵](evidence/2026-09-26-zxui-table-density/density-size-matrix.json)、[固定列状态](evidence/2026-09-26-zxui-table-density/table-state-receipts.json)。
- [固定列修复前](evidence/2026-09-26-zxui-table-density/fixed-columns-before.png)、[修复后](evidence/2026-09-26-zxui-table-density/fixed-columns-after.png)、[原生固定列滚动](evidence/2026-09-26-zxui-table-density/raw-fixed-scrolled.png)。
- [最终用户页](evidence/2026-09-26-zxui-table-density/user-army-dark-default-final.png)、[角色浅色宽松](evidence/2026-09-26-zxui-table-density/role-default-light-comfortable.png)、[登录日志暗色](evidence/2026-09-26-zxui-table-density/loginlog-default-dark-default.png)。

## 构建与交付

| 检查 | 结果 |
| --- | --- |
| ZXUI `pnpm build:theme`、`pnpm build` | 通过 |
| 结构样式策略、样式拆分、GridList 主题测试 | 38 项通过；本轮只新增 1 项 |
| `check-structural-style.ts` | 单一来源、162+162+162 变体闭包、确定性构建、tar 审计通过 |
| 本轮策略 TS、业务 Vue 与夹具的聚焦 lint | 通过 |
| RuoYi `yarn ui:standards` | 静态规范检查及 14 项既有测试通过 |
| RuoYi `yarn type-check` | 更新本地包前后均通过 |
| 源码直连生产构建 | 通过，`/tmp/ruoyi-table-source-build`，26.60s |
| 本地安装包生产构建 | 通过，`/tmp/ruoyi-table-installed-build`，24.32s |
| 安装包结构 CSS 与库生成源比对 | 字节一致，SHA-256 `088932840eb7c7c92d5ade9d8c55ad17b7111ba8fe345ab2708d6fce2d6b4c41` |

本地交付为 `vendor/zxio-zxui-3.0.0-next.0-table.20260926.tgz`，package.json 与 yarn.lock 已更新；开发服务继续源码直连。未发布 npm、未提交 Git。两仓原有未提交改动保留，本地包包含此前已完成的工具栏和 Search 修复。

同目录保留构建、测试与类型检查日志；[交付断言](evidence/2026-09-26-zxui-table-density/delivery-verification.json)核对了安装样式、18 组模式归属、多行无截断、密度递增和固定列边界。

本轮未宣称全仓质量检查全绿：既有大包、peer dependency、Vue 插件提示仍存在；上一轮记录的工程页格式错误、独立 chart / drive 包契约问题没有在本轮处理或重新验证。下一项仍是窄屏顶栏布局，属于业务布局优化，应单独评估，不混进表格适配层。

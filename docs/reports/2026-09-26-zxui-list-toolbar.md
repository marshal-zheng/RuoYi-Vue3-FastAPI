# ZXUI 与 RuoYi：公共列表工具栏收敛

本轮完成：修复 ZXUI Search 清空时使用旧查询的事件顺序问题；ZXUI 新增 `ZxListToolbar`，RuoYi 的 23 处列表接入，并删除业务侧 111 行重复工具栏样式。查询、权限、控件属性、请求回调和页面脚本保持不变。

## 判定与修复

问题的直接来源是业务 `src/assets/styles/components.less`：两套重复规则使用固定间距，筛选分组不允许换行。最初检索遗漏了 LESS 文件；浏览器实测后已纠正结论。1024px 窗口下，用户页工具栏可用宽度 536px，内部内容宽度 1064px，控件超出列表。

ZXUI 原有 GridList 只提供 `form` 插槽，没有统一的列表工具栏布局。该能力也适用于不使用 GridList 的部门、菜单列表，因此应由库提供独立组件，业务负责填充操作和筛选内容。

- 组件：`/Users/hqz/Downloads/element-plus/packages/components/list-toolbar/src/list-toolbar.vue`。三个具名插槽 `actions`、`filters`、`search`；没有查询模型、请求或权限逻辑。原生属性透传根节点，使用 group 语义并保留普通 Tab 顺序。
- 样式：`/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css` 的 list-toolbar 区段。按容器宽度换行，间距读取 `--zx-semantic-spacing-control-y`，无新增主题变量或固定颜色。空分组不占布局。
- 公共入口：根包导出与全局安装、`@zxio/zxui/list-toolbar`、`@zxio/zxui/list-toolbar/style/css` 均可用，包含构建后的类型和样式。
- 文档：ZXUI 中英文 ListToolbar 页面、可运行示例、GridList 引用及侧栏入口。
- 业务：23 处模板改为具名插槽。完整清单见 [迁移文件](evidence/2026-09-26-zxui-list-toolbar/migrated-files.json)。旧 `zx-grid-form-bar` 引用已清零；保留该 LESS 文件的其他表格规则。
- 本地交付：更新 `vendor/zxio-zxui-3.0.0-next.0-toolbar.20260926.1.tgz`、package.json 和 yarn.lock。未发布 npm，未提交 Git。开发仍使用源码直连。

## 验证中发现并修复的库问题

ZxSearch 清空按钮先发出 `clear` / `search`，异步 watcher 随后才更新 v-model，导致业务回调读取旧查询。真实用户页表现为输入框已经清空、列表仍只有搜索后的 1 条。

修复位于 ZXUI `packages/components/search/src/search.vue`：值同步 watcher 使用 `flush: 'sync'`，保证 v-model 先于动作事件更新。新增一条受控调用方测试，修复前明确失败（`clear:admin`、`search:admin` 先于 `model:`），修复后通过。真实页面复测一次点击清空即恢复 2 条，无需再点击搜索。中英文 Search 文档补充事件顺序。本轮合计只新增两条回归测试。

## 验证

| 项目 | 结果 |
| --- | --- |
| ZXUI `pnpm build:theme`、`pnpm build` | 通过，包含声明生成和公共产物 |
| 新组件状态归属测试 + 现有 GridList 测试 | 6 项通过；只新增 1 项测试 |
| Search 与快捷键测试 | 7 项通过，包含新增的事件顺序回归 |
| 现有样式拆分测试 | 5 项通过 |
| ZXUI 本轮组件、入口与示例 lint | 通过 |
| RuoYi `yarn type-check` | 新安装包下通过 |
| RuoYi 源码直连生产构建 | 通过，输出 `/tmp/ruoyi-toolbar-source-build` |
| RuoYi 安装包生产构建 | 通过，输出 `/tmp/ruoyi-toolbar-installed-build` |
| 安装包入口验证 | 根导出、leaf 导出相同；全局注册成功；leaf CSS 包含布局和 density 变量 |
| 23 处迁移前后比对 | 控件属性、脚本与 scoped styles 一致；无新增 lint 诊断 |

浏览器在真实后端页面验证用户、角色和部门列表。用户搜索 `admin` 返回 1 条，清空后恢复 2 条。代表性布局结果：

| 页面 / 窗口宽度 | 工具栏宽度 | 内容宽度 | 结果 |
| --- | ---: | ---: | --- |
| 用户 / 1024px（修复前） | 536px | 1064px | 溢出 |
| 用户 / 1024px（修复后） | 536px | 536px | 正常换行 |
| 角色 / 768px | 691px | 691px | 操作、筛选、搜索可见 |
| 角色 / 390px | 313px | 313px | 操作按钮与筛选均换行 |
| 部门 / 390px | 308px | 308px | 独立工具栏正常 |

本轮验证默认浅色、科技蓝暗色、陆军松枝绿暗色；间距分别读取主题值（默认与科技蓝 16px，陆军绿 14px）。本轮没有重跑九主题全部模式矩阵，也没有单独切换 compact density；上一批次的全主题验证不能替代本轮未执行的检查。最终恢复陆军松枝绿暗色、原始窗口尺寸及展开侧栏。

证据：[浏览器测量](evidence/2026-09-26-zxui-list-toolbar/browser-receipts.json)、[用户页 1024px](evidence/2026-09-26-zxui-list-toolbar/user-1024.png)、[角色页 768px](evidence/2026-09-26-zxui-list-toolbar/role-768.png)、[默认浅色](evidence/2026-09-26-zxui-list-toolbar/role-default-light.png)、[科技蓝暗色](evidence/2026-09-26-zxui-list-toolbar/role-tech-blue-dark.png)、[迁移比对](evidence/2026-09-26-zxui-list-toolbar/ruoyi-toolbar-migration-verification.json)。同目录保存构建、测试和包入口检查记录。

合计 18 项聚焦测试通过；Search 修复后已重新构建 ZXUI、本地包及业务两条生产链路。

## 仍需区分的已有问题

- 全仓包契约检查未通过：独立 chart 包缺少 tokens/types 依赖声明，drive 有 5 处依赖允许列表错误。它们不是本轮新增 ListToolbar 出口错误；没有修改这些独立仓库。
- 23 处业务文件的 scoped lint 保留了工程页原有的 49 条格式错误、原有警告；前后诊断比对确认没有新增。不把这项检查表述为全绿。
- 生产构建仍有既有大包提醒；浏览器仍有既有 Provider 重复配置、Element Plus text button 弃用等警告。

## 后续优先级

1. **P1，先调业务**：`components.less` 仍全局固定表头 60px、表格行 56px、行高 56px 和字号 14px，阻止 ZXUI 的表格密度完整生效。先移除或收敛这些覆盖，再判断库的映射是否有缺口。
2. **P2，业务布局**：390px 下顶栏文字和账户区域拥挤换行，见部门页截图。列表工具栏已经无横向溢出，顶栏需单独处理响应式布局。
3. **P2，先确认复用需求**：旧 RightToolbar 的搜索/刷新被注释，列配置直接修改传入数据。当前有效使用很少，尚不适合直接扩成庞大的库工具栏；若需要公共列设置，应单独设计受控的 columns API。

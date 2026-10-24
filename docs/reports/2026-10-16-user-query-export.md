# 用户列表与 Excel 导出条件统一

日期：2026-10-16。本轮仅修复用户管理页的条件来源，未提交 Git、未发布包。

## 责任与根因

问题在业务页面，ZXUI 已有公开能力足够解决，无需修改组件库或 HTTP 客户端。

- 导出按钮位于页面 `header-right` 插槽，原先引用的 `query` 只属于 GridList 的 `form` 插槽。Vue 编译后实际读取不存在的 `_ctx.query`，随后旧 `onExport` 将条件覆盖为 `{}`。
- 部门保存在独立的 `deptSelectedId`，日期在列表加载时转换，导出又依赖请求完成后写入的 `currentQuery`。同一组条件存在多份状态；旧请求后完成还会覆盖导出缓存，GridList 自身的响应代次保护无法保护这份旁路状态。
- 后端列表和导出均使用 `UserPageQueryModel`、`GetUserListQuery`、同一数据权限及 `paginate_with_dept` 过滤逻辑；本次条件丢失发生在前端。导出的既有服务上限为 10000 条，本轮没有改变它。

依据为业务 `src/views/system/user/index.vue`、`src/api/system/user.ts`、`src/utils/ruoyi.ts`，ZXUI `packages/components/grid-list/src/{instance,use-grid-state,use-grid-request}.ts`，以及后端 `modules/system/api/user_controller.py`、`application/services/user_service.py`、`infrastructure/user_repository.py`。`getStateSnapshot` 返回 query/pager 的深拷贝，`updateState` 是现有公开状态入口。

## 本轮实现

1. 部门选择写入 `query.deptId`，保留其余筛选，并重置到第 1 页。
2. 列表将 GridList 的 `query/pager` 显式转换为用户 API 的平铺筛选和 `page/pageSize`。
3. 导出按钮直接调用 `handleExport`，通过 `getStateSnapshot()` 取得当前查询；列表、导出共用已有 `queryTransform → serializeDateRange`，日期转换不修改可编辑条件。
4. 导出仅传筛选，不传分页；移除独立部门状态、异步条件缓存及旧 `onExport`。

长期收益来自消除多份查询状态，复用已有公开契约。没有新增查询管理器、兼容层、依赖或全局参数规则。用户名、手机、状态、日期和部门仍是业务条件，不进入 `@zxio/http`。

## 验证

新增 2 项必要回归，执行真实页面中的函数，并编译模板检查插槽作用域。先恢复任务开始时的页面观察到 2 项预期失败，再应用修复通过；锁定同源条件、分页边界、部门切换、清空条件及旧请求完成后不覆盖导出条件。此处没有将 mock 逆序完成冒充为整个 GridList 的运行时竞态测试。

| 检查 | 结果 |
| --- | --- |
| 业务定向回归 | 5 文件、103 项通过，含本轮新增 2 项 |
| ZXUI 既有 GridList 请求回归 | 1 文件、12 项通过 |
| 前端全量 ESLint / type-check | 通过 |
| ZXUI 源码直连生产构建 | 通过，25.37 秒；存在 CSS、chunk 及动态导入提示，未扩大修复范围 |
| 两仓库 `git diff --check` | 通过 |
| 独立只读审查 | 无阻塞项；另行运行本轮 2 项回归通过 |
| changed 规范脚本 | 未通过：既有 `VersionList.vue` console 检查；该文件与任务开始时 hash 一致，其余 guardrails 通过 |

真实验证使用实际用户页 handler、ZXUI 源码 `useGridState/useGridRequest`、业务请求和下载模块、Axios 1.20.0，经 JSDOM XMLHttpRequest 访问本机 FastAPI/MySQL；通过 openpyxl 读取真实导出的 Excel，以用户编号比较完整集合：

| 场景 | 列表总数 / Excel 行数 | 结果 |
| --- | --- | --- |
| 专用用户名筛选，每页 1 条，跨 2 页后导出 | 2 / 2 | 一致，导出不受当前页限制 |
| 用户名 + 手机 + 状态 + 日期 + 部门 | 1 / 1 | 一致 |
| 状态无匹配 | 0 / 0 | 一致 |
| 切换另一部门 | 1 / 1 | 一致 |
| 日期无匹配 | 0 / 0 | 一致 |
| 清空日期、状态和手机 | 2 / 2 | 一致，无旧日期残留 |
| 清空全部条件 | 3 / 3 | 一致，包含当轮 2 个临时用户 |

7 个场景均确认列表请求成功、列表和导出发送相同筛选、导出排除分页、可编辑查询未被转换污染、loading 关闭一次。有数据的 Excel 均为 1 个工作表、13 列；零结果导出维持后端既有空表行为。控件清空值按当前实现核对：状态 `undefined`、日期 `null`、文本 `''`。

验证期间新增停用临时用户时，发现范围外问题：创建已经落库，后续详情回读因 `get_user_with_relations` 限定正常状态而返回 404。本轮没有修改它；完整验证改用两个正常临时用户，停用状态验证无匹配结果。探针早期另纠正了状态清空值及请求层省略 undefined 属性的断言，生产代码未因此扩大改动。

所有尝试的专用标记用户均经业务 API 软删除并查询确认无可见遗留；软删除及正常审计历史保留。Excel 临时二进制已删除。仅停止本轮启动的后端及子进程，保留原有 Docker/Redis 服务。

反馈、loading、文件保存入口由探针记录，没有使用 computer use，没有浏览器点击或视觉验收；不把真实后端验证表述为浏览器端到端验收。工作区原有业务与 ZXUI 改动按任务开始时 hash 核对，本轮仅改业务用户页、增加上述回归和本报告证据。

证据：[真实结果](evidence/2026-10-16-user-query-export/actual.json)、[检查命令](evidence/2026-10-16-user-query-export/checks.json)、[基线保留](evidence/2026-10-16-user-query-export/baseline-preservation.json)。

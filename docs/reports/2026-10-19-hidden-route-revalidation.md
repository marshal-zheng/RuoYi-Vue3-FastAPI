# RuoYi 隐藏路由热更新、刷新与权限切换复验

已完成 8 条非仿真业务隐藏路由、设备无 ID 变体的真实页面复验。修复了权限重载后仍 404、当前 404 不恢复及异步响应竞态，并修复验收中发现的字典筛选和页面布局问题。68 项测试、全量前端类型检查、改动文件 ESLint、源码直连构建均通过。保留已有改动，未提交或推送。

## 实际范围与结果

继续使用本地 MySQL/Redis、后端 8088、前端 80，前端通过 `VITE_ZXUI_LOCAL=true` 直连 ZXUI 源码。真实入口使用鼠标/键盘操作；刷新为完整文档重载；热更新为临时修改实际 Vue 脚本，收到 Vite `hot updated` 后核对页面和挂载 Router，再恢复源文件原字节。

| 页面 | 真实入口 | 刷新 / 脚本 HMR | 撤权 / 直访拒绝 / 同地址重新授权 |
| --- | --- | --- | --- |
| 分配角色（对照） | 用户行“分配角色” | 通过 | 通过 |
| 分配用户 | 角色行“分配用户” | 通过 | 通过 |
| 字典数据 | 字典类型链接 | 通过 | 通过 |
| 调度日志 | 定时任务“日志” | 通过 | 通过 |
| 修改生成配置 | 生成表行“编辑” | 通过 | 通过 |
| 工程详情 | 工程名称链接 | 通过 | 通过 |
| 设备详情 | 设备名称链接 | 通过 | 通过 |
| 设备详情（无 ID） | 新加→填写名称/自有分类→下一步 | 通过 | 通过 |
| 拓扑设计 | 版本“图编辑” | 通过 | 通过 |

逐项证据见 [覆盖矩阵](evidence/2026-10-19-hidden-route-revalidation/coverage.json)、[真实入口/刷新/HMR 原始记录](evidence/2026-10-19-hidden-route-revalidation/route-cases.json)、[9 组权限变化记录](evidence/2026-10-19-hidden-route-revalidation/permission-transitions.json)。查询参数（含生成器页码、拓扑版本 ID）在同地址恢复时保持。

公共隐藏路由另行验证：个人中心通过真实头像菜单进入、刷新与 HMR；登录、注册、401、未知地址的预期 404 均通过刷新与 HMR，并验证注册返回登录、401 返回、404 返回首页。[公共边界记录](evidence/2026-10-19-hidden-route-revalidation/public-routes.json)。`/redirect` 是瞬时跳转，只验证跳转到已授权字典页，没有声称对其驻留页面做独立 HMR。[重定向结果](evidence/2026-10-19-hidden-route-revalidation/redirect-after.json)。

仿真路由及仿真执行按仓库 AGENTS.md 排除。调度日志使用 `jobId=0` 的全部日志入口，现有任务/日志为空，未创建或运行任务。现有工程 1、版本 1、设备 1、生成元数据 `sys_post` 和字典 1 均只读；未保存设备草稿、拓扑、生成配置，也未生成文件或执行 DDL。设备菜单原本不存在，使用可清理的独立菜单暴露真实 `device/index` 页面。

## 根因、修复与证据

### 1. 新权限未参与隐藏路由过滤

开发菜单重载只读取 `/getRouters`，隐藏路由却使用用户 Store 中的旧权限过滤。因此后台已授权、菜单已出现，真实“字典类型”链接仍跳到 404。[修复前状态与截图](evidence/2026-10-19-hidden-route-revalidation/stale-permissions-before.json)。

`permission.reloadDynamicRoutes` 现在先刷新 `getInfo`，再读取并注册菜单及权限路由。初始生成和重载均使用现有安全会话版本，阻止已结束会话的迟到菜单覆盖新会话；不同会话不会共享旧的进行中重载。`user.getInfo` 在更新状态前同样检查会话版本，并在没有角色时清空旧权限。空角色与迟到用户信息分支属于静态代码定位加单元测试，未冒充真实页面复现。

### 2. 路由已加入，页面仍停留在 404

真实浏览器中主动刷新用户权限后，`router.resolve` 已得到 `Data`，但 `currentRoute` 仍为 catchall，页面继续显示 404。[修复前匹配差异](evidence/2026-10-19-hidden-route-revalidation/rematch-before.json)。

采用 Vue Router 已有的 `replace` 重新匹配当前完整地址；无权限时才转到首个可访问菜单。该行为依据 [Vue Router 动态路由文档](https://router.vuejs.org/guide/advanced/dynamic-routing.html)：添加记录不会自动更新当前渲染页面。当前路径在异步读取完成后取得，避免把请求期间的新导航拉回旧页面。

修复后，无需手动刷新，原 404 直接恢复为字典数据页。[授权后结果](evidence/2026-10-19-hidden-route-revalidation/permission-grant-after.json)。真实拦截并延迟菜单响应，期间通过头像菜单进入个人中心，撤权完成后仍停留个人中心，字典路由已删除。[慢请求导航验证](evidence/2026-10-19-hidden-route-revalidation/delayed-menu-navigation.json)。修复前 4 个真实 Router 回归均失败，修复后通过；旧会话响应分支由内存中的真实 Router 验证。[失败基线](evidence/2026-10-19-hidden-route-revalidation/tests-before.log)。

权限变化由后台真实授权 API 暂置，再调用现有开发同步入口触发路由重载；页面导航和登录切换使用真实用户控件。没有修改客户端权限数组来制造结果，也没有宣称普通角色修改会自动发布 SSE。另用两个独立账号真实退出/登录，受限账号直访及刷新均保持预期 404，切回管理员角色账号恢复路由。[账号切换拒绝证据](evidence/2026-10-19-hidden-route-revalidation/account-switch-denied.json)。

### 3. 字典缓存命中时漏掉类型筛选

字典元数据已有缓存时，默认类型在 watcher 创建前已存在，非 immediate watcher 不运行；HMR 后第一条列表请求缺少 `dictType`，从用户性别 3 条变成全部字典 84 条。改为立即同步当前类型，继续复用原列表和查询机制。[修复前](evidence/2026-10-19-hidden-route-revalidation/dictionary-cache-before.json)、[修复后 3 条](evidence/2026-10-19-hidden-route-revalidation/dictionary-cache-after.json)。

新增挂载实际字典页、使用真实 Query 缓存的回归，检查第一条列表请求包含 `sys_user_sex`；修复前断言精确失败于缺少该参数。[测试失败基线](evidence/2026-10-19-hidden-route-revalidation/dict-test-before.log)。

### 4. 页面可见性问题

- 头像依赖已无定义的旧图片类，图片实高 198px、容器仅 120px，遮住用户名。头像组件现在拥有自身的 120px 尺寸、圆形裁切和图片适配；实测图片与容器均为 120px，文字不重叠，裁剪弹框打开/关闭正常。[修复前尺寸](evidence/2026-10-19-hidden-route-revalidation/avatar-layout-before.json)、[修复后](evidence/2026-10-19-hidden-route-revalidation/avatar-layout-after.json)。
- 1100px 下字典操作及工程版本“图编辑”被挤出可视区。使用既有表格 `fixed="right"`，使操作入口可见；真实点击“图编辑”并返回通过。[入口坐标与点击结果](evidence/2026-10-19-hidden-route-revalidation/narrow-route-controls-after.json)。
- 生成器把百分比字符串当列最小宽度，字段和选择器被压缩到难以阅读。改为可读的数值最小列宽并固定字段名，宽表通过表格原生横向滚动展示；1100px 下滚动 802px 后仍能识别字段并访问最右侧选项，提交/返回始终可见。[滚动验证](evidence/2026-10-19-hidden-route-revalidation/generator-scroll-after.json)。采用 [Element Plus Table 的固定列与列宽能力](https://element-plus.org/en-US/component/table.html)，未添加自定义滚动或尺寸框架。

此次在业务层修复路由授权、请求时序和页面配置，ZXUI 源码未改。复用现有会话版本、路由 API 与表格能力；代价是开发菜单重载增加一次 `getInfo` 读取，密集生成器表格需横向滚动，避免再引入路由缓存或兼容分支。

## 热更新共享基础与视觉验证

上轮 Router 单例及 lazy Layout 修复保留，本轮 `src/router/index.js` 原字节未改。将实际加载模块及两份额外 `t` 时间戳模块作为诊断探针读取：3 份导出均指向当前挂载 Router，8 条业务路由各只有 1 个记录。[模块身份探针](evidence/2026-10-19-hidden-route-revalidation/router-module-identity.json)。这是显式诊断探针，不代表浏览器自然发生了 3 次并行模块加载。

8 条业务页和个人中心均检查 1440×1000、1100×800；已逐张查看截图，修正上述遮挡与窄屏入口问题。横向宽表的非固定数据列允许表内滚动，未声称所有列同时可见。[最终视口记录](evidence/2026-10-19-hidden-route-revalidation/visual-checks.json)。代表截图：[字典窄屏](evidence/2026-10-19-hidden-route-revalidation/Data-1100-final.png)、[图编辑入口](evidence/2026-10-19-hidden-route-revalidation/ProjectDetail-1100-final.png)、[生成器左侧](evidence/2026-10-19-hidden-route-revalidation/GenEdit-1100-final.png)、[滚动右侧](evidence/2026-10-19-hidden-route-revalidation/GenEdit-1100-scrolled.png)、[头像修复](evidence/2026-10-19-hidden-route-revalidation/Profile-1440-final.png)。

探索覆盖已显示 404 后授权、当前页撤权、慢菜单读取与用户导航交错、完整账号退出/登录、设备无 ID 草稿、生成器横向滚动。未出现未处理页面异常；业务浏览器记录共 637 个请求、无 5xx，含有意受限的初始版本读取 403。公共边界补验单列记录。[请求记录](evidence/2026-10-19-hidden-route-revalidation/network.json)、[页面异常记录](evidence/2026-10-19-hidden-route-revalidation/page-errors.json)。

## 质量检查与清理

- `vitest run --config ../docs/reports/evidence/2026-10-19-hidden-route-revalidation/source.vitest.config.mts`：7 文件、68 项通过，覆盖真实 Router/Pinia、权限 Store、用户会话、菜单 HTTP 契约、开发同步、授权页面和字典缓存。[日志](evidence/2026-10-19-hidden-route-revalidation/tests-final.log)。
- `vue-tsc --noEmit`：通过；10 个本轮改动文件 ESLint：通过。[类型检查](evidence/2026-10-19-hidden-route-revalidation/typecheck.log)、[Lint](evidence/2026-10-19-hidden-route-revalidation/lint.log)。
- `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus vite build --outDir /tmp/ruoyi-hidden-route-build-mvex2c1g --emptyOutDir`：通过；保留既有依赖及分包体积提示，无部署。[构建日志](evidence/2026-10-19-hidden-route-revalidation/build.log)。
- 两个用户 143/144、角色 97、菜单 1080、设备分类 1 删除均返回 204；有效业务记录、关联、意外保存设备均为 0；自有会话残留为 0，清除 2 个自有 CSRF 键，浏览器关闭。[API 清理](evidence/2026-10-19-hidden-route-revalidation/cleanup-api.json)、[存储核验](evidence/2026-10-19-hidden-route-revalidation/cleanup-storage.json)。用户/角色遵循正常软删除策略，未删除既有业务或审计资料。
- 14 个关注文件保存基线，其中 5 个（Router、主守卫、开发同步及其测试、Vitest 配置）保持原字节；本轮修改 6 个业务文件、3 个已有测试，新增 1 个测试。既有脏改动保留。临时 HMR 注释全部移除，结构化证据认证字段扫描通过。[保存清单](evidence/2026-10-19-hidden-route-revalidation/preservation.json)、[本轮差异目录](evidence/2026-10-19-hidden-route-revalidation/current-pass-diff/)。字典页初始为干净文件，其基线取自保存的初始 Git HEAD。
- RuoYi 与 ZXUI 的前后 HEAD 分别保持 `4ed36ba`、`09257a6`；没有执行提交或推送。前端/后端仍 200。[最终汇总](evidence/2026-10-19-hidden-route-revalidation/verification-summary.json)。

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-19-hidden-route-revalidation.md
EVIDENCE:
- READ: router/index.js, stores/permission.ts, stores/user.ts, real entry callers, AGENTS.md, prior acceptance report.
- SEARCH: hidden route paths, permissions, menu reload callers and actual page controls.
- COMMAND: Plan structure rg checks passed; execution results are listed above.
PLAN_CHANGES: Added observed dictionary, avatar and narrow-table fixes plus public route boundaries during execution.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: completed current-session execution; preserve changes for user review.
BLOCK_REASON: none
UNBLOCK_ACTION: none

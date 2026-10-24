# 用户“分配角色”偶发 404 根因与修复

已复现完整 404，并修复前端开发模式下的 Router 实例分叉。真实页面授权、清空、重复进入、刷新、前进后退及权限反例通过。保留已有改动，本轮没有提交或推送。

## 根因证据

这次失败现场的 URL 是有效的 `/system/user-auth/role/141`，但页面只有“404错误”。已挂载 Router 只有 8 条公共路由，没有 `AuthRole`，应用 Pinia 尚未建立用户/权限 store，启动时也没有正常执行 `/getInfo`、`/getRouters`。不是后台授权接口找不到用户：此前该对象的授权读取为 200，页面授权保存为 204，认证的菜单签名/事件请求仍成功。

浏览器在同一文档实际加载了两份 Router 模块：

| 模块时间戳 | 是否挂载到应用 | 当时路由数 | 当前路径 |
| --- | --- | ---: | --- |
| `1792392525819` | 是 | 8 | `/system/user-auth/role/141` |
| `1792392633347` | 否 | 8 | `/` |

用浏览器已经加载过的**完整模块 URL**读取命名空间，确认两者的 `default` 是不同对象。入口持有第一份 Router，守卫依赖链引用了另一份；因此实际挂载的 Router 没有执行登录守卫，也没有生成动态路由，最终命中公共 catch-all 404。这次诊断没有通过手动删除路由制造现场。

另一个触发问题是同步依赖循环：`Router → Layout → Sidebar → Permission Store → Router`。修改 Layout 脚本并在热更新时点击授权入口，抓到了 `ReferenceError: Cannot access 'Layout' before initialization`，位置为 Router 公共路由的 Layout 引用。布局热更新、模块失效与刷新时的资源请求交错，使不同时间戳的模块引用成为可发生的场景。仅改成懒加载消除了初始化异常，但随后仍捕获到上述完整 404；因此修复同时处理了循环依赖和 Router 实例身份。

证据：[完整 404 现场](evidence/2026-10-19-user-role-route-404/404-two-router-modules.json)、[两个实例身份](evidence/2026-10-19-user-role-route-404/router-identity-before.json)、[现场截图](evidence/2026-10-19-user-role-route-404/page-failure-observed.png)、[循环初始化错误](evidence/2026-10-19-user-role-route-404/hmr-before.json)。

## 实现

- `src/router/index.js` 导出共享的懒加载 Layout，Permission Store 也使用该加载器。Router 初始化不再同步执行 Layout/Sidebar/Permission Store；菜单落地页判断仍使用同一个 Layout 引用。
- 在开发环境复用 Vite 原生 `import.meta.hot.data` 保存 Router。相同模块路径的不同 `t` 版本在**同一文档**内共用 Router 和 History，守卫、Store 与挂载应用不会分叉。完整文档刷新后创建新实例；生产构建没有 HMR 缓存。没有增加全局注册框架或改成无条件公开隐藏路由。
- 增加真实 Vue Router + Pinia 回归；Vitest 的解析扩展顺序与生产 Vite 对齐，才能实际导入原先省略 `.vue` 扩展名的 Router，避免继续把整个 Router mock 掉。

方案核对了 [Vite HMR data 的模块路径生命周期](https://vite.dev/guide/api-hmr.html#hot-data)、[Vue Router 动态注册契约](https://router.vuejs.org/guide/advanced/dynamic-routing.html)，以及当前安装的 Vue Router/Vite 实现。直接使用现有懒加载与 HMR 能力，没有新增依赖。

## 验证

| 验证层级 | 结果与边界 |
| --- | --- |
| 真实页面与服务 | 独立账号 140 对用户 141 选择角色 95，保存 204；重新进入勾选状态保留。清空保存 204，重开不再勾选。重复关闭/进入 3 次、直接刷新及浏览器后退/前进通过。 |
| 慢请求交错 | 只延迟真实 `/getRouters` 请求，不替换响应；等待期间从用户页点击“分配角色”，再释放响应。最终仍匹配 `AuthRole`，没有 404。 |
| HMR | 同样的 Layout 脚本更新与真实按钮点击通过，不再出现 Layout 初始化错误。验证包括热更新及随后的完整刷新；完整刷新可以更换实例，不能据此要求跨文档实例不变。 |
| 多版本模块探针 | 同一文档额外求值两个不同 `t` 的 Router URL，与已挂载版本合计三份引用全部是同一个 Router；仍有 51 条路由和 `AuthRole`。这是模块身份探针，明确不冒充页面输入。 |
| 权限反例 | 只读账号 142 的用户列表没有“分配角色”按钮；直接深链没有 `AuthRole`，显示预期的 404；尝试 PUT 授权返回 403。修复没有越过编辑权限边界。 |
| 可视检查 | 1440×1000、1100×800 的授权对象、角色表格、勾选状态和保存/关闭按钮可见；窄视口长角色名按原有规则省略，页面无异常遮挡。 |
| 自动回归 | **46 项 / 5 文件通过**：3 项新 Router/Layout 回归，5 项路由 Store、10 项菜单 HTTP 契约、7 项菜单同步、21 项授权页面回归。 |
| 类型、风格、构建 | 完整 `vue-tsc --noEmit`、受影响文件 ESLint、Vitest 配置格式检查及 `git diff --check` 通过。ZXUI 源码直连生产构建通过（30.67 秒），输出到独立 `/tmp/ruoyi-user-role-404-build-mvevs2b7`，没有部署。构建保留已有依赖/大 chunk 提示。 |

关键记录：[修复后实例身份](evidence/2026-10-19-user-role-route-404/router-identity-after.json)、[真实授权保存](evidence/2026-10-19-user-role-route-404/grant-page.json)、[清空读回](evidence/2026-10-19-user-role-route-404/clear-role-page.json)、[重复导航及慢请求](evidence/2026-10-19-user-role-route-404/page-route-cycles.json)、[历史导航](evidence/2026-10-19-user-role-route-404/history-navigation.json)、[权限页面反例](evidence/2026-10-19-user-role-route-404/permission-negative.json)、[写入 403](evidence/2026-10-19-user-role-route-404/permission-denied-write.json)、[测试日志](evidence/2026-10-19-user-role-route-404/tests.log)、[构建日志](evidence/2026-10-19-user-role-route-404/build.log)。

## 清理与保留

账号 140、141、142，角色 95、96 及其关联已通过 API 清理；数据库计数确认活动用户、活动角色、用户角色、角色菜单、角色部门均为 0。已退出登录并清理自有会话/CSRF，残留自有会话为 0；关闭了本轮 Playwright 浏览器，没有清空共享日志。

临时 Layout/Sidebar 探针已移除，文件字节恢复到本轮开始基线；13 个基线文件无缺失，仅 5 个已有文件发生本轮预期修改，新增 1 个 Router 回归文件。原用户页、授权页、登录守卫、用户 Store、菜单同步实现均保留。两仓库 HEAD 在并行工作期间发生变化，本轮未执行提交/推送，也未回退其他工作的提交。

[清理记录](evidence/2026-10-19-user-role-route-404/cleanup-storage.json)、[源码增量与保留核对](evidence/2026-10-19-user-role-route-404/preservation.json)、[服务状态](evidence/2026-10-19-user-role-route-404/services-final.json)。后端和前端仍分别为 200，供后续本地工作继续使用。

后续复验已覆盖其余非仿真隐藏路由：发现并修复权限快照未刷新、当前 404 未重新匹配及异步会话/导航竞态，另修复真实页面发现的字典筛选和可见性问题。见 [隐藏路由复验报告](2026-10-19-hidden-route-revalidation.md)。上文保留本次分配角色问题的原始复现与证据。

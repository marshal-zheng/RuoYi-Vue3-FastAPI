RESULT: FAIL
P0: 0
P1: 0
P2: 1
RERUN_REQUIRED: yes
Reviewer Mode: independent-subagent

## Spec Alignment Review Report

### Summary

审查对象为项目本地工作树 `/Users/hqz/dev/RuoYi-Vue3-FastAPI/.worktrees/role-authorization-convergence` 相对 BASE `3e6936e1a839d21ebb17ac5eec36721772d8862f` 的本轮候选（含新增文件），以及源 dirty 后端的 `backend/source-preserving.patch`。首轮发现一项必须修正的 P2 权限可用性问题。未发现 P0/P1。审查代理未参与本轮实现，未修改产品代码，未使用 computer use。

最初委派为前端独立审查；主代理随后明确扩大为本轮后端候选及源保留补丁的独立审查。后端实际业务写入包含源仓保留的 JSON DTO/UserRoleService 实现，不能用工作树 HEAD 旧写端替代该真实契约。

### Spec Checklist

- [x] 角色、用户角色授权、角色已/未分配用户读取使用独立资源身份、规范化参数与原生 Query 生命周期。
- [x] 对照 ZXUI 源码确认 controlled GridList 的 rows/pagination/status、page-change、refresh 与空态契约；原 request 模式读取嵌套 pager。
- [x] 检查真实 mounted GridList/ElTable 测试覆盖初读、分页、快速搜索、失败/重试、paused、跨页选择、清空、重开与 scope/route 隔离。
- [x] 角色树使用独立权限端点资源键；抽屉保持 useEditorRead 开启快照，不用刷新结果覆盖草稿。
- [x] 写命令捕获 DTO/scope，角色写入失效 roles/users，授权写入失效 users；成功写入不等待后续读取成功。
- [x] 用户/角色授权返回仅恢复 submitted filters/page/size；会话变化清空，不启用全局 KeepAlive。
- [ ] 管理员角色操作入口使用与源后端一致的系统管理员身份（P2-01）。
- [x] 核实后端完整已有授权、读取前目标用户数据范围检查、缓存移除范围，以及源停用角色可编辑/不存在 404 等 dirty 规则保留。

### Alignment Table

| ID | Requirement / Evidence | Result |
| --- | --- | --- |
| A1 | role.ts / user.ts 查询工厂复制规范化筛选，页码和 pageSize 进入 key；API 传递 signal/queryRequest/scope | PASS |
| A2 | role/index.vue 受控列表、只读缓存行状态操作、搜索回第一页、主命令失效 | PASS |
| A3 | 三授权页的增量/完整替换语义、显式空数组、选中集合、草稿保护与读取恢复 | PASS |
| A4 | RoleFormDrawer / RoleDataScopeDrawer 初读取消、错误重试、刷新错误/paused、重开/旧写隔离 | PASS |
| A5 | system-list-navigation.ts 只保存已提交筛选和分页，session watch 清空 | PASS |
| A6 | 管理员角色操作入口与后端实际身份一致 | FAIL: P2-01 |
| A7 | getAuthRole 控制器 → query → handler 的数据范围检查在服务读取前；仓储返回可选正常角色与已分配停用/管理员角色 | PASS |
| A8 | 移除 role:list/select/detail、menu:tree/role_tree/list 结果缓存（源 menu:list 已无该缓存），menu:detail 保留 | PASS |
| A9 | 源 dirty 规则采用窄 source-preserving.patch；标准源基线/交付验证 | Candidate review PASS; source-baseline checks deferred to source delivery |

### Verification Log

| ID | Command / Inspection | Result | Evidence |
| --- | --- | --- | --- |
| V1 | `./node_modules/.bin/vitest run src/queries/system/role.test.ts src/queries/system/user.test.ts tests/unit/components/RoleAuthorizationMounted.test.ts tests/role-query-list.test.ts tests/unit/components/EditorReadLifecycle.test.ts tests/unit/components/RoleFormDrawer.test.ts --reporter=dot`（工作树 frontend） | PASS | 独立运行：6 files / 91 tests passed，exit 0；4.09s。非阻断 Browserslist 数据年龄提示。 |
| V2 | `./venv/bin/python -m pytest tests/unit/services/test_role_query_consistency.py tests/unit/services/test_user_authorization_read.py tests/unit/services/test_role_service.py -q --no-cov`（工作树 backend） | PASS | 独立运行：19 passed，exit 0；3.49s。仅定向单元/内存与测试数据库验证。 |
| V3 | `git diff --check`（工作树） | PASS | 独立运行 exit 0，无输出。 |
| V4 | 阅读 `/Users/hqz/Downloads/element-plus/packages/components/grid-list/src/{grid-list.vue,use-grid-controller.ts,use-grid-request.ts}` | PASS | controlled 模式无内部 loadOnMounted 请求；页面提供 pagination.page/size/total 和 status；查询仅由业务 Query observer 所有。 |
| V5 | 阅读 `backend/http_runner.py`、`http_schedule.py`、`http-red.json`、`http-green.json` | PASS | 独立审阅他方证据，未重新执行该真实 HTTP 调度。RED 的 role list/detail/menu tree 后续独立 GET 仍旧；GREEN 独立 GET 为已提交值。跨数据范围分别由重复旧 role ID 变为各自 ID，越范围 authRole GET 从 200 变 403，assignedDisabledVisible 从 false 变 true。 |
| V6 | 阅读 `backend/source-preserving.patch` 及 `source-inputs`/`source-preserved-candidate` 关键实现；核实源 UserRoleService/DTO 写链路 | PASS | 补丁不回退源停用角色 detail 读取、404 和 JSON 写边界；菜单 detail 缓存不属于删除范围。 |

真实受控 HTTP A/B 直接覆盖三类缓存消费者（role list/detail/role menu tree）及权限/关联读取；其余三类缓存使用生产服务与 MemoryRedis 的定向回归，不把它们称为独立真实 HTTP A/B。A/B 使用 source-preserving 候选导入和仓储 barrier，不是最终无 overlay 的源运行。前端使用真实 GridList/ElTable 的 jsdom mounted 测试，其他壳组件和 HTTP API 为测试替身；没有浏览器验收。

源分支 ancestry、标准源无 overlay 业务链路、源基线、保留快照、工作树/分支清理均由主代理后续交付阶段完成，属于 source-baseline checks deferred to source delivery，不是未实现的候选功能阻断。本报告不宣称这些步骤已完成，也不宣称全库全绿。

### Action Items

**P2-01：管理员角色操作入口使用角色名称，而后端使用系统用户身份。**

- 观察位置：`ruoyi-fastapi-frontend/src/views/system/user/authRole.vue:86-94,154-159`、`src/views/system/role/authUser.vue:131-135`、`src/views/system/role/selectUser.vue:118-123`（首轮候选行号）。
- 复现条件：登录账号 userId 不是 1，但持有 `admin` 角色与相关编辑权限；打开包含 roleId=1 已有关联的用户授权页，或直接进入 roleId=1 的角色授权路径。
- 原因：前端 `checkRole(['admin'])` 为 true，解除 protectedRoles/管理员角色操作限制；源 `UserModel.check_admin` 只将 userId=1 设置为 admin，源两个 controller 传递 `enforce_scope_checks=not current_user.user.admin`，源 `UserRoleService._check_roles` 对 enforce=true 的 roleId=1 调用 `check_role_allowed_services` 并拒绝。完整替换还会检查已有 roleId=1，所以即使未选中该角色也不能绕过。
- 影响：界面错误地允许保存或管理员角色授权操作，随后服务端必然拒绝；用户授权页还不显示“需要管理员调整授权”的原因。这是确定的入口可用性错误，不是成功越权证据。
- 建议：在本轮授权入口使用已捕获 `QueryScope.userId === '1'` 与实际后端系统管理员身份一致（或明确同步修改后端契约；本轮不需要扩大权限策略），保留普通接口权限检查。
- 必要回归：以非 1 用户但 roles=['admin'] 检查完整替换阻止并显示原因、roleId=1 撤销禁止、选择用户弹框增量授权禁止；同时保留 userId=1 的既有授权路径。
- 状态：已通知主代理与授权实现代理，待修复后独立复验。此首轮 FAIL 报告保留，不覆盖为 PASS。

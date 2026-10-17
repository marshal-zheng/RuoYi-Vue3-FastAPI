# 角色管理与双向授权浏览器验收修复：独立复审

复审对象：基线 `fe5081897704dc4bff1cfff5fbdc06ea357f7af5`，项目本地工作树 `role-browser-acceptance` 的 7 个已跟踪文件 diff 及新增 `test_role_user_read_contract.py`。本记录仅评价当前候选；浏览器验收仍由主代理继续进行。

## 结论

未发现 P0、P1、P2 问题，可以在浏览器验收完成、临时验收数据清理并核对提交边界后交付。

- **行身份修复有对应行为依据。** 已检查当前依赖 Element Plus 2.13.0 `table-body/render-helper.mjs`：未指定 rowKey 时按行索引作为行和单元格 key。新增回归挂载真实 ElTable/ElTableColumn，保留 API 与抽屉替身；查询刷新将同一行位置角色 82 换成 85，核对旧操作节点已脱离页面、新按钮属于新节点且编辑调用 `85`。已检查 RED 日志，原实现只在节点复用断言失败；本次独立运行 GREEN。测试覆盖列表刷新时真实 DOM 的业务身份边界，不用抽屉内部实现冒充编辑流程。
- **创建时间丢失修在读取投影层。** RoleUserItemReadModel 与 UserAllocatedRoleReadModel 补充 `create_time`，仓储及 service 原来已有该值；不改变写入模型、请求体、权限检查或关联集合语义。测试分别覆盖已分配/未分配用户、已关联/可选角色，通过真实 SQLite 仓储、service、query handler 和 HTTP 响应序列化验证 `createTime`。这些测试不发起 ASGI 路由请求，真实端到端交互以主代理浏览器证据为准。
- **公开契约边界清楚。** 已核对原有 UserInfoModel、RoleModel/SelectedRoleModel 含创建时间。角色用户列表路由使用通用 PageResponseModel；用户授权路由使用 UserRoleResponseModel，当前读取模型不作为 OpenAPI schema 直接公开。已检查离线 schema 对照元数据，本轮不需要生成产物变更。
- **视觉改动范围明确。** 表单标签 inline-flex 保持必填标记同行；角色表时间列最小宽度 180px、操作固定右侧；用户授权长角色名/权限字符使用现有表格 tooltip 能力。视觉效果、1024/1440 视口及键盘实际交互由主代理验收，本复审没有将这些未完成项目判为通过。

## 独立验证

- 后端 5 个相关测试文件：**25 passed**。使用共享源 venv，测试数据库为 SQLite 内存，不连接或修改真实数据库。
- 前端角色列表、授权 API、角色及用户查询资源 4 个 suite：**37 passed**。
- 隔离工作树 `git diff --check`：通过。
- `applied-paths.json` 8 个文件：源目录与隔离工作树 sha256 全等。
- 详细命令、基线与文件 hash 见 `independent-review-verification.json`。

## 验证边界

本代理没有使用浏览器、登录、操作真实数据库或服务，也没有修改产品文件或提交。未运行全仓构建/全量测试。主代理此前后端/frontend 约定检查及 RED/GREEN 元数据已阅读，但不计为本代理重跑。源目录全局 diff check 报告的 `tests/unit/security/test_sql_injection.py:389` 末尾空行属于无关 dirty，未修改；隔离候选无该问题。

## 最终布局差量复核

仅复核最后一条差量：角色列表创建时间列从 `width="180"` 改为 `min-width="180"`。已用上一轮记录的文件 hash 证明替换回旧属性后内容完全一致，且源目录和隔离工作树相同。Element Plus 表格保留时间列 180px 的最小宽度，宽屏可分配剩余空间，避免所有列固定宽度留下空白；窄屏列最小宽和右侧操作列固定关系不变。未发现新增 P0/P1/P2。未重复已通过测试，主代理负责最终源 suite、浏览器截图、临时数据清理和提交。

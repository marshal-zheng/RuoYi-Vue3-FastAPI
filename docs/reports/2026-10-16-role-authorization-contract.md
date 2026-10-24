# 用户角色授权 HTTP 契约与权限边界

本轮收敛用户分配角色、角色增量授权用户、单个及批量取消授权四种操作。保留原有 URL，改用四个专用 JSON 输入和固定服务方法，消除共用可选字段导致追加请求误走替换或清空的路径。同步封闭普通用户新增、编辑中 `roleIds` 的同类写入口；未混入其他 HTTP 优化，未提交或发布。

## 输入与操作语义

| PUT 路径 | 输入模型 | 必填 JSON 字段 | 集合语义 |
| --- | --- | --- | --- |
| `/system/user/authRole` | `UserRolesAssignModel` | `userId`, `roleIds` | 完整替换，`[]` 清空 |
| `/system/role/authUser/selectAll` | `RoleUsersGrantModel` | `roleId`, `userIds` | 非空增量添加，保留其他角色 |
| `/system/role/authUser/cancel` | `RoleUserRevokeModel` | `roleId`, `userId` | 只撤销指定关联 |
| `/system/role/authUser/cancelAll` | `RoleUsersRevokeModel` | `roleId`, `userIds` | 非空批量撤销指定关联 |

四个操作均返回 204，无响应体；OpenAPI 和生成 TypeScript 响应均已一致。请求字段不再从 Query/CSV 中提取，旧 Query-only 调用返回 422。JSON 中其他操作的字段、未知字段均拒绝。

ID 必须为 `1..2147483647` 的整数，与当前 DO 的 Integer 身份定义一致；不把布尔、字符串或浮点值强制转换成 ID。数组按首次出现的顺序去重，集合缺失、null、CSV 字符串或非法成员返回现有 Problem Details 422。普通用户新增/编辑仅其 `roleIds` 字段复用同一严格、去重类型，保持原有“省略则保留、null 或空数组则清空”的约定。

采用现有 FastAPI/Pydantic 的模型、字段约束和 `extra='forbid'`，没有新增依赖或通用授权框架。JSON 数组可以直接表达空集合，省去 CSV 的解析和缺省歧义；代价是所有真实调用一起迁移。严格类型依据 [Pydantic strict mode 官方说明](https://docs.pydantic.dev/latest/concepts/strict_mode/)，并已用本机实际版本和注册路由验证。

## 权限与事务

新增 `UserRoleService` 集中四种关系操作，预检复用既有用户/角色保护及数据范围规则，访问数据库使用现有 Repository。所有目标预检完成后才写关联，复用 CQRS、请求数据库会话和事务装饰器，统一提交；预检失败、第二项写入失败、提交失败均无部分关联残留。

- 用户与角色都必须存在且未删除。非管理员同时受用户范围、角色范围约束；批量包含一个不可访问对象即整单拒绝。
- 用户 1 的角色关联受到保护。非管理员即使拥有全部数据范围，也不能授予或撤销角色 1；管理员仍可对普通用户合法授予、撤销角色 1。
- 整组替换检查提交角色和当前角色的并集，防止通过清空或替换移除无权操作的旧关联。普通用户新增/编辑显式写入角色时复用这项预检，避免绕路。
- 用户分配角色继续要求 `system:user:edit`；角色侧三个操作继续要求 `system:role:edit`。角色页的添加、单个取消和批量取消按钮均已对齐这个权限。
- 追加与撤销只改变目标关联，重复授权/重复撤销不影响其他角色；没有建立兼容双轨，旧混合模型、旧增删服务和无消费者的关联详情服务/port 已移除。

实际授权页链路还发现一个被缓存掩盖的调用错误：旧方法把 AsyncSession 当成 RoleService，角色选项缓存未命中时会发生 AttributeError。该读取现直接复用原 loader 所用的 `RoleRepository.find_all_active()`，选项过滤规则保持一致；已先复现失败，再通过回归。

## 验证与证据

[命令和验证汇总](evidence/2026-10-16-role-authorization-contract/verification.json)、[真实业务结果](evidence/2026-10-16-role-authorization-contract/actual.json)、[独立复核](evidence/2026-10-16-role-authorization-contract/review.txt)：

- 后端聚焦 **117 项通过**。新权限回归使用真实 SQLite、生产 Repository 和 SQL 数据范围表达式，断言拒绝前没有关联 DML；覆盖存在性、受保护对象、两侧范围、整批拒绝、清空、增量、去重和事务回滚。专用授权、普通编辑绕路及冷缓存读取均保留失败回归证据。
- 前端聚焦 **28 项通过**，覆盖生产 SFC setup/动作、API 的 JSON 序列化及操作反馈链路；全局 `yarn lint:check`、`yarn type-check` 和 ZXUI 源码直连生产构建通过。构建保留既有大 chunk 提示。
- **86 项真实链路检查通过**：生产 SFC setup/保存/确认、生产 API/request/feedback、ZXUI HTTP 源码、Axios XHR、真实 FastAPI、本地 Docker MySQL 和验证专用 Redis。包括污染字段、ID/集合边界、双方缺失及越权、接口权限、管理员合法授权、普通用户编辑绕路、批量失败和合法关联保留。
- 写入中途和最终提交故障由临时本地服务包装器注入；两种 500 均只产生一次反馈、保留客户端请求/响应上下文，不触发重新登录，关联整批回滚。最终提交阶段使用既有最外层兜底错误处理，其 500 缺少服务端请求编号；这是本轮验证出的限制，未扩展通用异常中间件。
- OpenAPI 差异限于四条操作和相关请求 schema；四个专用模型新增、旧混合模型删除，普通用户两个输入模型的角色数组约束同步更新。17 个契约/生成文件重复生成无漂移。保留既有枚举成员顺序，未扩大无关生成差异。
- 独立复核运行 **101 项相关回归通过**，并确认最终生成物、旧路径清理和事务链无阻塞发现。
- `yarn ui:standards` 通过（14 项）。新 Python 文件 Ruff/格式检查通过，与本轮起点比较后端 Ruff 无新增诊断。后端约定脚本通过；前端约定脚本仍被未改动 `VersionList.vue` 的既有 console 用法阻挡。

未使用 computer use，未验收浏览器视觉渲染和原生表单校验，未运行完整全仓测试。这里的真实业务证据覆盖生产代码到数据库的实际请求链路。

## 数据与工作区

[工作区起点比较](evidence/2026-10-16-role-authorization-contract/workspace-audit.json)记录 3578 个起点条目：本轮修改 26 个已有文件，没有删除基线文件；保留全部既有未提交、未跟踪及已删除状态。新增文件为专用 DTO、业务服务、必要回归及本报告/证据。

验证只操作自己创建的临时用户、角色、部门和关联。真实请求完成后原有用户、角色、岗位、部门列表及总数完全一致，完整用户角色关联完全一致；另核对原有用户/角色/部门身份和用户岗位、角色菜单、角色部门关联摘要一致。仅物理清理本轮创建的临时记录，正常操作及登录审计保留，不宣称数据库被物理回滚。

[运行环境清理](evidence/2026-10-16-role-authorization-contract/runtime-cleanup.json)：验证后端 8088 和专用 Redis 16379 已停止。日常 Redis 6379 当时无法从宿主连接，故验证使用独立临时进程；没有启动 Homebrew Redis 服务。原有 Docker MySQL、Redis 及其他容器保持运行。

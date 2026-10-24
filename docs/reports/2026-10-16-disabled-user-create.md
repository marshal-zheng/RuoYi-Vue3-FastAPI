# 停用用户创建后回读 404 修复

本轮已完成，未提交 Git、未发布。仅修改后端关联查询、两个身份认证调用及对应的内部协议，未改 ZXUI、HTTP、前端或数据库结构。

## 根因和责任

创建控制器执行 `AddUserCommand` 后，通过 `_load_user_detail → GetUserDetailQuery → user_detail_services` 读取创建资源并返回 201。原 `get_user_with_relations` 无条件要求用户状态正常，把已经存在的停用用户当作不存在，导致创建后的资源回读报 404；普通详情及修改状态后的回读也受同一条件影响。

这个方法有 6 处生产调用：用户管理服务 4 处，身份认证服务 2 处。不能直接删除状态过滤，否则 token 解析可能接受停用用户。密码登录则使用独立的 `LoginRepository.find_user_with_dept`，并由 `authenticate_user` 显式拒绝停用账号。

本轮将 `get_user_with_relations(user_id, *, active_only=False)` 定义为默认读取未删除的用户，管理端可查看停用账号。token 解析和路由读取显式传入 `active_only=True`；HTTP 与 WebSocket 共用该 token 解析链路。`IUserRepository` 同步更新签名和语义。软删除、接口权限、数据权限及关联部门/角色/岗位原有条件保持不变，密码登录的停用判断没有修改。

长期收益是管理可见性与认证有效性不再混在一个隐含条件中，创建和状态变更能够复用同一个详情读取。代价仅为一个明确的查询条件及两处真实消费者迁移，没有增加平行查询实现或新的认证机制。

## 回归和代码验证

新增一个测试文件，共 6 项：4 组使用真实 SQLite 查询验证启用、停用、软删除状态的管理/认证可见性；另 2 组通过实际 `LoginService` 和 repository 验证启用账号可解析当前用户、停用账号拒绝解析，token 验证器单独 stub。先观察原实现停用详情返回空及缺少显式认证查询契约的失败，再完成修复。新增 token 用例的非空密码 fixture 修正后，最终全部通过。

| 检查 | 结果 |
| --- | --- |
| 用户读写、仓储、登录、token、控制器、协议覆盖定向回归 | 8 文件、42 项通过 |
| 新增测试 Ruff / 格式检查 | 通过 |
| 内部协议格式 / 修改文件 Python 编译 | 通过 |
| Git 差异空白检查 | 通过 |
| 独立只读审查 | 生产调用无遗漏、无剩余阻塞；独立复跑新增 6 项通过 |
| 修改源文件 Ruff 对比 | 修改前后均 169 项既有诊断，没有新增诊断 |
| 修改源文件格式对比 | 修改前后相同，`user_repository.py` 和 `login_service.py` 原有格式不合规 |
| changed 后端规范脚本 | 未通过：全工作区目标共 204 项 Ruff 诊断及上述两文件格式；guardrails 通过，没有混入全文件格式化 |

扩展运行还发现既有 `test_login_controller_refresh.py` 期望 `body.data.token`，实际 endpoint 已返回平铺资源，结果为 35 项通过、该项 KeyError。已比较 HEAD，refresh 函数和该测试均未修改，且本轮修改的方法不在该路径上；没有将该次运行报告为全部通过，也未修改范围外契约或测试。

## 真实业务验证

使用实际 `UserFormDialog` 创建提交与打开 handler、业务 API、源码 `@zxio/http`、Axios 1.20.0，经 JSDOM XMLHttpRequest 访问真实本机 FastAPI/MySQL。创建的临时用户没有管理权限，仅关联一个现有岗位。

| 场景 | 实际结果 |
| --- | --- |
| 表单创建停用用户 | 201，返回停用资源及有效绝对 Location，岗位关联保留，success 事件一次 |
| 打开停用用户详情、按停用条件查询 | 详情 200、列表命中 1 条，打开 loading 释放 |
| 使用正确密码登录停用用户 | 401，保留“用户已停用”原因 |
| 启用后登录、读取当前用户和路由 | 状态变更、登录、getInfo、getRouters 均 200 |
| 普通用户访问管理详情 | 403，接口权限仍然生效 |
| 再次停用后由管理员回读 | 状态变更和详情均 200 |
| 停用后使用原有效 token、新密码登录 | getInfo、getRouters、密码登录均 401 |
| 软删除后读取详情 | 删除 204、详情 404、可见列表遗留 0 条 |

上述 8 组完整验证通过。探针早期修正了 Location 的既有 `/dev-api` 前缀和路由集合 `{ items }` 断言，没有因此修改生产代码。所有尝试的专用标记用户均已通过业务 API 软删除并查询确认无可见遗留，正常软删除与审计记录保留；探针登录会话已退出。

扩展检查实际表单编辑资料时发现另一个既有问题：`edit_user_services` 对 `exclude_unset=True` 的结果无条件执行 `del edit_user['role']`，页面没有传入该字段时返回 500/KeyError。这与启停状态无关，服务文件与 HEAD 完全一致，已记录但未混入修复；因此不声称一般资料编辑链路通过。

UI 打开、loading、success、反馈入口由探针记录，没有使用 computer use，没有浏览器点击或视觉验收。本轮仅停止自己启动的后端和子进程，保留原有 Docker/Redis。任务开始时已有的 475 个业务工作区文件、141 个 ZXUI 文件按 hash 核对保持不变。

证据：[真实结果](evidence/2026-10-16-disabled-user-create/actual.json)、[检查与边界](evidence/2026-10-16-disabled-user-create/checks.json)、[静态检查对比](evidence/2026-10-16-disabled-user-create/static-comparison.json)、[基线保留](evidence/2026-10-16-disabled-user-create/baseline-preservation.json)。

# 角色授权后端读取闭环证据

本报告覆盖本轮后端实现与受控验证；源分支交付、无 overlay 标准后端验收由主任务记录。起点为 `std` / `3e6936e1a839d21ebb17ac5eec36721772d8862f`。未操作 computer use、steamer-front，未 reset、seed 或更改既有用户和权限数据。

## 根因与修复

- `RoleService` 的 `role:list`、`role:select`、`role:detail` 采用 cache-aside；角色写入在事务提交前删除结果缓存，已经取得旧 SQL 快照的并发 GET 可以随后回填。`MenuService` 的 `menu:tree`、`menu:role_tree`、`menu:list` 还依赖当前用户角色关系，现有双向授权写入没有失效这些结果。
- `role:list` 把 `str(data_scope_sql)` 放入缓存键。两个不同部门的 SQLAlchemy 条件都字符串化为 `sys_dept.dept_id = :dept_id_1`，忽略绑定值。纯内存探针及真实双账号 HTTP 均证明了不同范围错命中。
- 移除上述六类结果缓存，保持直接仓库读取；保留不属于本轮角色关联依赖的 `menu:detail` 缓存。未增加锁、版本、分布式协调或全局依赖框架。当前本机只读统计为 2 个有效角色、94 个正常菜单；正常非管理员角色选项 1 行，单次查询约 1.407 ms。这是本机观测，不是容量保证。
- `GET /system/user/authRole/{userId}` 原读取只包括正常且非管理员角色目录，完整替换提交可能遗漏原有停用或管理员角色。新增仓库查询返回“正常可选目录 + 全部已关联正常/停用/管理员角色”的并集，`flag`、`user.role`、`user.roleIds` 从完整 `UserRoleDO` 关系产生。
- 同步补齐授权详情目标不存在的 404，以及调用者的用户数据范围检查。双向授权写 DTO、增量/替换/清空/撤销与原有预检保持源仓当前规则。

SQLAlchemy 官方说明字符串 SQL 与绑定参数值是分开的；跨进程标识需要包含参数值：[SQLAlchemy 表达式与编译](https://docs.sqlalchemy.org/en/20/core/foundation.html#sqlalchemy.sql.expression.ClauseElement.compile)。Redis 的 cache-aside 依赖应用失效与 TTL，并不自动协调数据库提交：[Redis cache-aside](https://redis.io/docs/latest/develop/use-cases/cache-aside/)。本轮修复选择来自真实依赖和 A/B 证据，不是把所有资源缓存统一删除。

## 验证

新增 10 项回归在任务基线全部失败，修复后全部通过；最后扩大到角色/菜单/用户查询、控制器和事务相关 **49 passed**。覆盖真实服务与生产 QueryCache 的受控内存竞态、绑定参数范围隔离，以及 SQLite 真实仓库的完整关联读取、缺失目标和拒绝越范围读取。

在独占登录时间窗中，使用源目录 FastAPI、真实 MySQL/Redis 和正常产品 HTTP API 执行相同调度的 RED/GREEN。仅测试进程提供局部仓库 SQL 后 barrier 与本地 Unix IPC，QueryCache 使用本轮独有命名空间，端口为 `18088`。GREEN 仅通过 7 个源保留候选文件的定向 import 覆盖实现；源文件未改动。

| 检查 | RED 源 current | GREEN 候选 |
| --- | --- | --- |
| 角色列表旧读跨写后回填 | 新独立 GET 仍为 v1，SQL 已 v2 | 独立 GET 为 v2 |
| 角色详情旧读跨写后回填 | 新独立 GET 仍为 v2，SQL 已 v3 | 独立 GET 为 v3 |
| 角色菜单勾选旧读回填 | 独立 GET 仍为空，关联已提交 | 独立 GET 含新菜单 ID |
| 两个自建部门账号读取同参数角色列表 | B 错拿 A 的角色 | A/B 各自正确 |
| A 读取 B 的用户授权详情 | HTTP 200 | HTTP 403 |
| 已关联停用角色 | roles 中缺失 | roles 中存在且 flag=true |

每轮 3 个角色、2 个用户、2 个部门全部经正常 DELETE 清理；独立 SQL 的有效行计数、`sys_user_role`、`sys_role_menu`、`sys_role_dept` 关联计数均为 0。自建用户的 Redis 活跃会话索引为 0，两轮管理员会话均正常 logout。主任务随后复用了 GREEN 进程做源码/本地产物前端链路，收到其完成通知后清空独有缓存并停止 PID 54989；RED PID 52216 也已停止。两 PID 不存在、18088 关闭、本轮 socket 删除，未停止共享数据库/Redis/8088 服务。

首次 RED 登录与主任务管理员探针并发，既有单会话策略替换了主任务会话。发现后立即暂停并改为串行；主任务自建 6 条 fixture 的恢复清理由主任务独立记录。不能把该次会话失败归因于本轮产品修改。

## 源保留与检查边界

源仓已有未提交的角色写字段白名单、关系缺省保留、停用详情读取、缺失详情 404、独立 `UserRoleService` 与严格 JSON DTO。这些不是本轮新增，不能从任务 HEAD 整文件覆盖源文件。源保留候选使用原始源内容，仅替换已限定的方法/导入，`source-preserving.patch` 在未修改的源 current 上 `git apply --check` 通过。未把 source-only `user_role_service.py` 或其测试整份纳入任务。

受影响 7 个产品文件为 `modules/system/{api/user_controller.py,application/handlers/query/user_query_handlers.py,application/queries/user_queries.py,application/services/role_service.py,application/services/menu_service.py,application/services/user_service.py,infrastructure/role_repository.py}`。其中角色/菜单/用户服务及用户控制器与源 dirty 重叠，需按源保留补丁移植。

任务受影响既有文件 Ruff 基线和修复版同为 **125 条诊断**，逐文件、规则、消息和代码行对照没有新增诊断；格式检查同有既有未格式化文件。3 份本轮测试 Ruff/format 通过。技能 validate 在提供 venv PATH 后如实返回 lint/format 失败；不能据此声称全后端全绿。

另对源 current 的 5 份相关既有测试做对照：基线 **124 passed / 2 failed**，候选 **120 passed / 6 failed**。原有 2 失败均为已去缓存的部门服务还断言必须删缓存；新增 4 失败均为 source-only 测试直接 patch 已删除的角色缓存符号（2 项）或断言必须删除角色缓存（2 项）。这些实现耦合断言未被偷偷修改或整份带入交付；授权业务行为回归、真实 A/B 及本轮 49 项回归通过。角色服务不保留无用途缓存兼容符号来让旧断言变绿。

源现有写规则允许保留或删除已关联停用角色，也未在服务端禁止直接 API 新授予停用角色。本轮只修完整读取，不新增 source-only 写规则。管理员角色关联的操作资格沿用 `current_user.user.admin`，不是仅角色名称中含 `admin`。角色定义本身仍受管理员保护。

原始证据保存在源 `.git/codex-delivery-preservation/role-authorization-convergence/backend/`：`unit-{red,green}.log`、`http-{red,green}.json`、`backend-{red,green}.log`、`source-tests-{baseline,candidate}.log`、`source-tests-comparison.json`、`ruff-{head,task}.json`、`lint-comparison.json`、`readonly-scale.json`、`owned-relations-session-cleanup.json`、`runtime-cleanup.json`、`source-inputs.json`、`source-preserving.patch`。最终候选只比真实 GREEN 运行多一处 `List[RoleDO]` → `list[RoleDO]` 返回注解；运行原始 SHA 另存 `runtime-inputs-before-final-annotation.json`，最终任务回归再次通过。仍需主任务在源交付后完成标准无 overlay 验证。

源交付补记：实现现已交付 `std@d558dfb`，标准源 8088 无 overlay 的两种消费方式实链通过，源相关后端 91 tests 通过；最终保留、清理及全库检查边界见同目录 `2026-10-17-role-authorization-convergence.md`。

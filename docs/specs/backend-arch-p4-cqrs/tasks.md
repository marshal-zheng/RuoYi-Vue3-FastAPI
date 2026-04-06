# CQRS 读写分离实现任务

> 范围说明（2026-02-21）：本阶段 CQRS 改造优先覆盖系统管理域，`simulation/protocol/device` 相关模块暂不纳入实现范围，后续单独排期。

- [x] 1. 建立 CQRS 目录与基础抽象
  - 创建 `application/commands|queries|handlers|behaviors|read_models|mediator` 结构。
  - 定义 `ICommandHandler`、`IQueryHandler`、`IPipelineBehavior` 抽象接口。
  - 建立 Handler 注册表。
  - 本轮进展：`modules/system/application` 已落地 CQRS 基础结构、`CommandResult`/Handler/Behavior 抽象、`HandlerRegistry` 与 `Mediator`；补充 `modules/system/tests/test_cqrs_mediator.py` 验证注册、分发、缺失处理器报错与管道执行顺序。
  _需求追溯: R1.AC1, R2.AC1, R3.AC4, R4.AC1_

- [x] 2. 全量写路径改造为 CommandHandler
  - 将写类接口改造为 Command -> Handler 处理模式。
  - CommandHandler 内实现验证、业务决策与持久化。
  - 返回统一 `CommandResult`。
  - 本轮进展：`/system/config`、`/system/dict`、`/system/dept`、`/system/menu`、`/system/post`、`/system/notice`、`/system/role`、`/system/user` 写路径均已迁移到 CommandHandler。`config` 已落地 `Add/Edit/Delete/Refresh`，`dict` 已落地 `DictType` 与 `DictData` 的 `Add/Edit/Delete/Refresh`，并新增 `dept/menu/post/notice/role/user` 的写 Command 与 Handler；对应控制器写接口统一改为 `mediator.send(command)`。`dept/role/user` 控制器残留的数据权限与可操作性校验已下沉至对应 `*_command_handlers.py`，控制器仅保留请求映射与分发。新增 `modules/system/tests/test_config_write_commands.py`、`modules/system/tests/test_dict_write_commands.py`、`modules/system/tests/test_dept_write_commands.py`、`modules/system/tests/test_menu_write_commands.py`、`modules/system/tests/test_post_write_commands.py`、`modules/system/tests/test_notice_write_commands.py`、`modules/system/tests/test_role_write_commands.py`、`modules/system/tests/test_user_write_commands.py` 覆盖分发链路。
  _需求追溯: R1.AC1, R1.AC2, R1.AC3, R1.AC4_

- [x] 3. 全量读路径改造为 QueryHandler + ReadModel
  - 将查询接口改造为 Query -> Handler 处理模式。
  - 为列表/详情/视图场景定义独立 ReadModel。
  - 读路径执行只读会话语义。
  - 本轮进展：`config/dict/dept/menu/post/notice/role/user` 读路径已迁移到 QueryHandler。`config` 新增 `GetConfigList/GetConfigDetail/GetConfigValueByKey` 与 `ConfigPage/ConfigDetail/ConfigValue`；`dict` 新增 `GetDictTypeList/GetDictTypeOptions/GetDictTypeDetail/GetDictDataByType/GetDictDataList/GetDictDataDetail` 与对应 `DictType/DictData` ReadModel；`dept` 新增 `GetDeptEditOption/GetDeptList/GetDeptTreeSelect/GetDeptDetail` 与 `DeptItem/DeptTreeNode/DeptDetail` ReadModel；`menu` 新增 `GetMenuTree/GetRoleMenuTree/GetMenuList/GetMenuDetail` 与 `MenuItem/MenuTreeNode/RoleMenuTree` ReadModel；`post` 新增 `GetPostList/GetPostDetail` 与 `PostPage/PostDetail` ReadModel；`notice` 新增 `GetNoticeList/GetNoticeDetail` 与 `NoticePage/NoticeDetail` ReadModel；`role` 新增 `GetRoleDeptTree/GetRoleList/GetRoleDetail/GetRoleAllocatedUsers/GetRoleUnallocatedUsers` 与 `RoleDeptTree/RolePage/RoleDetail/RoleUserPage` ReadModel；`user` 新增 `GetUserDeptTree/GetUserList/GetUserProfile/GetUserDetail/GetUserAuthRole` 与 `UserPage/UserProfile/UserDetail/UserRoleResponse` ReadModel。新增 `modules/system/tests/test_config_read_queries.py`、`modules/system/tests/test_dict_read_queries.py`、`modules/system/tests/test_dept_read_queries.py`、`modules/system/tests/test_menu_read_queries.py`、`modules/system/tests/test_post_read_queries.py`、`modules/system/tests/test_notice_read_queries.py`、`modules/system/tests/test_role_read_queries.py`、`modules/system/tests/test_user_read_queries.py` 覆盖处理器与分发链路。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4_

- [x] 4. 引入 Mediator 并收敛控制器职责
  - 控制器只负责请求映射与分发器调用。
  - 写操作统一 `mediator.send(command)`。
  - 读操作统一 `mediator.query(query)`。
  - 本轮进展：`/system/config`、`/system/dict`、`/system/dept`、`/system/menu`、`/system/post`、`/system/notice`、`/system/role`、`/system/user` 读路径控制器已统一改为 `mediator.query(query)`，写路径保持 `mediator.send(command)`。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4_

- [x] 5. 落地 Pipeline 横切行为
  - 实现验证、鉴权/审计、事务、日志等管道。
  - 固化执行顺序并支持短路失败。
  - 记录命令类型、耗时、状态与 trace 关联。
  - 本轮进展：新增 `CommandValidationBehavior`、`CommandAuthAuditBehavior`、`CommandTransactionBehavior`、`CommandEventCollectionBehavior`、`CommandLoggingBehavior` 并注入 `Mediator` 默认写管道；新增 `QueryPerformanceBehavior` 作为默认读管道，输出查询耗时与慢查询证据。补充 `modules/system/tests/test_command_pipeline_behaviors.py`、`modules/system/tests/test_query_pipeline_behaviors.py`。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4_

- [x] 6. 完成读性能治理与跨上下文查询编排
  - 消除 N+1，采用 JOIN 或批量查询。
  - 实现 Composed Query 聚合查询能力。
  - 建立读性能回退监控与回滚策略。
  - 本轮进展：新增 `ComposedQueryExecutor`（并发分支 + 超时边界）并在 `GetRoleDeptTreeQueryHandler`、`GetUserDetailQueryHandler` 落地跨服务聚合查询；超时时自动降级为顺序查询回退，保证可用性。既有 Repository 继续复用 JOIN/批量查询实现，新增 `modules/system/tests/test_role_read_queries.py`、`modules/system/tests/test_user_read_queries.py` 的超时回退覆盖。
  _需求追溯: R5.AC1, R5.AC2, R5.AC3, R5.AC4_

- [x] 7. 执行一次性切换与验收
  - 移除旧式上帝 Service 入口，不保留并行逻辑。
  - 完成 Handler、管道、控制器端到端测试。
  - 校验 API 契约与性能基线。
  - 本轮进展：`config/dict/dept/post/role/user` 导出接口已改为先走 `mediator.query(...)` 获取读模型，再执行导出映射，移除导出场景下的旧列表查询入口；`dept/role/user` 写路径控制器业务校验已全部下沉到 CommandHandler。补齐历史控制器切换治理脚本并接入当时的 CI 门禁，阻断系统控制器回退直调业务 service。新增 `tests/integration/test_system_cqrs_cutover.py` 覆盖读链路契约、写链路与 Query/Command pipeline 的端到端验收。新增历史 CQRS 查询派发微基准脚本与 `baselines/cqrs-query-dispatch-benchmark-2026-02-22.json`，并在 `baselines/performance-baseline-2026-02-22.md` 归档可复验基线结果；相关脚本现已移除。
  _需求追溯: R6.AC1, R6.AC2, R6.AC3, R6.AC4_

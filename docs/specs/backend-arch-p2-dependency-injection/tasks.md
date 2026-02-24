# 依赖注入容器实现任务

> 范围调整（2026-02-21）：
> 本轮暂不处理仿真/协议/设备相关模块（`simulation`、`protocol`、`device*`），相关迁移任务与门禁清零要求顺延到后续里程碑。

- [x] 1. 建立应用级容器与组合根
  - 新增 `container/app_container.py` 与 `container/wiring.py`，定义核心 Provider。
  - 在应用启动阶段执行容器构建与绑定校验。
  - 启动失败时输出可定位错误并中断服务。
  _需求追溯: R1.AC1, R1.AC2, R1.AC3, R1.AC4_

- [x] 2. 全量改造 Service 为构造器注入（按本轮范围）
  - 将 `module_admin` 与 `module_generator` 服务改为实例方法，不保留业务 classmethod。
  - 服务依赖统一通过构造参数注入（Repository/Service/Infrastructure）。
  - 依赖类型统一改为 Protocol。
  - 本轮进展：`ProjectVersionService`、`ProjectTopologyService`、`ProjectService`、`LoginService`、`UserService`、`DeptService`、`ConfigService`、`CommonService`、`DictTypeService`、`DictDataService`、`JobService`、`JobLogService`、`OperationLogService`、`LoginLogService`、`GenTableService`、`GenTableColumnService`、`MenuService`、`PostService`、`NoticeService`、`RoleService` 已完成构造器注入改造；门禁统计业务 `@classmethod` 已从 213 降至 0（剩余模块按范围调整暂缓）。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R7.AC2_

- [x] 3. 统一 Repository 与会话生命周期装配（按本轮范围）
  - 将 Repository 创建收敛到容器工厂，禁止在业务逻辑中即时 new。
  - 与 `get_db()` 请求级会话对齐，确保单请求多仓储共享同一会话。
  - 本轮进展：`dept_service`、`config_service`、`user_service`、`common_service`、`dict_service`、`job_service`、`job_log_service`、`log_service`、`gen_service`、`menu_service`、`post_service`、`notice_service`、`role_service`、`project_service`、`login_service`、`audit_log_service` 已由容器注入/工厂依赖方式移除业务方法内即时 `new`；`log_annotation` 移除静态服务调用并改为容器解析，`scheduler_event_listener` 改为 task-scoped `AsyncSessionLocal` 持久化任务日志；门禁统计业务依赖即时实例化从 200 降至 15（全部位于暂缓的 `simulation` 模块）。
  - 为后台任务定义独立会话工厂。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4_

- [x] 4. 基础设施 Provider 单例化管理
  - 将 Redis/缓存/调度器注册为应用级 Provider。
  - 完成启动、关闭与异常路径治理。
  - 将 Provider 状态接入健康检查摘要。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4_

- [x] 5. 控制器注入方式统一为容器解析
  - 控制器统一使用 `Depends(Provide[Container.xxx])` 或等效容器封装。
  - 删除控制器层 `Service(query_db)` 直接实例化。
  - 启动阶段校验缺失绑定并提前失败。
  - 本轮进展：`module_admin` 与 `module_generator` 控制器已统一为 `Depends(service_provider(...))` 容器解析；静态业务调用（排除鉴权 `LoginService`）= `0`，`Service(query_db)` 直接实例化 = `0`。
  _需求追溯: R5.AC1, R5.AC2, R5.AC3, R5.AC4, R2.AC3_

- [x] 6. 建立测试覆盖与依赖替换机制
  - 在测试夹具中集成 `container.override()` 与 `reset_override()`。
  - 支持真实 DB + fake 外部依赖的混合模式。
  - 对覆盖失败场景提供清晰错误。
  _需求追溯: R6.AC1, R6.AC2, R6.AC3, R6.AC4_

- [x] 7. 建立防回退 CI 规则
  - 增加脚本检查新增 classmethod 业务服务。
  - 增加脚本检查业务方法内部实例化依赖。
  - 将规则接入 CI 强制门禁。
  _需求追溯: R7.AC2, R7.AC3, R7.AC4_

- [x] 8. 迁移收敛与验收
  - 按模块优先级完成全量切换并记录里程碑。
  - 完成注入链路回归、事务边界回归与性能基线对比。
  - 更新架构文档与容器依赖图。
  - 本轮进展：
    - 里程碑收敛：核心管理域（`user/dept/config/common/dict/job/log/menu/post/notice/role`）与 `module_generator` 注入改造已稳定；暂缓域（`simulation`、`protocol`、`device*`）维持独立 backlog。
    - 回归结果：`tests/unit/container` + `tests/unit/utils/test_transaction_manager.py` + 关键集成链路共 `76 passed`（`-n 0 --no-cov`）；事务边界测试 `14 passed`。
    - 性能基线：新增 `baselines/performance-baseline-2026-02-21.md`（容器构建/校验与服务解析开销快照）。
    - 文档归档：刷新 `container-graph.dot` / `container-graph.txt`，并同步更新 `design.md`、`acceptance-review.md`。
  _需求追溯: R7.AC1, R7.AC4, R1.AC3, R2.AC4, R3.AC2_

# 垂直切片与 DDD 模块边界实现任务

> 当前批次范围：`system/identity/project`；`simulation/protocol/device` 暂不纳入本轮收口。

- [x] 1. 创建 `modules/` 目标结构与上下文骨架
  - 创建 `identity/project/simulation/device/protocol/system/codegen/scheduler` 上下文目录。
  - 每个上下文初始化 `api/application/domain/infrastructure/ports.py/tests` 结构。
  - 固化目录模板与命名规则。
  _需求追溯: R1.AC1, R1.AC2, R2.AC1, R2.AC4_

- [x] 2. 构建显式模块注册表并替换手工路由注册
  - 新增 `modules/registry.py` 作为唯一模块声明入口。
  - 改造 `server.py` 仅通过 registry 加载路由与容器扩展。
  - 删除旧的手工 controller 列表注册方式。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4_

- [x] 3. 完成上下文边界切分与 ACL 映射
  - 将跨上下文共享实体拆为上下文视图模型。
  - 实现 ACL 转换层，禁止直接复用他上下文内部实体。
  - 跨上下文交互统一走 `ports.py`。
  - 本轮进展：`project` 上下文新增 `ProjectTopologyView` 与 ACL 映射；`simulation` 上下文新增 project-topology 端口适配器；`SimulationService` 在创建/重建会话时通过 `simulation.ports -> project.ports` 读取拓扑，不再直接复用对方内部实体数据结构。
  _需求追溯: R2.AC2, R2.AC3, R2.AC4_

- [x] 4. 共享内核收敛与治理
  - 将无业务语义公共能力沉淀到 `shared`。
  - 清理被错误放入 shared 的业务逻辑。
  - 建立 shared 变更影响测试清单与执行规则。
  - 本轮进展：新增 `shared/kernel` 并沉淀通用响应模型；移除 `module_admin/shared` 中业务语义错误码与冗余响应定义；补充 `shared-impact-test-matrix.md` 作为 shared 变更准入规则与最小回归清单。
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4_

- [x] 5. 拆分巨型文件并收敛上下文内聚
  - 对超大 service/repository 文件按子领域拆分。
  - 保证相关 API、应用服务、领域规则与仓储实现在同一上下文可定位。
  - 禁止新增横向分层目录下新业务代码。
  - 本轮进展：`simulation` 场景提取 `ACL + ports + adapter` 子模块，剥离跨上下文拓扑读取逻辑；补齐历史“横向分层目录新增业务文件”治理脚本与 baseline（脚本现已移除）。系统域完成 `config/dept/menu/notice/post/role/user/dict` 服务与仓储拆分迁移并删除旧文件；项目域完成 `project/project_topology/project_version` 服务与仓储迁移至 `modules/project`，并删除旧实现。
  _需求追溯: R1.AC3, R1.AC4, R6.AC2_

- [x] 6. 执行一次性迁移并删除旧结构
  - 按上下文完成旧路径到新路径映射迁移。
  - 迁移完成后删除旧目录对应实现（不保留并行实现）。
  - 修复全量 import 路径并确保构建通过。
  - 本轮进展：更新迁移映射表 `migration-map-2026-02-22.md`，完成 `system/identity/project` 全量 `service/repository/controller` 迁移到 `modules/*`；已删除 `module_admin/service/{config,dept,dict,menu,notice,post,role,user,audit_log,cache,captcha,common,log,login,online,server,project,project_topology,project_version}_service.py`、`module_admin/repository/{config,dept,dict,menu,notice,post,role,user,audit_log,common,log,login,project,project_topology,project_version}_repository.py`、`module_admin/controller/{config,dept,dict,menu,notice,post,role,user,audit,cache,captcha,common,log,login,online,resilience,server,project,project_version}_controller.py`；容器、注册表、测试导入与跨上下文 ports 入口已完成切换并通过回归。
  _需求追溯: R5.AC1, R5.AC2, R5.AC3, R5.AC4_

- [x] 7. 建立边界防回退与验收机制
  - 在 CI 增加跨上下文违规导入检查。
  - 增加目录归属检查与架构巡检报告。
  - 执行上下文级回归测试与权限回归。
  - 本轮进展：补齐历史模块边界治理脚本，校验 `modules/*` 跨上下文运行时导入仅允许经 `modules.<context>.ports`，并接入当时的 CI 门禁；目录归属门禁延续历史目录归属治理脚本（脚本现已移除）。更新巡检报告 `docs/specs/backend-arch-p3-vertical-slice-ddd/reports/module-boundary-report-2026-02-22.json`（`scanned_files=206, violations_count=0`）；已执行 `system/identity/project` 服务与集成回归及容器回归。
  _需求追溯: R6.AC1, R6.AC2, R6.AC3, R6.AC4_

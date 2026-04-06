# 统一数据库交付工作流 实现任务

> 注：当前仓库公开入口已收敛为 `scripts/db.py`，旧 `push` 兼容别名和独立种子脚本入口已移除。本文保留实现阶段的任务记录。

- [x] 1. 扩展统一数据库工作流配置与 CLI 骨架
  - 在 `ruoyi-fastapi-backend/config/env.py` 增加统一工作流配置项和状态字段，覆盖 `dev-sync / finalize / deploy / status / verify` 所需上下文
  - 在 `ruoyi-fastapi-backend/scripts/db.py` 中新增 `dev-sync`、`verify`、`status --format json`，并最终收敛旧 `push` 入口
  - 为 CLI 输出定义稳定字段，供 `scripts/start.sh`、Docker、CI 和排障脚本共享
  _需求追溯: R1.AC1, R1.AC2, R1.AC4, R6.AC1, R8.AC3_

- [x] 2. 抽离受管引用数据声明加载与统一校验层
  - 新建 `ManagedDataDeclarationLoader`，统一读取 `menus.registry.yaml`、字典/配置 YAML 与 `release-plan.yaml`
  - 明确第一阶段“受管引用数据”与 “bootstrap 初始化数据”边界，并形成统一错误模型
  - 复用现有 `menu_registry_loader.py` 校验能力，补齐字典、配置、release-plan 的一致性校验
  _需求追溯: R1.AC5, R2.AC4, R2.AC7, R5.AC1, R5.AC5, R7.AC4_

- [x] 3. 实现受管数据规划器与执行器核心
  - 新建 `ManagedDataPlanner`，支持 `upsert-row`、`delete-row`、`ensure-link`、`remove-link` 四类规范化操作
  - 新建 `ManagedDataApplier`，支持 `dry-run`、幂等执行、受管对象 prune 和失败前置
  - 将现有菜单 diff/reconcile 逻辑下沉复用，避免继续依赖运行时热同步直接写库
  _需求追溯: R1.AC2, R2.AC3, R4.AC7, R5.AC5, R6.AC3_

- [x] 4. 建立正式 bundle 产物结构和受管对象元数据
  - 新增 `ruoyi-fastapi-backend/db_artifacts/releases/<bundle_id>/` 目录结构与文件格式约定
  - 新增 `sys_db_workflow_artifact`、`sys_db_workflow_object` 两张元数据表及其 Alembic 迁移
  - 定义 `bundle.yaml`、`managed-data.yaml`、`release.manifest.yaml` 的 checksum 与幂等约束
  - 准备首个 baseline bundle 的生成策略或辅助脚本
  _需求追溯: R1.AC5, R3.AC3, R3.AC6, R3.AC7, R4.AC4, R5.AC4_

- [x] 5. 实现统一 `dev-sync` 编排与结构化报告
  - 按“声明校验 -> schema sync -> managed data apply -> 结果汇总”的顺序编排开发态同步
  - 在显式开发模式下继续允许破坏性 schema apply，并明确输出风险边界
  - 为成功、失败、跳过输出结构化报告，至少包含目标数据库、耗时、失败步骤和受影响对象
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC5, R2.AC6, R5.AC2, R6.AC2, R6.AC3, R8.AC1_

- [x] 6. 收敛开发启动链路并移除旁路生效机制
  - 修改 `scripts/start.sh`，启动前默认执行 `python scripts/db.py dev-sync` 或 `python scripts/db.py deploy --revision head`
  - 删除 `apply_sql_updates` 启动旁路，不再扫描 `sql/*.sql` 作为功能生效路径
  - 将 `DEV_MENU_SYNC` / `DevMenuSyncRuntime` 调整为弃用状态并从日常联调链路中移除
  - 保证启动前同步失败时阻断应用启动
  _需求追溯: R1.AC3, R2.AC4, R2.AC8, R4.AC3, R4.AC5, R7.AC3_

- [x] 7. 扩展 `finalize` 以同时正式化 schema、受管数据和发布可见性
  - 在 finalize 临时数据库上先应用正式 schema head 和历史 baseline bundle
  - 生成 Alembic migration、`managed-data.yaml` 和 `release.manifest.yaml`
  - 当 schema 或 data 无差异时返回 no-op，但仍输出明确结果
  - 根据 `release-plan.yaml` 将未获批准的菜单、权限、字典或配置排除在本次正式产物之外
  _需求追溯: R3.AC1, R3.AC2, R3.AC4, R3.AC5, R3.AC6, R3.AC7, R5.AC3, R8.AC2_

- [x] 8. 扩展 `deploy` 和 Docker 入口为顺序发布链路
  - 保持 `db.py deploy --revision head` 为唯一正式数据库升级入口
  - 在 `deploy` 中顺序执行 schema migration、managed-data bundle、release manifest，并在任一步失败时立即停止
  - 保证无 bundle 时以 no-op 方式通过，不破坏现有共享环境、预发、生产和客户升级链路
  - 记录 artifact history 并提供恢复指引，但不实现跨步骤全局自动回滚
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC6, R4.AC7, R5.AC4_

- [x] 9. 将 bootstrap seed 收缩为 bootstrap-only 并完成基线迁移
  - 把菜单、角色菜单、字典、系统配置相关逻辑从 bootstrap seed 中抽离到统一工作流
  - 为 bootstrap seed 增加 `bootstrap-only` 模式，只保留用户、部门、岗位、角色及其初始化关系
  - 明确新环境恢复顺序为“schema migration -> baseline bundles -> bootstrap seed”
  _需求追溯: R1.AC5, R4.AC2, R4.AC5, R8.AC2, R8.AC3_

- [ ] 10. 实现统一 `status / verify` 与 CI 治理门禁
  - 扩展 `status`，输出 schema、managed data、visibility 的 drift 状态、最近一次工作流结果和待正式化差异
  - 新增 `verify --ci`，统一校验 schema drift、声明合法性、bundle chain 和旁路入口
  - 将 `db.py verify` 逐步收敛为统一 verify 的 `schema-only` 适配层或内部调用
  - 在 CI / 发布脚本中接入统一校验，发现未正式化差异或旁路时直接失败
  _需求追溯: R6.AC1, R6.AC3, R6.AC4, R7.AC1, R7.AC2, R7.AC4_

- [ ] 11. 补齐测试、文档与渐进式切换计划
  - 为 CLI、loader、planner、applier、bundle、deploy 路径补齐单元测试、集成测试和回归测试
  - 编写迁移实施说明，明确旧命令边界、弃用窗口、baseline 执行方式和回退策略
  - 更新开发与部署文档，统一为 `dev-sync -> finalize -> deploy -> verify` 的团队心智
  _需求追溯: R4.AC5, R6.AC2, R7.AC3, R8.AC3_

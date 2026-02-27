# 开发态动态菜单热同步实现任务

## 任务列表

- [x] 1. 增加开发态开关与配置读取（后端/前端）
  - 后端在配置层新增 `DEV_MENU_SYNC` 与监听参数（如去抖时间），统一提供 `is_dev_menu_sync_enabled()` 判定函数。
  - 前端新增 `VITE_DEV_MENU_SYNC` 与轮询周期配置，默认关闭，开发环境按显式开关启用。
  - 保证开关关闭时完全沿用当前行为，不影响 `seed_data.py` 既有初始化逻辑。
  _需求追溯: R1.AC1, R5.AC1, R7.AC1_

- [x] 2. 为菜单表补充“声明管理范围”数据标记
  - 编写 Alembic 迁移，为 `sys_menu` 增加 `managed_by_seed` 字段和索引。
  - 更新 `MenuDO` 与相关序列化逻辑，确保字段可读写且默认值为 `0`。
  - 明确仅 `managed_by_seed=1` 进入自动 prune 范围。
  _需求追溯: R1.AC6, R2.AC4_

- [x] 3. 扩展 YAML 解析与目标态组装能力
  - 在 `menus.yaml`/`dev.yaml` 合并流程中支持解析 `managed_by_seed` 显式字段。
  - 统一生成“目标菜单快照”（按 `menu_id`）并输出新增/更新/删除候选集合。
  - 保持非声明管理范围菜单仅可读取或 upsert，不进入自动删除集合。
  _需求追溯: R1.AC2, R1.AC3, R1.AC6, R2.AC4_

- [x] 4. 实现声明式对账服务（事务 upsert + prune + 关系清理）
  - 新建 `DevMenuReconcileService`，提供 `sync_once(trigger, dry_run)` 能力。
  - 在单事务内执行：`sys_menu` upsert、声明范围 prune、`sys_role_menu` 失效关系清理。
  - 支持 `dry_run` 差异输出且不落库，并返回结构化 `SyncReport`。
  _需求追溯: R1.AC4, R2.AC1, R2.AC2, R6.AC1, R6.AC3_

- [x] 5. 接入开发态运行时：启动同步 + 文件监听同步
  - 新建 `DevMenuSyncRuntime`，在应用 `lifespan` 启动后先执行一次同步。
  - 监听 `scripts/seed_data/base/menus.yaml` 与 `scripts/seed_data/overlays/dev.yaml` 变更并触发同步（含去抖与串行锁）。
  - 同步失败仅记录并保留服务可用，等待下一次触发自动重试。
  _需求追溯: R1.AC5, R6.AC4, R7.AC2_

- [x] 6. 完成缓存失效与可观测日志闭环
  - 同步成功后按模式失效 `query_cache:menu:*`、`query_cache:role:*`，避免手工清 Redis。
  - 记录结构化同步日志（新增/更新/删除/耗时/触发来源/结果）。
  - 为失败场景记录可检索错误日志（包含异常摘要与下次重试条件）。
  _需求追溯: R6.AC1, R6.AC4_

- [x] 7. 实现授权签名服务与开发态接口
  - 新建 `DevMenuSignatureService`，基于用户角色、角色菜单、有效菜单生成确定性签名（sha256）。
  - 新增 `GET /dev/menu/signature`（登录态）与 `POST /dev/menu/sync`（管理员 + 支持 dry-run）。
  - 接口在非开发环境或开关关闭时返回不可用并输出告警日志。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R5.AC3, R6.AC3_

- [x] 8. 在后端路由注册中接入开发态控制器
  - 按现有模块注册方式将 `dev_menu_sync_controller` 挂载到 system 模块。
  - 确保 dev 接口不影响现有 `/getRouters` 与系统管理 API 路由行为。
  - 增加最小化鉴权与开关守卫逻辑，避免生产误暴露。
  _需求追溯: R5.AC1, R5.AC2, R5.AC3_

- [x] 9. 新增前端开发态签名轮询插件
  - 新建 `dev-menu-hot-sync` 插件，在 `import.meta.env.DEV && VITE_DEV_MENU_SYNC=1` 时启动。
  - 轮询周期默认 `2000ms`，签名不变则跳过后续逻辑，以满足 3 秒内可见目标。
  - 签名接口失败时不破坏当前路由，按下一轮周期重试。
  _需求追溯: R3.AC2, R3.AC3, R3.AC4, R5.AC1_

- [x] 10. 扩展 permission store：无重登重建动态路由
  - 增加 `reloadDynamicRoutes()`：移除旧动态路由、重新拉取 `/getRouters`、重新注册路由。
  - 当当前路由已失效时自动跳转 `firstMenuPath`，保证删除菜单后的平滑降级。
  - 记录热更新触发原因（签名变化）与执行结果日志。
  _需求追溯: R2.AC3, R3.AC1, R4.AC4, R6.AC2_

- [x] 11. 后端测试：对账、签名、环境隔离、失败恢复
  - 单元测试覆盖：差异计算、事务回滚、dry-run、签名稳定性与变更敏感性。
  - 集成测试覆盖：启动同步、文件变更同步、删除联动清理、非 dev 环境禁用。
  - 增加生产误配置保护测试，验证拒绝破坏性同步并输出告警。
  _需求追溯: R1.AC2, R1.AC3, R1.AC4, R2.AC1, R2.AC2, R4.AC2, R4.AC3, R5.AC1, R5.AC3, R6.AC3, R6.AC4, R7.AC2_

- [x] 12. 前端测试：轮询策略与路由热更新行为
  - Vitest 覆盖：签名变化触发重建、签名不变不重建、请求失败重试。
  - 覆盖删除当前菜单后的自动跳转与重建失败保持现状。
  - 覆盖开发开关关闭时不启动轮询。
  _需求追溯: R2.AC3, R3.AC1, R3.AC2, R3.AC3, R4.AC4, R5.AC1, R6.AC2_

- [x] 13. 文档与回退策略落地
  - 更新开发文档与 FAQ，说明“新增/删除菜单无需重登”的标准流程。
  - 在 `start.sh`/README 中补充开关开启方式与关闭回退方式。
  - 明确该能力为开发态优化，不改变生产链路与发布流程。
  _需求追溯: R3.AC4, R5.AC2, R7.AC3_

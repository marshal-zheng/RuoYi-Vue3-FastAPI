# 开发态菜单单一事实源实现任务

- [x] 1. 建立单一声明源文件与基础约束
  - 新建 `ruoyi-fastapi-backend/scripts/seed_data/menus.registry.yaml`，定义 `version/menus/role_grants` 顶层结构。
  - 在仓库文档中将菜单来源说明收敛为 `menus.registry.yaml`，移除“开发者需同时改多个 YAML”的指引。
  - 明确授权声明字段采用 `role_key`，禁止在声明模型中要求 `role_id`。
  _需求追溯: R1.AC1, R1.AC2, R1.AC5, R7.AC5_

- [x] 2. 实现 MenuRegistryLoader 与强校验能力
  - 新增 `menu_registry_loader.py`，提供 registry 解析、标准化与目标态构建能力。
  - 实现校验规则：重复 `menu_id`、父子关系/循环依赖、字段类型、组件路径格式、角色授权结构合法性。
  - 接入角色存在性校验：`role_key` 必须在系统角色集合中可解析，缺失时输出可定位错误。
  - 编写对应单元测试覆盖合法与非法输入。
  _需求追溯: R1.AC2, R1.AC4, R6.AC2, R6.AC6_

- [x] 3. 完成历史配置迁移并退场（legacy -> registry）
  - 迁移期已完成 `base/menus.yaml + overlays/* role_menus` 到 `menus.registry.yaml` 的一次性收敛。
  - 迁移报告与映射校验已完成，稳态后移除迁移命令入口，避免回流。
  - 保留 CI 防回流校验，持续阻断旧入口定义复活。
  _需求追溯: R7.AC1, R7.AC2, R7.AC6_

- [x] 4. 重构 DevMenuReconcileService 为 registry 驱动
  - 将同步输入源切换到 `menus.registry.yaml`，按目标态执行 `sys_menu` 新增/更新/删除。
  - 保持 `managed_by_seed=1` 受管边界，仅对受管菜单执行破坏性操作。
  - 对受管菜单授权执行 `sys_role_menu` 全量声明对齐（含未声明残留删除）。
  - 保留 `dry-run` 差异输出能力，确保 `dry-run` 不写库。
  - 强化事务语义：失败全量回滚、成功显式提交并失效 `menu/role` 相关缓存。
  - 增加结构化同步结果输出（新增/更新/删除/授权变更/耗时/触发来源）。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R3.AC3, R6.AC3, R6.AC4_

- [x] 5. 重构 SeedDataManager 为 registry 单一来源
  - 将 `seed_entity('menus')` 与 `seed_role_menus()` 的数据来源统一到 `MenuRegistryLoader`。
  - 执行期将 `role_key` 映射为 `role_id` 入库，未知 `role_key` 直接失败并返回错误详情。
  - 确保 dev/prod 共享同一菜单与授权声明来源，避免环境间定义漂移。
  _需求追溯: R1.AC2, R1.AC5, R5.AC2, R7.AC3_

- [x] 6. 调整开发态运行时开关与监听链路
  - `DevMenuSyncRuntime` 的 `watch_paths` 收敛为 `menus.registry.yaml`。
  - 保持启动即同步 + 文件变更同步行为，仅在 `APP_ENV=dev && DEV_MENU_SYNC=true` 生效。
  - 非开发环境误开开关时拒绝执行破坏性同步并输出告警。
  - 保证关闭开关即可回退到旧行为（无开发态热同步链路）。
  _需求追溯: R4.AC1, R5.AC1, R5.AC3, R5.AC4_

- [x] 7. 固化授权一致性语义（不自动授予）
  - 明确同步与种子流程中不引入“新增菜单自动授予角色”逻辑。
  - 通过测试验证：admin 账号因管理员权限可见新增菜单；非管理员账号无授权时不可见。
  - 验证非管理员展示严格受最终授权结果控制。
  _需求追溯: R3.AC1, R3.AC2, R3.AC4_

- [x] 8. 验证前端无重登热更新体验
  - 保持 `/dev/menu/signature` 轮询与签名变更触发 `reloadDynamicRoutes()` 机制。
  - 补充测试覆盖“当前路由失效后自动跳转首个可访问菜单”。
  - 增加开发态性能验收：菜单声明保存后 3 秒内前端可见变化。
  _需求追溯: R4.AC2, R4.AC3, R4.AC4_

- [x] 9. 交付脚手架命令（新增/删除菜单）
  - 新增 `scripts/menu_registry_tool.py add`：默认自动分配不冲突 `menu_id`，支持显式 `--menu-id` 覆盖并做冲突校验。
  - 新增 `scripts/menu_registry_tool.py remove --menu-id --cascade`：删除菜单并同步维护声明内授权关系。
  - 输出命令执行摘要，便于开发者快速确认变更。
  _需求追溯: R1.AC3, R6.AC1, R6.AC7_

- [x] 10. 交付本地校验器与 CI 防回流规则
  - 新增 `scripts/check_menu_registry.py --strict`，统一执行语法、语义、角色映射、旧入口回流检查。
  - 在 `.github/workflows/ci.yml` 与 `.gitlab-ci.yml` 接入 `menu-registry-check`。
  - 校验失败时阻断合并，禁止新增“多入口菜单定义”与稳态后旧入口回流。
  _需求追溯: R1.AC4, R6.AC5, R7.AC4, R7.AC7_

- [x] 11. 完成稳态收敛与旧入口退场
  - 在迁移完成后移除 `base/menus.yaml` 与 `overlays/*` 的菜单授权来源职责。
  - 调整运行时与 seed 读取逻辑，不再从旧入口读取菜单/授权定义。
  - 更新 FAQ/README/脚本说明，统一开发者入口为 `menus.registry.yaml`。
  _需求追溯: R1.AC1, R7.AC3, R7.AC7_

- [x] 12. 执行端到端验收与回退演练
  - 覆盖开发态新增/修改/删除菜单联调：数据库对齐、侧栏可见性、路由可达性。
  - 覆盖手动同步与 `dry-run` 验证：差异报告完整且 `dry-run` 无写库。
  - 覆盖回退演练：关闭开发态开关后系统恢复旧行为，生产模式链路不受影响。
  _需求追溯: R2.AC4, R5.AC2, R5.AC3, R6.AC3, R6.AC4_

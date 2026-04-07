# 开发态受管数据近实时热对齐实现任务

- [x] 1. 建立开发态热对齐运行时底座与开关边界
  - 在 `ruoyi-fastapi-backend/config/env.py` 中新增开发态热对齐配置项，覆盖 watcher、防抖、SSE heartbeat 和启停开关。
  - 在 `ruoyi-fastapi-backend/server.py` 的 `lifespan()` 中按 `APP_ENV=dev && DB_WORKFLOW_MODE=development` 条件初始化运行时，并将状态对象挂到 `app.state`。
  - 新增运行时快照与状态模型，支持模块目录扫描、文件新增/删除感知、最近一次成功状态记录与串行执行锁。
  - 明确非开发态、非 development 工作流下不注册 watcher、不暴露事件接口，保持现有正式链路边界。
  _需求追溯: R1.AC1, R1.AC2, R1.AC5, R4.AC3, R6.AC3_

- [x] 2. 抽取并实现受管数据快路径同步服务
  - 从 `scripts/internal/db_workflow/dev_sync_service.py` 中抽取可复用的声明加载、`compiled_checksum` 计算、managed-data apply、metadata 同步和 postcondition verify 逻辑。
  - 新增 `ManagedDataFastReconcileService`，只处理 capability 受管数据，不触发 Atlas schema apply。
  - 在快路径中实现“两级跳过”策略：目录快照无变化不编译，`compiled_checksum` 无变化不写库也不发事件。
  - 保持事务回滚、非受管对象保护、显式 CLI `python scripts/db.py dev-sync` 兜底入口不变，避免运行时和 CLI 语义分叉。
  _需求追溯: R1.AC3, R1.AC4, R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R4.AC1, R4.AC4, R4.AC5_

- [x] 3. 实现开发态 SSE 事件代理与后端调试接口
  - 在 `modules/system/api/dev_menu_sync_controller.py` 中新增 `GET /dev/menu/events`，返回开发态 `SSE` 长连接事件流。
  - 新增 `DevMenuEventBroker`，负责订阅管理、`ready/menu_changed/heartbeat` 事件广播与断连清理。
  - 保留 `GET /dev/menu/signature` 作为兜底检查接口，并将 `POST /dev/menu/sync` 改为复用新的快路径同步服务。
  - 确保 dev-only 路由注册逻辑继续受 `modules/registry.py` 控制，非开发态或未启用时返回 `404`。
  _需求追溯: R3.AC1, R3.AC5, R4.AC2, R5.AC1, R6.AC3_

- [x] 4. 重构前端热更新插件为 EventSource 主路径
  - 基于 `ruoyi-fastapi-frontend/src/plugins/dev-menu-hot-sync.ts` 改造为 `EventSource('/dev/menu/events')` 单连接订阅模式。
  - 收到 `menu_changed` 事件后立即调用 `permissionStore.reloadDynamicRoutes('sse_menu_changed')`，并复用现有“无权限路由自动跳转首个菜单”逻辑。
  - 为 `SSE` 断线场景实现指数退避重连；持续失败后才降级到低频签名检查或 `window.__DEV_MENU_SYNC__.refreshRoutes()` 手动刷新。
  - 调整前端配置逻辑，停止把高频 polling 作为默认主路径，同时保持调试 API 和 404 静默退出能力。
  _需求追溯: R3.AC2, R3.AC3, R3.AC4, R3.AC5, R4.AC2_

- [x] 5. 收敛日志与性能守护策略
  - 在请求日志中间件中加入 `/dev/menu/events` 排除能力，避免 `SSE` 长连接与 heartbeat 淹没正常调试日志。
  - 为自动热对齐输出单条结构化摘要日志，只包含触发来源、耗时、成功状态、变更计数和错误信息。
  - 将对象级 diff、checksum 对比、详细 reconcile 清单降为 debug 级别输出。
  - 保证空闲状态不发生周期性数据库写入、全量 `dev-sync` 或全量动态路由重建，满足近实时且低噪音的开发体验目标。
  _需求追溯: R4.AC1, R4.AC4, R5.AC1, R5.AC2, R5.AC3, R5.AC4, R5.AC5_

- [x] 6. 保持统一工作流与正式发布链路不变
  - 保留 `scripts/start.sh` 的启动前统一 `dev-sync` 语义，避免首次启动时数据库与声明不一致。
  - 明确开发态热对齐只作为运行时体验增强，不写入正式 release artifact，也不改变 `finalize/deploy/verify` 的输入输出契约。
  - 更新开发与工作流文档，统一说明“启动前全量 dev-sync + 运行时 managed-data fast path + 正式 finalize/deploy”的团队心智。
  - 处理 legacy `DEV_MENU_SYNC` / `VITE_DEV_MENU_SYNC` 兼容说明，避免旧开关与新运行时并存导致误解。
  _需求追溯: R6.AC1, R6.AC2, R6.AC4_

- [x] 7. 补齐端到端测试、回归和人工验证闭环
  - 为目录扫描、防抖合并、checksum 跳过、快路径事务回滚、`SSE` 事件广播、请求日志排除分别补齐后端单元测试。
  - 为修改 `*.module.yaml` 后自动热对齐、前端自动重载路由、404 降级、手动 `POST /dev/menu/sync` 兜底补齐前后端集成测试。
  - 为正式链路补跑回归，证明 `python scripts/db.py dev-sync/finalize/deploy --revision head/verify --ci` 仍保持现有行为。
  - 编写最小化真实开发验证步骤，覆盖“新增菜单 1 秒内出现、删除菜单 1 秒内消失、日志不被 `/dev/menu/events` 刷屏”三类信号。
  _需求追溯: R1.AC2, R2.AC5, R3.AC4, R4.AC5, R5.AC4, R6.AC1, R6.AC2, R6.AC4_

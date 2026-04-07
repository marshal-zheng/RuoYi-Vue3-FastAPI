# Dev Managed Data Hot Reconcile Runbook

## 适用范围

- 功能：开发态受管数据热对齐
- 版本：Task 7 验收基线
- 适用环境：`APP_ENV=dev` 且 `DB_WORKFLOW_MODE=development`

## 标准心智

1. 启动前：`./scripts/start.sh` 会先执行统一 `dev-sync`
2. 运行时：保存 `capabilities/modules/*.module.yaml` 后，后端执行 managed-data fast reconcile，前端通过 `SSE` 自动刷新路由
3. 正式发布：仍然只走 `python scripts/db.py finalize` -> `python scripts/db.py deploy --revision head`

## 自动化回归

首选入口：

```bash
./scripts/verify-dev-menu-hot-sync.sh
```

该脚本现在作为单一事实源，统一覆盖：

- capability/module 主链 e2e：`*.module.yaml -> ManagedDataFastReconcileService -> DevMenuEventBroker -> signature`
- 后端快路径核心回归：环境开关、请求日志降噪、runtime/watcher、SSE broker、controller、工作流边界
- 前端主链回归：`devMenuSync` 配置、permission store 热重载、SSE 主路径与 fallback

如需拆分调试，直接查看 [`scripts/verify-dev-menu-hot-sync.sh`](/Users/hqz/dev/RuoYi-Vue3-FastAPI/scripts/verify-dev-menu-hot-sync.sh) 中维护的测试文件清单。

## 最小人工验证

### 0. 启动

```bash
./scripts/start.sh
```

确认信号：

- 启动日志里出现“启动前统一 dev-sync 执行完成”
- 后端日志里出现“开发态受管数据热对齐运行时已启用”
- 浏览器登录后，Network 中可以看到 `GET /dev/menu/events` 保持连接

### 1. 新增菜单 1 秒内出现

1. 选择一个开发模块文件，例如 `ruoyi-fastapi-backend/capabilities/modules/platform.module.yaml`
2. 新增一个开发菜单，并把该菜单授权给当前登录角色
3. 保存文件

预期：

- 1 秒内侧边栏出现新菜单
- 后端日志出现一条 `dev_managed_data_hot_reconcile`
- 不应看到 `/dev/menu/events` 被 heartbeat 请求日志刷屏

### 2. 删除菜单 1 秒内消失

1. 在同一个 `*.module.yaml` 中删除上一步新增的菜单与对应授权
2. 保存文件

预期：

- 1 秒内侧边栏移除该菜单
- 后端日志再次出现一条 `dev_managed_data_hot_reconcile`
- 刷新页面后菜单仍保持删除后的状态

### 3. 手动兜底

当 `SSE` 被本地代理或浏览器插件打断时：

```bash
curl -X POST http://127.0.0.1:9099/dev/menu/sync \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"trigger":"manual","dryRun":false}'
```

或在浏览器控制台执行：

```js
window.__DEV_MENU_SYNC__.refreshRoutes()
```

预期：

- 接口返回 200
- 当前页面动态路由刷新成功
- 手动同步失败时，后端保留 error 级别日志

## 正式链路回归

以下命令的语义必须保持不变：

```bash
cd ruoyi-fastapi-backend
python scripts/db.py dev-sync
python scripts/db.py finalize --message "check hot reconcile boundary"
python scripts/db.py deploy --revision head
python scripts/db.py verify --ci
```

验收关注点：

- `dev-sync` 只在 `DB_WORKFLOW_MODE=development` 可用
- `finalize` 继续生成正式 revision / bundle，不读取运行时热对齐状态
- `deploy` 继续只消费正式 release bundle
- `verify --ci` 继续校验声明、bundle 链、bypass 入口和 drift 状态

## 回退

- 临时关闭运行时热对齐：`DEV_MANAGED_DATA_HOT_RECONCILE_ENABLED=false`
- 如直接运行前端 `yarn dev`，可追加：`VITE_DEV_MENU_SYNC=0`
- 正式环境不需要任何回退动作，因为本能力默认不参与正式 `finalize / deploy`

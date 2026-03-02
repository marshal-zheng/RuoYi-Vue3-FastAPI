# Q: 开发模式新增/删除菜单后为什么会 404？现在应该怎么做？

## 结论（当前标准流程）
- 开发模式下已经支持菜单声明式热同步，不需要再「退出登录再登录」。
- 菜单与授权只维护在 `ruoyi-fastapi-backend/scripts/seed_data/menus.registry.yaml`。

## 生效条件
- 后端（`ruoyi-fastapi-backend/.env.dev`）：
  - `APP_ENV=dev`
  - `DEV_MENU_SYNC=true`
- 前端（`ruoyi-fastapi-frontend/.env.development`）：
  - `VITE_DEV_MENU_SYNC='1'`
  - `VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS='1000'`（默认 1 秒轮询）

## 正确用法
1. 在 `ruoyi-fastapi-backend/scripts/seed_data/menus.registry.yaml` 新增/修改/删除菜单。
2. 授权在同一文件的 `role_grants` 中声明，角色标识使用 `role_key`（不是 `role_id`）。
3. 菜单条目必须声明 `managed_by_seed: true`。
4. 菜单 `component` 必须与前端组件路径匹配（例如 `system/user/index` 对应 `src/views/system/user/index.vue`）。
5. 保存后等待一个轮询周期（通常 1~3 秒），侧栏与路由会自动重建。

## 机制说明（为什么不再需要重登）
- 后端监听 `menus.registry.yaml` 变更，执行事务同步：
  - `sys_menu` 声明式对齐（新增/更新/删除）
  - 仅对 `managed_by_seed=1` 范围执行破坏性操作
  - `sys_role_menu` 对受管菜单执行全量声明对齐（未声明即删除）
  - 失效 `query_cache:menu:*`、`query_cache:role:*`
- 前端轮询 `/dev/menu/signature`，签名变化时自动 `reloadDynamicRoutes()`。

## 排查清单（仍出现 404 时）
1. 调试接口是否可用：`GET /dev/menu/signature`（开发态开启时应返回 200）。
2. 查看后端日志是否有 `Dev menu sync failed`。
3. 执行校验：`cd ruoyi-fastapi-backend && python scripts/check_menu_registry.py --strict`。
4. 检查 `component` 路径是否与 `src/views` 实际文件一致。
5. 确认前端轮询开关未关闭（`VITE_DEV_MENU_SYNC='1'`）。

## 回退方式（不影响生产）
- 仅开发态启用该能力，生产态默认不启用。
- 如需回退旧行为，只需关闭开关：
  - 后端：`DEV_MENU_SYNC=false`
  - 前端：`VITE_DEV_MENU_SYNC='0'`

# Q: 开发模式新增/删除菜单后为什么会 404？现在应该怎么做？

## 结论（当前标准流程）
- 开发模式下已经支持菜单声明式热同步，不需要再「退出登录再登录」。
- 只要按规范修改种子文件，菜单新增/删除会自动同步数据库并触发前端动态路由热重建。

## 生效条件
- 后端（`ruoyi-fastapi-backend/.env.dev`）：
  - `APP_ENV=dev`
  - `DEV_MENU_SYNC=true`
- 前端（`ruoyi-fastapi-frontend/.env.development`）：
  - `VITE_DEV_MENU_SYNC='1'`
  - `VITE_DEV_MENU_SYNC_POLL_INTERVAL_MS='1000'`（默认 1 秒轮询）

## 正确用法
1. 在 `ruoyi-fastapi-backend/scripts/seed_data/base/menus.yaml` 新增或删除菜单。
2. 菜单条目必须显式声明：`managed_by_seed: true`。
3. 菜单 `component` 必须与前端组件路径匹配（例如 `system/user/index` 对应 `src/views/system/user/index.vue`）。
4. 保存文件后等待一个轮询周期（通常 1~3 秒）：
   - 新菜单应自动显示并可访问。
   - 删除菜单应自动从侧栏消失，当前页若失效会自动跳转到第一个可访问菜单。

## 机制说明（为什么不再需要重登）
- 后端监听 `menus.yaml/dev.yaml` 变更，执行事务同步：
  - `sys_menu` upsert
  - `managed_by_seed=1` 范围内 prune
  - 清理 `sys_role_menu` 失效关系
  - 失效 `query_cache:menu:*`、`query_cache:role:*`
- 前端轮询 `/dev/menu/signature`，签名变化时自动 `reloadDynamicRoutes()`，无登出重建路由。

## 排查清单（仍出现 404 时）
1. 调试接口是否可用：`GET /dev/menu/signature`（开发态开启时应返回 200）。
2. 查看后端日志是否有 `Dev menu sync failed`。
3. 检查新增菜单是否写了 `managed_by_seed: true`。
4. 检查 `component` 路径是否与 `src/views` 实际文件一致。
5. 确认前端轮询开关未关闭（`VITE_DEV_MENU_SYNC='1'`）。

## 回退方式（不影响生产）
- 仅开发态优化，生产态默认不启用。
- 如需回退旧行为，只需关闭开关：
  - 后端：`DEV_MENU_SYNC=false`
  - 前端：`VITE_DEV_MENU_SYNC='0'`

# Q: 开发模式新增/删除菜单后为什么会 404？现在应该怎么做？

## 结论（当前标准流程）
- 开发模式下已经支持基于模块声明的受管数据热对齐，不需要再「退出登录再登录」。
- 菜单与授权只维护在 `ruoyi-fastapi-backend/capabilities/modules/*.module.yaml`。
- 标准心智是“启动前全量 `dev-sync`，启动后开发态热对齐，正式发布仍走 `finalize -> deploy`”。

## 生效条件
- 后端（`ruoyi-fastapi-backend/.env.dev`）：
  - `APP_ENV=dev`
  - `DB_WORKFLOW_MODE=development`
  - `DEV_MANAGED_DATA_HOT_RECONCILE_ENABLED=true`（默认值）
- 前端：
  - 开发环境默认会尝试连接 `SSE`，无需额外开关
  - `VITE_DEV_MENU_SYNC='0'` 只保留为直接运行 `yarn dev` 时的兼容禁用开关

## 正确用法
1. 通过 `./scripts/start.sh` 启动项目；若当前是 `DB_WORKFLOW_MODE=development`，脚本会先执行一次统一 `dev-sync`。
2. 在 `ruoyi-fastapi-backend/capabilities/modules/*.module.yaml` 新增/修改/删除菜单，并在同文件维护 `role_grants`。
3. 角色授权声明使用 `role_key`，菜单 `component` 必须与前端组件路径匹配（例如 `system/user/index` 对应 `src/views/system/user/index.vue`）。
4. 保存后等待约 1 秒；后端会感知模块声明变化，前端会通过 `SSE` 自动刷新动态路由。
5. 如果需要手动兜底，可调用 `POST /dev/menu/sync` 或在浏览器执行 `window.__DEV_MENU_SYNC__.refreshRoutes()`。

## 机制说明（为什么不再需要重登）
- `./scripts/start.sh` 会先执行统一工作流入口，确保应用启动前数据库已经和 capability 声明对齐。
- 后端启动后监听 `capabilities/modules/*.module.yaml` 变更，执行开发态 managed-data fast reconcile：
  - `sys_menu`、`sys_role_menu`、字典和配置按声明目标态快速对齐
  - 失效菜单、角色、字典和配置相关缓存
  - 成功时广播 `/dev/menu/events` 的 `menu_changed` 事件
- 前端优先使用 `SSE` 自动刷新；只有持续重连失败时，才退化到低频签名检查。

## 排查清单（仍出现 404 时）
1. 确认 `APP_ENV=dev` 且 `DB_WORKFLOW_MODE=development`，并且 `./scripts/start.sh` 启动时没有在 `dev-sync` 阶段失败。
2. 调试接口是否可用：`GET /dev/menu/events` 或 `GET /dev/menu/signature`（开发态开启时应返回 200）。
3. 查看后端日志是否有 `dev_managed_data_hot_reconcile` summary，或手动同步失败日志。
4. 执行校验：`cd ruoyi-fastapi-backend && python scripts/menu.py check`。
5. 必要时执行工作流校验：`cd ruoyi-fastapi-backend && python scripts/db.py verify --ci`。
6. 检查 `component` 路径是否与 `src/views` 实际文件一致。
7. 如直接运行前端 `yarn dev`，确认没有把 `VITE_DEV_MENU_SYNC='0'` 留在本地环境中。

## 回退方式（不影响生产）
- 仅开发态启用该能力，生产态和正式发布链路不受影响。
- 如需临时关闭运行时热对齐：
  - 后端：`DEV_MANAGED_DATA_HOT_RECONCILE_ENABLED=false`
  - 如直接运行前端 `yarn dev`，可额外设 `VITE_DEV_MENU_SYNC='0'`

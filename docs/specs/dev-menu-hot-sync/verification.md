# 开发态动态菜单热同步验收记录

更新日期：2026-02-27

## 自动化验证

推荐使用一键命令：
```bash
./scripts/verify-dev-menu-hot-sync.sh
```

### 后端专项
```bash
./ruoyi-fastapi-backend/venv/bin/pytest \
  ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_hot_sync_e2e.py \
  ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_sync_runtime.py \
  ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_reconcile_service.py \
  ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_signature_service.py \
  ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_sync_controller.py \
  ruoyi-fastapi-backend/tests/test_menu_seed_scope.py \
  ruoyi-fastapi-backend/tests/unit/modules/test_registry.py \
  -q --no-cov
```
结果：`24 passed`

覆盖点：
- 开关守卫（仅 dev + 开关开启）
- 启动同步与文件变更触发
- `dry_run` 不落库
- 事务异常回滚
- 删除联动 `sys_role_menu` 清理
- 授权签名稳定性与变化敏感性
- 开发态 API 鉴权与环境隔离
- 端到端链路：YAML 变更 -> 菜单收敛 -> 关系清理 -> 签名变化
- 路由注册隔离：非 dev 或开关关闭时不注册 `/dev/menu/*`

### 前端专项
```bash
cd ruoyi-fastapi-frontend
yarn test:run \
  tests/unit/config/devMenuSync.test.ts \
  tests/unit/stores/permission.test.ts \
  tests/unit/plugins/devMenuHotSync.test.ts
```
结果：`3 files, 10 tests passed`

覆盖点：
- 开关关闭不启动轮询
- 签名变化触发热重建，签名不变不重建
- 请求失败下周期重试
- 未登录不轮询签名接口
- 当前路由失效自动降级到 `firstMenuPath`
- 无 `name` 的动态路由也能通过 remover callback 清理

## 手工联调清单（开发模式）

前置条件：
- 后端：`APP_ENV=dev`、`DEV_MENU_SYNC=true`
- 前端：`VITE_DEV_MENU_SYNC='1'`
- 菜单条目显式声明：`managed_by_seed: true`

### 1. 新增菜单可见性
1. 在 `ruoyi-fastapi-backend/scripts/seed_data/base/menus.yaml` 新增菜单。
2. 保存后观察后端日志，确认出现 `Dev menu sync report` 且 `success=true`。
3. 前端等待一个轮询周期（默认 1 秒）。
4. 验证侧边栏出现新菜单，点击可访问无 404。

### 2. 删除菜单收敛
1. 从 `menus.yaml` 删除同一菜单。
2. 观察后端日志，确认 `deleted > 0` 且 `role_menu_deleted >= 0`。
3. 前端轮询后侧边栏应移除该菜单。
4. 若当前正在该菜单页面，应自动跳转到首个可访问菜单。

### 3. 数据库与缓存检查
可选 SQL：
```sql
SELECT menu_id, menu_name, managed_by_seed FROM sys_menu WHERE menu_id IN (...);
SELECT role_id, menu_id FROM sys_role_menu WHERE menu_id IN (...);
```

预期：
- 新增后 `sys_menu` 存在、删除后不存在。
- 删除后 `sys_role_menu` 不再有对应 `menu_id` 关系。
- 无需手工清 Redis 缓存。

## 回退策略
仅开发态生效；需要回退时关闭开关即可：
- 后端：`DEV_MENU_SYNC=false`
- 前端：`VITE_DEV_MENU_SYNC='0'`

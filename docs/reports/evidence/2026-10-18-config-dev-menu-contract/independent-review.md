# Config refresh / dev-menu 当前响应契约独立复审

**BASE_SHA:** `c65cddfde6d0f24640d00f2eed38f83ac38fd926`。

**候选:** 项目本地 `.worktrees/config-dev-menu-contract`，实际 tracked 差量仅两个测试文件，生产/前端/生成产物无 diff。

- `ruoyi-fastapi-backend/modules/system/tests/test_config_refresh_command.py` SHA256: `d32b473bd2c0172d827c6e34f07e897e79a881fda7cd2fb26e69bbcf32e5467e`
- `ruoyi-fastapi-backend/modules/system/tests/test_dev_menu_sync_controller.py` SHA256: `98dd68603c2be99c43d94983baf3f88f6f6925a47586d8fb891d3f6850571260`

**结论：PASS；P0=0 / P1=0 / P2=0。RERUN 通过，可按当前范围继续精确交付与源验证。** 本报告只针对上述 hash，不表示未提交候选已经交付。

## 实现与真实消费核对

已阅读 `RefreshConfigCacheCommandHandler.handle`、config controller、dev-menu signature/status/sync controller、`ResponseUtil.ok_resource`，并核对前端 `devMenuSync.ts` 及 `dev-menu-hot-sync.ts`：

- refresh handler 调用传入 Redis 对应的 config service，返回成功 command result，`status='refreshed'`、`data={}`，同时发 `system.config.cache_refreshed` 事件。config HTTP controller 本来就返回顶层 `{'status':'refreshed'}`；日志消息 fallback 不等于业务结果必须保留 `data.message`。
- `ok_resource` 对普通资源映射直接序列化为 JSON，没有 data envelope。dev-menu 三个资源端点已按该能力返回 signature/status/reconcile 字段；前端实际读取 `payload.signature`。测试直接读取 JSON 顶层，与实现和消费者一致。

本候选没有修改生产实现，没有恢复 message/data 兼容包装，没有引入探针或其他产品入口。独立重算 7 个相关实现/消费文件：实际 source、候选和 HEAD 字节全部相等，因此没有借 source dirty 实现让候选通过。

## 断言没有弱化

两个 refresh 断言从错误的 `data.message` 改为精确 `data == {}`，保留 success、status、operator，补 trace/request metadata、唯一事件类型和 Redis 对象身份核对。缺失 Redis 仍检查 CACHE_ERROR，并明确服务未收到调用参数。

五处 dev-menu 成功场景保留原字段精确值、HTTP 状态、reconcile 调用、dry-run 不失效、菜单变化事件/runtime 更新、config-only 不发菜单事件等原断言；仅改为顶层 JSON，并新增 `'data' not in payload`，防止兼容包装回归。404/403、SSE headers 和 ready 事件用例保持。未删测试、跳过用例、宽化预期或用新的 mock 替代被测生产响应逻辑。

## 独立执行

1. 从隔离候选 backend 用绝对 source venv 运行：`python -m pytest -q -n 0 --no-cov modules/system/tests/test_config_refresh_command.py modules/system/tests/test_dev_menu_sync_controller.py tests/unit/controllers/test_config_controller.py`：**16 passed**，exit 0。前两个文件包含本轮 14 项，另两项为相邻 config 路由契约。
2. 两个变化文件的 Ruff check、Ruff format --check：均 exit 0，零问题。
3. `git diff --check`：exit 0；tracked 差量精确等于两个测试文件。

完整命令和日志 SHA 见 `independent-tests.json`、`independent-lint.json` 及对应日志；候选 scope/hash 见 `independent-candidate.json`。

已检查主代理 RED 的 7 failed / 7 passed、源原工作区 14 passed 及候选更广相关集合 155 passed / 实际源同命令 163 passed（源有额外原测试）记录，证明修正先前只存在源未提交内容、当前候选本身可通过。这些是主代理证据，不算本代理重跑，不与独立 16 项相加。

## 边界

本代理未使用 browser/computer use、登录、运行服务、连接或修改真实数据库/Redis，也未改源产品、创建依赖 symlink 或提交。TestClient 依赖替身与异步 stub 只在测试内使用，不替代读取真实 controller/response 代码。未运行全库测试，不宣称所有历史问题已解决；最终 std 提交范围、无关改动保留和任务资源清理仍由主代理完成。

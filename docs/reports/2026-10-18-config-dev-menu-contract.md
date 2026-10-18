# 配置刷新与 dev/menu 测试契约收敛

基线为 `std@c65cddfde6d0f24640d00f2eed38f83ac38fd926`。干净工作树复现原有 **7 failed / 7 passed**；源目录已存在两份相关测试的未提交修正，原集合 **14 passed**。本轮仅交付这两份测试及本报告证据，保留其他未提交工作。

## 真实契约与修正

- `RefreshConfigCacheCommandHandler` 调用配置缓存初始化服务，返回 `data={}`、`status='refreshed'` 和缓存刷新事件。成功提示不属于命令业务数据；HTTP 控制器返回顶层 `{'status': 'refreshed'}`，前端 API 也以此声明。本轮把两条旧 `message` 断言迁移为空业务数据与状态，并保留、补强 Redis 调用、操作人、追踪元数据和事件断言；删除源原修正中的重复状态断言。
- dev/menu 的 signature、status、sync 通过 `ResponseUtil.ok_resource` 直接返回顶层资源。前端热同步实际读取 `payload.signature`。五处响应断言改读顶层字段，并明确断言不存在 `data` 包裹；原有业务字段、权限/404、SSE、dry-run、运行态、事件发布和配置变更不触发菜单重载等检查保留。
- 核对的七个生产实现/前端消费文件在源目录、隔离候选与 HEAD 完全相同；没有恢复成功消息、旧响应包裹或其他兼容路径，也没有修改产品代码、公开契约和生成产物。

## 验证与边界

隔离候选原集合 **14 passed**，扩大到全部 `modules/system/tests` 及配置控制器/服务、响应工具、managed-data reconcile 单测后 **155 passed**；不再排除原两份失败文件。实际源同一扩大命令 **163 passed**，包含源已有额外测试，两种集合数量不累加。

两份测试的 Ruff、format 和 backend conventions guardrails 通过。独立复审无 P0/P1/P2，独立执行相关 16 项测试及两文件 lint/format 通过。验证使用真实 FastAPI TestClient 响应边界、替代服务及 SQLite/内存 fixture，不等于真实数据库或浏览器业务验收；未启动服务、登录或访问真实 MySQL/Redis。未运行全仓测试或声称全库全绿。

基线失败、命令、日志 SHA、消费输入和独立复审见[验证证据](evidence/2026-10-18-config-dev-menu-contract/verification.json)。本轮交付后的源复验、逐路径保留、索引及临时工作树/分支清理记录保存在 `.git/codex-delivery-preservation/config-dev-menu-contract/`；不推送远端。

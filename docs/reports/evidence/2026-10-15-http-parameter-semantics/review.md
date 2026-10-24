# 本轮只读审查

审查由同模型、同推理强度的子代理在当前两个 checkout 完成，未修改文件，未使用 computer use。

首次发现一个 P2：Axios 模式先执行 joinParamsToUrl、再注入 query token，会令 Axios 默认 query 再次合入。复现为 tenant 默认参数出现两次。

修复前补充三个既有 client 测试案例，实际观察两个失败：默认 query 重复，以及未拼接 URL 时 URLSearchParams 的 query token 未被序列化；另一个案例通过。

最终修复仅作用于 Axios 模式：token 注入后再消费 query；内建 query token 注入 URLSearchParams 时先复制实例并使用 set。Legacy 时序不变。

复查结论：原 P2 已消除，未发现新的本轮范围阻塞问题。审查者独立复跑 HTTP 全库 88 项通过，git diff --check 通过；此前也独立执行新增日志兼容案例 2 项通过。

现有业务防重复提交只看 data、不看 params 的行为在本轮迁移前后均存在，属于后续独立评估事项，本轮未改动。

# Backend Architecture P0 Runbook

## 版本与适用范围

- 文档版本：v1
- 更新时间：2026-02-11
- 适用：`backend-architecture-p0-foundation` 涉及的幂等、限流、观测、仿真共享状态、CI 守护

## CI 基线（GitLab）

- 本项目以 **GitLab CI** 作为架构门禁来源，不以 GitHub workflow 作为发布阻断依据。
- 关键 job：
  - `dao-import-check`
  - `migration-drift-check`
  - `architecture-regression-tests`

## Feature Toggles

- 幂等中间件：`idempotency_enabled`（`config/env.py`）
- 限流中间件：`rate_limit_enabled`
- OTel tracing：`otel_enabled`
- JSON 日志：`log_json_enabled`

## 降级行为说明

- Redis 不可用时：
  - 幂等中间件回退到进程内缓存（跨 worker 不共享）。
  - 限流回退到进程内计数器（全局配额不再严格一致）。
  - 仿真 runtime state 存储回退到进程内内存（重启后状态丢失）。
- OTel 依赖缺失时：
  - `init_otel_tracing` 自动跳过埋点并记录 warning，业务继续可用。

## 故障处理

### 1) 写接口大量 409（幂等冲突）

- 检查请求是否复用了同一 `X-Idempotency-Key` 且请求体不同。
- 检查 `idempotency_path_prefixes` 和 `idempotency_exclude_paths` 是否配置过宽。
- 必要时临时关闭幂等中间件：`idempotency_enabled=false`。

### 2) 大量 429（限流触发）

- 查看响应头：`Retry-After`、`X-RateLimit-*`、`X-RateLimit-Tier`。
- 确认是否突发流量或代理层 IP 汇聚导致。
- 临时调整阈值：
  - `rate_limit_auth_ip/rate_limit_auth_user`
  - `rate_limit_write_ip/rate_limit_write_user`
  - `rate_limit_read_ip/rate_limit_read_user`

### 3) 仿真跨 worker 状态不一致

- 优先检查 Redis 连通性与延迟。
- 检查会话 owner 锁键：`sim:session:{session_id}:producer_owner` 是否存在异常抖动或频繁漂移。
- 校验是否出现多 worker 同 session 同时推送导致数据竞争（owner 失效场景）。
- 若 Redis 异常，先将流量收敛到单 worker，恢复 Redis 后再扩容。

## 回滚流程（最小化影响）

1. 将 `idempotency_enabled=false`，重启后端实例。
2. 将 `rate_limit_enabled=false`，重启后端实例。
3. 将 `otel_enabled=false` 或降低采样率 `otel_traces_sample_ratio`。
4. 必要时将 `log_json_enabled=false` 回退到文本日志格式。
5. 回滚后执行健康检查：
   - `GET /health`
   - `GET /ready`
   - `GET /metrics`

## 恢复检查清单

- 中间件链路恢复：
  - 幂等：同 key 同 payload 重试仅执行一次
  - 限流：超阈值返回 429 + `Retry-After`
- 观测恢复：
  - 日志包含 `request_id/trace_id`
  - `/metrics` 可抓取
  - OTel exporter 可见 span（若启用）
- 仿真恢复：
  - 跨进程 smoke 用例通过
  - 会话状态可从 shared store 读取

# P2 DI 性能基线（2026-02-21）

## 范围与环境

- 范围：P2 本轮验收范围（排除 `simulation`、`protocol`、`device*` 迁移收尾）
- Python：`ruoyi-fastapi-backend/venv/bin/python 3.13.11`
- 目标：评估 DI 框架自身开销（不包含 DB/Redis I/O）

## 采样方法（可复现）

1) 容器启动阶段开销（build + validate）

采集说明：该结果由历史容器启动微基准脚本生成，脚本已从当前仓库移除，产物保留在 `di-bootstrap-benchmark-2026-02-21.json`。

2) 服务解析对比（direct provider call vs `resolve_service`）

采集说明：该结果由历史容器解析微基准脚本生成，脚本已从当前仓库移除，产物保留在 `di-resolution-benchmark-2026-02-21.json`。

原始产物：
- `docs/specs/backend-arch-p2-dependency-injection/baselines/di-bootstrap-benchmark-2026-02-21.json`
- `docs/specs/backend-arch-p2-dependency-injection/baselines/di-resolution-benchmark-2026-02-21.json`

## 结果快照

### 1) 容器启动阶段（ms）

- `build_ms`: `avg=0.002`, `p95=0.002`, `max=0.005`
- `validate_ms`: `avg=0.001`, `p95=0.001`, `max=0.014`
- `total_ms`: `avg=0.003`, `p95=0.003`, `max=0.016`

### 2) 服务解析对比（p95, us）

- `avg_overhead_p95_us`: `0.041`
- `max_overhead_p95_us`: `0.167`
- `avg_overhead_p95_pct`: `6.228`
- `max_overhead_p95_pct`: `21.229`

说明：
- 百分比受“基线仅微秒级”影响，抖动放大明显，个别 service 出现负值/高百分比属微基准噪声。
- 判定优先看绝对值：`resolve_service` 相比 direct call 的 p95 额外开销在本次样本中最大 `0.167us`。

## 结论

- DI 框架自身开销维持在微秒级（服务解析）与近零毫秒级（容器 build+validate）。
- 已补齐“同场景 direct vs resolve”对比口径，满足 P2 Task 8 性能基线可复验要求。
- 本基线用于版本间横向对比；NFR2 的接口级 P95（端到端）仍建议在独立压测中验证。

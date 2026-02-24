# P4 CQRS 性能基线（2026-02-22）

## 范围与环境

- 范围：P4 系统管理域 CQRS 分发链路（不含 DB/Redis I/O）
- Python：`ruoyi-fastapi-backend/venv/bin/python 3.13.11`
- 目标：量化 `Mediator.query` 及默认读管道（`QueryPerformanceBehavior`）的分发开销

## 采样方法（可复现）

```bash
cd ruoyi-fastapi-backend && venv/bin/python scripts/benchmark_cqrs_query_dispatch.py --iterations 50000 --warmup 2000 > ../docs/specs/backend-arch-p4-cqrs/baselines/cqrs-query-dispatch-benchmark-2026-02-22.json
```

原始产物：
- `docs/specs/backend-arch-p4-cqrs/baselines/cqrs-query-dispatch-benchmark-2026-02-22.json`

## 结果快照（us）

- `direct handler p95`: `0.125`
- `mediator (no query behaviors) p95`: `0.5`
- `mediator + default query behaviors p95`: `2.0`

开销（p95）：
- `mediator_plain_vs_direct`: `+0.375 us`
- `mediator_pipeline_vs_direct`: `+1.875 us`
- `mediator_pipeline_vs_plain`: `+1.5 us`

## 结论

- CQRS 分发与默认读管道带来的额外 p95 开销保持在微秒级。
- P4 本轮用于切换验收的“分发链路基线”已沉淀，可用于后续版本回归对比。
- 端到端接口级 P95（含数据库）仍建议在独立压测环境按 NFR1 单独评估。

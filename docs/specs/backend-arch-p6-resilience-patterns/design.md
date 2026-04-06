# 高级弹性模式技术设计

## 架构概述

P6 采用统一弹性中间层治理外部依赖调用：

- Retry（tenacity）
- Circuit Breaker（状态机）
- Bulkhead（Semaphore 隔离）
- Saga（持久化补偿事务）
- Graceful Degradation（降级输出）
- Deep Health（深度健康探测）

所有关键外部调用必须绑定弹性策略，不保留“裸调用”路径。

## 数据流图

```mermaid
flowchart TD
    REQ[Request] --> POL[Policy Router]
    POL --> CB[Circuit Breaker]
    CB --> RTY[Retry]
    RTY --> BH[Bulkhead]
    BH --> CALL[External/DB Call]
    CALL --> MAP[Degradation Mapper]
    MAP --> RESP[Response + X-Degraded-Services]
    CALL --> SAGA[Saga Engine]
    SAGA --> STORE[(redis saga keys)]
    POL --> DEEP[/health/deep]
```

## 组件与接口定义

- `resilience/retry_policy.py`
- `resilience/circuit_breaker.py`
- `resilience/bulkhead.py`
- `resilience/saga_engine.py`
- `resilience/degradation.py`
- `resilience/health_deep.py`
- `resilience/policy_center.py`
- `resilience/executor.py`
- `resilience/runtime.py`
- `resilience/policy_bindings.json`

策略路由规则：

- 按依赖类型与业务关键级别装载策略模板。
- 策略配置集中管理，支持灰度与回滚。
- 外部调用绑定曾由历史 resilience 治理脚本在 CI 中强制校验；该脚本现已移除。

## API 接口设计

新增运维接口：

- `GET /health/deep`
- `GET /resilience/circuit-breakers`
- `GET /saga/instances`
- `POST /saga/{id}/compensate`

统一约束：

- 必须走管理员权限和审计日志。
- 降级场景响应附带 `X-Degraded-Services`。

## 数据模型与数据库变更

持久化策略：

- Saga 状态优先写入 Redis（`saga:instance:*`），无 Redis 时降级到内存存储（测试/应急）。
- 熔断器状态当前为内存态，支持后续扩展持久化。

新增指标：

- `retry_attempt_total`
- `circuit_breaker_state`
- `bulkhead_rejected_total`
- `saga_failed_total`

## 安全考量

- 运维接口严格鉴权，禁止普通用户访问。
- 降级响应禁止泄露内部依赖拓扑与敏感错误。
- Saga 补偿需幂等，避免重复补偿破坏一致性。
- 策略配置更新需参数合法性校验。

## 测试策略

- 单元测试：retry/circuit/bulkhead/saga 状态行为。
- 集成测试：故障注入下的降级、恢复、健康检查。
- 混沌演练：持续故障场景下的告警与恢复。
- 性能回归：验证弹性层引入后核心接口 P95 回退在阈值内。

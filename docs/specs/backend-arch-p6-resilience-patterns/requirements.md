# 高级弹性模式需求规格

## 简介

引入生产级弹性治理能力，覆盖 Retry、Circuit Breaker、Bulkhead、Saga、Graceful Degradation 与深度健康检查。目标是在外部依赖抖动和局部故障场景下保持核心链路可用、可观测、可恢复。

## 前置与约束

- 依赖 P1-P5 的接口边界、事件机制和可观测基础。
- `tenacity` 用于重试策略；Circuit Breaker 使用独立熔断组件（自研状态机或专用库）实现。
- Bulkhead 基于 `asyncio.Semaphore` + 超时控制。
- Saga 通过持久化状态机与补偿动作实现，不依赖内存状态。

## 需求列表

### R1: Circuit Breaker 熔断治理

**用户故事:** 作为 SRE，我希望外部依赖故障时自动熔断，以防级联故障扩散。

**验收标准 (EARS):**
- R1.AC1: WHEN 连续失败达到阈值时 THE SYSTEM SHALL 将熔断器切换为 OPEN 并快速失败或返回降级结果。
- R1.AC2: WHEN OPEN 冷却期结束时 THE SYSTEM SHALL 进入 HALF_OPEN 并限制探测请求数量。
- R1.AC3: WHEN HALF_OPEN 探测成功率达到恢复条件时 THE SYSTEM SHALL 切换回 CLOSED。
- R1.AC4: WHEN 熔断状态变更时 THE SYSTEM SHALL 记录结构化日志、指标并发布状态变更事件。

### R2: Retry with Backoff 重试策略

**用户故事:** 作为开发者，我希望暂时性失败可自动重试，以减少偶发错误对用户的影响。

**验收标准 (EARS):**
- R2.AC1: WHEN 调用抛出可重试异常时 THE SYSTEM SHALL 使用指数退避 + 抖动策略重试。
- R2.AC2: WHEN 定义重试策略时 THE SYSTEM SHALL 支持 `max_retries`、`base_delay`、`max_delay`、`jitter` 参数配置。
- R2.AC3: WHEN 重试耗尽后仍失败时 THE SYSTEM SHALL 抛出原始异常并附带重试上下文。
- R2.AC4: WHEN 发生重试时 THE SYSTEM SHALL 记录每次重试的次数、等待时长和异常类型。

### R3: Bulkhead 舱壁隔离

**用户故事:** 作为平台稳定性负责人，我希望高延迟操作不会耗尽全局资源。

**验收标准 (EARS):**
- R3.AC1: WHEN 并发请求进入不同资源类型（外部 API、数据库写、文件 IO）时 THE SYSTEM SHALL 使用独立并发池隔离。
- R3.AC2: WHEN 并发池达到上限时 THE SYSTEM SHALL 按策略执行排队等待或快速失败。
- R3.AC3: WHEN 请求等待超过 `max_wait` 时 THE SYSTEM SHALL 返回受控错误并打点。
- R3.AC4: WHEN 并发池利用率超过告警阈值时 THE SYSTEM SHALL 上报 Prometheus 指标并触发告警。

### R4: Saga 编排与补偿

**用户故事:** 作为开发者，我希望跨模块长事务在局部失败时可自动补偿，避免脏状态残留。

**验收标准 (EARS):**
- R4.AC1: WHEN 定义 Saga 流程时 THE SYSTEM SHALL 为每个步骤定义 `action` 与 `compensate` 行为。
- R4.AC2: WHEN 任一步骤失败时 THE SYSTEM SHALL 按逆序执行已完成步骤补偿。
- R4.AC3: WHEN 补偿失败时 THE SYSTEM SHALL 标记 Saga 为 `FAILED_NEEDS_MANUAL_INTERVENTION` 并记录诊断信息。
- R4.AC4: WHEN Saga 执行时 THE SYSTEM SHALL 将步骤状态持久化（PENDING/COMPLETED/COMPENSATING/FAILED）。

### R5: Graceful Degradation 优雅降级

**用户故事:** 作为产品经理，我希望关键功能在依赖异常时仍可服务，用户影响最小化。

**验收标准 (EARS):**
- R5.AC1: WHEN Redis 或缓存依赖不可用时 THE SYSTEM SHALL 自动旁路缓存并保持核心读写可用。
- R5.AC2: WHEN 非关键外部服务不可用时 THE SYSTEM SHALL 返回默认值或跳过非关键步骤并继续主流程。
- R5.AC3: WHEN 发生降级时 THE SYSTEM SHALL 在响应中标注降级依赖信息（如 `X-Degraded-Services`）并记录日志。
- R5.AC4: WHEN 依赖恢复健康时 THE SYSTEM SHALL 自动恢复正常路径，无需人工介入。

### R6: 深度健康检查

**用户故事:** 作为 SRE，我希望快速判断系统是否可对外服务并定位故障依赖。

**验收标准 (EARS):**
- R6.AC1: WHEN 调用 `/health/deep` 时 THE SYSTEM SHALL 并发检查数据库、Redis、关键外部 API 等依赖状态。
- R6.AC2: WHEN 单个依赖检查超时时 THE SYSTEM SHALL 在超时阈值内返回该依赖 `degraded`，并不中断其他检查。
- R6.AC3: WHEN 所有关键依赖健康时 THE SYSTEM SHALL 返回 `healthy` 状态与 HTTP 200。
- R6.AC4: WHEN 任一关键依赖不健康时 THE SYSTEM SHALL 返回 `unhealthy` 状态与 HTTP 503。

### R7: 策略治理与防回退

**用户故事:** 作为架构负责人，我希望弹性策略配置统一且可审计，避免策略漂移。

**验收标准 (EARS):**
- R7.AC1: WHEN 新增外部依赖调用点时 THE SYSTEM SHALL 明确绑定对应的 retry/circuit/bulkhead 策略配置。
- R7.AC2: WHEN 策略配置变更时 THE SYSTEM SHALL 支持灰度开关与回滚。
- R7.AC3: WHEN CI 执行弹性规则检查时 THE SYSTEM SHALL 阻断未配置弹性策略的关键外部调用。
- R7.AC4: WHEN 周期性演练执行时 THE SYSTEM SHALL 输出故障演练报告（触发率、恢复时间、失败原因）。

## 非功能需求

- NFR1: 弹性策略引入后，核心 API 在稳态下 P95 延迟回退不超过 5%。
- NFR2: 深度健康检查总耗时目标不超过 5 秒。
- NFR3: Saga 状态写入与查询应具备可追踪性，失败流程必须可恢复或可人工接管。
- NFR4: 所有弹性组件必须暴露指标与结构化日志，满足生产排障要求。

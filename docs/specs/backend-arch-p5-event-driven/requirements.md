# 事件驱动架构需求规格

## 简介

以 Domain Event 作为跨模块协作机制，采用“事务内写 Outbox + 异步发布 + 幂等消费”的模式，逐步替代跨模块直接函数调用。该阶段优先保证一致性、可追踪与可重放能力，为后续分布式消息化升级保留扩展点。

## 前置与约束

- 依赖 P1-P4 的接口边界、注入与 CQRS 处理链。
- 初期为进程内 Event Bus，不强制引入外部消息队列。
- 采用 Transactional Outbox 作为发布可靠性基础。
- Event History（审计历史）与 Outbox 职责分离，避免语义混淆。

## 需求列表

### R1: Domain Event 契约

**用户故事:** 作为开发者，我希望事件结构统一且可版本化，以便安全演进和跨模块协作。

**验收标准 (EARS):**
- R1.AC1: WHEN 定义领域事件时 THE SYSTEM SHALL 使用不可变模型，至少包含 `event_id`、`event_type`、`aggregate_type`、`aggregate_id`、`occurred_at`、`payload`、`metadata`。
- R1.AC2: WHEN 创建事件时 THE SYSTEM SHALL 自动生成唯一 `event_id` 与时间戳，并记录事件版本号。
- R1.AC3: WHEN 关键业务操作完成时 THE SYSTEM SHALL 产出对应领域事件并进入发布流程。
- R1.AC4: WHEN 序列化事件时 THE SYSTEM SHALL 使用 JSON 编码并保留版本兼容字段。

### R2: Event Bus 接口与分发语义

**用户故事:** 作为架构师，我希望事件总线有稳定抽象，以便未来替换实现而不影响业务代码。

**验收标准 (EARS):**
- R2.AC1: WHEN 发布事件时 THE SYSTEM SHALL 通过 `IEventBus.publish(event)` 接口发送。
- R2.AC2: WHEN 注册订阅者时 THE SYSTEM SHALL 通过 `IEventBus.subscribe(event_type, handler)` 或等效注册表机制完成绑定。
- R2.AC3: WHEN 同一事件有多个订阅者时 THE SYSTEM SHALL 隔离处理器执行失败，单个失败不阻塞其他处理器。
- R2.AC4: WHEN 处理器执行失败时 THE SYSTEM SHALL 记录结构化日志与失败指标，并进入重试或补偿策略。

### R3: Transactional Outbox 一致性保障

**用户故事:** 作为平台工程师，我希望业务提交与事件持久化原子一致，以便避免“业务成功但事件丢失”。

**验收标准 (EARS):**
- R3.AC1: WHEN CommandHandler 产出领域事件时 THE SYSTEM SHALL 在同一数据库事务内写入 Outbox 记录。
- R3.AC2: WHEN Outbox 中存在待发布记录时 THE SYSTEM SHALL 由后台 Dispatcher 定期拉取并发布到 Event Bus。
- R3.AC3: WHEN 发布成功时 THE SYSTEM SHALL 更新 Outbox 状态字段（如 `published_at`、`status`）。
- R3.AC4: WHEN 发布失败时 THE SYSTEM SHALL 记录 `retry_count`、`next_retry_at` 并执行指数退避重试。

### R4: Event History 与审计追踪

**用户故事:** 作为审计员，我希望事件历史可查询、可追溯，以便满足合规与排障需求。

**验收标准 (EARS):**
- R4.AC1: WHEN 事件发布成功后 THE SYSTEM SHALL 将事件写入可查询的历史存储（独立表或归档视图）。
- R4.AC2: WHEN 查询事件历史时 THE SYSTEM SHALL 支持按 `aggregate_id`、`event_type`、时间范围过滤。
- R4.AC3: WHEN 历史数据增长到阈值时 THE SYSTEM SHALL 提供归档或分区策略并保持查询可用。
- R4.AC4: WHEN 事件回放执行时 THE SYSTEM SHALL 支持按事件流顺序重放并记录回放任务日志。

### R5: 幂等消费与跨模块编排

**用户故事:** 作为开发者，我希望事件消费在重试场景下仍无副作用重复。

**验收标准 (EARS):**
- R5.AC1: WHEN 同一事件被重复投递时 THE SYSTEM SHALL 通过 `event_id + handler` 去重，保证处理幂等。
- R5.AC2: WHEN 新增跨模块副作用时 THE SYSTEM SHALL 通过新增事件处理器扩展，而不修改事件源模块核心逻辑。
- R5.AC3: WHEN 处理器需要读取其他模块数据时 THE SYSTEM SHALL 通过该模块 `ports` 契约访问。
- R5.AC4: WHEN 处理器重试耗尽仍失败时 THE SYSTEM SHALL 将事件标记为人工介入并提供诊断上下文。

### R6: 可观测性与运行治理

**用户故事:** 作为 SRE，我希望事件链路可观测，以便快速定位积压、失败与时延问题。

**验收标准 (EARS):**
- R6.AC1: WHEN 事件系统运行时 THE SYSTEM SHALL 暴露 Outbox 积压、发布成功率、失败率、重试次数等指标。
- R6.AC2: WHEN Outbox 积压超过阈值时 THE SYSTEM SHALL 触发告警并附带模块维度标签。
- R6.AC3: WHEN 执行健康检查时 THE SYSTEM SHALL 返回事件分发组件状态与最新滞后时间。
- R6.AC4: WHEN 事件处理完成时 THE SYSTEM SHALL 在日志中关联 `trace_id` 与 `event_id`。

## 非功能需求

- NFR1: 默认轮询间隔为 1 秒，且可配置。
- NFR2: 在默认配置下，Outbox 事件从提交到发布成功的 P95 延迟目标不超过 2 秒。
- NFR3: 单事件 `payload` 大小上限为 64KB，超过时必须显式拒绝并记录错误。
- NFR4: 事件处理语义为 at-least-once，消费端必须具备幂等保障。

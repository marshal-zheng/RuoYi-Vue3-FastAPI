# CQRS 读写分离需求规格

## 简介

在不引入物理读写分库的前提下落地 CQRS：写路径以 Command 为中心，读路径以 Query/ReadModel 为中心。通过 Handler 与可组合管道降低服务层复杂度，并为 P5 事件驱动输出标准化领域事件。

## 前置与约束

- 依赖 P1-P3 已在目标模块建立接口边界与注入机制。
- Command/Query 使用 Pydantic 模型定义并保留类型安全。
- 采用“模块级渐进迁移”，不要求全量功能同一迭代切换。
- 当前迭代优先覆盖系统管理域（`config/dict/dept/menu/post/notice`），`simulation/protocol/device` 暂不纳入本阶段。

## 需求列表

### R1: Command 与写路径 Handler

**用户故事:** 作为开发者，我希望写操作有统一命令模型与处理入口，以便业务规则集中且可测试。

**验收标准 (EARS):**
- R1.AC1: WHEN 新增写操作时 THE SYSTEM SHALL 定义对应 Command 模型，包含该操作所需输入与上下文元数据。
- R1.AC2: WHEN Command 被处理时 THE SYSTEM SHALL 由单一 CommandHandler 承担验证、业务决策与持久化编排。
- R1.AC3: WHEN 命令参数非法时 THE SYSTEM SHALL 返回类型化验证错误（字段级原因可定位）。
- R1.AC4: WHEN Command 成功执行时 THE SYSTEM SHALL 返回标准 `CommandResult`（结果数据、状态、可选领域事件）。

### R2: Query 与读路径 Handler

**用户故事:** 作为前端与后端开发者，我希望查询路径可独立优化，以便在不影响写模型的前提下优化读取性能。

**验收标准 (EARS):**
- R2.AC1: WHEN 新增查询能力时 THE SYSTEM SHALL 定义 Query 模型（过滤、排序、分页等）。
- R2.AC2: WHEN Query 被处理时 THE SYSTEM SHALL 由 QueryHandler 构建读优化查询并返回专用 ReadModel。
- R2.AC3: WHEN 读取列表与详情场景差异明显时 THE SYSTEM SHALL 定义独立 ReadModel，禁止直接复用写模型。
- R2.AC4: WHEN 执行查询处理时 THE SYSTEM SHALL 使用只读会话语义（无显式写事务提交）。

### R3: Mediator 与路由规则

**用户故事:** 作为控制器开发者，我希望控制器只负责编排请求与响应映射，不承载业务规则。

**验收标准 (EARS):**
- R3.AC1: WHEN 控制器接收写请求时 THE SYSTEM SHALL 构造 Command 并提交给 Mediator 或等效分发器。
- R3.AC2: WHEN 控制器接收读请求时 THE SYSTEM SHALL 构造 Query 并提交给 Query 分发入口（可与 Mediator 共用机制）。
- R3.AC3: WHEN 分发器找不到对应 Handler 时 THE SYSTEM SHALL 返回明确配置错误并记录缺失类型。
- R3.AC4: WHEN 新增 Handler 时 THE SYSTEM SHALL 通过注册表完成映射，禁止隐式反射导致不可控路由。

### R4: Pipeline Behaviors 横切管道

**用户故事:** 作为架构维护者，我希望验证、日志、事务等横切逻辑可复用，避免各 Handler 重复实现。

**验收标准 (EARS):**
- R4.AC1: WHEN 分发 Command 时 THE SYSTEM SHALL 按固定顺序执行管道（验证 -> 鉴权/审计 -> 事务 -> Handler -> 事件收集）。
- R4.AC2: WHEN 验证管道失败时 THE SYSTEM SHALL 在进入 Handler 前终止执行并返回错误。
- R4.AC3: WHEN 事务管道包裹写 Handler 时 THE SYSTEM SHALL 在成功时提交、异常时回滚。
- R4.AC4: WHEN 日志管道执行时 THE SYSTEM SHALL 记录命令类型、耗时、结果状态与关联 trace id。

### R5: 读模型与查询性能治理

**用户故事:** 作为性能优化负责人，我希望读模型和查询可持续优化且不引入 N+1 风险。

**验收标准 (EARS):**
- R5.AC1: WHEN 定义 ReadModel 时 THE SYSTEM SHALL 仅包含视图需要字段，避免返回无关数据。
- R5.AC2: WHEN ReadModel 依赖关联数据时 THE SYSTEM SHALL 通过 JOIN/批量查询避免 N+1。
- R5.AC3: WHEN 存在跨上下文查询场景时 THE SYSTEM SHALL 通过组合查询服务（Composed Query）完成聚合并定义边界超时策略。
- R5.AC4: WHEN 查询性能回退超过阈值时 THE SYSTEM SHALL 输出慢查询证据并回滚或修复。

### R6: 渐进迁移与兼容策略

**用户故事:** 作为项目负责人，我希望 CQRS 改造可逐模块推进，不影响线上稳定性。

**验收标准 (EARS):**
- R6.AC1: WHEN 启动 CQRS 迁移时 THE SYSTEM SHALL 明确“先写后读”或“先读后写”模块顺序与里程碑。
- R6.AC2: WHEN 模块迁移未完成时 THE SYSTEM SHALL 允许旧服务入口与新 Handler 共存，并定义退役日期。
- R6.AC3: WHEN 某模块完成迁移时 THE SYSTEM SHALL 提供控制器、Handler、读模型、事务与回归测试证据。
- R6.AC4: WHEN 新增功能开发时 THE SYSTEM SHALL 默认优先使用 CQRS 模式，不再扩张旧式上帝服务。

## 非功能需求

- NFR1: CQRS 迁移后，目标模块读路径 P95 延迟相对基线不回退超过 5%。
- NFR2: Handler 与管道实现应保持可维护性，建议单文件不超过 300 行（超限需拆分并在评审说明）。
- NFR3: 分发链路与错误日志需支持 trace 关联，便于问题定位。
- NFR4: Command/Query/ReadModel 文件应支持 IDE 跳转、补全与静态检查。

# 垂直切片与 DDD 模块边界需求规格

## 简介

将现有“按技术层分目录”的结构逐步迁移为“按业务上下文分模块”的垂直切片结构。每个 Bounded Context 自包含 API、应用服务、领域模型和基础设施实现，并通过 Protocol 边界进行跨上下文协作。

## 前置与约束

- 依赖 P1（Protocol 契约）与 P2（DI 机制）完成核心模块基线。
- 采用渐进迁移（Strangler）而非一次性替换。
- 模块划分遵循 DDD Bounded Context 和高内聚低耦合原则。
- 共享能力收敛到 `shared` 内核，禁止无边界共享业务实现。
- 本批次实施范围聚焦 `system/identity/project`，`simulation/protocol/device` 标记为后续批次（暂不纳入本轮验收）。

## 需求列表

### R1: 目标模块结构

**用户故事:** 作为开发者，我希望一个业务需求主要在一个上下文目录内完成，以便降低定位与修改成本。

**验收标准 (EARS):**
- R1.AC1: WHEN 新增或迁移业务能力时 THE SYSTEM SHALL 将其放入对应 `modules/<context>/` 目录并保持上下文内聚。
- R1.AC2: WHEN 创建上下文目录时 THE SYSTEM SHALL 包含 `api/`、`application/`、`domain/`、`infrastructure/`、`ports.py`、`tests/` 等标准子结构。
- R1.AC3: WHEN 单文件体量持续膨胀时 THE SYSTEM SHALL 按子领域拆分文件，而非继续扩展单一巨型文件。
- R1.AC4: WHEN 开发者检索某业务能力时 THE SYSTEM SHALL 能在同一上下文目录内定位 API、用例、模型与仓储实现。

### R2: Bounded Context 边界规则

**用户故事:** 作为架构师，我希望上下文边界清晰，以便团队并行开发且减少跨模块副作用。

**验收标准 (EARS):**
- R2.AC1: WHEN 制定模块规划时 THE SYSTEM SHALL 至少覆盖 `identity`、`project`、`simulation`、`device`、`protocol`、`system`、`codegen`、`scheduler` 等目标上下文。
- R2.AC2: WHEN 一个实体在多个上下文出现时 THE SYSTEM SHALL 通过 ACL/映射对象转换，禁止跨上下文直接复用内部实体。
- R2.AC3: WHEN 上下文之间发生调用时 THE SYSTEM SHALL 通过 `ports.py` 契约与应用层入口交互，不直接访问对方内部仓储实现。
- R2.AC4: WHEN 新增上下文时 THE SYSTEM SHALL 完成上下文目录、契约定义、容器注册与最小回归测试。

### R3: 共享内核治理

**用户故事:** 作为维护者，我希望共享代码可控，以便避免“共享层膨胀成新耦合中心”。

**验收标准 (EARS):**
- R3.AC1: WHEN 多模块复用基础模型或错误定义时 THE SYSTEM SHALL 放入 `shared` 内核并保持向后兼容策略。
- R3.AC2: WHEN 多模块复用工具能力时 THE SYSTEM SHALL 仅共享无业务语义的横切能力（事务、分页、响应、审计等）。
- R3.AC3: WHEN 共享内核变更时 THE SYSTEM SHALL 触发受影响上下文回归测试并给出影响清单。
- R3.AC4: WHEN 发现业务逻辑被放入共享内核时 THE SYSTEM SHALL 在评审阶段阻断并要求回归到所属上下文。

### R4: 模块注册与启动策略

**用户故事:** 作为平台工程师，我希望模块注册机制显式、可审计，而不是隐式魔法扫描。

**验收标准 (EARS):**
- R4.AC1: WHEN 应用启动时 THE SYSTEM SHALL 通过显式模块注册表加载路由与容器扩展。
- R4.AC2: WHEN 新增模块时 THE SYSTEM SHALL 仅需在注册表中增加模块声明即可接入。
- R4.AC3: WHEN 移除模块时 THE SYSTEM SHALL 通过删除注册项完成下线，启动过程不因扫描残留导致 ImportError。
- R4.AC4: WHEN 启动完成时 THE SYSTEM SHALL 输出已加载模块、路由前缀与版本信息日志。

### R5: 渐进迁移与兼容策略

**用户故事:** 作为项目负责人，我希望迁移可持续交付，不因“大爆炸式重构”阻断业务迭代。

**验收标准 (EARS):**
- R5.AC1: WHEN 迁移启动时 THE SYSTEM SHALL 提供旧路径到新路径的映射表（文件级别）。
- R5.AC2: WHEN 某上下文尚未完全迁移时 THE SYSTEM SHALL 允许旧入口转调新实现并保持接口兼容。
- R5.AC3: WHEN 一个上下文迁移完成时 THE SYSTEM SHALL 通过契约测试、接口回归与性能基线后再移除旧实现。
- R5.AC4: WHEN 迁移里程碑达成时 THE SYSTEM SHALL 更新迁移看板与文档，标注已迁移/待迁移边界。

### R6: 架构防回退机制

**用户故事:** 作为架构守护者，我希望后续开发不会回退到“跨层硬耦合”模式。

**验收标准 (EARS):**
- R6.AC1: WHEN 提交跨上下文变更时 THE SYSTEM SHALL 在 CI 中校验是否存在违规跨模块内部导入。
- R6.AC2: WHEN 新增控制器/服务文件时 THE SYSTEM SHALL 校验其目录归属符合目标模块结构规范。
- R6.AC3: WHEN 评审识别到“绕过 ports 直接访问对方仓储”行为时 THE SYSTEM SHALL 阻断合并并给出修正建议。
- R6.AC4: WHEN 周期性架构巡检执行时 THE SYSTEM SHALL 输出边界违规统计和趋势报告。

## 非功能需求

- NFR1: 模块化改造后，整体启动耗时相对基线增加不超过 20%。
- NFR2: 迁移应支持分批发布，每个里程碑均可独立回滚。
- NFR3: 新建模块脚手架应在秒级完成，并自动生成最小测试模板与注册入口。

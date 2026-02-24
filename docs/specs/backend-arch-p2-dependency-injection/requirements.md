# 依赖注入容器需求规格

## 简介

引入可测试、可演进的 IoC/DI 机制，替代当前“部分 classmethod + 部分手工工厂”的混合模式。目标是统一对象装配、显式声明依赖边界，并保持与 FastAPI 请求生命周期一致的资源管理方式。

## 前置与约束

- 依赖 P1（Protocol 契约）已落地核心模块。
- 选型为 `dependency-injector`，但允许以“容器 + FastAPI Depends 包装”方式渐进迁移。
- 不采用一次性重构；新代码强约束、存量代码模块化迁移。
- 容器配置必须支持 `dev/test/prod` 环境覆盖。
- 范围调整（2026-02-21）：本轮暂不纳入仿真/协议/设备相关模块（`simulation`、`protocol`、`device*`）的迁移验收与缺口清零，统一在后续里程碑收敛。

## 需求列表

### R1: 组合根与容器定义

**用户故事:** 作为平台工程师，我希望依赖装配有统一入口，以便依赖关系可追踪、可审计。

**验收标准 (EARS):**
- R1.AC1: WHEN 应用启动时 THE SYSTEM SHALL 在组合根初始化应用容器，并注册基础设施、仓储工厂、服务工厂。
- R1.AC2: WHEN 容器初始化失败（缺失配置、依赖循环、资源不可达）时 THE SYSTEM SHALL 阻止应用启动并输出可定位错误。
- R1.AC3: WHEN 需要分析依赖关系时 THE SYSTEM SHALL 通过脚本导出 Provider 依赖图（DOT/文本均可）。
- R1.AC4: WHEN 新增组件时 THE SYSTEM SHALL 仅通过容器配置完成注册，不在业务层硬编码实例化流程。

### R2: Service 构造器注入规范

**用户故事:** 作为开发者，我希望服务依赖在构造函数中显式声明，以便代码可读且便于测试替换。

**验收标准 (EARS):**
- R2.AC1: WHEN 新增或重构 Service 时 THE SYSTEM SHALL 使用构造器注入 Repository/Service/Infrastructure 依赖（类型优先为 Protocol）。
- R2.AC2: WHEN Service 需要跨服务能力时 THE SYSTEM SHALL 依赖接口类型，不直接导入目标实现类。
- R2.AC3: WHEN 在业务代码中实例化 Service 时 THE SYSTEM SHALL 仅允许在组合根或测试夹具中创建，禁止在业务方法内部 `new` 依赖对象。
- R2.AC4: WHEN 构造器依赖数量持续增长时 THE SYSTEM SHALL 触发设计告警并要求拆分职责或引入聚合依赖对象。

### R3: 会话与资源生命周期

**用户故事:** 作为开发者，我希望数据库会话边界明确，以便事务一致且连接不泄漏。

**验收标准 (EARS):**
- R3.AC1: WHEN HTTP 请求进入时 THE SYSTEM SHALL 复用 FastAPI 请求级 `AsyncSession`，并注入到该请求内的服务/仓储实例。
- R3.AC2: WHEN HTTP 请求结束时 THE SYSTEM SHALL 自动提交或回滚并释放该请求会话。
- R3.AC3: WHEN 后台任务需要数据库访问时 THE SYSTEM SHALL 使用独立 Task-scoped 会话工厂，避免复用请求会话。
- R3.AC4: WHEN 单个请求涉及多个仓储时 THE SYSTEM SHALL 保证其共享同一会话实例。

### R4: 基础设施 Provider 管理

**用户故事:** 作为 SRE，我希望重量级依赖统一管理生命周期，以便稳定启动、优雅关闭、便于健康探测。

**验收标准 (EARS):**
- R4.AC1: WHEN 应用启动时 THE SYSTEM SHALL 通过容器创建 Redis/缓存/调度器等基础设施 Provider。
- R4.AC2: WHEN 应用关闭时 THE SYSTEM SHALL 按依赖顺序释放资源并记录关闭结果。
- R4.AC3: WHEN 任一关键基础设施初始化失败时 THE SYSTEM SHALL 终止启动并输出结构化错误日志。
- R4.AC4: WHEN 执行健康检查时 THE SYSTEM SHALL 返回关键 Provider 的可用状态摘要。

### R5: FastAPI 集成方式

**用户故事:** 作为开发者，我希望容器集成不影响现有路由开发体验。

**验收标准 (EARS):**
- R5.AC1: WHEN 控制器声明依赖时 THE SYSTEM SHALL 支持 `Depends` + 容器 Provider 包装的注入方式（可直接 `Provide[Container.xxx]` 或封装函数）。
- R5.AC2: WHEN 使用 `Provide` 注入时 THE SYSTEM SHALL 使用 Provider 路径而非接口类型字面量作为运行时键。
- R5.AC3: WHEN 新增路由接入依赖时 THE SYSTEM SHALL 不需要在控制器中手工拼装依赖图。
- R5.AC4: WHEN 某 Protocol 缺失实现绑定时 THE SYSTEM SHALL 在启动校验阶段失败，而非请求运行时才出现 500。

### R6: 测试覆盖与替换机制

**用户故事:** 作为测试工程师，我希望依赖替换粒度可控，以便单元/集成测试高效隔离。

**验收标准 (EARS):**
- R6.AC1: WHEN 执行单元测试时 THE SYSTEM SHALL 允许通过 `container.override()` 注入 mock/fake 依赖。
- R6.AC2: WHEN 测试结束时 THE SYSTEM SHALL 自动清理覆盖（如 `reset_override()`）避免测试间污染。
- R6.AC3: WHEN 执行集成测试时 THE SYSTEM SHALL 支持“部分真实依赖 + 部分替身依赖”混合模式。
- R6.AC4: WHEN 覆盖关键依赖失败时 THE SYSTEM SHALL 在测试初始化阶段给出明确错误。

### R7: 渐进迁移治理

**用户故事:** 作为项目负责人，我希望迁移过程可分阶段交付且可防回退。

**验收标准 (EARS):**
- R7.AC1: WHEN 迁移开始时 THE SYSTEM SHALL 提供模块优先级清单与里程碑（先核心模块，后低频模块）。
- R7.AC2: WHEN 模块未迁移完成时 THE SYSTEM SHALL 允许兼容适配层共存，但禁止新增 classmethod 静态模式。
- R7.AC3: WHEN CI 执行架构检查时 THE SYSTEM SHALL 阻断新增“业务方法内部实例化依赖”与“新增静态服务入口”。
- R7.AC4: WHEN 模块完成迁移验收时 THE SYSTEM SHALL 记录迁移状态并更新架构文档。

## 非功能需求

- NFR1: 引入容器后，应用冷启动时间相对基线增加不超过 10%。
- NFR2: 注入机制不应导致核心接口 P95 延迟回退超过 5%（以同环境基线对比）。
- NFR3: 测试环境覆盖与重置操作应在毫秒级完成，并可在单测中稳定复现。
- NFR4: 容器配置应按领域拆分文件，避免单文件过大导致维护困难。

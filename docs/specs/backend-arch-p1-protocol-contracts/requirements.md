# Protocol 接口契约需求规格

## 简介

为 Repository、Service 和基础设施组件建立 `typing.Protocol` 契约，目标是降低跨模块耦合、提升静态可验证性，并为后续 DI（P2）与模块化（P3）提供稳定边界。该阶段不改变业务语义，仅改变类型契约与依赖声明方式。

## 前置与范围

- 采用 Python `typing.Protocol` 结构化子类型，不要求实现类显式继承。
- 兼容现有 `IRepository[T]` / `BaseRepository[T]`，以增量迁移方式推进，不做一次性重写。
- 适用于 `module_admin`、`module_generator` 与后续新模块；优先覆盖被控制器高频调用的服务与仓储。

## 需求列表

### R1: Protocol 定义规范

**用户故事:** 作为开发者，我希望接口定义格式一致，以便快速理解能力边界并减少实现耦合。

**验收标准 (EARS):**
- R1.AC1: WHEN 新增或修改可复用组件（Repository/Service/Infrastructure）时 THE SYSTEM SHALL 为其补充对应 Protocol 定义。
- R1.AC2: WHEN 定义 Protocol 方法时 THE SYSTEM SHALL 声明完整参数类型、返回类型和方法级 docstring。
- R1.AC3: WHEN Protocol 中方法签名发生变化时 THE SYSTEM SHALL 同步更新依赖该接口的调用方类型注解。
- R1.AC4: WHEN 代码评审检查接口契约时 THE SYSTEM SHALL 能在单一入口文件中检索到接口定义与导出项。

### R2: Repository 契约落地

**用户故事:** 作为开发者，我希望仓储能力通过接口暴露，以便服务层仅依赖抽象而非具体实现。

**验收标准 (EARS):**
- R2.AC1: WHEN Service 依赖 Repository 时 THE SYSTEM SHALL 使用 Repository Protocol 作为构造参数或依赖注解类型。
- R2.AC2: WHEN Repository 暴露公开查询/写入方法时 THE SYSTEM SHALL 在对应 Protocol 中声明同名签名。
- R2.AC3: WHEN 运行静态类型检查时 THE SYSTEM SHALL 能验证实现类满足其 Repository Protocol 的结构化约束。
- R2.AC4: WHEN 新增 Repository 公开方法时 THE SYSTEM SHALL 在同次变更中更新 Protocol 与最小回归测试。

### R3: Service 契约落地

**用户故事:** 作为架构维护者，我希望服务间调用通过接口发生，以便限制跨模块实现耦合。

**验收标准 (EARS):**
- R3.AC1: WHEN Service A 依赖 Service B 时 THE SYSTEM SHALL 使用 B 的 Service Protocol 类型，而非直接依赖 B 的具体类。
- R3.AC2: WHEN Service 定义公开业务能力时 THE SYSTEM SHALL 仅将对外方法纳入 Protocol，内部辅助方法不暴露。
- R3.AC3: WHEN 新增跨模块调用时 THE SYSTEM SHALL 通过 Protocol 进行依赖声明，并在评审中禁止新增实现类硬编码导入。
- R3.AC4: WHEN 迁移期存在旧调用路径时 THE SYSTEM SHALL 提供兼容适配层并标注淘汰计划。

### R4: 基础设施契约落地

**用户故事:** 作为测试工程师，我希望外部依赖可被替换，以便单元测试不依赖真实 Redis/外部服务。

**验收标准 (EARS):**
- R4.AC1: WHEN 访问 Redis 能力时 THE SYSTEM SHALL 通过 `IRedisClient`（或等效命名）Protocol 访问。
- R4.AC2: WHEN 使用缓存、审计、事件发布等基础设施时 THE SYSTEM SHALL 提供独立 Protocol（如 `ICacheProvider`、`IAuditLogger`、`IEventBus`）。
- R4.AC3: WHEN 执行单元测试时 THE SYSTEM SHALL 能注入内存实现或 stub/mock 实现替代真实外部依赖。
- R4.AC4: WHEN 基础设施实现替换时 THE SYSTEM SHALL 不需要修改业务服务方法签名。

### R5: 组织方式与命名约定

**用户故事:** 作为开发者与 AI 助手，我希望接口组织策略在当前结构与未来模块化结构下都一致可查。

**验收标准 (EARS):**
- R5.AC1: WHEN 系统仍处于现有分层结构时 THE SYSTEM SHALL 将公共 Protocol 放在集中 `ports` 包中并统一导出。
- R5.AC2: WHEN 迁移到垂直切片结构（P3）时 THE SYSTEM SHALL 允许上下文内 `ports.py` 并保持统一命名前缀规范。
- R5.AC3: WHEN 存在跨上下文公共契约时 THE SYSTEM SHALL 放入共享 `ports` 包，避免重复定义同语义接口。
- R5.AC4: WHEN 查询接口定义时 THE SYSTEM SHALL 能通过静态检索规则在 1 次跳转内定位到定义文件。

### R6: 治理与验收自动化

**用户故事:** 作为平台工程师，我希望 Protocol 迁移可量化且可在 CI 中阻断回退。

**验收标准 (EARS):**
- R6.AC1: WHEN 提交涉及 Repository/Service 公共方法变更的代码时 THE SYSTEM SHALL 在 CI 校验 Protocol 是否同步更新。
- R6.AC2: WHEN 运行类型检查流水线时 THE SYSTEM SHALL 至少对本次变更影响模块执行严格类型校验并阻断新增错误。
- R6.AC3: WHEN 周期性架构检查执行时 THE SYSTEM SHALL 输出 Protocol 覆盖率报告（已覆盖类、未覆盖类、覆盖比例）。
- R6.AC4: WHEN 发现未按规范新增实现类耦合导入时 THE SYSTEM SHALL 通过脚本检查或 lint 规则给出可定位错误。

## 非功能需求

- NFR1: 引入 Protocol 后不引入额外运行时调用开销（仅静态类型层生效）。
- NFR2: Protocol 文档与定义应可维护：单文件建议不超过 800 行，超过则按领域拆分。
- NFR3: 类型检查门禁应支持增量执行，单次 CI 增量检查目标不超过 3 分钟。

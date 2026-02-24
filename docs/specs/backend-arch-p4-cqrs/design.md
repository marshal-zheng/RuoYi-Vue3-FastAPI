# CQRS 读写分离技术设计

## 架构概述

P4 采用“控制器仅分发 + Handler 承担用例”目标态：

- 写路径：Controller -> Command -> CommandHandler。
- 读路径：Controller -> Query -> QueryHandler。
- Mediator/Dispatcher 作为唯一分发入口。
- 横切逻辑由 Pipeline 统一处理（验证、鉴权、日志、事务）。
- 旧式“控制器直调上帝 Service”模式不保留。
- 本阶段范围：优先落地系统管理域（`config/dict/dept/menu/post/notice`），`simulation/protocol/device` 后续单独迭代。

## 数据流图

```mermaid
flowchart TD
    REQ[Request] --> CTL[Controller]
    CTL --> CMD[Command/Query]
    CMD --> MED[Mediator]
    MED --> VB[Validation]
    VB --> AB[Auth/Audit]
    AB --> TB[Transaction(write)]
    TB --> HD[Handler]
    HD --> RES[CommandResult/ReadModel]
    RES --> CTL
    CTL --> RSP[Response]
```

## 组件与接口定义

- `application/commands/*.py`
- `application/queries/*.py`
- `application/handlers/command/*.py`
- `application/handlers/query/*.py`
- `application/behaviors/*.py`
- `application/mediator.py`
- `application/read_models/*.py`

核心接口：

- `ICommandHandler[TCommand, TResult]`
- `IQueryHandler[TQuery, TResult]`
- `IPipelineBehavior[TRequest, TResult]`

强约束：

- Controller 不得直接调用 Repository/领域写入逻辑。
- 新增写能力必须通过 CommandHandler。
- 新增读能力必须通过 QueryHandler + ReadModel。

## API 接口设计

外部 URL 可保持不变，内部执行路径统一：

- 写 API：`mediator.send(command)`
- 读 API：`mediator.query(query)`

错误约定：

- 参数校验失败统一返回验证错误。
- Handler 未注册返回配置错误并记录 handler key。

## 数据模型与数据库变更

- 写模型复用领域实体与仓储。
- 读模型独立 Pydantic DTO，不与写模型共基类。
- 读性能瓶颈时引入投影表或视图（增量迁移）。

事务策略：

- 写路径由事务行为托管。
- 读路径只读执行，无写提交。

## 安全考量

- Pipeline 前置执行鉴权，禁止绕过。
- Query 必须参数化，禁止字符串拼接 SQL。
- ReadModel 最小字段暴露，避免敏感数据泄漏。

## 测试策略

- 单元测试：
  - Handler 行为与 Pipeline 顺序。
- 集成测试：
  - Controller -> Mediator -> Handler 链路。
- 回归测试：
  - 与改造前 API 契约一致性。
- 性能测试：
  - 读路径 P95 和慢查询监控验证。

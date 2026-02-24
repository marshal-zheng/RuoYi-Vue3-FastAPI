# 依赖注入容器技术设计

## 架构概述

P2 采用“组合根统一装配 + 构造器注入 + 请求级会话”的目标态实现：

- 启动时构建唯一应用容器，注册全部 Provider。
- 控制器依赖由容器解析，不再手写业务实例化。
- Service 全量改为实例方法 + 构造器注入，不保留 classmethod 服务模式。
- 事务边界继续由 `get_db()` 与事务装饰器管理。
- 当请求内已存在事务时，事务管理器默认使用 savepoint 执行嵌套事务，确保内层异常回滚不污染外层事务。

## 本轮范围调整

- 生效日期：2026-02-21。
- 暂缓模块：`simulation`、`protocol`、`device*`（含对应 controller/service/repository 的全链路改造与补测）。
- 验收口径：本轮 DI 迁移与门禁收敛以非暂缓模块为准；暂缓模块在后续里程碑独立验收。

## 数据流图

```mermaid
flowchart TD
    L[FastAPI Lifespan] --> C[Build AppContainer]
    C --> P[Register Providers]
    R[HTTP Request] --> DB[get_db -> AsyncSession]
    R --> D[Depends(Provide[Container.xxx_service])]
    D --> S[Service Instance]
    S --> RF[Repository Factory(session)]
    RF --> SQL[(DB)]
    T[Tests] --> O[container.override]
    O --> S
```

## 组件与接口定义

- `container/app_container.py`
: 声明基础设施、仓储工厂、服务工厂 Provider。
- `container/wiring.py`
: 应用 wiring 与启动绑定校验。
- `container/providers.py`
: 按模块拆分 provider 定义，避免单文件膨胀。
- `module_admin/service/*`
: 全量改造为构造器注入，不允许静态业务入口。
- `tests/conftest.py`
: 容器覆盖、reset 与 fixture 生命周期管理。

约束：

- Controller 层禁止 `Service(query_db)` 直接实例化。
- Service 内禁止 `Repository(query_db)` 即时 new。
- 新增代码必须通过容器依赖图注册。

## API 接口设计

不新增业务 API，统一依赖注入入口：

- `Depends(Provide[Container.xxx_service])` 作为标准注入形式。
- `build_container(settings)` 在启动阶段执行。
- `validate_container_bindings(container)` 在启动阶段失败即中断。

测试入口：

- `container.override(provider, fake)`
- `container.reset_override()`

## 数据模型与数据库变更

P2 无数据库 schema 变更。

生命周期模型：

- Database Session：请求级。
- Redis/缓存/调度器：应用级单例。
- Service/Repository：由容器工厂按请求解析。

## 安全考量

- 容器配置统一从环境读取，不在代码内硬编码凭据。
- 启动期即校验依赖绑定，避免运行时注入失败。
- 测试覆盖必须 reset，防止跨用例污染导致权限与行为漂移。

## 测试策略

- 单元测试：
  - 对服务进行构造器注入 mock 测试。
  - 验证 override/reset 生命周期。
- 集成测试：
  - 关键路由验证容器注入链路与事务边界。
- 架构测试：
  - CI 阻断新增 classmethod 业务服务与业务层直接实例化依赖。
- 性能基线：
  - 基线快照归档在 `docs/specs/backend-arch-p2-dependency-injection/baselines/performance-baseline-2026-02-21.md`。

<!-- Updated: 2026-02-11 -->
# 数据与迁移 Codemap

> 数据层由 SQLAlchemy DO/VO、Repository 抽象、Alembic 迁移与 YAML 种子数据共同组成，覆盖从模型定义到环境初始化的全链路。

## ORM 模型层（DO/VO）

**用途：** 定义持久化对象与对外数据结构，作为业务与数据库之间的稳定契约。

**关键文件：**
- `ruoyi-fastapi-backend/module_admin/entity/do/base.py` — ORM 基础字段与基类。
- `ruoyi-fastapi-backend/module_admin/entity/do/*.py` — 业务持久化模型（用户、角色、菜单、项目、仿真等）。
- `ruoyi-fastapi-backend/module_admin/entity/vo/*.py` — 业务返回模型与请求/响应对象。
- `ruoyi-fastapi-backend/module_generator/entity/do/gen_do.py` — 代码生成域模型。
- `ruoyi-fastapi-backend/module_generator/entity/vo/gen_vo.py` — 代码生成域 VO。

**依赖关系：** Repository 依赖 DO 进行查询/写入；Controller/Service 依赖 VO 组织输入输出；Alembic 通过导入 DO 聚合 `Base.metadata`。

**架构模式：** DO 与 VO 分离；模型按业务域拆分；共享基类统一字段语义。

## 数据访问抽象与查询策略

**用途：** 将业务逻辑与底层 SQL 细节隔离，统一数据访问规范。

**关键文件：**
- `ruoyi-fastapi-backend/module_admin/repository/base_repository.py` — 通用仓储基类。
- `ruoyi-fastapi-backend/module_admin/repository/query_builder.py` — 动态查询构造。
- `ruoyi-fastapi-backend/module_admin/repository/specification.py` — 查询规格抽象。
- `ruoyi-fastapi-backend/docs/REPOSITORY_LAYER_POLICY.md` — 仓储层治理规则。

**依赖关系：** Service 仅依赖 Repository；Repository 依赖 `config/database.py` 的 Session 与 `entity/do`；CI 通过脚本检查禁止运行时回流 DAO。

**架构模式：** Repository 模式；查询构建器；架构约束自动化守卫。

## 数据库连接与事务边界

**用途：** 统一数据库 URL、连接池策略、会话生命周期与测试隔离策略。

**关键文件：**
- `ruoyi-fastapi-backend/config/env.py` — 数据库与连接池配置源。
- `ruoyi-fastapi-backend/config/database.py` — 异步引擎、SessionMaker、软删除过滤初始化。
- `ruoyi-fastapi-backend/config/get_db.py` — 请求事务提交/回滚与测试内存库切换。
- `ruoyi-fastapi-backend/server.py` — 启动阶段 `init_create_table()` 与运行时状态挂载。

**依赖关系：** `get_db.py` 依赖 `database.py`；业务 Repository/Service 通过依赖注入获取 Session；应用生命周期负责初始化与释放连接资源。

**架构模式：** 异步会话工厂；请求级事务管理；测试环境可替换数据源。

## Alembic 迁移体系

**用途：** 管理数据库结构演进，支持多环境升级与回滚。

**关键文件：**
- `ruoyi-fastapi-backend/alembic/env.py` — 迁移环境配置、模型导入与在线/离线迁移。
- `ruoyi-fastapi-backend/alembic/versions/*.py` — 版本化迁移脚本。
- `ruoyi-fastapi-backend/alembic.ini` — Alembic 主配置。
- `ruoyi-fastapi-backend/scripts/check_migration_drift.py` — 迁移漂移检查。

**依赖关系：** `alembic/env.py` 依赖 `config/env.py` 和 `module_admin/entity/do/*`；CI 依赖漂移检查脚本与迁移命令验证变更可执行性。

**架构模式：** 版本化迁移；在线/离线双模式；结构漂移门禁。

## 种子数据与初始化流程

**用途：** 用可维护的 YAML 声明初始化基础数据，支持环境覆盖与幂等执行。

**关键文件：**
- `ruoyi-fastapi-backend/scripts/seed_data.py` — 种子数据装载主流程。
- `ruoyi-fastapi-backend/scripts/seed_data/manifest.yaml` — 加载顺序、表映射、主键映射。
- `ruoyi-fastapi-backend/scripts/seed_data/base/*.yaml` — 基础种子数据。
- `ruoyi-fastapi-backend/scripts/seed_data/overlays/*.yaml` — 环境差异覆盖数据。
- `ruoyi-fastapi-backend/sql/*.sql` — 初始化 SQL 与增量脚本。

**依赖关系：** `seed_data.py` 依赖 ORM 模型与 `config/database.py`；根目录 `scripts/setup.sh`/`scripts/start.sh` 依赖 `sql/*.sql` 初始化或增量更新数据库。

**架构模式：** Base + Overlay 数据分层；按依赖顺序加载；脚本化初始化流程。

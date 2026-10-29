<!-- Updated: 2026-10-27 -->
# 后端架构 Codemap

> 后端以 FastAPI 为核心，采用 Controller -> Service -> Repository 分层并内建缓存、审计、追踪、指标等横切能力。

## 应用装配与生命周期

**用途：** 统一应用启动、依赖初始化、路由挂载与关闭清理。

**关键文件：**
- `ruoyi-fastapi-backend/app.py` — Uvicorn 启动入口。
- `ruoyi-fastapi-backend/server.py` — FastAPI 实例、生命周期（含文件资产存储归属核对）、健康检查（`/health/file-assets`）、Prometheus 输出、路由注册。旧 `/profile` 静态挂载已随文件资产硬切换删除。

**依赖关系：** `server.py` 依赖 `config/*` 初始化数据库/Redis/调度器；依赖 `middlewares/handle.py` 与 `exceptions/handle.py` 注入横切逻辑；通过 `modules/registry.py` 注册 API 并应用模块能力门禁。

**架构模式：** 集中式应用装配；生命周期内聚初始化；路由聚合注册。

## 配置与基础设施层

**用途：** 提供环境变量、数据库连接、会话管理、缓存与调度基础能力。

**关键文件：**
- `ruoyi-fastapi-backend/config/env.py` — 应用、数据库、Redis、限流、幂等等配置模型。
- `ruoyi-fastapi-backend/config/database.py` — SQLAlchemy 异步引擎与 Session 构建。
- `ruoyi-fastapi-backend/config/get_db.py` — 请求级数据库会话与测试环境替代策略。
- `ruoyi-fastapi-backend/config/get_redis.py` — Redis 连接池与系统缓存初始化。
- `ruoyi-fastapi-backend/config/get_scheduler.py` — 系统任务调度器初始化与关闭。

**依赖关系：** 业务服务通过 `get_db`/`get_redis` 获取基础依赖；`server.py` 在生命周期中将缓存、监控、状态对象挂入 `app.state`。

**架构模式：** 配置对象集中管理；异步数据库访问；测试环境替身资源（如内存 DB/假 Redis）。

## 业务域 `module_admin`

**用途：** 承载系统管理、工程、设备、协议、仿真等核心业务能力。

**关键文件：**
- `ruoyi-fastapi-backend/module_admin/controller/*.py` — API 控制层，处理请求参数与响应。
- `ruoyi-fastapi-backend/module_admin/service/*.py` — 业务规则、流程编排、领域协同。
- `ruoyi-fastapi-backend/module_admin/repository/*.py` — 数据访问抽象与查询构造。
- `ruoyi-fastapi-backend/module_admin/entity/do/*.py` — 持久化模型（SQLAlchemy DO）。
- `ruoyi-fastapi-backend/module_admin/entity/vo/*.py` — 对外数据结构（VO）。
- `ruoyi-fastapi-backend/module_admin/shared/` — 共享响应与错误码定义。

**依赖关系：** Controller 调用 Service；Service 调用 Repository；Repository 依赖 `entity/do` 与 `config/database.py`；VO 与共享响应被 Controller/Service 共同使用。

**架构模式：** 严格分层；仓储模式（Repository）；DO/VO 分离；领域子模块化（用户、角色、项目、仿真等）。

## Dashboard 文档持久化 `modules/system`

**用途：** 为账号布局与工程场景共享布局提供带修订号的持久化边界。

**关键文件：**
- `ruoyi-fastapi-backend/modules/registry.py` — 将 Dashboard API 注册到 system/platform 能力门禁。
- `ruoyi-fastapi-backend/modules/system/api/dashboard_controller.py` — 布局读写删除入口与 409 冲突响应。
- `ruoyi-fastapi-backend/modules/system/application/services/dashboard_service.py` — 认证账号隔离、工程存在性及项目查询/编辑权限校验。
- `ruoyi-fastapi-backend/modules/system/infrastructure/dashboard_repository.py` — 条件写入、版本快照与删除墓碑。
- `ruoyi-fastapi-backend/module_admin/entity/do/dashboard_do.py`、`ruoyi-fastapi-backend/module_admin/entity/vo/dashboard_vo.py` — 当前文档/版本存储与有界 JSON 请求契约。
- `ruoyi-fastapi-backend/alembic/versions/20261017_add_dashboard.py` — Dashboard 两表迁移。

**依赖关系：** API 复用 identity、请求级数据库会话及容器 project 服务；模型接入 Alembic/Atlas。前端共享 `PersistentDashboard.vue` 负责布局冲突交互，server monitor 通过标准 widget 包提供真实数据。

**架构模式：** 服务端派生身份；共享场景校验全局项目权限；文档与版本同事务提交；删除清空内容/历史并保留递增计数，防止旧版本覆盖重建文档。

## 文件资产 `modules/file_assets`

**用途：** 私有 S3 兼容桶上的文件资产：后端代理上传与校验、业务同事务绑定、同源流式读取、按状态回收与孤儿清扫。规格见 `docs/specs/file-assets-minio/`，运维见同目录 `runbook.md`。

**关键文件：**
- `ruoyi-fastapi-backend/modules/file_assets/api/file_asset_controller.py`、`api/http.py` — 上传、元数据、内容流（ETag/304、强制下载）与草稿丢弃。
- `ruoyi-fastapi-backend/modules/file_assets/application/asset_service.py` — 上传提交点（UPLOADING → READY）、配额、读取授权。
- `ruoyi-fastapi-backend/modules/file_assets/application/binding_service.py` — `replace_field_assets` / `release_owner`，只 flush 不提交。
- `ruoyi-fastapi-backend/modules/file_assets/application/cleanup_service.py`、`jobs.py` — 草稿/上传回收、删除任务（租约与退避）、孤儿清扫、墓碑清除。
- `ruoyi-fastapi-backend/modules/file_assets/application/runtime.py` — 槽位、存储归属三态、健康与指标。
- `ruoyi-fastapi-backend/modules/file_assets/application/validation/` — 图片规范化、Office/PDF/文本受限校验。
- `ruoyi-fastapi-backend/modules/file_assets/infrastructure/s3_storage.py`、`bootstrap.py` — 三套 Boto3 client、建桶与安装标识。
- `ruoyi-fastapi-backend/modules/system/application/file_asset_policies.py`、`container/file_asset_policies.py` — 头像/公告归属策略与登记（生成业务的策略由生成器产出）。
- `ruoyi-fastapi-backend/modules/system/application/notice_content.py`、`user_avatars.py` — 公告 HTML 净化与引用绑定、头像替换。
- `ruoyi-fastapi-backend/middlewares/upload_limit_middleware.py`、`middlewares/route_path.py` — multipart 解析前的请求体上限；按去掉 root_path 的路径匹配 CSRF/限流。
- `ruoyi-fastapi-backend/scripts/file_assets.py` — bootstrap-storage、check-storage、retry-deletes、check-consistency、sweep-orphans。

**依赖关系：** 业务模块通过 `AssetOwnerPolicy` 提供权限与归属，文件模块不导入业务 controller；读写都在业务请求事务内调用绑定服务；维护任务经现有 sys_job 调度（禁止并发）。

**架构模式：** 资产行是唯一真源；上传门禁 + 按状态删除 + 孤儿清扫代替逐次写入证据；对象键 `assets/YYYY/MM/<asset_id>` 不复用；存储仅后端可达，浏览器只访问同源 `/file-assets/`。

## 代码生成域 `module_generator`

**用途：** 基于数据表定义自动生成前后端模板代码。

**关键文件：**
- `ruoyi-fastapi-backend/module_generator/controller/gen_controller.py` — 代码生成入口 API。
- `ruoyi-fastapi-backend/module_generator/service/gen_service.py` — 生成流程编排。
- `ruoyi-fastapi-backend/module_generator/repository/gen_repository.py` — 元数据查询。
- `ruoyi-fastapi-backend/module_generator/templates/` — Python/Vue/SQL/JS 模板集合。

**依赖关系：** 生成服务依赖 `module_generator/repository` 获取库表元信息，并渲染 `templates/` 输出代码内容。

**架构模式：** 模板驱动生成；控制层与生成逻辑分离。

## 横切能力与公共层

**用途：** 统一处理非功能性需求，包括异常、中间件、观测与安全控制。

**关键文件：**
- `ruoyi-fastapi-backend/middlewares/handle.py` — 中间件顺序编排（限流、幂等、追踪、日志等）。
- `ruoyi-fastapi-backend/exceptions/handle.py` — 全局异常处理注册。
- `ruoyi-fastapi-backend/utils/` — 响应封装、日志、追踪、审计、缓存、查询监控等工具。
- `ruoyi-fastapi-backend/docs/REPOSITORY_LAYER_POLICY.md` — 仓储层约束与治理规则。

**依赖关系：** 全局中间件与异常处理由 `server.py` 装配；`utils/*` 被 controller/service/repository 广泛复用；治理脚本由 CI 调用以防架构回退。

**架构模式：** 横切关注点集中化；可观测性默认开启；架构约束脚本化治理。

## 质量保障与回归测试

**用途：** 使用测试与静态检查防止核心链路回归。

**关键文件：**
- `ruoyi-fastapi-backend/tests/unit/` — 单元测试（中间件、服务、控制器等）。
- `ruoyi-fastapi-backend/tests/integration/` — 集成测试（核心业务链路与错误处理）。
- `ruoyi-fastapi-backend/scripts/db.py` — 统一数据库工作流入口。
- `ruoyi-fastapi-backend/docs/REPOSITORY_LAYER_POLICY.md` — 仓储层约束说明。

**依赖关系：** 开发与部署主链路依赖 `db.py` 与 `tests/*`；历史治理脚本已移出当前仓库，不再属于默认日常路径。

**架构模式：** 分层测试策略；规则脚本前置；回归集优先覆盖核心模块。

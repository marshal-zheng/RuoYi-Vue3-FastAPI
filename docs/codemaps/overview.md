<!-- Updated: 2026-02-11 -->
# 系统总览 Codemap

> 该仓库是 Vue3 前端 + FastAPI 后端的前后端分离架构，围绕系统管理、工程拓扑与仿真场景构建。

## 可部署单元

**用途：** 划分运行边界与协作接口，明确主应用和基础设施关系。

**关键文件：**
- `ruoyi-fastapi-backend/app.py` — 后端进程启动入口（Uvicorn）。
- `ruoyi-fastapi-backend/server.py` — FastAPI 应用装配、生命周期、路由注册与健康检查。
- `ruoyi-fastapi-frontend/src/main.ts` — 前端应用入口，注册路由、状态、插件与全局组件。
- `ruoyi-fastapi-frontend/src/router/index.js` — 路由静态表与权限动态路由定义。
- `docker-compose.yml` — 前后端 + MySQL + Redis 的容器编排。

**依赖关系：** 前端通过 `src/api/*` 调用后端 REST 接口；后端依赖 `module_admin` 与 `module_generator` 提供业务能力；`docker-compose.yml` 将 MySQL/Redis 与后端纳入同一网络供前端反向代理访问。

**架构模式：** 前后端分离；单后端多业务模块聚合；容器化部署与本地脚本双运行路径。

## 后端边界与职责

**用途：** 描述 FastAPI 应用内部的分层协作与横切能力。

**关键文件：**
- `ruoyi-fastapi-backend/server.py` — 聚合控制器、中间件、异常处理、指标与健康端点。
- `ruoyi-fastapi-backend/config/` — 环境变量、数据库、Redis、调度器配置。
- `ruoyi-fastapi-backend/module_admin/` — 主业务域（系统管理、工程/设备/协议/仿真）。
- `ruoyi-fastapi-backend/module_generator/` — 代码生成业务与模板。
- `ruoyi-fastapi-backend/middlewares/handle.py` — 中间件装配顺序（限流、幂等、追踪、日志等）。

**依赖关系：** `server.py` 组装 `config`、`module_admin`、`module_generator`、`middlewares`、`exceptions`；业务层依赖 `repository` 与 `entity`；全局工具依赖 `utils` 提供日志、响应、追踪、缓存能力。

**架构模式：** Controller -> Service -> Repository 分层；配置集中化；可观测性内建（metrics/tracing/logging）。

## 前端边界与职责

**用途：** 描述 Vue3 应用的路由权限、页面与 API 访问链路。

**关键文件：**
- `ruoyi-fastapi-frontend/src/main.ts` — 应用初始化、UI 库和全局工具注册。
- `ruoyi-fastapi-frontend/src/permission.ts` — 导航守卫、鉴权与动态路由注入。
- `ruoyi-fastapi-frontend/src/store/modules/permission.ts` — 基于后端菜单生成路由树。
- `ruoyi-fastapi-frontend/src/api/` — 按域拆分的接口调用层。
- `ruoyi-fastapi-frontend/src/views/` — 系统管理、工程、仿真、设备等页面模块。

**依赖关系：** `permission.ts` 依赖 `store/modules/user` 与 `store/modules/permission`；页面组件依赖 `api/*` 和 `components/business/*`；HTTP 请求最终统一经 `utils/request.ts`。

**架构模式：** 页面域驱动目录；Pinia 状态管理；动态路由 + 菜单权限；插件化全局能力注入。

## 运行与质量保障

**用途：** 归纳开发启动、CI 检查与回归守卫，保证架构约束落地。

**关键文件：**
- `scripts/setup.sh` — 本地一键环境准备（MySQL/Redis/依赖安装）。
- `scripts/start.sh` — 本地前后端联动启动与 SQL 增量执行。
- `.gitlab-ci.yml` — 主合并门禁（安全脚本、迁移漂移与架构回归测试）。
- `.github/workflows/ci.yml` — GitHub 侧手动触发 CI（前后端构建/检查）。

**依赖关系：** CI 脚本依赖 `ruoyi-fastapi-backend/scripts/*` 执行架构与安全规则检查；本地脚本依赖前后端各自运行入口与数据库初始化 SQL。

**架构模式：** 脚本化环境初始化；多管线质量门禁；架构规则自动化校验（如禁止 DAO 回流）。

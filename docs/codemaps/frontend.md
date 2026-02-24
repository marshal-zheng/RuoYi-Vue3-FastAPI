<!-- Updated: 2026-02-11 -->
# 前端架构 Codemap

> 前端基于 Vue3 + Vite + Pinia，采用“路由权限驱动 + 业务域视图拆分 + 统一 HTTP 客户端”的结构。

## 应用入口与运行时装配

**用途：** 完成 UI 框架、插件、全局组件与运行模式初始化。

**关键文件：**
- `ruoyi-fastapi-frontend/src/main.ts` — 应用创建、Element Plus/ZXUI、全局组件与 mock 启动逻辑。
- `ruoyi-fastapi-frontend/src/App.tsx` — 应用根组件。
- `ruoyi-fastapi-frontend/src/plugins/index.js` — 全局工具插件注册（auth/tab/cache/modal/http/download）。

**依赖关系：** `main.ts` 依赖 `router`、`store`、`plugins`、`directive`；全局能力统一注入页面与组合式逻辑。

**架构模式：** 入口集中注册；插件化能力注入；环境开关驱动的 mock 启动。

## 路由与权限控制

**用途：** 管理静态路由、动态菜单路由与导航守卫。

**关键文件：**
- `ruoyi-fastapi-frontend/src/router/index.js` — 常量路由与权限动态路由配置。
- `ruoyi-fastapi-frontend/src/permission.ts` — 登录态校验、菜单拉取、动态路由注入。
- `ruoyi-fastapi-frontend/src/store/modules/permission.ts` — 后端路由树转换与前端组件映射。

**依赖关系：** `permission.ts` 调用 `store/modules/user` 获取用户信息，调用 `store/modules/permission` 生成路由；`store/modules/permission.ts` 依赖 `api/menu.ts` 获取菜单数据并使用 `router.addRoute` 注入。

**架构模式：** 前后端协同 RBAC；运行时动态路由；首菜单路径自动决策。

## 状态与会话管理

**用途：** 管理全局业务状态、界面状态与用户会话。

**关键文件：**
- `ruoyi-fastapi-frontend/src/store/index.ts` — Pinia 实例。
- `ruoyi-fastapi-frontend/src/store/modules/user.ts` — 登录态与用户信息。
- `ruoyi-fastapi-frontend/src/store/modules/settings.ts` — 主题与标题等界面配置。
- `ruoyi-fastapi-frontend/src/store/modules/tagsView.ts` — 多页签状态。

**依赖关系：** 权限模块与用户模块互相协作决定可访问页面；设置模块由路由守卫和布局组件共同消费。

**架构模式：** 模块化 Pinia store；会话与 UI 状态分离。

## API 与 HTTP 抽象层

**用途：** 统一接口调用方式，按业务域组织 API 模块。

**关键文件：**
- `ruoyi-fastapi-frontend/src/api/_shared/http-client.ts` — 类型安全 HTTP 包装。
- `ruoyi-fastapi-frontend/src/utils/request.ts` — 请求兼容层、错误处理与下载能力。
- `ruoyi-fastapi-frontend/src/api/system/*.ts` — 系统管理接口。
- `ruoyi-fastapi-frontend/src/api/project/*.ts` — 工程与拓扑接口。
- `ruoyi-fastapi-frontend/src/api/simulation/simulation.ts` — 仿真相关接口。

**依赖关系：** 业务 API 依赖 `_shared/http-client.ts` 与 `utils/request.ts`；页面层只依赖 `api/*` 不直接操作底层 HTTP 细节。

**架构模式：** API 分域管理；请求层向下兼容；统一错误与下载处理。

## 视图与业务组件

**用途：** 按业务域组织页面和可复用业务组件。

**关键文件：**
- `ruoyi-fastapi-frontend/src/views/system/` — 用户/角色/菜单/字典等系统管理页面。
- `ruoyi-fastapi-frontend/src/views/project/` — 工程管理、拓扑编辑、仿真监控页面。
- `ruoyi-fastapi-frontend/src/views/device/` — 设备与分类页面。
- `ruoyi-fastapi-frontend/src/components/business/` — 业务组件（如 DAG、字典输入组件）。
- `ruoyi-fastapi-frontend/src/layout/` — 布局框架与壳层组件。

**依赖关系：** `views/*` 调用 `api/*`，复用 `components/business/*` 与 `components/ui/*`；`layout/*` 承载路由页面容器和全局导航。

**架构模式：** 领域页面聚合；业务组件复用；布局与业务解耦。

## 开发工具与测试支持

**用途：** 提供 Mock 能力、构建插件与测试配置，支撑开发与验证。

**关键文件：**
- `ruoyi-fastapi-frontend/src/mocks/` — MSW mock handlers/factories/scenarios。
- `ruoyi-fastapi-frontend/vite/plugins/*.ts` — Vite 插件集合（自动导入、svg、压缩等）。
- `ruoyi-fastapi-frontend/vitest.config.ts` — 测试与覆盖率门槛配置。
- `ruoyi-fastapi-frontend/tests/` — 前端测试入口与用例。

**依赖关系：** `main.ts` 根据环境变量按需加载 `src/mocks`；构建流程依赖 `vite/plugins`；测试运行依赖 Vitest 配置。

**架构模式：** 开发/测试环境隔离；构建能力插件化；覆盖率门槛治理。

# 前端离线演示 Runtime 实现任务

- [x] 1. 建立运行模式与构建基线
  - 新增 `VITE_APP_RUNTIME_MODE` 解析器，明确支持 `real`、`fallback`、`demo-offline` 三种模式，并兼容现有 `VITE_ENABLE_MOCK` 映射。
  - 调整 [main.ts](/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/main.ts) 与现有 MSW 启动入口，确保 `fallback` 与 `demo-offline` 各自走单一职责路径。
  - 新增 `.env.demo-offline`、`build:demo-offline`、`preview:demo-offline`，并校正构建入口与文档声明一致。
  - 优先修复当前构建阻塞项，例如 `@zxio/zxui/style` 导出解析问题，确保 `build:prod` 与 `build:demo-offline` 都具备可验证基础。
  _需求追溯: R1.AC1, R1.AC2, R1.AC3, R1.AC4, R2.AC1, R8.AC3_

- [x] 2. 落地 demo runtime 启动编排与运行边界
  - 创建 `src/demo/runtime/**`，集中编排数据库初始化、场景导入、demo handler 注册和运行态调试信息。
  - 为 `demo-offline` 增加 API 前缀级 catch-all handler，未覆盖 `/api/**` 请求统一返回确定性 demo 错误，禁止静默穿透真实网络。
  - 在 `demo-offline` 且 debug 开启时暴露只读 `window.__DEMO_RUNTIME__`，提供模式识别、场景识别、重置和导出入口；`real` 与 `fallback` 不暴露该接口。
  - 增加运行模式标识、请求来源日志和场景切换日志，便于区分真实响应、fallback 响应和离线演示响应。
  _需求追溯: R1.AC2, R3.AC3, R3.AC4, R5.AC1, R8.AC1, R8.AC2_

- [x] 3. 实现场景包 schema、Dexie 数据库与仓储层
  - 引入 Dexie，并建立 `meta`、认证、菜单、项目、版本、拓扑、仿真、序列号等表结构及版本迁移机制。
  - 定义标准场景包 schema、版本字段、指纹字段和兼容校验逻辑，禁止 AI 或人工输入直接绕过 schema 落库。
  - 实现默认场景导入、显式重置、场景切换、场景导出和首次打开自动导入逻辑，确保切换过程使用事务避免新旧数据混杂。
  - 抽象 `AuthRepository`、`SystemRepository`、`ProjectRepository`、`ProjectVersionRepository`、`TopologyRepository`、`SimulationRepository`、`ScenarioRepository`，统一 IndexedDB 访问边界。
  - 建立本地自增 ID/序列号机制，避免刷新页面后项目、版本和仿真实体主键冲突。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R5.AC3, R7.AC1, R7.AC2, R7.AC3, R7.AC4_

- [x] 4. 实现离线登录、会话恢复与菜单基础数据链路
  - 以场景包账号为数据源实现 `captchaImage`、`login`、`getInfo`、`auth/logout`、`auth/refresh`、`auth/csrf-token` 等 handler/service/repository。
  - 对齐现有 [user.ts](/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/store/modules/user.ts) 与 [permission.ts](/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/permission.ts) 的会话恢复和菜单加载流程，尽量不改页面与 API 签名。
  - 实现 `getRouters`、字典数据、部门树等登录后基础接口，保证登录页、首页和导航页在 `demo-offline` 下稳定进入。
  - 保持现有业务页面“无感知数据来源”，页面继续通过现有请求入口获取数据，不新增页面层分支判断。
  _需求追溯: R2.AC5, R2.AC6, R3.AC1, R3.AC2, R5.AC1, R5.AC2, R6.AC1, R7.AC5_

- [x] 5. 实现项目、版本与拓扑的离线 CRUD 主链路
  - 为项目模块补齐 `/project/list`、`/project/:id`、新增、编辑、删除、导出占位等离线 handler/service/repository。
  - 为版本模块补齐 `/project/version/list`、详情、新增、编辑、删除、克隆、固化、解固化等离线能力。
  - 为拓扑模块补齐读取与保存接口，确保项目与版本维度下的拓扑数据可持久化回写 IndexedDB。
  - 保证刷新页面、重新进入地址后仍能看到客户刚刚执行的 CRUD 结果，不因重新加载而回退到内存初值。
  - 对响应结构进行兼容适配，确保现有页面、表格和表单不需要重写即可消费 demo 数据。
  _需求追溯: R2.AC2, R2.AC3, R2.AC5, R3.AC1, R3.AC2, R4.AC1, R4.AC5, R5.AC1, R5.AC2, R6.AC1_

- [x] 6. 实现仿真只读 HTTP 演示接口
  - 为仿真页面补齐会话创建、状态查询、报文列表、带宽、告警、故障、事件等只读 HTTP 接口，数据来源为场景包预置内容或本地只读会话。
  - 对首期不支持的仿真控制接口统一返回 `501 DEMO_NOT_SUPPORTED`，确保页面行为明确且不会触发真实后端访问。
  - 保持返回结构与现有仿真页面消费模型兼容，避免在页面层做 demo 特判。
  _需求追溯: R2.AC5, R5.AC1, R5.AC2, R6.AC1, R6.AC4, R6.AC5_

- [x] 7. 实现仿真 WebSocket 票据与只读事件流
  - 实现 `POST /auth/ws-ticket` 的本地签发与校验逻辑，记录 `sessionId`、过期时间与单次使用状态。
  - 优先使用 MSW 官方 `ws.link` / `WebSocketHandler` 接入 `/simulation/sessions/:sessionId/ws`，不采用全局 monkey patch。
  - 建立 `DemoRealtimeStream` 调度器，按场景包 `streamFrames` 推送 `status`、`messages`、`bandwidth`、`alarms`、`animation`、`faults`、`pong`。
  - 如果浏览器环境下 MSW WebSocket 拦截存在兼容性问题，则仅在显式 `SimulationRealtimeTransport` 抽象内做降级，不修改业务页面的 WebSocket 消费模型。
  - 实现连接关闭清理、ping/pong 和只读连接生命周期控制，避免 timer、票据和连接状态泄漏。
  _需求追溯: R5.AC1, R5.AC2, R6.AC2, R6.AC3, R6.AC4, R6.AC5_

- [x] 8. 补齐文档、场景运维与 AI 扩展边界说明
  - 更新 MSW 与运行模式文档，明确 `real`、`fallback`、`demo-offline` 的职责边界、适用场景和限制。
  - 在文档中明确说明静态部署必须基于 HTTP(S) 服务器，`file://` 不受支持，并给出本地预览方式。
  - 记录默认场景、重置场景、切换场景、导出场景的操作方式，以及后续 AI 只允许生成标准场景包的边界。
  - 说明 demo 账号、菜单权限、场景数据与 IndexedDB 的本地隔离边界，避免被误认为真实生产数据。
  _需求追溯: R2.AC4, R7.AC3, R8.AC3, R8.AC4_

- [ ] 9. 完成测试矩阵与静态产物验收
  - 为运行模式解析、Dexie 仓储、场景导入/重置、认证服务、项目/版本服务、仿真 HTTP/WebSocket handler 补齐单元与集成测试。
  - 增加未实现 API catch-all、会话恢复、页面刷新后数据保留、场景切换不混数、仿真 ping/pong 的关键回归测试。
  - 执行 `yarn lint:check`、`yarn type-check`、`yarn test:run`、`yarn build:prod`、`yarn build:demo-offline`，并通过静态服务预览验证登录、菜单、项目 CRUD、版本 CRUD、拓扑保存和仿真只读实时页。
  - 在“无真实后端进程”前提下完成最终 smoke，确认 `demo-offline` 真正满足裸 `dist-demo-offline` 演示要求。
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R6.AC2, R6.AC3, R8.AC1, R8.AC2, R8.AC3_

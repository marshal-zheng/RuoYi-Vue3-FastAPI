# 前端离线演示 Runtime 运维说明

## 运行模式边界

| 运行模式       | 使用场景               | 边界说明                                                                 |
| -------------- | ---------------------- | ------------------------------------------------------------------------ |
| `real`         | 生产构建、真实后端联调 | 不启动 MSW，不初始化 demo IndexedDB，所有 API/WebSocket 都访问真实服务。 |
| `fallback`     | 本地开发兜底           | 真实后端优先，仅在 `404` 或网络异常时回退到 MSW mock；不适合客户静态演示。 |
| `demo-offline` | 无后端静态演示         | 纯 MSW + IndexedDB 场景包运行，不穿透真实后端；未实现 API 返回确定性 `501`。 |

`VITE_APP_RUNTIME_MODE` 是主控制项，取值只能是 `real`、`fallback`、`demo-offline`。旧变量 `VITE_ENABLE_MOCK` 仅做兼容映射：`off -> real`、`fallback -> fallback`、`pure -> demo-offline`。

## 静态部署

`demo-offline` 产物必须通过 HTTP(S) 服务器访问，不支持直接打开 `file://`。MSW service worker 需要稳定的 origin 和 scope，Vite 静态资源加载、动态导入以及 MSW WebSocket 拦截也都按 HTTP(S) 运行环境设计。

本地预览：

```bash
cd ruoyi-fastapi-frontend
yarn build:demo-offline
yarn preview:demo-offline
```

部署到静态服务器时发布 `dist-demo-offline/`，并确保 SPA 路由回退到 `index.html`。生产构建继续发布 `dist/`。`public/mockServiceWorker.js` 会随构建进入静态根路径，保持与应用同源即可；不需要启动 FastAPI 后端。

## 场景运维

默认场景注册在 `ruoyi-fastapi-frontend/src/demo/scenarios/index.ts`，当前默认包来自 `ruoyi-fastapi-frontend/src/demo/scenarios/default.ts`，场景 id 为 `default`。运行时会按 `VITE_DEMO_SCENARIO_ID` 选择注册场景；未配置时使用 `default`。

首次打开或场景 id、版本、指纹不匹配时，runtime 会把标准场景包导入 `ruoyi-demo-offline` IndexedDB。若场景已匹配，则保留客户在浏览器本地做过的项目、版本、拓扑等演示数据修改。

开启 `VITE_DEMO_RUNTIME_DEBUG=true` 后，`demo-offline` 会暴露调试入口：

```ts
window.__DEMO_RUNTIME__?.getMode()
window.__DEMO_RUNTIME__?.getScenario()
window.__DEMO_RUNTIME__?.getSnapshot()
await window.__DEMO_RUNTIME__?.resetScenario()
await window.__DEMO_RUNTIME__?.exportScenario()
```

- 默认场景：使用 `VITE_DEMO_SCENARIO_ID=default` 或不设置该变量。
- 重置场景：执行 `resetScenario()`，会重新导入当前场景包并清空该场景管理的业务表。
- 切换场景：新增场景包后在 `src/demo/scenarios/index.ts` 注册，并用 `VITE_DEMO_SCENARIO_ID=<scenarioId>` 启动；导入过程使用事务，避免新旧场景数据混杂。
- 导出场景：执行 `exportScenario()`，返回当前 IndexedDB 中的标准 `DemoScenarioPackage` 快照，便于保存为后续场景包素材。

## AI 扩展边界

AI 只能生成或修改符合 `ruoyi-fastapi-frontend/src/demo/scenarios/schema.ts` 的标准 `DemoScenarioPackage`。生成结果必须经过 `validateDemoScenarioPackage` 校验，再通过 `ScenarioRepository` 导入或注册到 `src/demo/scenarios/index.ts`。

AI 不应直接写 IndexedDB，不应绕过 schema 修改仓储表结构，也不应为某个客户场景修改 `src/demo/handlers/**` 的接口语义。需要扩展能力时，先扩展 schema、仓储、服务和 handler 的通用能力，再让场景包只提供数据。

## 本地隔离边界

默认 demo 账号来自场景包：`admin / admin123`，角色为 `admin`，权限为 `*:*:*`。菜单、字典、部门、项目、版本、拓扑、仿真会话与 WebSocket 回放帧也都来自同一个场景包或浏览器本地 IndexedDB。

`demo-offline` 使用的 IndexedDB 数据库名为 `ruoyi-demo-offline`，数据只存在当前浏览器 profile 和 origin 下。登录 token、CSRF token、WebSocket ticket 都是本地演示凭据，不代表真实生产身份或后端会话。

仿真首期是只读演示边界。明确不支持的仿真控制或写操作会返回 `501 DEMO_NOT_SUPPORTED`；未覆盖的 `/api/**` 会被 catch-all 返回 `501 DEMO_API_NOT_IMPLEMENTED`，避免静默访问真实后端。

## MSW Mock 指南

本项目的前端 Mock 能力由 [Mock Service Worker](https://mswjs.io/) 驱动，支持浏览器、Node（单测/SSR）以及纯前端演示多场景统一复用。

### 运行模式

业务级运行模式优先由 `VITE_APP_RUNTIME_MODE` 控制，只有以下三种值：

```bash
VITE_APP_RUNTIME_MODE=real|fallback|demo-offline
```

| 运行模式       | 适用场景                   | MSW 行为                                                                 | 数据来源与限制                                                                                                   |
| -------------- | -------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| `real`         | 生产构建、联调真实后端     | 不启动 MSW                                                               | 所有请求都走真实后端；不初始化 `src/demo/**`、不写入 `ruoyi-demo-offline` IndexedDB。                             |
| `fallback`     | 本地开发补齐缺失接口       | 真实后端优先；`404` 或网络异常时由 `src/mocks/handlers/**` 返回兜底数据  | 可能访问真实后端，不保证完全离线；只用于开发，不用于客户静态演示。                                               |
| `demo-offline` | 无后端静态演示、客户离线包 | 使用 `src/demo/handlers/**` 注册纯 MSW HTTP/WebSocket handler，禁止穿透后端 | 数据来自标准场景包并持久化到 `ruoyi-demo-offline` IndexedDB；未覆盖 `/api/**` 返回 `501 DEMO_API_NOT_IMPLEMENTED`。 |

旧变量 `VITE_ENABLE_MOCK` 仍保留兼容映射：`off -> real`、`fallback -> fallback`、`pure -> demo-offline`。

```bash
VITE_ENABLE_MOCK=off|fallback|pure
```

常用命令：

```bash
yarn dev                 # .env.development 默认 fallback
yarn dev:mock            # demo-offline 开发预览
yarn build:prod          # real 生产构建
yarn build:demo-offline  # demo-offline 静态演示构建，输出 dist-demo-offline/
yarn preview:demo-offline # 预览 dist-demo-offline/
```

`demo-offline` 静态产物输出到 `dist-demo-offline/`，生产构建继续使用 `dist/`。演示产物必须通过 HTTP(S) 服务器访问，不能直接用 `file://` 打开。MSW service worker 需要浏览器 origin 和 scope，Vite 静态资源、动态导入以及 WebSocket 拦截也都按 HTTP(S) 运行环境设计。本地验收请使用 `yarn preview:demo-offline` 或等价静态服务器。

### 目录结构

```
src/mocks/
  handlers/              # 各模块接口 handlers
  factories/             # 数据构造器（faker 等工具）
  scenarios/             # Handler 组合场景（default/pure）
  utils/                 # 响应包装、回退工具
  browser.ts             # 浏览器端 worker 启动封装
  server.ts              # Node/Vitest 使用的 setupServer
  index.ts               # 对外暴露的入口
```

`demo-offline` 的 IndexedDB 场景包、仓储、服务与 handler 位于 `src/demo/**`。`src/mocks/**` 继续承担传统 fallback/pure mock 入口与 Node/Vitest MSW server 能力，两者不要混写业务数据。

### 新增接口 Mock

1. 在 `src/mocks/handlers/<module>.ts` 中添加 handler，示例：

```ts
import { http, HttpResponse } from 'msw'
import { createApiPath } from '../constants'
import { withBackendFallback } from '../utils/with-backend-fallback'
import { resultSuccess } from '../utils/response'

export function createFooHandlers(strategy: MockStrategy) {
  return [
    http.get(createApiPath('/foo'), ({ request }) =>
      withBackendFallback(
        request,
        () => HttpResponse.json(resultSuccess({ foo: 'bar' })),
        { strategy, tag: 'foo:list' }
      )
    )
  ]
}
```

`createApiPath` 会读取 `VITE_APP_BASE_API`，默认统一使用 `/api`，避免 Mock handler 和运行时请求前缀再次分叉。

2. 在 `src/mocks/handlers/index.ts` 中汇总：

```ts
import { createFooHandlers } from './foo'

export function createHandlers(strategy: MockStrategy) {
  return [
    ...createSystemHandlers(strategy),
    ...createUserHandlers(strategy),
    ...createFooHandlers(strategy)
  ]
}
```

### Fallback 策略说明

`withBackendFallback` 会先尝试访问真实后端：

1. 请求成功且状态码非 `404` 时，直接透传真实响应。
2. 状态码为 `404` 或网络异常时，执行 `createMockResponse` 并返回 Mock 数据。

在开发模式下（`import.meta.env.DEV === true`），控制台会打印回退日志，便于确认是走了真实接口还是 Mock。

### Node / 测试环境

如需在单元测试中使用 Mock，可在测试入口引入：

```ts
import { createMockServer } from '@/mocks/server'

const server = createMockServer()

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### 注意事项

- `public/mockServiceWorker.js` 由 `npx msw init public --save` 生成，请勿手动修改。
- 如需彻底禁用 Mock，可在 `.env.local` 或运行环境中设置 `VITE_APP_RUNTIME_MODE=real` 或 `VITE_ENABLE_MOCK=off`。
- 客户静态演示请使用 `demo-offline`，不要使用 `fallback`；`fallback` 会尝试真实后端，只适合开发兜底。
- `demo-offline` 的场景运维、AI 扩展和数据隔离边界见 `docs/specs/frontend-demo-offline-runtime/runbook.md`。
- 旧的 `mock/` 目录已被 MSW 替代，可分阶段迁移或删除。

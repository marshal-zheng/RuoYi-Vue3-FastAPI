## MSW Mock 指南

本项目的前端 Mock 能力由 [Mock Service Worker](https://mswjs.io/) 驱动，支持浏览器、Node（单测/SSR）以及纯前端演示多场景统一复用。

### 运行模式

- `yarn dev`（`mode=development`）  
  `.env.development` 中设置 `VITE_ENABLE_MOCK='fallback'`：优先请求真实后端，返回 `404` 或网络异常时自动降级到 Mock。
- `yarn dev-mock`  
  脚本会通过 `cross-env VITE_ENABLE_MOCK=pure vite` 启动，始终返回 Mock 数据，可完全脱离后端。
- 生产构建 (`yarn build` / `yarn build:stage`)  
  `.env.production` / `.env.staging` 默认 `VITE_ENABLE_MOCK='off'`，如需远程演示可改为 `fallback` 或 `pure`。

单一环境变量即可控制：

```bash
VITE_ENABLE_MOCK=off|fallback|pure
```

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

### 新增接口 Mock

1. 在 `src/mocks/handlers/<module>.ts` 中添加 handler，示例：

```ts
import { http, HttpResponse } from 'msw'
import { withBackendFallback } from '../utils/with-backend-fallback'
import { resultSuccess } from '../utils/response'

export function createFooHandlers(strategy: MockStrategy) {
  return [
    http.get('/dev-api/foo', ({ request }) =>
      withBackendFallback(
        request,
        () => HttpResponse.json(resultSuccess({ foo: 'bar' })),
        { strategy, tag: 'foo:list' }
      )
    )
  ]
}
```

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
- 如需彻底禁用 Mock，可在 `.env.local` 或运行环境中设置 `VITE_ENABLE_MOCK=off`。
- 旧的 `mock/` 目录已被 MSW 替代，可分阶段迁移或删除。

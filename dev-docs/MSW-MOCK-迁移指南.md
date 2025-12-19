# MSW Mock 功能迁移指南

本文档详细说明如何将 MSW (Mock Service Worker) 的 mock 功能迁移到另一个 Vue3 项目中。

## 功能特点

- **三种运行模式**：`off` / `fallback` / `pure`
- **fallback 模式**：优先走真实接口，404 或网络错误时自动降级到 mock
- **pure 模式**：完全脱离后端，全部走 mock
- **打包后可用**：生产环境也可以启用 mock，适合演示
- **支持 Node 环境**：可用于单元测试

---

## 一、安装依赖

```bash
# 核心依赖
npm install msw --save-dev

# 可选：用于生成假数据
npm install @faker-js/faker

# 可选：用于跨平台设置环境变量
npm install cross-env --save-dev
```

---

## 二、初始化 Service Worker

在项目根目录执行：

```bash
npx msw init public --save
```

这会在 `public/` 目录生成 `mockServiceWorker.js` 文件，并在 `package.json` 中添加：

```json
{
  "msw": {
    "workerDirectory": ["public"]
  }
}
```

---

## 三、目录结构

在 `src/` 下创建 `mocks/` 目录，结构如下：

```
src/mocks/
├── browser.ts          # 浏览器端 worker 启动封装
├── server.ts           # Node/Vitest 使用的 setupServer
├── index.ts            # 对外暴露的入口
├── types.ts            # 类型定义
├── handlers/           # 各模块接口 handlers
│   └── index.ts
├── factories/          # 数据构造器（faker 等工具）
│   └── index.ts
├── scenarios/          # Handler 组合场景
│   ├── index.ts
│   ├── default.ts
│   └── pure.ts
└── utils/              # 工具函数
    ├── request.ts      # 请求解析工具
    ├── response.ts     # 响应包装工具
    └── with-backend-fallback.ts  # 核心：回退逻辑
```

---

## 四、核心文件代码

### 4.1 `src/mocks/types.ts`

```typescript
// @ts-nocheck
export type MockStrategy = 'fallback' | 'pure'
export type MockMode = 'off' | MockStrategy

export type MockScenario = 'default' | 'pure'

export type OnUnhandledRequestHandler = (
  request: Request,
  print: {
    info(...args: any[]): void
    warning(...args: any[]): void
    error(...args: any[]): void
  }
) => void

export type OnUnhandledRequestOption = 'bypass' | 'warn' | 'error' | OnUnhandledRequestHandler

export interface StartMockOptions {
  strategy?: MockStrategy
  scenario?: MockScenario
  onUnhandledRequest?: OnUnhandledRequestOption
}
```

### 4.2 `src/mocks/utils/response.ts`

```typescript
// @ts-nocheck
export type Recordable<T = any> = Record<string, T>

export interface ResultOptions {
  msg?: string
}

export interface ErrorOptions<T = null> {
  code?: number
  data?: T
}

export function resultSuccess<T = Recordable>(
  data: T,
  { msg = '操作成功' }: ResultOptions = {}
) {
  return {
    code: 200,
    data,
    msg,
    type: 'success'
  }
}

export function resultError<T = null>(
  msg = '请求失败',
  { code = 500, data = null as T }: ErrorOptions<T> = {}
) {
  return {
    code,
    data,
    msg,
    type: 'error'
  }
}

export function resultPageSuccess<T = any>(
  page: number,
  pageSize: number,
  list: T[],
  { msg = '操作成功' }: ResultOptions = {}
) {
  const pageData = pagination(page, pageSize, list)
  return {
    ...resultSuccess({
      records: pageData,
      total: list.length,
      size: pageSize,
      current: page,
      pages: Math.ceil(list.length / pageSize)
    }),
    msg
  }
}

export function pagination<T = any>(
  pageNo: number,
  pageSize: number,
  array: T[]
): T[] {
  const offset = (pageNo - 1) * Number(pageSize)
  const size = Number(pageSize)
  return offset + size >= array.length
    ? array.slice(offset, array.length)
    : array.slice(offset, offset + size)
}
```

### 4.3 `src/mocks/utils/request.ts`

```typescript
// @ts-nocheck
export function getRequestToken(request: Request): string | undefined {
  const raw = request.headers.get('authorization')
  if (!raw) return undefined
  return raw.replace(/^Bearer\s+/i, '')
}

export async function readJsonBody<T = any>(request: Request): Promise<T | undefined> {
  try {
    return await request.clone().json()
  } catch (error) {
    return undefined
  }
}

export function getSearchParams(request: Request): URLSearchParams {
  const base =
    typeof window === 'undefined'
      ? 'http://localhost'
      : window.location.origin
  const url = request.url.startsWith('http')
    ? new URL(request.url)
    : new URL(request.url, base)
  return url.searchParams
}
```

### 4.4 `src/mocks/utils/with-backend-fallback.ts` ⭐ 核心

```typescript
// @ts-nocheck
import { bypass } from 'msw'

import type { MockStrategy } from '../types'

export interface FallbackOptions {
  strategy: MockStrategy
  tag?: string
}

export async function withBackendFallback(
  request: Request,
  createMockResponse: () => Response | Promise<Response>,
  { strategy, tag }: FallbackOptions
): Promise<Response> {
  // pure 模式：直接返回 mock
  if (strategy === 'pure') {
    const mockResponse = await createMockResponse()
    return markMockResponse(mockResponse, strategy, tag)
  }

  // fallback 模式：先尝试真实接口
  return fetch(bypass(request))
    .then((upstreamResponse) => {
      // 非 404 直接返回真实响应
      if (upstreamResponse.status !== 404) {
        return upstreamResponse
      }
      // 404 时降级为 Mock
      return Promise.resolve(createMockResponse()).then((res: Response) =>
        markMockResponse(res, strategy, tag)
      )
    })
    .catch(() =>
      // 网络错误也降级为 Mock
      Promise.resolve(createMockResponse()).then((res: Response) =>
        markMockResponse(res, strategy, tag)
      )
    )
}

export function markMockResponse(
  response: Response,
  strategy: MockStrategy,
  tag?: string
) {
  const headers = response.headers
  headers.set('X-Mock-Response', 'true')
  headers.set('X-Mock-Mode', strategy)
  if (tag) {
    headers.set('X-Mock-Handler', tag)
  }
  return response
}
```

### 4.5 `src/mocks/handlers/index.ts`

```typescript
// @ts-nocheck
import type { MockStrategy } from '../types'

// 导入各模块的 handlers
// import { createUserHandlers } from './user'
// import { createSystemHandlers } from './system'

export function createHandlers(strategy: MockStrategy) {
  return [
    // ...createUserHandlers(strategy),
    // ...createSystemHandlers(strategy),
  ]
}
```

### 4.6 `src/mocks/scenarios/index.ts`

```typescript
// @ts-nocheck
import type { MockScenario, MockStrategy } from '../types'

import { createDefaultScenarioHandlers } from './default'
import { createPureScenarioHandlers } from './pure'

export function createScenarioHandlers(
  strategy: MockStrategy,
  scenario: MockScenario = 'default'
) {
  if (scenario === 'pure') {
    return createPureScenarioHandlers()
  }

  return createDefaultScenarioHandlers(strategy)
}
```

### 4.7 `src/mocks/scenarios/default.ts`

```typescript
// @ts-nocheck
import type { MockStrategy } from '../types'
import { createHandlers } from '../handlers'

export function createDefaultScenarioHandlers(strategy: MockStrategy) {
  return createHandlers(strategy)
}
```

### 4.8 `src/mocks/scenarios/pure.ts`

```typescript
// @ts-nocheck
import { createHandlers } from '../handlers'

export function createPureScenarioHandlers() {
  return createHandlers('pure')
}
```

### 4.9 `src/mocks/browser.ts`

```typescript
// @ts-nocheck
import { setupWorker, type SetupWorkerApi } from 'msw/browser'

import { createScenarioHandlers } from './scenarios'
import type { MockScenario, MockStrategy, StartMockOptions } from './types'

declare global {
  interface Window {
    __MSW_WORKER__?: SetupWorkerApi
    __MSW_STRATEGY__?: MockStrategy
    __MSW_SCENARIO__?: MockScenario
  }
}

function ensureWorker(
  strategy: MockStrategy,
  scenario: MockScenario
): SetupWorkerApi {
  const handlers = createScenarioHandlers(strategy, scenario)
  const existing = window.__MSW_WORKER__
  if (existing) {
    existing.resetHandlers(...handlers)
    window.__MSW_STRATEGY__ = strategy
    window.__MSW_SCENARIO__ = scenario
    return existing
  }

  const worker = setupWorker(...handlers)
  window.__MSW_WORKER__ = worker
  window.__MSW_STRATEGY__ = strategy
  window.__MSW_SCENARIO__ = scenario
  return worker
}

export async function startBrowserMock(options: StartMockOptions = {}) {
  if (typeof window === 'undefined') {
    return undefined
  }

  const strategy: MockStrategy = options.strategy ?? 'fallback'
  const scenario: MockScenario =
    options.scenario ?? (strategy === 'pure' ? 'pure' : 'default')

  const worker = ensureWorker(strategy, scenario)
  await worker.start({
    onUnhandledRequest: options.onUnhandledRequest ?? 'bypass'
  })
  return worker
}
```

### 4.10 `src/mocks/server.ts` (Node/测试环境)

```typescript
// @ts-nocheck
import { setupServer, type SetupServerApi } from 'msw/node'

import { createScenarioHandlers } from './scenarios'
import type { MockScenario, MockStrategy } from './types'

export function createMockServer(
  strategy: MockStrategy = 'fallback',
  scenario: MockScenario = strategy === 'pure' ? 'pure' : 'default'
): SetupServerApi {
  return setupServer(...createScenarioHandlers(strategy, scenario))
}
```

### 4.11 `src/mocks/index.ts`

```typescript
// @ts-nocheck
import { startBrowserMock } from './browser'
import type {
  MockMode,
  MockScenario,
  MockStrategy,
  StartMockOptions
} from './types'

function resolveModeFromEnv(): MockMode {
  const raw = import.meta.env.VITE_ENABLE_MOCK
  if (raw === 'pure') return 'pure'
  if (raw === 'fallback') return 'fallback'
  return 'off'
}

function resolveScenario(strategy: MockStrategy, scenario?: MockScenario) {
  if (scenario) return scenario
  return strategy === 'pure' ? 'pure' : 'default'
}

export async function setupBrowserMocks(
  options: StartMockOptions = {}
) {
  const mode = resolveModeFromEnv()
  const strategy =
    options.strategy ??
    (mode === 'off' ? undefined : (mode as MockStrategy))

  if (!strategy) {
    return undefined
  }

  const scenario = resolveScenario(strategy, options.scenario)

  return startBrowserMock({
    strategy,
    scenario,
    onUnhandledRequest: options.onUnhandledRequest
  })
}

export { resolveModeFromEnv }
export type { MockMode, MockScenario, MockStrategy, StartMockOptions }
```

---

## 五、修改入口文件 `main.ts`

```typescript
import { createApp } from 'vue'
import App from './App.vue'
// ... 其他 imports

const app = createApp(App)

// ... 其他配置

async function bootstrap() {
  const mockMode = import.meta.env.VITE_ENABLE_MOCK ?? 'off'
  if (mockMode !== 'off') {
    const { setupBrowserMocks } = await import('./mocks')
    await setupBrowserMocks()
  }

  app.mount('#app')
}

bootstrap()
```

---

## 六、配置环境变量

### `.env.development`

```bash
# Mock 模式：fallback（真实接口优先）| pure（全 Mock）| off（禁用）
VITE_ENABLE_MOCK = 'fallback'
```

### `.env.production`

```bash
# 生产环境默认关闭，需要演示时可改为 fallback 或 pure
VITE_ENABLE_MOCK = 'off'
```

---

## 七、配置 npm scripts

```json
{
  "scripts": {
    "dev": "vite",
    "dev-mock": "cross-env VITE_ENABLE_MOCK=pure vite",
    "build": "vite build"
  }
}
```

---

## 八、编写 Handler 示例

### 8.1 简单示例 `src/mocks/handlers/test.ts`

```typescript
// @ts-nocheck
import { http, HttpResponse } from 'msw'

import type { MockStrategy } from '../types'
import { resultSuccess } from '../utils/response'
import { withBackendFallback } from '../utils/with-backend-fallback'

export function createTestHandlers(strategy: MockStrategy) {
  return [
    http.get('/api/test', ({ request }) =>
      withBackendFallback(
        request,
        () =>
          HttpResponse.json(
            resultSuccess({
              message: 'mock response',
              timestamp: Date.now()
            })
          ),
        { strategy, tag: 'test:mock' }
      )
    )
  ]
}
```

### 8.2 带参数示例

```typescript
http.get('/api/user/:id', ({ request, params }) => {
  const userId = String(params.id)
  return withBackendFallback(
    request,
    () =>
      HttpResponse.json(
        resultSuccess({
          userId,
          username: `user_${userId}`,
          status: '0'
        })
      ),
    { strategy, tag: 'user:detail' }
  )
})
```

### 8.3 POST 请求示例

```typescript
import { readJsonBody } from '../utils/request'

http.post('/api/login', async ({ request }) => {
  const payload = await readJsonBody<{ username?: string; password?: string }>(request)
  
  return withBackendFallback(
    request,
    () => {
      const { username = '', password = '' } = payload ?? {}
      
      if (!username || !password) {
        return HttpResponse.json(resultError('用户名或密码不能为空'))
      }
      
      return HttpResponse.json(
        resultSuccess({ token: `mock-token-${Date.now()}` })
      )
    },
    { strategy, tag: 'user:login' }
  )
})
```

### 8.4 分页列表示例

```typescript
import { getSearchParams } from '../utils/request'
import { pagination } from '../utils/response'

const mockList = Array.from({ length: 100 }, (_, i) => ({
  id: i + 1,
  name: `Item ${i + 1}`
}))

http.get('/api/list', ({ request }) =>
  withBackendFallback(
    request,
    () => {
      const searchParams = getSearchParams(request)
      const page = Number(searchParams.get('pageNum') ?? 1)
      const size = Number(searchParams.get('pageSize') ?? 10)
      const rows = pagination(page, size, mockList)
      
      return HttpResponse.json(
        resultSuccess({
          rows,
          total: mockList.length
        })
      )
    },
    { strategy, tag: 'list' }
  )
)
```

---

## 九、在 handlers/index.ts 中注册

```typescript
// @ts-nocheck
import type { MockStrategy } from '../types'

import { createTestHandlers } from './test'
import { createUserHandlers } from './user'

export function createHandlers(strategy: MockStrategy) {
  return [
    ...createTestHandlers(strategy),
    ...createUserHandlers(strategy),
    // 添加更多模块...
  ]
}
```

---

## 十、单元测试中使用

```typescript
import { createMockServer } from '@/mocks/server'

const server = createMockServer('pure')

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

test('example', async () => {
  // 测试代码
})
```

---

## 十一、调试技巧

1. **查看响应头**：mock 响应会带有以下 header：
   - `X-Mock-Response: true`
   - `X-Mock-Mode: fallback | pure`
   - `X-Mock-Handler: <tag>`

2. **控制台日志**：在 `withBackendFallback` 中可以添加日志：
   ```typescript
   if (import.meta.env.DEV) {
     console.log(`[MSW] ${tag} -> mock response`)
   }
   ```

3. **浏览器 DevTools**：Network 面板可以看到请求是走了真实接口还是被 Service Worker 拦截

---

## 十二、注意事项

1. `public/mockServiceWorker.js` 由 MSW 生成，不要手动修改
2. 修改 handler 后会自动热更新，无需重启
3. 如需彻底禁用，设置 `VITE_ENABLE_MOCK=off`
4. 生产环境打包时，如果 `VITE_ENABLE_MOCK=off`，mock 代码会被 tree-shaking 掉（因为是动态 import）

---

## 十三、完整文件清单

需要创建的文件：

```
src/mocks/
├── browser.ts
├── server.ts
├── index.ts
├── types.ts
├── handlers/
│   └── index.ts
├── factories/
│   └── index.ts
├── scenarios/
│   ├── index.ts
│   ├── default.ts
│   └── pure.ts
└── utils/
    ├── request.ts
    ├── response.ts
    └── with-backend-fallback.ts
```

需要修改的文件：

- `package.json` - 添加依赖和 scripts
- `main.ts` - 添加 mock 初始化逻辑
- `.env.development` - 添加 `VITE_ENABLE_MOCK`
- `.env.production` - 添加 `VITE_ENABLE_MOCK`


---

## 十四、可选：使用 Faker 生成假数据

如果需要生成更真实的假数据，可以创建 factories：

### `src/mocks/factories/index.ts`

```typescript
// @ts-nocheck
export * from './user'
```

### `src/mocks/factories/user.ts`

```typescript
// @ts-nocheck
import { fakerZH_CN as faker } from '@faker-js/faker'

export interface MockUser {
  userId: number
  userName: string
  nickName: string
  email: string
  phone: string
  status: '0' | '1'
  createTime: string
}

let userSeed = 1

function nextUserId() {
  return userSeed++
}

function formatDateTime(date: Date): string {
  const pad = (value: number) => value.toString().padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

export function resetUserSeed() {
  userSeed = 1
}

export function createUser(overrides: Partial<MockUser> = {}): MockUser {
  const nickName = overrides.nickName ?? faker.person.fullName()
  const userName =
    overrides.userName ??
    faker.internet
      .userName({ firstName: nickName })
      .replace(/[^a-zA-Z0-9]/g, '')
      .toLowerCase()

  return {
    userId: overrides.userId ?? nextUserId(),
    userName,
    nickName,
    email: overrides.email ?? faker.internet.email(),
    phone: overrides.phone ?? faker.phone.number('1##########'),
    status: overrides.status ?? faker.helpers.arrayElement(['0', '1']),
    createTime: overrides.createTime ?? formatDateTime(faker.date.recent({ days: 30 })),
  }
}

export function createUserList(
  count: number,
  overrides?: (index: number) => Partial<MockUser>
): MockUser[] {
  resetUserSeed()
  return Array.from({ length: count }, (_, idx) => {
    const userOverrides = overrides ? overrides(idx) : {}
    return createUser({
      userId: userOverrides?.userId ?? nextUserId(),
      ...userOverrides
    })
  })
}
```

然后在 handler 中使用：

```typescript
import { createUserList } from '../factories'

const mockUsers = createUserList(50)

http.get('/api/user/list', ({ request }) =>
  withBackendFallback(
    request,
    () => {
      const searchParams = getSearchParams(request)
      const page = Number(searchParams.get('pageNum') ?? 1)
      const size = Number(searchParams.get('pageSize') ?? 10)
      const rows = pagination(page, size, mockUsers)
      
      return HttpResponse.json(
        resultSuccess({ rows, total: mockUsers.length })
      )
    },
    { strategy, tag: 'user:list' }
  )
)
```

---

## 十五、快速开始 Checklist

- [ ] 安装依赖：`npm install msw @faker-js/faker cross-env -D`
- [ ] 初始化 SW：`npx msw init public --save`
- [ ] 创建 `src/mocks/` 目录结构
- [ ] 复制核心文件（types.ts, utils/, scenarios/, browser.ts, server.ts, index.ts）
- [ ] 创建 `handlers/index.ts` 并编写第一个 handler
- [ ] 修改 `main.ts` 添加初始化逻辑
- [ ] 配置 `.env.development` 和 `.env.production`
- [ ] 添加 npm scripts
- [ ] 运行 `npm run dev` 测试

祝迁移顺利！🎉

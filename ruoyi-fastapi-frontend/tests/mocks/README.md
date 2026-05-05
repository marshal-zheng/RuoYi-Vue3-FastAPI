# MSW Test Runtime

Vitest 通过 `tests/setup.ts` 全局启动 `mockServer`。HTTP 合约测试默认使用 `src/mocks/handlers/**` 主线 handler，不再维护 `tests/mocks/api-contract-handlers.ts` 这类测试私有 API 契约。

## 使用规则

- 成功路径：调用真实 API 函数或 `@/utils/request`，并通过 `setupMainlineMockHandlers()` 为每个测试文件提供独立的 `MockDemoDb` 与 `createMockHandlers({ strategy: 'pure' })`。
- 错误路径：使用 `@/mocks/handlers/error-common` 的 `createStatusHandler`、`createNetworkErrorHandler`、`createTimeoutHandler`。
- 场景级错误：使用 `createScenarioHandlers('pure', 'error-429' | 'error-5xx' | 'error-timeout')`。
- 纯状态、纯组件交互、路由注册等与 HTTP 合约无关的测试可以 mock 上层 API 模块。

## 本地检查

```bash
yarn test:run tests/unit/api src/api/login.test.ts src/store/modules/user.login.test.ts
bash scripts/check-mock-standards.sh
```

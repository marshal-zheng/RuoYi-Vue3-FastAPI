# Frontend Mock Alignment Rollout

日期：2026-04-30

## 结果

- Vitest 全局 MSW Node server 已在 `tests/setup.ts` 启动，默认 `pure` 策略。
- API 合约测试已迁移到 `src/mocks/handlers/**` 主线 handler，删除测试私有 `tests/mocks/api-contract-handlers.ts`。
- 新增共享错误场景库：`src/mocks/handlers/error-common.ts` 与 `src/mocks/scenarios/error.ts`。
- 核心 API 合约模块已覆盖 `503`、`429`、timeout profile：project、config、menu、simulation、dict data、dict type、role、login。
- `fallback` 语义已覆盖上游成功、上游 `404` 回退、上游网络异常回退。
- CI 门禁已阻止 `src/mocks` 新增 `@ts-nocheck`、合约测试 mock `@/utils/request`、以及重引入测试私有 API contract handlers。

## 验证

```bash
bash scripts/check-mock-standards.sh
bash ../scripts/check-mock-mainline.sh
yarn type-check:strict
yarn test:run tests/unit/api src/api/login.test.ts src/store/modules/user.login.test.ts src/mocks/scenarios/error.test.ts src/mocks/handlers/api-contract.test.ts src/mocks/handlers/fallback.integration.test.ts src/mocks/utils/with-backend-fallback.test.ts
```

聚焦验证结果：12 个文件、55 个用例通过；新增 scenario factory 测试覆盖 `error-429` 与 `error-5xx` 的 debug headers 和 problem details。

## 维护边界

新增 HTTP 合约测试不得引入并行契约 fixture。若主线 handler 缺接口，先补 `src/mocks/handlers/**` 和 typed dataset/repository；只有请求序列化探针这类测试专属断言可以在测试内临时注册局部 handler。

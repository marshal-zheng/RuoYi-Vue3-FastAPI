# 新业务模块 Mock 主线 Definition of Done

新增业务模块只要包含前端 API、页面展示或 demo-offline 演示链路，就必须接入当前 contract-first 单套 mock 主线。

## Required Evidence

- OpenAPI 契约：后端 artifact 可导出并通过 `--check`，前端 `yarn api:generate` 与 `shared/openapi.json` 同步。
- 类型约束：API 调用层、typed mock data、handler 响应或临时本地契约在 TypeScript 下可检查。
- 数据事实源：业务实体进入 `src/mocks/data/<domain>/`，复杂域按聚合拆分，`index.ts` 只做轻量聚合。
- 确定性 factory：使用统一 seed 和固定 reference time；稳定 dataset/factory 不使用动态时钟、未受控随机数或未固定参考时间的相对日期。
- MSW handler：进入 `src/mocks/handlers/**`，`fallback` 和 `demo-offline` 复用同一套 handler 注册入口。
- 持久化边界：核心演示写操作进入 `src/mocks/store/**` repository/seed/reset；只读展示接口明确保持只读。
- Invariant：新增至少一组领域 invariant，覆盖外键、唯一键、枚举、权限或核心业务关系。
- API 合约测试：通过真实 API 函数或请求兼容层进入 HTTP 链路，不直接 mock 请求适配层。
- Demo-offline 验收：关键 `/api/**` 已覆盖；未覆盖 API 返回确定性 `501`；`build:demo-offline` 可构建。
- Prod 边界：`build:prod` 不启动 MSW、不初始化 mock store、不暴露 debug reset/export 能力。

## Verification Commands

```bash
cd ruoyi-fastapi-backend
.venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json --check

cd ../ruoyi-fastapi-frontend
yarn api:generate
yarn lint:check
yarn type-check
yarn test:run
yarn build:prod
yarn build:demo-offline

cd ..
scripts/check-mock-mainline.sh
scripts/check-mock-mainline.sh --require-dist
```

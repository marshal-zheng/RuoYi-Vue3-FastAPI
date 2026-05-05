# Mock 契约覆盖与 Schema 门禁实现任务

- [x] 1. 建立 OpenAPI operation inventory 和 registry 结构
  - 在 `src/mocks/contracts/coverage/` 下建立 `registry.schema.json`、`types.ts`、`index.ts` 和 `registry/` 分域目录。
  - 定义 `ContractCoverageStatus`、`ContractSchemaStatus`、`ContractRegistryEntry`、报告 summary 与 failure/warning 类型。
  - 明确 registry JSON 是提交基线，完整 coverage report 只由命令生成；默认不提交完整报告文件。
  - 用脚本或临时命令从 `shared/openapi.json` 生成当前 operation inventory，记录 OpenAPI 版本、operation 数、method/path/operationId/tags 和 response schema 可用性。
  _需求追溯: R1.AC1, R1.AC2, R1.AC4, R2.AC1, R7.AC1, R7.AC6_

- [x] 2. 实现 OpenAPI reader、fingerprint 和 path 规范化核心函数
  - 新增轻量纯函数模块，读取 `../shared/openapi.json` 并枚举所有 HTTP operations。
  - 计算稳定 artifact fingerprint，不包含时间戳、绝对临时路径或环境噪音。
  - 实现 OpenAPI `{param}` 与 MSW `:param` 的路径规范化和匹配逻辑，允许参数名不同但动态段位置一致。
  - 为 operation 枚举、fingerprint、path 匹配增加小型 fixture 单元测试。
  _需求追溯: R1.AC1, R1.AC3, R2.AC2, R7.AC3_

- [x] 3. 实现 registry loader 和静态一致性校验
  - 从 `src/mocks/contracts/coverage/registry/**/*.json` 读取并合并 registry entries。
  - 校验 entry schema、允许的 status/schemaStatus、重复 method/path、重复 handler tag、孤儿 registry entry 和未分类 OpenAPI operation。
  - 校验 `mock-handled`、`unsupported-501`、`real-only`、`legacy-local-contract`、`missing` 的必填字段组合。
  - 校验 registry 中引用的测试文件都存在，且测试文件路径使用仓库相对路径。
  _需求追溯: R1.AC2, R1.AC3, R2.AC1, R2.AC3, R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC6, R9.AC3_

- [x] 4. 初始填充全量 endpoint coverage registry
  - 按 auth、system、project、simulation、monitor、real-only、missing 等分域 JSON 填充当前 `shared/openapi.json` 的全部 operations。
  - 将 demo-offline 主链路标记为 critical，首批覆盖 auth、system menu、dict、role、dept、project、version、topology 和 simulation read model。
  - 为 non-critical `missing` 明确 owner、原因、影响范围和迁移动作，避免无主债务。
  - 为 schema `{}`、unknown、binary response、本地契约和已验证 OpenAPI schema 标记明确 schemaStatus。
  _需求追溯: R1.AC2, R1.AC5, R3.AC5, R3.AC7, R4.AC1, R4.AC2, R4.AC3, R5.AC3, R6.AC1_

- [x] 5. 实现 `check-mock-contracts.mjs` 快速门禁 CLI
  - 新增 `ruoyi-fastapi-frontend/scripts/check-mock-contracts.mjs`，支持 `--strict`、`--format=summary|json|markdown` 和 `--write-report <path>`。
  - 输出总 operations、各分类数量、critical 缺口数量、schema coverage 数量、local contract 数量和 failure/warning 列表。
  - 发现覆盖缺口、registry 漂移、critical 失败、测试文件缺失、重复 tag 或 schema 状态违规时返回非 0。
  - 保证默认命令只输出 stdout，不要求提交完整 coverage report 文件。
  - 确保正常本地仓库状态下单独执行 contract coverage check 目标耗时小于 10 秒。
  _需求追溯: R1.AC3, R1.AC4, R3.AC5, R3.AC6, R3.AC7, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5, R7.AC6, R8.AC4, R8.AC6_

- [x] 6. 增加 local contract 和 critical 辅助审计
  - 扫描 `src/mocks/contracts/local.ts`，确认 `legacy-local-contract` registry entry 的 `localContract` 名称真实存在。
  - 当 OpenAPI artifact 已经提供可靠 schema 时，拒绝无例外说明的 `legacy-local-contract` 延续。
  - 扫描 `src/api/**`、demo-offline 页面入口和后续 E2E 入口作为辅助信号，发现疑似 critical 调用漏标时输出可定位 failure 或 warning。
  - 保持 `critical` 事实源只来自 registry，不由扫描结果自动改写。
  _需求追溯: R4.AC4, R4.AC5, R4.AC6, R6.AC1, R6.AC2, R6.AC3, R6.AC4_

- [x] 7. 加强 handler tag 对齐和 coverage 静态测试
  - 新增 `src/mocks/contracts/coverage.test.ts`，复用 CLI 纯函数校验真实 registry。
  - 校验 `mock-handled` 与 `unsupported-501` 的 `handlerTag` 唯一且格式稳定。
  - 对当前业务 handlers 中已有 `X-Mock-Handler` 进行辅助审计，发现 registry tag 与实际响应不一致时失败。
  - 保证文件下载等非 JSON 响应也有可定位 handler tag。
  _需求追溯: R2.AC3, R2.AC4, R2.AC5, R3.AC1, R3.AC3, R9.AC2, R9.AC3, R9.AC4_

- [x] 8. 增加 OpenAPI + AJV response schema resolver
  - 将 AJV 声明为显式 devDependency，避免依赖 transitive package。
  - 在 `tests/mocks/contracts/openapi-schema-validator.ts` 或等价位置实现 response schema resolver。
  - 支持按 method、OpenAPI path、status code 解析 200 response schema 和 `#/components/schemas/*` 引用。
  - 对 `{}`、缺失 schema、unknown、binary response 和 local adapter schema 返回明确 skip reason，不计入 OpenAPI schema coverage。
  - 为 schema resolver 增加单元测试，覆盖 `$ref`、缺失 schema、binary 和失败字段输出。
  _需求追溯: R1.AC5, R5.AC1, R5.AC2, R5.AC3, R5.AC4, R8.AC5_

- [x] 9. 增加核心 API schema validation 测试
  - 新增或扩展 `src/mocks/handlers/api-contract-schema.test.ts`。
  - 复用 `MockDemoDb`、`createMockDataSource()` 和 `createMockHandlers({ strategy: 'pure', dataSource })`。
  - 通过真实 `src/api/**` API function、`fetch` 或 request 兼容层触发 MSW handler，不 mock `@/utils/request`。
  - 对 auth、system、project、version、topology 首批核心 endpoint 执行 AJV response validation 或校验 schema-unavailable 例外。
  - 对 simulation read model 中 OpenAPI schema 不可靠的 endpoint 标记并验证 `schema-unavailable`。
  _需求追溯: R4.AC1, R5.AC1, R5.AC2, R5.AC3, R5.AC5, R9.AC1, R9.AC2, R9.AC3_

- [x] 10. 固化 unsupported、binary、real-only 和 missing 分类测试
  - 为 `unsupported-501` endpoint 增加测试，确认 HTTP 501、稳定 body 语义和 `X-Mock-Handler`。
  - 为 binary/file download endpoint 标记 `binary-response` 并验证不进入 JSON schema validation。
  - 为 `real-only` endpoint 校验不得标记 critical，并要求报告中包含原因。
  - 为 non-critical `missing` 技术债校验 owner、原因、影响范围和迁移动作齐全。
  _需求追溯: R3.AC2, R3.AC3, R3.AC5, R3.AC7, R4.AC2, R5.AC3, R7.AC2_

- [x] 11. 接入 package scripts 和本地开发命令
  - 在 `ruoyi-fastapi-frontend/package.json` 增加 `mock:contracts`、`mock:contracts:report` 和 `mock:contracts:json`。
  - 确认 `mock:contracts` 不启动 Vite、不启动 Vitest、不构建前端。
  - 在脚本缺少 OpenAPI artifact、registry JSON 或 schema validation 依赖时 fail fast，并输出明确修复命令。
  - 确认显式 `--write-report` 产物写入生成路径，不成为默认提交基线。
  _需求追溯: R7.AC4, R7.AC6, R8.AC1, R8.AC4, R8.AC5, R8.AC6_

- [x] 12. 集成 GitLab 和 GitHub 前端质量门禁
  - 在 `.gitlab-ci.yml` 的 `frontend-quality-gates` 中加入 targeted schema test 和 `yarn mock:contracts`。
  - 在 `.github/workflows/ci.yml` 手动前端检查中加入同等 contract coverage check。
  - 保持 `yarn api:generate` 和 generated client drift check 仍先于契约覆盖门禁。
  - 确认 GitHub 辅助 workflow 与 GitLab 主门禁口径一致。
  _需求追溯: R1.AC3, R8.AC1, R8.AC2, R8.AC3_

- [x] 13. 更新 mock 文档、DoD 和 spec 索引
  - 更新 `src/mocks/README.md`，说明新增或修改 API 必须同步 OpenAPI artifact、coverage registry、handler metadata、schema 状态和测试证据。
  - 更新 mock module DoD，增加 endpoint 分类、critical 评估、schema validation 或 schema-unavailable 例外要求。
  - 更新 `docs/specs/README.md`，标记 `mock-contract-coverage-and-schema-gates` 是当前 mock 主线的 P0 治理升级 spec。
  - 文档中如提到外部 mock server、旧 demo runtime、多场景 package 或 MCP，必须明确非目标、历史或暂停状态。
  _需求追溯: R10.AC1, R10.AC2, R10.AC3, R10.AC4_

- [x] 14. 执行验收命令并形成结果记录
  - 运行 `cd ruoyi-fastapi-frontend && yarn mock:contracts`，确认报告稳定、失败定位清晰且性能符合 10 秒软门槛。
  - 运行 `cd ruoyi-fastapi-frontend && yarn test:run src/mocks/contracts src/mocks/handlers/api-contract-schema.test.ts`。
  - 运行 `cd ruoyi-fastapi-frontend && yarn type-check:strict`。
  - 运行前端完整质量门禁相关命令：`yarn lint:check`、`yarn type-check`、`yarn test:run`、`yarn build:prod`、`yarn build:demo-offline`、`bash ../scripts/check-mock-mainline.sh --require-dist`。
  - 记录未运行命令、原因和补跑命令；不得把未验证项包装成已完成。
  _需求追溯: R7.AC1, R7.AC3, R7.AC4, R8.AC1, R8.AC4, R8.AC6, R9.AC1, R9.AC2_

  验收记录:
  - `yarn mock:contracts`: 通过；244 operations，critical failures 为 0，耗时低于 10 秒软门槛；存在辅助 critical-audit warning。
  - `yarn test:run src/mocks/contracts src/mocks/handlers/api-contract-schema.test.ts`: 通过，2 files / 7 tests。
  - `yarn type-check:strict`: 通过。
  - `yarn type-check`: 通过。
  - `yarn test:run`: 通过，62 files / 634 tests。
  - `yarn build:prod`: 通过；保留既有 chunk size / dynamic import warning。
  - `yarn build:demo-offline`: 通过；保留既有 chunk size / dynamic import warning。
  - `bash ../scripts/check-mock-mainline.sh --require-dist`: 通过。
  - `yarn lint:check`: 通过；仍输出既有全量 warning。
  - `yarn eslint <本次触碰的 src 文件>`: 通过。
  - 未运行命令: 无。

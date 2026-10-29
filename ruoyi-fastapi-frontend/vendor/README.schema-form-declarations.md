# Schema Form 声明修复包（2026-10-29）

当前安装 `zxio-schema-form-0.1.0-declarations.20261029.tgz`，包内版本仍为 `0.1.0-remark-a.20261022.1`，SHA-256 `af076ed55118384aed61d6d866bd8688e34b47d617fb1d3097e38db04e92b1b0`。未发布 npm。`@zxio/zxui` 继续使用 `zxio-zxui-3.0.0-next.0-completion.20261028.tgz`，未替换。

相对 completion.20261028：

- 公开声明改由 vue-tsc 生成，不再引用 `@zxio/components`、`@zxio/shared`、`@zxio/utils/dist` 等消费者无法解析的模块；声明从 1.12 MB 降到约 105 KB。
- 级联字段的输入框带上字段 id 与 aria-labelledby，宽度撑满所在列。
- 其余 JS、样式、文档与示例行为不变。

来源：ZXUI 仓库 `packages/schema-form/dist` 构建后，经 `scripts/contracts/check-form-conditional-edit-packed.mjs` 的 `npm pack` 生成，复制前核对 SHA-256。安装命令 `YARN_ENABLE_NETWORK=0 corepack yarn install --mode=skip-build`，`yarn.lock` 只变更 schema-form 条目。

验证：全量 `./node_modules/.bin/vue-tsc --noEmit` 通过；`VITE_ZXUI_LOCAL=false` 下用户、岗位、SDK 与附件上传 12 个文件 135 项通过。证据见 ZXUI 仓库 `docs/reports/evidence/schema-declarations-2026-10-29/`。

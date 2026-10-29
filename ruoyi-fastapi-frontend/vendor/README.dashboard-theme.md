# Dashboard / Grid 主题配套包（2026-10-26）

这是本地在研联调交付，没有 npm 发布。package.json 和权威 yarn.lock 选用本组 17 个配套 tarball；相同 semver 不表示它与 registry 原包相同。旧 tarball 保留为历史验收证据，不在当前依赖图中使用。

- ZXUI 3.0.0-next.0 包含 Element Plus 2.14.7 适配及主题事务资源绑定竞态修复。
- Dashboard 0.1.0 公开 `@zxio/dashboard/theme`，仅转导 Grid 的主题数据。业务在既有 precompiled Host 登记该 bundle，使用默认启用登记模块语义。
- Grid 1.0.6 的配套文件为 `zxio-vue-grid-layout-1.0.6-theme.20261026.tgz`，SHA-256 `265198c9231d7b6f1001130df11b212f99e892d0e0ffa36dd461b72a5cbbb46d`。来源为 `/Users/hqz/Downloads/vue-grid-layout` 的标准构建。
- tokens、theme-compiler、theme-css-codec、theme-consumer、9 个登记主题及 theme-tailwind 同步为当前配套版本。主题核心契约为 `sha256:bb14425c9adb15ad223670c7b84c6ac93f035ec0ad21127a298fba59263b4c37`。
- Vue 3.5.44、Element Plus 2.14.7、Vite 5.4.21；Yarn resolutions 将核心/协议/编译器/Grid 的传递引用固定为同一 tarball。继续使用现有 Vite dedupe。

构建：在 ZXUI 仓库执行各所属包 build 与 `pnpm build`，ZXUI 从 `dist/@zxio/zxui`、tokens 从 `packages/tokens/dist` pack，其余从各包目录 pack。Grid 复用已验证配套文件。每个包均由 `corepack pnpm --dir <publication-root> pack --pack-destination <staging>` 生成，未改写生成包绕过契约。

完整包名、版本、来源、SHA-256 和验证结果见 [交付报告](../../docs/reports/zxui-dashboard-sync-2026-10-26/README.md)及其中的 `package-identity.json`。未发布和未提交的源码仍需后续独立交付。

# ZXUI / RuoYi 第二批：公共 Vite 主题部署

日期：2026-09-26。承接已认可 review 的「官方 Vite 接入/部署能力」，本批完成主题资产部署部分。组件源码 alias、公共列表工具栏、第三方主题适配、密度与缩放仍按后续批次推进。未发布 npm、未创建提交。

## 判定与归属

这部分属于 ZXUI 应提供的基础能力。原业务维护约 200 行包定位、资产交付、更新监听代码，docs 也自行处理相同的资产路径边界。它们不是业务规则，每接入一个新业务都复制一套，会增加目录变化、哈希校验和生命周期处理不一致的风险。

此外，旧业务构建向 `public/zx-theme-assets` 写入部署资产，之后 Vite 会继续复制目录内容。开发和构建虽然已经分目录，但旧 public 产物仍可能残留。

## 完成内容

- ZXUI 新增公开 `@zxio/theme-compiler/vite`，交付 ESM、CJS 和类型声明。`themeDeploymentPlugin` 接收主题包登记，支持可选 themeId 断言、虚拟模块名、资产目录、解析锚点和本地 workspace。
- 始终通过主题包公开 exports 读取 manifest/CSS，不让业务推测 generated 路径。`workspaceRoot` 只负责本地主题包，不替代组件源码 alias。
- 开发中间件原样提供 CSS，避免 Vite CSS 转换破坏 SRI；生产通过 Rollup asset emission 输出，每个实例拥有独立临时目录，不再写业务 public。
- 监听由公开 manifest 路径推导的父目录，处理原子目录替换。成功后同时更新部署映射与资产并刷新页面；失败保留上一份可用输出。关闭服务或 middleware-mode server 时释放监听器。
- docs 复用公开 `resolveThemeAssetRequest`；原有压缩 catalog、SSR 与首帧逻辑保留。路径处理覆盖 base、编码错误、目录穿越、越界 symlink 和私有 owner 文件。
- RuoYi 部署封装缩至 39 行，只保留单一登记表、业务依赖声明检查和公共插件配置。Host 与虚拟模块直接引用 `ThemeDeploymentOutput`，删除手写的弱类型副本。
- compiler 包的类型检查和声明构建改为解析 pnpm symlink 实际位置，解决新增 Vite 类型无法找到其 Rollup 依赖的问题；没有修改仓库其他 TS 项目的设置。

源码：[公共插件](/Users/hqz/Downloads/element-plus/packages/theme-compiler/src/vite/index.ts)、[资产路径边界](/Users/hqz/Downloads/element-plus/packages/theme-compiler/src/vite/assets.ts)、[业务配置](/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vite/zxui-theme-packages.ts)。使用说明已补入 compiler README 与中英文主题运维文档。

## 本地依赖交付

首次检查 installed 模式时，旧 vendor 主题被新 compiler 以 `invalid-local-adapter-identity` / `invalid-tailwind-adapter-identity` 拒绝。原因是上一批已调整适配器契约，而业务打包保存的主题仍是旧产物。

保留严格契约校验，使用当前已生成的九套主题与 compiler 本地打包，文件名增加 `-vite.20260926.tgz`，更新 package.json 和 yarn.lock。没有更新 ZXUI UI 主包、没有发布 npm，也没有把旧 tarball 删除。它们是本地候选包，同版本号不表示 registry 已发布新版本。后续正式发布需按仓库版本治理统一提升版本。

旧 public 目录的 2,935 个文件经过 owner 清单与 SHA-256 核对，备份到 `/tmp/ruoyi-zxui-vite-before/public-zx-theme-assets`；没有直接删除或覆盖未知文件。原 package.json/yarn.lock 也保存在该备份目录。

## 验证证据

| 检查 | 结果 |
| --- | --- |
| ZXUI Vite 新入口与 docs 既有回归 | 11 / 11 通过，其中新增 5 个集成用例 |
| 源码目录原子替换、失败保持与恢复 | 真实临时包、真实 Vite server 验证通过 |
| 开发/构建隔离、GET/HEAD、`?direct`、子路径 | 验证通过，CSS 原字节交付 |
| middleware 模式释放监听器 | 验证通过，不依赖 HTTP server close 事件 |
| compiler 包类型检查及 ESM/CJS/声明构建 | 通过 |
| ZXUI 本批源码 lint 与格式 | 通过 |
| RuoYi 登记表与 Host 接线回归 | 4 / 4 通过 |
| RuoYi `yarn type-check` | 通过；旧 mock/JSON fixture 已适配公开类型 |
| RuoYi 本批主题接线文件 lint | 通过 |
| RuoYi 源码直连完整生产构建 | 通过，`/tmp/ruoyi-zxui-vite-build` |
| RuoYi vendor 模式完整生产构建 | 通过，`/tmp/ruoyi-zxui-vite-vendor-app-build`；部署映射与源码构建一致 |
| installed 包的 Vite 5 部署构建 | 通过，`/tmp/ruoyi-zxui-vite-installed-build` |
| 源码 / installed 产物对照 | 每种模式 9 主题、2,934 项 CSS 的 SHA-256、SRI、字节数全部通过；部署映射完全一致 |
| 两仓 `git diff --check` | 通过 |

真实页面使用 `http://localhost/system/user`，经 `VITE_ZXUI_LOCAL=true` 直连 ZXUI。完成九主题各 light/dark 共 18 次组合，记录实际 scope 身份、选用的 CSS 链接及 computed sidebar/button 样式；核对深色新增用户弹框，未提交表单，恢复陆军松枝绿深色。此次是部署链路回归，不重复声称整站对比度或全部组件状态通过。

证据：[部署一致性](./evidence/2026-09-26-zxui-vite-theme-deployment/ruoyi-zxui-vite-integrity.json)、[浏览器组合记录](./evidence/2026-09-26-zxui-vite-theme-deployment/browser-themes.json)、[真实弹框截图](./evidence/2026-09-26-zxui-vite-theme-deployment/army-pine-dark-dialog.png)、[库端回归](./evidence/2026-09-26-zxui-vite-theme-deployment/zxui-vite-tests.log)、[业务回归](./evidence/2026-09-26-zxui-vite-theme-deployment/ruoyi-zxui-vite-tests.log)。

## 保留边界与后续

- 浏览器在关闭弹框的自动化操作期间捕获 `keybindings/dist/... → toEventSnapshot` 的 `event.getModifierState is not a function`。它不是 CSS 加载/SRI 错误；当前证据不能说明自然键鼠操作是否同样触发。需在 keybindings 独立仓库核对事件兼容，未把它混入本批主题部署实现。
- docs 的共享资产解析器和 SSR catalog 回归通过；未重新执行整站 docs 生产构建或宣称 docs 全站视觉验收。
- 生产构建仍有已有大 chunk 提示，依赖安装仍提示 Vitest peer 版本及 testing-library peer 缺失；未为本批接入扩大依赖治理范围。
- 后续优先推进公共列表工具栏，再处理第三方内容主题适配和密度/缩放。组件源码 alias 的官方入口仍待后续收敛，不能将本批称为完整 Vite 源码接入方案。

# 独立复核：RuoYi Dashboard / Grid 主题配套同步

最终代码与包复核结论：下述图标属性透传缺陷已在库构建层修复，当前 `.20261026.1` 配套包及业务接线未发现剩余 P0 / P1 / P2 缺陷。该结论针对本地集成范围；最终业务页面操作、偏好恢复和临时资源清理由主代理的最终证据负责，不据此声称全仓测试、外部发布或已提交源码基线完成。

## 范围与隔离

使用 `baseline/*.task.diff` 界定本轮变化，未把全部未提交工作当作本轮实现。RuoYi 起点 HEAD 为 `1e9160a8ca470b4ca51791f736f6b7ba4fec7eb7`。

审阅业务 Host 与其测试、`package.json`、权威 `yarn.lock`、17 个 tarball、vendor 说明，以及库的 Dashboard 公开 theme 入口、precompiled Host/composition/runtime 实现。发现源码与安装包视觉差异后，追加审阅这四个库构建文件：

- `internal/build/src/plugins/production-vue.ts`
- `internal/build/src/plugins/production-vue.test.ts`
- `internal/build/src/tasks/modules.ts`
- `internal/build/src/tasks/full-bundle.ts`

本复核未修改产品源码、依赖或业务数据，未启动浏览器或 GUI。唯一写入为本目录的复核报告和探针结果。

## 已闭环发现：生产包丢失根节点 attrs

源码与最初安装包的侧栏图标表现不同。业务 CSS 对带 `navigation-menu-icon` 的嵌套图标有明确隐藏规则；初轮生产包的真实 Icon 模板保留了顶层注释 Fragment，导致传入的 class 等 attrs 丢失，而源码开发模式会从该 Fragment 提取单根。

独立检查实际 plugin-vue 5.2.4 和 Vue 3.5.44 代码确认：plugin-vue 将 `template.compilerOptions` 传给 SFC 的 template parser，随后复用 AST；`isProduction: true` 本身没有为这个 parser 明确关闭注释。Vue 的生产 `renderComponentRoot` 不执行只在开发模式使用的 DEV_ROOT_FRAGMENT 单根提取。官方依据：[plugin-vue descriptor parser](https://github.com/vitejs/vite-plugin-vue/blob/plugin-vue%405.2.4/packages/plugin-vue/src/utils/descriptorCache.ts)、[模板 AST 复用](https://github.com/vitejs/vite-plugin-vue/blob/plugin-vue%405.2.4/packages/plugin-vue/src/template.ts)、[Vue 根节点 attrs 处理](https://github.com/vuejs/core/blob/v3.5.44/packages/runtime-core/src/componentRenderUtils.ts)。

独立内存探针直接编译真实 `icon-core.vue` 的模板，先在通常的非 production Node 构建进程环境执行 parse/compileTemplate（`isProd: true`、复用 AST），再在生产 Vue custom renderer 中挂载。默认配置产生 8 处 `_Fragment` 和 `2112` 标记，丢失 consumer class、data 属性、aria-label 与传入 style；显式 `comments: false` 后无该 Fragment，以上属性全部透传。结果见 [review-compile-probe.json](review-compile-probe.json)。这是内存编译/渲染探针，不冒充完整浏览器页面。

最终修法合理：共享 `productionVuePlugin()` 显式声明 `comments: false`，模块构建和 full bundle 同用该工厂；原 `hoistStatic: false`、`cacheHandlers: false` 及已存在的 BetterDefine 选择保留。没有在 Icon 或业务中追加 attrs 补丁。两分支回归使用真实 Rollup 插件编译与 Icon 相同的“注释 + 条件根”最小模板，并在独立生产 Vue SSR 进程中验证 class、aria-label、style；它是机理回归，真实 Icon 由上述探针与最终业务验证补足。

独立重跑 `corepack pnpm exec vitest run internal/build/src/plugins/production-vue.test.ts --reporter=dot`：**1 文件、2 测试通过，exit 0**。另读取并确认主代理保存的两分支红灯、修复后 17 项测试、lint 和最终库构建记录；这些日志不是本复核自行重跑的结果。

## 最终包与接线独立核验

1. 最终 ZXUI 为 `zxio-zxui-3.0.0-next.0-dashboard-theme.20261026.1.tgz`，SHA-256 为 `451333dc1248cc68cf391a2e6395e24ddd443a9afc76d994d2463530b0f1bbfb`。重新计算全部 17 个 tarball 的 SHA-256，并逐文件与实际安装比较：**7,144 文件、0 不同**。最终安装的 `icon-core.vue.mjs` 已无 Fragment 或 2112 标记。[最终探针](review-probes.json)保留逐包结果；[初轮探针](review-probes.initial.json)只属于被替换的旧核心包。
2. 从实际 Grid bundle 的 `coreRequirements.experimentalContractContentHash` 与 9 个登记主题的 `identity.contractContentHash` 逐一比较，均为 `sha256:bb14425c9adb15ad223670c7b84c6ac93f035ec0ad21127a298fba59263b4c37`；Tailwind adapter 的契约也一致。
3. 从 vfadmin、ZXUI、Dashboard、widgets、chart、schema-form、compiler、codec、Grid 以 Node `createRequire` 解析 Vue、runtime-core、tokens、consumer、codec、Grid，各依赖均为单一物理根；使用 `rg --files -uu node_modules` 递归查询对应 package.json 也未发现副本。最终核心重打包后这些依赖选择未变。
4. 安装的 runtime-core 确实包含绑定前等待 scope 事务、资源获取前记录 generation、generation 改变时释放资源并重绑的实现；不是仅更新 tarball 名称。
5. Dashboard 的 `./theme` 只转导 Grid 的纯主题数据。业务在原 precompiled Host 登记一次，没有第二 Host、业务 token 映射、Seeds 或诊断隐藏；`local.modules ?? parent?.modules ?? allModules` 支持省略模块子集并默认启用全部登记模块。
6. 最终安装包生产构建记录为 **8,583 模块、0 个库源码路径命中**，runtime-core 仅一个 ESM 模块；consumer 的根与 Vue 两入口属于同一安装包。
7. 独立重跑业务 `./node_modules/.bin/vitest run src/theme/zx-theme-host.test.ts tests/unit/components/dashboard-chart-settings.test.ts --reporter=dot`，初轮与最终安装包均为 **2 文件、7 测试通过**。最终重跑日志见 `logs/reviewer-consumer-final.log`。

包内容核验使用 Python tarfile 逐项读取字节直接比较，未解包覆盖工作区。契约与解析核验使用公开包导出、Node createRequire 和 assert，未修改生成 manifest 或绕过验证。

## 视觉与交付边界

独立目视检查初轮 `source-1280.png` 与 `packed-panel-menu.png`：监控页的主要控制区、面板和菜单未见主题失配或菜单越界，侧栏差异进一步触发了上述真实构建缺陷的修复。此处不把初轮旧包截图当成 `.1` 最终产物验收。早期 source 样本的空 grid.text 与颜色过渡采样也已提示主代理覆盖；最终结论应引用稳定截图后的计算样式和明确页面 URL。

本复核没有运行全仓 lint/test，也未重演全部浏览器交互；没有声称所有页面、所有轴组合或仿真页已验收。file tarball 使用保留 semver，由锁文件与哈希区分身份；正式发布需要另行确认版本和发布动作。不关闭 WI-0008，不提交、推送或发布，不评估无关 AI、file-assets/minio 或其他线程工作。

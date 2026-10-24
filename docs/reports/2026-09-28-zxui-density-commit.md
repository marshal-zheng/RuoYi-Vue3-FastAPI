# 全局 density 偏好提交收口（2026-09-28）

本轮修复业务全局 density 的状态顺序：原 `setZxThemePreference` 在 ZXUI Provider 异步切换前，就更新菜单读数并写入 localStorage。若布局参与者失败，Host 回滚为旧密度，而已存偏好仍是请求值。现在 `ZxThemePreferenceBridge` 在应用 Provider 内使用 ZXUI 公开的 `useThemeRuntime`、`useThemeScope` 和 `updateScope` 先提交作用域；成功后统一更新主题、明暗与 density 偏好并保存，失败则维持上次已生效值并显示重试提示。快速连续操作串行消费最新请求，不把中间请求写入持久化。整个过程不 reload，不重挂业务页面。

业务 `src/theme/zx-theme-config.ts` 是偏好的单一状态入口；`src/App.tsx` 安装桥接组件；主题菜单在待提交时标记 `aria-busy`。ZXUI 的通用布局事务与业务 VXE 适配保持原分工，没有为 density 再建一套 CSS 或组件库 API。旧 `SizeSelect` 控制 Element Plus 的组件 size，和 density 不同；按 Display Scaling 设计 D13 留待旧 size 迁移，不将其映射为 density。

验证：聚焦 Vitest 2 文件 9 项通过，覆盖成功提交、失败不污染存储、慢请求后的最新选择及存储拒绝时保留本次有效选择。Chromium 本地源码链中，5000 行 VXE 样例切 compact 后行高 48→44px，主题和存储一致；注入一次重算失败后保持 default/48px，选择器恢复 default，本地存储未写入请求值，显示重试提示且无页面异常；延迟重算期间连续选择 compact→comfortable，最终主题、行高 52px 与持久化均为 comfortable。真实业务登录页选择 compact 后进入 `/system/user` 保持 compact；用户管理从 default 切到 comfortable 后输入高 32→36px、表格行高 53px，未提交的用户名筛选值保持，路由无导航或 reload，页面无异常。

源码直连业务构建通过；改动文件 ESLint 和 `git diff --check` 通过。安装包交付、类型检查与可变行高虚拟表验收见下节。显示大小属于单独的 Display Scaling 工作，不能据此宣称全站所有像素都由 density 缩放。

## ZXUI Dropdown 密度补齐

真实页面检查发现，Element Plus Dropdown 菜单项在 default、compact、comfortable 下始终为 32px，而同一作用域的输入控件已经按 `--el-component-size` 变化。组件库 `packages/theme-chalk/src/structural.css` 在普通 Dropdown 菜单项上使用这个有效控件高度作为 `min-height`，移除固定纵向内边距；ZXUI MoreAction 自有尺寸预设不受影响。`pnpm build:theme` 后，Chromium 源码直连业务的菜单项高度实测为 32/28/36px，无页面异常。结构拆分测试 5 项通过，生成样式镜像同步更新。

`pnpm theme-consumer:check:structural` 当前仍失败，输出仅有既存 Display Scaling 的 `--zx-display-text-*`、`--zx-display-line-body` 变量准入及其 `var()` 回退问题；没有新增 Dropdown 规则的诊断。这是组件库当前并行 Display Scaling 工作的质量门禁限制，不能记为本轮检查通过。

## 本地安装包交付与交错行高验收

从当前 ZXUI 源码构建并打包 `@zxio/zxui`。类型生成首次失败是仓库 `tsconfig.base.json` 漏映射已公开的 `@zxio/tokens/display` 子路径；补齐仓库路径映射后 `pnpm build` 通过，产物公开 `useDisplayLayoutParticipant` / `ZxDisplayLayoutParticipant`，结构 CSS 与生成源字节一致。新版 ZXUI 运行时依赖 tokens 的 display 子路径，因此同时构建本地 `@zxio/tokens` 包，并用 Yarn resolution 保证 ZXUI 与主题编译器使用同一份 tokens。

首次安装包页面在显式 `display: office/100` 夹具中报 `TR_DISPLAY_ASSET_UNSUPPORTED`：旧主题包没有新版显示契约。核对九个主题的当前生成 manifest 与 tokens 的 `displayContract.contentHash` 完全一致后，重新打包九个主题和主题编译器；安装包夹具随后正常挂载。业务 `package.json`、`yarn.lock` 现指向这组本地候选包，未发布 npm。

最终检查：ZXUI `pnpm build`、tokens 与主题编译器构建通过；RuoYi `yarn type-check` 通过，安装包模式 `VITE_ZXUI_LOCAL=false yarn build:prod` 通过，夹具 ESLint 通过。Chromium 安装包页面中，5000 行 VXE 表设置交错行高并定位第 160 行后，default→compact→comfortable 的第 160 行始终保持距视口顶端 12px；普通行高 48→44→52px，显式 84px 行维持 84px，未出现错误提示。真实登录页切换至陆军松枝绿并选择 compact 后，Host variant 正确更新；最后恢复陆军松枝绿、深色、default density。

后续 ZXUI docs 启动暴露了源码开发路径与安装包路径的差异：`node --import tsx` 将没有 ESM 边界的 `src/display/index.ts` 当作 CommonJS，导致已构建的主题编译器无法取得 `checkDisplayContract` 具名导出。组件库在 `packages/tokens/src/display/package.json` 单独声明 ESM，不改变其他 tokens 子入口；`node --import tsx` 导入与 `pnpm docs:dev` 均通过。VitePress 已在 `http://localhost:2000/` 启动，浏览器首页正常渲染、无页面错误。启动日志仍有 `@noble/hashes` 预优化警告，但未阻止首页加载。

# Drawer divider 隔离验证

使用真实 ZXUI Drawer、Dialog、ConfigProvider、useDrawer 和业务 ThemeHost。仅提供本地测试内容，不访问业务 API，不连接用户现有浏览器。

从 `ruoyi-fastapi-frontend/` 执行，分别在两个终端启动服务和检查脚本：

```bash
./node_modules/.bin/vite --config tests/fixtures/drawer-divider/vite.config.ts
node scripts/check-drawer-divider.mjs
```

默认从 `/Users/hqz/Downloads/element-plus` 加载源码；可通过 `ZXUI_LAYOUT_REPO` 指定另一份 ZXUI checkout。

验证业务实际安装的 ZXUI 包：

```bash
DRAWER_TEST_INSTALLED=1 DRAWER_TEST_PORT=4200 ./node_modules/.bin/vite --config tests/fixtures/drawer-divider/vite.config.ts
DRAWER_TEST_URL=http://127.0.0.1:4200 DRAWER_EVIDENCE_DIR=../docs/reports/evidence/2026-10-13-zxui-drawer-divider/installed node scripts/check-drawer-divider.mjs
```

安装包模式不启用 ZXUI 源码 alias；两种模式均通过当前 ZXUI checkout 的公开 theme deployment 构建端生成主题资产，再交给真实业务 ThemeHost。这样可单独验证已安装的组件和样式，不把现有 vendor 主题 manifest 的 adapter identity 阻塞混入 Drawer 检查。此夹具构建通过不代表普通业务安装包生产构建通过。

```bash
DRAWER_TEST_INSTALLED=1 ./node_modules/.bin/vite build --config tests/fixtures/drawer-divider/vite.config.ts
```

检查覆盖：

- modal/inline/push × 默认、上层 Provider、就近 Provider、组件 true/false、恢复继承；四个方向及浅色/深色主题。
- 默认与自定义 footer、无 footer、`noTitle`、`with-header=false`、长短内容、滚动位置保持。
- 全屏、调整尺寸与复位、390px 移动端、Hook updateOptions、公共与分区 CSS 变量。
- 40 次 divider 切换的观察器、全局监听和 DOM 矩形读取增量；5 次开关后的活跃目标及监听数量；动画结束后的空闲 LayoutCount。

`noTitle` 沿用现有行为，仅隐藏标题内容，仍保留关闭按钮所在 header；移除整个 header 使用 `with-header=false`。

分隔线使用真实 border，默认开启时头尾各占 1px，正文自然减少 2px；区域 padding、外层高度和正文滚动归属保持正确。

证据输出包括 `browser.json`、`enabled.png` 和 `disabled.png`。`totalBounds` 统计整页矩形读取，测试切换阶段不调用几何快照；`ownedBounds/ownedRaf` 仅按源码栈识别 Drawer/shared modal，安装包压缩栈不用于这两项归属判断。观察器探针为统计而保留实例引用；活跃目标与监听数量是生命周期检查，不是堆内存或所有第三方资源的无泄漏证明。耗时是本机带探针的 Chromium 诊断值，未作为跨设备性能基准。

# ZXUI / RuoYi 剩余主题项收尾

本轮已完成此前清单中非仿真范围的剩余改造。问题主要在业务自建界面和第三方皮肤；可复用的源码解析与原生页签文字色问题在 ZXUI 修复。此结论不等于所有历史数据页面、所有交互状态均已逐页验收。

## 清单对账与归属

| 原优先级与项目 | 归属 | 本轮结果 |
| --- | --- | --- |
| P1 拓扑、设备图编辑器 | 业务 | XFlow 网格/背景通过公开 `useThemeAdapter` 读取 Host 已提交的实际颜色，随图实例就绪和主题变化重绘；移除延迟初始化。Dag、控制栏、缩略图、右键菜单等界面消费语义 token。设备详情取消固定网格色。 |
| P1 表单设计器 | 业务 | 组件面板、画布、属性区、选中/拖拽区域、复制/删除操作去除固定紫蓝灰色。生成器样式源码没有主题色写入；既有生成契约测试通过。 |
| P2 Quill / wangEditor | 业务 | Quill 工具栏、字号选择器、选中/悬停态、tooltip、输入与默认正文表面映射主题；原始正文颜色与颜色面板色块保留。复核前批 wangEditor 适配。 |
| P2 VXE 表格与浮层 | 业务 | 新增 `vxe-theme.css`，消费安装版本公开变量，覆盖主表格、条纹、编辑、选择、校验和文档级右键菜单。沿用已有 validation 层。 |
| P2 窄屏顶部栏 | 业务 | 左侧可收缩、右侧操作区保留空间；窄屏压缩主题按钮与头像，保留可访问名称；长昵称和面包屑截断。 |
| P2 零散固定 UI 色 | 业务 | 两处 FileTypeSelector、401/404 页面完成映射；历史 utility 按实际消费者归类，见下文。 |
| P2 官方源码接入 | ZXUI | 新增公开 `zxuiSourcePlugin`，按 UI export map 精确解析入口，统一内部依赖 alias、Vue 去重、预构建排除和文件访问范围。业务删除约 90 行内部解析配置，只保留环境开关及路径。 |
| 实测新增：原生页签选中文字偏暗 | ZXUI | `theme-chalk` 的 EP 适配区将非禁用页签 active/hover 文字映射到 `accent.on-surface`；不在业务覆盖核心 `--el-*`。 |

源码插件位于 ZXUI `packages/theme-compiler/src/vite/source.ts`，通过 `@zxio/theme-compiler/vite` 导出。compiler 构建将 Vite 外置，增加可选 peer；中英文运维指南及 README 已说明源码插件与主题部署插件的分工。只新增 2 项解析回归测试，验证真实公共样式子入口、Host 入口、独立 feature 不被接管及未准备仓库的失败提示。

## 保留内容与边界

- 图模型的设备/协议颜色、用户保存的节点边属性、坐标和导出底色不随主题改写；设备外壳材质也保留。Dag 显式 `theme="dark"` 的兼容调用保留；未指定时跟随 Host。
- `Dag/config/edgeConfig.js` 的工具仅在配置聚合入口导出，没有发现活动调用；不借主题收尾修改未使用的模型默认值。
- `tailwind.css`、`theme.module.css` 的历史品牌阶梯与按钮工具类未发现活动非仿真调用；ThemeValidation 的灰阶演示只有统一导出，没有发现页面引用。本轮保留这些兼容定义，不将全局 gray/slate 重映射为主题色。活动文件选择器和错误页已单独修复。
- 仿真专用页面、整站显示缩放、独立 chart/drive 包契约、历史仓库级检查问题、发布 npm 和提交 Git 不属于本轮范围。

## 浏览器证据

浏览器使用本地端口 80 的源码直连应用。真实设备新增页面与公告弹框仅查看、切换、取消，没有保存业务数据。

| 范围 | 实测结果 |
| --- | --- |
| 9 主题 × light/dark | 18 个 Host 提交状态；每个主题明暗切换均改变网格与背景；网格 SVG 使用具体颜色，没有未解析 CSS var。 |
| 图数据及编辑内容 | 18 次图数据检查均不变；Quill、wangEditor 的用户指定红色均为 `rgb(255, 0, 0)`。 |
| 真实设备详情 | 陆军松枝绿明暗切换，网格重绘；设备外壳保持原样。详情未使用 XFlowBackground，实际底色由外层 `.xflow-graph` 承担，内部背景层透明是正常结构。 |
| 真实表单设计器 | 工厂蓝明暗验证；暗色页签的 computed color 已等于 `accent.on-surface`。 |
| 真实公告新增弹框 | 松枝绿暗色下工具栏、字号浮层、选中态可读，取消退出。 |
| VXE | 内存夹具验证暗色输入框、主表格及挂载到 document 的右键菜单。 |
| 顶部栏 | 768、390、320px 无文档横向溢出；320px 主题菜单和用户菜单均成功打开。 |

证据：[18 组主题记录](evidence/2026-09-27-zxui-remaining-theme-convergence/consumer-matrix.json)、[窄屏测量](evidence/2026-09-27-zxui-remaining-theme-convergence/navbar-responsive.json)、[设计器暗色](evidence/2026-09-27-zxui-remaining-theme-convergence/designer-dark.png)、[设计器浅色](evidence/2026-09-27-zxui-remaining-theme-convergence/designer-light.png)、[设备暗色](evidence/2026-09-27-zxui-remaining-theme-convergence/device-dark.png)、[公告暗色](evidence/2026-09-27-zxui-remaining-theme-convergence/notice-dark.png)、[第三方消费夹具](evidence/2026-09-27-zxui-remaining-theme-convergence/consumer-dark.png)。

验证边界：历史工程 DAG 和版本专属预览没有完成带真实记录的端到端访问，相关共享图形/富文本消费通过同一业务组件的内存夹具验证。错误页、文件选择器及部分拓扑浮层以源码、token 存在性、类型/构建检查覆盖；不宣称逐状态视觉验收。矩阵覆盖普通对比度、默认密度；不代表 forced-colors 或整站无障碍认证。

结束时恢复陆军松枝绿、深色、默认密度及常规视口，侧边栏展开。

## 检查与交付

| 检查 | 结果 |
| --- | --- |
| ZXUI 结构策略、样式拆分、Vite 部署与源码解析 | 42 项通过；其中本轮新增 2 项 |
| RuoYi `yarn ui:standards` | 静态规范及既有 14 项测试通过 |
| RuoYi `yarn type-check` | 通过 |
| 本轮业务 TS/Vue 聚焦 ESLint | 0 error、63 warning；警告未作为本轮主题改造扩大清理 |
| 本轮 ZXUI TS 聚焦 ESLint | 通过 |
| compiler、theme-chalk、ZXUI 构建 | 通过 |
| `theme-consumer:check:structural` | 单一来源、162+162+162 变体闭包、确定性构建与 tar 审计通过 |
| 业务源码直连生产构建 | 通过，29.75s，输出 `/tmp/ruoyi-remaining-source-build` |
| 业务安装包生产构建 | 通过，27.57s，输出 `/tmp/ruoyi-remaining-installed-build` |
| 本轮改动 `git diff --check` | 两仓通过 |

安装包 CSS 与 ZXUI 生成源字节一致，SHA-256 为 `158de5897802c5f8fb1ed7073e9dd9cacba7648c9adde6caf5ffa0e4105c5da5`。构建仍有已有的大 chunk、peer dependency 和插件提示，不宣称全仓检查全绿。

本地候选包与 lockfile 已更新：

- `vendor/zxio-zxui-3.0.0-next.0-remaining.20260927.tgz`
- `vendor/zxio-theme-compiler-1.0.0-source.20260927.1.tgz`

日常开发继续使用 `VITE_ZXUI_LOCAL=true` 与 `VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus`。未发布 npm、未提交 Git。两仓其他已有改动保留。

[机器可读检查摘要](evidence/2026-09-27-zxui-remaining-theme-convergence/verification.json)与构建、测试日志同目录保存。本报告收尾此前主题审计、优先级修复、Vite 资产部署、列表工具栏和表格密度报告中的本轮待办；各历史报告仍保留当时的验证边界。

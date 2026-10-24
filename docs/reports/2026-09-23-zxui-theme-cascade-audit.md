# 业务与 ZXUI 主题级联复核

日期：2026-09-23。范围：非仿真业务页面、共享外壳及 ZXUI 的 Element Plus 主题适配。

## 归属结论

| 现象 | 归属 | 源码证据与处理 |
| --- | --- | --- |
| `/system/role` 的角色顺序上下箭头与分隔线在深色主题下偏亮 | ZXUI 公共适配 | 业务正确使用 `el-input-number`。Element Plus 的步进按钮用根变量 `--el-fill-color-light`、`--el-text-color-regular`、`--el-border`；ZXUI 生成的根别名原用零权重 `:where([data-zx-theme])`，在 `html` 上输给 Element Plus 的 `:root`。已给根别名及 resolved 变体补一个主题属性权重，静态 bootstrap 同步识别。九套主题统一受益。 |
| 顶部和侧栏显示旧配色的疑虑 | 业务遗留声明与公共级联并存 | 主外壳当前已给顶部 `header`、侧栏 `panel`、Logo `brand` 表面角色；顶部与侧栏子元素在局部映射 ZXUI 语义色。旧全局蓝色渐变无实际消费者，已移除这些误导性的顶部/侧栏固定色声明。Element Plus 根变量修复也使顶部菜单及侧栏内的原生控件正确继承主题。 |
| 工程卡片固定蓝色、白底、灰字 | 业务 | `src/views/project/index.vue` 直接使用固定色与浅色渐变。已改为 card、accent、fill、text 等 ZXUI 语义 token。 |
| 设备协议抽屉固定白底、蓝色和灰阶 | 业务 | `src/components/business/Device/ProtocolListDrawer.vue` 使用浅色 Tailwind utility。已改为 card/header/canvas 表面和语义交互色。 |
| 布局设置存在独立的“侧边栏深/浅”选择 | 业务 | `sideTheme` 和旧 `theme` 只在设置 UI 与本地布局存储中读写，真实侧栏从未消费。已删除这两个无效状态及虚假的侧栏主题选项，主题包与明暗模式仍由 ZXUI 偏好入口管理。 |
| ZXUI 生成物已修复，但业务页面刷新后数字步进框仍显示旧颜色 | 业务开发服务部署缓存 | 运行中的 Vite 在启动时复制并固定主题部署资产。实测 `localhost` 返回的 defense-green CSS 仍为旧零权重根选择器；重启 Vite 后返回的新 CSS 已含修复后的选择器且哈希一致。业务 Vite 插件现监听本地 ZXUI 主题包的原子生成目录替换，重新部署资产并通知页面重载，避免后续重复出现源码与业务页面不一致。 |
| 角色表单未选中 radio/checkbox 的轮廓在深色背景上过暗 | ZXUI 公共主题契约与 Element Plus 结构样式 | Element Plus 的未选中描边沿用普通 `--el-border`，而深色主题的普通边框是低透明度表面边框。业务无覆盖。经业务截图复核，改用普通 `semantic.border.default` 后 checkbox 有改善，但 radio 仍偏暗。现新增 `semantic.border.control`，从各主题的次级文字色推导，并让两种小控件的常态描边消费它；Element Plus 更具体的选中、焦点、悬停和禁用规则仍生效。 |

这次没有将 `el-input-number` 换成 `ZxInputNumber`：ZXUI 文档明确允许已有 Element Plus 步进输入继续使用，后者也依赖同一公共主题别名。替换业务标签不能修复所有业务库的根变量级联。

## 主题覆盖判断

业务登记的 default、defense-green、army-pine、air-gray、pap-olive、rocket-moss、factory-blue、tech-blue、industrial-blue 均由同一个 ZXUI Host 和 deployment API 切换。没有发现某一个主题缺少导航的 `header/panel/brand` 角色；本次公共级联缺陷同时影响九套主题的 Element Plus 根变量。

业务仍有以下非仿真主题消费缺口，归属均在业务，不能通过改变 ZXUI 主题种子掩盖：

- `src/assets/styles/theme.module.css` 与 `tailwind.css` 仍含固定的 Tailwind 色板和通用 utility；本轮只移除已确认无消费者的导航固定色。当前非仿真页面对 `primary-*` utility 的直接消费集中在本轮已迁移的设备协议抽屉，其余色板多数是未消费的历史定义。全局重映射灰阶会影响领域配色，需按实际消费者逐项迁移。
- `src/views/project/components/NodeEditDrawer.vue` 被非仿真拓扑页复用，但使用仿真变量及固定暗色 fallback；它同时被仿真页引用，改动时须保留仿真用途。
- `src/components/ui/RichEditor/src/Editor.vue`、`VxeTableValidation/validation.less`、`src/components/business/ZxFlow/`、`src/views/device/detail.vue`、`src/views/project/entry.vue`、`src/views/register.vue`、`src/components/ui/Crontab/index.vue` 仍有固定 UI 色。图表系列色、用户正文色和拓扑数据含义色需要单独判断，不能机械替换。
- `src/components/ui/FloatingPanel/index.vue` 仍以固定 slate 灰阶实现明暗分支；共享消费者应改为 ZXUI 表面与文字语义。

## 验证与边界

- ZXUI 定向适配器与 bootstrap 测试：26 项通过；主题编译检查：1458/1458 变体及生成字节匹配；theme-compiler TypeScript 检查通过。
- 业务 `yarn type-check` 与源码直连的 `yarn build:demo-offline` 通过；设置 Store 的现有测试已缩减为真实契约的 3 项并通过；本轮修改 `git diff --check` 通过。
- 在运行中的 `http://localhost` 上复核了真实主题资产：服务重启前返回旧选择器，重启后九套主题的公开部署 CSS 均返回新选择器，内容哈希匹配；本地主题重编译后，监听器重新写入业务开发部署目录。Vite 插件修改通过 ESLint 与 `yarn type-check`。
- ZXUI 结构样式源、镜像及分包构建同步完成；`theme-consumer:check:structural`、主题编译检查、公共契约与适配器定向测试通过。九套主题的新控件描边与字段底色的计算对比度：浅色约 3.2–3.5，深色约 4.1–4.7。运行中的业务 Vite 已返回新 token 和 radio/checkbox 描边规则，`yarn type-check` 通过。
- 业务已有工程列表文件的 ESLint/Prettier 格式问题较多；本轮新引入的两处格式问题已修复，没有对整文件做无关格式重排。
- 当前约束不允许 computer use，因此未宣称已在浏览器对 `/system/role`、顶部和侧栏逐主题完成视觉验收。源码、运行服务返回的 CSS 和真实业务源码构建均已核对；修复后的页面视觉状态仍需用户刷新观察。

前次导航与登录页的 9 主题 × 2 模式浏览器矩阵见 `docs/reports/2026-09-22-zxui-theme-adoption-audit.md`；它属于前次版本的证据，不替代本次改动后的视觉验收。

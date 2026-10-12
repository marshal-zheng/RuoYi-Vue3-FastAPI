# ZXUI 主题设计与 RuoYi 业务接入评估

评估日期：2026-10-11。

**判断：保留现有主题内核，优先完善公共接入链路，并收敛业务残留样式。** ZXUI 已具备支撑多业务的主题能力；当前最明确的差距，是 docs 已具备的应用级体验和优化尚未全部进入公共消费路径。业务同时保留固定色盘和局部绘图样式，因此不能将所有页面问题归因给主题包。

本报告中的 ZXUI 指 `/Users/hqz/Downloads/element-plus`，不是上游 Element Plus。业务基于 `/Users/hqz/dev/RuoYi-Vue3-FastAPI` 当前工作副本，包括本次开始前已存在的未提交修改。

本轮完成源码、现有生成产物和 Vite 虚拟模块的数据测量；没有修改产品代码、运行 lint/build、新增测试或操作浏览器。顶部和侧栏的当前可见异常仍需页面复现，以下不会将源码推断表述为页面验收结果。仿真专用界面、导出画布背景、设备材质和协议分类色不纳入普通界面颜色替换。

## 已有能力与保留理由

| 能力 | 当前证据 | 判断 |
| --- | --- | --- |
| 单一主题来源 | Seed → foundation/semantic → compiler → theme package → Host/Provider | 保留，不另建业务主题引擎 |
| 表面角色 | canvas、panel、card、field、header、overlay、blocking、selected、brand，每类具有填充、边界、外阴影、内阴影、高光、主次文字 | 已能覆盖后台外壳和大部分业务自有容器 |
| 多维变化 | mode、density、contrast、motion、radius；每个主题已有 162 个变体 | 具备能力，不意味着业务每处样式已消费全部轴 |
| 可读文字 | on-surface 与 on-fill 分离，按钮不同填充状态各有前景角色 | 方向正确，避免品牌色同时承担所有文字职责 |
| 作用域和浮层 | app-scoped Host、嵌套 Provider、Portal、事务式提交和失败保留 | 是多业务复用需要的底座 |
| 外部组件消费 | 业务扩展模块、CSS/JS adapter、theme-consumer 协议、display layout participant | 已有扩展机制，优先补标准适配和示例 |
| Tailwind | `@zxio/theme-tailwind/v4.css` 使用 `@theme inline` 映射公共语义 | 已有公共能力，业务尚未接入这条路径 |

关键源码：[主题派生](</Users/hqz/Downloads/element-plus/packages/tokens/src/kernel/derivation.ts>)、[surface 结构样式](</Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css:5948>)、[业务扩展文档](</Users/hqz/Downloads/element-plus/docs/zh-CN/guide/theme-extensions.md>)、[周边库协议](</Users/hqz/Downloads/element-plus/docs/zh-CN/guide/theme-consumer-protocol.md>)。

## 色值测量

读取九个现有主题的已生成 CSS，选择 light/dark，其他轴固定为 density-default、contrast-normal、motion-full、radius-default。递归解析公共 CSS 变量到 sRGB 色值，计算前景与不透明背景的相对亮度比。

- 18 个主题与明暗组合，核算 288 对 surface 主次文字与基础填充色；最小值约 4.65:1，来自 industrial-blue 深色 brand 次级文字。
- 额外核算 90 对强调色/状态文字与 surface-body，最小值约 8.56:1。
- 36 对半透明 selected 表面文字未计入，因为结果依赖其实际底层背景。
- 没有把渐变、高光叠加、抗锯齿、焦点、控件边界、悬停、运行时 Seeds 覆盖或高对比变体包含在上述结论中。

这些结果支持“现有默认配色不需要先重做”，不代表整页 WCAG 合规。普通文字 4.5:1 的参考阈值和例外见 [W3C 对比度说明](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)。

逐主题结果见 [色值测量数据](./evidence/2026-10-11-zxui-theme-assessment/contrast.json)。

## 应由 ZXUI 优先优化的部分

| 优先级 | 优化点 | 事实依据 | 建议落点 |
| --- | --- | --- | --- |
| P1 | 公共 Vite 主题元数据交付 | 公共插件直接序列化完整 deployment；docs 使用私有无损压缩模块 | 将已验证的压缩能力下沉到 compiler 公共交付路径，保留资产身份和校验 |
| P1 | 普通业务的最短接入路径 | RuoYi 自己实现偏好读取、迁移、更新队列、失败反馈、Provider bridge 和 document 投影 | 提供可选应用级 controller/recipe；存储端口可配置，继续复用现有 Host 事务 |
| P1 | surface 公共契约的稳定性 | 九类 surface 的 63 个 facet 均由 `surfaceContractEntry` 标为 experimental，却已用于 docs、结构样式和真实业务外壳 | 确定稳定消费子集、兼容承诺和迁移策略；不要仅机械改 lifecycle 标签 |
| P1 | 外壳交互的标准消费示例 | 背景角色已具备，业务仍大量手写菜单 hover/selected/collapsed 与 `!important` | 提供 header/sidebar/tabs 的可复用样式 recipe，成对规定前景、背景、焦点和选中状态 |
| P2 | 第三方适配的复用交付 | RuoYi 已有 VXE CSS 映射、虚拟布局 participant、X6 JS adapter，但仍是业务私有代码 | 从真实页面提炼独立适配模块，限定受支持版本；不把 VXE/X6 私有细节塞入内核 |
| P2 | 将 docs 的主题检查能力供业务使用 | docs Theme Lab 已有 inspector、scope 信息和探针；业务缺少同等便利入口 | 提供可选开发工具，显示主题身份、作用域、角色、最终值及覆盖来源 |
| P2 | 密度、字体、动效的应用级配套 | 内核和 display 层已有能力；业务 header、主题按钮、tabs 仍有固定尺寸/动效 | 明确哪些属于布局尺寸、哪些随 density/display/motion；保留固定几何的合理用途 |

P1 表示下一轮优先投入，不表示每项都已构成生产故障。此次没有证据支持“主题引擎整体失效”或需要重写内核。

### 公共交付体积的实测差距

在业务目录以 Vite middleware 模式加载实际配置和 `virtual:zxui-theme-deployment`；不监听端口、不启动浏览器、不执行 build。当前本地源码直连启用，登记九主题，deployment 含 2,934 条资产条目。

| 同一份数据 | 公共插件当前输出 | 使用 docs 现有压缩器 | 减少 |
| --- | ---: | ---: | ---: |
| 模块文本 | 6,744,285 B，约 6.43 MiB | 1,478,253 B，约 1.41 MiB | 78.1% |
| gzip | 1,022,164 B | 444,744 B | 56.5% |
| Brotli | 429,584 B | 287,217 B | 33.1% |

压缩模块解码后，`JSON.stringify(decoded) === JSON.stringify(original)` 为 true。测量的是开发虚拟模块及同输入编码结果，不是生产 bundle、网络实测或首屏时延；不能将这些比例直接表述为页面提速比例。2,934 条条目也不表示首屏下载全部 CSS，当前 Host 使用 on-demand stylesheet policy。

这是最明确应回到组件库处理的优化，业务不应复制 docs 压缩器作为永久方案。进一步的登记懒加载和变体元数据裁剪需单独评估，不能破坏完整性和按需解析契约。

证据：[公共插件序列化位置](</Users/hqz/Downloads/element-plus/packages/theme-compiler/src/vite/index.ts:243>)、[docs 压缩器](</Users/hqz/Downloads/element-plus/docs/.vitepress/build/compact-theme-data.ts>)、[原始测量](./evidence/2026-10-11-zxui-theme-assessment/deployment.json)。

### 外观设计应怎样继续优化

现有 shadow、tonal、glow 材质已经能够表达不同品牌气质。下一步应明确应用区域的使用节制：长时间工作的表格、表单和导航优先保持安静的内容底色；品牌和发光效果用于适当的强调区域。保留当前用户满意的主题外观，以真实高密度页面验证层级，避免把所有容器都当成需要明显边框、阴影和高光的卡片。

这是设计建议，未经过当前业务页面的视觉比较，不能认定现有 glow 主题已经过重。也不建议立即新增“材质强度”第六轴；先用现有 surface、theme seeds 和业务扩展表达，再判断是否有跨业务重复需求。

角色组合应形成明确约定：header/panel/canvas 用于外壳；card/field 用于内容和输入；overlay/blocking 用于浮层。hover、selected、pressed、focus 是交互状态，应成对使用其前景与背景。`accent.base` 适合作为品牌填充/标识，正文链接应优先选择 `accent.on-surface`。

## 应由 RuoYi 调整的部分

| 区域 | 当前代码事实 | 归属与建议 |
| --- | --- | --- |
| 顶部和侧栏外框 | `layout/index.vue` 已有 header surface，Sidebar 已有 panel surface，Logo 已有 header surface | 已部分接入。当前可见异常须检查生效样式、资源版本和选中变体，不能声称完全未接主题 |
| Tailwind 色盘 | `tailwind.css` 与 `theme.module.css` 重复声明固定 primary/success/gray 等色阶；`.card` 仍 `bg-white`；success 部分色阶甚至来自蓝色系 | 业务责任。接入现有公共 adapter，迁移实际主题用途的类；保留有明确领域含义的固定色 |
| 业务别名与作用域 | 多个业务颜色 alias 在 `:root` 定义；`projectZxThemeScope` 向 html 写入 theme/variant 属性，恰好命中生成主题 CSS 选择器 | 不是纯观察属性，会在 document 上激活全套主题变量。当前单根应用可以工作，但嵌套主题、卸载和多个 app 的所有权容易混淆。按业务边界重绑 alias，明确 canvas/portal 策略 |
| 侧栏交互 | hover 使用 selected-on-text，但背景保持 panel/透明；选中与悬停依赖较多业务强制样式 | 成对统一交互语义。目前内置 selected 与 panel 主文字可能相同，故不将它夸大为已证实的对比度故障 |
| 设备详情图形 | 已路由到 `views/device/detail.vue`，端口填充固定 `#fff/#e8f3ff`，标签固定灰/蓝 | 业务责任。节点底色、文本、选择态通过已有 JS adapter 随主题更新；协议分类的 stroke 不机械替换 |
| 图编辑器 | `useGraphTheme` 已使背景和网格消费 Host；部分 shape/port 仍有固定值 | 继续完善已有适配，不再用第二个 `isDark ? ... : ...` 色盘 |
| VXE | 已有主题 CSS 映射和布局事务 participant | 不应被列为“完全没接主题”。优先核对虚拟滚动、浮层和局部 scope 的实际效果，再提炼复用层 |
| 字体、密度、动效 | header/主题开关存在固定高度，主题开关固定 32px/13px，tabs 和菜单有固定过渡 | 分类调整；固定侧栏宽度、图形尺寸不必一律 token 化 |

关键业务源码：

- [顶部布局](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/layout/index.vue:12>)、[侧栏](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/layout/components/Sidebar/index.vue:103>)。
- [Tailwind 固定色盘](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/assets/styles/tailwind.css:1>)、[业务根别名](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/assets/styles/theme.module.css:85>)。
- [document 投影](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/theme/zx-theme-config.ts:144>)、[业务偏好事务 bridge](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/theme/ZxThemePreferenceBridge.tsx>)。
- [设备端口配色](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/views/device/detail.vue:447>)、[图形主题 adapter](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/components/business/ZxFlow/composables/useGraphTheme.ts>)、[VXE 布局适配](</Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/src/plugins/vxe-layout.ts>)。

不能把检索命中数当成缺陷数量：旧 dashboard 路由在静态 router 中已注释；DAG matrix 入口存在注释代码；VXE 校验样式中的一部分固定色位于 `.simulation-dark`。这些与当前活跃业务页面应分别处理。预览色块、图片、导出白底、设备材质和分类编码也不应自动跟随主色。

## 对照成熟组件库与应用案例

| 官方方案/案例 | 已核查做法 | 对 ZXUI 的启发 |
| --- | --- | --- |
| [Ant Design 主题](https://ant.design/docs/react/customize-theme/) 与 [ProLayout](https://procomponents.ant.design/en-US/components/layout/) | Seed/Map/Alias 派生、局部主题、组件 token；ProLayout 暴露 layout token 和外壳定制面 | 内核继续集中派生；把常见外壳消费方式变得明确，避免业务反复覆盖内部类名 |
| [MUI 官方 Dashboard](https://mui.com/material-ui/getting-started/templates/) | Dashboard 使用共同 AppTheme，合并 Data Grid、Charts、Date Pickers、Tree View 的定制；侧栏读取 background.paper、divider、text.secondary | 一个主题应覆盖整页和周边组件。ZXUI 的参考模板应走公开接入路径，包含真实表格和图形 |
| [Carbon UI Shell](https://www.carbondesignsystem.com/building-blocks/core/components/ui-shell-header/specifications) | 将 header、菜单各状态的背景、文字、图标、焦点映射到明确 token；shell zone 可以使用局部主题 | 给出完整状态表和区域主题规则，比单独增加一个 sidebar 背景变量更有效 |
| [Carbon 层级色](https://www.carbondesignsystem.com/building-blocks/foundations/color/guidelines) | 区分页面层与上下文层，使用 layer 组件管理 contextual token | 检查抽屉内卡片、卡片内输入等层次；先澄清现有 role 使用，再决定是否需要层级扩展 |
| [MUI CSS 变量](https://mui.com/material-ui/customization/css-theme-variables/overview/) | 说明切换、首帧与 CSS 变量的收益，同时明确 HTML 体积等代价 | 对外提供明确的加载成本、启动策略和部署说明；不能仅以 docs 首屏体验代表公共业务链路 |

MUI 案例还核查了 [Dashboard 源码](https://raw.githubusercontent.com/mui/material-ui/master/docs/data/material/getting-started/templates/dashboard/Dashboard.tsx) 和 [SideMenu 源码](https://raw.githubusercontent.com/mui/material-ui/master/docs/data/material/getting-started/templates/dashboard/components/SideMenu.tsx)。以上是官方文档/模板的结构性对照，未操作其在线演示，也不将模板视为已审计的商业生产系统。

上游 [Element Plus 暗色方案](https://element-plus.org/en-US/guide/dark-mode) 以 CSS 变量和 `html.dark` 为基础。ZXUI 当前拥有更完整的应用作用域和交付协议，适合保留；业务不应再叠加一个与 Host 独立的全局暗色控制源。

## 建议执行顺序与验收边界

1. **先复现外壳问题。** 固定同一 themeId/mode/density，检查 header、Logo、sidebar 的最终 fill/highlight/edge/on-text、CSS 覆盖来源及主题资产。对照 docs 的同角色，不要求主题变化一定表现为大面积品牌主色。
2. **收敛业务第二套主题来源。** 先处理公共 Tailwind 入口、业务别名和外壳交互，再处理设备详情图形的背景、标签和选中态；不批量重涂协议/状态类别色。
3. **下沉 ZXUI 的公共优化。** 将元数据压缩纳入公共 compiler，提供最短业务接入 recipe，并把主题生命周期、canvas 和原生 Element Plus 浮层的接入方式讲清楚。
4. **再稳定跨业务契约。** 根据 RuoYi 的真实页面选择稳定 surface 子集，整理 VXE/X6 的可复用适配和主题诊断工具。

视觉验证优先覆盖默认、军工绿、科技蓝、工厂蓝的明暗模式，再巡检全部九主题。代表页面采用设备列表/详情、用户管理、表单抽屉和拓扑编辑；关注焦点、hover、selected、disabled、弹层、刷新恢复，以及紧凑密度下表格行高与滚动位置。无需为本轮评估新建大量测试，也无需用全部 162 个变体做页面穷举。

**当前交付状态：整体设计评估完成；产品代码未改；顶部/侧栏现象尚未完成浏览器复现和修复验收。**

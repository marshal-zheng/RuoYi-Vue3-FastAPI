# Drawer / Dialog 统一浮层布局

最新验收为 [2026-10-14 独立审查与修复](2026-10-14-independent-overlay-lint-review.md)：修复清 lint 漏验回归、撤销库新增规则豁免并收口真实类型/数据契约，已重跑组件库、业务全量及源码/安装包布局矩阵。

后续验收：此前剩余的 1230 条业务 lint 警告已清零，规则未放宽；真实 API、mock、OpenAPI 和生成类型已按新契约同步，组件库及业务前端已再次全量验证。最新结果见 [业务 lint 清零与真实契约硬切](2026-10-13-business-lint-cleanup.md)。本报告下文保留前一阶段的历史验证记录。

## 交付与范围

已在 ZXUI 组件库实现一套共享布局契约，当前业务安装本地构建包。用户后续明确授权在研阶段硬切，因此本轮清理旧布局入口，并同步已知调用；不保留旧布局行为分支。

库源码位于 `/Users/hqz/Downloads/element-plus`，业务位于本仓库。两个工作区原有未提交改动均保留；本轮以 `/tmp/zxui-overlay-layout-baseline-20261013` 的 27 文件快照界定增量。业务 `src/App.tsx` 原有 divider 配置未改动。没有提交、发布 npm 包或创建/修改角色、用户等业务记录。本次全量格式修复包含仿真目录的格式整理；仿真功能未迁移。后续全量收尾以 `/tmp/zxui-overlay-full-validation-baseline/business` 及库侧全量验证快照界定增量。

## 最终契约

| 责任 | 实现 |
| --- | --- |
| 默认四边留白 | 从所属主题的 density / display 间距角色派生，组件不写死 16/24px |
| 三段横向对齐 | header、正文和 footer 消费共享横向留白；LTR/RTL 使用逻辑边 |
| 分割线 | 画在分区边缘内；开关、粗细不改变正文几何或滚动位置 |
| 普通内容 | 两组件 `bodyScroll="auto"` 都使用正常文档流，正文视口负责滚动 |
| 编辑器、虚拟表格、分栏 | `bodyScroll="none"` 提供有界 flex 布局，内容自行管理滚动 |
| 配置层级 | 单实例 → `zxDialog` / `zxDrawer` → `overlayLayout` → 所属主题配方 |
| 覆盖粒度 | 共享 `paddingInline`；独立 `headerPadding`、`bodyPadding`、`footerPadding` |
| 参数形式 | CSS shorthand 字符串、非负 px 数字、逐逻辑边对象；支持 `var/calc/clamp` |
| 恢复与清零 | `undefined` 继承；`0` 清零；对象 `all` 重设基准后再覆盖指定边 |
| Hook | 两个 Hook 接受同名选项、ref 和 `updateOptions` |
| 嵌套弹层 | 单实例内部变量在每个根重置，选择器限定直接分区；Provider 正常继承 |
| 扩展 | 移动端 gutter、底部 safe-area、命中区下限；布局不依赖 ZXUI namespace |

主题默认配方先使用已完成 display 投影的间距角色；显式 API 长度保持原值，不重复缩放。公开组件角色包括 `--zx-overlay-padding-inline`、`--zx-overlay-{header,body,footer}-padding-block`，以及共享/逐区 divider 变量。

```vue
<ZxConfigProvider
  :overlay-layout="{ paddingInline: 'clamp(1rem, 2vw, 2rem)' }"
  :zx-dialog="{ bodyPadding: { blockEnd: '2rem' } }"
>
  <ZxDrawer :body-padding="{ blockStart: 0 }" />
  <ZxDialog height="70dvh" :body-padding="0" body-scroll="none">
    <BusinessEditor />
  </ZxDialog>
</ZxConfigProvider>
```

虚拟内容需要宿主、全屏或显式高度形成有限空间；滚动归属本身不将自然高度 Dialog 变为满屏。业务可以组合内部带留白区域、铺满区域和独立滚动区。默认 footer 合并底部安全区；没有 footer 时由正文默认留白合并。显式分区 padding 由调用者决定。

header/footer 保持可见溢出。原生 scrollbar 的实际占宽由既有 ResizeObserver 回调同步到逻辑边距，保持三段与正文 client area 对齐。自动滚动模式在既有 observer 上增加 body 观察目标；没有新增 observer 实例、全局监听或轮询。滚动探针为内容盒内绝对定位元素，不再占流或抵消 padding。

## 硬切迁移

- 移除 `noContentPadding`；统一通过 `bodyPadding: 0` 清空正文留白。
- 移除 `--zx-dialog-{header,body,footer}-padding` / `--zx-drawer-{header,body,footer}-padding` 专属 CSS 别名；分区覆盖走公共 API。
- 移除旧 divider 修饰类及 Drawer 专属 divider 别名；两组件使用共享 divider 状态和角色，逐区外观使用 `--zx-overlay-header-divider` / `--zx-overlay-footer-divider`。
- 库内 ConfirmInput、业务代码预览和 DagMatrixDialog 改为 `bodyPadding: 0`；ProtocolFormDrawer 删除旧布尔绑定。
- RoleFormDrawer 删除额外的 `padding: 0 4px`，正文跟随组件统一 gutter。

主要源码：

- `/Users/hqz/Downloads/element-plus/packages/components/_shared/overlay-layout.ts`
- `/Users/hqz/Downloads/element-plus/packages/components/_shared/use-modal-scroll.ts`
- `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`
- ConfigProvider、Drawer/Dialog props/templates、两套 Hook、公共类型和双语文档/示例。

当前包：`ruoyi-fastapi-frontend/vendor/zxio-zxui-3.0.0-next.0-overlay-validation.final.20261013.tgz`；公开 compiler、九个主题包及 Tailwind 适配包同步更新为当前构建产物。package.json/yarn.lock 已更新，现有 hooks resolution 保留。ZXUI 包 SHA256：`07005ff2f4d315d2abd1d645f86e95ec15b4b88b10740d3a078fd0e66019e4ba`。完整安装包身份见 [installed-artifacts.json](evidence/2026-10-13-zxui-overlay-layout/full-validation/installed-artifacts.json)。

## 验证

| 检查 | 最终结果 |
| --- | --- |
| ZXUI 根 lint、五套 typecheck、UI contracts 四阶段 | 全部通过；lint 0 error / 0 warning |
| ZXUI 完整 test:run（真实 exit 0） | Vitest 338 文件 / 2474 项；Node 39 项；MCP 84 项；authority 3 personas / 21 阶段 valid |
| ZXUI build:theme、build、公开 compiler build | 通过 |
| 准入新契约与写入负控 | 69 项通过；独立审查 P2 已闭环 |
| Host 生命周期计时补充 | 单进程两文件、3 项通过；各 20 次真实生命周期采样 |
| 主题部署工具资产监听 / 事务恢复 | 9 项通过；CSS-only、原子目录替换、资产计划收缩/扩展、发布期间源漂移、关闭释放均验证 |
| 主题部署压缩 | 4 项通过；gzip 499009 bytes，保留 500000 原预算 |
| 当前协议打包 / 冻结基线 | 独立 ESM/CJS/types/浏览器通过；gen3 正常准入，旧 gens 拒绝且字节不变 |
| Chart 独立包测试 / typecheck | 27 项通过 / 通过 |
| 业务完整 lint / typecheck | 0 error、1230 既有 warnings / 通过 |
| 业务完整 Vitest | 82 文件、680 项通过 |
| 业务 UI standards | 505 文件、0 违规；14 项测试通过 |
| 业务纯安装模式生产构建 | 通过 |
| 离线业务 E2E | 官方 Playwright runner：核心 1 项、页面状态 8 项通过 |
| 源码 / 安装包布局矩阵 | 各 156 项通过，pageErrors 0 |
| 源码 / 安装包 divider 生命周期与交互 | 各 26 项通过 |
| 实际角色 Drawer / 用户 Dialog | 两主题 × 两组件 × 桌面/移动端，8 项通过；四边几何、正确主题/模式、零业务写入 |
| 独立只读审查 | 全量收尾增量无剩余 P0/P1/P2 |

布局矩阵覆盖：1440/390 宽度、默认浅色/军绿深色、两组件、compact/default/comfortable、90/100/125 display scale 和 LTR/RTL。扩展场景检查 shorthand 变量、逐边继承/恢复、显式零、主题角色、距离场景不重复缩放、自然高度、委托滚动、经典 12px 原生 scrollbar、自定义 namespace、嵌套隔离和默认行内流。

40 次间距/divider 更新前后，observer、全局 listener 和几何读取计数相同。5 次关闭/重开循环后，关闭态 observer 目标为 0，活动全局 listener 数恢复基准。divider 性能验证的空闲 layout 数为 0。

浏览器验证使用独立 headless Chromium；真实业务验证只打开/关闭表单，不提交角色或用户记录。安装包夹具的主题由库 checkout 的公开 deployment API 交付；另外已独立执行整套当前 vendor 的纯安装模式业务生产构建。离线 E2E 的写入仅发生于独立浏览器 IndexedDB，未调用真实后端写入。

### 本轮全量收尾

- 修正 HTTP mock 的调用签名；刷新公开 compiler 类型与主题资产身份，不在业务补写库类型或新增兼容 shim。
- 完整业务 ESLint 的 872 个格式错误清零；业务 1230 条既有非格式 warnings 保留。完整业务源码快照对比有 57 个文件变化，主要为格式整理、类型/mock/断言和包锁同步。
- ConfirmInput 及相关组件主题测试改为当前 surface/field/status 语义角色；不再断言旧混色百分比。包契约按实际公开 Host/Runtime 入口与独立 Chart 投影职责更新。
- 关闭确认硬切到所属 Host 的 ThemeFeedback；无 owner 时保留脏草稿，函数 guard 可由业务自管。Drawer/Dialog 共用事务与并发/取消保护。中英文文档及无 Host、owner confirm/cancel 回归已同步。
- 配置 store 等待已提交的主题偏好；Host 测试保留实际 controller API，验证绑定与释放职责；mock 数据断言匹配当前 seed 集合。Playwright / Node / MCP / 特殊 authority 测试由各自真实 runner 执行，常规入口显式组合这些检查。
- 修补 Timeline 已输出的 measured edge 变量对应的结构样式。组件回归与主题聚焦 133 项通过；独立 CSS 浏览器探针覆盖 24 场景、48 条边，端点/游标误差小于 0.1px。探针按组件渲染 schema 和 measured 变量验证结构 CSS，未把它标成 Vue Timeline + ThemeHost 完整端到端测试。
- 准入用 TypeScript AST 识别跨行/注释、对象键和复合赋值等静态写入；validator 独立验证所属文件及有限 selector/property/value 配方。公开 geometry 和 extension 声明保持独立职责，未知 paint/private/core 写入不能冒充已迁移。独立审查发现的 P2 用原始实际探针和新增负控闭环。
- 修复主题开发服务只监听 manifest/package、每轮重绑监听器导致的恢复丢失：稳定目录监听覆盖公开资产，失败恢复重试依然只校验公开导出。候选部署完整验证后才替换 active 数据/目录；失败保留旧 hash 资产及模块一致性。只改 CSS、源漂移和资产计划扩展的旧逻辑均有真实 RED，最后 9 项通过；compiler 重建打包同步业务后 typecheck/纯安装构建再次通过。
- 根 lint 排除 Git 对象、临时构建树、生成 MCP API、冻结证据和 Host 资产，保留它们的字节；未用格式器重写历史 receipt 或旧冻结 tarball。
- 修正只读库存单元测试与同轮文档生成器的共享 checkout 竞态：迁到真实隔离 Git 夹具，仍调用真实 capture/diff，覆盖 tracked/untracked/ignored/symlink 与 ignored CSS 改写漂移；生产只读门禁未修改。
- Vite 配置类型检查保留原有 63 个文件及 61 个 paths，通过临时 compile-only 配置绑定声明的根宿主 Vite；配置自动清理，运行时按各宿主解析。消费者夹具改用公开 Source/deployment/Host 契约并完成真实构建。

根默认测试仍保留两项 opt-in 计时 skip；对应两文件已另以规定的单进程环境运行，补充 3/3 通过。完整根测试重跑在源码/产物冻结后执行，最终真实 exit 0；早期失败日志保留作回归修复对照，不参与最终结果。

验收以标准根质量门禁和业务前端门禁为范围；根 AGENTS 明确排除的六个独立仓库不等同于本次全库覆盖。Chart 的局部检查已跑。未改后台实现，本轮未运行后台测试。未执行旧 spec 的完整发布/composite 流程；历史 theme-consumer admission/receipt 不被此次 unit PASS 替换。Task21 新测试只构造临时 synthetic unit fixture 来验证当前字节绑定和漂移拒绝，不作为实际 composite 运行证据。authority 输出明确为 `local-working-source-validation`、dirty 工作区，未冒充 clean release 准入。

### 可复跑入口

业务目录：

```sh
node scripts/check-overlay-layout.mjs
OVERLAY_TEST_URL=http://127.0.0.1:4300 node scripts/check-overlay-layout.mjs
DRAWER_TEST_URL=http://127.0.0.1:4299 node scripts/check-drawer-divider.mjs
node scripts/check-overlay-business.mjs
```

启动布局夹具：`DRAWER_TEST_PORT=4299 vite --config tests/fixtures/drawer-divider/vite.config.ts`；安装模式额外设置 `DRAWER_TEST_INSTALLED=1` 并改用 4300。测试期间服务仅绑定 127.0.0.1。正常开发服务 80/8088 保留运行。

## 证据

- [军绿深色角色 Drawer](evidence/2026-10-13-zxui-overlay-layout/full-validation/business/army-pine-drawer-desktop.png)
- [军绿深色用户 Dialog](evidence/2026-10-13-zxui-overlay-layout/full-validation/business/army-pine-dialog-desktop.png)
- [军绿深色移动端 Drawer](evidence/2026-10-13-zxui-overlay-layout/full-validation/business/army-pine-drawer-mobile.png)
- [军绿深色移动端 Dialog](evidence/2026-10-13-zxui-overlay-layout/full-validation/business/army-pine-dialog-mobile.png)

- [源码矩阵](evidence/2026-10-13-zxui-overlay-layout/full-validation/source/browser.json)
- [安装包矩阵](evidence/2026-10-13-zxui-overlay-layout/full-validation/installed/browser.json)
- [源码 divider](evidence/2026-10-13-zxui-overlay-layout/full-validation/divider-source/browser.json)
- [安装包 divider](evidence/2026-10-13-zxui-overlay-layout/full-validation/divider-installed/browser.json)
- [实际业务](evidence/2026-10-13-zxui-overlay-layout/full-validation/business/browser.json)
- 最终 [组件库完整测试](evidence/2026-10-13-zxui-overlay-layout/full-validation/zxui-full-validation-test-run-final.log)、[组件库类型检查](evidence/2026-10-13-zxui-overlay-layout/full-validation/zxui-full-validation-typecheck-final.log)、[业务完整测试](evidence/2026-10-13-zxui-overlay-layout/full-validation/ruoyi-overlay-final-tests.log)、[最终安装模式构建](evidence/2026-10-13-zxui-overlay-layout/full-validation/ruoyi-overlay-compiler-recovery-build.log) 均通过。其他本次全量构建、测试及门禁日志见 [full-validation](evidence/2026-10-13-zxui-overlay-layout/full-validation/)；首次交付日志保留于 `verification/`，旧状态报告仅作为历史存档。最终结论以本次全量日志为准。

## 调研取舍

[Fluent 2 Drawer](https://fluent2.microsoft.design/components/web/react/core/drawer/usage) 明确分离 header/body/footer，并通过 DrawerBody 提供正文滚动；[Ant Design Drawer](https://ant.design/components/drawer/) 提供分区语义样式及分区 token；[MUI DialogContent](https://mui.com/material-ui/api/dialog-content/) 将 dividers、theme defaults 和实例样式作为独立定制入口。

基于这些公开设计，本轮选择共享默认配方、分区/逻辑边覆盖和独立滚动归属，并加入本项目需要的 divider 几何稳定、Provider 层级及主题作用域隔离。这是针对当前业务约束的工程取舍，浏览器证据验证的是本库实现。

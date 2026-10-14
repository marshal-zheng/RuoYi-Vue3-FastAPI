# 组件库独立审查与修复（2026-10-14）

本次从源码和起始快照重新审查，未把前轮“通过”报告当作证明。审查对象是 `/Users/hqz/Downloads/element-plus` 根仓库拥有的 Drawer/Dialog、共享布局、Provider/主题桥接、相关 Hook/关闭流程，以及前轮全量验证对源码、测试和验证入口的修正。没有对六个独立包仓库做全库独立审查。

## 发现与处理

### P2：有效布局输入在新增测试中通过 any 绕过类型约束（已修复）

位置：`packages/components/_shared/__tests__/overlay-layout.test.tsx` 原 176–246 行；当前 35–37、176–241 行。

前轮新增的 Provider 合并及两个 Hook 用例把有效输入强制转换为 `any`，padding/scroll refs 也声明为 `ref<any>`。运行时断言虽然存在，公共 API 输入类型却没有参加校验；把 `bodyScroll` 拼成旧值时也不会产生静态错误。

已将公共/专用 Provider fixture 声明为 `ZxOverlayLayoutConfig`，逐实例输入声明为同一真实布局配置；Provider 合并使用 `Partial<ZxConfigProviderContext>`，Hook refs 使用 `ZxOverlayPadding | undefined`、`ZxOverlayBodyScroll | undefined`。去掉该测试中的全部新增 `as any`、`ref<any>`，保留原 runtime 合并、0 值、空值继承、undefined 恢复和两个 Hook 的断言。

独立 public consumer 编译证明：无需断言的 Provider 合并、逻辑边、ref 和 updateOptions 调用有效；旧 `noContentPadding`、非法 bodyScroll 和物理 `left` 输入确实被 TypeScript 拒绝。负控的 `@ts-expect-error` 仅存在于记录的独立编译探针，未引入产品代码。

### P2：库全量清理新增了规则关闭和扩大测试豁免（已修复）

位置：`internal/eslint-config/index.js:124`，以及原 `scripts/theme-consumer-protocol/{app.ts,packed-browser.ts,client.ts}:1`、`scripts/ai-production-hardening/check-local-authority-observation.mjs:1`。

原先通过新增 4 条 `eslint-disable` 和把原 `__tests__` 豁免扩展到所有 test/spec 后缀，使未解决的问题不再显示。只读独立 `--no-inline-config` 探针确实复现 6 条问题；恢复原 matcher 后又显示 `docs/.vitepress/theme/route-features.test.ts` 中的 6 条组件定义警告。这不符合用户禁止关闭规则的要求。

修复：

- ESLint 配置恢复到前轮全量起始快照的原始字节，未增加豁免范围。
- consumer 的 FailureProbe 与 packed 的 standalone 根组件抽为各自模块；打包 fixture 复制清单同步更新，保留真实 tarball/module-graph 验证。
- route-features 测试保持原文件位置与发现范围，空 Vue app 创建抽到一个独立 fixture 工厂。每次仍生成独立真实 App，5 项并发、失败重试、SSR 隔离和导航撤销断言保留。
- CLI 输出使用 `process.stdout.write`，保留 JSON/行文本和换行；删除新增禁用指令。
- 浏览器 Vue warn/error handlers 仍把反馈存入原数组。两个浏览器门禁通过 `captureConsumerFeedback` 读取并断言这些数组，保持失败可见；没有通过去掉 console 同时丢掉验证信号。该读取边界检查 unknown 对象与每一个字符串项，不使用 any、as never 或双重类型断言。

新增真实 Vue 负控：无法解析组件产生的 warning 和 render 抛错必须被反馈读取；错误形态和缺失记录必须失败。先观察到 2 项 RED，修复后 3 项全部通过。两套实际打包门禁使用隔离 headless Chromium（receipt `via: launch`），新拆模块确实交付，浏览器处理后的 warnings 仍为空且 dispose 完成。

## 审查结果与界限

在本次审查覆盖的生产逻辑内，未确认新的 P0/P1 行为破坏，也没有发现需要改动生产滚动、关闭或留白实现的缺陷。本次修复限定在测试类型、fixture 模块和门禁反馈/输出、原 ESLint 配置；未修改 Drawer/Dialog 的生产行为。

逐项核对了：

- 四边留白的 shorthand 与逻辑边合并，all 重置逐边、0 清零、undefined/空字符串继承，以及公共 Provider → 专用 Provider → 实例优先级。
- density/display 配方消费已投影的主题 spacing；显式长度保持原值，不重复缩放。divider 以边缘伪元素绘制，不参与布局；原生 scrollbar gutter 用现有 observer 同步 header/footer，逻辑 inline-end 支持 RTL。
- `auto` 文档流与 `none` 有界 flex/内容滚动分工；bodyPadding 为 0 不改滚动归属；业务必须提供有界高度的约束已写入公开文档。
- 关闭 guard 由 initiating Host/feedback owner 执行，无 owner 时 dirty 草稿保留；自定义业务函数 guard 可自行管理，独立重复关闭/旧会话状态保持现有事务保护。
- Hook 中新选项确实绑定并允许恢复 undefined。旧 noContentPadding 和组件专属 padding/divider CSS 别名没有留在执行实现中；检索命中仅为公开迁移说明。
- 新 autocomplete observer fixture 保留真实 ElAutocomplete 和 production hook；仅控制 MutationObserver/ResizeObserver/RAF 的交付。仍验证 fit prop、CSS 像素重测、两个 owner 隔离、coalescing，以及销毁后已捕获回调不再 updatePopper；未改变 production observer。
- 有限区域 Object.fromEntries 到 Record 的转换有完整三区域构造依据；未将外部 unknown 响应强转为业务对象。库 Hook 原有 any/defaultData 等不属于本次增量，未把它们宣称为已经全库类型清零。
- 两项主题断言及其余配方断言改为实际新 semantic/extension 契约，保留结构、边线、焦点与角色检查；没有通过删除整个行为断言或扩大整个 structural.css 匹配来制造通过。
- 全量门禁将 Node 契约测试、MCP Node 环境、authority 独立执行，有对应真实执行入口；局部工作树 authority 结果明确不等于 clean release。六个独立 Git 包继续由其自身负责验证。

本子任务没有复跑全库构建/2475 项聚合测试，也没有单独复跑业务页面或全量来源浏览器主题协议矩阵。这些由 root 在所有库/业务修复 freeze 后统一执行；下面是本子任务真正执行且读取过结果的证据。

## 执行证据

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 独立初始聚焦 6 文件 | 80/80 | `library-focused.log` |
| 原指令关闭的独立 lint 负控 | 6 条复现 | `library-disabled-rules-probe.json`、`library-repair-lint-red.log` |
| 恢复原 matcher 后全库扫描 | 仅 route-features 的 6 条 | `library-restored-rules-lint-scan.json` |
| 修复后原规则全库扫描（1894 文件） | 0 errors / 0 warnings，exit 0 | `library-lint-final.json` |
| 修复文件及关联 mts，--no-inline-config | 0 errors / 0 warnings，exit 0 | `library-repair-lint-green.log` |
| 最终聚焦 8 文件 | 88/88，exit 0 | `library-repair-focused-green.log` |
| 反馈负控 RED → GREEN | 2 失败 → 3 通过 | `library-feedback-red.log`、最终聚焦日志 |
| 公共布局正/负类型 consumer | exit 0，非法输入拒绝有效 | `library-public-layout-consumer.ts/.log` |
| 完整 Vitest 类型 | exit 0 | `library-repair-vitest-types.log` |
| protocol tools/browser 类型 | 均 exit 0 | `library-repair-protocol-tools-types.log`、`library-repair-protocol-browser-types.log` |
| 来源浏览器 production build | exit 0 | `library-repair-browser-build.log` |
| 实际 packed ESM/CJS/types/cross-copy | exit 0，headless launch | `library-repair-protocol-packed.log`、`library-repair-packed-receipt.json` |
| hosted packed public leaves + SSR/browser | exit 0，headless launch | `library-repair-protocol-hosted-packed.log`、`library-repair-hosted-packed.json` |

本轮作用域差异记录：`library-starting-diff.patch` 以 2026-10-13 起始快照区分在研原有 dirty 改动；`library-repair-before/` 保留此次审查修复前字节；`library-repair.patch` 与 `library-repair-manifest.json` 保留本次 before/after 及新增文件 hash。临时公开类型探针目录已删除，没有提交或发布。

注意：协议浏览器 fixture build 会清空并重建其私有 generated dist。最初将它与 fixture 类型检查并行，曾造成暂时找不到 example-panel 声明；改为先完成 build 再运行两项类型检查后均通过。最终结果不使用该并行失败来推断接口有问题，也不隐藏此执行顺序限制。

建议 root 的最终顺序：`pnpm lint` → `pnpm typecheck` → `pnpm ui-contracts:check` → `pnpm build:theme` → `pnpm build` → 设置新 evidence 目录后 `pnpm test:run`；业务源码/安装包 UI 检查在这些 owning builds 完成后执行。

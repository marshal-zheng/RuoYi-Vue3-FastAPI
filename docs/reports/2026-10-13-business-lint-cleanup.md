# 业务 lint 清零与真实契约硬切

2026-10-14 后续独立审查发现并修复了此阶段测试未覆盖的注册、仿真错误降级、端口筛选和实时状态回归，以及库规则豁免、SDK/mock 和旧原型缺口。最新全量结果为业务 805 项、库主测试 2478 项通过，见 [独立审查与修复报告](2026-10-14-independent-overlay-lint-review.md)。下文保留此前阶段的历史证据，不代表这些缺口当时已被覆盖。

业务源码原有 1230 条 ESLint 警告已全部修复，最终检查 602 个文件，0 错误、0 警告。组件库和业务前端的标准全量门禁通过；本报告接续 [Drawer / Dialog 统一布局报告](2026-10-13-zxui-overlay-layout.md)，其中此前留下的 lint 警告已关闭。

## 范围与规则

起始告警涉及 200 个文件：基础工具 344 条、应用/API 382 条、业务组件 295 条、项目/仿真 209 条。本次源码增量包含必要的调用点、类型声明、生成拥有者与回归测试，共 232 个新增、修改或删除文件；数量不同于原告警文件数。

ESLint、两个 TypeScript 配置和 Vitest 配置与任务起始快照逐字节相同。没有新增 eslint-disable、ts-ignore/nocheck、as any、as unknown as 或 as never；公开泛型实际约束输入、行模型或结果。`lint` 和 `lint:check` 增加 `--max-warnings 0`，阻止后续警告进入标准门禁。检查范围没有缩小，源码 lint 包含仿真目录。

原警告包括 746 条 explicit-any、277 条 unused-vars、91 条 console、84 条 empty-object-type，以及 32 条其他规则警告。完整计数、配置 hash 与逐文件源码增量见 [lint-summary.json](evidence/2026-10-13-business-lint-cleanup/lint-summary.json)、[config-integrity.json](evidence/2026-10-13-business-lint-cleanup/config-integrity.json)、[source-changes-final.json](evidence/2026-10-13-business-lint-cleanup/source-changes-final.json) 和 [断言/屏蔽增量扫描](evidence/2026-10-13-business-lint-cleanup/source-unsafe-pattern-diff.json)。

保留两个工作区原有未提交改动，没有提交、发布或替换依赖版本。业务基线为 `/tmp/ruoyi-lint-cleanup-baseline-20261013`，后台扩展修正基线为 `/tmp/ruoyi-lint-backend-baseline`。

## 主要改动

- API 和业务表格改用生成模型、确切 DTO、ZXUI/VXE 公开行模型及实例类型。列表查询按真实 `loadData({query,pager})` 和 `updateState('query.field', value)` 契约处理，有真实组件调用回归。
- Vue 全局声明指向真实组件、工具和插件类型，删除无消费者的旧 TSX/defaults 工具及过时别名。动态 JSON、WebSocket 和错误数据在入口使用 unknown，并经过实际结构校验。
- FormDialog 对非法 width/height 明确抛错；未知反馈 key 在开发和生产都拒绝。图模型拒绝重复 ID 或非法身份更新，并保留原状态。没有把 console 日志搬到另一层以绕过规则。
- 修复 debounce 丢失末次参数、树构建混合数字/字符串 ID 和原型键问题、下载将空 204 当文件保存、生成 ElRate 丢失 max 等实际缺陷；相应测试先复现失败，再验证修正。
- 仿真目录只收紧类型、数据入口和必要回归，没有迁移 UI、状态机或现有乐观状态流程。WebSocket 数组和对象内部数组保留实际业务结构。

### HTTP 列表与生成模型

真实 `ResponseUtil.ok_resource(list)` 会输出 `{items}`。只看 service 返回 list 会得出错误的数组契约；本轮通过真实 `/getRouters` 请求和 controller/factory 产物确认这一点，并撤回早期数组判断。

路由、菜单、部门、字典选项、设备分类及仿真外层集合统一消费 `HttpCollection.items`；mock 同步实际 envelope，不保留 array/items/data 多形态兼容。部门非分页列表移除虚构分页字段。仿真带宽使用实际 `port_id` 参数；start/stop 返回 `{sessionId, action, status:'accepted'}`，创建会话资源不再虚构 projectId/versionId/createdAt 必填字段。

后台 `CollectionResult<T>` 使用必填的 `items: list[T]`。修正菜单、部门两项和字典四个错误 array schema，并为分类 options 声明确切 DTO collection；空对象、裸数组均有拒绝回归。实际响应工厂的 runtime envelope 未改变。

独立审查发现分类 `/options` 与 `/checkNameUnique` 被先注册的动态 ID 路由捕获，真实 ASGI 请求返回 422。静态路由已移到动态路由之前，唯一性查询按实际 `category_id` 传参；数字详情路由和资源输出仍通过回归。分类选项类型来自重新生成的 `DeviceCategoryOptionModel`。

通过后台 exporter 更新 `shared/openapi.json`，再运行正式 SDK 生成脚本，未手写生成结果。SDK 的维护源为 `scripts/openapi-client/*.template`；生成器版本及三个 helper 的上游 hash 锁定，未知结构变化拒绝处理。独立目录重生、幂等后处理、严格类型检查和 source/template 字节比较均通过。Fetch SDK 用真实公开泛型检查 request/method；204 JSON 返回 null，SSE 完成和错误类型按实际运行结果处理。

详见 [应用契约报告](evidence/2026-10-13-business-lint-cleanup/application-result.md)、[仿真 wire 报告](evidence/2026-10-13-business-lint-cleanup/project-wire-audit.md)、[最终独立审查](evidence/2026-10-13-business-lint-cleanup/review-final-collection.md) 和 [SDK 当前模板证明](evidence/2026-10-13-business-lint-cleanup/sdk-current-template-proof.json)。

## 最终全量验证

业务前端按以下顺序在冻结源码上执行，各命令真实 exit 0。验证前后 3805 个源码、测试夹具和配置文件的 hash 没有变化，见 [冻结检查](evidence/2026-10-13-business-lint-cleanup/business-gate-source-integrity.json)。

| 业务前端命令 | 结果 |
| --- | --- |
| `yarn lint:check` | 0 错误、0 警告；另保存最终完整 ESLint JSON |
| `yarn type-check` | 0 类型诊断 |
| `yarn test:run` | 98 文件，758/758 通过 |
| `yarn ui:standards` | 508 文件，0 违规；14/14 回归通过 |
| `yarn mock:contracts` | 244 operations；75 项 critical，0 failures |
| `yarn mock:overlays` | 11 overlays；0 failures |
| `yarn build:prod` | 生产构建通过 |
| `yarn e2e:demo-offline` | 1/1 核心流程通过；含登录、项目操作、版本、拓扑、仿真、网络隔离和 reset |
| `yarn e2e:demo-offline:page-state` | 8/8 页面状态通过 |

业务命令、退出码和耗时见 [business-validation.json](evidence/2026-10-13-business-lint-cleanup/business-validation.json)，日志位于 [证据目录](evidence/2026-10-13-business-lint-cleanup/)。

组件库位于 `/Users/hqz/Downloads/element-plus`，标准入口及 opt-in 计时入口已重新执行：

| 组件库命令 | 结果 |
| --- | --- |
| `pnpm lint` | 通过 |
| `pnpm typecheck` | 全部类型检查通过 |
| `pnpm ui-contracts:check` | 四阶段通过 |
| `pnpm test:run` | 主 Vitest 2475 项通过；Node 39/39；MCP 84/84；authority 21 阶段通过 |
| `pnpm build:theme`、`pnpm build` | 均通过 |
| 两个 opt-in composition timing 文件 | 单进程另跑 3/3 通过，各保留 20 个样本 |

默认主 Vitest 保留 1 个 opt-in 文件、2 个测试的 skip，对应计时检查已按正式环境另跑，不将 skip 冒充默认执行。authority 为 `local-working-source-validation`，工作区 dirty，不是 clean release 准入。

库首轮完整测试暴露 happy-dom MutationObserver listener 被 GC 回收的测试环境问题。仅修正 ThemeProvider Autocomplete 测试夹具，用可控 observer/RAF 验证真实组件和 hook、owner 隔离、coalescing、卸载取消及释放；没有放大 timeout、增加重试或修改生产布局。真实 GC 探针、首轮失败日志和最终完整通过日志均保留。库生产实现与安装依赖未因这个测试修正再打新包。

组件库退出码见 [library-validation-final.json](evidence/2026-10-13-business-lint-cleanup/library-validation-final.json)，完整组合测试见 [library-test-run-final.log](evidence/2026-10-13-business-lint-cleanup/library-test-run-final.log)。

### 浏览器与后台补充验证

| 场景 | 结果 |
| --- | --- |
| Drawer/Dialog 源码布局矩阵 | 156 场景通过，0 页面异常 |
| Drawer/Dialog 安装包布局矩阵 | 156 场景通过，0 页面异常 |
| divider 源码与安装包 | 各 26 场景通过 |
| 当前业务 Role Drawer / User Dialog | 两主题、桌面/移动端共 8 场景通过，0 页面异常、0 角色/用户写操作 |
| 后台 collection schema、分类 ASGI、response factory/exporter/分类服务回归 | 27/27 通过 |
| 后台改动文件 Ruff / format / conventions helper | 9 文件通过；无新增 guardrail 违规 |
| 后台 OpenAPI exporter `--check` | artifact 与当前源码一致 |

浏览器只用隔离 headless CLI 验证，临时夹具服务已关闭；80/8088 开发服务保留可用，最终 HTTP 200。当前业务验证会登录，不能将“0 角色/用户写操作”扩大描述为“0 数据库写入”。离线 E2E 的项目操作发生于 mock 内存状态。

布局执行记录见 [overlay-matrix-execution.json](evidence/2026-10-13-business-lint-cleanup/overlay-matrix-execution.json)，当前业务几何和截图见 [business-browser-final](evidence/2026-10-13-business-lint-cleanup/business-browser-final/)。分类 ASGI 回归验证真实路由、参数解析及序列化，认证/服务依赖有覆写，不代表完整数据库/权限端到端测试。此次后台检查限于相关契约和改动文件，没有运行后台全库 pytest/mypy。

## 现有检查提示的边界

业务 ESLint 警告已清零。mock 覆盖检查仍会提示非 Core overlay 缺口（65 条）及覆盖审计信号；生产构建保留 chunk size、Browserslist 等工具提示。它们不是本轮 1230 条 ESLint 警告，相关规则和判定没有关闭，正式入口均 exit 0，不将此结果描述为所有 API 已有完整离线覆盖。

旧 frontend-conventions 辅助 `validate.sh --changed` 把已删除 TSX 文件继续交给 ESLint，并对任务前已有的 simulation 颜色与 detail 日志报错；该辅助脚本没有计为通过，也没有修改规则绕过。起始快照对比确认本轮没有新增 console/hex，证据为 [辅助 policy 增量对照](evidence/2026-10-13-business-lint-cleanup/legacy-helper-policy-baseline-comparison.json)。标准源码 lint、类型和完整测试结果如上。

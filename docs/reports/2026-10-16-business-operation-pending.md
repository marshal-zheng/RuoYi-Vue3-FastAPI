# HTTP 第 2 轮：业务操作 pending 与全局防重退出

日期：2026-10-16。已实施并完成本轮验证，未提交 Git、未发布 npm。

## 结果与职责

全局一秒时间窗口及 `sessionObj` 指纹判断已从业务 HTTP 拦截器删除，生产代码和测试中的 `repeatSubmit` 声明全部移除。表单、按钮和领域操作按各自生命周期防重入，`@zxio/http` 本轮没有修改。

| 层 | 本轮责任 |
| --- | --- |
| `@zxio/http` | 保持独立请求、原生 signal、超时和通用错误处理；没有提交锁或业务操作登记 |
| ZXUI 弹框/抽屉 | 复用已有的同步提交保护，等待实际确认回调；不增加业务接口规则 |
| 业务入口 | 决定操作实例和并行边界，pending 覆盖校验、确认、写请求及必要的导航/完成处理 |
| 后端 | 保留原有权限、安全检查和幂等行为 |

主要收益是防重时间与真实任务一致：慢请求不会因超过一秒而失去保护，失败后不用等待固定冷却时间；另一操作实例可独立运行。代价是业务入口需要明确自身的任务归属，不能依靠 HTTP 层猜测用户意图。

业务侧新增 `src/utils/operation.ts`，仅使用 Vue 的 `ref/readonly`，提供 `pending/run`。进入时先登记当前任务，再同步发布 pending，防止同步 watcher 重入；`finally` 释放。同步异常、异步失败和取消都保留原值。相同操作实例的在途重入返回同一个完整操作 Promise，不再次执行校验、确认、写请求或成功副作用，也不把后来的参数排队。它不是 HTTP 结果缓存，未读取 URL、请求参数或时间，没有全局状态。

列表删除、批处理等以本页面的同一次交互为单位；不同页面实例和不同操作分别管理。状态开关额外按行管理，其他行可并行，避免一个页面级布尔值误拦另一个行操作。

选型前复核了仓库现有保护，以及 [VueUse useAsyncState](https://vueuse.org/core/useasyncstate/) 和 [TanStack Vue Query mutations](https://tanstack.com/query/latest/docs/framework/vue/guides/mutations)。前者提供异步状态，后者默认允许变更并行、同 scope 可排队；这些能力不直接等于本轮的交互防重入。当前不需要查询缓存或变更队列，因此复用已有 ZXUI 提交流程，未托管入口只补业务侧的小型生命周期连接，不新增依赖。

## 盘点与迁移

静态扫描覆盖 117 个非 GET API 方法、114 个 API 调用点和 58 个候选文件；再补查登录、内联鉴权、有副作用的 GET、上传 transport 和 12 处 `proxy.download`。每个候选的处置记录见 [写入口清单](evidence/2026-10-16-business-operation-pending/write-entry-inventory.json)，这是代码审计清单，不代表浏览器逐页验收。

- 为 56 处未由组件托管的 handler 管理独立操作生命周期，覆盖保存、删除、导入、授权、任务执行、缓存操作、登录退出等；3 处状态开关按行创建操作实例。
- 标准 `useFormDialog/useDialog/useDrawer` 的异步确认直接复用已有保护，没有机械重复包裹。
- 修复协议抽屉的异步断链：保存使用可等待的业务 `save` 回调，写入完成后才通知成功。Vue `emit` 不承担等待父级保存的职责。
- 头像上传等待裁剪回调和实际上传；回调验证表单转换为可等待任务；授权页返回提交 Promise，设备保存等待导航。
- 登录、注册的原有 loading 统一消费操作 pending，覆盖校验到导航完成；按钮点击、回车和程序调用进入同一个操作入口。
- 设备/协议批量导入保留已有同步 `importing` 检查及 `finally` 清理，上传队列继续允许不同文件并行。
- 有副作用的生成器 GET、登录解锁 GET 也补上生命周期；它们以前不受 HTTP 一秒拦截覆盖，属于盘点发现的既有缺口。
- 两份在用 Vue 3 Jinja 模板同步接入提交生命周期、等待写请求，并对提交数据取快照，防止 checkbox 编码修改表单值而破坏失败重试。未迁移非本业务使用的 Vue 2 模板。
- POST 导出和模板下载按读取语义保持独立；未将所有 POST 一概当作提交。未使用的上传/工具导出不铺新保护，未被调用的 `useTopology.js` 保持任务前原样。

仿真表单与领域命令没有展开迁移。移除 HTTP 猜测后发现的两处直接依赖得到有限修复：自动事件按 session/event ID 记录在途状态，不重复触发同一自动事件，不同行事件可并行；WebSocket 票据获取和 CONNECTING 阶段防重入，断开/切换会话使旧任务失效。手动 step、调速和手动事件指令保留明确调用语义，没有全局串行化。

## 验证与证据

| 验证 | 结果 |
| --- | --- |
| 新业务操作回归 | 7 项，覆盖同步 watcher 重入、同步获取、超过一秒的慢任务、错误/取消释放和独立实例 |
| 业务源码直连回归 | 23 文件、167 项通过，包括 API、utils、登录 store、生成器、仿真控制/事件/WS |
| 后端生成器既有契约测试 | 4 项通过 |
| 既有 ZXUI 提交生命周期回归 | 11 项通过；安装包实现也核对了校验前同步置位及完整 await |
| 两份后端 Jinja 模板 | 分别渲染并通过 Vue script/template 编译；运行探针验证重入、失败保留及 checkbox 立即重试 |
| 实际业务回调内存探针 | 5 项通过：两份生成模板、协议保存、头像上传、逐行状态开关 |
| 前端 lint / type-check | 通过 |
| 变更规范检查 | 前端通过；后端 guardrails 通过，Python 检查跳过，见下方边界 |
| 源码直连生产构建 | 通过，23.39 秒；仅现有 chunk 大小提示 |
| Git diff 检查 | 通过 |
| 独立只读审查 | 无剩余阻塞；发现的 ZIP await 和 WS 旧票据归属问题均已修复并复核 |

新回归先观察失败：旧 HTTP transform 仍记录时间指纹，自动事件和 WS 重入分别多发请求；会话切换及同步 pending watcher 重入回归也在修复前失败。新增一个 7 项业务操作测试文件，其他必要回归放在既有文件，没有为排查铺大量新测试。

真实验证通过实际业务模块、实际 `ConfigList` 操作 handler、Vue pending、Axios 1.20.0、JSDOM XMLHttpRequest 和本地真实 FastAPI 执行。源码直连与安装包模式各 **6 项通过**：

1. 真实登录与鉴权信息正常。
2. 真实删除响应被暂存超过 1.2 秒，触发三次只出现一次确认、一次后端删除和一次刷新。
3. 自建临时内置配置删除返回真实 409；修正其可删除状态后，同一操作在一秒内重试成功，失败后 pending 已释放。
4. 两个实际业务操作实例均在任一响应释放前派发；完成一个不会释放另一个的 pending。
5. 两次相同 PUT 均独立完成，HTTP 层没有隐式提交策略。
6. 相同 POST 先遇到真实唯一性 409，解除其临时记录冲突后可在一秒内用同一请求体重新创建成功，无 `repeatSubmit` 逃生开关。

两种模式都只使用带专用标记的本地临时配置。结束时仅清理本次记录，并通过真实列表查询确认遗留数为 0。正常登录会话和操作审计记录保留。结果见 [源码直连](evidence/2026-10-16-business-operation-pending/actual-source.json)、[安装包](evidence/2026-10-16-business-operation-pending/actual-installed.json)。

## 验证边界与范围控制

真实接口探针批准了测试中的确认动作，并记录刷新效果；转发网关只控制真实响应的释放时间，没有构造成功/失败响应。没有使用 computer use，没有浏览器点击或视觉验收。逐行状态、裁剪上传、协议回调和生成模板的控制边界使用内存探针，API/UI 依赖为受控替身，不能当作这些页面的真实接口验收。具体边界见 [生命周期证据](evidence/2026-10-16-business-operation-pending/lifecycle-seams.json)。

前端 `tests/generator-form-contract.test.ts` 验证的是前端表单生成器；后端两份 Jinja 的渲染、编译及运行另行验证，不混用证据。模板探针覆盖代表性的平面、树表及 checkbox 场景，没有穷举所有字段和子表组合。

后端规范脚本的 PATH 中未找到 Ruff，因此跳过 lint/format，Mypy 和脚本内 Pytest 也未运行；其成功结果仅证明 guardrails 通过。本轮后端只改两份 Jinja 模板，没有改 Python 运行代码。4 项既有生成器测试是另外执行的结果。

本轮保留了已有 API 反馈策略，某些页面原有 catch 会处理错误；通用操作 helper 自身不吞错、不改写错误。按钮 pending 仅防当前交互重入，不代替后端幂等或跨客户端一致性。

未改 `@zxio/http`、请求准备阶段错误管线、retry/logger、查询缓存、数据库结构或后端幂等机制。两边既有未提交工作均保留，业务 package.json/yarn.lock 与本轮前一致。

本轮启动的后端及其子进程已停止，其他已有服务未停止。命令和统计见 [checks.json](evidence/2026-10-16-business-operation-pending/checks.json)。

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN:
- docs/plans/2026-10-16-business-operation-pending.md
EVIDENCE:
- READ: AGENTS.md, existing HTTP report, real API/caller sources, ZXUI confirmation lifecycle, active generator templates.
- SEARCH: Mutation callers, method helpers, pending/loading, repeatSubmit/sessionObj, side-effect GET, upload and export paths.
- COMMAND: Inventory and plan structure checks passed before continuing execution.
PLAN_CHANGES:
- Added narrow automatic-event and WebSocket ticket lifecycle dependencies found during the audit; preserved broader simulation scope.
WORK_ITEM_SYNC_SUGGESTION:
- none
NEXT_ACTION: completed current-session execution and independent review; no further approval required for this round.
BLOCK_REASON: none
UNBLOCK_ACTION: none

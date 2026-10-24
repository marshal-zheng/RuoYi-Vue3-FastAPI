# HTTP 日志与通知异常隔离

本轮已完成。通用旁路隔离在 ZXUI；业务负责反馈展示、重新登录提示和下载失败提示的生命周期。没有调整重试、参数、鉴权策略或下载协议，没有新增依赖，没有提交或发布 npm。

## 根因与责任边界

ZXUI 原来直接执行 logger 与 notifier：开始日志抛错可阻止发送；成功日志／通知抛错会把成功请求变成失败；错误通知抛错会覆盖原错误，并可能阻止 `onAuthError`。`createNotifier` 只保护订阅器的同步异常，未保护 override、message/modal 以及异步拒绝。转换上下文和 `setNotifier` 也会暴露未保护的对象。

业务的成功提示、错误提示位于响应／错误转换钩子内。提示格式器、Provider 或字段错误展示适配器异常可能打断钩子。重新登录提示拒绝后，原来的“提示已显示”标记不会释放；下载反馈派生的 Promise 也可能产生未处理拒绝。

处理顺序保持为请求准备 → Axios → 响应转换／插件 → 成功判定与解包；异常仍进入既有错误管线。旁路保护没有包住转换、成功判定或鉴权逻辑。

| 职责 | 本轮处理 |
| --- | --- |
| ZXUI 日志、通知、订阅器 | 单独保护每个回调；同步执行、保留接收者；隔离同步异常和返回 Promise 的拒绝，不等待旁路完成 |
| ZXUI 上下文／动态通知器 | 构造和 `setNotifier` 均建立保护；插件通过 context 使用日志与通知时也受保护 |
| EnhancedLogger | 自定义输出和默认序列化都位于保护内；独立使用同样适用 |
| 业务反馈 | 在 presenter 所属边界保护格式化、字段错误展示及 Provider Promise；不吞掉整个 HTTP transform |
| 重新登录提示 | 展示失败释放标记；先清状态再关闭句柄；过期句柄的异步关闭拒绝也被承接 |
| 下载失败提示 | 保护反馈观察者派生链，下载本身继续抛原错误，保留已有取消与 loading 行为 |
| 响应与鉴权语义 | `afterResponse`、`successResolver`、Token 准备、`onAuthError` 异常仍使请求失败；`onError` 抛错仍终止管线 |

采用内部小型执行边界，没有引入观察者框架、配置组合或业务策略进入 HTTP 包。定向核对了 [OpenTelemetry 官方安全执行实现](https://github.com/open-telemetry/opentelemetry-js/blob/main/experimental/packages/opentelemetry-instrumentation/src/utils.ts)，借鉴其按调用职责局部保护的思路；此处另承接返回的异步工作。业务反馈保留自己的轻量展示边界，避免依赖 HTTP 内部辅助函数。

异步回调须返回 Promise，不能先用 `void` 脱离返回链。已同步更新业务 notifier、HTTP 文档和示例。旁路异常不会再通过同一个日志／通知通道二次上报，以免递归失败。

## 验证

| 验证 | 结果 |
| --- | --- |
| ZXUI HTTP 测试 | 8 文件、102 项通过，包含 9 项本轮针对性回归 |
| 业务 HTTP／反馈／下载／operation 测试 | 5 文件、53 项通过 |
| ZXUI HTTP 构建、受影响文件 lint、测试类型检查 | 通过 |
| 业务 `yarn lint:check`、`yarn type-check`、受影响文件 lint／格式 | 通过 |
| 生产构建：源码直连／安装包 | 分别通过，25.30 秒／24.35 秒；只有既有 chunk 大小提示 |
| 独立复核 | 发现并修复过期提示异步 close 遗漏，未遗留阻塞问题 |
| 仓库约定脚本 | 仍失败于既有 `VersionList.vue` console 使用；整文件 SHA256 与本轮开始相同 |

必要回归均有故障证据。特别是异步 close 使用普通函数返回拒绝 Promise：移除 `await` 时测试明确因未处理拒绝退出 1，恢复后通过。最初用 spy 返回拒绝 Promise 的测试会被 tinyspy 的 settled-results 观察掩盖，已改正，没有把该无鉴别力结果作为证据。

测试结果及命令见 [验证记录](evidence/2026-10-16-http-observer-isolation/verification.json)、[库测试](evidence/2026-10-16-http-observer-isolation/library-final-tests.log)、[业务测试](evidence/2026-10-16-http-observer-isolation/business-final-tests.log)、[异步关闭修复前](evidence/2026-10-16-http-observer-isolation/stale-close-red-verified.log)和[修复后](evidence/2026-10-16-http-observer-isolation/stale-close-green.log)。

## 真实业务闭环

源码与安装包两种模式各 **10 项检查通过**。使用真实本地 FastAPI、MySQL、Axios 1.20.0 XMLHttpRequest、生产 ConfigDlg 的 onConfirm、useFormDialog/useDialog、业务 HTTP、feedback presenter 和 channel。仅在 UI 反馈适配器与 logger 上注入异常，未替换业务响应。没有使用 computer use，没有进行浏览器点击或原生表单视觉验证。

- 真实登录：开始日志抛错、成功通知失败，仍获得会话并读回 admin 信息。
- 真实参数弹窗：提示同步抛错、异步拒绝、永不完成时，均写入成功、可回读、产生 confirm 事件且 pending 释放。
- 真实 409 冲突：保留 Axios cause、原始响应、请求 config 与 Problem Details；通知失败不覆盖错误，修改键名后同一弹窗重试成功。
- 真实 422：字段错误展示抛错，仍得到原始校验错误。
- 真实修改：成功文案格式器失败不影响保存；另以真实读取响应验证转换及成功判定异常仍失败。
- 真实 401：失败通知不阻止鉴权回调；鉴权回调抛错按身份原样保留。业务提示同步失败、异步失败及过期句柄异步关闭失败后，均可继续提示，有效会话恢复后仍可读取。
- 真实 Excel 导出及 404 下载失败：成功文件可解析，失败不保存文件，原错误透传，loading 释放，即便错误提示抛错也无未处理拒绝。
- 真实 XHR 取消：保留取消原因，通知静默，operation pending 释放。
- 清理与未处理拒绝检查：每次探针创建的 4 条参数记录均删除，原有 7 条记录明细完全一致；全部旁路异步拒绝均已承接。

详见[源码模式](evidence/2026-10-16-http-observer-isolation/actual-source.json)、[安装包模式](evidence/2026-10-16-http-observer-isolation/actual-installed.json)和[Excel 检查](evidence/2026-10-16-http-observer-isolation/workbooks.json)。仅停止本轮启动的后端 PID 55063，未修改 Docker MySQL 或 Redis 的运行状态。

联调另发现范围外问题：后端分页 COUNT 缓存可能在写入／删除后保留旧总数；本次删除后 items 已恢复 7 条，total 一度为 11。直接查询 MySQL 确认总记录数 7、探针记录 0。没有把此差异误判成 HTTP 解包问题，也没有混入缓存修复。

## 本地交付与工作区保护

业务引用本地 `vendor/zxio-http-1.0.0-observers.20261016.tgz`，锁文件已更新；Axios 保持 1.20.0。构建目录、归档与安装目录的 53 个文件一致，manifest 按 JSON 语义比对。开发仍通过既有 `VITE_ZXUI_LOCAL=true` 和 `VITE_ZXIO_REPO_ROOT` 直连源码。未发布 npm。

公开文档及 notifier 示例已同步，在隔离目录运行组件类型、示例和 llms 生成器，仅回写 4 段 HTTP 文档全文；HTTP 类型和示例索引无需变更，非 HTTP 聚合条目保持不变。

见[归档一致性](evidence/2026-10-16-http-observer-isolation/package-integrity.json)、[生成记录](evidence/2026-10-16-http-observer-isolation/metadata.json)和[工作区保护](evidence/2026-10-16-http-observer-isolation/baseline-preservation.json)。本轮之外既有修改未变。

## 计划检查点（实施前）

STATUS: PLAN_DRAFTED

FILES_WRITTEN:
- docs/plans/2026-10-16-http-observer-isolation.md

EVIDENCE:
- READ: Both AGENTS.md files; HTTP client/notifier/logger; business transforms, feedback channels/presenter and tests.
- SEARCH: Logger/notifier call sites, context/setNotifier exposure, presenter callers and download feedback observer.
- COMMAND: Plan structure checks passed; targeted red regressions reproduced the failures.

PLAN_CHANGES:
- Isolate observers at their owner and preserve semantic hooks; include the existing download feedback observer.

WORK_ITEM_SYNC_SUGGESTION:
- none

NEXT_ACTION: current-session execution (completed with evidence above)

BLOCK_REASON: none

UNBLOCK_ACTION: none

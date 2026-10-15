# HTTP 下载边界修复与真实业务验证

日期：2026-10-15。本轮只处理下载错误解码、取消反馈、错误透传与 loading 生命周期，保留前几轮 HTTP 修复。

## 责任与修复

| 责任方 | 原问题 | 本轮结果与收益 |
| --- | --- | --- |
| ZXUI `packages/http` | Blob、ArrayBuffer 失败体仍是二进制，消费者拿不到服务端错误详情 | 新增公共异步 `resolveHttpError`，默认错误处理直接使用；其他业务也能复用，无需各写一套解码 |
| 业务 HTTP 适配 | 自定义错误 hook 读取原始 response.data，忽略解码结果 | 调用库 resolver 后从 error.data 补充 Problem Details，保留文本、message、msg 错误详情及原错误上下文 |
| 业务通用下载入口 | 取消当失败提示、catch 吞掉拒绝、全屏 loading 实例在并发请求之间覆盖 | 取消静默、返回原任务保留拒绝、失败仅提示一次；引用计数使最后一个下载结束时才关闭共享遮罩 |
| 业务文件保存入口 | 成功状态下返回的 Problem 错误可能被保存成文件 | 检查非 2xx 与无附件标记的 JSON Problem；有效 JSON 附件仍正常保存，服务端文件名与文件字节保留 |
| 业务页面调用点 | 设备导出的 finally 产生无人处理的派生拒绝；工程导出提示取消失败 | 设备成功/失败均释放 exporting；工程导出在事件边界捕获错误并跳过取消提示 |

### 库的二进制错误契约

`createHttpError` 保持同步兼容。`resolveHttpError` 在它创建或保留的 HttpError 上补充解码结果，不替换原 `cause`、`response`、`config`、`raw` 或 `response.data`。业务字段放在 `data`；原始传输证据继续可查。

- 支持 Blob、ArrayBuffer 和 ArrayBuffer view，view 只读取自身的 offset/length。
- 解码上限为 1 MiB，读取前检查；超限、空内容、读取失败和格式损坏均退回原错误。
- 优先解析 JSON；明确为 `text/plain` 的失败体可保留文本详情，其他非 JSON 内容不冒充结构化错误。
- 取消错误直接返回，不读取二进制体。库不增加保存文件、业务码判断或 UI 提示职责。
- 默认错误处理自动使用；自定义 onError hook 需显式 await resolver，README 已给出说明。

通用下载返回原任务，同时挂接独立的失败反馈观察者。调用方 await 仍收到原始错误；原有不等待的事件调用也有拒绝处理器。请求失败、错误体判定失败、取消及保存入口抛错都会经过 finally；取消不保存文件、不弹失败消息。

文件 helper 不把所有 JSON 文件当成失败：显式 attachment/文件名保留附件语义；无附件标记的 `application/problem+json` 或符合业务 Problem 契约且 status >= 400 的 JSON 才判作错误。非 2xx 始终拒绝，包括被自定义 validateStatus 放行的响应。

## 真实业务验证

使用真实业务 HTTP、通用 download、版本导出 API 与文件 helper，连接本机 FastAPI :8088；Axios 为 1.20.0，传输为 JSDOM XMLHttpRequest。只替换界面反馈、loading 和 file-saver 的入口，没有使用 computer use，也没有做浏览器点击与系统保存对话框验收。

源码直连与本地安装包在独立进程各通过 9 项：

| 检查 | 结果 |
| --- | --- |
| 真实登录 | admin 登录、用户信息查询及退出正常 |
| Word 经通用 download 导出 | 5336 字节与传输内容一致，使用服务端中文文件名，loading 关闭一次 |
| 真实版本 Word、ZIP、XML API | 分别为 5336、165、603 字节，保存入口收到原文件内容 |
| 用户导出非法分页，HTTP 422 Blob | 解码 Problem，保留原 Blob、cause/config/requestId；拒绝、一次反馈、关闭 loading |
| 版本 XML 非法参数，HTTP 422 ArrayBuffer | 解码 Problem，保留原 ArrayBuffer 与错误上下文 |
| 两个实际 Word 导出并发 | 共用一个遮罩；第一个完成不关闭，最后一个完成才关闭 |
| 实际导出进行中取消 | XHR.abort 一次，AbortError/ERR_CANCELED 和取消原因保留；无反馈、无保存、loading 收尾 |
| 实际导出后保存入口抛错 | 同一个保存错误继续拒绝，一次反馈，loading 收尾 |
| 原有不等待 download 的调用 | 422 失败无 unhandledRejection，一次反馈，loading 收尾 |

并发与取消使用临时本地网关延迟真实后端导出字节，没有伪造导出数据。当前版本没有协议记录，165 字节 ZIP 为服务端返回的说明附件；本轮验证文件传输边界，没有据此宣称工作簿业务内容验收通过。只执行登录、查询、导出、退出，没有新增或修改业务记录。

结构化证据：[源码模式](evidence/2026-10-15-http-download-boundary/source-actual.json)、[安装包模式](evidence/2026-10-15-http-download-boundary/installed-actual.json)。不保存 token、请求头和完整错误对象。

## 单独发现的后端导出阻塞

合法 `POST /system/user/export`（`page=1&pageSize=10`）未通过真实导出验收：请求超时后，后端工作进程持续占用约一个 CPU 核心。

重启后使用独立 Node fetch 绕过 Axios、ZXUI 和业务前端，仍在 5001 ms 超时，工作进程 CPU 为 99.1%。这说明该阻塞可在后端链路独立复现，不能归因于本轮下载客户端。证据见 [独立复现](evidence/2026-10-15-http-download-boundary/backend-independent.json)。

排查线索是 token-source guard/idempotency 中间件的请求体 replay receive 与 StreamingResponse 断连监听的交互：读完后持续返回空 http.request，可能形成忙循环。这是尚待进一步定位的推断，本轮没有修改后端，也没有将用户 Excel 导出标记为通过。验证转用可正常完成的版本 Word/ZIP/XML 导出，避免扩大当前修复范围。

## 回归与质量检查

- ZXUI 在既有 client 测试增加二进制回归，先复现解码失败；同时覆盖取消、超限、读取失败、损坏内容、纯文本和 view offset。HTTP 套件：8 个文件、75 项通过。
- 业务在既有 HTTP/download 测试补充错误内容和文件契约；新增一个下载生命周期测试文件，4 项覆盖取消、原错、并发及保存失败。源码与安装包模式分别为 18 个文件、85 项通过。
- 复查发现 message/msg 详情覆盖及非 2xx 状态边界，分别先观察失败后修复；最后的只读复查无剩余可执行问题。
- ZXUI 修改源文件/测试 ESLint、Prettier、测试文件 strict TypeScript 和 `pnpm -C packages/http build` 通过，包构建包含源码类型检查。
- 业务 `yarn type-check`、`yarn lint:check` 及 `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed` 通过。新测试移除不必要的 Axios 运行时导入后，4 项再次通过。
- 显式 `VITE_ZXUI_LOCAL=false` 与 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` 的生产构建均通过，使用独立临时输出目录。
- 两仓库 `git diff --check` 通过。

业务回归使用 `yarn vitest run src/api src/utils src/store/modules/user.login.test.ts`；源码测试使用相同 Vitest 配置加精确 `@zxio/http` 源码别名。实际探针分别运行 source/installed，证据区分两种模式。

## 本地交付与范围

业务已安装 `vendor/zxio-http-1.0.0-download-boundary.20261015.tgz`，依赖和 yarn.lock 同步更新。SHA-256：`dca07c3edf70076452b5a028a9cbb2b7369aea332979f6be912d71887e2ab641`。安装后的 client/errors 构建文件及公开声明与 ZXUI 当前 dist 一致，发布 manifest 不含工作区 source 条件；Axios 保持 1.20.0。

未发布 npm、未提交 Git。重试、防重复提交、query/body 语义、日志、后端中间件与其他 HTTP 优化未混入。已停止本轮启动的验证后端，原有 MySQL/Redis 保持。

## Plan-stage Checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-15-http-download-boundary.md
EVIDENCE:
- READ: ZXUI errors/client and business HTTP/download/export consumers.
- SEARCH: binary response handling, failure feedback, cancellation and fullscreen loading ownership.
- COMMAND: plan structure checks, failing/passing regressions, type/lint/builds and actual backend probes.
PLAN_CHANGES: Three dependent tasks covering the library contract, business lifecycle and local verification.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: Review the local changes and evidence; backend Excel streaming remains a separate issue.
BLOCK_REASON: none
UNBLOCK_ACTION: none

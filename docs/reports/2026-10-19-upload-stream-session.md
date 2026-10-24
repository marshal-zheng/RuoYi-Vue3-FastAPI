# RuoYi 上传、导入与实时连接会话验收

状态：本轮实现、定向回归、真实浏览器/API 验收、数据清理完成；保留既有改动，未提交或推送。

前置结论见 [会话续期根因报告](2026-10-18-session-renewal.md)。原来的十分钟失效属于续期缺陷，访问令牌本身的 600 秒期限符合配置。本轮继续补齐绕过普通 HTTP 的上传与实时连接入口，没有延长访问期限或改变单点登录策略。

## 已查明并修复

| 问题 | 根因及处理 |
| --- | --- |
| FileUpload、ImageUpload、Editor 未共用续期 | 三个封装使用 Element Plus 内置 XHR，并在初始化时保存 token header。改为通过 `http-request` 调用现有业务 request，复用 Axios 会话续期、CSRF、FormData、反馈和取消。 |
| 上传列表在成功、移除或并行上传时不同步 | 原有批次计数与文件列表存在多个所有者。统一使用原生文件列表，父级只接收成功路径；移除回调必须采用回调传入的最新列表，不能等待被动 v-model 同步。真实页面夹具发现移除后值未清空，修复后补了回归。 |
| SSE 重连不会先更新认证 Cookie | 原生 EventSource 不经过业务 adapter。建立或重建连接前先调用已有的认证签名接口，续期完成后再开 SSE；用连接代次与来源身份忽略旧回调，本地认证范围结束时关闭连接。 |
| 退出后未使用的 WebSocket 票据仍可连接 | 修复前真实握手可以成功。票据原来只绑定用户、Origin 和仿真路径，没有绑定可撤销的登录会话。现在签发和消费都检查登录会话元数据及单点登录指针；退出、替换登录或元数据过期后不能建立新连接。 |
| 主动断开 WebSocket 后再次连接 | 原来的 onclose 无法区别主动断开、卸载和意外掉线。添加连接代次、查询范围归属与 socket 身份检查，主动断开取消定时器，意外关闭才重新申请新票据。 |
| 本地 WebSocket 票据请求 422 | Vite 5.3.2 的本地代理在 `changeOrigin: true` 时改写普通 HTTP 请求的 Origin。后端直连接受浏览器 Origin，代理后失败。局部改为 `changeOrigin: false`，保留浏览器 Origin/Host，真实票据签发与握手通过。 |

选型复用现有 Element Plus 上传扩展点、Axios request、查询范围和 Redis 会话，不增加上传框架或另一套认证基础设施。认证、Cookie 和票据撤销属于 RuoYi，本轮修复在业务仓库；ZXUI 原有 26 个修复文件 SHA256 均未变化。代价是两个小型业务 composable，以及重连前的一次认证探测。

依据：[Element Plus Upload 官方 API](https://element-plus.org/en-US/component/upload.html#api)、[Vite 5 代理配置](https://v5.vite.dev/config/server-options#server-proxy)、[Vite 官方仓库 Origin 改写问题](https://github.com/vitejs/vite/issues/17562)。同时检查了本机安装版本的上传 Promise 回调、文件移除和代理实现。Element Plus 负责成功/失败回调，业务 transport 不手动重复触发。

## 真实运行结果

运行现有 Colima MySQL/Redis、8088 后端和 80 前端，前端启用 `VITE_ZXUI_LOCAL=true` 与本地 ZXUI 源码路径。共享管理员被其他登录替换时，未将预期单点撤销误判成续期失败；最终计时使用本轮独占账号。

**公告编辑器自然过期验收：** 独占用户在 Europe/London 02:46:49 登录，原访问令牌 02:56:49 到期。02:57:22 通过真实图片工具栏和文件选择器上传时，已过去 **633.54 秒**，Redis access TTL=-2，刷新会话 TTL=604167。此前没有刷新请求。实际顺序仅一次 refresh 200、一次 upload 200、图片 GET 200，64×64 图片解码成功；点击真实确定按钮保存公告得到 201，服务器读回的 HTML 含该图片地址。证据：[时间序列](evidence/2026-10-19-upload-stream-session/natural-upload.json)、[公告截图](evidence/2026-10-19-upload-stream-session/05-notice-image-after-natural-expiry.png)。

**真实用户导入：** 从页面下载模板，使用模板要求的中文枚举“男/正常”，两次各创建一个独占用户并核对返回结果；第二次在原始访问期限之后、公告已成功续期的会话中完成。损坏工作簿返回现有 500 后，导入窗口保留可操作状态；通过移除控件换成有效工作簿重试，200、成功 1 条、落库账号一致。没有开启“更新已经存在的用户”。没有把该导入写成“独立自然到期触发续期”的证据。证据：[首次导入](evidence/2026-10-19-upload-stream-session/import-first.json)、[失败后重试与回读](evidence/2026-10-19-upload-stream-session/import-second.json)。

**FileUpload/ImageUpload：** 目前只有全局注册和生成模板消费者，没有现成手写业务页面。因此使用明确标注“非现有业务页面”的临时夹具，挂载实际组件并访问真实后端。验证文件/图片上传、无效类型与大小阻止请求、503 故障注入后重试、成功路径回传、文件/图片删除和预览。1440×1000 与 1100×800 视口检查通过，预览图片加载且对话框完整可见。上传中现有全屏 loading 会阻止普通关闭按钮，所以卸载取消采用诊断卸载探针，观测到 `net::ERR_ABORTED`，没有将其描述成页面按钮验收。证据：[检查记录](evidence/2026-10-19-upload-stream-session/fixture-final.json)、[小视口预览](evidence/2026-10-19-upload-stream-session/08-image-preview-small.png)。

**SSE：** 用现有诊断 API 停止连接，仅驱逐独占账号 access 缓存，再启用实际插件；原生浏览器链路为 signature 401 → refresh 200 → signature 200 → EventSource 200。本地退出时该 SSE 请求取消，随后观察 44.576 秒没有重连。此处是受控缓存驱逐及诊断重连，区别于公告的自然实等。证据：[SSE 记录](evidence/2026-10-19-upload-stream-session/sse-reconnect.json)。

**WebSocket：** 浏览器原生 WebSocket 验证新票据握手与 ping/pong、新票据重连成功；复用、路径不匹配、实等 35.764 秒的过期票据，以及退出后尚未使用的票据，均无法连接。修复前后的退出票据对照分别见 [修复前](evidence/2026-10-19-upload-stream-session/ws-before-fix.json)、[修复后](evidence/2026-10-19-upload-stream-session/ws-after-fix.json)。没有创建实际仿真工程，也没有声称完成仿真页面流程验收；主动断开和迟到回调由实际 composable 的单元回归覆盖。

**终态撤销：** 明确核对并撤销本轮专用会话后，再通过真实上传选择器提交。仅 upload 401、refresh 401，没有成功重放或模型路径更新。页面仅一个“登录状态已失效/重新登录”入口；点击后 logout 204 并到达登录页。证据：[记录](evidence/2026-10-19-upload-stream-session/revoked-upload.json)、[截图](evidence/2026-10-19-upload-stream-session/09-revoked-session-upload.png)。

## 回归与基线

- 前端聚焦 37 项、5 文件通过；含真实 ZXUI 源码直连的整组 81 项、8 文件通过，两组存在重叠，不相加。
- 后端票据与登录相关 27 项通过。前一轮真实 Redis 轮换、重放和并发验证仍保留在前置报告，本轮没有把旧结果算作新运行。
- 受影响前端源码与测试 ESLint 无诊断。默认忽略的 Vite 配置另行强制检查：修复前后均 49 项原有诊断，新增 0。
- 源码直连 vue-tsc 与只读基线均为 34 项原有诊断，新增/移除 0；后端相关 Ruff 原有 17 项，新增 0。没有清理无关类型或格式问题。
- 测试日志保留 Element Plus 旧 underline API 提示、单测未注册全局预览组件/图标的 Vue 提示及现有后端 regex 弃用提示。真实浏览器预览通过；浏览器 pageerror 记录为空。临时夹具配置过程中遇到过 provider 和 Vite 依赖缓存问题，修正夹具上下文并刷新后才采集最终证据。

可复跑命令（在对应前/后端目录）：

```bash
./node_modules/.bin/vitest run tests/unit/components/AuthenticatedUpload.test.ts tests/unit/components/WebSocketSession.test.ts src/plugins/dev-menu-hot-sync.test.ts src/utils/session.test.ts src/utils/io-toolkit/upload.contract.test.ts --reporter=dot
./node_modules/.bin/vitest run --config ../docs/reports/evidence/2026-10-19-upload-stream-session/source.vitest.config.mts
./venv/bin/python -m pytest -o addopts='' tests/unit/services/test_security_token_service.py tests/unit/controllers/test_login_controller_refresh.py tests/unit/services/test_login_service_core.py -q
```

[证据汇总](evidence/2026-10-19-upload-stream-session/verification-summary.json)包含 47 项核对，明确区分浏览器/API、故障注入、诊断探针、测试和静态基线。15 个实现/测试文件保存了独立基线、SHA256 和本轮增量补丁，覆盖原有未提交内容而不重置它们。

## 清理与边界

身份核对后清理用户 125/126/127、公告 11、精确记录的 5 个上传文件和自身 CSRF；API 中剩余本轮用户/公告为 0，已知会话键剩余 0。临时夹具源文件与自建浏览器/API contexts 已移除/关闭。保留数据库本身、业务服务和其他容器；结束时 MySQL/Redis 运行，前端和后端 /docs 均 200。见 [清理](evidence/2026-10-19-upload-stream-session/cleanup.json)、[服务状态](evidence/2026-10-19-upload-stream-session/services-final.json)。票据 URL 日志已脱敏，证据不保存原始 token、Cookie 或 Authorization header。

后端当前不主动踢断其他地方已经建立的长连接。本轮覆盖的是新握手、重连和本地退出的连接清理，不把它扩大成远端已连接会话的即时撤销保证。本地未配置持久签名密钥，后端重启导致现有 JWT 失效的开发环境行为仍在。损坏 Excel 返回 500 的问题已在用户后续授权下修复并完成真实页面验收，见 [损坏 Excel 导入修复报告](2026-10-19-corrupt-excel-import.md)。文件/图片封装保留原有全屏上传 loading；成功文件现在逐个发布已提交路径，不再等待整批成功，调用扫描未发现依赖旧批次时机的手写消费者。

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-19-upload-stream-session.md
EVIDENCE: READ actual upload/HTTP/session/stream consumers and installed library implementations; SEARCH callers and mature extension points; COMMAND focused tests, lint and baseline checks; BROWSER real notice/import controls plus labelled fixture and stream probes.
PLAN_CHANGES: Added shared upload model ownership, Vite Origin preservation, login-session-bound tickets and WebSocket generation guards only after concrete failures were observed.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: Current-session execution, review, acceptance, cleanup and reconciliation completed.
BLOCK_REASON: none
UNBLOCK_ACTION: none

# RuoYi 会话续期根因与验证

状态：修复、定向回归、真实 API、跨 600 秒的页面续期及清理全部完成。

## 根因结论

原验收中的会话失效属于续期缺陷。600 秒的访问令牌到期本身符合配置，但系统已有 604800 秒的刷新令牌，用户不应在持续使用页面时被要求重新登录。

原始后端日志（Europe/London，UTC+01:00）：

| 事件 | 时间 | 进程 |
| --- | --- | --- |
| 登录成功 | 2026-10-18 15:42:51.266 | 98991 |
| 最后一次详情读取成功 | 2026-10-18 15:52:15.469 | 98991 |
| 首次会话拒绝 | 2026-10-18 15:52:53.749 | 98991 |
| 后续拒绝 | 15:52:59.774 / 15:53:05.812 | 98991 |
| 后端因其他文件变更而重载 | 2026-10-18 16:16:12 | 12788 |

首次拒绝发生在登录约 602 秒后；日志为 `Session not active or token mismatch`。该记录不能区分缓存缺失与 token 不同，但当时没有其他登录、注销或重启，且恰好跨过访问期限，结合实现可确定是访问会话缓存到期。JWT 配置还有 60 秒时钟容差，因此此时先通过签名/时间校验，再在 Redis 会话校验中拒绝。那次运行期间没有 `/auth/refresh` 请求。

直接责任：前端只在启动/恢复页面时调用 refresh，运行中的 HTTP 401 直接提示重新登录。后端原本把 access token、刷新会话元数据、单点登录指针全部设为访问令牌的 600 秒 TTL；refresh 又没有验证可撤销会话，直接重新登记。因此不能简单加一个无限刷新重试。

## 修复

- 业务 HTTP 的 Axios adapter 在访问 token 距离到期不足 30 秒时，先刷新再发送请求；并发请求共用一次刷新。明确收到 401 后最多重放一次，复用已经序列化的正文，不重复执行业务 transform 或成功反馈。403、网络错误、服务端错误不触发重放。
- 刷新使用独立 Axios client，避免递归。Web Locks 对同源标签页的刷新轮换排序；CSRF header 优先取当前 Cookie。请求取消、查询范围结束、注销或替换登录后，不再派发旧请求或恢复旧凭证。
- `restoreSession` 共用同一个刷新入口；旧恢复失败不能清空随后成功登录的新凭证。注销入口明确不续期，并提前使本地凭证版本失效。
- Redis 中 access token 仍按 600 秒到期，刷新会话及当前会话指针按 7 天到期。会话保存刷新 token 的 SHA256 摘要，使用现有 redis-py WATCH/MULTI/EXEC 原子验证和轮换；已注销、被替换、元数据过期或已轮换的 token 不能重建会话。
- 撤销和轮换采用相同受监视键，撤销旧会话不会删除别的当前会话指针。移除鉴权读取中不必要的 GET 后 SET，避免与撤销竞态重新写回 access token。
- 注销时访问令牌已过期，仍可用刷新令牌识别并撤销会话。

选型：保留既有 Axios、ZXUI HTTP 和 redis-py。会话 Cookie、CSRF、单点登录、业务状态属于 RuoYi，修复放在业务侧。通用 HTTP 包无需新增认证策略。Axios adapter 的复用边界参见 [官方请求配置](https://axios-http.com/docs/req_config)；Redis 事务依据 [官方异步 WATCH/MULTI 文档](https://redis.io/docs/latest/develop/clients/redis-py/async/)。代价是少量业务会话传输代码，以及刷新元数据保留时间从十分钟恢复为既定的七天。

## 验证

- 后端定向 15 项通过，其中 8 项在真实本地 Redis 上以随机 UUID 前缀隔离，覆盖访问缓存消失、刷新轮换、重放、注销/替换/过期、8 路并发只成功一次、刷新与撤销竞态、旧会话撤销保留新指针。测试结束仅删除自身前缀。
- 前端认证定向 50 项通过；包含原页面的源码直连回归共 171 项、8 文件通过。
- 前端定向 ESLint 通过；后端相关文件 lint 诊断与修复前相同，原有 5 项，新增 0。
- 全量源码直连 vue-tsc 与只读虚拟基线均为 34 项原有诊断；新增/移除均 0。没有为了通过类型检查改动无关代码。
- 真实 API：访问缓存主动移除后 401 → refresh 200 → getInfo 200；旧 refresh 重放 401；logout 204 后旧 refresh 401 / access 401；另一处新登录后旧 refresh 401 / access 401，新 access 200。
- 首次共享管理员计时被其他登录替换；没有把这次预期撤销当作续期失败。改用本轮独占用户进行最终 600 秒实等。开发热更新曾产生 Layout 初始化错误，冷启动独占用户后没有该异常。

运行命令：

```bash
# ruoyi-fastapi-backend
RUOYI_SESSION_REDIS_TEST_URL=redis://127.0.0.1:6379/2 ./venv/bin/python -m pytest -o addopts='' tests/integration/security/test_user_session_renewal.py tests/unit/controllers/test_login_controller_refresh.py tests/unit/services/test_security_token_service.py -q
# ruoyi-fastapi-frontend
./node_modules/.bin/vitest run src/utils/session.test.ts src/utils/http.test.ts src/store/modules/user.login.test.ts --reporter=dot
```

源码直连命令及日志、只读基线、API 时间序列、截图、清理与文件 SHA256 证据位于 ZXUI 工作区 `docs/reports/evidence/2026-10-18-form-contract-session-repair/session-renewal/`。

## 边界

本轮验证普通业务 HTTP 会话续期，不将长期 SSE/WebSocket 已建立连接或直接使用 Element Plus 内置 XHR 的旧上传封装描述为已验收。后续上传、导入、SSE 重连和 WebSocket 票据撤销已单独闭环，见 [2026-10-19 后续报告](2026-10-19-upload-stream-session.md)，其中明确区分真实业务页面、组件夹具和诊断探针。访问期限、刷新期限、单点登录策略没有改变。本地未配置持久签名密钥，进程重启后现有 JWT 失效仍是当前开发环境行为；原始事故发生时没有重启。

原有工作区改动保留，未提交或推送。先前 26 个 ZXUI 修复文件与上一阶段 SHA256 完全相同。本轮 11 个实现/测试文件的独立基线、最终摘要与增量补丁均已保存；包括 login controller 中用户原有的登录状态改动，没有覆盖。

## 最终真实页面结果

独占临时用户登录于 2026-10-18 16:34:08（Europe/London），原访问令牌到期于 16:44:08。16:44:25 点击真实“保存”按钮时，已过去 **617 秒**，Redis access TTL 为 -2，刷新会话 TTL 仍为 604183 秒。此前没有 refresh 请求。请求顺序为一次 refresh 200、一次资料 PUT 422；422 是测试邮箱 `.invalid` 域名被后端拒绝，与认证无关。16:44:57 将邮箱改为 `example.com` 后，只发一次 PUT 200，没有第二次续期，服务器读回昵称、手机号、邮箱均一致。页面没有重新登录提示。

第二个同源标签页恢复后，原页保存按 401 → refresh 200 → PUT 200 完成；两个真实标签页并发恢复共 5 轮、10 个业务请求全部成功。明确撤销本轮用户的会话记录后，原页只发一次 PUT 401 和一次 refresh 401，没有成功重放，页面保留草稿并仅显示一个“重新登录”入口。点击后到达登录页，sessionStorage 凭证和认证 Cookie 均清空。

资料页冷启动没有页面异常，1440×1000 视口内保存按钮完整可见。验证中两次预期业务拒绝（422 校验和撤销后的 401）被页面错误事件记录为“请检查输入字段”和“用户token已失效，请重新登录”；没有把它们写成零错误结果。共享管理员计时中的一次 Layout 热更新初始化异常单独保留，最终独占用户冷启动未复现。

临时用户 ID 124 已经身份核对后删除，并读回确认不存在；自身 access/session/active pointer/CSRF 记录全部不存在。最后清理用的管理员会话也正常注销。自建浏览器及 API contexts 已关闭；MySQL、Redis、前端和后端保留运行，结束时容器运行中，前端和后端 /docs 均 HTTP 200。

最终运行时 23 个检查全部通过；证据：[汇总](/Users/hqz/Downloads/element-plus/docs/reports/evidence/2026-10-18-form-contract-session-repair/session-renewal/verification-summary.json)、[自然到期](/Users/hqz/Downloads/element-plus/docs/reports/evidence/2026-10-18-form-contract-session-repair/session-renewal/natural-expiry.json)、[多标签页](/Users/hqz/Downloads/element-plus/docs/reports/evidence/2026-10-18-form-contract-session-repair/session-renewal/multi-tab.json)、[清理](/Users/hqz/Downloads/element-plus/docs/reports/evidence/2026-10-18-form-contract-session-repair/session-renewal/cleanup.json)、[撤销提示截图](/Users/hqz/Downloads/element-plus/docs/reports/evidence/2026-10-18-form-contract-session-repair/session-renewal/04-revoked-session-relogin.png)。所有证据不保存 token、Cookie 或 Authorization header。

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-18-session-renewal.md
EVIDENCE: READ identity token service / login controller / business HTTP / user store; SEARCH refresh, session TTL and actual callers; COMMAND plan structure checks passed.
PLAN_CHANGES: Preserve baseline; repair the existing session transport and atomic refresh authority; verify with focused regressions and real local services.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: Completed current-session execution, real-time verification, scoped review, cleanup and evidence reconciliation; no work item is bound.
BLOCK_REASON: none
UNBLOCK_ACTION: none

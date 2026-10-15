# HTTP 取消生命周期与错误保留验证

日期：2026-10-15。仅处理取消生命周期和错误上下文；保留上一轮 Axios 1.20.0、HTTP 源码接入及超时修复。

## 责任与修复

| 归属 | 查明的问题 | 本轮修复与受益 |
| --- | --- | --- |
| ZXUI canceler | 完成时重新计算内容 key；旧请求结束可能清掉新请求；JSON 序列化后 key 变化导致登记残留 | 用每次请求的固定登记与实例身份清理，取消替代请求不再串扰，完成请求及时释放登记 |
| ZXUI signal | 外部 signal 监听没有解绑，取消原因丢失 | 统一链接内部 controller，结束或取消时解绑，保留调用方 reason |
| ZXUI 并发插件 | 调用方带 signal 时插件取消没有作用到真实请求；排队取消不能立即结束 | 取消实际派发 signal，排队项立即拒绝并释放监听；内部按请求实例定位，复用公开 ID 不误伤其他请求 |
| ZXUI 错误契约 | 丢失原始 cause，重复分类可能再次包装，默认取消仍发失败通知 | 保留 cause/response/config，已分类错误原样返回；取消统一为 AbortError/ERR_CANCELED，提供 isAbortError，跳过默认失败反馈 |
| 业务 HTTP 适配 | 重新创建普通 Error，丢失库类型、取消标识和原始上下文 | 在原 HttpError 上补充 Problem Details 与 meta；取消提前抛出，不触发错误或重新登录提示 |

通用生命周期与错误契约均修在 `/Users/hqz/Downloads/element-plus/packages/http/`。业务仅修改 `src/utils/http.ts` 的错误适配与既有测试，未向业务页面加入额外取消机制。

## 真实业务验证

使用业务现有 `login()`、`getInfo()`、`getProject()`、HTTP/兼容请求层、Axios 1.20.0 和 JSDOM XMLHttpRequest，连接本机 FastAPI :8088。工程详情使用已有 `projectId=1`。

仅替换界面反馈入口，并用临时本地网关延迟交付真实后端响应，确保请求仍在传输中时触发取消；未伪造工程响应。反馈入口记录调用次数；没有执行浏览器页面点击验收或 computer use。两种模式分别在独立进程执行，源码模式加载 ZXUI HTTP TypeScript，安装模式加载业务实际依赖的构建包。

| 验证 | 源码直连 | 安装包 |
| --- | --- | --- |
| 真实登录与用户信息 | 通过 | 通过 |
| 外部 AbortController 取消工程请求 | XHR.abort 调用 1 次；AbortError/ERR_CANCELED；cause/config/reason 保留 | 相同 |
| 连续三个相同工程请求 | 前两个取消，第三个返回 projectId=1；旧请求清理未破坏替代请求 | 相同 |
| 已完成请求清理 signal | 添加/移除 abort 监听各 1 次；结束后 abort 不再影响传输 | 相同 |
| 取消后恢复普通直连请求 | 工程详情正常返回 | 相同 |
| 非法工程 ID 触发真实 422 | ValidationError，原 cause/response/config 与 problem/meta/requestId 均保留 | 相同 |

所有取消检查中，失败反馈与重新登录提示均为 0；真实 422 仅产生一次业务失败反馈。没有新建或修改工程数据；登录、查询、退出会产生正常鉴权及请求记录。

结构化证据：[源码模式](evidence/2026-10-15-http-cancellation/source-actual.json)、[安装模式](evidence/2026-10-15-http-cancellation/installed-actual.json)。记录不包含 token、请求头或原始错误对象。

并发插件当前未在业务全局启用，因此其 running/queued/同 ID 隔离边界通过库内真实客户端及 deferred adapter 锁回归，没有为验证而在业务启用插件。

## 质量检查

- ZXUI：`pnpm exec vitest run packages/http/__tests__`，8 个文件、58 项通过；仅在既有 canceler/client/concurrency 测试中补充本轮回归。
- ZXUI：修改文件 ESLint、`pnpm -C packages/http build` 通过；构建包含 TypeScript 类型检查。
- 业务：`./node_modules/.bin/vitest run src/api src/utils src/store/modules/user.login.test.ts --coverage.enabled=false`，17 个文件、74 项通过；源码别名模式同样 74 项通过。
- 业务：`yarn type-check`、`yarn lint:check`、前端约定脚本通过。
- 业务：显式 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` 与 `VITE_ZXUI_LOCAL=false` 的 `yarn build:prod` 均通过。
- 两仓库 `git diff --check` 通过；只读审查发现的同 ID 取消串扰已先复现失败、修复、测试通过，并经复查确认。

## 交付与边界

业务使用 `vendor/zxio-http-1.0.0-cancellation.20261015.tgz`，package.json 与 yarn.lock 同步；未发布 npm。该包从当前 HTTP dist 打包，包含上一轮超时修复，因此现在关闭源码模式也能获得同一修复。安装包的发布 manifest 不含工作区专用 source 条件，Axios 仍为 1.20.0。

验证包 SHA-256：`baca6c457ed408aa38ce2ce6f6a0a140e3e2700c3714937071c69e16e04afd46`。安装后的并发插件构建文件与本轮 dist 校验一致。

本轮保留既有“相同请求取消前一个”的策略，不调整重试、去重、超时规则、分页、响应插件顺序或页面交互。验证完成后关闭本轮启动的后端服务，保留原有 MySQL/Redis 运行状态。

## Plan-stage Checkpoint

STATUS: PLAN_UPDATED
FILES_WRITTEN: docs/plans/2026-10-15-http-cancellation.md
EVIDENCE:
- READ: ZXUI canceler/concurrency/errors/client and business http/request/project API.
- SEARCH: AbortController, cancellation/error hooks, pending registration ownership.
- COMMAND: plan structure checks, focused tests, lint/type checks, builds and actual-backend probes.
PLAN_CHANGES: Added dependency-ordered lifecycle/error/actual-verification tasks and recorded execution results.
WORK_ITEM_SYNC_SUGGESTION: none; no work item attached.
NEXT_ACTION: implementation complete; user review of the linked evidence.
BLOCK_REASON: none
UNBLOCK_ACTION: none

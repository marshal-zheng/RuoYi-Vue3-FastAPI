# RuoYi 生产静态服务与会话交错验收

状态：本地生产页面验收、迟到 Cookie 竞态修复、自然续期、重登、权限交错及清理已完成。保留既有改动，未提交或推送。

## 本轮范围

基于当前未提交工作区重新构建生产包，以独立 `nginx:1.27-alpine` 容器在 `127.0.0.1:18080` 提供静态服务。开发前端 80、后端 8088、现有 MySQL/Redis 保留运行。未创建 worktree、未部署外部环境。ZXUI 继续源码直连，本轮未修改库源码。

已核对前端 Dockerfile、Nginx、Router history、生产环境 `/api` 与 `real` runtime、开发同步开关。仓库 Nginx 的 `try_files ... /index.html` 支持 history 深链接，`/api/` 转发时移除前缀；Compose 的 backend 容器端口 8000 与原配置一致。本轮临时配置只把 `backend:8000` 改为 `host.docker.internal:8088`，没有修改部署配置。Colima 未挂载宿主机 `/tmp`，因此通过 `docker cp` 将构建产物复制到自有容器，运行时 index SHA256 与最终构建一致。[运行记录](evidence/2026-10-19-production-session-acceptance/static-runtime.json)、[有效 Nginx](evidence/2026-10-19-production-session-acceptance/nginx-effective.log)。

## 真实页面与权限生效时机

| 页面状态 | 真实入口 | 文档直达、刷新、浏览器返回 | 最终包直达复验 |
| --- | --- | --- | --- |
| 分配角色 | 自有用户行“分配角色” | 通过 | 通过 |
| 分配用户 | 自有角色行“分配用户” | 通过 | 通过 |
| 字典数据 | 字典类型链接 | 通过 | 通过 |
| 调度日志 | 定时任务“日志” | 通过 | 通过 |
| 生成配置 | `sys_post` 行编辑图标 | 通过 | 通过 |
| 工程详情 | 工程名称链接 | 通过 | 通过 |
| 拓扑设计 | 版本“图编辑” | 通过，保留 versionId | 通过 |
| 设备详情 | 设备名称链接 | 通过 | 通过 |
| 设备无 ID | 新加、填写名称/自有分类、下一步 | 通过 | 通过 |

生成器 `page=1`、拓扑 `versionId=1` 在刷新后保留。草稿刷新后仅验证无 ID 路由和默认画布可用，不声称未保存草稿跨刷新持久化。调度日志为空，未创建或执行任务。设备入口由自有临时菜单暴露；现有工程、版本、设备、字典及生成元数据均只读。

证据：[入口与刷新](evidence/2026-10-19-production-session-acceptance/production-routes.json)、[直达](evidence/2026-10-19-production-session-acceptance/production-direct.json)、[浏览器返回](evidence/2026-10-19-production-session-acceptance/production-back.json)、[修复后最终包](evidence/2026-10-19-production-session-acceptance/production-routes-after-fix.json)。

普通角色编辑后，后端每次鉴权重新读取当前角色/菜单，因此当前字典页面再次查询立即返回 403；生产前端仍持有既有路由与权限快照，完整刷新才重新读取 `getInfo/getRouters` 并进入 404。重新授权后原 404 保持，刷新相同地址恢复字典页面。生产构建没有 `__DEV_MENU_SYNC__`，没有开发 SSE 请求；普通角色编辑也没有发布菜单变更事件的契约。本轮没有新增实时权限推送。[权限时机实测](evidence/2026-10-19-production-session-acceptance/permission-effective-timing.json)。

验收角色首次读取工程版本出现 403，原因是夹具最初只复制已有菜单权限，而仓库没有版本权限菜单；补齐自有版本读取权限后正常。这是夹具授权不足，未作为业务缺陷修改。

## 新发现：迟到续期响应可覆盖新会话 Cookie

已有会话版本检查可以阻止旧响应体改写访问令牌，但不能阻止浏览器处理响应的 `Set-Cookie`。通过延迟真实续期响应、在同一文档内调用真实 Store 退出并以真实登录控件切换 A→B，再交付旧 A 响应：访问令牌仍属 B，刷新 Cookie 却被旧响应覆盖。[修复前诊断](evidence/2026-10-19-production-session-acceptance/same-document-refresh-switch.json)。

这个分支明确属于同文档诊断：退出由 Store action 触发，路由跳转由诊断脚本调用。正常用户菜单退出使用 `location.href='/login'`，整页跳转会取消旧文档请求；本轮也实测了这条真实控件路径，不能把两类证据混为一谈。

修复复用已有会话机制，涉及 4 个生产源文件：

- `auth.ts` 为当前安全会话持有 AbortController，清凭证时同步取消旧会话的续期网络请求。
- `session.ts` 向 Axios 续期请求传入该 signal，并抽取已有 Web Lock 为 Cookie 操作共用入口；没有 Web Locks 时以 Promise 链保持同文档顺序。
- `api/login.ts` 的登录、退出与续期共用原有 `ruoyi-session-refresh` 锁。
- `user.ts` 的旧登录响应缺少 CSRF 时的补取入口也使用同一锁，覆盖实际 Cookie 写入调用。

选择依据：浏览器已拥有 Cookie 与同源标签的资源边界，现有实现已用 Web Locks 协调续期，扩展它即可；不新增后端接口、锁服务或跨标签权限推送。收益是阻止旧续期写入新凭证；代价是其他标签正在续期时，登录/退出需等待该次请求完成或超时。本地单个续期请求仍受原有 10 秒超时约束；不声称多个排队操作的总等待恒定小于 10 秒。参照 [Axios AbortController](https://axios-http.com/docs/cancellation) 与 [Web Locks 官方行为](https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API)。

三个新增回归修复前均失败：续期未携带可取消 signal、登录未等待续期锁、退出未等待续期锁；修复后通过。[失败基线](evidence/2026-10-19-production-session-acceptance/cookie-race-tests-before.log)、[通过日志](evidence/2026-10-19-production-session-acceptance/cookie-race-tests-after.log)。

最终生产包重放原诊断：旧续期请求 `net::ERR_ABORTED`，新 B 访问令牌和刷新 Cookie 均保持不变。[修复后](evidence/2026-10-19-production-session-acceptance/same-document-refresh-switch-after.json)。另用两个真实标签：A 的续期持锁，B 的真实登录点击后处于等待，锁快照存在 1 held/1 pending，登录请求尚未发出；释放 A 响应后 B 登录完成，随后 B 的读取按 `401 → refresh 200 → read 200` 成功。[跨标签记录](evidence/2026-10-19-production-session-acceptance/native-cross-tab-cookie-order.json)。这验证 Cookie 顺序，不声称不同标签能长期保有不同登录身份或自动同步所有 UI。

## 会话隔离与恢复

- 慢用户信息、慢菜单读取期间，通过用户菜单真实退出并登录受限 B，旧文档请求被取消，新账号权限没有恢复成 A。[真实切换](evidence/2026-10-19-production-session-acceptance/delayed-getInfo-switch-final.json)、[慢菜单](evidence/2026-10-19-production-session-acceptance/delayed-menu-switch.json)。
- 同文档另行诊断：旧 `getInfo/getRouters` 的真实 200 响应实际到达后，现有安全会话版本仍保持 B 的身份、菜单和隐藏路由边界。[用户信息 200](evidence/2026-10-19-production-session-acceptance/same-document-getInfo-switch.json)、[菜单 200](evidence/2026-10-19-production-session-acceptance/same-document-menu-switch.json)。
- 只失效自有访问会话并延迟真实 401，退出时旧查询被取消，B 登录后没有“重新登录”提示。记录耗时约 2.4 秒，未以 10 秒 HTTP 超时代替取消证据。[迟到 401](evidence/2026-10-19-production-session-acceptance/late-401-switch.json)。
- 同源新标签无 sessionStorage 访问令牌时，通过刷新 Cookie 静默恢复；原标签的旧访问令牌随后按 `401 → refresh 200 → read 200` 恢复。[多标签恢复](evidence/2026-10-19-production-session-acceptance/multi-tab-restoration.json)。
- 最终包仅撤销自有 B 的 access/session，真实查询及续期均返回 401，页面保留一个重登入口；点击后进入带原地址的登录页，真实登录返回业务页。稳定提示框位于 y=16，完整可见。[最终重登](evidence/2026-10-19-production-session-acceptance/expired-relogin-final.json)、[截图](evidence/2026-10-19-production-session-acceptance/expired-session-prompt-final.png)。这属于真实后端会话失效，不冒充等待 7 天刷新 JWT 自然过期。

最终包自然到期：等待约 620 秒，访问缓存 TTL=-2、刷新会话仍存在；真实查询按 `refresh 200 → GET user/list 200` 完成，仍为同一用户/会话、到期时间延长且无重登提示。请求前撤回字典权限，续期后已有页面快照保持；完整刷新字典地址后权限和路由已移除，重新授权并刷新恢复。[自然到期及权限交错](evidence/2026-10-19-production-session-acceptance/natural-expiry-final.json)。第一次等待期间被辅助标签同账号重登替换，已作废，原因是本地实际 `app_same_time_login=false`，不是 CSRF 或续期故障。[作废说明](evidence/2026-10-19-production-session-acceptance/discarded-natural-attempt.json)。

## 视觉与质量检查

9 个页面状态在 1440×1000、1100×800 各保存稳定截图，共 18 张，逐张查看；无持续加载、入口遮挡、必需控件越出视口或文档横向溢出。字典/生成器宽表允许表内横向滚动，不声称所有非固定列同时可见。生成器未保存；拓扑画布只读，未执行仿真、导出或保存。[视口记录](evidence/2026-10-19-production-session-acceptance/visual-checks.json)。自然续期截图展示查询收尾过程，只支撑身份连续性，最终结果以请求和会话核对为准。部分早期 `*-entry/refresh` 截图捕获到加载态，只作为过程证据；视觉结论使用 `*-1440-final/1100-final`，重登使用 `expired-session-prompt-final`。

- 最终 HTTP/会话定向回归：7 文件 88 项通过；包括 3 个新增回归。[日志](evidence/2026-10-19-production-session-acceptance/http-session-tests-final.log)。
- 最终源码直连路由/页面回归：7 文件 68 项通过，与上述测试有 7 项 user store 测试重叠，不将两组相加当作不同测试总数。[日志](evidence/2026-10-19-production-session-acceptance/route-tests-final.log)。
- 后端续期/安全服务回归：18 项通过，使用自有隔离测试键；后端源码未改。[日志](evidence/2026-10-19-production-session-acceptance/backend-session-tests.log)。
- 最终 `vue-tsc --noEmit`、本轮 6 文件 ESLint 均通过。[类型](evidence/2026-10-19-production-session-acceptance/typecheck-final.log)、[Lint](evidence/2026-10-19-production-session-acceptance/lint-final.log)。
- 源码直连最终生产构建通过，保留既有 Browserslist/Sass/分包体积提示。[构建](evidence/2026-10-19-production-session-acceptance/build-fixed.log)。
- `validate.sh --changed` 失败于既有仿真删除文件仍被传给 ESLint，以及仿真 `FaultBoardPanel.vue` 颜色值；这些路径不在本轮验收范围，未改。[原始日志](evidence/2026-10-19-production-session-acceptance/frontend-standards.log)。

## 清理、保留与未验证边界

两个自有用户 145/146、角色 98/99、6 个菜单及分类 2 的删除均返回 204；数据库有效记录、用户/角色关联、意外保存设备及自有 access/session/active/CSRF 残留全部为 0。正常退出自有管理员会话，仅按值匹配删除本轮管理员 CSRF。自建浏览器关闭，临时 Nginx 正常停止后移除，自建 `/tmp` 构建目录删除。原开发前端及后端仍为 200，MySQL/Redis 保留运行。[API 清理](evidence/2026-10-19-production-session-acceptance/cleanup-api.json)、[存储核对](evidence/2026-10-19-production-session-acceptance/cleanup-storage.json)、[服务](evidence/2026-10-19-production-session-acceptance/services-final.json)。

初始基线中的既有文件没有丢失或无关改写；除 4 个生产源文件、1 个既有测试与新增 1 个回归文件外无源码变更，ZXUI 无改动，两仓库 HEAD 保持。未提交、推送或外部发布。[本轮增量](evidence/2026-10-19-production-session-acceptance/scoped-source.diff)、[保留核对](evidence/2026-10-19-production-session-acceptance/preservation.json)、[机器汇总](evidence/2026-10-19-production-session-acceptance/verification-summary.json)。

明确未验证：完整 Docker builder 镜像构建、外部部署、TLS/跨站 Cookie、7 天刷新令牌自然到期、无 Web Locks 浏览器的跨标签互斥、不同账号标签长期共存/自动身份 UI 同步、普通角色变更实时推送、仿真运行、既有工程/设备/生成配置的写入和生成文件。没有重复 169 项全目录验收。最终包 1105 条响应无静态资源失败或 5xx，未记录页面异常；含预期失效会话的 401。[运行汇总](evidence/2026-10-19-production-session-acceptance/runtime-summary.json)。

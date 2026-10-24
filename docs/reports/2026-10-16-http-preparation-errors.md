# HTTP 第 3 轮：请求准备错误统一处理

日期：2026-10-16。已实施并完成本轮验证，未提交 Git、未发布 npm。

## 结果与责任

通用问题修在 ZXUI `packages/http`，业务只修复本地错误信息的回退。提交 pending、领域反馈、登录恢复与表单流程继续由业务负责，本轮没有修改 `useOperation` 或增加 HTTP 提交策略。

| 责任 | 本轮处理 |
| --- | --- |
| ZXUI 请求准备 | 前置 hook、token 获取/应用、显式 URL 拼接、超时配置失败进入既有错误管线一次，位于重试循环之外 |
| ZXUI 错误分类 | 新增 `RequestPreparationError`；取消仍为 `AbortError`；没有 response 不再自动等同网络错误 |
| ZXUI 上下文 | 保留原始抛出值为 `cause`，保留最新成功加工的 `config/request`，取消保留 signal 与原始 reason |
| 业务错误加工 | 本地失败没有响应 payload 时保留具体 message；继续使用原反馈入口及 `silentError`、反馈 key 等选项 |

收益是准备失败可以可靠释放业务 pending、立即人工重试，并保留定位原因；不会因误判网络故障而自动重复执行准备逻辑。代价是错误钩子的类型契约统一为 `HttpError`，已同步实际消费者、文档和交付包。

## 根因与实现

1. 原 `request()` 在进入发送阶段的 `try/catch` 前执行前置加工、token、URL 和超时准备，失败会直接退出，绕过 `onError`。
2. 原 factory 把所有没有 response 的异常都分类为 `NetworkError`。Axios 的 `transformRequest` 或配置校验失败因此可能被默认重试，且原始错误通常不带 config。
3. Axios 即使已创建 transport 对象，也可能因非法 timeout 等配置失败；因此已知配置错误代码要先于网络分类判断。
4. 原业务 Problem Details 回退会用通用文案覆盖本地准备异常，造成原始原因丢失。

ZXUI 在准备阶段逐个更新当前配置，每个 hook 返回的新配置都会成为后续错误的上下文。准备失败包装为 `RequestPreparationError`，`code=ERR_REQUEST_PREPARATION`，`cause` 直接指向原始抛出值，不修改被冻结的原错误。原始异常的 code、stack、response 等仍可通过 cause 查看。

取消优先识别标准取消错误及 signal 原样抛出的 reason；当自定义 reason 自身也含 `reason` 字段时，仍保留整个对象的身份，不误取其嵌套字段。取消不触发默认失败通知。

发送阶段交给错误钩子前也先规范化，并为缺少 config 的原始异常提供当前请求配置。`createHttpError/resolveHttpError` 接受 unknown 与可选 fallbackConfig；已有 `HttpError` 保持原实例。`onError` 接收规范化的 `HttpError`，沿用原有的注册顺序、抛错终止和返回值不恢复请求的语义。

明确的 Axios 配置、URL、不支持等错误归为准备错误，重试管理器仅增加对此类型的禁止重试判断，即使自定义条件返回 true 也不会重试。其他重试次数、延时、通知时机和策略不变。无法可靠判断阶段的普通本地异常保留基础 `HttpError`，默认不重试；显式自定义 retryCondition 继续由调用方决定。没有预执行 Axios serializer/transform，也没有重写 adapter 或增加阶段状态机。

选型复核了 [Axios 官方错误处理](https://axios.rest/pages/advanced/error-handling)、[官方取消契约](https://axios.rest/pages/advanced/cancellation)及已安装 Axios 1.20.0 的 Axios/dispatchRequest/http/XHR 实现：准备失败、已发出但无响应、收到错误响应需要区分；创建 adapter/transport 不是请求已发送的充分证据。直接复用已有错误类、管线和原生 signal，无需新增依赖。

## 验证结果

| 验证 | 结果 |
| --- | --- |
| 新增回归 | 既有 client.test.ts 中 13 项、既有业务 http.test.ts 中 2 项；没有新增测试文件 |
| ZXUI HTTP 全部用例 | 7 文件、93 项通过 |
| 既有示例生成器用例 | 6 项通过 |
| HTTP 严格测试类型 / 定向 ESLint | 通过 |
| HTTP 独立 ESM/CJS 构建 | 通过 |
| 业务受影响回归：源码直连 / 安装包 | 各 24 文件、195 项通过 |
| 前端 lint / type-check | 通过 |
| 生产构建：源码直连 / 安装包 | 通过；21.39 秒 / 19.98 秒，仅现有 chunk 大小提示 |
| 两仓库 git diff --check | 通过 |
| 独立只读审查 | 无剩余阻塞；审查方另跑 HTTP 93 项、业务 HTTP 20 项及 ESM/CJS 类型检查 |

首先观察到 7 项预期失败：前置 hook、token 获取/应用、显式 query serializer 和两种准备取消均未进入错误钩子，普通本地异常也被误分类。之后补查冻结的已有 HttpError 和已创建 transport 的配置失败，先观察失败再分别修复。业务两项回归也先复现错误信息被通用文案覆盖。回归没有铺设新的框架或测试目录。

## 真实业务验证

源码直连和安装包模式各 **8 项通过**，使用实际业务请求模块、ConfigList 删除 handler、Vue pending、Axios 1.20.0、JSDOM XMLHttpRequest 和真实本地 FastAPI：

1. 真实登录和鉴权信息正常。
2. 实际 ConfigList 删除操作在准备失败后释放 pending；重入复用同一操作，错误反馈一次、没有派发请求；修正后同一 handler 真实删除成功并刷新一次。
3. token provider 抛出被冻结的原始错误：保留 cause 和具体原因，不分类为目标请求网络错误，不自动重试；pending 释放后人工重试真实查询成功。
4. Axios 实际 transformRequest 编码失败：保留原始 TypeError 与 config，只执行一次编码；pending 释放，恢复编码后真实业务查询成功。
5. 准备期间抛出自定义取消 reason：cause、reason 和 signal 身份保留，零派发、零反馈，pending 释放，后续真实查询成功。
6. 业务下载准备失败：保留 silentError/feedback 上下文，下载入口只反馈一次，pending/loading 释放；重试后真实用户 Excel 导出成功。
7. 暂存真实查询响应后取消：保留 reason/signal，pending 释放且无错误提示，后续真实查询成功。
8. 暂存真实用户 Excel 响应后取消：pending/loading 释放，不保存文件、不发出失败提示。

两份真实 Excel 均由 openpyxl 解析：1 个工作表、至少 2 行、13 列，含预期用户。临时二进制已删除。仅创建、操作和清理带专用标记的本地临时配置，两模式分别通过真实列表查询确认遗留数为 0。正常登录/导出等审计记录保留。

结果见 [源码直连](evidence/2026-10-16-http-preparation-errors/actual-source.json)、[安装包](evidence/2026-10-16-http-preparation-errors/actual-installed.json)、[Excel 检查](evidence/2026-10-16-http-preparation-errors/workbooks.json)。

## 交付与验证边界

业务切换至本地归档 `vendor/zxio-http-1.0.0-preparation.20261016.tgz`，更新锁文件，Axios 保持 1.20.0。归档、构建及安装目录的 50 个文件已比对；package.json 按 JSON 语义比对以消除打包格式差异，LICENSE 来自仓库根目录。详见 [包一致性](evidence/2026-10-16-http-preparation-errors/package-integrity.json)。未发布 npm。

更新公开文档、错误钩子类型及网络错误示例，示例改用明确的 ERR_NETWORK。生成器在隔离目录执行，只同步 HTTP 类型/示例条目及四段 HTTP 文档全文，非 HTTP 聚合条目保持不变，见 [生成产物](evidence/2026-10-16-http-preparation-errors/metadata.json)。全类型生成命令遇到范围外 text-editor 生成器加载 keybindings 声明依赖失败；HTTP/组件目标生成器已单独成功执行，没有修改该依赖。

全工作区 changed 规范脚本仍因 `VersionList.vue` 已有 console 调用报错，已通过本轮开始时的文件 hash 确认它未被本轮修改。该脚本的其他 guardrails 通过，前端全量 ESLint/type-check 单独通过；没有把该脚本整体报告为通过。既有工作区改动保持，见 [基线保留](evidence/2026-10-16-http-preparation-errors/baseline-preservation.json)。

准备失败由探针注入真实 hooks/token provider/Axios encoder，恢复请求访问真实后端。转发网关只暂存真实后端响应，没有构造成功/失败内容。确认动作、反馈、loading 和保存文件入口由探针记录；未使用 computer use，没有浏览器点击或视觉验收，不声称全部页面逐一实测。

本轮没有变更后端、操作 pending、提交策略、查询缓存、请求共享、日志体系或其他 UI。仅停止本轮启动的后端及其子进程，保留原有 Docker/Redis 和其他已有服务。命令、计数和限制见 [checks.json](evidence/2026-10-16-http-preparation-errors/checks.json)。

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN:
- docs/plans/2026-10-16-http-preparation-errors.md
EVIDENCE:
- READ: both AGENTS.md files, current library/client/error/retry contracts, business feedback/request/operation sources and preceding reports.
- SEARCH: actual error-hook consumers, fallback context, Axios source, public contract and generated metadata owners.
- COMMAND: plan structure verified before implementation; completion evidence is recorded above and in checks.json.
PLAN_CHANGES:
- Included explicit Axios setup codes and the narrow preparation-error retry guard after the transport-created option failure was reproduced.
WORK_ITEM_SYNC_SUGGESTION:
- none
NEXT_ACTION: completed current-session execution and independent review.
BLOCK_REASON: none
UNBLOCK_ACTION: none

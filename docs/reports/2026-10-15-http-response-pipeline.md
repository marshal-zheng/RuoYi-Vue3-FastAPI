# HTTP 响应管线修复与真实业务验证

日期：2026-10-15。本轮仅修复响应插件提前截断处理链的问题；既有 Axios、超时和取消修复保持。

## 责任与根因

问题属于 ZXUI `packages/http`，业务不需要补丁：

- 客户端把默认成功判定与解包放在普通 `afterResponse` 队列末尾；任一 hook 返回普通数据就直接退出，因此后续插件、默认成功判定和返回选项可能不执行。
- 运行期通过 `use()` 或 `extendTransforms()` 添加的 hook 位于原默认解包之后，也可能永远无法执行。
- Grid List 插件把 `code/data` 外壳与列表数据扁平合并。即使单独取消提前退出，最终 resolver 仍可能拿到未经加工的内层数据，或失去可靠的协议边界。
- 列表加工中的对象展开会丢失业务附加的非枚举 `__httpMeta`，导致 requestId 等元数据不能传到消费者。

## 最终执行契约

| 阶段 | 行为 |
| --- | --- |
| 1. 响应加工 | 按注册顺序执行全部用户和插件 hook，包括运行期追加项。返回 AxiosResponse 替换当前响应；返回普通值替换 response.data 后继续；undefined/void 保留当前响应 |
| 2. 成功判定 | 正常转换模式下，所有加工完成后统一调用一次 successResolver，判定最终响应体，处理成功通知或抛出业务错误 |
| 3. 最终解包 | 在末尾统一返回 resolver.data，插件不负责提前结束管线 |

默认 finalizer 已移出普通响应 hook 队列。Grid List 保留协议外壳，只在对应 payload 内补充 list/pager；克隆时保留属性描述符，同时保持原 payload/pager 不变。公共 hook 类型支持同步和异步 void，便于只观察响应而不替换数据。

`isReturnNativeResponse: true` 保留既有语义：执行全部加工后返回完整 AxiosResponse，并跳过业务 resolver；`isTransformResponse: false` 返回加工后的完整 body，同样跳过 resolver。这里的 native/body 包含加工结果，不表示未经加工的传输原文。HTTP 非成功状态仍由 Axios 拒绝。

hook 作者仍需保留最终 resolver 所需的协议字段。本次不是在加工前校验原始业务码，也不新增强制协议格式。

## 必要兼容边界

普通返回值现在会继续进入最终判定，因此复查发现并修正默认 resolver 对 `false` 的误读：只在非 null 对象上读取协议字段；裸 primitive 按 HTTP 状态判定。`false` 可正常作为成功结果返回，`{ success: false }` 仍判失败。此改动只保障响应加工返回值的兼容性，没有扩展其他成功策略。

以前依赖“hook 返回普通值即终止”来定制最终返回值的消费者，需要迁移到 successResolver 的 data 返回契约；行为变化和迁移方式已写入库 README 与公开类型说明。

## 真实业务验证

通过现有业务 login/getInfo、工程列表、角色列表、字典集合及工程导出函数，使用真实 Axios 1.20.0、JSDOM XMLHttpRequest 和本机 FastAPI :8088。仅替换界面反馈入口，并添加临时响应观察插件记录阶段顺序；请求、登录态、业务数据和后端响应均真实执行。没有使用 computer use 或进行浏览器点击验收。

源码模式和本地安装包模式各在独立进程完成 8 项检查：

| 检查 | 结果 |
| --- | --- |
| 登录与用户信息 | admin 登录、鉴权查询正常 |
| 工程分页列表 | items=1、total=1、page=1、pageSize=2；pager 与请求及业务响应一致 |
| 角色分页列表 | items=2、total=2；原业务数据结构保留 |
| 字典集合 | items=21；原 items 结构保留 |
| 原始 Axios 列表响应 | status/config/headers 保留，加工后的 body/pager/meta 可用；resolver 未调用 |
| 未解包列表 body | 加工执行，完整 body 保留；resolver 未调用 |
| 二进制工程导出 | application/zip，492 字节，仍正常穿过完整响应链 |
| 真实非法分页参数 422 | ValidationError 正常拒绝，cause/config/response/requestId 保留；一次失败反馈 |

普通列表和导出均记录到 `late-hook → resolver`，证明运行期追加 hook 在最终成功判定之前执行。各列表的非枚举 `__httpMeta`/requestId 在 Grid 加工后仍保留。真实 422 在传输错误链处理，不进入成功响应链。

未新增或修改工程、角色、字典等业务记录；只有登录、查询、导出及退出操作。结构化证据：[源码模式](evidence/2026-10-15-http-response-pipeline/source-actual.json)、[安装包模式](evidence/2026-10-15-http-response-pipeline/installed-actual.json)。证据未保存 token、请求头或原始错误对象。

## 回归与质量检查

- ZXUI 现有 client/grid-list 测试中补充回归：先观察到 9 项目标失败，再修复；非枚举元数据与 false 兼容边界也分别先观察失败后修正。
- `pnpm exec vitest run packages/http/__tests__`：8 个文件、67 项通过。
- 两个改动测试文件单独 strict TypeScript 检查通过；公共声明的同步/异步 void 消费检查通过。
- HTTP 修改文件 ESLint、Prettier 及 `pnpm -C packages/http build` 通过；包构建包含源代码类型检查。
- 业务 API/utils/login 测试：安装包与 HTTP 源码别名分别为 17 个文件、74 项通过，没有新增业务测试文件。
- 业务 `yarn type-check`、`yarn lint:check`、前端约定检查通过。
- 显式 `VITE_ZXUI_LOCAL=false` 与 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` 的生产构建均通过，使用独立临时输出目录。
- 两仓库 `git diff --check` 通过。只读复查确认外壳、元数据、冻结对象、primitive/数组/二进制、晚注册 hook 和 native/raw 边界，无剩余需处理问题。

## 本地交付与范围

业务本轮只更新 HTTP vendor 依赖与锁文件，没有新增 HTTP 适配或页面实现改动：

- 包：`ruoyi-fastapi-frontend/vendor/zxio-http-1.0.0-response-pipeline.20261015.tgz`。
- SHA-256：`cb5dcc419e24e53df6c6f78e824db70b28eab734d3d225f75209619f8f52022a`。
- 已核对安装后的 client/grid-list/resolvers 构建文件及公开声明与本轮 dist 一致；发布 manifest 不含工作区专用 source 条件，Axios 仍为 1.20.0。
- 源码直连和关闭源码模式均可使用本次修复；未发布 npm、未提交 Git。

下载错误解码、query/body 语义、防重复提交、请求身份、重试、日志等剩余事项未混入；本轮未改变分页字段计算规则。验证后关闭了本轮启动的后端服务，原有 MySQL/Redis 状态保持。

## Plan-stage Checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-15-http-response-pipeline.md
EVIDENCE:
- READ: ZXUI client/grid-list/resolvers/types and business HTTP/list APIs.
- SEARCH: afterResponse, extendTransforms, native/raw options and response metadata.
- COMMAND: plan structure, failing regressions, passing HTTP/business suites, strict type checks, lint/builds and actual-backend probes.
NEXT_ACTION: implementation complete; user review of the report and local changes.
BLOCK_REASON: none
UNBLOCK_ACTION: none

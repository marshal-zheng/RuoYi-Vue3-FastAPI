# HTTP / API / Store / SDK / Mock 独立审查

审查日期：2026-10-14。审查者为本轮新委派的 HTTP 专项代理；未以此前报告的通过结论作为证据。实现与 `/tmp/ruoyi-lint-cleanup-baseline-20261013` 比较，后台相关变化与 `/tmp/ruoyi-lint-backend-baseline` 比较，核对真实 controller → service → `ResponseUtil` 工厂。发现项与根代理核验后，在明确范围内直接修复。

## 结论

本范围发现并关闭 8 类 P2 缺口。没有发现本轮清 lint 引入的 P0 / P1 问题。部分问题是历史错误在新契约类型化后仍被 mock 或死适配器掩盖，不能用“以前测试通过”证明其正确。

最终 HTTP 专项验证：39 个测试文件、178 项测试通过；完整 Vue 类型检查、mock 严格类型检查、API / store / mocks 的零警告 ESLint 门禁通过；mock contracts / overlays 严格门禁通过。详细命令、退出码、负控和日志见 [http-verification.json](http-verification.json)。根代理负责组件库、业务整体构建和 E2E 的最终验收，本专项不把聚焦测试冒充全仓验证。

## 发现与修复

| 优先级 | 问题、实际影响和 owner 证据 | 最终处理 |
| --- | --- | --- |
| P2 | `client/types.gen.ts:151` 的 SSE 参数用 `RequestOptions<never>`，事件 callback 的 `data` 是 `never`；core 的 `createSseClient` 参数遗漏其泛型，callback 又退成 `unknown`。独立真实 tsc 访问 `event.data.id` 编译失败。 | 修改 3 份维护模板，通过正式生成入口再生。状态码映射 payload、直接 core resource callback 与 generator 共用正确数据类型，未断言 callback、未删除泛型。新测试同时通过完整编译和真实 Fetch / stream 解析。 |
| P2 | SSE `id/retry` 控制帧也派发 callback，携带 `data: undefined`，会违反新数据类型并使读取 `data.id` 的 callback 异常。负控实际获得 2 次 callback，正确应为 1 次。 | `core/serverSentEvents.gen.ts:185` 仅把带 `data` 的帧作为数据事件；续接 ID 和 retry 仍保留。与 [WHATWG event stream interpretation](https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation) 的空数据缓冲区处理一致。 |
| P2 | `_shared/http-client.ts` 将真实解包 request 用 `as unknown as AxiosInstance` 伪装；另有无生产消费者的重复 user login / logout / 蛇形密码适配和 `/project/{id}/topology` GET / PUT。真实后台只有 canonical auth 及 `/project/topology/{id}`、`/project/topology/save`。旧 unit test 借 MSW 假路由继续给假入口“验收”。 | 删除无生产消费者的假 Axios 适配器、死 API 入口、旧拓扑 MSW 路由及死 mock 信封类型。保留 `_shared/types/common.ts` 的既有 canonical 类型。旧拓扑测试改用真实公开 API；旧地址负控明确进入未实现 501。 |
| P2 | `simulation.ts`、共用 unhandled 和 overlay unsupported 仍返回 `{ code, msg, data }` / `application/json`，测试继续期待旧信封。 | 统一 ProblemDetails 的 `type/title/status/detail/instance/errorCode` 和 `application/problem+json`，保留只读拒绝行为、明确原因和 debug headers。负控不再容许旧 `code/msg/data`。 |
| P2 | `system.ts` 的创建、更新、删除、授权等仅 echo 输入或空成功，数据源 system repository 实际只读，后续 GET 始终不变；给它们补 201 / 204 仍是在冒充已实现写入。 | 根代理批准后，将全部 22 项未实现 system 状态写入硬切为明确 501 ProblemDetails，registry 同步 unsupported 能力；全 registry unsupported 由 13 项变为 35 项。其 GET 保留。正常真实后台不变；offline 系统写入的行为有意改为拒绝，不能再展示虚假的保存成功。确有 session 状态效果的 auth logout 保留实际 204 空 body。 |
| P2 | `user.ts` 的 `/system/user/deptTree` mock 仍为裸数组，真实 `user_controller.py` 明确 `ok_collection`，API 已承诺 `HttpCollection`。部门树消费者得到 `items: undefined`。 | `user.ts:238` 返回 `{ items }`；用真实 `deptTreeSelect` API 的 MSW 回归验证 User 业务入口。 |
| P2 | 有实际 Dexie 持久化的 project / version / clone 创建却返回 200 且没有 Location；clone 仍接受 `versionId` 旧别名，忽略调用者必填 `versionNumber`，改成 `V{id}`。真实 `CloneProjectVersionModel` 和 service 必须使用 `sourceVersionId/versionNumber/versionName`。 | 持久化创建返回 201 + 可 GET 读回同一资源的 Location；删除返回真实 204 空 body。clone repository 直接消费生成模型，运行边界检查必填字段并拒绝旧别名；保存请求版本号和名称、复制拓扑、检查重复号 409，并验证拒绝不新增记录。 |
| P2 | 协议 export 标记 `Promise<Blob>` 却 POST JSON，真实 endpoint `protocolId: int = Form(...)` 返回 XLSX；另外 cache 的两条后台声明仍 `List[...]`，实际 `ok_resource(list)` 变成 `{ items }`，导致再生 SDK 假类型。 | 由根代理修复 protocol 表单 / blob 解码并做 native binary 证据；本专项独立 ASGI probe 证实 JSON 422、Form 200、streaming 内容保留。根代理将 cache 模型改为 `CollectionResult[CacheInfoModel]/CollectionResult[str]` 并正式 export；本专项正式再生 SDK。未手写 generated 输出。 |

## 类型与行为检查

- `request` 的公开缺省类型保持 `unknown`；逐个核对修改过的 system、monitor、tool、device、protocol、project、simulation 请求方法、query / body 和成功形态。外层列表经 `ok_resource` 必須进入 `items`，嵌入资源内部的数组保留其业务含义；资源、批量结果、204 `null` 分开处理。
- 核对 permission 路由树转换、ParentView 路径展开、不可变 snapshot、user login / refresh 的 camelCase CSRF token、退出 session 和 dictionary 缓存。没有通过恢复 array / data / items 多分支兼容掩盖不一致。
- SSE 保留的唯一 payload 类型断言位于真实解析 / 可选校验与转换后的 transport I/O 边界，沿用 SDK 请求映射泛型。没有 `as Client` 或 callback 整体强转；未加入 `as unknown as`、`any`、`@ts-ignore` 或关闭规则。适配器的伪 Axios 双重断言已删除。
- 新 optional 字段按严格 `exactOptionalPropertyTypes` 用条件对象字段处理，没有把 DTO 的可选字段放宽为任意 `undefined`。
- SDK 在独立临时目录用锁定 generator → owner postprocess → 精确 formatter 重新生成 16 个文件，与仓库输出逐字节一致。重复 postprocess 无改动，未知结构负控拒绝且没有部分写入。见 [http-sdk-proof.json](http-sdk-proof.json)。

## 测试证据和边界

[最终 API / store / mocks / unit API 测试](http-api-mock-unit-final.log)、[完整类型检查](http-type-final.log)、[mock 严格类型检查](http-mock-strict-final.log)、[零警告 lint](http-lint-final.log)、[生成幂等与拒绝负控](http-sdk-proof.json)、[ASGI Form / JSON 对照](http-protocol-export-probe.json) 均是本次新执行。

负控保留了 SSE 类型失败、控制帧多派发、旧 501 信封、原创建 / 删除状态、新 clone 参数及请求版本号失败。clone 重复号负控仅临时撤销唯一性 guard，观察失败后恢复，通过最终聚焦验证。对应日志均在本目录，未删除失败记录。

本专项未使用 computer use，未向正常业务数据库写角色 / 用户 / 项目数据；ASGI 用新临时 app 与 service double，mock 写入仅发生在测试独立的 fake IndexedDB 中。没有提交、发布、重启开发服务或关闭 ESLint / 类型规则。

本审查范围固定为本次清 lint 的 HTTP 数据路径与上述必要根源修复；没有把所有历史未加入离线主线的 API、未变更仿真 legacy helper 或完整 SSE grammar fuzz / 并发 clone 事务保证列为已完成验收。registry 的明确 unsupported / missing / schema-unavailable 项仍是可见能力边界；不声称所有 mock 都完整模拟后台。库视觉和普通业务组件由另两名独立审查代理负责，整体最终验证由根代理执行。

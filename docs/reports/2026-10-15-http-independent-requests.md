# HTTP 第一轮优化：请求独立与参数契约收敛

日期：2026-10-15。已实施并完成本轮验证，未提交 Git、未发布 npm。

## 结果与收益

ZXUI HTTP 现在每次调用独立发送、独立返回，不再根据 URL/参数指纹取消其他调用，也不在传输层共享结果。调用方通过 Axios 原生 `config.signal` 管理自己拥有的请求；普通请求保留原始 signal，显式并发插件仍保留队列和取消能力。

参数统一采用 Axios 契约：`params` 负责 query，`data` 负责 body，同名字段互不覆盖，JSON null 不再被清理。删除 `parameterMode` 和 legacy 分支，当前业务无需模式开关。

长期收益是去掉传输层对“相同业务操作”的错误推断，避免不同服务、租户、响应格式或返回契约之间相互影响；同时减少配置组合、全局登记和失效清理逻辑。代价是旧接口硬切，真实需要跨组件共享的读取必须在应用查询层明确 key、缓存和失效规则。本轮没有新增查询框架或自建替代机制。

## 责任与迁移

通用机制修在 ZXUI `packages/http`：

- 删除指纹取消登记、自动结果去重及其实现、测试和旧示例。
- 删除配置 `deduplication`、`deduplicate`、`ignoreCancelToken`、`parameterMode`。
- 删除公开导出 `AxiosCanceler`、`getPendingKey`、`DedupManager`、`createDedupManager`、`defaultKeyGenerator`、`describeRequestPayload`、`normalizeParams`、`createUrlSearchParams`、`isFormData`、`isNil`。`joinTimestamp` 不再支持旧的 restful 字符串分支。
- 并发插件的 signal 连接辅助函数迁到内部 `abort.ts`；保留既有取消原因与监听释放逻辑。
- 保留显式 `joinTime`、`joinParamsToUrl`；URLSearchParams 加时间戳或 token 前复制实例，自定义 serializer 仍生效。
- 更新 README、中英文组件/指南、取消示例及 HTTP 类型和示例元数据。

业务仅移除旧配置/fixture，切换到匹配的本地包 `vendor/zxio-http-1.0.0-independent.20261015.tgz` 并更新锁文件；Axios 保持 1.20.0。源码直连与安装包两种交付均已验证。包内 50 个文件与安装目录逐一一致，构建产物与归档一致，旧 canceler/dedup 产物已消失。完整校验见 [交付包证据](evidence/2026-10-15-http-independent-requests/package-integrity.json)。

已检索库、文档、示例、独立包和业务消费者，未发现额外生产调用需要迁移。业务字典缓存保留。

## 验证结果

| 验证 | 结果 |
| --- | --- |
| 改实现前的新契约回归 | 16 项预期失败，确认可复现隐式取消和旧参数行为 |
| ZXUI HTTP 全部用例 | 7 文件、80 项通过 |
| GridList 请求生命周期既有回归 | 12 项通过 |
| 示例生成器既有回归 | 6 项通过 |
| 业务 API/utils/登录/ListQueryContract，源码直连 | 19 文件、94 项通过 |
| 同一业务范围，安装包模式 | 19 文件、94 项通过 |
| HTTP 构建、受影响用例严格类型、定向 ESLint | 通过 |
| 业务 lint、type-check、变更文件规范 | 通过 |
| 业务生产构建，源码直连/安装包 | 均通过，18.78 秒 / 17.32 秒 |
| 新取消示例 script/template 编译 | 通过 |
| 两个仓库 `git diff --check` | 通过 |
| 独立只读审查 | 无本轮阻塞项；另行复跑 HTTP 80 项、GridList 12 项并比对安装包 |

HTTP 用例数下降包含被删除功能的旧测试退役，没有为调试新增大量测试文件。新增独立请求回归放在既有 `client.test.ts`；原取消登记用例替换为内部 signal 连接的 3 项必要检查。

真实验证通过实际业务 API、请求封装、Axios 1.20.0 和 JSDOM XMLHttpRequest 访问本地真实 FastAPI。源码和安装包各 **15 项通过**，包括：

1. 登录、鉴权信息和真实用户查询。
2. 两个完全相同的用户查询各发出一次请求且都完成。
3. 相同 URL 的 JSON/Blob，以及原生响应/最终解包，分别保持各自返回契约。
4. 业务上传入口和库 `upload` 均完成 multipart 协议文件预览，服务端成功解析，不创建协议记录。
5. 两个相同真实查询中仅取消第一个：原始 signal 和 reason 身份保留，第二个完成，无取消错误提示。
6. 真实查询响应倒序返回：使用实际 GridList 请求/状态实现，最新列表、分页、loading 和 error 保持正确，过期响应不发 `dataLoaded`。
7. 用户 Excel 经业务下载入口成功，query/body 冲突不会互相覆盖，URLSearchParams 重复键和空值保持；loading 各关闭一次。
8. 导出 JSON null、自定义 query serializer、422 二进制错误透传及服务后续响应正常。

两份用户 Excel 均由 openpyxl 解析：1 个工作表、2 行、13 列，包含预期用户。原始 Excel/Word 临时文件已删除，只留脱敏检查结果。完整结果见 [源码直连](evidence/2026-10-15-http-independent-requests/source-actual.json)、[安装包](evidence/2026-10-15-http-independent-requests/installed-actual.json) 和 [Excel 检查](evidence/2026-10-15-http-independent-requests/xlsx-inspection.json)。

## 证据边界与剩余范围

真实接口验证使用了真实服务和数据；反馈、loading、保存文件的 UI 入口由探针记录。取消/倒序完成由本地转发网关暂存真实后端响应控制时序，没有伪造响应内容。未使用 computer use，未做浏览器点击或视觉验收。跨服务、跨租户情形由适配器回归验证，没有构造额外业务服务。

GridList 的 generation 保护覆盖组件内部列表、分页、错误与 loading。业务 `loadUserData` 在 await 后写 `currentQuery` 的外部副作用不受组件保护；不同查询原本就存在这一边界，本轮没有修改该业务流程，也没有声称已验证所有页面副作用。

下一轮仍是业务重复提交治理：移除全局一秒时间指纹，按真实写入口的操作生命周期管理 pending。请求准备阶段的统一错误处理随后单独实施。本轮没有修改这两项，也没有混入 retry/logger、查询缓存、其他 UI 或后端优化；前一轮参数兼容的审计日志改动仍保留。业务记录未增删改；登录会话、导出审计等正常运行记录不在此断言内。

生成器在临时隔离目录执行，仅同步 HTTP 文件与聚合索引的 HTTP 条目，已检查非 HTTP 条目不变。被忽略的生成输出保留校验值及 HTTP 快照，见 [元数据证据](evidence/2026-10-15-http-independent-requests/metadata.json)。构建仅出现现有 chunk 大小、peer 依赖和私有源环境占位符提示，没有构建错误。

验证命令与计数汇总见 [checks.json](evidence/2026-10-15-http-independent-requests/checks.json)。本轮启动的后端及其子进程已停止，未停止其他已有服务。

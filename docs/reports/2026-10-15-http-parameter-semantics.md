# HTTP 参数语义收敛验证

本轮已完成：ZXUI 增加兼容模式，业务明确采用 query/body 分离语义；URLSearchParams 重复键、空值和 JSON null 保留。源码直连与最终安装包各通过 9 项真实请求检查，用户 Excel 与版本 Word 导出正常。没有混入其他 HTTP 优化，未自动提交或发布 npm。

## 先查后改的结论

检查了业务通过 request/http 导入识别出的 210 个调用，其中 43 个包含 params、8 个是非 GET params 调用。另行核对后端参数声明、调用消费者及 joinTime/joinParamsToUrl 使用情况。完整分类见 [inventory.json](evidence/2026-10-15-http-parameter-semantics/inventory.json)。

| 调用 | 后端契约与迁移判断 |
| --- | --- |
| PUT `/system/user/authRole` | userId、roleIds 为 Query；不需要隐式 JSON body |
| PUT `/system/role/authUser/cancelAll`、`selectAll` | roleId、userIds 为 Query；不需要隐式 JSON body |
| POST `/tool/gen/importTable`、`createTable` | tables/sql 为 Query；不需要隐式 JSON body |
| DELETE `/simulation/faults/:id` | sessionId 为 Query；仅检查源码，不改动或验收仿真 UI |
| POST `/device/export`、`/device/category/export` | 两个未使用的 helper，未找到对应后端路由；保持原样，不声称已验证接口 |

没有发现生产调用依赖字符串 params 自动拼路径，也没有生产调用启用 joinParamsToUrl/joinTime。登录与协议导出已有 URLSearchParams 表单体，需要继续保留表单编码。

另发现业务操作日志只读取 body/path，过去依赖库把 Query 复制进 body 才记录到这些参数。迁移时一并做最小兼容修复：日志从 Query 初始化，再由现有 form/body/path 覆盖；保留原有字符串/JSON 输出形式、身份获取及入库流程。Query 本身为字符串，未引入新的日志体系或后端 API 变更。

## 库与业务各自修改

ZXUI 的通用问题在 `packages/http` 修复：

- 新增一个公开选项 `requestOptions.parameterMode: 'legacy' | 'axios'`。默认 legacy，兼容未知消费者；客户端、请求配置和第二参数可按既有优先级覆盖。
- Axios 模式中 params 只负责 query、data 只负责 body，同名字段互不覆盖；核心不删除 JSON null，不再把字符串 params 解释为路径。
- URLSearchParams 查询和表单体保留重复键及空字符串；GET 时间戳和内建 query token 注入先复制实例，不修改调用者。
- 显式 joinParamsToUrl 在 token 注入后经 Axios serializer 拼接 query，保留自定义 paramsSerializer/baseURL，且消费一次；body 不进入 URL。
- README 记录默认兼容行为及迁移方式。分页插件与自定义 hook 仍按自身契约加工请求。

业务前端只增加全局 `parameterMode: 'axios'`，已有 5 个授权/生成器 API 在原测试文件增加实际请求契约验证；没有逐个改写 API。后端日志兼容只改动现有两条参数读取分支，并增加一个针对装饰器的测试文件。Axios 仍为已对齐的 1.20.0。

本地交付包为 `vendor/zxio-http-1.0.0-parameters.20261015.tgz`，已更新 package.json/yarn.lock。49 个源码构建载荷文件与压缩包、node_modules 逐字节一致；package.json 语义一致，仅 pnpm pack 去掉末尾换行。包不包含源码目录。校验值见 [package-verification.json](evidence/2026-10-15-http-parameter-semantics/package-verification.json)。

## 真实业务验证

通过真实业务 TypeScript 模块、Axios 1.20.0 和 JSDOM XMLHttpRequest 访问本机真实 FastAPI :8088。反馈、loading 和文件保存入口作记录桩；未使用浏览器点击或 computer use。源码模式加载 `packages/http/src/index.ts`，安装包模式加载 node_modules。

| 检查 | 源码与安装包结果 |
| --- | --- |
| 真实登录、获取当前用户 | 通过，已有 URLSearchParams 登录表单兼容 |
| 现有 listUser API 的普通 query | 200，返回预期筛选记录 |
| URLSearchParams query 重复键、空值、GET 时间戳 | 200，重复键与空值保留，调用方实例不变 |
| 用户 Excel：有效 form body + 同名无效 query | 200，表单值不再被 query 覆盖 |
| 用户 Excel：URLSearchParams body 与 query 都有重复键 | 200，各自重复键与空值保留，输入实例不变 |
| 现有版本 Word API：imageBase64 显式 null | 200，实际 XHR JSON body 包含 null，文档为现有 HTML `.doc` 格式 |
| Word 请求：显式拼 query + 自定义 serializer | 200，serializer 调用一次，原有 query 保留，body/null 独立 |
| 用户 Excel：无效 form body + 同名有效 query | 422，query 不能覆盖 body 校验；原始 Blob 保留、反馈一次、loading 关闭 |
| 导出后服务与鉴权查询 | 持续正常响应 |

两条链路保存的真实用户 Excel 均用 openpyxl 检查：1 张表、含表头 2 行、13 列，包含预期登录账户记录。成功导出没有失败反馈，loading 正常关闭。仅保存脱敏检查结果，原始业务文件已从临时验证产物移除。没有修改角色授权、执行建表 SQL 或用真实用户编辑来验证清空字段；null 结论限定为传输保留及现有导出接口接受，不扩大为所有业务字段的清空语义。

实际请求与文件结果见 [source-actual.json](evidence/2026-10-15-http-parameter-semantics/source-actual.json)、[installed-actual.json](evidence/2026-10-15-http-parameter-semantics/installed-actual.json)、[source-workbook.json](evidence/2026-10-15-http-parameter-semantics/source-workbook.json)、[installed-workbook.json](evidence/2026-10-15-http-parameter-semantics/installed-workbook.json)。

## 回归、审查与限制

先观察失败再修复：库参数契约 8 项失败，业务配置与 Query-only 写请求 6 项失败，日志兼容 2 项失败。审查补充的边界另观察到 2 项失败，均已修复。测试集中补在既有 HTTP/API 文件；后端只新增必要的日志兼容测试。

| 验证 | 最终结果 |
| --- | --- |
| ZXUI HTTP 全库 | 8 个文件、88 项通过 |
| 业务 API/utils/用户登录回归 | 源码与安装包各 18 个文件、90 项通过 |
| 日志兼容及两个请求体回放中间件 | 18 项通过 |
| ZXUI 目标 ESLint、测试严格类型检查、HTTP 构建 | 通过 |
| 业务 lint:check、type-check、前端变更规范检查 | 通过 |
| VITE_ZXUI_LOCAL=true/false 两次生产构建 | 通过，分别 19.16s / 19.69s |
| 后端新增测试 Ruff、两个变更文件格式检查 | 通过 |
| 两个仓库 git diff --check | 通过 |

后端变更规范检查的 Ruff 阶段未通过：`log_annotation.py` 原有 35 项问题仍存在，本轮前后规则数量相同，没有新增规则类别或数量；未混入旧文件清理。格式和其余规范 guardrails 通过。后端测试有既有 Pydantic regex 弃用警告，安装和构建也有既有 peer/Browserslist/包体积提示。详情见 [verification.json](evidence/2026-10-15-http-parameter-semantics/verification.json) 和 [audit-ruff-comparison.json](evidence/2026-10-15-http-parameter-semantics/audit-ruff-comparison.json)。

只读审查发现并关闭一个 P2：query 拼接早于 query token 注入时，会重复添加默认参数。最终复查没有本轮范围阻塞项，审查者独立复跑 88 项通过。见 [review.md](evidence/2026-10-15-http-parameter-semantics/review.md)。

验证后仅停止本轮启动的后端，8088 已无监听；现有 MySQL/Redis 保留。本轮不改防重复提交策略、重试、去重键、请求前异常管线或 HTTP 日志。未做 npm 发布、Git 提交、推送；两仓库原有其他工作区变更保留。

## 计划阶段检查点

本轮采用 [实施计划](../plans/2026-10-15-http-parameter-semantics.md)。输入完整、范围收敛；检查了真实调用依赖后选择默认 legacy、业务显式迁移，日志兼容作为避免业务回归的必要改动纳入。三个任务均已完成，验证证据如上，未附着独立工作项。

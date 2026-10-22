# 后端 API 与生成契约验证

验证日期：2026-10-22。执行目录为项目本地 `.worktrees/generic-remark-rich-text`。本记录覆盖后端对象、API、关联响应、缓存、Excel 及生成产物；数据库转换流程的演练见单独报告，浏览器业务验收不由本记录替代。

## 结果与证据类型

| 验证 | 结果 | 证据边界 |
| --- | --- | --- |
| 相关 Python 完整测试组 | 496 passed，退出码 0 | 单元测试、真实 ASGI HTTP/DI/仓储链路，隔离 SQLite；含审查后补充回归 |
| 其中共享 common 测试 | 159 passed | 协议、Pydantic、派生值、Excel 工具及 OpenAPI |
| 其中备注 HTTP 集成 | 22 passed | 原有 9 项、6 项错误码/事务与只读错误、3 项生成器列表、4 项日志安全 HTTP；另有 1 项非分页服务验证 |
| 其中 OpenAPI 结构 | 34 passed | 当前 FastAPI 应用生成的 schema |
| 七个生产 ORM 映射的 MySQL CRUD | 1 passed，循环覆盖 7 表 | 本机 Docker MySQL，自动创建并删除独立数据库；未修改日常业务库 |
| 生成客户端与 Mock API 契约 | 3 文件、25 passed | Vitest；不属于浏览器真实页面验收 |
| OpenAPI drift | 通过 | 当前应用与仓库 artifact 一致 |
| 客户端再次生成 | 17 个文件、0 文件漂移 | OpenAPI + 16 个生成 TS 文件 SHA-256 比较 |
| 实际生成控制器的公开响应契约 | 8 passed | 真正生成 VO 与控制器后构建 FastAPI OpenAPI，并验证 response adapter |
| 备注日志安全专项 | 14 passed | 真实成功/失败操作审计持久化、异常响应与日志、三类事务、任意字段文档和派生值、异常组及普通诊断 |
| 本子任务 22 个代码文件 Ruff | check/format 均通过 | 新代码及涉及的 VO、契约和回归测试 |

机器可读摘要见 [backend-api-evidence.json](backend-api-evidence.json)。最新完整日志：`/tmp/remark-backend-privacy-final-tests.log`（496 项、退出码 0）。此前记录：`/tmp/remark-backend-api-review-final-tests.log`（465 项）、`/tmp/remark-errors-final.log`（错误码与 RFC9457 22 项）、`/tmp/remark-backend-mysql-crud.log`、`/tmp/remark-api-client-contract-tests.log`、`/tmp/remark-openapi-privacy-check.log`、`/tmp/remark-generated-drift.json`。

## 日志与审计的正文保护

安全回归使用通过正式 DTO 接纳的有效备注，以及在真实 API 仓储边界注入的 `StatementError`，其 SQL 参数和驱动错误消息均含固定正文 sentinel。初始 7 项回归全部复现泄漏；修复后，最终 14 项专项及旧有日志、事务、失败登录审计回归一起通过。

- 新增小型 `utils/log_safety.py`，复用 SQLAlchemy 已有异常类型及现有审计敏感字段 registry。数据库异常、因果链或异常组仅输出异常类型及驱动提供的整数错误码，SQL、params、驱动消息及异常 traceback repr 不写日志。普通非数据库异常保持既有堆栈诊断。
- 事务的新建、嵌套、加入分支，操作日志装饰器、全局异常处理，以及真实请求经过的 CQRS 命令/查询失败分支均消费同一安全诊断；保留事件类型、操作人、request/trace ID 等既有定位信息。
- 操作审计在请求参数和响应结果序列化前递归处理文档，保留记录身份和普通业务值。`remark`/`remarkText` 及 snake alias 使用占位；任意生成字段名的完整 v2 envelope、body、裸 doc 树、JSON 编码表单值也按结构识别，同时处理相邻派生 Text 字段。正常 API 返回的权威文档不受影响。
- 原有数据库变更审计同样接入保护，`sys_role` before/after 不再把文档 stringify 成完整正文。既有敏感字段配置继续生效。2,000 字审计长度处理仍保留，其用途是容量限制；正文保护在该限制之前完成。
- 两项 HTTP 测试通过实际独立 SQLite session 持久化成功/失败操作审计，确认失败审计在业务回滚后存在，且 `oper_param`、`json_result`、`error_msg` 均不含正文；成功响应仍返回完整文档。另核对通用异常处理和 CQRS 查询路径不会在日志或错误响应中输出正文。

方案核对了 SQLAlchemy 的 [StatementError 公开语义](https://docs.sqlalchemy.org/en/20/core/exceptions.html#sqlalchemy.exc.StatementError) 和 [hide_parameters](https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.hide_parameters)。仅配置隐藏绑定参数不能覆盖手动构造的异常、驱动消息以及审计请求/响应内容；此处在实际日志和审计边界保留安全诊断。该结论由本轮含 sentinel 的真实 HTTP/日志回归验证。

## 独立审查后的边界收敛

- 错误码：codec 的 `RemarkError` 增加纯结构化 `code/path`，保留原安全字符串及 ValueError 类型以供迁移使用。VO 边界将其转换为 `PydanticCustomError`，公开 `remark_version`、`remark_structure`、`remark_link`、`remark_budget`；只读派生输入使用 `remark_readonly`。详细 reason/path 在错误 context 中，不携带正文，并通过 Pydantic loc 交给既有 ProblemDetails；没有全局解析异常文本。
- 字段路径：全局请求错误处理只剥除 transport 的首段 `body`，保留文档中实际的 `remark.body`。6 项真实 HTTP 回归验证各类 code、完整路径、拒绝后其他字段及原文未变化，以及 camel/snake 两种只读派生输入均定位到 `remarkText`。最初的错误码测试 4 项全部失败，修复后通过；只读路径测试也完成红绿验证。
- 现有生成器列表：`get_gen_table_list_services` 返回类型化读取投影，而不是直接把仓储字典装入 JSONResponse。分页与非分页都在响应前验证文档、计算摘要；真实 HTTP 验证嵌套列表文字、损坏对象/旧字符串拒绝和原数据保留，另用真实仓储验证非分页路径。4 项回归先全部失败，修复后通过。
- 生成模板：remark 分支的详情、新建、更新响应公开 ReadModel，新建状态显式为 201；普通和主子表列表公开 typed page items，树表使用现有 CollectionResult。8 项测试实际生成 VO/控制器模块再调用 FastAPI.openapi，覆盖普通、树形、主子表、仅子表采用备注的情况，确认任意字段名派生 Text 的 readOnly、列表 items 类型、主子投影保留及写入拒绝伪造字段。测试中的服务只有导入占位符，不把该 schema 探针称为生成控制器真实 HTTP CRUD 验收。

共享 HTTP 测试夹具已放到 `tests/integration/conftest.py`，避免从测试模块加载 plugin 时依赖收集顺序。审查修复没有改变业务字段类型；现有 OpenAPI artifact 再次执行 `--check` 通过，无需再次生成客户端。

## 已核对的行为

### 七个字段的持久化与写入边界

`sys_user`、`sys_role`、`sys_post`、`sys_dict_type`、`sys_dict_data`、`sys_config`、`gen_table` 的生产 DO 均映射为 nullable `JSON(none_as_null=True)`。真实 MySQL 测试对每个映射保存完整对象，核对 `JSON_TYPE(remark)='OBJECT'`，修改其他字段后重读确认备注保留，整份文档替换后重新加载确认 ORM 跟踪成功，最后确认明确清空得到 SQL NULL。

HTTP 测试通过真实控制器、Mediator、服务与仓储验证六个系统入口：创建、详情重读、遗漏备注的更新、非法旧字符串拒绝、伪造 `remarkText` 拒绝、拒绝后的原文保留、显式清空与重读。用户和角色另外核对专用状态更新不重写备注。生成器配置通过真实保存入口验证完整文档、派生值、遗漏保留、只读字段拒绝和清空；保留根代理对参数遗漏保持 options 的修复。

现有用户/角色写入、关系授权、事务失败和详情读取测试一起执行，验证备注改造仍走既有白名单、鉴权与事务路径。HTTP 集成使用受控当前用户依赖替身，不宣称覆盖真实登录会话与完整 JWT 链路。

### 读取与关联响应

公共读取模型使用同一个 `RemarkReadProjection`。服务端从权威 JSON 重算 `remarkText`，输入中伪造的摘要不作为内容源。OpenAPI 将该字段标为 readOnly 且读取响应中必需。

审计补齐了身份接口的遗漏：原来的 `CurrentUserModel.user.role` 使用写入 `RoleModel`，会缺少派生文字。新增 VO 层 `RoleInfoModel`、`PostInfoModel` 读取投影，`UserInfoModel.role` 与 `UserDetailModel` 的角色/岗位选项共同采用读取投影，避免 VO 层反向依赖 application 层。先失败的回归测试复现缺少 `remarkText`，修复后通过。

新增真实 HTTP 测试创建带文档的角色、岗位及关联用户，再读取用户详情，核对用户关联角色及角色、岗位选项的文档和派生文字；另通过 `/getInfo` 核对身份响应嵌套角色的序列化以及忽略伪造派生输入。系统 CQRS 读取模型继续保留自己的明确响应职责。

### 缓存与 Excel

字典缓存以类型键为边界。损坏 JSON、旧字符串备注或非法文档触发该键删除并从权威记录重建，重新写入完整文档与派生文字；没有全量删除其他类型键。当前格式缓存命中直接经读取模型校验，旧的无格式标记测试夹具已显式迁移，没有加入运行时字符串兜底。

六个业务导出服务均从已验证文档派生文字，明确指定备注列为 Excel 文字列。新增测试读取真实 XLSX，核对段落、空行、中文/表情、嵌套列表编号和缩进，确认 `=1+1` 单元格类型为文字，无额外可见前缀。伪造 `remarkText` 不影响导出，投影也不覆盖调用者记录中的权威文档。旧 config 导出夹具中的字符串已改为显式构造文档或 null。

## OpenAPI 与客户端

已重新导出 `shared/openapi.json`，SHA-256：

```text
69cce0ed724fb7ce9a3d9d2d7861b511617d90af3aa7c0c14782b65efbc7ffcc
```

34 项结构测试核对：9 个写入模型显式引用 nullable `RemarkDocument-Input` 且没有摘要写入权威；13 个公开读取投影引用 `RemarkDocument-Output` 并公开只读派生字段；7 个 GET 查询不展开递归备注；文档外壳字段精确、资源 maxItems=0；4 个专用用户/角色写入模型拒绝额外字段且不包含备注。

使用仓库锁定的生成器执行 `scripts/generate-api-types.sh --artifact`，并再次执行后逐文件比较 SHA-256，17 个产物没有变化。相关生成客户端和 Mock schema 测试通过。该结果不替代整个前端 type-check/build，后者由前端验收记录说明。

## 可复现命令

在 `ruoyi-fastapi-backend` 中运行完整相关组：

```bash
./venv/bin/python -m pytest \
  tests/unit/common/ \
  tests/integration/test_remark_http_contract.py \
  tests/integration/test_remark_http_errors.py \
  tests/integration/test_remark_generator_list.py \
  tests/unit/module_generator/test_remark_generated_openapi.py \
  tests/integration/test_error_handling_rfc7807.py \
  tests/unit/services/test_remark_exports.py \
  tests/unit/services/test_dict_service.py \
  tests/unit/services/test_config_service.py \
  tests/unit/controllers/test_user_role_write_contract.py \
  tests/unit/controllers/test_role_write_http.py \
  tests/unit/services/test_user_service.py \
  tests/unit/services/test_user_role_authorization_writes.py \
  tests/unit/services/test_role_write_relations.py \
  tests/unit/services/test_remark_cache.py \
  tests/unit/services/test_dict_data_export.py \
  tests/unit/services/test_role_user_read_contract.py \
  tests/unit/services/test_detail_resource_contract.py \
  tests/unit/services/test_uncached_detail_contract.py \
  tests/integration/test_system_cqrs_cutover.py \
  tests/unit/scripts/test_export_openapi.py \
  tests/unit/test_collection_openapi_contract.py \
  tests/integration/test_remark_log_privacy.py \
  tests/unit/utils/test_remark_log_privacy.py \
  tests/unit/test_log_annotation.py \
  tests/integration/test_failed_login_log_persistence.py \
  tests/unit/utils/test_transaction_manager.py \
  -n 0 --no-cov --tb=short --no-showlocals

RUN_REMARK_MYSQL=1 ./venv/bin/python -m pytest \
  tests/integration/test_remark_mysql_crud.py -n 0 --no-cov --tb=short

./venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json
./venv/bin/python scripts/export_openapi.py --check --output ../shared/openapi.json
```

项目根目录执行 `bash scripts/generate-api-types.sh --artifact`。前端目录执行：

```bash
./node_modules/.bin/vitest run \
  src/api/_generated-client-contract.test.ts \
  src/mocks/handlers/api-contract.test.ts \
  src/mocks/handlers/api-contract-schema.test.ts --reporter=dot
```

Ruff 检查的 22 个负责文件通过。旧 `test_config_service.py` 当前 65 项/HEAD 66 项，`gen_service.py` 当前 8 项/HEAD 17 项；安全修复涉及的旧文件：`exceptions/handle.py` 当前 37 项/HEAD 38 项、`transaction_manager.py` 45/46、`log_annotation.py` 14/15、`audit_logger.py` 21/22。没有新增 lint 规则；异常处理函数的既有 PLR0915 数字从 56 减到 54，消息文字随改善变化。不能据此声明整个仓库 Ruff 全绿。早期对照结果保留在 `/tmp/remark-api-ruff-new.json`。

安全修复后再次导出 OpenAPI 并执行 `--check`，退出码均为 0，SHA-256 保持上文值；公开字段类型没有变化。

## 未验证项目

- 未使用 computer use；没有把 HTTP/组件测试称为七个页面的真实界面保存、重开、清空、焦点或输入法验收。
- 没有对生产库迁移，也没有将隔离 MySQL ORM CRUD 当作数据库升级演练的全部证据。
- 本子任务没有运行真实 PostgreSQL、真实登录会话或完整前端构建；这些必须按总验收中的实际证据标注。

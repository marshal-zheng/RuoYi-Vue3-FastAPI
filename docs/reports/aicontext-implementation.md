# AI 可关闭与局域网模型：实施记录

2026-10-27，隔离工作分支 `codex/aicontext-implementation`。尚未交付回源分支，七宿主与冻结协议已接入，必需实现验收、两轮独立审查及三仓完成证明已通过，待交付。规格锚点：ZXUI 仓 `docs/specs/AICONTEXT-text-field-ai-contract/`；本文件不另立要求。

## 后端阶段

- `AI_ENABLED=false` 为默认值，没有默认公网 URL/模型，不继承通用 `OPENAI_*` 密钥或地址。普通应用导入和 remark codec 在禁止 DNS/socket、拦截所有可选 SDK 导入的子进程中通过。
- 显式选择 `openai-compatible` 协议只决定传输适配，不要求 OpenAI 账号。无认证局域网端点通过每请求公开 `extra_headers` 的 `omit` 省略 Authorization；API key 只由 `AI_AUTH_MODE=bearer` / `AI_API_KEY` 提供。SDK 重试 0、禁重定向、禁环境代理、总超时与分项超时均显式设置。实际请求由 httpx2 MockTransport 捕获；当前产品 adapter 也经只允许指定 127.0.0.1 端口、禁止 DNS 的真实 HTTP 验证，恰好一次连接/请求且正常关闭客户端，不代表真实模型质量已验收。
- 已替换旧场景端点、手写上游 HTTP/SSE 和 DeepSeek 默认配置。复用 IAM any-of、共享 Bulkhead、现有频率计数、OperationLogService 独立短会话、remark codec 与现有 Prometheus registry。
- SDK/SSE 可选依赖锁在 `ruoyi-fastapi-backend/requirements-ai.txt`：openai 3.37.0 / httpx2 2.16.0 / sse-starlette 3.0.3，框架 FastAPI 0.115.8 / Starlette 0.45.3 / AnyIO 4.10.0 / Pydantic 2.11.7，Python 3.13.12。主 requirements 将 SQLAlchemy 声明对齐到前置解析通过的 2.0.48，未安装到原工作区。
- sse-starlette 3.0.3 的发送时限只覆盖 data 帧，且 DEBUG 会打印原帧。局部 ASGI 包装把时限覆盖到心跳/start/end，并禁用库的内容日志；保留成熟 SSE 编码、心跳与任务管理。慢客户端和断连均关闭 SDK/释放整流许可，审计在 ASGI 终结且每次只尝试一次。
- 公开 request/status、有限 HTTP ProblemDetails、delta/result/error union 已登记 OpenAPI，再用既有生成器输出 TypeScript，未手改 generated。扩展入口采用 [FastAPI 官方 OpenAPI 扩展机制](https://fastapi.tiangolo.com/how-to/extending-openapi/)，Pydantic 生成联合类型和引用。

验证命令（业务 worktree 的 `ruoyi-fastapi-backend`）：隔离 `backend-env/bin/python -m pytest tests/unit/services/test_text_field_ai.py tests/unit/services/test_text_field_ai_http.py tests/unit/services/test_text_field_ai_document.py tests/unit/services/test_ai_context_contract.py -q -n 0 --no-cov`，106 项通过。新模块 Ruff check/format 通过；修改的共享旧文件存在原有 Ruff 债务，增量检查记录在 worktree Git metadata。覆盖无 stop、length、stop 后异常、JSON/codec/token 失败、notice-only、307/308/401/429 单次请求、无认证请求、权限/策略/VO、用户/IP 限流、两慢流/饱和、GZip 心跳、慢发送、取消/超时、审计失败，以及 HTTP/SSE/日志哨兵检查。

## 前端阶段

七宿主接入同一静态定义与 runtime scope；真实用户弹窗的三轮联系方式 A/B、采用/撤销/重开，以及真实岗位 Formily 字段接线均通过源码模式的实际 HTTP payload 检查。原生表单回归发现并修复编辑器目标失效后被表单时钟误恢复为改写基准的问题，修复位于独立 text-editor 分支 `c576152`，21 项字段回归通过。源码完整 7 组 110 项通过（含业务/状态 14 项、HTTP/SSE 25 项、共享契约 37 项、生成器 2 项及原有 remark 往返/Formily 回归）。新 adapter 在合法终态后正常 EOF 才 resolve，ID/重复终态/后续事件均拒绝；状态失效仅重新读取策略，不重放请求。

`tsconfig.ai-context.json` 覆盖七宿主、新 adapter、根状态与相关测试，类型检查通过。执行环境只读复用主工作区的已装依赖，私有声明投影复用未改的公开 UI 声明，并将新 AI 叶子和本轮 editor/schema-form 产物指向 worktree；实际 DOM 回归由 Vite 源码插件加载完整当前实现。没有修改主工作区安装环境。整个旧测试目录的全量 typecheck 含既有非本轮错误，不能将聚焦检查表述为全仓已通过。

生成器复用现有 TypeScript 编译器加载纯静态导出，兼容仓库 CI Node 20，不增加 Vue AST 编译器或依赖。SSE 类型模板补充了已有生成 SDK 所传入的 error 泛型，再运行既有 API 类型生成器。

## 共享契约与隐私边界

`shared/ai-context/contract.json` 已冻结 ai-context/v1。独立 JSONschema 检查 37 组（无 DNS/socket），Python 实际 Pydantic/文法消费 24 组共享向量，TS 实际 codec/HTTP/SSE 消费 37 项；生成器 2 项覆盖声明源漂移和 secret 用途引用。生成检查、聚焦 TypeScript、ESLint 通过。现有 GitLab/GitHub 前端质量通道已接入清单反漂移命令。

后端 token/有限错误定义位于 `common/ai_context.py`，DTO 不再反向依赖 application service。供应商数据省略传输 UUID/修订指纹，只保留用途和非敏感可提示 item id。真实回环验证发现 SDK/httpcore DEBUG 泄露响应头，已在 SDK 客户端/HTTP transport 完成导入后安装上下文过滤；AI 请求的 OTel 与 SDK/HTTP 内容日志被禁止，普通并发 HTTP 诊断保持可用。

部署与离线可选依赖见 [部署指南](../../ruoyi-fastapi-backend/docs/text-field-ai-deployment.md)，公开内核/编辑器/Formily 接线见 ZXUI 文档。隐私保护针对实例已获准读取的已知个人值，不保证自动识别任意自然语言中未知个人信息。浏览器和真实模型未执行；尚未交付回源分支或切换开发服务。

## 本地安装与构建验收

ZXUI 聚合构建、owner editor/schema-form 构建与公开契约检查通过。业务使用本轮三个正常构建 tarball，package.json 和 Yarn 锁文件已更新，Element Plus 对齐库声明的 2.14.7；没有发布 npm。主工作区安装不动。隔离 worktree 在 APFS 写时复制的私有依赖上执行 `yarn install --immutable` 成功，原生安装脚本正常执行；其后实际包模式 7 组 110 项和 `yarn type-check:ai-context` 通过。此前只读链接投影出现两份 Vue，已通过真实安装解决，没有引入测试配置兼容补丁。

源码生产构建、三个实际 tarball 的生产构建通过。ZXUI 文档站及 select/dialog/list-view 三路交付预算通过。这里是本 spec 的包消费验证，不宣称此前 29 包全量发布准入重新通过。

D16 保证边界增加了未知历史号码仍可作为原文保留的回归，明确不做任意 PII 识别；三条合成指令使用固定 SDK 合成返回，验证 notice-only envelope 与正文分离，不宣称真实模型遵循指令或禁止编造的质量已证实。一次 CPU 竞争下 0.1 秒测试超时先于流就绪，串行重跑原命令 106 项通过；生产超时未放宽。

## 独立审查修复

Round 1 指出两项 P1：测试 SDK/CI 通道不闭合，以及公开编辑器在脱敏后遗漏文档 wire codec gate。F1 已将 `requirements-ai.txt` 和共享 schema checker 的开发依赖纳入 `requirements-dev.txt`，主 GitLab architecture-regression-tests 增加四个 AI/共享契约文件和 schema checker，GitHub 全测试亦运行共享 checker；生产基础 requirements 未加入可选 SDK。base+dev 依赖 dry-run 解析、CI YAML 解析通过；同一隔离 backend-env 已具有对应依赖，106 项收集/执行和 37 项 checker 通过。未触发远程 CI。

F2 位于独立 editor 提交 `3289f83`：capture/mask 后对 document/selection/candidate 逐一复用 `validateBasicRichTextDocument(value, options.limits())`，在任何 adapter 之前拒绝扩张超限。默认5000字符、自定义800字符的两项零调用回归验证原文和表单未变；owner 4 文件共53项、types/build/实际非忽略 lint 通过。更新 editor tarball 为 `aicontext.20261027.2`，删除本轮被替换的旧候选，实际 immutable 安装、业务110项及聚焦类型检查再次通过。

最终 Round 2 为 independent-subagent PASS，48条需求/31条设计/39条任务全覆盖，无未解决 P0/P1/P2；三仓 final-review-proof 和 claim-proof 均通过（仅 implementation-complete-awaiting-delivery）。本次状态更新不改变已审查的义务或实现。源环境基线验证待用户验证并请求交付后执行；浏览器/真实模型未执行。

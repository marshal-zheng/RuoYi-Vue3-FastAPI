# 可选文本字段 AI 部署

字段 AI 默认关闭，普通表单和备注编辑无需模型服务、模型密钥或可选 SDK。不需要 OpenAI 账号、公网地址或 OpenAI 模型。启用时只访问部署方显式配置的端点；没有默认地址、模型、重试、重定向或公网回退。

## 启用与局域网服务

基础应用按原 requirements 安装。仅需启用此能力时，在制品准备环境安装或准备这些可选依赖：

```sh
pip install -r requirements.txt -r requirements-ai.txt
```

运行环境可以使用事先准备的离线 wheelhouse：`pip install --no-index --find-links=/path/to/wheels -r requirements.txt -r requirements-ai.txt`。依赖准备与运行时模型调用是两件事。

服务须提供 OpenAI-compatible 的 `/chat/completions` JSON envelope / SSE 协议；此处是协议名称，支持部署方自托管或内网网关。其他协议应实现 `ai_providers/base.py` 的薄端口，不新增默认路由或隐式 fallback。

```dotenv
AI_ENABLED=true
AI_PROVIDER=openai-compatible
AI_BASE_URL=http://model.internal:8000/v1
AI_MODEL=internal-instruct
AI_AUTH_MODE=none
AI_PROVIDER_CLASS=first-party
AI_CONTEXT_PERSONAL_POLICY=mask
```

以上地址和模型仅为部署示例，程序不内置它们。地址仅允许 http/https，禁止 userinfo/query/fragment；不做 DNS 探活。需要认证时设置 `AI_AUTH_MODE=bearer`，通过部署秘密注入 `AI_API_KEY`；无认证服务无需密钥。通用 `OPENAI_*`、代理环境变量和旧 `DEEPSEEK_*` 不作为回退。无效可选配置或清单、关闭、缺配置、缺 SDK 均只使 AI 不可用。

`GET /system/ai/text-field/status` 要求登录，返回可用性、契约/清单/策略版本与公开策略；不返回地址、密钥、模型。`POST /system/ai/text-field/generate` 要求该 scope 的任一完整权限；生成器表仅 `tool:gen:edit`。认证先于 JSON/VO 解析，服务端校验清单、用途、action、metadata、策略、预算、codec 与 token，才准入供应商。

## 隐私与资源

默认 mask。never 禁读 personal 上下文，且浏览器继续阻断本次编辑已知个人值；plain 仅允许 first-party / contract-bound。前端映射只保留在字段编辑实例，关闭、采用和重开不清空，换记录/重新加载销毁。仅文本可回填，属性和 URL 不能夹带 token 或已知原值。

保护范围是本次读取及同字段编辑实例此前已知值，无法保证识别手输的未知个人信息、重新加载的历史文本或组合属性推断身份。选中联系方式后才读取；自然语言不会扩大读取范围。采用前核对，候选不会自动保存业务记录。

默认总时限 90s、8192 tokens、每用户 20/分钟和 IP 60/分钟、每进程并发 4/等待 0.2s。Bulkhead 覆盖整条上游消费与 close；多 worker 总并发乘 worker 数。只在 stop + 正常结束 + 完整 JSON/codec/token 校验后发 result；notice-only 可提示缺信息。终态后业务帧、ID 错或无终态 EOF 不可采用。

SSE 不压缩，注释心跳与所有 ASGI send 均有超时；慢客户端、断连、取消和异常会清理上游。不得为生成路由加读取 body 的 `@Log`。审计只记规范 ID、字段 id/count、promptVersion、配置 model、有限 outcome/时长，终结后独立短会话写一次；不记 instruction、值、文档、候选、映射、SDK body/header/异常原文。自动模型/HTTP instrumentation 在上游调用中被抑制，SSE 库原帧日志被过滤。指标只有有限标签。

## 发布清单与契约

`src/ai-context/definitions.ts` 是业务前端的唯一静态定义源，secret 只留本地。运行前端 `yarn ai-context:generate` 生成 shared、backend resources 两份 manifest 和前端 revision；`yarn ai-context:check` 从源重新生成并逐份比较，不能只比较两个旧文件。生成器复用现有 TypeScript 和 Ajv 2020，不读取 Vue、表单值或密钥。部署必须把同一份 manifest 字节与对应前端一起发布，不能手改格式或清单。

后端 `scripts/export_openapi.py` 导出 shared OpenAPI，前端 `yarn api:generate` 生成类型。修改模板后也必须重跑生成，不能手改 `_generated`。共享 schema、文法和合成向量位于 `shared/ai-context`；Python 公共 VO/codec 与 TS 实际 SSE adapter 都有回归。当前实施证据见 [实施记录](../../docs/reports/aicontext-implementation.md)，核心规格在 ZXUI 仓 `docs/specs/AICONTEXT-text-field-ai-contract/`。

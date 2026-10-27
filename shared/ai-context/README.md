# ai-context/v1

2026-10-27 冻结；边界见 `contract.json`。ZXUI 内核、TextEditor、七个业务宿主、实际 HTTP/SSE adapter 与后端模型共同消费本契约，旧 AI scene 协议已移除。规范来源为 ZXUI `docs/specs/AICONTEXT-text-field-ai-contract/`；此处只保存机器契约、合成向量及生成清单。

`manifest.schema.json` 排除 secret；request/events schema 为闭合字段。正文另经现有 `remark-a-v1` codec，不能以 schema 通过替代正文校验。占位符文法与 TS/Python 实际消费者一致。流向量的单帧可能合法，但重复终态、ID 错误、无终态 EOF 或终态后事件必须由实际 adapter 拒绝。

AI 默认关闭，不要求 OpenAI 公网服务、账号或模型。显式启用并配置服务地址与模型后才构造协议客户端；关闭、缺配置不能回退公网。普通表单和编辑保持可用。部署、可选依赖和离线安装见 [部署指南](../../ruoyi-fastapi-backend/docs/text-field-ai-deployment.md)。

## 生成与检查

唯一声明源为 `ruoyi-fastapi-frontend/src/ai-context/definitions.ts`。`yarn ai-context:generate` 生成 shared/backend 两份清单及前端 SHA-256；`yarn ai-context:check` 从源重新计算并分别比较三个输出。测试保留“两个旧 JSON 相同但声明源已变”的失败回归。不得手改生成清单或 revision。

后端 `python scripts/export_openapi.py --output ../shared/openapi.json` 导出真实 DTO/SSE 联合类型，然后前端 `yarn api:generate` 生成类型。不要手改 generated 文件。

从业务仓运行 `python scripts/check_ai_context_contract.py`（开发依赖 `requirements.contracts.txt`），禁止 DNS/socket，验证三个 schema、合成正负向量和文法。后端 `tests/unit/services/test_ai_context_contract.py` 使用实际 Pydantic/文法，前端 `tests/unit/ai-context-contract.test.ts` 使用实际 codec/HTTP/SSE adapter；流序列与 HTTP 错误语义由后者验证，避免再造测试专用状态机。

当前协议采用 openai 3.37.0/httpx2 2.16.0/sse-starlette 3.0.3，对应 FastAPI 0.115.8/Starlette 0.45.3/AnyIO 4.10.0/Pydantic 2.11.7；只在后端对应协议 adapter 使用。测试为合成传输和仅回环 HTTP，真实模型质量及浏览器未验证。

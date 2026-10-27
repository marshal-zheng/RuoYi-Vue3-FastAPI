# ai-context/v1 草案

此目录是 ZXUI `AICONTEXT-text-field-ai-contract` Task 0 的共享机器草案，尚未冻结。部署清单由任务 5/6 的静态定义生成，本阶段不提交假冒正式清单。schema 只约束 wire 形状；字段唯一性、用途子集、权限、策略、声明顺序、富文本 codec、token 位置和流终态由后续 TS/Python 消费者验证，边界列在 `draft.json`。

`manifest.schema.json` 排除 secret；`request.schema.json` 和 `events.schema.json` 只接受有限字段。Document 必须另外通过已有 `remark-a-v1` codec，不能用 schema 通过替代正文校验。`vectors/request`、`events`、`http`、`streams` 以及占位符向量包含合成数据和预期判定。流序列用例的单帧可以合法，但重复终态、ID 错误等整流仍须拒绝。

AI 为可关闭的后端可选能力，不要求 OpenAI 公网服务、账号或模型。只有显式启用并配置服务地址与模型才创建对应协议客户端；关闭或缺配置不能回退到 SDK 默认公网地址。普通表单和编辑器保持可用。

已验证的兼容候选为 openai 3.37.0 / httpx2 2.16.0 / sse-starlette 3.0.3，对应 FastAPI 0.115.8 / Starlette 0.45.3 / AnyIO 4.10.0 / Pydantic 2.11.7。此前 14 项离线 SDK/ASGI 和真实 loopback HTTP 探针见 ZXUI `docs/reports/evidence/2026-10-27-delivery/`。完整业务解析需对齐实际已安装的 SQLAlchemy 2.0.48，原声明的 2.0.38 不满足 Atlas Provider；当前主工作区声明没有被更改。选择兼容 SDK 不意味着项目必须使用 OpenAI；其他协议按真实部署选择成熟客户端。

本目录检查采用开发依赖 jsonschema，运行时不加载该工具。将 `requirements.contracts.txt` 安装到隔离环境后，从业务仓运行：

```sh
python scripts/check_ai_context_contract.py
```

检查禁止 DNS 与 socket 出站，验证 schema 本身、正负形状向量、占位符文法和流向量的单帧。HTTP/流预期要在后续实际 adapter 测试中消费；此检查不宣称应用集成、模型质量或浏览器已验收。

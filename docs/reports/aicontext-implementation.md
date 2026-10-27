# AI 可关闭与局域网模型：实施记录

2026-10-27，隔离工作分支 `codex/aicontext-implementation`。尚未交付回源分支，业务前端接入和最终契约验收仍在进行。规格锚点：ZXUI 仓 `docs/specs/AICONTEXT-text-field-ai-contract/`；本文件不另立要求。

## 后端阶段

- `AI_ENABLED=false` 为默认值，没有默认公网 URL/模型，不继承通用 `OPENAI_*` 密钥或地址。普通应用导入和 remark codec 在禁止 DNS/socket、拦截所有可选 SDK 导入的子进程中通过。
- 显式选择 `openai-compatible` 协议只决定传输适配，不要求 OpenAI 账号。无认证局域网端点通过每请求公开 `extra_headers` 的 `omit` 省略 Authorization；API key 只由 `AI_AUTH_MODE=bearer` / `AI_API_KEY` 提供。SDK 重试 0、禁重定向、禁环境代理、总超时与分项超时均显式设置。实际请求由 httpx2 MockTransport 捕获；真实 loopback HTTP 探针见 ZXUI 的既有前置证据，不代表真实模型质量已验收。
- 已替换旧场景端点、手写上游 HTTP/SSE 和 DeepSeek 默认配置。复用 IAM any-of、共享 Bulkhead、现有频率计数、OperationLogService 独立短会话、remark codec 与现有 Prometheus registry。
- SDK/SSE 可选依赖锁在 `ruoyi-fastapi-backend/requirements-ai.txt`：openai 3.37.0 / httpx2 2.16.0 / sse-starlette 3.0.3，框架 FastAPI 0.115.8 / Starlette 0.45.3 / AnyIO 4.10.0 / Pydantic 2.11.7，Python 3.13.12。主 requirements 将 SQLAlchemy 声明对齐到前置解析通过的 2.0.48，未安装到原工作区。
- sse-starlette 3.0.3 的发送时限只覆盖 data 帧，且 DEBUG 会打印原帧。局部 ASGI 包装把时限覆盖到心跳/start/end，并禁用库的内容日志；保留成熟 SSE 编码、心跳与任务管理。慢客户端和断连均关闭 SDK/释放整流许可，审计在 ASGI 终结且每次只尝试一次。
- 公开 request/status、有限 HTTP ProblemDetails、delta/result/error union 已登记 OpenAPI，再用既有生成器输出 TypeScript，未手改 generated。扩展入口采用 [FastAPI 官方 OpenAPI 扩展机制](https://fastapi.tiangolo.com/how-to/extending-openapi/)，Pydantic 生成联合类型和引用。

验证命令（业务 worktree 的 `ruoyi-fastapi-backend`）：隔离 `backend-env/bin/python -m pytest tests/unit/services/test_text_field_ai.py tests/unit/services/test_text_field_ai_http.py tests/unit/services/test_text_field_ai_document.py -o addopts='' -q`，75 项通过。新模块 Ruff check/format 通过；修改的共享旧文件存在原有 Ruff 债务，增量检查记录在 worktree Git metadata。覆盖无 stop、length、stop 后异常、JSON/codec/token 失败、notice-only、307/308/401/429 单次请求、无认证请求、权限/策略/VO、用户/IP 限流、两慢流/饱和、GZip 心跳、慢发送、取消/超时、审计失败，以及 HTTP/SSE/日志哨兵检查。

## 待继续

七宿主源码接入、多轮 A/B 回填真实出站数据、两端共享向量、生成器反漂移和部署/公开文档验收尚未完成。`ai-context/v1` 仍为草案。浏览器和真实模型未执行。

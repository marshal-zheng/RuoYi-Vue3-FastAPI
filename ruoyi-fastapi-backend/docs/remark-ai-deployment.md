# AI 备注服务

AI 备注由 FastAPI 调用 DeepSeek。前端只调用本机业务 API，不持有模型凭证。
部署时在后端进程环境或部署环境的 `.env` 文件中提供以下变量，密钥由部署系统注入，不提交到仓库：

```dotenv
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
REMARK_AI_TIMEOUT_SECONDS=90
```

环境由现有 `config/env.py` 加载。配置调整后重启后端。不要在 `VITE_` 环境变量、浏览器存储或业务参数配置表中存放模型密钥。
没有有效凭证时 `GET /system/remark/ai/status` 返回 `{"available":false}`，生成请求在发起外部调用前返回 503 ProblemDetails。
status 接口只返回可用性，不返回密钥、供应商 URL 或配置内容。

`POST /system/remark/ai/generate` 要求已有登录状态，以及当前场景对应的新增或修改权限。
生成器表配置要求 `tool:gen:edit`。请求结构由 `RemarkAIRequest` 的 OpenAPI 定义维护：
`scene`、`instruction`、`target`、`document`、`selection`、`candidate`、`context`。
七个 scene 为 `user`、`role`、`post`、`dictType`、`dictData`、`config`、`genTable`。
上下文严格限制为各场景的中文显示值所需字段，参数值、密码、联系方式、整个表单不在允许范围内。
输出仅用于编辑器候选，不写数据库。用户采用后仍通过原表单保存流程提交。

返回 `text/event-stream`，每条 data 为一个 JSON 对象：

- `{"type":"delta","text":"正文增量"}`：从部分 JSON 中提取的文本，仅用于候选预览。
- `{"type":"result","document":{...}}`：完整、通过现有 remark-a-v1 校验的 Document v2。
- `{"type":"error","code":"...","message":"可展示的错误"}`：结束失败，原文保持不变，不能采用不完整输出。

原始模型 JSON 和思考内容不返回浏览器。只有正常 stop 和完整终止事件可形成结果。
前端不得自动重试生成请求，应通过 AbortSignal 在取消、关闭或切换表单会话时中止。
浏览器断开时服务会取消待处理读取并关闭供应商流。没有自动重试，也不持久化提示词或候选。
反向代理应保留 `X-Accel-Buffering: no` 和 `Cache-Control: no-store`，禁用该端点响应缓冲。
当前 Starlette 0.45.3 的 GZip 中间件会缓冲流，因此该路由使用 `Content-Encoding: identity`。

供应商实现采用已使用的 HTTPX 异步客户端，直接对接 DeepSeek chat completions 的 JSON mode/SSE。
部分解析复用 Pydantic Core `from_json(..., allow_partial='trailing-strings')`，只发送持续追加的正文前缀。
最终结果补齐块 ID 和必要默认属性，再复用现有备注 codec 拒绝未知节点、非法链接/颜色和超限内容。
不静默截断，不将供应商异常正文或 HTTP headers 写日志。

官方协议依据：[DeepSeek JSON Output](https://api-docs.deepseek.com/guides/json_mode/)、
[DeepSeek Chat Completion](https://api-docs.deepseek.com/api/create-chat-completion)、
[Pydantic JSON 解析](https://docs.pydantic.dev/latest/concepts/json/)、
[HTTPX 异步流](https://www.python-httpx.org/async/)。

# Schema 作者 API：一次有边界对照的失败回执

本次**没有获得 token 或产物质量测量**，不能得出优化后节省 token 的结论。两次请求均在生成前被服务拒绝，usage 缺失记为 `null`，不是 0。

## 固定实验

同一普通岗位 CRUD 任务：五个编辑字段、类型安全、DTO 白名单与身份隔离、后端字段错误映射、两列响应式布局及备注整行、公开 submit/reset。两版均可用自身公开能力实现；旧版允许 NativeRule.col，未要求旧版不支持的 canonical 返回或复合字段功能。

业务要求与模板固定在 [task.md](task.md)，业务类型在 [domain.ts](domain.ts)。每版只提供其 README、对应公开入口/类型和同一任务。提示明确禁止工具调用、联网、读其他文件和子代理；没有提供组件实现或业务产品源码。输入全文与 SHA-256 位于 [manifest.json](manifest.json) 和两版目录。

使用本机 `codex-cli 0.142.4`，保留用户现有 CLI 配置，不读取 config/auth 文件，不覆盖模型或 provider；两次请求都显式设置 `xhigh`。默认模型通过失败事件被观测为 `gpt-6-astra`，未有成功生成来进一步验证实际执行型号。执行目录相互隔离，read-only sandbox，每版各一次，顺序执行，每次最多 300 秒，无恢复/修复追加轮次。[run.py](run.py) 保留准确命令及限时逻辑。

## 真实结果

| 项目 | baseline | current |
| --- | --- | --- |
| CLI 退出码 | 1 | 1 |
| 运行秒数 | 8.496 | 6.523 |
| turn.completed | 缺失 | 缺失 |
| input_tokens | 未获得 | 未获得 |
| cached_input_tokens | 未获得 | 未获得 |
| output_tokens | 未获得 | 未获得 |
| reasoning_output_tokens | 未获得 | 未获得 |
| 生成代码 | 无 | 无 |
| 类型/行为质量检查 | 未运行：没有产物 | 未运行：没有产物 |

服务错误是 HTTP 400 `invalid_request_error`：当前配置的 `gpt-6-astra` 要求更新的 Codex app 或 CLI。CLI 同时报告找不到该模型的 metadata。未更换模型、升级环境或重跑；失败耗时不用于比较作者效率。

原始事件：[baseline/events.jsonl](baseline/events.jsonl)、[current/events.jsonl](current/events.jsonl)。每次完整命令、失败对象、usage 事件数组和明确的空指标在各版 `run-result.json`；汇总见 [summary.json](summary.json)。

## 复跑与解释边界

任务、公开资料、输出 JSON schema 和 runner 已冻结；若今后在兼容客户端上复跑，应另建结果目录保留本次失败，继续同任务、同模型和强度、同限时，不覆盖历史证据。成功后才对未修改的模型产物执行对应版本声明的 vue-tsc 以及 DTO/字段错误/布局检查。

即使未来这一个样本成功，也只能说明普通岗位 CRUD 样本的表现；不能据此宣称复杂业务普遍正确、普遍节省 token，或用输出代码行数代替实际 usage。

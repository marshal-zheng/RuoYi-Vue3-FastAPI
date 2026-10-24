# 同一 schema API 的文档组织 AI/token 对照协议

本轮比较作者文档的组合与内容，模型、API、类型与实际 schema 发行包完全相同。A 是修改前的完整 README；B 是新的任务入口 README 全文加 CRUD 任务文档全文。两组附加相同五个公共类型文件全文；不沿文档链接追加其他材料。输入和评分器在模型调用前以时间戳及 SHA-256 冻结。

## 相同任务与变化因素

- 原样复用上一轮的 `task.md`、`domain.ts`、`output-schema.json`，完成五字段岗位 CRUD、DTO 白名单与可信身份、后端错误映射、两列与整行备注、保存和恢复。
- A：本轮文档修改前保存的 `README.md` 全文。
- B：新版 `README.md` 全文与 `docs/authoring/crud.md` 全文。
- 相同附加类型：`src/index.ts`、`src/types.ts`、`src/form-create/index.ts`、`src/form-create/types.ts`、`src/fields/types.ts` 全文。两份类型材料逐字相同，并验证本次源码类型没有改变。
- 两组共用同一当前 schema 包公开声明及运行时，不把 baseline 当成旧 API。评分器对两组统一使用当前 path/泛型契约。
- 没有向模型提供实现、业务答案、评分器、测试或上轮输出。CRUD 文档沿用原有 name/sort 示例，补充通用 DTO 与生命周期引导，没有岗位模型字段或任务答案。共同提示包装与输出结构保持一致。
- 处理因素是“完整文档材料”与“任务入口 + CRUD 文档材料”的组合，包含内容、组织与长度变化，不能将它们拆分成各自的独立因果，也不能把推理随机波动归因为其中某项。
- B 的 README 导航计入输入，但任务路径由实验预先指定；无工具任务不会测量自动检索、选路或沿链接读取成本。结果只指给定材料下的一次代码作者任务，不代表完整 AI 开发流程的 token 消耗。

## 固定运行方式

- 同上一轮准确的 bundled CLI 路径、版本与二进制 SHA-256，模型 `gpt-6-astra`、推理 `xhigh`。如 CLI 哈希变化，在任何正式请求之前停止，不默默替换客户端。
- 四次独立首次生成，顺序 A1、B1、B2、A2（ABBA）。每次独立空目录、无历史会话，最长 600 秒，失败和超时保留且不重试。
- 沿用同一 `--ignore-user-config --ignore-rules --ephemeral` 配置，关闭 shell、多代理、apps、plugins、hooks、memories、browser/computer use、image、skill search 等，关闭 web search，`project_doc_max_bytes=0`，跳过宿主 skill 发现。提示禁止任何工具。
- 不读取、复制或修改凭据、全局配置；不启动浏览器或 computer use。模型调用仅在主代理审核冻结材料并明确允许后进行。
- 所有 argv、原始 JSONL、stderr、final JSON、时间、输入与输出哈希保留。输出代码原样进入独立评分，不人工修补或隐藏失败样本。

## 预先固定的事件分类与质量评分

- 上轮已观察到 CLI 在 `turn.started` 前发送已知 experimental-feature 告警。`runtime-settings.json` 保存完整事件。本轮预先规定：只有在第一个 `turn.started` 前、完整解析事件与该对象精确相同的告警，作为客户端预检 warning 记录，不计为模型工具调用。
- 其他 error、turn.failed、畸形事件、任何真实工具或非消息/推理 item 仍使无工具协议不合格。不会在看到本轮结果后扩大豁免范围。
- 质量使用已修正 ElCol 累计断点语义的独立 checker，并在正式调用前通过合法/非法 oracle 验证并冻结。两组使用同一当前 API、实际发行包和同一标准。
- 类型、内存业务行为、SFC 静态契约和人工审查分别记录；质量通过不等于浏览器或完整表单引擎已经验证。该评估器不评判复杂明细或未出现在共同任务中的功能。

## 指标与结论边界

- 仅取实际 `turn.completed.usage`：input、cached input、cache write input、output、reasoning output；缺失记 null。reasoning 已含于 output，不重复相加。
- total = input + output；uncached input = input − cached input。保留每次值、两组均值、逐对差值和四次实验总量；失败不会从质量成功率分母中删除。
- 同时报告首次质量成功率、无工具协议结果和耗时，不用源码行数/字节数代替 token，不按未知账户价格估算费用。
- ABBA 缓和顺序影响，但不能排除随机性、缓存和服务调度影响。一个任务、每组两次重复，只能得出此材料与此模型设置下的观察；不能推广为复杂业务、多模型或总体开发效率的稳定提升。
- 若 B 更贵、正确率下降或方向不一致，原样报告，不挑样本、不改任务、不重试。只在质量相当且协议有效的前提下解释文档的 token 收益。

`prepare.py` 只冻结材料，`python3 run.py` 只核验，`python3 run.py --execute` 才调用模型。官方事件与参数依据：[非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)、[CLI 参数](https://learn.chatgpt.com/docs/developer-commands?surface=cli)。

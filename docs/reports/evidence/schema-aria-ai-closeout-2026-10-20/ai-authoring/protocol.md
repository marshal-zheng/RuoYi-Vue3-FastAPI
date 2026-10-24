# Schema 普通 CRUD 作者对照：预先固定的实验协议

目标是测量本次 schema 公共契约与文档升级对一个普通 CRUD 作者任务的实际影响。先冻结材料及评分条件，再调用模型；不把代码行数、README 字节数或业界论文当成本包 token 节省的证据。

## 材料和比较范围

- 任务、业务 domain、输出 JSON schema 原样复用上一轮失败实验，哈希写入 manifest。五字段岗位编辑、DTO 白名单、可信身份、服务端错误、两列与整行备注、保存/恢复均为两版共有能力。
- A 是上一轮冻结的真实优化前源码快照。B 是本次运行前真实 ZXUI schema 源码的公共作者文档。
- 两版使用完全相同的提取规则：README 全文，加 `src/index.ts`、`src/types.ts`、`src/form-create/index.ts`、`src/form-create/types.ts`、`src/fields/types.ts` 五个文件全文。最后一项两版都保留，避免 current 的 `FieldPath` 缺失类型定义。没有选取更有利的片段，也没有提供私有实现、业务现成答案或测试代码。
- 两版都给出 FormCreate 3.3.5 的相同原生布局类型摘录。允许 baseline 用原生 Rule.col，不要求使用它没有的泛型、path 或 fullWidth。
- 只有一个任务、每版两次重复。结果适用于这个普通 CRUD、此材料与此模型；不推广成复杂企业表单、多模型或总体开发生产率结论。

## 运行控制

- 使用本机已有可用 bundled Codex CLI，冻结版本和二进制 SHA-256；显式模型 `gpt-6-astra`，推理 `xhigh`。
- 按 A1、B1、B2、A2（ABBA）顺序串行运行。两对顺序相反，缓和单调时间与缓存顺序影响；不声称消除了随机性或服务器调度影响。
- 每次新建独立空工作目录，不恢复会话。使用 `--ignore-user-config --ignore-rules --ephemeral`，`project_doc_max_bytes=0`；不读取、复制或更改认证文件及全局配置。
- shell、子代理、apps、plugins、hooks、memories、browser/computer use、image、skill search 等通过同一 CLI feature 配置关闭，关闭 web search，并跳过宿主 skill 发现；提示也禁止所有工具。任何非消息/推理 item 都使该次不符合无工具实验协议，不会删除记录或悄悄重跑。
- 每次最多 600 秒。保留每次原始 stdout JSONL、stderr、final JSON、完整 argv、时间、输入与输出哈希。超时或失败同样记录；不补跑、不挑样本、不人工修改生成代码、不隐藏修复轮次。本实验每次只有首次生成，修复轮次统一为零。

## 质量与指标

- 由独立 checker 对原样生成文件进行对应版本公开类型检查、业务 DTO/错误映射/save 行为检查，以及 SFC 的初始化、ref、按钮动作和 pending 约束检查。评分项在看到任何正式输出前冻结；工具、JSON 格式、类型、行为、界面静态契约分别记分，失败详情保留。
- 代码类型通过不等于行为通过；符合运行协议也不等于任务正确。报告同时列出两者，不将无效/错误输出当作成功节省。
- 只使用 `turn.completed.usage` 的实际值。分别记录 input、cached input、cache write、output、reasoning output。缺失为 null，不补零；reasoning 已属于 output，不重复相加。
- 总量为 input + output；uncached input 为 input - cached input（字段都存在时）。缓存成本与时间单独展示，不按未知账户价格估算费用；输入量含 CLI 固定上下文，不等于用户提示自身 token 数。
- 每个样本和每对差值都保留，再列每版均值。两次重复不足以做显著性或稳定节省声明；若 current 更贵或质量无提高，直接报告该结果。

## 依据与运行方式

OpenAI 官方 [非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode) 给出 JSONL 事件和 `turn.completed.usage`；[CLI 参数](https://learn.chatgpt.com/docs/developer-commands?surface=cli) 说明 `--ignore-user-config` 不加载用户配置但继续使用现有认证；[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference) 说明 shell、多代理、hooks、web search 等开关。具体可用 feature 以冻结 CLI 的 `features list` 输出为证。

`prepare.py` 只冻结一次材料；`python3 run.py` 只验哈希；`python3 run.py --execute` 才发出四次模型请求。已成功的 smoke 独立存放，不计入正式样本。

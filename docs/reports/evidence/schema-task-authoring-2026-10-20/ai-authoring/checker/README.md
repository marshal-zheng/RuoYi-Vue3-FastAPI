# 文档任务切片对照：独立质量评估

本轮仅比较两种文档输入。两组都使用相同的当前 schema API、公共类型和发行声明，`baseline` 标签代表修改前完整 README，绝不代表上一轮旧版 `FieldIssue.field` 契约。

评估器复用上一轮经过 oracle 验证的 `check-v2.cjs`。唯一调整是强制 `--variant=current`，并移除旧版 field 契约的不可达评分分支；其余 30 项检查、原生响应式断点累计语义和通过标准保持不变。原始脚本 SHA-256：`e4dd58a0d70f0f8c767bcd2204167519751cd9de37467903253c6a469ce78f91`。

```sh
node checker/check.cjs \
  --output=/absolute/path/runs/01-baseline/final.json \
  --variant=current \
  --artifact=/absolute/path/artifacts/current/package \
  --domain=/absolute/path/domain.ts \
  --zxui=/Users/hqz/Downloads/element-plus \
  --formcreate=/absolute/path/node_modules/@form-create/element-ui \
  --result=/absolute/path/runs/01-baseline/quality.json
```

`artifact` 是两组共用的本轮文档构建发行包；实际包路径和哈希由实验 manifest 固定。本次改动只涉及文档，正式评分前核对它的所有声明与 oracle 所用的上一轮当前发行声明逐字相同。Oracle 可先使用 `enterprise-review.20261020` 包，其 SHA-256 为 `231de85743ef36ee5aaf664d434b2b5d1c1c8cf9cde7bfa59f16feedc7257a58`。必须使用真实 FormCreate 3.3.5 类型，不能替换成仓库的宽泛 shim。实际实验组名保留在每次调用与运行结果中，评估器返回的 `variant=current` 仅表示 API 版本。

每个未经修改的首轮输出必须满足：

- CLI 协议有效：同模型、同 effort、同任务、同输出格式，零工具调用；预先登记的 CLI 启动警告由 runner 单独审计。
- 所有自动检查通过：输出结构、无显式 any/类型抑制、真实公开声明、字段名类型、DTO 白名单及身份隔离、非法值拒绝、原样 signal、后端错误映射、原生规则验证、单次会话初始化、公开 submit/reset、pending 禁用按钮及响应式布局。
- 人工源码审查通过：没有隐藏的第二份可编辑值、额外请求、私有 API 或未覆盖的任务遗漏。

未知后端字段包含空值、普通未知值、`__proto__`、`constructor` 和 `toString`；消息必须保留为表单级错误，不能误取对象原型属性。两组完全相同。

检查数只是故障定位信息，不能当作通用质量百分比。生成源码不得人工修补后计为首轮成功。任何不支持的运行时 import 或评估设施失败须区分为评估器限制，不能未经分析计作作者错误。如果后续发现评估器缺陷，保留原始结果，以有时间、差异、哈希和原因的独立修正版统一重评全部受影响样本。

手写 oracle 不是模型输出，也不提供给模型：

- `oracle-current.json`：上一轮当前 API 合法 oracle，预期 30/30。
- `oracle-invalid.json`：上一轮错误 oracle，预期拦截不存在的 ref 类型、不可信身份和未知错误误映射，固定四项失败。
- `oracle-min-width.json`：同当前 API 的合法 oracle，使用 `col={span:24,md:12}` 且不提供 columns，预期 30/30；确认原生 `min-width` 断点语义没有回归。

验证范围为真实发行声明的 vue-tsc、领域函数及 async-validator、Happy DOM 中使用公共 SchemaForm API stub 的宿主接线。它不代表浏览器或完整引擎交互验证。最终只报告这个普通 CRUD 任务两轮配对的局部证据，不推断所有复杂业务成功率；源码字节数不能替代实际 token。

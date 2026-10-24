# @zxio/schema-form

代码定义复杂表单与配置面板。按当前任务读对应页面；复杂业务组合多页，完整能力保留在 [契约参考](docs/authoring/reference.md)，不以减少上下文限制功能。

## 选择作者任务

| 当前任务                                  | 入口与继续阅读条件                                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 新增、编辑业务记录或表单弹框              | [CRUD](docs/authoring/crud.md)：值、规则、DTO、提交、错误、生命周期与布局                                  |
| JSON 编辑、上传、自定义对象控件           | [复合字段](docs/authoring/composite-fields.md)：raw/canonical、活动/阻断、消息、验证、焦点；与宿主任务组合 |
| 明细增删排序、嵌套服务端错误              | [明细与错误](docs/authoring/nested-errors.md)：分段路径、稳定行身份、摘要降级；自定义行控件再读复合字段    |
| 已有 DAG / Dashboard draft、history、预览 | [受控配置面板](docs/authoring/controlled-fields.md)：复用字段与解析器，保留宿主状态所有权                  |
| 读取持久化 JSON 定义                      | [JSON 导入](docs/authoring/json-import.md)：受限准入；代码规则无需白名单                                   |
| 核对全部语义、升级或排查边界              | [完整契约参考](docs/authoring/reference.md)：全部能力和验证命令                                            |

例如：带上传、可排序明细和服务端行错误的编辑弹框，组合 CRUD、复合字段、明细与错误；图节点内的 JSON 编辑器组合受控配置面板与复合字段。任务入口是阅读导航，不是功能子集或新的配置 DSL。

## 公共入口

- `@zxio/schema-form`：共享 JSON/值/bindings 类型、copy/equal；[类型定义](types.d.ts)。
- `@zxio/schema-form/fields`：字段、文本输入、解析器、消息和编辑活动；[类型定义](fields/types.d.ts)。根入口与此入口均不依赖表单引擎。
- `@zxio/schema-form/form-create`：CRUD 会话、规则与 JSON 导入；[类型定义](form-create/types.d.ts)。只有此入口依赖可选 peer `@form-create/element-ui@3.3.5`。

Vue、Element Plus、ZXUI 由宿主提供。结构样式为 `@zxio/schema-form/style.css`；浮层复用现有 ThemeHost `bind(app)` 和 `ZxThemeProvider`，只加载 CSS 不够。上方源码链接用于阅读类型，业务只从公开入口导入。

## 与 AI 协作

提供本页、选中的任务页、相关公开类型和业务编辑值/API 约束；需要具体复杂实现时再读取任务页链接的 recipe 或完整参考。按真实需求选择，遇到未覆盖行为继续检索，不让模型凭空猜 API。recipe 来自已验证的 pilot 原文件，安装包随构建交付同一份内容。

类型签名以公开声明为准，行为边界以完整参考为准；任务页说明如何组合。改动后运行消费者类型检查及受影响链路。AI/token 收益须用同任务、同模型设置下的正确率、返工与实际 token 测量，不能从文档长度直接推定。

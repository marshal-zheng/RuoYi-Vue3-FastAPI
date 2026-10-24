# 在 DAG 或 Dashboard 中复用受控字段

适用于已有 draft、history、预览、事务或提交策略的配置面板。使用 `@zxio/schema-form/fields` 与必要的根入口 JSON 工具；该路线不加载 FormCreate。普通业务记录的表单会话见 [CRUD](crud.md)。

## 保留宿主所有权

schema 字段负责输入、解析、消息和焦点；现有宿主继续拥有 canonical draft、raw 状态归属、history、记录身份及所有提交入口。复用字段契约不要求把图编辑器改为 CRUD 会话，也不要求复制一套 Rule 或保存会话。

现有 DAG 适配入口为 `@zxio/x6-devkit-dag/zxui`，使用该包的消费者按其公开文档扩展 `renderField`。其他 Vue Flow / Dashboard 宿主可直接把同一 `/fields` 契约接入已有编辑管线，无需依赖 X6 或该 DAG 适配器；本包不替它新增通用 history/事务框架。

## 组织字段与输入

`ZxField` 提供 label、description、required、messages。把默认 slot 的 `controlProps` 绑定给真实输入或有对应可访问语义的复合控件，而不是外层布局 div。对象/数组组使用 `group`，得到 fieldset/legend 和 aria-labelledby。

`ZxNumberTextInput` / `ZxJsonTextInput` 接收 `text/disabled/readonly`，发出 `edit({ text, badInput })`，暴露 focus。用 `parseNumberText` / `parseJsonText` 解析，结果是 `empty | valid(value) | invalid`。保留用户 raw 文本，只有 valid 才提交 canonical 值；invalid 报告阻断。empty 如何转换由领域定义，JSON 字面量 `null` 是有效的已有值，不等于 empty；解析器不执行表达式。

完整签名和状态分支直接见 [字段类型](../../fields/types.d.ts)；共享 JSON 与 bindings 类型见 [共享类型](../../types.d.ts)。不复制另一套宽松字符串/数字转换规则来替换解析器。

## 接通阻断、资源和错误

自定义控件遵循 [复合字段](composite-fields.md) 的 `FieldMessage`、`FieldControl` 与 `FieldEditState` 语义。每次 `edit-state` 是完整快照，pending 本身不禁止提交，blocking 必须在全部提交路由检查，包括自动保存、切换前应用、快捷键和显式保存。

宿主将字段相对路径映射到自身 draft；raw、messages 与行身份一起移动。宿主切换、重置、删除或替换字段时，退役旧回调与活动；控件取消或废弃异步工作，避免迟到结果写入另一个编辑上下文。DAG 已有适配器负责它的会话和编辑器记录；其他宿主复用自己的等价机制。

组件自己渲染 messages、正确关联 ARIA 并提供 focus，不把未知后代错误丢掉。复用对象/数组控件可参考 [MeasurementRows.vue](../../examples/inspection/MeasurementRows.vue) 和 [ProtocolConfig.vue](../../examples/protocol/ProtocolConfig.vue)，但这些 recipe 的领域状态和 CRUD 的 `arrayKeys` 不是所有宿主都必须照搬的存储模型。

## 运行与验证

宿主提供 Vue、Element Plus、ZXUI；导入 `@zxio/schema-form/style.css`，浮层继续使用现有 ThemeHost `bind(app)` 与 `ZxThemeProvider`。安装的可选适配包可能已包含相应结构样式，遵循其公开入口。

检查同一个无效 raw 能阻止真实宿主的全部提交入口，修正后能恢复提交；检查 reset/切换/移动后的回调和 history 仍由原宿主管理。完整入口依赖边界见 [参考](reference.md#依赖与-json-导入)。代码定义的复杂对象与数组不受 JSON 导入 profile 的字段数限制。

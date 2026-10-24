# 编写 JSON、上传或对象复合字段

适用于一个字段内部有多个控件、未完成输入或异步资源的场景。CRUD 会话先读 [普通 CRUD](crud.md)；已有 DAG / Dashboard 会话先读 [受控配置面板](controlled-fields.md)。字段共享相同的受控值、错误和编辑活动语义。

## 接入现有值所有者

CRUD 在 `bindings` 中显式登记复合字段，普通组件仍可直接登记：

```ts
const bindings = {
  SettingsEditor: { component: SettingsEditor, composite: true },
  BusinessLabel: BusinessLabel,
}
```

字段接收 `modelValue`、`disabled`、`messages: readonly FieldMessage[]`，发出 `update:modelValue`。`FieldMessage.path` 相对当前字段，省略 path 表示当前字段整体。适配器转发原生 value listener，不持有另一份可写值。

组件只持有确实无法表达为 canonical 值的输入状态，例如尚未解析的 raw 文本、上传进度和资源取消句柄；更新对象/数组时创建新值，不能直接改 `modelValue`。canonical 值仍须是 JSON：附件上传得到业务元数据后再写入 canonical，File 不进入表单快照。

## 让所有提交入口感知未完成输入

发出 `edit-state({ pending?, blocking? })` **完整快照**；省略 pending 表示 false，省略 blocking 表示空数组。公开契约见 [字段类型](../../fields/types.d.ts)。

| 字段状态                    | 上报与提交行为                                          |
| --------------------------- | ------------------------------------------------------- |
| 刷新可选项，但现有值可提交  | 仅 pending；宿主可以显示活动，仍允许提交                |
| 上传中，业务不能先保存      | pending 与 blocking 同时上报                            |
| JSON/数字文本非法或尚未完成 | 保留 raw，报告 blocking；不能静默提交上一个合法值       |
| 解析成功或活动结束          | 更新 canonical，报告新的完整状态，清除已结束的活动/阻断 |

用 `defineExpose` 提供 `focus(relativePath?)`，必要时提供 `validate(): boolean | Promise<boolean>`。CRUD 提交先等全部复合校验，再运行引擎校验，每个异步边界复查会话有效性和 blocking。按钮 disabled 仅是交互提示，字段不能自行绕过宿主提交管线。

reset 和记录切换会重新挂载字段。组件负责取消自己的异步资源并拒绝失效回调；适配器在卸载时清理字段状态。宿主回填值时区分父级对同一值的回声与真正的外部替换，避免无意义覆盖用户仍有效的 raw 格式。

## 渲染错误与可访问关系

组件负责把当前和后代 messages 呈现到真实控件，并让 `focus` 按相对路径定位。不能只在外层 div 上放 `aria-invalid` / `aria-describedby`。合并已有帮助说明和错误描述 ID，保持父级传入的关联；未知或无法定位的子路径在字段摘要显示。组控件可用 `ZxField group` 的 fieldset/legend 语义。

数组包含可移动行时，CRUD 表单同时声明 `arrayKeys`。行身份、错误迁移、删除和降级规则见 [明细与错误](nested-errors.md)。

## 复用已验证的 recipe

这些链接指向 pilot 原始实现，构建把同一源文件交付到安装包，不维护第二套文档实现：

- [JsonSettingsField.vue](../../examples/recipes/JsonSettingsField.vue)：raw/canonical 分离，`parseJsonText`，blocking，父值回声判断，validate/focus 与 ARIA 合并。
- [AttachmentField.vue](../../examples/inspection/AttachmentField.vue)：上传期间 pending/blocking，独立请求取消，丢弃失效结果，canonical 只保留已完成附件元数据。它使用 [inspection/model.ts](../../examples/inspection/model.ts) 的业务类型。
- [MeasurementRows.vue](../../examples/inspection/MeasurementRows.vue)：对象数组编辑、增删排序、相对子路径错误和 focus。
- [ProtocolConfig.vue](../../examples/protocol/ProtocolConfig.vue)：一个对象字段内的数组与其他属性组合。

recipe 的领域规则与服务接口属于示例业务，按真实需求替换；字段契约、生命周期和所有权遵循 [完整参考](reference.md#复合字段契约)。验证至少覆盖一次非法 raw 阻断、有效输入恢复、reset/卸载清理，以及本任务实际使用的异步或错误定位路径。

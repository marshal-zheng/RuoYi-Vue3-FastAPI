# 编辑明细并定位嵌套错误

适用于原生 group/subForm 或复合对象、数组字段。先接入 [CRUD 会话](crud.md)，自定义行编辑器再结合 [复合字段](composite-fields.md)。

## 用值路径表达错误

```ts
const arrayKeys = [{ path: ['items'], key: 'clientId' }] as const
const issue = { path: ['items', 1, 'quantity'], message: '库存不足' } as const
```

将 `arrayKeys` 传给 `ZxSchemaForm`，把 issue 放到失败结果的 `issues` 中。路径类型为 `readonly (string | number)[]`，数字定位数组下标；`['address', 'city']` 与 `['address.city']` 是两个不同地址。不要用字符串点号拆解代替后端到编辑值的显式映射。

错误里的下标指向**提交快照**。每行需有稳定且唯一的 string/number 属性，初始行与新增行都要有，不能使用当前排序位置作为 key。该属性属于编辑值，是否写入服务器 DTO 由业务决定。

## 让错误跟随原记录

- 声明稳定 key 后，移动行不会把错误留给旧下标对应的新行；删除出错行会移除其错误。
- 只有出错值发生变化时才清除对应错误；改兄弟字段不应顺带隐藏错误。
- 未声明 key 时，仅完整数组未改变才可可靠定位。key 缺失/重复或结构变化不能可靠关联时退回表单摘要，不猜另一行。
- 嵌套 `arrayKeys` 的数字段表示提交时具体父行路径，按实际数组结构分别声明；没有通配符路径语法。
- 成功、reset 和卸载会清理本轮错误。错误投影只管理自身错误，不覆盖作者已有 wrap 布局与错误配置。

## 连接控件、摘要与聚焦

原生 group/subForm 由适配器通过公开 `getSubForm` 定位；复合字段收到相对自身的剩余路径。复合字段负责把消息和 `focus(relativePath)` 转到具体输入。调用 `form.focus(path)` 可显式定位，省略 path 时定位当前错误。

没有 path、字段未知、隐藏或不能包装的原生控件错误保留为表单摘要；复合字段即使 `wrap:false` 也收到 messages。复合字段无法识别的后代路径应在自己的摘要显示，不静默丢弃。字段消息对实际输入的 ARIA 关联随当前行位置一起更新。

hidden/display 不意味着从编辑值删除；disabled 不定义提交含义。条件值清理、none/unset/null 的领域差别在 DTO adapter 中明确处理。原生 `ignore` 则不进入 canonical / 保存基线，reset 后从规则重建；需要保存或关闭保护的值保留在 canonical。

## 从原始 recipe 接入

- [MeasurementRows.vue](../../examples/inspection/MeasurementRows.vue)：稳定行 ID、移动/删除、名称和数值控件的相对错误/焦点，业务类型见 [model.ts](../../examples/inspection/model.ts)。
- [ProtocolConfig.vue](../../examples/protocol/ProtocolConfig.vue)：对象字段内的 `fields` 数组以及整体摘要。

验证真实提交中的服务端错误，在错误返回后移动、修改、删除对应行，并检查未知字段仍可见。路径与 ArrayKey 的权威签名见 [会话类型](../../form-create/types.d.ts)，完整边界见 [参考](reference.md#嵌套路径与明细身份)。

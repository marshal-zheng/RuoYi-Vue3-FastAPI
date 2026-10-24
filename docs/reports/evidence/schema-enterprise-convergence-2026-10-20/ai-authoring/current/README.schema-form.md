# @zxio/schema-form

代码定义复杂表单与配置面板的公共能力。根入口和 `/fields` 不依赖表单引擎；CRUD 通过 `/form-create` 使用固定的 FormCreate 3.3.5。DAG、Dashboard 继续拥有自己的 draft、history、预览和提交策略。

## 从这里开始

- 普通 CRUD：下方完整示例；编辑值类型贯穿 initial、read、save、saved。
- 复合字段：受控 `modelValue` + `edit-state` + `messages` + `focus/validate`；参考 [JSON 字段 recipe](../../docs/research/schema-form-pilot/pilot/recipes/JsonSettingsField.vue)。
- 明细与错误：使用分段 `path` 和 `arrayKeys`；参考 [巡检明细](../../docs/research/schema-form-pilot/pilot/inspection/MeasurementRows.vue) 与 [协议配置](../../docs/research/schema-form-pilot/pilot/protocol/ProtocolConfig.vue)。
- DAG / Dashboard：只消费 `/fields`；无需引入 CRUD 的 Rule 或保存会话。

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { ZxSchemaForm } from '@zxio/schema-form/form-create'
import type {
  RuleFor,
  Save,
  SchemaFormInstance,
} from '@zxio/schema-form/form-create'
import '@zxio/schema-form/style.css'

interface EditValues {
  name: string
  sort: number
}
const initial: EditValues = { name: '', sort: 0 }
const form = ref<SchemaFormInstance<EditValues>>()
const createRules = (): RuleFor<EditValues>[] => [
  {
    type: 'ZxInput',
    field: 'name',
    title: '名称',
    validate: [{ required: true, message: '请输入名称' }],
  },
  {
    type: 'ZxInputNumber',
    field: 'sort',
    title: '排序',
    props: { min: 0, precision: 0 },
  },
]
const save: Save<EditValues> = async (values, signal) => {
  const response = await saveBusinessDto(values, signal) // 业务 API / DTO adapter
  if (!response.ok)
    return {
      ok: false,
      issues: [{ path: ['name'], message: response.message }],
    }
  return { ok: true, values: response.editValues } // 可省略 values
}
</script>
<template>
  <ZxSchemaForm
    ref="form"
    :initial="initial"
    :create-rules="createRules"
    :save="save"
    :columns="2"
  />
  <button :disabled="form?.pending || form?.blocked" @click="form?.submit()">
    保存
  </button>
</template>
```

`RuleFor<T>` 检查顶层字段名，不把原生控件 props 再复制成另一套类型系统。复杂规则用 `SchemaRule`（原生 Rule 加 `fullWidth?: boolean`）；`NativeRule` 保留引擎原生类型。初始值只放 `initial`，不用 Rule 的 `value` 创建第二份基线。

## 值、生命周期和提交

FormCreate 独占可写值与客户端校验。会话只保留独立快照和保存基线；业务拥有 API、DTO、权限、资源和记录身份。`Values` 是 JSON 对象；泛型支持没有 index signature 的业务 interface，运行时仍拒绝 Date、File、非有限数字和非法 JSON。可选控件清空产生的对象属性 `undefined` 在快照时省略，数组成员不能是 `undefined`。

| 接口                             | 语义                                                                                                |
| -------------------------------- | --------------------------------------------------------------------------------------------------- |
| `createRules(context)`           | 每个记录会话调用一次；返回可信原生规则，函数和响应式 options 保留；reset 为新引擎实例复制规则       |
| `context.read()` / `form.read()` | 返回独立编辑值快照，修改它不会写回表单                                                              |
| `context.signal()`               | 记录资源寿命；reset 不取消，组件卸载或宿主换 key 后取消                                             |
| `save(values, signal)`           | 单次提交寿命；reset/卸载取消，失效提交结果不接纳；业务将 DTO 转成编辑值                             |
| `{ok: true, values?}`            | 有 values 时用权威值更新引擎、基线和 saved；省略时接受本次提交值；values 是完整替换而非 patch       |
| `{ok: false, issues}`            | 路径错误投影到字段；无法定位、隐藏字段的错误显示为表单摘要                                          |
| `reset()`                        | 取消提交、清理错误及字段活动，重新挂载引擎并恢复最近成功基线                                        |
| `pending` / `fieldPending`       | 前者为校验或保存进行中，后者为复合字段活动；字段 pending 本身不禁止提交                             |
| `blocked`                        | 存在复合字段未完成/非法输入；所有 `submit()` 调用均检查，不只依赖按钮 disabled                      |
| `phase`                          | `idle / validating / saving / blocked / invalid / saved / error`，供宿主稳定判断；status 是辅助提示 |
| `focus(path?)`                   | 定位原生字段或交给复合控件的相对路径；省略时定位当前错误                                            |

组件属性：`initial/createRules/save/bindings?/arrayKeys?/columns?/labelPosition?/labelWidth?/disabled?`。ref 类型使用 `SchemaFormInstance<T>`，不使用泛型 SFC 的 `InstanceType`。`diagnostics` slot 提供状态而不默认展示开发信息。

记录变更由宿主更换组件 `key`，不是修改 initial。Dialog 管读取、重试和关闭保护，使用 form.dirty/pending/blocked；关闭壳的重复 autoResetForm/preValidate/confirmOnDirty。无效 raw 输入可能不改变 canonical 值，因此关闭保护需要考虑 blocked。取消回调不会回滚服务器已经完成的写入。

## 嵌套路径与明细身份

```ts
const arrayKeys = [{ path: ['items'], key: 'clientId' }] as const
const issue = { path: ['items', 1, 'quantity'], message: '库存不足' } as const
```

路径是 `readonly (string | number)[]`，不解析点号字符串；`['address', 'city']` 与 `['address.city']` 不同。原生 group/subForm 通过公开 `getSubForm` API 定位；复合字段收到剩余的相对路径。字段名未知或不提供 path 的错误保留在摘要。

数组错误锚定提交快照里的稳定 string/number key，移动后跟随原行，删除该行后移除；仅修改出错值才清除相应错误。未声明 key 的数组只在完整数组未改变时可靠定位；缺失/重复 key 或不确定的结构变化退回摘要，不猜另一行。嵌套 arrayKeys 的数字段表示提交时具体父行的路径，按实际结构声明。

错误投影只拥有自身 error，保留作者 wrap 布局与既有错误配置。成功、重置、卸载会清理本轮错误。客户端校验仍用原生 validate/control，业务负责把后端字段名映射为编辑值路径。

隐藏不等于删除：原生 hidden/display 控制呈现，disabled 控制编辑，none/unset/null 的领域含义由业务定义。需要从提交 DTO 删除的条件字段在 DTO adapter 显式处理，不靠隐藏控件隐式丢值。代码 Rule 的原生联动/子表单能力继续由固定引擎提供；不新增联动 DSL。

## 复合字段契约

```ts
const bindings = {
  ProtocolConfig: { component: ProtocolConfigField, composite: true },
  BusinessLabel: BusinessLabelComponent, // 普通组件无需描述符
}
```

复合组件接收引擎受控的 modelValue，发出 `update:modelValue`；接收 `disabled` 与 `messages: readonly FieldMessage[]`。`FieldMessage` 为 `{severity, message, path?}`，path 相对当前复合值。公共适配器转发原生 value listener，不持有第二份值。

组件发出 `edit-state({pending?, blocking?})`；blocking 是待用户处理的 FieldMessage 数组。上传期间可同时 pending/blocking；仅刷新可选项通常只 pending。raw 文本与 canonical 值分开命名，只有解析成功才更新 canonical；非法输入保留 raw 并报告 blocking，不能静默提交上一个合法值。重置/记录更换重新挂载字段；组件自己取消资源，适配器在卸载时清理状态。

通过 `defineExpose` 提供 `focus(relativePath?)`、可选 `validate(): boolean | Promise<boolean>`。submit 先等待并检查所有复合校验，再运行引擎校验；每个异步边界复查会话有效性和 blocking。仅有 pending 不构成阻断。具体控件负责渲染消息、路径导航和错误的无障碍关联。

## 公共字段与布局

`ZxField` 提供 label/description/required/messages；slot 的 controlProps（id、aria-required、aria-invalid、aria-describedby）绑定到实际控件。`group` 使用 fieldset/legend 和 aria-labelledby，适合对象/数组组，避免 label 指向无 labelable 语义的 div。

`ZxNumberTextInput` 与 `ZxJsonTextInput` 都接收 `text/disabled/readonly`，发出 `edit({text,badInput})`，暴露 focus。分别用 `parseNumberText` / `parseJsonText` 得到 `empty | valid(value) | invalid`。空字符串和 JSON null 不等价；是否允许 empty 由领域决定。解析器不接受表达式执行。DAG 的扩展口在 `@zxio/x6-devkit-dag/zxui`，它保留自身 raw/blocker/history owner。

SchemaForm 的 `columns=1|2|3` 通过原生栅格响应式降列；顶层规则 `fullWidth` 横跨整行。业务布局策略只声明一次列数，标签和 density 继续消费宿主主题，不在每个调用点堆 span/gutter。原生 Rule.col 仍可表达业务确实需要的布局。

## 依赖与 JSON 导入

运行时和声明均按入口隔离：根入口只提供 Json/Values/Bindings、copy/equal；`/fields` 提供公共控件与 FieldPath/FieldMessage/FieldEditState/FieldControl；只有 `/form-create` 依赖可选 peer `@form-create/element-ui@3.3.5`。Vue、Element Plus、ZXUI 外置并由宿主提供。使用浮层控件需由现有 theme Host bind(app) 和 ZxThemeProvider 提供作用域，不能仅加载 CSS。

代码 bindings 和 JSON 导入准入分离。只有导入持久化 JSON 时使用 `parseDefinition(text, policy)`；`createZxuiDefinitionPolicy()` 提供默认受限 props 策略，自定义组件单独声明。代码作者无需维护 props 白名单。导入 profile 固定 engine/contract，限制 100,000 字符串码元、40 个顶层字段、40 层 JSON；拒绝事件、执行标记和非白名单键。它是受支持子集的准入约束，不是执行任意不可信原生配置的沙箱，也不是代码定义表单的规模上限。

## 本地验证与升级

```bash
pnpm -C packages/schema-form typecheck
pnpm -C packages/schema-form test
pnpm -C packages/schema-form build
node docs/research/schema-form-pilot/pilot/run.mjs test
```

输出 ESM/CJS、声明、style.css、README/LICENSE。仍未发布 npm。RuoYi、DAG 本轮使用本地 `zxio-schema-form-0.1.0-enterprise.20261020.tgz`（包内版本 0.1.0）；由 build 后的 dist 打包并更新消费者 lockfile。RuoYi 源码联调使用 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus`。

在研硬切：`FieldIssue.field` 改为 `path`；`Save/BusinessContext/SchemaFormInstance` 贯通泛型；代码 binding 直接为组件或显式 composite；JSON 白名单移至独立 policy；reset 不再取消记录资源 signal。已有消费者必须一起迁移，不保留无消费者依据的兼容分支。

AI 辅助编写时优先给出本页的入口示例、相关 recipe 与业务编辑值类型，再运行类型检查和受影响链路。类型/稳定契约可减少误用，但不等于已经证明 token 减少；实际 token、返工和正确率必须在同任务、同模型设置下测量，不能用代码行数代替。

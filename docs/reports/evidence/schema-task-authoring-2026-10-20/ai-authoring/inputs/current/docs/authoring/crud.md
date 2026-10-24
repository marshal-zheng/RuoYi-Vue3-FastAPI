# 新建或编辑一条业务记录

适用于代码定义的新增、编辑表单和表单弹框。使用 `@zxio/schema-form/form-create`；它固定使用 FormCreate 3.3.5。复杂明细、上传和配置对象仍在同一会话中组合，按文末指引继续阅读。

## 建立一份编辑值

先声明业务编辑类型与 `initial`，再用 `RuleFor<T>[]` 描述顶层字段。FormCreate 独占可写值与客户端校验；业务拥有 API、DTO、权限、资源和记录身份。不要额外维护一份 `v-model` / draft，也不要在 Rule 的 `value` 中放初值。`read()` 返回独立快照，修改快照不会写回表单。

下面的 `saveBusinessDto` 是业务提供的 API / DTO adapter，不是包 API。它接收编辑值及原始 `AbortSignal`，转换为业务 DTO，并把服务端响应转回完整编辑值：

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
  const response = await saveBusinessDto(values, signal)
  if (!response.ok)
    return {
      ok: false,
      issues: [{ path: ['name'], message: response.message }],
    }
  return { ok: true, values: response.editValues }
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

`RuleFor<T>` 检查顶层字段名，不重新定义控件 props。组、子表单、原生联动使用 `SchemaRule` / `NativeRule` 与原生 `validate/control`。为真实业务规则补充原生校验；例如整数范围不能只靠输入控件的 `min/precision`，枚举也不能只靠下拉选项。

## 接通读取、提交与错误

1. 宿主读取记录并转换成完整 `initial`，完成后挂载表单。用新的组件 `key` 切换记录；修改 `initial` 不是记录切换机制。身份由当前读取会话捕获，不能信任编辑值里的 ID。
2. `save(values, signal)` 收到独立 JSON 快照。DTO adapter 在边界校验值，只选择可写字段，显式补入可信身份；不要把编辑值整体展开为 DTO。Date、File、非有限数字不属于编辑值；对象属性 `undefined` 在快照中省略，数组不允许 `undefined`。
3. 把同一个 `signal` 传给支持取消的 API。它只代表本次提交，reset/卸载会取消，失效结果不会回填；取消不能回滚服务器已完成的写入。宿主仍负责有副作用请求期间的关闭或替换策略。
4. 失败返回 `{ ok: false, issues }`。把服务端字段标识显式映射为分段 `path`，使用自有键判断或 `Map`，不要解析错误文案或把任意字符串当对象属性。未知字段保留为摘要错误，不丢弃。请求异常可抛出，由表单呈现失败。
5. 成功返回 `{ ok: true }` 接受本次提交值；返回 `values` 则完整替换，经引擎字段投影和 JSON 归一化后作为新基线及 `saved` 事件值。返回值不是 patch，也不是原始 DTO。`@saved` 中由宿主刷新列表或关闭弹框。

`createRules(context)` 每个记录会话调用一次。字典、权限等资源使用 `ref` / `reactive` props，适配器将其接入原生 `computed`，在 group 与 reset 后仍更新。异步资源可使用 `context.signal()`；它持续到记录卸载或换 key，reset 不取消。联动或交叉校验通过 `context.read()` 读取当前快照，具体选项加载仍用控件公开 API。资源不属于编辑值。显式原生 `computed` 同路径配置优先。

## 连接宿主交互和布局

- 保存入口统一调用 `form.submit()`；它处理复合校验、原生校验、阻断和保存。`pending` 表示校验/保存中，此时重复提交会被拒绝。`fieldPending` 本身不阻断；字段未完成由 `blocked` 表达，submit 仍检查校验结果，不能把所有异步选项刷新都当阻断。
- `reset()` 取消提交、清理错误和字段活动，重新挂载引擎并恢复最近成功基线。表单 ref 使用 `SchemaFormInstance<T>`，不冒充 Element Plus `FormInstance`。
- Dialog 管读取、重试和关闭保护，依据 `dirty/pending/blocked` 判断；非法 raw 输入可能不改变 canonical 值，不能只查 dirty。关闭壳的重复 autoResetForm/preValidate/confirmOnDirty，防止两个状态所有者。
- 用一次 `columns=1|2|3` 声明响应式列数，跨整行规则设 `fullWidth`；特殊业务布局仍可用原生 Rule.col。标签策略由宿主统一提供，控件 density 由主题提供。浮层依赖现有 ThemeHost 的 `bind(app)` 和 `ZxThemeProvider`，只导入 CSS 不够。
- hidden/display 只控制显示，disabled 只控制编辑；需要去掉的条件字段在 DTO adapter 中显式处理。原生 `ignore` 不进入 canonical 与保存基线，reset 后由规则初始化。

公开签名见 [会话类型](../../src/form-create/types.ts)。逐项生命周期、phase、diagnostics slot 与基线细节见 [完整参考](./reference.md#值生命周期和提交)。

## 按业务复杂度继续组合

| 任务增加的内容                              | 继续阅读                                                   |
| ------------------------------------------- | ---------------------------------------------------------- |
| JSON 编辑、上传、对象编辑器或其他自定义控件 | [复合字段](./composite-fields.md)                          |
| 明细增删排序、嵌套服务端错误、聚焦子字段    | [嵌套路径与明细身份](./nested-errors.md)                   |
| 已有 DAG / Dashboard draft 和 history       | [受控配置面板](./controlled-fields.md)，由现有宿主拥有会话 |
| 从持久化 JSON 导入定义                      | [JSON 导入](./json-import.md)，代码定义无需准入白名单      |

验证当前消费者的类型检查、真实校验/提交/重置链路与涉及的复合字段。使用包作者验证命令时见 [本地验证与升级](./reference.md#本地验证与升级)。按任务选读不限制复杂规则、嵌套层次或代码表单的字段数量。

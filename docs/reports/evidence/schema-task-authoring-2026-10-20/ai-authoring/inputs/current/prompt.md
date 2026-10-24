你正在完成一个有边界的代码作者样本。只使用本提示中给出的当前版本公开文档、类型及模板，不调用任何工具、不联网、不读取其他文件、不读配置或凭据、不启动子代理。直接返回规定 JSON，其中 postFormTs 和 postEditorVue 是完整文件源码；不要额外解释。

任务来自 RuoYi 岗位管理，两个版本都必须实现相同普通 CRUD 行为，不能要求某版本独有能力。使用该版实际支持的类型：若 Save/SchemaFormInstance 不支持泛型，使用公开旧契约并在 DTO 边界正确收窄；禁止为了看起来类型正确添加 any、ts-ignore 或 as unknown as。不要自己实现表单引擎或第二份可写表单值。

固定业务模型与服务（domain.ts 已提供，不输出也不修改）：
```ts
export interface PostValues {
  postName: string;
  postCode: string;
  postSort: number;
  status: '0' | '1';
  remark: string;
}
export interface PostDto extends PostValues { postId?: number }
export interface ServerIssue { field: string; message: string }
export interface PostApi {
  write(dto: PostDto, signal: AbortSignal): Promise<
    { ok: true } | { ok: false; errors: readonly ServerIssue[] }
  >;
}
```

要求：
1. post-form.ts 导出 createPostRules、toPostDto、postFieldIssues、createPostSave。规则字段名有 PostValues 类型检查。名称必填（非全空白），最长50；编码必填（非全空白），最长64；排序允许0且必须非负整数；状态为'0'或'1'；备注textarea。中等及更宽屏幕前四字段两列、窄屏一列，备注整行；用该版公开columns/fullWidth或原生Rule.col表达都合格。
2. toPostDto(values, postId?) 只输出五个可编辑字段及可信参数postId（存在才加）；忽略输入额外字段，不从编辑值接受身份。无效业务值应拒绝，不让旧版Values的宽类型造成静默写入。createPostSave(api,postId?)将dto和原样signal交api.write，服务成功仅返回{ok:true}，不要额外GET。
3. postFieldIssues(errors:readonly ServerIssue[])将post_name/post_code/post_sort映射至postName/postCode/postSort；状态与备注对应同名字段；未知及空field保留原错误消息并进入表单摘要，不能错误指向其他已知字段。根据当前版本公开FieldIssue契约输出。
4. PostEditor.vue 使用script setup lang=ts，props为 { initial:PostValues; postId?:number; api:PostApi }，导入同目录domain.ts与post-form.ts。宿主为每条记录创建/更换这个组件key，本组件不负责请求读取和切换。一次会话只初始化一次规则和save；ZxSchemaForm唯一拥有编辑值。保存按钮调用公开submit，恢复按钮调用公开reset；保存/恢复按钮在form.pending时禁用；ref使用该版公开SchemaFormInstance。主题宿主已由应用配置，只需引入公共style.css。
5. 保持简洁，不加测试文件、不加HTTP实现、不加业务页面壳、不用新功能伪造旧版无法完成的要求。

同一文件模板（请补全，可调整必要导入/类型）：
```ts
// post-form.ts
import type { PostApi, PostDto, PostValues, ServerIssue } from './domain';
// 公共schema类型导入
export function createPostRules() { /* TODO */ }
export function toPostDto(/* TODO */): PostDto { /* TODO */ }
export function postFieldIssues(errors: readonly ServerIssue[]) { /* TODO */ }
export function createPostSave(api: PostApi, postId?: number) { /* TODO */ }
```
```vue
<!-- PostEditor.vue -->
<script setup lang="ts">
// TODO: public imports, props, one session, typed ref
</script>
<template>
  <!-- TODO: schema form and save/reset actions -->
</template>
```

以下为两版相同的 FormCreate 3.3.5 公共布局类型摘录（用于支持普通两列，不代表schema独有能力）：
```ts
type SizeObject = { span?: number; offset?: number }
type ColProps = { span?: number; xs?: number | SizeObject; sm?: number | SizeObject; md?: number | SizeObject; lg?: number | SizeObject; xl?: number | SizeObject }
// NativeRule includes:
interface RuleAttrs { col?: Boolean | Partial<ColProps & { labelWidth?: number | string; show?: Boolean }> }
```


本次提供的公开作者文档全文：

### README.md

# @zxio/schema-form

代码定义复杂表单与配置面板。按当前任务读对应页面；复杂业务组合多页，完整能力保留在 [契约参考](./docs/authoring/reference.md)，不以减少上下文限制功能。

## 选择作者任务

| 当前任务                                  | 入口与继续阅读条件                                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 新增、编辑业务记录或表单弹框              | [CRUD](./docs/authoring/crud.md)：值、规则、DTO、提交、错误、生命周期与布局                                  |
| JSON 编辑、上传、自定义对象控件           | [复合字段](./docs/authoring/composite-fields.md)：raw/canonical、活动/阻断、消息、验证、焦点；与宿主任务组合 |
| 明细增删排序、嵌套服务端错误              | [明细与错误](./docs/authoring/nested-errors.md)：分段路径、稳定行身份、摘要降级；自定义行控件再读复合字段    |
| 已有 DAG / Dashboard draft、history、预览 | [受控配置面板](./docs/authoring/controlled-fields.md)：复用字段与解析器，保留宿主状态所有权                  |
| 读取持久化 JSON 定义                      | [JSON 导入](./docs/authoring/json-import.md)：受限准入；代码规则无需白名单                                   |
| 核对全部语义、升级或排查边界              | [完整契约参考](./docs/authoring/reference.md)：全部能力和验证命令                                            |

例如：带上传、可排序明细和服务端行错误的编辑弹框，组合 CRUD、复合字段、明细与错误；图节点内的 JSON 编辑器组合受控配置面板与复合字段。任务入口是阅读导航，不是功能子集或新的配置 DSL。

## 公共入口

- `@zxio/schema-form`：共享 JSON/值/bindings 类型、copy/equal；[类型定义](./src/types.ts)。
- `@zxio/schema-form/fields`：字段、文本输入、解析器、消息和编辑活动；[类型定义](./src/fields/types.ts)。根入口与此入口均不依赖表单引擎。
- `@zxio/schema-form/form-create`：CRUD 会话、规则与 JSON 导入；[类型定义](./src/form-create/types.ts)。只有此入口依赖可选 peer `@form-create/element-ui@3.3.5`。

Vue、Element Plus、ZXUI 由宿主提供。结构样式为 `@zxio/schema-form/style.css`；浮层复用现有 ThemeHost `bind(app)` 和 `ZxThemeProvider`，只加载 CSS 不够。上方源码链接用于阅读类型，业务只从公开入口导入。

## 与 AI 协作

提供本页、选中的任务页、相关公开类型和业务编辑值/API 约束；需要具体复杂实现时再读取任务页链接的 recipe 或完整参考。按真实需求选择，遇到未覆盖行为继续检索，不让模型凭空猜 API。recipe 来自已验证的 pilot 原文件，安装包随构建交付同一份内容。

类型签名以公开声明为准，行为边界以完整参考为准；任务页说明如何组合。改动后运行消费者类型检查及受影响链路。AI/token 收益须用同任务、同模型设置下的正确率、返工与实际 token 测量，不能从文档长度直接推定。


### docs/authoring/crud.md

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


当前版本公开入口及类型：

### src/index.ts
```ts
export { copy, equal } from './json'
export type { Binding, Bindings, CompositeBinding, Json, Values } from './types'
```

### src/types.ts
```ts
import type { Component } from 'vue'

export type Json =
  | null
  | boolean
  | number
  | string
  | Json[]
  | { [key: string]: Json }
export type Values = Record<string, Json>

/** Composite fields opt into messages, edit-state, validation and focus adaptation. */
export interface CompositeBinding {
  component: Component
  composite: true
}
export type Binding = Component | CompositeBinding
export type Bindings = Record<string, Binding>
```

### src/form-create/index.ts
```ts
import '../style.css'

export { default as ZxSchemaForm } from '../SchemaForm.vue'
export { createZxuiBindings, createZxuiDefinitionPolicy } from '../zxui'
export { parseDefinition } from '../definition'
export type {
  ArrayKey,
  BusinessContext,
  DefinitionPolicy,
  FieldPath,
  FormPhase,
  SchemaRule,
  Definition,
  FieldIssue,
  NativeRule,
  RuleFor,
  Save,
  SaveResult,
  SchemaFormInstance,
} from './types'
export type {
  Bindings,
  Binding,
  CompositeBinding,
  Json,
  Values,
} from '../types'
```

### src/form-create/types.ts
```ts
import type { Rule } from '@form-create/element-ui'
import type { Values } from '../types'
import type { FieldPath } from '../fields/types'

export type { Rule as NativeRule } from '@form-create/element-ui'
export type { FieldPath } from '../fields/types'
export type SchemaRule = Rule & { fullWidth?: boolean }
export type RuleFor<T extends object> = Omit<SchemaRule, 'field' | 'value'> & {
  field: Extract<keyof T, string>
  value?: never
}
export interface Definition {
  id: string
  revision: number
  engine: 'form-create@3.3.5'
  contract: 'zxui-schema-form-v1'
  rules: Rule[]
}
/** Import admission is separate from trusted code component registration. */
export type DefinitionPolicy = Record<string, { props: readonly string[] }>
export interface FieldIssue {
  /** Segments address the submitted editing value. Missing/unknown paths are form-level. */
  path?: FieldPath
  message: string
}
export interface ArrayKey {
  /** Path to an array. A numeric segment matches that concrete parent row. */
  path: FieldPath
  /** Stable string/number property on every row; duplicates cannot be safely addressed. */
  key: string
}
export type SaveResult<T extends object = Values> =
  | { ok: true; values?: T }
  | { ok: false; issues: readonly FieldIssue[] }
export type Save<T extends object = Values> = (
  values: T,
  signal: AbortSignal
) => Promise<SaveResult<T>>
export type FormPhase =
  | 'idle'
  | 'validating'
  | 'saving'
  | 'blocked'
  | 'invalid'
  | 'saved'
  | 'error'
export interface BusinessContext<T extends object = Values> {
  read(): T
  /** Record lifetime: reset does not cancel resources initialized once by createRules. */
  signal(): AbortSignal
}
export interface SchemaFormInstance<T extends object = Values> {
  read(): T
  reset(): void
  submit(): Promise<boolean>
  focus(path?: FieldPath): void
  readonly dirty: boolean
  readonly pending: boolean
  readonly fieldPending: boolean
  readonly blocked: boolean
  readonly phase: FormPhase
  readonly status: string
}
```

### src/fields/types.ts
```ts
import type { Json } from '../types'

/** Data addressing only; interpretation and stable row identity belong to the host. */
export type FieldPath = readonly (string | number)[]

export interface FieldMessage {
  severity: 'error' | 'warning' | 'info'
  message: string
  /** Relative to the receiving composite field. */
  path?: FieldPath
}
/** A complete snapshot: omitted pending/blocking mean false/empty in every host. */
export interface FieldEditState {
  /** Activity indicator. Non-blocking option refreshes may set this alone. */
  pending?: boolean
  /** Unfinished edits that the host must check at every commit entry point. */
  blocking?: readonly FieldMessage[]
}
export interface FieldControl {
  focus(path?: FieldPath): void
  /** Composite validation is invoked by the host's submit pipeline. */
  validate?(): boolean | Promise<boolean>
}
export interface FieldControlAttrs {
  id: string
  'aria-required'?: true
  'aria-invalid'?: true
  'aria-describedby'?: string
  'aria-labelledby'?: string
}
export interface NumberTextEdit {
  text: string
  badInput: boolean
}
export type ParsedNumberText =
  | { status: 'empty' }
  | { status: 'valid'; value: number }
  | { status: 'invalid' }

export interface JsonTextEdit {
  text: string
  badInput: boolean
}
export type ParsedJsonText =
  | { status: 'empty' }
  | { status: 'valid'; value: Json }
  | { status: 'invalid' }
```

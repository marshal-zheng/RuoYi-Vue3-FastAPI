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

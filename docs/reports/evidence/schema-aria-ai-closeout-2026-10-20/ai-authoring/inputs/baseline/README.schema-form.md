# @zxio/schema-form

ZXUI 主仓内独立 workspace package。共用字段呈现；CRUD 可选 FormCreate 3.3.5。DAG、Dashboard 保留自己的配置模型和编辑会话，不需要为了复用字段而引入表单引擎。

## 公共入口

```ts
import { copy, equal } from '@zxio/schema-form'
import type { Json, Values, Bindings } from '@zxio/schema-form'
import {
  ZxField,
  ZxNumberTextInput,
  parseNumberText,
} from '@zxio/schema-form/fields'
import { ZxSchemaForm } from '@zxio/schema-form/form-create'
import type {
  RuleFor,
  Save,
  SchemaFormInstance,
} from '@zxio/schema-form/form-create'
import '@zxio/schema-form/style.css'
```

- 根入口：JSON 值类型、独立快照与相等比较。`/fields`：受控字段、无障碍关联、数字文本解析；两者的运行时代码及类型均不依赖 FormCreate。
- `/form-create`：原生 Rule、渲染和保存会话；仅使用该入口的应用安装可选 peer `@form-create/element-ui@3.3.5`。
- 宿主安装 Vue、Element Plus、ZXUI peers，加载公共主题及组件样式。本包不注册全局插件或复制 UI runtime。
- 使用 `ZxSelect` 等带浮层的 ZXUI 控件时，应用须先通过 `@zxio/zxui/theme-host` 的 Host `bind(app)`，并在字段上层提供 `ZxThemeProvider`。仅加载 CSS 或使用 `ElConfigProvider` 不能建立主题与浮层作用域；缺少该 owner 时控件会保持禁用。已有 ZXUI 应用复用现有 Host，不为每张表单创建独立运行时。
- 业务拥有 API、DTO、权限、字典和流程；DAG 拥有 draft、撤销重做、路径、提交策略和输入缓冲。

## CRUD 接入

```vue
<script setup lang="ts">
import { ZxSchemaForm } from '@zxio/schema-form/form-create'
import type { RuleFor, Save } from '@zxio/schema-form/form-create'
import '@zxio/schema-form/style.css'

const initial = { name: '', sort: 0 }
const createRules = (): RuleFor<typeof initial>[] => [
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
const save: Save = async (values, signal) => {
  await saveBusinessDto(values, signal) // 业务实现并映射服务端错误
  return { ok: true }
}
</script>
<template>
  <ZxSchemaForm :initial="initial" :create-rules="createRules" :save="save" />
</template>
```

`createRules(context)` 每个组件会话只调用一次，返回可信代码中的原生规则，函数不经过 JSON 复制。`context` 只有 `read()` 和 `signal()`。异步字典应更新字段自己的响应式 options；内置 `ZxRadioGroup` 的 `options` 可传 getter，不重新构建整棵 rules。内置组件还包括 `ZxInput`、`ZxInputNumber`、`ZxSelect`、`ZxTagsInput`；`bindings` 可注册业务复合字段。

组件属性为 `initial/createRules/save/bindings?/labelPosition?/labelWidth?/disabled?`；记录身份变化由宿主换 `key`。`saved(values)` 通知保存成功。ref 仅提供 `read/reset/submit/dirty/pending/status`；可选 `diagnostics` slot 用于调试，不默认把内部状态展示给用户。原生规则 `value` 不应承担初始值，使用 `initial`。

FormCreate 是唯一可写值和客户端校验 owner。会话仅保留独立快照和成功保存基线。`save` 返回 `{ ok: true }` 或 `{ ok: false, issues: [{ field, message }] }`；未知或空 field 的错误显示在表单级，已知 field 映射为原生字段错误。`reset` 重挂载并恢复保存基线，取消旧 signal；旧异步结果不能回写。取消客户端回调不代表回滚已提交的服务器写入。

`Values` 是 JSON 对象；初始值拒绝 Date、File、undefined 和非有限数字。可选控件清空产生的对象成员 undefined 在引擎快照边界省略，随后由字段校验处理。数组成员仍必须是合法 JSON。

Dialog 负责显示、读数据、重试和关闭保护；关闭壳自身的 `autoResetForm/preValidate/confirmOnDirty`，使用 SchemaForm 的 dirty/pending，避免重复维护模型与验证。

## DAG / Dashboard 字段接入

`ZxField` 接收 label、description、required、messages，默认 slot 提供 `controlProps`（id、aria-required、aria-invalid、aria-describedby），调用方绑定到实际控件。容器 attrs 只落在根元素。

`ZxNumberTextInput` 接收 `text/disabled/readonly`，发出 `edit({ text, badInput })`，使用文本输入保留 `-`、`1e` 等未完成内容。`parseNumberText` 返回 `empty | valid(value) | invalid`。业务会话负责 raw buffer、dirty 和 blocker；只有 valid 值才更新领域 draft，所有提交入口都必须检查 blocker，不能悄悄保存上一个合法值。

DAG 的 `DagSchemaFields` 在 `@zxio/x6-devkit-dag/zxui` 中维护领域字段映射。本包不引入 graph/document schema、路径解释器或另一个通用 schema DSL。

## 受限定义导入

`parseDefinition` 位于 `/form-create`，用于显式导入 JSON profile。固定 `engine: 'form-create@3.3.5'`、`contract: 'zxui-schema-form-v1'`，最多 100 KB / 40 字段 / 40 层。拒绝事件、表达式、模板、执行标记和非白名单 props。它是功能准入约束，不是执行不可信代码的沙箱。导入后在自己的 `createRules` 中复制并增强；组件不再接受旧 `definition/enhance` 属性，旧 `/zxui` 入口已移除。

## 版本与升级

本轮包版本为 `0.1.0`，尚未发布 npm。必需 peers 为 Vue `^3.5.0`、Element Plus `^2.13.0` 和 ZXUI `^3.0.0-next.0`；仅 `/form-create` 消费者另装 `@form-create/element-ui@3.3.5`。DAG 的 `/zxui` facet 需要 schema-form `^0.1.0` 与 ZXUI，DAG 根入口无需这些可选 peers。

本轮 RuoYi 与 X6 使用同一份 `zxio-schema-form-0.1.0-closeout.20261019.tgz`，文件名后缀只标识本地验收快照，包内版本仍为 `0.1.0`。快照从本包 `dist/` 打包；运行代码、声明、公共样式、README 与 LICENSE 一起交付。修改包后先 build，再重新打包并更新消费者 lockfile；不要只修改源码后沿用旧 tarball。

未来获准发布后，将消费者的 schema-form `file:...tgz` 改为已发布的 `0.1.0` 并重新安装锁定。ZXUI、theme-compiler 和 X6 各包须先完成其自身版本和发布门禁，再替换对应快照；不能因 schema-form 发布而猜测这些包已含本轮改动。先升级基础 ZXUI/主题，再升级 schema-form，最后升级 DAG adapter 和业务消费者。源码联调继续使用已有 `VITE_ZXUI_LOCAL` 显式开关，正式构建使用锁定发行依赖。

## 验证

```bash
pnpm -C packages/schema-form typecheck
pnpm -C packages/schema-form test
pnpm -C packages/schema-form build
```

输出 ESM、CJS、类型及公共 style.css；Vue、Element Plus、ZXUI、FormCreate 均 external。真实接入覆盖 RuoYi 岗位管理、x6-devkit DAG inspector 与 Dashboard 单个 CPU 时序图设置面板；历史巡检/RS422 消费者也同步迁移到新入口。本包尚未发布 npm。

Dashboard 复用 `/fields`，业务拥有嵌套草稿、条件字段保留策略和预览投影，Dashboard persistence 拥有保存版本。已验收实时预览、取消恢复、真实保存/刷新回显、失败重试与实际 409 冲突；详见 [第三场景验收](../../docs/reports/2026-10-19-dashboard-schema-card.md)。本轮未修改 Schema 运行时代码，仍使用同一份 `0.1.0` closeout 快照。发行包消费者需要显式引入公共 `style.css`，不能依赖另一条路由偶然加载的样式。

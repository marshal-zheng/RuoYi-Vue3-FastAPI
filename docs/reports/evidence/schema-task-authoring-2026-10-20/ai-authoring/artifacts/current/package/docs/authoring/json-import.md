# 导入持久化 JSON 定义

只有要读取持久化 JSON 配置时才使用本页。开发者直接写代码规则时从 [CRUD](crud.md) 开始，无需 `DefinitionPolicy` 或 props 白名单；两条路径共享既有引擎能力，信任边界不同。

## 在读取边界执行准入

```ts
import {
  createZxuiDefinitionPolicy,
  parseDefinition,
} from '@zxio/schema-form/form-create'

const policy = {
  ...createZxuiDefinitionPolicy(),
  BusinessSettings: { props: [] },
}
const definition = parseDefinition(savedText, policy)
```

`savedText` 是业务读取的原始字符串。成功返回的 definition 仍是受支持的原生规则子集；自定义组件要同时有受信任的代码 binding，policy 只声明导入允许的 props，不会注册组件。具体类型见 [Definition / DefinitionPolicy](../../form-create/types.d.ts)。

导入身份固定为 `engine: 'form-create@3.3.5'`、`contract: 'zxui-schema-form-v1'`，业务提供 id 和正整数 revision。当前 profile 限制 100,000 字符串码元、40 个顶层字段和 40 层 JSON，拒绝事件、执行标记、非法 JSON 与非白名单键。它是准入约束，不是执行任意不可信原生配置的沙箱，也不是代码表单的规模上限。

## 从已准入规则组合业务代码

在 `createRules(context)` 中基于导入结果建立会话独立规则，再通过受信任代码补充异步字典、校验函数、复合组件 props 或 fullWidth。导入中不能放函数；不要为允许原生代码联动而放宽持久化 JSON 的执行边界。运行时资源和编辑值的所有权仍遵循 [CRUD](crud.md)，复杂控件遵循 [复合字段](composite-fields.md)。

内置 policy 面向受支持控件的受限 props。扩充自定义组件 policy 前确认 props 的实际语义和组件可接受的输入，不能简单允许整个原生规则对象。代码组件登记不需要这套白名单。

验证导入失败在创建会话前呈现给用户，并保留可重试的读取流程；成功导入后检查本任务实际使用的异步资源、校验和提交。完整范围与依赖隔离见 [参考](reference.md#依赖与-json-导入)。本页不增加发布、版本迁移、远程执行或配置平台机制。

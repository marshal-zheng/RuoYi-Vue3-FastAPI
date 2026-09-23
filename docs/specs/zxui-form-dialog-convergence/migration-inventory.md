# 表单与弹窗迁移候选库存

扫描日期：2026-09-22。扫描对象：当前工作区的 `ruoyi-fastapi-frontend/src/`，包含当时尚未提交的修改。

本文是 `zxui-form-dialog-convergence` 的源码库存快照，不是迁移完成证据。本文中的数量均为**非仿真目录模板候选**，不承诺生产路由可达、当前菜单开放或运行时实例数量；未引用的 demo、孤立组件先核实其归属；不能仅因当前菜单未开放或未发现引用就豁免。确认仍属于本规格范围的可执行源码须迁移，纯文档/注释及仿真专用代码按定义排除。

除特别说明，以下文件路径以 `ruoyi-fastapi-frontend/` 为基准，行号为本次扫描时的一基源码行号。

## 扫描口径与结果

- 使用项目已有的 `@vue/compiler-sfc` 解析 SFC，再使用 `@vue/compiler-dom` 解析 `<template>`，共扫描 **235 个 `.vue` 文件**，解析错误 **0**。
- 仅统计模板 AST 的元素节点，分别精确匹配 `tag === 'el-dialog'`、`tag === 'el-input'`；`el-input-number` 单独计数，不并入 input。
- 不统计 HTML 注释、`script` / CSS 中的文本、生成器模板字符串；条件渲染和 `v-for` 中的节点按一个源码节点计数，不推断运行次数。
- 仿真目录边界为 `src/views/project/simulation/**`，整段排除，包括其中的备用页面。共享组件不能仅因被仿真页面引用就排除。
- 插槽计数限于 `el-input` 的直接子元素声明，区分 Vue 3 的 `#name` / `v-slot:name` 与遗留 `slot="name"`；四类为 prefix、suffix、prepend、append。
- textarea 仅统计精确的静态 `type="textarea"`，不推断动态 `:type` 的运行值。
- 本次未执行路由和组件生产可达性分析、浏览器检查或代码修改；只新增本文。

| 分类 | 全 `src` 模板 | 仿真目录内 | 非仿真目录模板候选 |
| --- | --- | --- | --- |
| `el-dialog` | 19 个 / 17 文件 | 1 个 / 1 文件 | **18 个 / 16 文件** |
| `el-input` | 200 个 / 73 文件 | 16 个 / 5 文件 | **184 个 / 68 文件** |
| `el-input-number`，不纳入本次 input 标签迁移计数 | 56 个 | 10 个 | **46 个** |
| 静态 textarea | 28 个 / 27 文件 | 0 | **28 个 / 27 文件** |
| 使用上述四类插槽声明的 input | 17 个 / 9 文件 | 0 | **17 个 / 9 文件** |
| 四类插槽声明 | 18 处 / 9 文件 | 0 | **18 处 / 9 文件** |

184 个 input 中，不带这四类插槽声明的有 **167 个**，其中静态 textarea 为 **28 个**；余下 **139 个**是无上述插槽且非静态 textarea 的 input。textarea 是 input 的子集，不应再加到 184 上。插槽 18 处对应 17 个 input，是因为登录密码框同时有 prefix 和 suffix。

存在两处动态 `:type`：`src/views/login.vue:55` 使用 `showPassword ? 'text' : 'password'`；`src/components/business/VxeDictAutocomplete/index.vue:16` 使用 `inputType`，其运行时是否为 textarea 不在静态 28 个的承诺内。

### 旧「257 处 input」的混算来源

全 `src` 的精确结果为 **200 个 el-input + 56 个 el-input-number + 1 个注释内 el-input = 257**。注释示例位于 `src/views/project/simulation/components/ProtocolAnalyzer.vue`。因此旧 257 不是 input 迁移实例数；也不应使用 `<el-input` 前缀匹配或 `\b` 边界代替标签精确匹配，因为连字符会使 `el-input-number` 被错误纳入。

## 原生 dialog 候选：18 个 / 16 文件

| 文件 | `el-dialog` 开始行 | 个数 |
| --- | --- | ---: |
| `src/components/business/Dag/components/DagMatrixView.vue` | 127 | 1 |
| `src/components/business/Dag/components/DagMatrixViewSimple.vue` | 127 | 1 |
| `src/components/business/Device/ExportDialog.vue` | 2 | 1 |
| `src/components/ui/ImageUpload/index.vue` | 34 | 1 |
| `src/components/ui/RightToolbar/index.vue` | 41 | 1 |
| `src/views/monitor/job/index.vue` | 178、295、305 | 3 |
| `src/views/monitor/job/log.vue` | 167 | 1 |
| `src/views/project/components/ExportDialog.vue` | 2 | 1 |
| `src/views/project/components/VersionList.vue` | 167 | 1 |
| `src/views/system/dict/data.vue` | 152 | 1 |
| `src/views/system/project/components/ProjectList.vue` | 101 | 1 |
| `src/views/system/role/selectUser.vue` | 3 | 1 |
| `src/views/system/user/profile/userAvatar.vue` | 4 | 1 |
| `src/views/tool/build/CodeTypeDialog.vue` | 2 | 1 |
| `src/views/tool/build/IconsDialog.vue` | 3 | 1 |
| `src/views/tool/build/TreeNodeDialog.vue` | 3 | 1 |

本表包含源码中存在但生产可达性未确认的组件。例如 `DagMatrixViewSimple` 未发现消费引用，`Dag/index.vue` 中的 `DagMatrixDialog` 模板及 import 已注释。它们保留为待核对候选；后续通过引用和产品用途确认归属。只要仍保留为范围内可执行源码，门禁就继续约束；不能仅因未发现引用而放行。删除无用代码需另有依据，不能以批量删除达到归零。

## 四类 input 插槽

| 插槽 | Vue 3 声明 | 遗留 `slot="..."` | 合计 |
| --- | ---: | ---: | ---: |
| prefix | 8 | 0 | 8 |
| suffix | 2 | 0 | 2 |
| prepend | 1 | 0 | 1 |
| append | 5 | 2 | 7 |
| 合计 | **16** | **2** | **18** |

| 文件 | input 开始行 → 插槽声明行及类型 |
| --- | --- |
| `src/components/business/Dag/components/DagSearchInput.vue` | 2 → 10 prefix |
| `src/components/ui/IconSelect/index.vue` | 3 → 11 suffix |
| `src/views/login.vue` | 34 → 43 prefix；55 → 65 prefix、73 suffix；87 → 97 prefix |
| `src/views/monitor/job/index.vue` | 249 → 250 append |
| `src/views/register.vue` | 6 → 13 prefix；19 → 27 prefix；33 → 41 prefix；47 → 55 prefix |
| `src/views/system/menu/components/MenuDrawer.vue` | 33 → 34 prepend |
| `src/views/tool/build/RightPanel.vue` | 89 → 90 append；98 → 99 append；138 → 139 遗留 append；179 → 180 遗留 append |
| `src/views/tool/build/TreeNodeDialog.vue` | 13 → 14 append |
| `src/views/tool/gen/genInfoForm.vue` | 113 → 114 append |

`RightPanel.vue:139` 使用 `<template slot="append">`，180 使用 `<el-select slot="append">`。这两处只是遗留插槽意图的源码证据，不代表 Vue 3 已正常提供相应具名插槽；迁移时须先转成 Vue 3 插槽语法，再检查 ZXUI 透传契约。

## 静态 textarea 候选：28 个 / 27 文件

| 文件 | input 开始行 |
| --- | --- |
| `src/components/business/Dag/components/DagMatrixView.vue` | 147 |
| `src/components/business/Dag/components/DagMatrixViewSimple.vue` | 147 |
| `src/components/business/Device/CategoryFormDialog.vue` | 21 |
| `src/components/business/Device/DeviceClazzDialog.vue` | 9 |
| `src/components/business/Device/DeviceNameDialog.vue` | 11 |
| `src/components/business/Device/NodeEditDrawer.vue` | 43 |
| `src/components/business/Device/PortEditDialog.vue` | 11 |
| `src/components/business/Protocol/ProtocolFormDrawer.vue` | 41 |
| `src/components/business/Protocol/templates/CANProtocolTemplate.vue` | 69 |
| `src/components/business/Protocol/templates/EthernetProtocolTemplate.vue` | 79 |
| `src/components/business/Protocol/templates/Protocol1553BTemplate.vue` | 69 |
| `src/components/business/Protocol/templates/RS422ProtocolTemplate.vue` | 69 |
| `src/views/monitor/cache/list.vue` | 136 |
| `src/views/project/components/ProjectEditDialog.vue` | 9 |
| `src/views/project/components/ProjectFormDialog.vue` | 23 |
| `src/views/project/components/ProtocolConfigDrawer.vue` | 50 |
| `src/views/project/components/VersionCloneDialog.vue` | 43 |
| `src/views/project/components/VersionList.vue` | 194 |
| `src/views/system/config/components/ConfigDlg.vue` | 11、21 |
| `src/views/system/dict/components/DictDlg.vue` | 18 |
| `src/views/system/dict/data.vue` | 187 |
| `src/views/system/post/components/PostDlg.vue` | 21 |
| `src/views/system/project/components/ProjectDlg.vue` | 5 |
| `src/views/system/role/components/RoleFormDrawer.vue` | 70 |
| `src/views/system/user/components/UserFormDialog.vue` | 122 |
| `src/views/tool/gen/basicInfoForm.vue` | 26 |
| `src/views/tool/gen/createTable.vue` | 6 |

## 仿真与共享边界

仿真目录内的排除项：

| 文件 | input 个数 | dialog 个数 |
| --- | ---: | ---: |
| `src/views/project/simulation/components/DataInjectionPanel.vue` | 3 | 0 |
| `src/views/project/simulation/components/EventFormDialog.vue` | 5 | 0 |
| `src/views/project/simulation/components/FaultInjectorMenu.vue` | 1 | 1，开始行 27 |
| `src/views/project/simulation/components/MessageListPanel.vue` | 1 | 0 |
| `src/views/project/simulation/components/ProtocolAnalyzer.vue` | 6 | 0 |

已核对的目录外仿真相关组件：

- `src/views/project/components/SimulationResultDialog.vue` 使用 `ZxDialog`，没有原生 el-dialog/el-input；只发现仿真 components barrel 的导出引用。
- `src/views/project/components/SimulationStatusPanel.vue` 没有原生 el-dialog/el-input。
- `src/components/ui/FloatingPanel/index.vue` 没有原生 el-dialog/el-input，只发现公共 barrel 导出；不能仅凭内容风格认定为仿真独占。

以上文件不影响 18 / 184。该核对不等于证明已穷尽所有目录外仿真专用依赖；后续发现的语义边界须单独登记并重新计数。

确认存在非仿真消费的共享区域不能排除：

- `src/components/business/Dag/index.vue` 同时被 `src/views/project/topo.vue:44` 和仿真页面引用；应按具体组件消费链判定，而不是整棵 Dag 目录排除。
- `src/views/project/components/NodeEditDrawer.vue` 被 `src/views/project/topo.vue:37` 引用，且内部继续调用 `ProtocolEditDialog`。
- `src/components/business/Protocol/templates/` 的四类协议模板被普通设备 `MessageConfigTab.vue` 和 `ProtocolFormDrawer.vue` 使用，保留在候选范围。

`src/components/ui/ThemeValidation/index.vue` 等仅发现导出、未证实生产消费的示例组件，仍属于目录扫描候选。先核实用途，确认属于范围内可执行源码就迁移；本库存不替代生产可达性和浏览器验收。

## 生成器：独立输出站点，不能混入页面模板数

生成器界面自身的 `.vue` 模板，例如 `RightPanel.vue` 中的 35 个 input，已计入 184。以下则是生成器输出规则、字符串或配置，另列处理；生成结果数量取决于用户表单配置，不是固定的运行时实例数。

| 位置 | 类型与数量 |
| --- | --- |
| `src/utils/generator/html.ts:109` | 1 个字面量 `el-dialog` 输出模板，`dialogWrapper` 返回整个标签对 |
| `src/utils/generator/html.ts:225`，返回位置 241 | 1 个 `el-input` 动态生成分支，返回 `<${el.tag}>`；此文件的字面量 `<el-input>` 个数为 0，但仍会生成原生 input |
| `src/utils/generator/html.ts:414`、417 | prepend、append 各 1 个字符串生成分支，仍输出遗留 `slot="..."` |
| `src/utils/generator/config.ts:244`、268、291 | 3 个 `tag: 'el-input'` 配置：单行文本、textarea、密码 |
| `src/utils/generator/drawingDefalut.ts:96` | 1 个默认 input 配置 |

调用链证据：`src/views/tool/build/index.vue:106` 导入 `makeUpHtml`，277 调用它；`src/utils/generator/html.ts:481` 根据生成类型调用 `dialogWrapper`。若本 spec 要求迁移后新生成代码也遵守组件契约，应单独验收这些输出站点，不能仅以 `.vue` AST 的原生标签归零证明生成器已收口。

## 后续使用本库存的规则

1. 实施前重新扫描受影响文件；文件修改后行号可能变化，本文不是冻结的替换脚本。
2. 先核对组件用途和共享依赖，再确定最终范围；不可达本身不是源码门禁的豁免理由，不能把未触达候选写成已页面验收。
3. 门禁分别处理范围内非仿真可执行模板、生成器输出、明确排除的仿真范围，避免全仓前缀 grep 造成错误结论。
4. 本文只证明扫描时的源码候选，不证明 ZXUI 插槽已修复、迁移已完成或浏览器已验收。

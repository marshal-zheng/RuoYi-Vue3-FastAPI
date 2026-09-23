# 输入公开契约与生成器实现记录

2026-09-22。范围为任务 12、任务 11 输入文档、任务 6 生成器源头，以及主代理协调的最终 tool/build 输入迁移。未修改 tasks.md；未提交；不覆盖其他代理的主题或业务修改。

## 输入候选契约

以 3.0.0-next.0 下一主版本候选交付；版本号由主代理统一更新。ZxInput 固定 ElInput，原生 number/search 不路由到其他控件或隐式搜索按钮。四个 slots 有/无 tooltip 均转发；已声明所有实际输入事件；直接转发模型，不维护双 watch。新增小型 ZxInputNumber，公开 ElInputNumber 数值能力并补实际 null 清空载荷类型。共同 Tooltip 只负责提示呈现。

ZxInput 实例公开 focus/blur/select/clear/input/textarea/textareaStyle。输入实际 DOM 引用随 textarea 切换更新。最终 class/style 归单个稳定 span 布局根，其他原生 attrs 归 ElInput，支持外部 Popover 指令引用；默认宽度100%，显式宽度/flex只作用一次，动态更新已回归。此为2026-09-23真实外部Popover缺陷修复后的最终边界，见 popover-reference-fix.md。底层 size/FormItem/Form/Provider 继承保留。

已知旧库内 number/search 消费者位于 docs/examples/input/types.vue：number 改显式 ZxInputNumber，增强 search 改 append 按钮；保持未 trim 字符串与不在 clear 自动搜索。中英文 input/input-number 文档明确旧行为迁移表、props/events/slots/expose、原生 search Event 与 ZxSearch 对象载荷差异。无其他库源码 number/search ZxInput 消费者被扫描确认。

输入改动文件（相对 ZXUI 仓）：

- packages/components/input/src/{input-core.vue,input-tooltip.vue,props.ts,instance.ts}
- packages/components/input/__tests__/input.test.tsx
- packages/components/input-number/{index.ts,src/props.ts,src/instance.ts,src/input-number.vue,src/input-number-core.vue,style/index.ts,style/css.ts,__tests__/input-number.test.tsx}
- packages/components/{index.ts,package.json}
- packages/zxui/{index.ts,core/index.ts,package.json,input-number/index.ts,input-number/style.ts,input-number/style-css.ts}
- typings/global.d.ts
- packages/theme-chalk/scripts/component-style-manifest.ts（新 input-number 叶 CSS 清单；不手改生成 CSS）
- internal/{contracts/ui-package-contracts.ts,eslint-config/index.js}
- docs/examples/input/types.vue
- docs/{zh-CN,en-US}/component/{input.md,input-number.md}
- docs/.vitepress/i18n/pages/component.json

## 生成器与页面

业务新增 src/utils/generator/identity.ts，统一新配置、旧设计读取、预览、导出的 input 身份。旧 el-input 配置转换到 zx-input，原生 type、数值模型、el-input-number 与 el-select 身份保持。纯读取转换不改原设计对象。

弹框导出采用 ZxDialog + useFormDialog + FormGrid + 真实 ElForm。提供完整 imports 与模型/可见性绑定；columns 为唯一布局输入，旧 span 在导出边界归约成 columns/full，字段不输出手写 span、label-width 或 gutter。旧嵌套行按整行容器保持字段次序。旧 prepend/append 输出 Vue 3 插槽语法。修复默认值字符串转义，以及数值 min/max/precision=0 的序列化。

CodeTypeDialog/TreeNodeDialog 迁移相同布局入口；IconsDialog 使用 xl 预设和库默认内容限高。TreeNodeDialog 对齐原父消费者的 commit 事件声明。

主代理协调的最后输入迁移在 tool/build 范围完成 39 个精确 el-input / 4 文件：RightPanel 35、CodeTypeDialog 1、TreeNodeDialog 2、IconsDialog 1。不改 el-input-number。此数为全局 184/68 初始库存中的子集，不能单独代表全仓最终数量。

本子集含原生 number 1 个（RightPanel 标签宽度，保留 v-model.number），textarea/search/dynamic type 均为 0；5 个 append 插槽（RightPanel 4、TreeNodeDialog 1），其中 2 个从旧 slot=append 转为 #append。既有文本输入 :value 改为 :model-value，确保设计数据能呈现。

业务改动文件：

- src/utils/generator/{identity,config,drawingDefalut,html,js,render}.ts
- src/views/tool/build/{CodeTypeDialog,TreeNodeDialog,IconsDialog,RightPanel}.vue
- tests/generator-form-contract.test.ts

## 验证

- ZXUI 4 个聚焦文件共 32 测试通过：Input 13、InputNumber 4、ConfirmInput 10、结构叶样式 5。覆盖 slots/参数、tooltip、input/clear 单次、IME、原生 number/search、search Event、旧增强字符串搜索组合、attrs/id/name/aria、实例响应性、size 继承、数值步进/清空。
- ZXUI 输入聚焦 TypeScript（tmp/input-contract/tsconfig.json）通过；相关源文件 lint 通过。
- ZXUI Web 全量 typecheck 曾只剩已有 dashboard 的 @zxio/vue-grid-layout/editor 解析失败，非本任务输入错误。聚合候选 build 成功由主题交付代理单独复核，不在此冒领打包浏览器结果。
- tests/generator-form-contract.test.ts 5 测试通过，包含 Vue SFC script/template 编译、完整公开 imports、旧设计读取、嵌套布局、预览 slots/model，以及同一 checkVueSource 门禁检查生成产物。
- 业务全量 vue-tsc --noEmit 通过（修正测试 script.bindings 可空类型后）。
- 生成器相关 lint：0 errors / 40 warnings，warnings 为原文件 any 与未使用参数等既有风格债。
- tool/build 六个 SFC（含 index/DraggableItem）在最终 checkVueSource(checkRawInput=true) 下全部零违规。

## 证据边界与剩余终验

本记录证明实现、类型、单元/编译/静态门禁；真实业务页面的逐页交互、截图与主题矩阵，以及同一公开表单的无源码 alias tarball 浏览器消费由主代理/主题代理完成。不能用此测试记录替代真实页面终验，也不声称正式 npm 发布或仿真通过。

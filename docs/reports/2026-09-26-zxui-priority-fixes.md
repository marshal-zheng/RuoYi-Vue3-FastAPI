# ZXUI / RuoYi 优先级修复：第一批交付

日期：2026-09-26。范围：已认可 review 中的前两项——GridList 请求竞争、公共主题操作文字可读性。通过 RuoYi 本地直连 ZXUI 源码交付，未发布 npm 或创建提交。

## 改动归属

### ZXUI：GridList 请求生命周期

- 请求在调用意图产生时获得递增序号。旧请求的成功、失败和 finally 均不能覆盖新意图；新查询尚在防抖队列中也生效。
- 立即刷新取消待执行的防抖查询；卸载取消队列、忽略在途结果、阻止异步 mounted/activated 回调重启自动刷新。
- 分页越界重取保留同一序号，并等待重取结束后才清除 loading；清空选择也核对当前序号。
- 公共 props、事件名和 load-data 载荷不变。不会中断业务已经发出的网络请求。

源码：[请求管理](/Users/hqz/Downloads/element-plus/packages/components/grid-list/src/use-grid-request.ts:38)、[组件卸载](/Users/hqz/Downloads/element-plus/packages/components/grid-list/src/grid-list.vue:404)。保留工作区已有的 fill 布局迁移。

### ZXUI：主题派生与组件消费

- 保留九套主题的品牌/状态填充色，新增 17 个公共文字角色，补齐 accent/success 及五种颜色的实心按钮 resting/hover/active 配对。已有 danger/warning/info 的 on-surface 改用更可读的派生值。
- `on-surface` 从主题正文色向品牌/状态色混合 30%；实心色块的文字按最终色块相对亮度选择纯黑或纯白。品牌表面的正文、辅助文字统一按普通字号的 4.5 门槛验收。
- Element Plus 适配器分别处理 solid、plain、text、link；链接 hover/active 不再用不够清晰的 tint 色当文字。选中 radio/checkbox 标签与实心图标分开配对。
- 实测修复了旧 `type="text"` 被 ZXUI 普通按钮兜底样式加背景的问题。当前页码改为不透明 accent 填充并使用 on-fill 前景。
- ZXUI 自身操作文字、加载文字、下拉选中项等消费新角色；边框、填充和指示条仍消费对应原角色。

源码：[公共角色](/Users/hqz/Downloads/element-plus/packages/tokens/src/contracts/theme-contract-v4.ts:161)、[Element Plus 状态映射](/Users/hqz/Downloads/element-plus/packages/theme-compiler/src/adapters/element-plus/mapping.ts:501)、[结构样式](/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css)。

### 契约与生成边界

新增 `color.contrast-text@1` 表达式，在最终轴变换和 Seeds 解析之后计算前景，避免黑白文字停留在旧色块上。输入限定为不透明 sRGB；无法计算时使用现有结构化诊断，不猜测底色。

诊断兼容规则增加一个明确的增量情形：允许新增带版本的算子 ID，要求旧 ID 全部保留，trace 字段、轴域和既有诊断定义保持原样。删除 ID 或修改原 trace 结构仍要求主版本变更，并有针对性回归。诊断和公共角色基线通过 owner update 命令生成；accent.base 描述修订附有 [契约证据](/Users/hqz/Downloads/element-plus/docs/reviews/2026-09-26-action-text-contract.json)。

派生版本为 1.2.0，EP mapping 为 2.3.0，新角色 introducedIn 为 4.4.0 experimental。九套主题、Tailwind 和结构样式均由生成器重建。因 adapter identity 变化，旧主题 generated 目录已保存在 `/tmp/zxui-priority-generated-before-20260926-050242`，没有手改生成文件。这里的版本标记不代表已经发布包。

### RuoYi：薄层消费调整

业务公共链接、协议链接/列表、工程卡片操作、富文本链接改读 `accent.on-surface`。为现有较旧的 vendor 包保留公共正文色 fallback；本次验收使用最新 ZXUI 源码。公共 aside 提示块移除固定浅底和固定文字色。没有新增业务 `--el-*` / `--zx-*` 核心值。

文件：`src/assets/styles/index.css`、`src/views/protocol/index.vue`、`src/views/project/index.vue`、`src/components/business/Device/ProtocolListDrawer.vue`、`src/components/ui/RichEditor/src/Editor.vue`。

## 验证

| 验证 | 结果 |
| --- | --- |
| GridList 现有及新增回归 | 15 / 15 通过 |
| 最终算子、诊断兼容、GridList 定向回归 | 57 / 57 通过（包含上述 GridList，不累加） |
| Kernel 全目录及适配器扩大检查 | 27 个文件、291 个用例通过；另一个旧 package-exports suite 因本地已有 dist 的前置断言失败，10 个用例未执行 |
| 结构样式策略回归 | 29 / 29 通过 |
| 主题数值检查 | 九主题 × light/dark × normal/high，3,800 个配对，最低 4.584 |
| 主题生成重放 | 1,458 / 1,458 变体及生成字节匹配 |
| 结构样式门禁 | 单一源码、确定性生成、三个参考主题闭合、theme-chalk/zxui tar 检查通过 |
| Kernel 诊断/解析/公共角色基线 | `check-contract.ts --include-contract` 通过 |
| compiler 包类型检查、tokens/compiler 构建 | 通过 |
| ZXUI 所改相关 lint / 格式 | 无 lint error；保留一处已有 console warning；格式通过 |
| RuoYi 本地直连生产构建 | 通过，输出 `/tmp/ruoyi-zxui-priority-build` |
| 两仓 diff whitespace 检查 | 通过 |

扩大检查后修改过的算子诊断和兼容策略已重新运行定向用例。没有把上述部分通过描述为全仓质量门禁通过。

**已有检查问题**：ZXUI 仓库级 `tsconfig.node.json` 在 docs Vite 插件类型、Vue 模块声明等位置报错；package-exports 测试假设本地不存在 dist，与当前已构建工作区冲突。RuoYi 定向 lint 报 49 个现有格式错误（集中于工程页原有模板/脚本）和 10 个 unused 警告；本批业务编辑限于样式，没有顺带重排这些代码。详见证据日志。

## 真实业务结果

Chrome 中使用 `http://localhost/system/user`，九主题各切换浅色/深色，共 18 个组合、180 个实际控件样本。检查新增/导入/导出按钮、文本操作、当前页码，以及新增弹框的选中状态文字与页脚按钮。只打开和关闭弹框，没有提交表单；结束时恢复陆军松枝绿深色。

下表为每个组合中测得的最小文字/背景对比度。计算读取实际 computed style 并合成背景色层；不代表整站无障碍认证。hover/active 的配对由静态矩阵与适配器回归覆盖，本次浏览器矩阵不宣称逐控件悬停/按下实测。forced-colors、任意自定义 Seeds 和仿真页面不在本轮矩阵内。

| 主题 | 浅色最低 | 深色最低 |
| --- | ---: | ---: |
| 默认 | 6.361 | 6.361 |
| 军工绿 | 5.137 | 7.703 |
| 陆军松枝绿 | 5.452 | 7.173 |
| 空军深蓝灰 | 4.745 | 7.141 |
| 武警深橄榄绿 | 5.452 | 6.393 |
| 火箭军苔藓绿 | 5.452 | 6.030 |
| 海军蓝 | 4.745 | 4.656 |
| 科技蓝 | 5.190 | 5.124 |
| 工厂蓝 | 4.649 | 4.649 |

证据：[浏览器矩阵](./evidence/2026-09-26-zxui-priority-fixes/browser-contrast.json)、[工厂蓝深色页面](./evidence/2026-09-26-zxui-priority-fixes/industrial-blue-dark.png)、[松枝绿深色弹框](./evidence/2026-09-26-zxui-priority-fixes/army-pine-dark-dialog.png)。

## 后续批次

保留原 review 的其余优先级：官方 Vite 接入/部署能力、公共列表工具栏、第三方内容主题适配、密度与缩放策略。当前修复不能替代这些工作，也未声称所有业务页面和所有 EP 组件状态已完成验收。

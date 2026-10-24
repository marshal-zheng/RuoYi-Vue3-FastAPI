# 作者文档独立覆盖审查

审查对象：ZXUI `packages/schema-form/README.md` 与 `docs/authoring/` 六页。依据为本轮修改前冻结 README、当前公开类型，以及 `session.ts`、`definition.ts` 和真实 recipe；本次是静态契约审查，不是新增浏览器验收。

结论：下列既有能力均有可达的任务入口与完整参考。未发现因任务切片删除复杂能力或新增运行时配置机制。修改前 README 从 `RuleFor<T>` 说明开始，到“本地验证与升级”之前的全部行为正文，在新 `reference.md` 中忽略空白后逐字一致；原 name/sort 示例移到 CRUD 页，没有嵌入本次 Post 五字段任务答案。

| 必须保留的能力或边界 | 新入口与定位 | 结论 |
| --- | --- | --- |
| 根、fields、form-create 分入口；只有 form-create 依赖可选引擎 | README“公共入口”；reference“依赖与 JSON 导入” | 保留 |
| FormCreate 唯一编辑值与验证 owner；业务拥有 DTO、身份、权限、API | CRUD“建立一份编辑值”“接通读取、提交与错误”；reference“值、生命周期和提交” | 保留 |
| RuleFor 字段检查、公开泛型、initial 唯一初值、公开 ref 而非 FormInstance | CRUD 示例及规则说明；reference“代码规则与资源”“值、生命周期和提交” | 保留 |
| createRules 每记录一次、读快照；记录资源 signal 与单次提交 signal 分寿命 | CRUD“接通读取、提交与错误”；reference 生命周期表 | 保留 |
| reset、卸载、换 key、失效结果以及取消不等于服务器回滚 | CRUD 第 1/3 步和宿主交互；reference 生命周期与记录段 | 保留 |
| JSON 值边界；undefined 对象/数组差异；权威保存值完整替换及引擎投影 | CRUD 第 2/5 步；reference 生命周期表及 JSON 说明 | 保留 |
| 原生 ignore/default 的初始基线与 dirty；隐藏不删值；DTO 决定发送 | CRUD 宿主交互；nested-errors 条件值段；reference 嵌套路径末段 | 保留 |
| ref/reactive options/props 经原生 computed，group/reset 保持更新，显式 computed 优先 | CRUD 资源段；reference“代码规则与资源”及示例 | 保留 |
| 分段 path 与含点字面字段不同；原生 group/subForm；复合相对路径 | nested-errors“用值路径表达错误”“连接控件、摘要与聚焦”；reference 嵌套路径节 | 保留 |
| 提交快照稳定 arrayKeys；移动、删除、值变化、无 key/重复 key 与不确定结构的摘要降级 | nested-errors“让错误跟随原记录”；reference 嵌套路径节 | 保留 |
| 错误投影只拥有自身 error；已有 wrap 保留；原生 wrap:false 与复合 messages 不同 | nested-errors 错误清理与摘要段；reference 嵌套路径节 | 保留 |
| 受控 composite binding；完整 edit-state 快照；字段 pending 不等于 blocked；每个提交入口和异步边界复查 | composite-fields 值 owner 与状态表；controlled-fields 阻断路由；reference 复合字段节 | 保留 |
| raw/canonical 分离、父值回声、validate/focus、上传取消和迟到结果退役 | composite-fields 状态/生命周期与四个 recipe；reference 复合字段节 | 保留并提供上传原 recipe 入口 |
| ZxField group 的 fieldset/legend；controlProps 关联实际输入；数字/JSON 的 empty/invalid/null | controlled-fields“组织字段与输入”；composite-fields“渲染错误与可访问关系”；reference 公共字段节 | 保留 |
| DAG/Dashboard 保持 draft/history/raw/blocker/提交策略；不强制使用 CRUD 或 X6 | controlled-fields；README 任务组合示例；reference 概述及公共字段节 | 保留，已纠正最初的适配范围泛化 |
| columns/fullWidth 与原生 Rule.col；主题 Host/Provider、density、公用 style | CRUD 宿主交互；README 公共入口；reference 公共字段与依赖节 | 保留 |
| JSON 导入 policy 与代码 bindings 分离；固定 engine/contract、大小/字段/深度限制；不是沙箱或代码规模限制 | json-import 全页；reference“依赖与 JSON 导入” | 保留 |
| phase、diagnostics、公开类型；版本硬切、构建验证、源码直连和安装包材料 | reference 生命周期表及“本地验证与升级”；README 类型入口 | 保留 |

审查发现的两项准确性问题已由文档作者修复：

1. 受控配置面板初稿把 Vue Flow / DAG 一概导向 `@zxio/x6-devkit-dag/zxui`。现在明确：该入口属于现有 DAG 适配，其他 Vue Flow / Dashboard 宿主可直接消费 `/fields`，无需依赖 X6。
2. CRUD 初稿“只有 blocked 阻止提交”过宽。真实 `session.submit()` 会拒绝进行中的重复提交，并检查会话、校验及阻断。现在明确区分提交 `pending` 与字段 `fieldPending`，保留防重复与校验要求。

七页源码文档共有 56 个相对链接，首次独立检查全部存在；文档作者另检查了锚点，最终文件哈希与本审查的正文保留检查见 `coverage-review.json`。发行包中的类型链接与 recipe 路径必须由构建改写并重新检查；源码链接有效本身不等于发行交付完成，这部分由本轮构建和实际 tarball 验证另行记录。

架构判断：任务页只组织阅读顺序与现有能力组合，没有新增 DSL、缓存、调度、运行时适配层或第二份示例实现。完整参考和公开类型保留为查证入口。任务页重复的少量关键边界服务于单页可用性，后续维护仍需同步查证完整参考，不能让短入口成为另一个行为定义来源。

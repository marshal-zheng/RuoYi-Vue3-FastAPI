# ZXUI 表单弹框统一需求规格

## 简介

统一非仿真业务的弹框尺寸、表单布局和主题消费方式。组件通用能力与主题适配缺口在 ZXUI 修复，页面布局、字典数据和业务硬编码在业务仓修复。所有归属判断先查源码与真实页面，再实施；不以专用 token 数量代替主题覆盖证据。

本次为 2026-09-22 长期收益优化修订。保留 R1–R11 及原验收项编号，按最新设计更新内容，并新增 R12/R13。执行已于 2026-09-23 按用户最新范围收尾；原始条款保留追溯，状态以 [执行进度](execution-progress.md) 与 [交付说明](../../reports/zxui-form-dialog-2026-09-22/completion-report.md) 为准，不宣称原始全范围或全部历史证据无条件通过。

## 2026-09-23 用户范围调整

用户依次明确“设备、仿真、工程不用管”和“监控、生成器也不用管”。因此后续实施及验收仅保留系统管理、登录/资料页，以及 ZXUI 通用输入、弹框、主题和本地候选包。已完成的其他改动及历史验证保留；停止模块的未验证分支不计通过、不再作为本次待办。以下原始条款不删改，以便追溯当时的设计。严格门禁继续保持已有覆盖，无新增allowlist。

## 长期收益目标

优先顺序是：**通用缺陷在库内一次解决 → 公开契约可供其他业务使用 → 业务只保留产品布局策略 → 生成器和必要门禁防止反复出现旧写法**。不以新增封装数量或标签替换数量衡量收益。

- 新业务通过公开包与接入示例即可获得本次修复，不复制 RuoYi 的主题补丁、私有路径解析或表单实例代理。
- 新增表单只声明模型、校验、列数与字段内容；调整布局策略不需要逐页修改。
- 同一主题登记驱动选择器、Host 和部署资产；同一表单策略驱动手写页面与生成结果。
- 本地源码验证和真实安装包验证都成立；已发布语义若必须调整，明确主版本边界，不能以维护成本转嫁给其他业务。

## 范围与已确认决策

- 用户明确要求“仿真不用管”：仿真页面、专用组件、图表、弹框和样式均不纳入排查、修改与验收。范围包含非仿真业务中的表单弹框、详情弹框，以及最终的输入框迁移。
- `src/views/project/simulation/**` 是明确排除的目录；目录外仅供仿真使用的组件也排除。共享组件若存在非仿真消费者，只围绕该消费者评估和验证，不扩展到仿真流程。
- R1–R4 的布局规则只约束弹框及其中的表单，不约束页面搜索栏、普通页内表单、画布、表格列宽等。R10 的输入框迁移覆盖非仿真业务模板及生成器模板，不仅限于弹框。
- 对上述范围一次性完成迁移，不留 baseline、allowlist 或长期双栈。模块范围定义不等于为未完成项设置豁免。
- 表单布局策略放业务；通用颜色、密度、控件行为放 ZXUI。业务保留原生 el-form/el-form-item 和 FormInstance，FormGrid 仅做布局，不新增 FormField 或一套表单代理。
- `el-input` → `zx-input` 保留用户 2026-09-20 决策：先完成 R11，再作为最后一个实现批次交 Cursor 执行，最后仍须真实页面终验。本次修订不启动批量替换。
- `el-input-number` 不得被 `<el-input` 前缀搜索误迁；`el-select` → `zx-select` 不在本次范围。
- 优先源码直连：`VITE_ZXUI_LOCAL=true`，`VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus`，无需先发布 npm；终验增加一次本地 tarball 消费验证，不以正式发布为前置。
- 本轮同时校正 ZxInput 的公开职责：原生输入、数值步进和增强搜索分开。现有 number/search 的重载语义属于已公开 API，变更按下一主版本候选交付，详见 R11/R13；不暗改现有 2.x 的补丁行为。
- 不新增 schema 表单引擎、主题平台、通用静态分析器或全套字段包装；富文本、绘图等其他主题改造继续由审计清单单独跟踪，不扩大本 spec。

## 2026-09-22 核对证据

完整来源与截图见 [主题接入审计](../../reports/2026-09-22-zxui-theme-adoption-audit.md)。业务源码路径以下相对于 `ruoyi-fastapi-frontend/`，ZXUI 路径相对于 `/Users/hqz/Downloads/element-plus/`。

| 事项 | 已确认事实 | 归属与处理 |
| --- | --- | --- |
| 添加用户布局 | `UserFormDialog.vue:166` 未声明尺寸并设置 `height: '60%'`；真实 DOM 宽 440px、高 600px | 业务明确尺寸与布局，不改变通用默认值来兜底所有业务 |
| 表单标签与状态 | 标签已继承主题文字色；状态 radio-group 内 radio input 数为 0 | 先查 `statusOptions` / 字典响应链，不能判断为控件存在但主题使其不可见；具体故障尚待定位 |
| 表单主题链 | EP label 读 `--el-text-color-regular`，星号读 danger，radio 选中态读 primary；ZXUI 已桥接这些全局变量 | 专用 `--el-form-*` alias 少不代表缺主题，按实际状态补缺口 |
| density | EP adapter 的 54 组产物在三档下去选择器后相同；ZXUI 核心主题自身已有 6/8/10px 差异 | 查 EP 度量桥接，保留核心 density 轴 |
| ZxInput | 两个分支不转发消费者 slots，expose 只有 focus/blur/select，仍有 `::icon` | ZXUI 通用契约缺口，必须在 R10 前补齐 |
| autofill | 业务登录页已改为主题填充与文字变量；ZXUI 尚无通用处理 | 局部修复不能充当库能力完成证据 |
| CSS 来源 | EP dark 引入与 `clearBusinessPrimaryOverrides()` 仍存在 | 按 R6 的实际覆盖前置条件清理 |

历史数字不再充当迁移验收清单：旧“257 个 el-input”实际混合了 200 个模板 el-input、56 个 el-input-number 和 1 个注释示例。排除仿真目录后的 AST 候选为 **el-input 184 处/68 文件、el-dialog 18 处/16 文件**；这是源码节点数，不证明运行时可达性。完整口径、插槽/textarea 分类与生成器单列见 [迁移库存](migration-inventory.md)。实施前核对共享/专用边界并重新扫描，后续代码变化以当次清单为准。

## 需求列表

### R1: 弹框尺寸来自预设档位

- R1.AC1: 当检查范围内的弹框调用时，不存在调用点硬编码像素或百分比宽度，包括 useDialog 选项和模板直接传值；其他 UI 元素宽度不受此规则约束。
- R1.AC2: 当使用业务表单弹框抽象时，1/2/3 列分别推导 md/lg/xl，当前 ZXUI 预设为 640/880/1120px；窄视口仍遵循组件库的视口约束。
- R1.AC3: 若表单需要覆盖推导结果，显式传合法 dialogSize 并注释理由；非表单弹框直接选预设，不强套 FormGrid。
- R1.AC4: 若表单弹框未声明可解析的尺寸，开发态有可见告警；业务 useFormDialog 显式提供 columns，不静默接受缺失尺寸。

### R2: 弹框表单节奏由单一业务抽象下发

- R2.AC1: 范围内弹框表单的 label-width 由一份业务布局策略生成 el-form 绑定，调用点不另写数值；纯布局 FormGrid 不代理表单 props。页内表单与搜索栏不强制改造。
- R2.AC2: FormGrid 只管响应式列数、横向 gap 与整行意图，横向间距来自同一布局策略；字段纵向节奏继续消费 ZXUI/EP density，不叠加另一套 row-gap 或控件尺寸。
- R2.AC3: 调用点只声明字段意图（如 full 占整行），不手写表单字段 span 几何值。
- R2.AC4: 业务继续将真实 el-form ref 交给 useDialog，不新增 FormInstance 转发、内部 ref 取出或 any 断言；校验、分步校验、重置、错误滚动/焦点和关闭重开行为保持。
- R2.AC5: columns 只有一个输入源，dialogSize 与 FormGrid 绑定从其派生；窄容器自动降列且 full 字段保持整行。策略控制初始标签宽度/横向间距与降列规则，长标签处理统一，不形成逐字段尺寸例外。

### R3: 弹框栈收口到 ZxDialog

- R3.AC1: 范围内可执行 Vue 模板的精确 el-dialog 标签归零；生成器输出模板单列检查，文档和注释不作为页面实例。
- R3.AC2: 迁移当次清单中所有范围内 el-dialog，包括会生成该标签的业务模板；不使用历史 19/17 数字替代清单验收。
- R3.AC3: 迁移后关闭、ESC、遮罩点击、挂载、校验、loading 和脏数据守卫与原行为等价。

### R4: 弹框高度由内容决定

- R4.AC1: 范围内弹框不再用百分比或 vh 的 height 固定实际高度；FormDialog 不接受直接 height。
- R4.AC2: 确需限高时使用经过验证的最大高度约束并保持正文可滚动；不得向 useDialog 传入当前未支持的 maxHeight 选项并误认为生效，具体接口见 design.md。

### R5: ZXUI 主题覆盖表单真实状态（ZXUI 仓）

- R5.AC1: 在 ZXUI 主题下，form/form-item/radio/checkbox 的标签、必填、错误、禁用、选中及焦点状态正确消费主题。直接 alias 或已验证的全局变量继承均有效；只对实际缺失的映射/结构样式补库能力，不要求为每种组件强造专用 token。
- R5.AC2: 通用输入主题处理浏览器 autofill 的背景与文字，使其随主题明暗变化；覆盖原生 el-input 和包装后的 zx-input，不能只在登录页打补丁。
- R5.AC3: 让 EP adapter/结构样式消费已有 density 度量，默认 size 下三档产生可测量的控件高度或纵向间距差异；保留核心 density 轴。保留 EP 原有有效 size 解析链（组件、已有 fallback、FormItem/Form、Provider、默认），density 只调整最终有效 size 下的主题度量，不改写 size 或其继承关系；度量表与代码统一，不让业务自行换算。
- R5.AC4: useDialog 开发态检测传入 formRef 但没有显式 dialogSize/width 的调用并告警；width 是组件库合法通用接口，但业务受 R1 约束。生产态不刷告警，不修改全部 ZxDialog 的默认档位。

### R6: 主题颜色只由 ZXUI 决定

- R6.AC1: 验证通过后，删除 src/main.ts 对 element-plus/theme-chalk/dark/css-vars.css 的引入，保留 Element Plus 必需的基础结构样式。
- R6.AC2: 先清理范围内与 ZXUI 对抗的业务主色写入及反向 alias，再删除 clearBusinessPrimaryOverrides() 及调用；领域语义色、图像和用户正文颜色不机械重写。
- R6.AC3: 上述删除依赖 R5 真实状态与明暗验证通过，并记录删除前后的计算样式与截图；不能仅因标签正常或专用 token 数量变化就判通过。全局主题改动可能影响排除模块，但不因此扩展仿真实施/验收范围，也不声称仿真已验证。

### R7: 范围内全量 CI 门禁，无存量基线

- R7.AC1: 新增 scripts/check-ui-standards.mjs，支持 --strict、--format=summary|json|markdown，违规时 exit 1，并输出范围与文件位置。
- R7.AC2: 不产出 baseline/allowlist；规则对约定范围一次性成立，仿真模块按明确范围排除，不能以“尚未迁完”新增文件豁免。
- R7.AC3: 迁移完成后接入 package.json、.github/workflows/ci.yml 与 .gitlab-ci.yml。
- R7.AC4: 覆盖 R1–R4 可静态检测项，复用 Vue/TS 解析器，检查明确的本地写法与统一入口；复杂动态配置须收敛入口并受类型/运行时约束，不实现通用跨文件数据流分析，也不静默跳过未知写法。
- R7.AC5: 生成器预览、配置、默认数据和导出共享组件身份约定；生成后的 SFC 与源码使用同一检查核心。范围内新增对 --el-* 或 --zx-* 核心主题值的竞争写入应被窄门禁拦截，不将全部业务色值视为违规。

### R8: 契约文档化

- R8.AC1: ZXUI 文档区分主题覆盖与行为封装，说明实际 props/events/slots/expose、density/size、scope/浮层及输入职责；提供可独立消费的公开表单示例和旧输入语义迁移说明，不把 RuoYi 布局 CSS 或私有路径复制为标准接入方案。
- R8.AC2: 业务 AGENTS.md 写明范围内表单弹框的统一写法与仿真排除范围，并指向本 spec；不把业务 label-width/gutter 数值规定为所有 ZXUI 消费者的标准。

### R9: 真实业务页面验证

- R9.AC1: 使用用户已授权的浏览器自动化在真实业务页面验证，记录浏览器和环境；AdsPower 可用，本次已获授权的内置浏览器证据也有效。docs/单测不能代替真实业务验收；不验证仿真。
- R9.AC2: 先沿状态选项未渲染的证据排查字典与响应适配，明确根因及归属并修复；恢复选项后再验证主题可见性，不把“0 个 radio”写成已确认字典为空。
- R9.AC3: 留存同页面、同主题、同视口的改前/改后截图及关键 DOM/计算样式，明确哪些仅完成基线、哪些已终验。

### R10: el-input 迁移到 zx-input（最后实现，交接 Cursor）

- R10.AC1: 范围内 Vue 模板的精确 el-input 标签及对应生成器输出全部迁为 zx-input；不匹配 el-input-number，不以旧前缀数量作为完成依据。
- R10.AC2: R11 完成并源码直连验证通过后，迁移清单中的 prefix/suffix/prepend/append 消费者全部迁移，不留插槽例外或白名单。
- R10.AC3: 所有 textarea、number、search 及动态 type 调用逐项确认模型值类型、属性、事件和渲染语义；若现有包装行为不兼容，先修正 ZXUI 契约，不能为追求标签归零静默改变业务行为。
- R10.AC4: 迁移完成后启用 no-raw-el-input 门禁，对约定范围一次性成立，无存量豁免。
- R10.AC5: 迁移后的真实业务页面逐页验证，包括 slots、输入/清空/焦点、实例方法和 flex 布局；不能只凭编译通过验收。
- R10.AC6: 不迁移 el-select 或 el-input-number；发现其他输入组件问题单独记录，不扩大本次批量替换范围。

### R11: ZxInput 职责清晰并兑现公开契约（ZXUI 仓，R10 的前置）

当前 input 文档声明完整继承 ElInput / ElInputNumber 的 props、events、slots，但实现尚未满足。先补实际契约，再迁移业务；不得声称所有 props/events 经 attrs 透传就天然兼容。

- R11.AC1: 在 tooltip 与非 tooltip 两个分支均转发 prefix/suffix/prepend/append 到底层 ElInput，保留插槽内容与参数。
- R11.AC2: 最终 ZxInput 的 type=search 保留原生输入语义，不再隐式注入搜索按钮；消费者 append 正常透传。旧增强搜索按显式组件/插槽组合迁移，不能继续依靠 type 同时选择 UI 行为。此条替代旧版“保留内建 append 并定优先级”的目标。
- R11.AC3: ZxInput 公开 expose 对齐实际 ElInput 能力：focus/blur/select/clear/input/textarea/textareaStyle，保持参数、返回值和响应性；不额外暴露任意底层组件状态包。数值组件按自己的契约暴露能力。
- R11.AC4: 清除 input-core.vue 的 ::icon 错误和职责拆分后的无效搜索分支；仍存在的搜索按钮图标绑定有效，不将移除的旧分支遗留在任一 tooltip 路径。
- R11.AC5: 增加聚焦回归锁定 slots、tooltip 两种路径、expose、原生 number/search 语义及拆出的数值/搜索消费行为；复用同一代表样板验证源码与包产物，不为每个业务点复制测试。
- R11.AC6: 文档分别列 ZxInput、数值输入及增强搜索的实际能力和迁移对应关系；不继续笼统宣称一个组件完整继承两类底层组件。文档收窄不能替代在用能力修复，主版本影响按 R13 交付。
- R11.AC7: 在真实业务中验证两层 wrapper 与 width: 100% 对搜索栏、flex 行、前后缀及 textarea 的影响，必要的通用修复在 ZXUI 完成。

- R11.AC8: ZxInput 固定消费 ElInput，type 专用于原生输入类型，不再把 number 转成 ElInputNumber；v-model 单一所有者，attrs/事件准确到达输入控件，name/id/aria、禁用、键盘、焦点与输入法组合输入行为保持，不增加 native/legacy 等永久兼容开关。
- R11.AC9: 将已有数值步进能力承接为小型 ZxInputNumber 并公开导出，迁移已知库内旧消费者；增强搜索按实际需求复用 ZxSearch 或显式 append 组合，核对 trim、清空触发与事件载荷，不机械替换。业务现有 el-input-number 仍不批量迁移。

### R12: 公开主题接入可供其他业务直接复用

- R12.AC1: 业务仅有一份主题登记，由其派生选择器、Host 注册与部署包列表；偏好状态经一个入口进入 Host/Provider，DOM 属性为投影而非另一套可写状态，不在页面拼 variant 字符串或写主题值。
- R12.AC2: 构建端复用 emitThemeDeployment 和主题包公开 exports，浏览器复用 createThemeDeploymentResolver 与既有 Host/Provider；最终运行时不遍历 generated/、不维护私有路径转换、不自行补写缺失库类型。源码 alias 限于显式开发工具边界。
- R12.AC3: 声明的主题包及 CSS/manifest 属于同一部署输出，安装后缺资产不能静默少一个主题；修正公开导出/类型和依赖声明，新增一个主题只需一处登记加正常依赖，不复制多份 ID 数组。
- R12.AC4: 弹框及内部二级浮层跟随发起它们的最近 scope，验证嵌套 scope、打开期间换肤、关闭重开；global body mirrored 只用于已确认的兼容边界，不能代替嵌套归属或跨 scope 污染验证。
- R12.AC5: 在既有库示例/消费 fixture 中提供一个不加载 RuoYi 修补 CSS 的表单弹框样板，与真实业务共用公开契约；若两边表现不同，记录归属并在正确层修复，不在业务增加另一套主题映射。

### R13: 可安装交付与公开 API 演进

- R13.AC1: 输入职责调整明确为下一主版本或其本地预发布候选，记录旧→新用法及行为差异；不得以现有 2.x 兼容补丁发布。已知库内消费者和示例迁移完成，外部消费者不能假定已升级。
- R13.AC2: 用真实本地 tarball、公开 imports 和部署资产完成一次隔离安装验证，禁 source alias/workspace fallback；复用既有 packed 工具，只扩展本次相关样板，不先发布 npm，也不把正式发布/外部升级作为 Cursor 的前置。
- R13.AC3: 同一代表样板通过源码和打包两种模式：类型、构建、slots/expose、明暗、density、嵌套弹框/浮层以及 autofill。记录实际 Vue/EP/ZXUI 解析版本、包哈希与产物路径；不通过本地类型补丁或重复运行时掩盖 peer/导出缺口。
- R13.AC4: 完成声明需包含业务真实页面、库通用能力和可安装产物三类证据；明确未完成项及外部升级要求。本 spec 完成不等于已发布 npm，也不等于仿真已验证。

# ZXUI 表单弹框统一实现任务

> 2026-09-22 长期收益修订。业务仓 `/Users/hqz/dev/RuoYi-Vue3-FastAPI`；**[ZXUI]** 任务在 `/Users/hqz/Downloads/element-plus`。
> 仿真及专用组件不排查、不修改、不验收；共享组件只覆盖非仿真消费者。库存见 [migration-inventory.md](migration-inventory.md)。
> 保留原 1–14 编号，新增 15/16。依赖决定顺序：15 在 9 前，12 在 11/13 前，16 在 14 前。执行状态已按 2026-09-23 用户最终范围回写。
> 输入职责调整采用下一主版本本地候选；源码直连优先，正式 npm 发布或外部业务升级不是 Cursor 迁移前置。
> **最终范围**：系统管理、登录/资料页、ZXUI 通用能力与本地候选包。用户停止设备、仿真、工程、监控、生成器的后续实施与验收；原任务描述保留，已做改动保留。`[x]`仅表示当前适用范围已完成，不代表停止模块全量通过。任务1仅余不可回补的历史同视口截图缺证；任务5停止后续验证。见[交付说明](../../reports/zxui-form-dialog-2026-09-22/completion-report.md)。

- [ ] 1. 修复状态选项数据链路并补齐样板基线
  - **收尾状态：实现和当前页面验证完成；仅R9.AC3原始同视口改前/改后证据不完整。旧截图未记录一致视口，不伪造通过；此项为历史证据限制，无新增实现待办。**
  - 复用现有添加用户证据：440×600、标签跟主题、radio input 为 0；沿 statusOptions、字典请求/缓存及响应适配确认具体根因并修复，记录业务/库归属。
  - 不硬编码字典兜底；deptList.filter 只作为相邻契约线索，不预设同因。恢复选项后检查原提交值与主题可见性。
  - 重扫库存和非仿真消费者，保存同页面/主题/视口的截图及 DOM，记录浏览器和真实依赖版本；未触达候选不算验收。
  - _需求追溯: R9.AC1, R9.AC2, R9.AC3_

- [x] 2. 建立业务薄布局策略与纯布局 FormGrid（依赖 1）
  - 一份布局策略管理 columns→dialogSize、label-width、横向 gap 与窄容器降列。useFormDialog 从唯一 columns 输入返回 dialogProps/events 与 formProps/layoutProps，不复制模型、提交或 dirty 状态。
  - 保留原生 el-form ref 与 el-form-item。FormGrid 只处理 CSS Grid 和 data-form-full，不包装 ElForm、不新增 FormField、不代理 FormInstance，也不新增 FormModalHandle。
  - 不增加 grid row-gap，纵向节奏由库主题/density 控制；长标签与降列规则在一个策略处维护。
  - 类型排除 width/height；统一入口对非法动态值诊断并剔除。保留合法预设例外及原 useDialog 回调语义。
  - 通过既有类型检查与实际校验/重置/分步/错误滚动/重开验证；不为纯布局数值新增一批单测。
  - _需求追溯: R1.AC2, R1.AC3, R1.AC4, R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5_

- [x] 3. 迁移 UserFormDialog 样板（依赖 1、2）
  - columns: 2 驱动同一尺寸/表单/布局绑定，原生 ElFormItem 声明字段与整行意图，删除 height: '60%'。
  - 核对正常视口 lg、窄容器降列、长标签、间距、错误滚动、状态选项、重开与提交；修正已有 placeholder 一致性。
  - 默认限高直接沿用库，需要时使用 dialogStyle.maxHeight，不传无效顶层 maxHeight。
  - 留存可对比证据，布局样板通过才复制到其他页面；不抢做最终输入框批量替换。
  - _需求追溯: R1.AC2, R2.AC3, R2.AC4, R2.AC5, R4.AC1, R4.AC2, R9.AC1, R9.AC2, R9.AC3_

- [x] 4. 迁移范围内其他表单弹框（依赖 3）
  - 以当前清单迁移项目、部门、通知、设备/端口、克隆、导入等普通表单；不包含仿真专用弹框。
  - 使用同一业务策略、原生表单与 FormGrid，去掉字段手写 label-width/gutter/span 和固定高度；不改内部表格/编辑器布局。
  - 逐页核对条件字段、校验、loading、脏数据守卫、关闭重开和提交值，保留范围内未完成项，不加 allowlist。
  - _需求追溯: R1.AC1, R1.AC2, R1.AC3, R2.AC1, R2.AC2, R2.AC3, R2.AC4, R4.AC1, R9.AC1_

- [ ] 5. 统一范围内非表单弹框尺寸（依赖 3）
  - **用户取消后续：此任务剩余版本、矩阵、日志、代码预览验证随设备/工程/监控/生成器移出本次范围。已有预设迁移和历史检查保留，不将未测分支勾为通过。**
  - 版本预览/详情、DagMatrix、操作日志、生成代码预览等按内容选预设，去掉硬编码宽度及百分比/vh 固定 height。
  - 依赖库默认限高，必要时用 dialogStyle.maxHeight；不强套 FormGrid。
  - 核对长内容、窄视口、关闭、全屏和挂载等既有行为，不扩展仿真验收。
  - _需求追溯: R1.AC1, R1.AC3, R4.AC1, R4.AC2, R9.AC1_

- [x] 6. 原生 dialog 与生成器表单源头收口（依赖 4、5）
  - 初始 18 个/16 文件仅为非仿真目录候选；按当次确认清单迁移 ZxDialog，并验证 ESC、遮罩、校验、loading、挂载及脏数据守卫。
  - 生成器 dialog 输出改用相同表单组合，完整输出 imports/注册/策略绑定；不把生成字符串当真实页面实例。
  - 整理现有 html/config/drawingDefalut/render 的有限组件身份对应，为后续 input 迁移准备一个统一来源，不再并行维护预览与导出的不同 tag。
  - 旧设计配置继续可读取、编辑、预览、导出；代表生成 SFC 解析与页面打开通过，源头不能重新生成旧布局。
  - _需求追溯: R3.AC1, R3.AC2, R3.AC3, R7.AC5_

- [x] 7. **[ZXUI]** 修实证主题缺口及通用 autofill
  - 复用公开 API 建立一个不加载 RuoYi 补丁的表单弹框代表样板，同时用于后续源码与打包消费检查。
  - 核对全局 alias、局部 scope 与标签/必填/错误/禁用/选中/焦点；已有继承不重复造 token，业务覆盖在业务清理，通用缺口在库源文件修复并生成。
  - 通用 autofill 验证背景/文字明暗，覆盖 ElInput 与最终 ZxInput；不得只用登录页覆盖当库能力。
  - 真实业务源码直连对照库样板，保存九主题明暗的代表表单证据；不复制整套全排列测试。
  - _需求追溯: R5.AC1, R5.AC2, R9.AC1, R9.AC3, R12.AC5_

- [x] 8. **[ZXUI]** EP density、scope 与尺寸告警（衔接 7）
  - 保留核心 density 轴，补 EP 度量消费；默认 size 测量三档差异，保留 EP 原有有效 size 解析链（组件、既有 fallback、FormItem/Form、Provider、默认），验证表单级尺寸继承；density 只作用于最终有效 size 下的主题度量，不改写继承链或两次缩放。
  - 复用已有 scope/Portal 能力验证嵌套弹框和内部二级浮层、打开中换肤、关闭重开；不能用 body mirrored 替代局部 scope 归属。
  - useDialog 开发态对 formRef 无显式 dialogSize/width 告警，业务 wrapper 推导后不误报，不修改所有 ZxDialog 的 small 默认值。
  - _需求追溯: R1.AC4, R5.AC3, R5.AC4, R12.AC4_

- [x] 9. 清理业务重复主题来源（依赖 4–8、15 与覆盖证据）
  - 清理 theme.module.css/tailwind.css 等反向 alias 与主色竞争写入，保留领域色和用户正文色；现有页面壳直接消费公开 surface/token，不增加业务映射层。
  - 状态/明暗覆盖通过后删除 EP dark/css-vars.css、clearBusinessPrimaryOverrides 及调用，确保旧写入不会重新覆盖。
  - 保留 EP 必需基础样式和正确加载顺序；库 autofill 已成立时移除重复的业务处理。
  - 对比实际非仿真页面的删除前后颜色，记录影响边界，不声称仿真通过。
  - _需求追溯: R6.AC1, R6.AC2, R6.AC3, R9.AC1, R9.AC3_

- [x] 10. 接入薄而严格的门禁（依赖 3–6、9、15）
  - 新增 check-ui-standards.mjs 薄入口，复用 Vue/TS 解析器和一个模板检查核心；源码与生成后 SFC 共用。
  - 只检查明确的模板/局部对象/统一入口。复杂间接配置改为受类型和运行时校验的入口，不做通用全程序分析，不静默跳过未知形状。
  - 覆盖 dialog 尺寸/高度绕过、表单策略、竞争主题写入和私有主题路径；不要误报页内布局、el-input-number、领域色或文档注释。
  - 无 baseline/allowlist，少量成组正反例防误报/漏报；存量通过再接入 package.json、GitHub/GitLab CI。
  - no-raw-el-input 待任务 13 完成启用；不因规则尚未启用标记输入迁移完成。
  - _需求追溯: R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC5_

- [x] 11. 完善公开示例和迁移说明（依赖 9、10、12、15）
  - **[ZXUI]** 写明原生输入、数值步进、增强搜索的职责和旧→新迁移差异，明确下一主版本候选边界与外部升级要求。
  - **[ZXUI]** docs 示例使用公开 Host/Provider/部署资产，说明 density/size 与 scope/Portal，不能要求其他业务复制 RuoYi 私有路径、类型补丁或 CSS。
  - 业务 AGENTS.md 写薄表单组合、主题唯一入口和仿真排除范围，指向 spec；业务标签宽度/gap 不成为全库规定。
  - 生成器示例与手写页面采用同一组合，库/业务契约说明与最终 Cursor 迁移目标一致。
  - _需求追溯: R8.AC1, R8.AC2, R11.AC6, R12.AC5, R13.AC1_

- [x] 12. **[ZXUI]** 拆清输入职责并完成公开契约（可与表单/主题任务并行）
  - 先记录下一主版本目标和旧行为对应表，不在现有 2.x 补丁中偷改。ZxInput 固定 ElInput，type 只表示原生输入类型，不新增永久 native/legacy 路由开关。
  - tooltip 两种路径透传四类 slots 与参数；expose 对齐 ElInput 的已承诺方法/属性，保持响应性，不暴露任意内部状态包。
  - 移除 number 路由和隐式 search append 分支，一并清除 ::icon。数值步进能力承接为小型 ZxInputNumber，补齐必要公开入口、类型、样式和库内已知调用迁移；不批量迁业务 el-input-number。
  - 旧增强搜索按需求复用 ZxSearch 或显式 append 按钮组合；核对 trim、清空触发、string 与对象载荷，保持已知消费者的业务行为，不重构所有搜索栏。
  - 统一 v-model 所有者与属性/事件目标；聚焦验证输入法组合输入、输入/清空事件只触发一次、name/id/aria、禁用、焦点和 flex。
  - 更新库内已知消费者与 docs 示例；聚焦回归覆盖真实契约，不按184个业务点复制测试。复用任务 7 的公开样板，源码直连验证业务兼容后放行。
  - _需求追溯: R11.AC1, R11.AC2, R11.AC3, R11.AC4, R11.AC5, R11.AC6, R11.AC7, R11.AC8, R11.AC9, R10.AC3, R13.AC1_

- [x] 13. Cursor 最后批量迁移 el-input（依赖 1–12、15）
  - 重新核对候选184个/68文件，静态textarea28个、17个input的18个slots为重叠分类，不按旧257前缀数替换。
  - 精确替换 el-input 为最终 ZxInput，number/search/动态type按已通过的原生语义方案逐项确认；不替换 el-input-number 或 el-select。
  - 同步生成器统一组件身份及配置/预览/输出，转换2处legacy append和生成器旧slot语法；已有设计配置读取与重新导出仍正常。
  - 核对 slots、实例方法、空值与事件、布局及动态类型，范围内一次迁完，不给复杂调用加白名单。
  - 启用 no-raw-el-input，共用模板检查器核验生成输出，逐页真实验证。前置是库本地候选通过，不是正式发布或所有外部消费者升级。
  - _需求追溯: R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5, R10.AC6, R7.AC5_

- [x] 14. 三类证据终验与状态回写（依赖 16）
  - 汇总库公开能力、真实业务页面、本地可安装产物证据，分别说明证明范围，不能拿导航旧矩阵或widget协议通过抵扣表单验收。
  - 逐页核对数据、尺寸、降列、滚动、校验、焦点、重开、输入及明暗；代表表单覆盖九主题明暗与代表主题三档density，异常再扩展，不做全排列。
  - 运行业务相关 lint/type-check/test:run/ui:standards 及 ZXUI 相关聚焦回归、既有生成/漂移检查；记录实际结果，不用新增测试数量代替质量。
  - 核对全部验收项后更新状态；未触达候选、外部升级要求及包交付限制明确记录。完成不代表已发布 npm，不代表仿真已验收。
  - _需求追溯: R9.AC1, R9.AC2, R9.AC3, R5.AC1, R5.AC3, R10.AC5, R13.AC4_

- [x] 15. 统一公开主题接入与资产交付（9、10、11、13 的前置）
  - 将现有主题选择器、Host和Vite包列表改为从一个登记源派生；登记依赖显式存在，缺包/manifest不可静默略过。
  - 构建端复用 emitThemeDeployment，浏览器用 createThemeDeploymentResolver；manifest/CSS共同交付，核对base路径，构建工具不进浏览器。
  - 移除业务运行时 generated glob、export→私有路径转换和 portalContainerScope 类型补丁；公开类型缺口在ZXUI补齐，开发alias只在工具边界保留。
  - 将偏好更新收敛为一个入口交Host/Provider，document属性为投影，去掉页面拼variant与重复状态写入；不新增另一套主题框架或必须的density设置UI。
  - 实际业务验证登记的九主题、登录/主框架/表单及二级浮层；公开样板无需RuoYi修补CSS，发现差异按归属修复。
  - _需求追溯: R12.AC1, R12.AC2, R12.AC3, R12.AC4, R12.AC5_

- [x] 16. 验证本地候选包可供其他业务安装（依赖 13）
  - 用本轮源码生成真实本地tarball和主题部署资产，记录包版本、哈希、实际解析路径及Vue/EP/ZXUI版本；先核对peer契约，不靠声明合并或重复运行时掩盖问题。
  - 复用已有packed-install/hosted-packed工具的安装/构建/浏览器能力，在隔离临时目录运行任务7/12的同一代表表单，禁止source alias/workspace fallback。
  - 核对公开imports/类型/样式及slots/expose/native类型、代表主题明暗、三档density、嵌套scope/二级浮层和真实autofill；无需在包fixture重复全部业务页面。
  - 没有正式npm发布、外部仓改动或外部全部升级前置；输出本地主版本候选消费证据及外部升级说明，交任务14终验。
  - _需求追溯: R13.AC1, R13.AC2, R13.AC3, R13.AC4_

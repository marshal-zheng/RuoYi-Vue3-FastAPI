# Spec Alignment Peer Review — 最终范围收尾

**当前用户保留范围已完成，未发现未解决的阻断代码问题。** 最终范围为系统管理、登录/个人资料、ZXUI通用输入/表单/主题与本地候选交付。设备、工程、监控、生成器停止后续工作，仿真始终排除。唯一历史证据限制是严格同视口改前/改后截图缺证，本审阅将其作为当前代码交付的非阻断限制披露，但不判该验收项通过，不伪造补拍。

本报告保留原始165条R/D/T审核表及历史partial，并单列当前适用状态；**不出具“原始全部范围100%通过”的PASS证明**。当前范围完成结论不把取消项当通过，也不表示全仓历史lint/test全绿。

Feature: zxui-form-dialog-convergence  
Spec Path: docs/specs/zxui-form-dialog-convergence  
Reviewer Mode: independent-subagent  
Time: 2026-09-23（最终用户范围与持久化证据）

## 审阅角色和边界

本审阅者是真实委派、可等待的 peer agent，已完整阅读 requirements/design/tasks，并对未实施的业务薄布局、弹框、主题公开部署、density与数据流独立读码。此前由本代理实现 input/input-number、generator/build dialogs；随后主线程明确授权本代理修复字典并发、菜单集合、role join数据契约，并接续root的input外部Popover修复及本地pack。这些部分是自审/交付证据，不能冒称独立；business_theme_deployment 已独立交叉复核 input/generator 与最新稳定根attrs路由，未发现新的阻断问题；数据修复和本轮 ContentDetailWrap 高度修复由本代理实施，已另获 business_theme_deployment 非作者读码交叉复核；该复核不替代接口/浏览器运行证据。最新输入浏览器由主题代理及root复验，未从自己的22项测试推导独立终验。

执行方式调整：用户接受由本会话直接完成，精确AST批量迁移等价落实任务13；没有声称Cursor实施。未提交或发布npm，未实施或声称验证simulation。授权诊断未读取/输出token、未新增登录、未改auth/安全配置。

## Summary

原始165项覆盖记录（保留已取消模块的未验事实）：

- R: covered 51 / partial 4 / missing 0
- D: covered 27 / partial 1 / missing 0
- T: covered 69 / partial 13 / missing 0

当前适用分类（独立于原始status，不将取消换成covered）：

- 当前范围有证据完成：152行。
- 用户取消该条后续验收：10行（既有实现/历史证据保留）。
- 历史视口证据限制：3行，即R9.AC3、T1.3及父项T1，实为1项限制。
- 当前范围待实施/待验证：0；未解决严重/高优先级代码问题：0。

13条真实业务路线B01–B13已按路线表所列操作实测；B14–B27等取消路线不计通过。原表中跨模块义务仍partial时，其当前系统/通用部分可完成，未覆盖的剩余部分已取消，见currentDisposition与范围说明。原始任务5不据共享组件局部证据冒称全部业务长内容通过。

## 已确认发现与复核

- F1 已修：两ExportDialog初始modelValue=true不打开；复核immediate watch与defaultData派生文件名，避免TDZ/dirty快照偏差。
- F2 已修：门禁允许a.dialogProps搭配b.formProps/layoutProps；本人最小反例已从[]变为form-dialog-source，正式正反例通过。
- F3 已修并完成最终业务复验：InputTooltip Fragment使外部Popover directive无法绑定；稳定元素根与正确attrs路由，native对照+两tooltip路径单click验证通过，新hash公开source/packed各两场景均已出现正确popup，B07菜单图标浮层亦已真实恢复。
- F4/F5/F6 已修：sys_yes_no并发取消、菜单collection对象当数组、role join行数组按mapping展开；聚焦回归通过，resumed记录显示字典radio及角色用户页面恢复。修复实施者交叉边界见上。
- F7 已定位并由fixture owner修复：两Vite共cache，14项依赖504；业务模块不需为此改码，重启后真实业务路由恢复，相关页面后续已随用户调整移出验收。
- F8 已修并真实路由复验通过：ContentDetailWrap.is-fill 的height:auto覆盖公开anchor的100cqh，零高度向版本表格传递。仅将旧100%限定非fill、删除fill覆盖，不改dialog hook。root实测内容869px/grid683px、克隆640px，required/3输入/取消正常（B25-clone-*）。该缺陷已存在baseline/business.patch，本轮验收暴露，修复列为自审。
- root新增cache两小diff独立复核：后端ResponseUtil.ok_resource(list)明确包装items，前端typed collections及items消费正确；readonly拼写与EP inputProps一致。真实DOM只读已由browser/resumed/B18-cache-readonly.json记录；监控后续验收现已取消。

- F9 本地环境已补齐：导入表两次真实请求均因缺gen_table报500；按root明确授权，仅模型create_all两张缺失生成器元数据表，旧35表保留，repo恢复10items/total34。后续元数据collection/pager/count-cache直接错误已有最小修复和回归；用户现已取消生成器后续验收，既有记录见generator-schema-init.md、generator-page-contract-fixes.md。

## Scope containment

初轮增量对照见 peer-review-scope-map.json、peer-review-baseline-hashes.json 与 baseline/{business,zxui}.patch。未将原有dirty内容当本轮新增。本轮新增数据契约修复映射R9/R10真实页面通路，inputPopover映射R10/R11，隔离fixture/cache映射T14/T16验收工具；均由主线程明确授权。库density生成资产量大属于同源生成。旧主题协议截图生成漂移不作为表单证据。ContentDetailWrap满高边界修复为B25真实通路必要（R9/R10），未扩大仿真实施。另有root明确授权的本地生成器缺表初始化，只创建gen_table/gen_table_column映射R9/R10真实验收前提，完整DDL可审，未改schema声明/认证。当前源代码与最终检查已冻结；范围调整和已留本地数据由completion-report.md披露。没有宣称所有未触达页面通过。

## Evidence index

业务src/tests/scripts路径相对ruoyi-fastapi-frontend，后端路径相对ruoyi-fastapi-backend；ZXUI路径相对/Users/hqz/Downloads/element-plus。报告产物路径相对此报告目录。

- **E01**: 业务 `src/components/ui/FormDialog/index.ts:11`、`policy.ts`、`FormGrid.vue`；ZXUI `packages/components/dialog/src/props.ts`。类型排除尺寸旁路，运行时sanitizer，单columns、md/lg/xl和纯布局。
- **E02**: 业务 `tests/generator-form-runtime.test.ts`（真实public组件/ElForm mount→open→required→resetFields→confirm）；`browser/user-final-validation.json`（focus=用户昵称）；`browser/resumed/project-required.json`（真实required/focus）。运行记录 `verification/peer-static-2026-09-23.log`。
- **E03**: `input-migration.json`、`browser-route-coverage.md`；业务两个 `src/components/business/Device/ExportDialog.vue`、`src/views/project/components/ExportDialog.vue` 的immediate watch/defaultData；门禁496文件0违规。
- **E04**: ZXUI `packages/theme-compiler/src/adapters/element-plus/density.ts`、`mapping.ts`、`packages/theme-chalk/src/structural.css`；`packages/components/hooks/use-dialog/__tests__/use-dialog.test.ts`；`library/static-verification.json`（聚焦/1458变体漂移/结构检查）。
- **E05**: `browser/business-nine-theme-matrix.json` + `browser/matrix-*.json/png`；`library/browser/observed-evidence-2026-09-22.json`明确旧候选历史24组；新候选结果只看 `library/browser/final-browser-2026-09-23.json`（24度量、4Popover、原生输入/实例/payload、嵌套scope与切肤；无效尝试保留不计通过）。同源真实autofill终态看E20；source旧paint缺失记录保留为修前失败，不作为终态。
- **E06**: 业务 `src/main.ts`、`src/assets/styles/tailwind.css`、`src/assets/styles/theme.module.css`、`src/theme/zx-theme-config.ts` 对照 `baseline/business.patch`；无机械改领域色/仿真声明。
- **E07**: 业务 `scripts/check-ui-standards.mjs`、`scripts/ui-standards-core.mjs`、`tests/ui-standards.test.ts`（混a/b controller反例已补）；`package.json`及仓根 `.github/workflows/ci.yml`、`.gitlab-ci.yml`。
- **E08**: ZXUI `docs/zh-CN/component/input.md`、`docs/en-US/component/input.md`、两语言 `input-number.md`、`docs/zh-CN/component/dialog.md`、`docs/zh-CN/guide/theme-tools.md`；业务根 `AGENTS.md`；`theme-surface-contract.md`锁定contract4.0.0/hash。
- **E09**: 业务 `src/utils/dict.ts`、`src/api/system/dict/data.ts:30`；`src/views/system/user/components/UserFormDialog.vue`；`src/utils/dict.test.ts`、`src/api/system/dict/data.test.ts`；`browser/matrix-default-light.json` radio0/1；`data-contract-fixes.md`。
- **E10**: 业务 `src/utils/generator/identity.ts`、`html.ts`、`js.ts`、`render.ts`；`tests/generator-form-contract.test.ts` + `tests/generator-form-runtime.test.ts`；`input-generator/implementation.md`；`input-migration.json`（184/68）。
- **E11**: ZXUI `packages/components/input/src/input-core.vue`、`input-tooltip.vue`、`packages/components/input-number/src/input-number-core.vue`、公开 `packages/zxui/input`/`input-number`；`packages/components/input/__tests__/input.test.tsx` 18项+number4项；`input-generator/popover-reference-fix.md`。business_theme_deployment 于2026-09-23独立复核最新根/attrs/事件/slot/expose，无新增阻断发现；对应其协调回报，本代理未将自审冒称独立。
- **E12**: 业务 `src/theme/zx-theme-packages.ts`、`zx-theme-config.ts`、`zx-theme-host.ts`、`src/App.tsx`、`vite/zxui-theme-packages.ts`；ZXUI `packages/zxui/theme-host/browser-core.ts`、`packages/components/theme-provider/__tests__/required-portal-binding.test.tsx`；公开 `docs/examples/dialog/public-form-contract.vue`。
- **E13**: `library/packed-receipt.json` rApuws/ZXUI3.0.0-next.0/sha085dfd40069635098fa97a8e29dd5764a9d5d4bd558492b5caf1df3e5453317a；Vue3.5.40、EP2.13.0，全部隔离realpath且逐包解析单实例；type/build/deployment exit0。
- **E14**: `browser/resumed/config-dict-fixed.json`、`role-assigned-fixed.json`、`role-unassigned-fixed.json`；业务 `tests/unit/components/MenuCollection.test.ts`、后端 `tests/unit/services/test_role_service.py` 和 `modules/system/tests/test_role_read_queries.py`。后端真实join行问题已修；business_theme_deployment非作者核对repository/PageUtil/服务两分页分支，与菜单controller collection及字典Map一起完成读码交叉复核，未发现新阻断问题。
- **E15**: `verification/peer-static-2026-09-23.log`：6文件21项/tsc/496文件门禁通过；主线程 `/private/tmp/zxui-final-business-build.log` build27.86s；旧全量lint/test失败仍保留，不套用局部全绿。
- **E16**: `dev-cache-isolation.md` + `verification/project-import-http-before.json`：两个Vite共缓存导致14个依赖504；fixture owner新增显式cacheDir，本审阅者未改业务页或simulation。

- **E17**: `browser-fixture-coverage.md` 及其linked browser产物；C/F真实组件17文件、G01生成SFC、FormGrid1100/650/320的3/2/1列及长标签/整行实测。部分C/F为旧候选，产物明确分界，不能代替生产route。
- **E18**: `business-theme-deployment.json` 已指向085dfd；tarball与installed1648文件逐字节0差异，旧build证据明确历史。
- **E19**: `project-detail-fill-fix.md`；ContentDetailWrap SFC/scoped Less编译通过，root B25真实复验内容869px/grid683px、克隆640px与required/输入/取消已通过，见browser/resumed/B25-clone-*.json/png。

- **E20**: `browser/resumed/public-source-fixed-autofill-light.json` / `public-source-fixed-autofill-dark.json` 与 `public-packed-autofill-light.json` / `public-packed-autofill-dark.json` 及同名PNG：两种输入实际autofill=true；主题色inset shadow覆盖浏览器autofill底色，textFill跟明暗。source公开style.css修复后重验通过；最终包仍085dfd。

- **E21**: `visual-baseline-comparison.md`；旧 `../zxui-theme-audit-2026-09-22/dialog-dom.json` / `dialog-current.png` 和新 `browser/matrix-industrial-blue-dark.json/png`。背景/label色一致，440×600/0radio变880×482/2radio。旧viewport未记录，不能作为同视口配对。

- **E22**: `browser-fixture-coverage.md`“真实窄视口N01”记录真实UserFormDialog组件在640×700、390×630的实际viewport、面板宽、单列、body滚动、页脚、Tab焦点及Cancel后回到opener；非整个业务shell移动端证明。旧user-final-narrow640未作窄屏证据。
- **E23**: `browser-route-coverage.md`最终B01–B13回写及链接原始JSON/PNG；补充`browser/resumed/B02-register-observe.json`、`B04-profile-inputs.json`、`B04-profile-password-observed.json`、`B04-avatar-dialog.json`、`B07-menu-icon-popover-fixed.json`。账号/密码只观察不提交，验证码按当前服务关闭状态处理，未穷举全部权限。
- **E24**: ZXUI `packages/components/hooks/use-dialog/__tests__/use-dialog.test.ts:34`选项响应与maskClosable映射，`:63`关闭guard拒绝/autoResetForm保持；这些5项已在`library/static-verification.json`重验。`required-portal-binding.test.tsx`真实loading mask有10项Host/Provider记录；`library/browser/final-browser-2026-09-23.json`notes明确Escape关闭真实dialog，空尺寸尝试只证明关闭而不计度量成功。系统UserForm未配置自定义dirty guard，默认遮罩禁关；未新增原不存在的行为验收要求。
- **E25**: `verification/closeout-results.json`与相邻`closeout-{types,standards,tests,lint,build}.log`：完整tsc、496文件0违规+14 tests、5文件42 tests、最后批ESLint0 errors/4 warnings、build26.78s均exit0；本人读取日志核对。`completion-report.md`及最新tasks/requirements记录用户范围、历史全量失败、局部残留测试数据、未发布/未提交/无生产部署边界。

## Spec Checklist

- R1.AC1: 当检查范围内的弹框调用时，不存在调用点硬编码像素或百分比宽度，包括 useDialog 选项和模板直接传值；其他 UI 元素宽度不受此规则约束。
- R1.AC2: 当使用业务表单弹框抽象时，1/2/3 列分别推导 md/lg/xl，当前 ZXUI 预设为 640/880/1120px；窄视口仍遵循组件库的视口约束。
- R1.AC3: 若表单需要覆盖推导结果，显式传合法 dialogSize 并注释理由；非表单弹框直接选预设，不强套 FormGrid。
- R1.AC4: 若表单弹框未声明可解析的尺寸，开发态有可见告警；业务 useFormDialog 显式提供 columns，不静默接受缺失尺寸。
- R2.AC1: 范围内弹框表单的 label-width 由一份业务布局策略生成 el-form 绑定，调用点不另写数值；纯布局 FormGrid 不代理表单 props。页内表单与搜索栏不强制改造。
- R2.AC2: FormGrid 只管响应式列数、横向 gap 与整行意图，横向间距来自同一布局策略；字段纵向节奏继续消费 ZXUI/EP density，不叠加另一套 row-gap 或控件尺寸。
- R2.AC3: 调用点只声明字段意图（如 full 占整行），不手写表单字段 span 几何值。
- R2.AC4: 业务继续将真实 el-form ref 交给 useDialog，不新增 FormInstance 转发、内部 ref 取出或 any 断言；校验、分步校验、重置、错误滚动/焦点和关闭重开行为保持。
- R2.AC5: columns 只有一个输入源，dialogSize 与 FormGrid 绑定从其派生；窄容器自动降列且 full 字段保持整行。策略控制初始标签宽度/横向间距与降列规则，长标签处理统一，不形成逐字段尺寸例外。
- R3.AC1: 范围内可执行 Vue 模板的精确 el-dialog 标签归零；生成器输出模板单列检查，文档和注释不作为页面实例。
- R3.AC2: 迁移当次清单中所有范围内 el-dialog，包括会生成该标签的业务模板；不使用历史 19/17 数字替代清单验收。
- R3.AC3: 迁移后关闭、ESC、遮罩点击、挂载、校验、loading 和脏数据守卫与原行为等价。
- R4.AC1: 范围内弹框不再用百分比或 vh 的 height 固定实际高度；FormDialog 不接受直接 height。
- R4.AC2: 确需限高时使用经过验证的最大高度约束并保持正文可滚动；不得向 useDialog 传入当前未支持的 maxHeight 选项并误认为生效，具体接口见 design.md。
- R5.AC1: 在 ZXUI 主题下，form/form-item/radio/checkbox 的标签、必填、错误、禁用、选中及焦点状态正确消费主题。直接 alias 或已验证的全局变量继承均有效；只对实际缺失的映射/结构样式补库能力，不要求为每种组件强造专用 token。
- R5.AC2: 通用输入主题处理浏览器 autofill 的背景与文字，使其随主题明暗变化；覆盖原生 el-input 和包装后的 zx-input，不能只在登录页打补丁。
- R5.AC3: 让 EP adapter/结构样式消费已有 density 度量，默认 size 下三档产生可测量的控件高度或纵向间距差异；保留核心 density 轴。保留 EP 原有有效 size 解析链（组件、已有 fallback、FormItem/Form、Provider、默认），density 只调整最终有效 size 下的主题度量，不改写 size 或其继承关系；度量表与代码统一，不让业务自行换算。
- R5.AC4: useDialog 开发态检测传入 formRef 但没有显式 dialogSize/width 的调用并告警；width 是组件库合法通用接口，但业务受 R1 约束。生产态不刷告警，不修改全部 ZxDialog 的默认档位。
- R6.AC1: 验证通过后，删除 src/main.ts 对 element-plus/theme-chalk/dark/css-vars.css 的引入，保留 Element Plus 必需的基础结构样式。
- R6.AC2: 先清理范围内与 ZXUI 对抗的业务主色写入及反向 alias，再删除 clearBusinessPrimaryOverrides() 及调用；领域语义色、图像和用户正文颜色不机械重写。
- R6.AC3: 上述删除依赖 R5 真实状态与明暗验证通过，并记录删除前后的计算样式与截图；不能仅因标签正常或专用 token 数量变化就判通过。全局主题改动可能影响排除模块，但不因此扩展仿真实施/验收范围，也不声称仿真已验证。
- R7.AC1: 新增 scripts/check-ui-standards.mjs，支持 --strict、--format=summary|json|markdown，违规时 exit 1，并输出范围与文件位置。
- R7.AC2: 不产出 baseline/allowlist；规则对约定范围一次性成立，仿真模块按明确范围排除，不能以“尚未迁完”新增文件豁免。
- R7.AC3: 迁移完成后接入 package.json、.github/workflows/ci.yml 与 .gitlab-ci.yml。
- R7.AC4: 覆盖 R1–R4 可静态检测项，复用 Vue/TS 解析器，检查明确的本地写法与统一入口；复杂动态配置须收敛入口并受类型/运行时约束，不实现通用跨文件数据流分析，也不静默跳过未知写法。
- R7.AC5: 生成器预览、配置、默认数据和导出共享组件身份约定；生成后的 SFC 与源码使用同一检查核心。范围内新增对 --el-* 或 --zx-* 核心主题值的竞争写入应被窄门禁拦截，不将全部业务色值视为违规。
- R8.AC1: ZXUI 文档区分主题覆盖与行为封装，说明实际 props/events/slots/expose、density/size、scope/浮层及输入职责；提供可独立消费的公开表单示例和旧输入语义迁移说明，不把 RuoYi 布局 CSS 或私有路径复制为标准接入方案。
- R8.AC2: 业务 AGENTS.md 写明范围内表单弹框的统一写法与仿真排除范围，并指向本 spec；不把业务 label-width/gutter 数值规定为所有 ZXUI 消费者的标准。
- R9.AC1: 使用用户已授权的浏览器自动化在真实业务页面验证，记录浏览器和环境；AdsPower 可用，本次已获授权的内置浏览器证据也有效。docs/单测不能代替真实业务验收；不验证仿真。
- R9.AC2: 先沿状态选项未渲染的证据排查字典与响应适配，明确根因及归属并修复；恢复选项后再验证主题可见性，不把“0 个 radio”写成已确认字典为空。
- R9.AC3: 留存同页面、同主题、同视口的改前/改后截图及关键 DOM/计算样式，明确哪些仅完成基线、哪些已终验。
- R10.AC1: 范围内 Vue 模板的精确 el-input 标签及对应生成器输出全部迁为 zx-input；不匹配 el-input-number，不以旧前缀数量作为完成依据。
- R10.AC2: R11 完成并源码直连验证通过后，迁移清单中的 prefix/suffix/prepend/append 消费者全部迁移，不留插槽例外或白名单。
- R10.AC3: 所有 textarea、number、search 及动态 type 调用逐项确认模型值类型、属性、事件和渲染语义；若现有包装行为不兼容，先修正 ZXUI 契约，不能为追求标签归零静默改变业务行为。
- R10.AC4: 迁移完成后启用 no-raw-el-input 门禁，对约定范围一次性成立，无存量豁免。
- R10.AC5: 迁移后的真实业务页面逐页验证，包括 slots、输入/清空/焦点、实例方法和 flex 布局；不能只凭编译通过验收。
- R10.AC6: 不迁移 el-select 或 el-input-number；发现其他输入组件问题单独记录，不扩大本次批量替换范围。
- R11.AC1: 在 tooltip 与非 tooltip 两个分支均转发 prefix/suffix/prepend/append 到底层 ElInput，保留插槽内容与参数。
- R11.AC2: 最终 ZxInput 的 type=search 保留原生输入语义，不再隐式注入搜索按钮；消费者 append 正常透传。旧增强搜索按显式组件/插槽组合迁移，不能继续依靠 type 同时选择 UI 行为。此条替代旧版“保留内建 append 并定优先级”的目标。
- R11.AC3: ZxInput 公开 expose 对齐实际 ElInput 能力：focus/blur/select/clear/input/textarea/textareaStyle，保持参数、返回值和响应性；不额外暴露任意底层组件状态包。数值组件按自己的契约暴露能力。
- R11.AC4: 清除 input-core.vue 的 ::icon 错误和职责拆分后的无效搜索分支；仍存在的搜索按钮图标绑定有效，不将移除的旧分支遗留在任一 tooltip 路径。
- R11.AC5: 增加聚焦回归锁定 slots、tooltip 两种路径、expose、原生 number/search 语义及拆出的数值/搜索消费行为；复用同一代表样板验证源码与包产物，不为每个业务点复制测试。
- R11.AC6: 文档分别列 ZxInput、数值输入及增强搜索的实际能力和迁移对应关系；不继续笼统宣称一个组件完整继承两类底层组件。文档收窄不能替代在用能力修复，主版本影响按 R13 交付。
- R11.AC7: 在真实业务中验证两层 wrapper 与 width: 100% 对搜索栏、flex 行、前后缀及 textarea 的影响，必要的通用修复在 ZXUI 完成。
- R11.AC8: ZxInput 固定消费 ElInput，type 专用于原生输入类型，不再把 number 转成 ElInputNumber；v-model 单一所有者，attrs/事件准确到达输入控件，name/id/aria、禁用、键盘、焦点与输入法组合输入行为保持，不增加 native/legacy 等永久兼容开关。
- R11.AC9: 将已有数值步进能力承接为小型 ZxInputNumber 并公开导出，迁移已知库内旧消费者；增强搜索按实际需求复用 ZxSearch 或显式 append 组合，核对 trim、清空触发与事件载荷，不机械替换。业务现有 el-input-number 仍不批量迁移。
- R12.AC1: 业务仅有一份主题登记，由其派生选择器、Host 注册与部署包列表；偏好状态经一个入口进入 Host/Provider，DOM 属性为投影而非另一套可写状态，不在页面拼 variant 字符串或写主题值。
- R12.AC2: 构建端复用 emitThemeDeployment 和主题包公开 exports，浏览器复用 createThemeDeploymentResolver 与既有 Host/Provider；最终运行时不遍历 generated/、不维护私有路径转换、不自行补写缺失库类型。源码 alias 限于显式开发工具边界。
- R12.AC3: 声明的主题包及 CSS/manifest 属于同一部署输出，安装后缺资产不能静默少一个主题；修正公开导出/类型和依赖声明，新增一个主题只需一处登记加正常依赖，不复制多份 ID 数组。
- R12.AC4: 弹框及内部二级浮层跟随发起它们的最近 scope，验证嵌套 scope、打开期间换肤、关闭重开；global body mirrored 只用于已确认的兼容边界，不能代替嵌套归属或跨 scope 污染验证。
- R12.AC5: 在既有库示例/消费 fixture 中提供一个不加载 RuoYi 修补 CSS 的表单弹框样板，与真实业务共用公开契约；若两边表现不同，记录归属并在正确层修复，不在业务增加另一套主题映射。
- R13.AC1: 输入职责调整明确为下一主版本或其本地预发布候选，记录旧→新用法及行为差异；不得以现有 2.x 兼容补丁发布。已知库内消费者和示例迁移完成，外部消费者不能假定已升级。
- R13.AC2: 用真实本地 tarball、公开 imports 和部署资产完成一次隔离安装验证，禁 source alias/workspace fallback；复用既有 packed 工具，只扩展本次相关样板，不先发布 npm，也不把正式发布/外部升级作为 Cursor 的前置。
- R13.AC3: 同一代表样板通过源码和打包两种模式：类型、构建、slots/expose、明暗、density、嵌套弹框/浮层以及 autofill。记录实际 Vue/EP/ZXUI 解析版本、包哈希与产物路径；不通过本地类型补丁或重复运行时掩盖 peer/导出缺口。
- R13.AC4: 完成声明需包含业务真实页面、库通用能力和可安装产物三类证据；明确未完成项及外部升级要求。本 spec 完成不等于已发布 npm，也不等于仿真已验证。
- D1: 职责分层与范围：库负责通用行为/主题，业务负责数据/薄布局；仿真及专用组件排除，无baseline/allowlist。
- D2: FormDialog目录只有策略、useFormDialog、纯布局FormGrid，不新增FormField/FormModalHandle/表单实例代理。
- D3: useFormDialog不复制visible/model/dirty/loading/提交；原生ElForm ref与命令接口保持。
- D4: 唯一必填columns生成dialogSize/formProps/layoutProps；业务100px标签/20pxgap，目标1/2/3列映射md/lg/xl。
- D5: FormGrid只响应式网格/横gap/data-form-full，无row-gap；长标签与窄容器降列规则统一，实际样板验证。
- D6: FormDialog类型排除width/height，入口诊断并剔除非法动态值；合法尺寸例外有理由。
- D7: 普通弹框按内容高度与库max-height，必要dialogStyle.maxHeight，不支持顶层maxHeight或style.height绕过。
- D8: 主题缺口在库源/生成层修复；全局alias继承有效；业务不重写库变量，清掉通用autofill重复。
- D9: EP有效size链保留；density仅度量，small/default/large统一表，Form/FormItem/Provider边界且不双缩放。
- D10: 最近Provider拥有dialog及二级浮层；打开中切换/重开/嵌套scope均验证；body mirrored仅兼容。
- D11: useDialog开发formRef缺size/width告警，生产不刷且通用small不变。
- D12: ZxInput固定ElInput，原生type，四slots双tooltip路径，expose七能力；attrs目标/vmodel单所有者/IME一次。
- D13: ZxInputNumber小组件承接数值步进；旧搜索显式组合保持trim/clear/载荷；不改ZxSearch或业务ElInputNumber。
- D14: 破坏API按下一主版本候选交付，旧search事件和外部升级边界说明。
- D15: 主题catalog单源派生UI/Host/build；登记缺依赖/manifest报错，正常依赖明确。
- D16: 构建使用公开emitThemeDeployment，浏览器公开resolver，部署独占目录及base路径正确；无runtime generated猜测/类型补丁。
- D17: 偏好一个入口进入Host/Provider，document属性只投影；不新增density UI或第二主题系统。
- D18: 页面壳/生成器消费公开surface/token，不添业务翻译层；experimental surface身份锁定。
- D19: 所有非仿真可执行孤立候选仍受门禁；NodeEditDrawer/Dag/协议模板共享消费者不整块排除。
- D20: 生成器有限身份集中、旧设计可读取编辑预览导出；新dialog输出完整imports/同组合/full意图。
- D21: 同代表生成SFC执行生成→解析→预览/打开，源码及产物共用checker。
- D22: 薄静态入口三种format/strict/exit1/范围位置，无baseline；仅明确本地Vue/TS形状，未知配置不静默跳过。
- D23: 数据沿statusOptions→字典/缓存/HTTP定位，不伪造字典，不预设dept同因，无数据库迁移。
- D24: 安全：已授权本地浏览器、截图不含token、测试提交清理；隔离tarball不registry发布或其他业务lockfile。
- D25: 顺序：库input/主题公开能力先满足，业务input最后批次；任务16在14前；不等正式发布或外部业务升级。
- D26: 三类证据分离；同代表公开样板source+packed，无RuoYiCSS，无alias/fallback，真实版本/hash/路径/单peer。
- D27: 复用既有packed-install/hosted-packed、相关生成漂移检查，不用旧widget通过抵扣表单。
- D28: 真实交互包含键盘开关/焦点返回、IME、校验失败、重开、长内容、真实autofill；执行相关lint/type/test/ui门禁。
- T1: 修复状态选项数据链路并补齐样板基线
- T1.1: 复用现有添加用户证据：440×600、标签跟主题、radio input 为 0；沿 statusOptions、字典请求/缓存及响应适配确认具体根因并修复，记录业务/库归属。
- T1.2: 不硬编码字典兜底；deptList.filter 只作为相邻契约线索，不预设同因。恢复选项后检查原提交值与主题可见性。
- T1.3: 重扫库存和非仿真消费者，保存同页面/主题/视口的截图及 DOM，记录浏览器和真实依赖版本；未触达候选不算验收。
- T2: 建立业务薄布局策略与纯布局 FormGrid（依赖 1）
- T2.1: 一份布局策略管理 columns→dialogSize、label-width、横向 gap 与窄容器降列。useFormDialog 从唯一 columns 输入返回 dialogProps/events 与 formProps/layoutProps，不复制模型、提交或 dirty 状态。
- T2.2: 保留原生 el-form ref 与 el-form-item。FormGrid 只处理 CSS Grid 和 data-form-full，不包装 ElForm、不新增 FormField、不代理 FormInstance，也不新增 FormModalHandle。
- T2.3: 不增加 grid row-gap，纵向节奏由库主题/density 控制；长标签与降列规则在一个策略处维护。
- T2.4: 类型排除 width/height；统一入口对非法动态值诊断并剔除。保留合法预设例外及原 useDialog 回调语义。
- T2.5: 通过既有类型检查与实际校验/重置/分步/错误滚动/重开验证；不为纯布局数值新增一批单测。
- T3: 迁移 UserFormDialog 样板（依赖 1、2）
- T3.1: columns: 2 驱动同一尺寸/表单/布局绑定，原生 ElFormItem 声明字段与整行意图，删除 height: '60%'。
- T3.2: 核对正常视口 lg、窄容器降列、长标签、间距、错误滚动、状态选项、重开与提交；修正已有 placeholder 一致性。
- T3.3: 默认限高直接沿用库，需要时使用 dialogStyle.maxHeight，不传无效顶层 maxHeight。
- T3.4: 留存可对比证据，布局样板通过才复制到其他页面；不抢做最终输入框批量替换。
- T4: 迁移范围内其他表单弹框（依赖 3）
- T4.1: 以当前清单迁移项目、部门、通知、设备/端口、克隆、导入等普通表单；不包含仿真专用弹框。
- T4.2: 使用同一业务策略、原生表单与 FormGrid，去掉字段手写 label-width/gutter/span 和固定高度；不改内部表格/编辑器布局。
- T4.3: 逐页核对条件字段、校验、loading、脏数据守卫、关闭重开和提交值，保留范围内未完成项，不加 allowlist。
- T5: 统一范围内非表单弹框尺寸（依赖 3）
- T5.1: 版本预览/详情、DagMatrix、操作日志、生成代码预览等按内容选预设，去掉硬编码宽度及百分比/vh 固定 height。
- T5.2: 依赖库默认限高，必要时用 dialogStyle.maxHeight；不强套 FormGrid。
- T5.3: 核对长内容、窄视口、关闭、全屏和挂载等既有行为，不扩展仿真验收。
- T6: 原生 dialog 与生成器表单源头收口（依赖 4、5）
- T6.1: 初始 18 个/16 文件仅为非仿真目录候选；按当次确认清单迁移 ZxDialog，并验证 ESC、遮罩、校验、loading、挂载及脏数据守卫。
- T6.2: 生成器 dialog 输出改用相同表单组合，完整输出 imports/注册/策略绑定；不把生成字符串当真实页面实例。
- T6.3: 整理现有 html/config/drawingDefalut/render 的有限组件身份对应，为后续 input 迁移准备一个统一来源，不再并行维护预览与导出的不同 tag。
- T6.4: 旧设计配置继续可读取、编辑、预览、导出；代表生成 SFC 解析与页面打开通过，源头不能重新生成旧布局。
- T7: **[ZXUI]** 修实证主题缺口及通用 autofill
- T7.1: 复用公开 API 建立一个不加载 RuoYi 补丁的表单弹框代表样板，同时用于后续源码与打包消费检查。
- T7.2: 核对全局 alias、局部 scope 与标签/必填/错误/禁用/选中/焦点；已有继承不重复造 token，业务覆盖在业务清理，通用缺口在库源文件修复并生成。
- T7.3: 通用 autofill 验证背景/文字明暗，覆盖 ElInput 与最终 ZxInput；不得只用登录页覆盖当库能力。
- T7.4: 真实业务源码直连对照库样板，保存九主题明暗的代表表单证据；不复制整套全排列测试。
- T8: **[ZXUI]** EP density、scope 与尺寸告警（衔接 7）
- T8.1: 保留核心 density 轴，补 EP 度量消费；默认 size 测量三档差异，保留 EP 原有有效 size 解析链（组件、既有 fallback、FormItem/Form、Provider、默认），验证表单级尺寸继承；density 只作用于最终有效 size 下的主题度量，不改写继承链或两次缩放。
- T8.2: 复用已有 scope/Portal 能力验证嵌套弹框和内部二级浮层、打开中换肤、关闭重开；不能用 body mirrored 替代局部 scope 归属。
- T8.3: useDialog 开发态对 formRef 无显式 dialogSize/width 告警，业务 wrapper 推导后不误报，不修改所有 ZxDialog 的 small 默认值。
- T9: 清理业务重复主题来源（依赖 4–8、15 与覆盖证据）
- T9.1: 清理 theme.module.css/tailwind.css 等反向 alias 与主色竞争写入，保留领域色和用户正文色；现有页面壳直接消费公开 surface/token，不增加业务映射层。
- T9.2: 状态/明暗覆盖通过后删除 EP dark/css-vars.css、clearBusinessPrimaryOverrides 及调用，确保旧写入不会重新覆盖。
- T9.3: 保留 EP 必需基础样式和正确加载顺序；库 autofill 已成立时移除重复的业务处理。
- T9.4: 对比实际非仿真页面的删除前后颜色，记录影响边界，不声称仿真通过。
- T10: 接入薄而严格的门禁（依赖 3–6、9、15）
- T10.1: 新增 check-ui-standards.mjs 薄入口，复用 Vue/TS 解析器和一个模板检查核心；源码与生成后 SFC 共用。
- T10.2: 只检查明确的模板/局部对象/统一入口。复杂间接配置改为受类型和运行时校验的入口，不做通用全程序分析，不静默跳过未知形状。
- T10.3: 覆盖 dialog 尺寸/高度绕过、表单策略、竞争主题写入和私有主题路径；不要误报页内布局、el-input-number、领域色或文档注释。
- T10.4: 无 baseline/allowlist，少量成组正反例防误报/漏报；存量通过再接入 package.json、GitHub/GitLab CI。
- T10.5: no-raw-el-input 待任务 13 完成启用；不因规则尚未启用标记输入迁移完成。
- T11: 完善公开示例和迁移说明（依赖 9、10、12、15）
- T11.1: **[ZXUI]** 写明原生输入、数值步进、增强搜索的职责和旧→新迁移差异，明确下一主版本候选边界与外部升级要求。
- T11.2: **[ZXUI]** docs 示例使用公开 Host/Provider/部署资产，说明 density/size 与 scope/Portal，不能要求其他业务复制 RuoYi 私有路径、类型补丁或 CSS。
- T11.3: 业务 AGENTS.md 写薄表单组合、主题唯一入口和仿真排除范围，指向 spec；业务标签宽度/gap 不成为全库规定。
- T11.4: 生成器示例与手写页面采用同一组合，库/业务契约说明与最终 Cursor 迁移目标一致。
- T12: **[ZXUI]** 拆清输入职责并完成公开契约（可与表单/主题任务并行）
- T12.1: 先记录下一主版本目标和旧行为对应表，不在现有 2.x 补丁中偷改。ZxInput 固定 ElInput，type 只表示原生输入类型，不新增永久 native/legacy 路由开关。
- T12.2: tooltip 两种路径透传四类 slots 与参数；expose 对齐 ElInput 的已承诺方法/属性，保持响应性，不暴露任意内部状态包。
- T12.3: 移除 number 路由和隐式 search append 分支，一并清除 ::icon。数值步进能力承接为小型 ZxInputNumber，补齐必要公开入口、类型、样式和库内已知调用迁移；不批量迁业务 el-input-number。
- T12.4: 旧增强搜索按需求复用 ZxSearch 或显式 append 按钮组合；核对 trim、清空触发、string 与对象载荷，保持已知消费者的业务行为，不重构所有搜索栏。
- T12.5: 统一 v-model 所有者与属性/事件目标；聚焦验证输入法组合输入、输入/清空事件只触发一次、name/id/aria、禁用、焦点和 flex。
- T12.6: 更新库内已知消费者与 docs 示例；聚焦回归覆盖真实契约，不按184个业务点复制测试。复用任务 7 的公开样板，源码直连验证业务兼容后放行。
- T13: Cursor 最后批量迁移 el-input（依赖 1–12、15）
- T13.1: 重新核对候选184个/68文件，静态textarea28个、17个input的18个slots为重叠分类，不按旧257前缀数替换。
- T13.2: 精确替换 el-input 为最终 ZxInput，number/search/动态type按已通过的原生语义方案逐项确认；不替换 el-input-number 或 el-select。
- T13.3: 同步生成器统一组件身份及配置/预览/输出，转换2处legacy append和生成器旧slot语法；已有设计配置读取与重新导出仍正常。
- T13.4: 核对 slots、实例方法、空值与事件、布局及动态类型，范围内一次迁完，不给复杂调用加白名单。
- T13.5: 启用 no-raw-el-input，共用模板检查器核验生成输出，逐页真实验证。前置是库本地候选通过，不是正式发布或所有外部消费者升级。
- T14: 三类证据终验与状态回写（依赖 16）
- T14.1: 汇总库公开能力、真实业务页面、本地可安装产物证据，分别说明证明范围，不能拿导航旧矩阵或widget协议通过抵扣表单验收。
- T14.2: 逐页核对数据、尺寸、降列、滚动、校验、焦点、重开、输入及明暗；代表表单覆盖九主题明暗与代表主题三档density，异常再扩展，不做全排列。
- T14.3: 运行业务相关 lint/type-check/test:run/ui:standards 及 ZXUI 相关聚焦回归、既有生成/漂移检查；记录实际结果，不用新增测试数量代替质量。
- T14.4: 核对全部验收项后更新状态；未触达候选、外部升级要求及包交付限制明确记录。完成不代表已发布 npm，不代表仿真已验收。
- T15: 统一公开主题接入与资产交付（9、10、11、13 的前置）
- T15.1: 将现有主题选择器、Host和Vite包列表改为从一个登记源派生；登记依赖显式存在，缺包/manifest不可静默略过。
- T15.2: 构建端复用 emitThemeDeployment，浏览器用 createThemeDeploymentResolver；manifest/CSS共同交付，核对base路径，构建工具不进浏览器。
- T15.3: 移除业务运行时 generated glob、export→私有路径转换和 portalContainerScope 类型补丁；公开类型缺口在ZXUI补齐，开发alias只在工具边界保留。
- T15.4: 将偏好更新收敛为一个入口交Host/Provider，document属性为投影，去掉页面拼variant与重复状态写入；不新增另一套主题框架或必须的density设置UI。
- T15.5: 实际业务验证登记的九主题、登录/主框架/表单及二级浮层；公开样板无需RuoYi修补CSS，发现差异按归属修复。
- T16: 验证本地候选包可供其他业务安装（依赖 13）
- T16.1: 用本轮源码生成真实本地tarball和主题部署资产，记录包版本、哈希、实际解析路径及Vue/EP/ZXUI版本；先核对peer契约，不靠声明合并或重复运行时掩盖问题。
- T16.2: 复用已有packed-install/hosted-packed工具的安装/构建/浏览器能力，在隔离临时目录运行任务7/12的同一代表表单，禁止source alias/workspace fallback。
- T16.3: 核对公开imports/类型/样式及slots/expose/native类型、代表主题明暗、三档density、嵌套scope/二级浮层和真实autofill；无需在包fixture重复全部业务页面。
- T16.4: 没有正式npm发布、外部仓改动或外部全部升级前置；输出本地主版本候选消费证据及外部升级说明，交任务14终验。

## Alignment Table

status为原始范围覆盖记录；currentDisposition为最终用户范围适用判断。withdrawn-by-user不是通过；historical-limitation是已披露限制。

| ID | Type | Spec Item | Status | Current disposition | Evidence | Gap / Scope boundary |
| --- | --- | --- | --- | --- | --- | --- |
| R1.AC1 | R | 当检查范围内的弹框调用时，不存在调用点硬编码像素或百分比宽度，包括 useDialog 选项和模板直接传值；其他 UI 元素宽度不受此规则约束。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts}; scripts/ui-standards-core.mjs; ZXUI dialog/src/props.ts [E01] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R1.AC2 | R | 当使用业务表单弹框抽象时，1/2/3 列分别推导 md/lg/xl，当前 ZXUI 预设为 640/880/1120px；窄视口仍遵循组件库的视口约束。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts}; scripts/ui-standards-core.mjs; ZXUI dialog/src/props.ts；当前范围收尾：E01, E17, E22。 [E01, E17, E22] | N01真实UserFormDialog在640×700与390×630实际视口分别607.986/357.986宽，单列；1920恢复后880宽双列。旧narrow640文件不计窄屏证据。 |
| R1.AC3 | R | 若表单需要覆盖推导结果，显式传合法 dialogSize 并注释理由；非表单弹框直接选预设，不强套 FormGrid。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts}; scripts/ui-standards-core.mjs; ZXUI dialog/src/props.ts [E01] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R1.AC4 | R | 若表单弹框未声明可解析的尺寸，开发态有可见告警；业务 useFormDialog 显式提供 columns，不静默接受缺失尺寸。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts}; scripts/ui-standards-core.mjs; ZXUI dialog/src/props.ts [E01] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R2.AC1 | R | 范围内弹框表单的 label-width 由一份业务布局策略生成 el-form 绑定，调用点不另写数值；纯布局 FormGrid 不代理表单 props。页内表单与搜索栏不强制改造。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R2.AC2 | R | FormGrid 只管响应式列数、横向 gap 与整行意图，横向间距来自同一布局策略；字段纵向节奏继续消费 ZXUI/EP density，不叠加另一套 row-gap 或控件尺寸。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R2.AC3 | R | 调用点只声明字段意图（如 full 占整行），不手写表单字段 span 几何值。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R2.AC4 | R | 业务继续将真实 el-form ref 交给 useDialog，不新增 FormInstance 转发、内部 ref 取出或 any 断言；校验、分步校验、重置、错误滚动/焦点和关闭重开行为保持。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs；当前范围收尾：E01, E02, E22, E24。 [E01, E02, E22, E24] | 原生FormInstance运行回归、UserForm必填与焦点、N01取消恢复opener、18次主题开关；分步通用契约已验证，系统页面无分步配置。 |
| R2.AC5 | R | columns 只有一个输入源，dialogSize 与 FormGrid 绑定从其派生；窄容器自动降列且 full 字段保持整行。策略控制初始标签宽度/横向间距与降列规则，长标签处理统一，不形成逐字段尺寸例外。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs; 真实同一useFormDialog columns:3 / FormGrid宿主1100→650→320，列数3→2→1，整行宽度等于宿主、长标签换行且scrollWidth无溢出。 [E01, E02, E17] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R3.AC1 | R | 范围内可执行 Vue 模板的精确 el-dialog 标签归零；生成器输出模板单列检查，文档和注释不作为页面实例。 | covered | covered | scripts/check-ui-standards.mjs: 496 files/0 violations; current migration inventory; two ExportDialog initial-open fix [E03, E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R3.AC2 | R | 迁移当次清单中所有范围内 el-dialog，包括会生成该标签的业务模板；不使用历史 19/17 数字替代清单验收。 | covered | covered | scripts/check-ui-standards.mjs: 496 files/0 violations; current migration inventory; two ExportDialog initial-open fix [E03, E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R3.AC3 | R | 迁移后关闭、ESC、遮罩点击、挂载、校验、loading 和脏数据守卫与原行为等价。 | partial | covered | scripts/check-ui-standards.mjs: 496 files/0 violations; current migration inventory; two ExportDialog initial-open fix；当前范围收尾：E22, E24。 [E03, E07, E22, E24] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 当前系统入口的挂载/校验/关闭重开有实测；UserForm无自定义dirty guard，useDialog默认禁遮罩关闭，已有guard/选项与真实loading契约测试；公开样板记录Escape关闭。没有为每页面凭空增加dirty功能。 |
| R4.AC1 | R | 范围内弹框不再用百分比或 vh 的 height 固定实际高度；FormDialog 不接受直接 height。 | covered | covered | src/components/ui/FormDialog/index.ts sanitizer; scripts/ui-standards-core.mjs; ZXUI dialog structural max-height [E01, E04] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R4.AC2 | R | 确需限高时使用经过验证的最大高度约束并保持正文可滚动；不得向 useDialog 传入当前未支持的 maxHeight 选项并误认为生效，具体接口见 design.md。 | covered | covered | src/components/ui/FormDialog/index.ts sanitizer; scripts/ui-standards-core.mjs; ZXUI dialog structural max-height；当前范围收尾：E01, E04, E22。 [E01, E04, E22] | N01实际body 524/604及454/604可滚动，底部备注聚焦触发scrollTop80且footer留在视口；门禁拦截尺寸旁路。 |
| R5.AC1 | R | 在 ZXUI 主题下，form/form-item/radio/checkbox 的标签、必填、错误、禁用、选中及焦点状态正确消费主题。直接 alias 或已验证的全局变量继承均有效；只对实际缺失的映射/结构样式补库能力，不要求为每种组件强造专用 token。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; 本人查看新候选packed明暗截图及24组computed：label/required/selected/disabled/check/radio清晰，required校验与focus实录；对应adapter继承和结构样式已读。 [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R5.AC2 | R | 通用输入主题处理浏览器 autofill 的背景与文字，使其随主题明暗变化；覆盖原生 el-input 和包装后的 zx-input，不能只在登录页打补丁。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; 最终同源public-source-fixed-autofill-{light,dark}与public-packed-autofill-{light,dark}：raw ElInput与tooltip ZxInput均实际:-webkit-autofill=true，inset shadow与textFill匹配明暗themeSurface/themeText。source修复只在play公开style.css入口，不改变085候选。 [E04, E05, E20] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R5.AC3 | R | 让 EP adapter/结构样式消费已有 density 度量，默认 size 下三档产生可测量的控件高度或纵向间距差异；保留核心 density 轴。保留 EP 原有有效 size 解析链（组件、已有 fallback、FormItem/Form、Provider、默认），density 只调整最终有效 size 下的主题度量，不改写 size 或其继承关系；度量表与代码统一，不让业务自行换算。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; library/browser/observed-evidence-2026-09-22.json 24组旧候选度量（明确历史）; 新085dfd source/packed × default/defense-green × 明暗 × 三density共24组；default28/32/36、defense26/30/34，small/large与Form继承符合统一表。4条过渡小数已有同key settled复核，不能采用关窗后null无效尝试。 [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R5.AC4 | R | useDialog 开发态检测传入 formRef 但没有显式 dialogSize/width 的调用并告警；width 是组件库合法通用接口，但业务受 R1 约束。生产态不刷告警，不修改全部 ZxDialog 的默认档位。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R6.AC1 | R | 验证通过后，删除 src/main.ts 对 element-plus/theme-chalk/dark/css-vars.css 的引入，保留 Element Plus 必需的基础结构样式。 | covered | covered | src/main.ts; src/assets/styles/{tailwind.css,theme.module.css}; src/theme/zx-theme-config.ts; docs/reports/.../baseline/business.patch [E06, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R6.AC2 | R | 先清理范围内与 ZXUI 对抗的业务主色写入及反向 alias，再删除 clearBusinessPrimaryOverrides() 及调用；领域语义色、图像和用户正文颜色不机械重写。 | covered | covered | src/main.ts; src/assets/styles/{tailwind.css,theme.module.css}; src/theme/zx-theme-config.ts; docs/reports/.../baseline/business.patch [E06, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R6.AC3 | R | 上述删除依赖 R5 真实状态与明暗验证通过，并记录删除前后的计算样式与截图；不能仅因标签正常或专用 token 数量变化就判通过。全局主题改动可能影响排除模块，但不因此扩展仿真实施/验收范围，也不声称仿真已验证。 | covered | covered | src/main.ts; src/assets/styles/{tailwind.css,theme.module.css}; src/theme/zx-theme-config.ts; docs/reports/.../baseline/business.patch; 最终R5状态/明暗及通用autofill已证；旧添加用户工厂蓝深色截图+计算色与终态相互对照，删除前后背景/标签色不变；未将仿真纳入。R9.AC3额外同视口配对限制另列。 [E06, E05, E21] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R7.AC1 | R | 新增 scripts/check-ui-standards.mjs，支持 --strict、--format=summary\|json\|markdown，违规时 exit 1，并输出范围与文件位置。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R7.AC2 | R | 不产出 baseline/allowlist；规则对约定范围一次性成立，仿真模块按明确范围排除，不能以“尚未迁完”新增文件豁免。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R7.AC3 | R | 迁移完成后接入 package.json、.github/workflows/ci.yml 与 .gitlab-ci.yml。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R7.AC4 | R | 覆盖 R1–R4 可静态检测项，复用 Vue/TS 解析器，检查明确的本地写法与统一入口；复杂动态配置须收敛入口并受类型/运行时约束，不实现通用跨文件数据流分析，也不静默跳过未知写法。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R7.AC5 | R | 生成器预览、配置、默认数据和导出共享组件身份约定；生成后的 SFC 与源码使用同一检查核心。范围内新增对 --el-* 或 --zx-* 核心主题值的竞争写入应被窄门禁拦截，不将全部业务色值视为违规。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R8.AC1 | R | ZXUI 文档区分主题覆盖与行为封装，说明实际 props/events/slots/expose、density/size、scope/浮层及输入职责；提供可独立消费的公开表单示例和旧输入语义迁移说明，不把 RuoYi 布局 CSS 或私有路径复制为标准接入方案。 | covered | covered | ZXUI docs/{zh-CN,en-US}/component/input*.md; docs/zh-CN/{component/dialog,guide/theme-tools}.md; business AGENTS.md:90 [E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R8.AC2 | R | 业务 AGENTS.md 写明范围内表单弹框的统一写法与仿真排除范围，并指向本 spec；不把业务 label-width/gutter 数值规定为所有 ZXUI 消费者的标准。 | covered | covered | ZXUI docs/{zh-CN,en-US}/component/input*.md; docs/zh-CN/{component/dialog,guide/theme-tools}.md; business AGENTS.md:90 [E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R9.AC1 | R | 使用用户已授权的浏览器自动化在真实业务页面验证，记录浏览器和环境；AdsPower 可用，本次已获授权的内置浏览器证据也有效。docs/单测不能代替真实业务验收；不验证仿真。 | covered | covered | src/utils/dict.ts:39; src/utils/dict.test.ts; api/system/dict/data.ts:31; UserFormDialog.vue:195; browser evidence pending; 主线程已授权IAB真实localhost业务操作，九主题18轮及resumed真实路由DOM/截图已持久化；不是docs替代。 [E09, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R9.AC2 | R | 先沿状态选项未渲染的证据排查字典与响应适配，明确根因及归属并修复；恢复选项后再验证主题可见性，不把“0 个 radio”写成已确认字典为空。 | covered | covered | dict.ts消费HttpCollection.items；2测试通过；browser/user-default-dark.json与user-industrial-blue-dark.json实有0/1两个radio、原字符串提交值保持；截图已人工查看。 [E09, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R9.AC3 | R | 留存同页面、同主题、同视口的改前/改后截图及关键 DOM/计算样式，明确哪些仅完成基线、哪些已终验。 | partial | historical-limitation | visual-baseline-comparison.md；browser/matrix-industrial-blue-dark.json/png；completion-report.md。 [E09, E05, E21, E25] | 历史证据限制：旧图1124×1000、新图1280×720，旧DOM未保存viewport；同页面同主题颜色/DOM可比，但严格同视口改前改后无法证明。用户要求不重建旧环境；非阻断披露，保持partial，非待补任务。 一项历史视口证据限制，经R9.AC3、T1.3及T1父项三行追溯；不表示三个独立缺陷。 |
| R10.AC1 | R | 范围内 Vue 模板的精确 el-input 标签及对应生成器输出全部迁为 zx-input；不匹配 el-input-number，不以旧前缀数量作为完成依据。 | covered | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment [E10, E11, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R10.AC2 | R | R11 完成并源码直连验证通过后，迁移清单中的 prefix/suffix/prepend/append 消费者全部迁移，不留插槽例外或白名单。 | covered | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment；当前范围收尾：E10, E11, E05, E23。 [E10, E11, E03, E05, E23] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R10.AC3 | R | 所有 textarea、number、search 及动态 type 调用逐项确认模型值类型、属性、事件和渲染语义；若现有包装行为不兼容，先修正 ZXUI 契约，不能为追求标签归零静默改变业务行为。 | partial | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment；当前范围收尾：E11, E05, E23。 [E10, E11, E03, E05, E23] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 当前B01–B13的密码显隐、readonly、textarea与正常text已结合实际字段/事件核对；number/search通用语义以同SFC源码/安装包及聚焦回归证明。设备VXE动态类型和生成器互斥分支已取消后续验收。 |
| R10.AC4 | R | 迁移完成后启用 no-raw-el-input 门禁，对约定范围一次性成立，无存量豁免。 | covered | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment [E10, E11, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R10.AC5 | R | 迁移后的真实业务页面逐页验证，包括 slots、输入/清空/焦点、实例方法和 flex 布局；不能只凭编译通过验收。 | partial | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment；当前范围收尾：E23, E22, E05。 [E10, E11, E03, E17, E23, E22, E05] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 当前B01–B13逐路由证据见E23；只覆盖记录内操作，未创建账号/改密码/穷举全部权限。其他模块不再待办。 |
| R10.AC6 | R | 不迁移 el-select 或 el-input-number；发现其他输入组件问题单独记录，不扩大本次批量替换范围。 | covered | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment [E10, E11, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC1 | R | 在 tooltip 与非 tooltip 两个分支均转发 prefix/suffix/prepend/append 到底层 ElInput，保留插槽内容与参数。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC2 | R | 最终 ZxInput 的 type=search 保留原生输入语义，不再隐式注入搜索按钮；消费者 append 正常透传。旧增强搜索按显式组件/插槽组合迁移，不能继续依靠 type 同时选择 UI 行为。此条替代旧版“保留内建 append 并定优先级”的目标。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC3 | R | ZxInput 公开 expose 对齐实际 ElInput 能力：focus/blur/select/clear/input/textarea/textareaStyle，保持参数、返回值和响应性；不额外暴露任意底层组件状态包。数值组件按自己的契约暴露能力。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC4 | R | 清除 input-core.vue 的 ::icon 错误和职责拆分后的无效搜索分支；仍存在的搜索按钮图标绑定有效，不将移除的旧分支遗留在任一 tooltip 路径。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC5 | R | 增加聚焦回归锁定 slots、tooltip 两种路径、expose、原生 number/search 语义及拆出的数值/搜索消费行为；复用同一代表样板验证源码与包产物，不为每个业务点复制测试。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review; 最终source/packed四slot、原生number/search、expose-select/inspect/clear、payload string7和数值quantity3、reset及外部Popover四场景；22聚焦测试补IME/model事件一次。 [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC6 | R | 文档分别列 ZxInput、数值输入及增强搜索的实际能力和迁移对应关系；不继续笼统宣称一个组件完整继承两类底层组件。文档收窄不能替代在用能力修复，主版本影响按 R13 交付。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC7 | R | 在真实业务中验证两层 wrapper 与 width: 100% 对搜索栏、flex 行、前后缀及 textarea 的影响，必要的通用修复在 ZXUI 完成。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review；当前范围收尾：E11, E23, E22。 [E11, E23, E22] | 系统搜索栏、资料/密码、参数textarea、菜单图标Popover与N01实际flex/宽度均有证据；22项输入回归和4个公开Popover复验已锁定通用根边界。 |
| R11.AC8 | R | ZxInput 固定消费 ElInput，type 专用于原生输入类型，不再把 number 转成 ElInputNumber；v-model 单一所有者，attrs/事件准确到达输入控件，name/id/aria、禁用、键盘、焦点与输入法组合输入行为保持，不增加 native/legacy 等永久兼容开关。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R11.AC9 | R | 将已有数值步进能力承接为小型 ZxInputNumber 并公开导出，迁移已知库内旧消费者；增强搜索按实际需求复用 ZxSearch 或显式 append 组合，核对 trim、清空触发与事件载荷，不机械替换。业务现有 el-input-number 仍不批量迁移。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R12.AC1 | R | 业务仅有一份主题登记，由其派生选择器、Host 注册与部署包列表；偏好状态经一个入口进入 Host/Provider，DOM 属性为投影而非另一套可写状态，不在页面拼 variant 字符串或写主题值。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue [E12, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R12.AC2 | R | 构建端复用 emitThemeDeployment 和主题包公开 exports，浏览器复用 createThemeDeploymentResolver 与既有 Host/Provider；最终运行时不遍历 generated/、不维护私有路径转换、不自行补写缺失库类型。源码 alias 限于显式开发工具边界。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue [E12, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R12.AC3 | R | 声明的主题包及 CSS/manifest 属于同一部署输出，安装后缺资产不能静默少一个主题；修正公开导出/类型和依赖声明，新增一个主题只需一处登记加正常依赖，不复制多份 ID 数组。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue [E12, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R12.AC4 | R | 弹框及内部二级浮层跟随发起它们的最近 scope，验证嵌套 scope、打开期间换肤、关闭重开；global body mirrored 只用于已确认的兼容边界，不能代替嵌套归属或跨 scope 污染验证。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue; source/packed nested-open、nested-popup-dark、nested-mode-switch-confirmed、parent-popup-mode-switch、reopen-after-mode-switch及nested-input-tooltip明确最近scope/variant；旧遮挡切换失败尝试保留且由真实成功重验替代。 [E12, E08, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R12.AC5 | R | 在既有库示例/消费 fixture 中提供一个不加载 RuoYi 修补 CSS 的表单弹框样板，与真实业务共用公开契约；若两边表现不同，记录归属并在正确层修复，不在业务增加另一套主题映射。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue; 公开同样板source/packed均实际打开，Host portal和外部Popover缺陷在库源修复；该样板不导入RuoYi补丁CSS。 [E12, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R13.AC1 | R | 输入职责调整明确为下一主版本或其本地预发布候选，记录旧→新用法及行为差异；不得以现有 2.x 兼容补丁发布。已知库内消费者和示例迁移完成，外部消费者不能假定已升级。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json [E13, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R13.AC2 | R | 用真实本地 tarball、公开 imports 和部署资产完成一次隔离安装验证，禁 source alias/workspace fallback；复用既有 packed 工具，只扩展本次相关样板，不先发布 npm，也不把正式发布/外部升级作为 Cursor 的前置。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json [E13, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R13.AC3 | R | 同一代表样板通过源码和打包两种模式：类型、构建、slots/expose、明暗、density、嵌套弹框/浮层以及 autofill。记录实际 Vue/EP/ZXUI 解析版本、包哈希与产物路径；不通过本地类型补丁或重复运行时掩盖 peer/导出缺口。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json; 最终同源public-source-fixed-autofill-{light,dark}与public-packed-autofill-{light,dark}：raw ElInput与tooltip ZxInput均实际:-webkit-autofill=true，inset shadow与textFill匹配明暗themeSurface/themeText。source修复只在play公开style.css入口，不改变085候选。 [E13, E05, E20] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| R13.AC4 | R | 完成声明需包含业务真实页面、库通用能力和可安装产物三类证据；明确未完成项及外部升级要求。本 spec 完成不等于已发布 npm，也不等于仿真已验证。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json；当前范围收尾：E13, E18, E23, E25。 [E13, E05, E18, E23, E25] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D1 | D | 职责分层与范围：库负责通用行为/主题，业务负责数据/薄布局；仿真及专用组件排除，无baseline/allowlist。 | covered | covered | 两仓增量diff对照baseline；UI_SCOPE；迁移库存。 [E03, E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D2 | D | FormDialog目录只有策略、useFormDialog、纯布局FormGrid，不新增FormField/FormModalHandle/表单实例代理。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue} [E01] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D3 | D | useFormDialog不复制visible/model/dirty/loading/提交；原生ElForm ref与命令接口保持。 | covered | covered | index.ts直接返回useDialog；页面传真实ref；无内部ElForm代理。 [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D4 | D | 唯一必填columns生成dialogSize/formProps/layoutProps；业务100px标签/20pxgap，目标1/2/3列映射md/lg/xl。 | covered | covered | policy.ts；index.ts；门禁三者owner反例已修复复核。 [E01] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D5 | D | FormGrid只响应式网格/横gap/data-form-full，无row-gap；长标签与窄容器降列规则统一，实际样板验证。 | covered | covered | FormGrid.vue源码通过；浏览器窄容器与长标签待证据。; 真实FormGrid窄容器、长标签、full整行测量见browser-fixture-coverage.md；不将容器测试冒称完整页面移动视口。 [E01, E02, E17] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D6 | D | FormDialog类型排除width/height，入口诊断并剔除非法动态值；合法尺寸例外有理由。 | covered | covered | index.ts FormDialogOptions/sanitize/checkColumns/updateOptions。 [E01, E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D7 | D | 普通弹框按内容高度与库max-height，必要dialogStyle.maxHeight，不支持顶层maxHeight或style.height绕过。 | covered | covered | 门禁496/0、库结构max-height与N01真实UserForm长内容滚动，见E22。 [E01, E04, E22] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D8 | D | 主题缺口在库源/生成层修复；全局alias继承有效；业务不重写库变量，清掉通用autofill重复。 | covered | covered | compiler源/生成产物；main.ts与业务样式增量；ui gate。 [E04, E06] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D9 | D | EP有效size链保留；density仅度量，small/default/large统一表，Form/FormItem/Provider边界且不双缩放。 | covered | covered | density.ts与docs度量表一致；实际测量待证据。; library/browser/observed-evidence-2026-09-22.json 24组旧候选度量（明确历史）; 最终24组度量和source/packed Form small/large实录；组件small/large覆盖继承、默认控件跟Form尺寸。 [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D10 | D | 最近Provider拥有dialog及二级浮层；打开中切换/重开/嵌套scope均验证；body mirrored仅兼容。 | covered | covered | use-theme-provider/use-dialog-portal；ZxSelect/Tooltip appendTo；公开fixture；浏览器待证据。; source/packed嵌套dialog/Select/tooltip为最近Provider归属，打开中切明暗、父子异色和重开均有对应observed。 [E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D11 | D | useDialog开发formRef缺size/width告警，生产不刷且通用small不变。 | covered | covered | hooks/use-dialog/index.ts及聚焦测试。 [E04] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D12 | D | ZxInput固定ElInput，原生type，四slots双tooltip路径，expose七能力；attrs目标/vmodel单所有者/IME一次。 | covered | covered | input实现/13测试；business_theme_deployment交叉复核，审阅者本人的实现范围不算独立。 [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D13 | D | ZxInputNumber小组件承接数值步进；旧搜索显式组合保持trim/clear/载荷；不改ZxSearch或业务ElInputNumber。 | covered | covered | input-number实现/4测试；docs/examples/input/types.vue；迁移清单。 [E11] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D14 | D | 破坏API按下一主版本候选交付，旧search事件和外部升级边界说明。 | covered | covered | 3.0.0-next.0；中英input/input-number迁移文档。 [E08, E13] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D15 | D | 主题catalog单源派生UI/Host/build；登记缺依赖/manifest报错，正常依赖明确。 | covered | covered | src/theme/zx-theme-packages.ts；vite/zxui-theme-packages.ts；package.json。 [E12] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D16 | D | 构建使用公开emitThemeDeployment，浏览器公开resolver，部署独占目录及base路径正确；无runtime generated猜测/类型补丁。 | covered | covered | public deployment入口；business-theme-deployment.json base / 和 /admin/；type/build通过。 [E12] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D17 | D | 偏好一个入口进入Host/Provider，document属性只投影；不新增density UI或第二主题系统。 | covered | covered | zx-theme-config.ts；App.tsx；zx-theme-host.ts；偏好3测试通过。 [E12] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D18 | D | 页面壳/生成器消费公开surface/token，不添业务翻译层；experimental surface身份锁定。 | covered | covered | 主代理授权的theme-surface-contract.md；从9个公开manifest export实读同一contractVersion=4.0.0与contractContentHash并记录opt-in/升级重验。 [E08, E12] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D19 | D | 所有非仿真可执行孤立候选仍受门禁；NodeEditDrawer/Dag/协议模板共享消费者不整块排除。 | covered | covered | UI_SCOPE三项排除；input-migration/原库存。 [E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D20 | D | 生成器有限身份集中、旧设计可读取编辑预览导出；新dialog输出完整imports/同组合/full意图。 | covered | withdrawn-by-user | generator/identity.ts与html/js/render；5 tests；交叉复核未见实现问题。 [E10] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| D21 | D | 同代表生成SFC执行生成→解析→预览/打开，源码及产物共用checker。 | covered | withdrawn-by-user | 5 tests包含compile/独立render，完整生成SFC实际mount/open待证据。; 本人复跑完整生成SFC真实public组件mount/open/validate/reset/confirm测试通过，复用checkVueSource。 [E10, E02] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| D22 | D | 薄静态入口三种format/strict/exit1/范围位置，无baseline；仅明确本地Vue/TS形状，未知配置不静默跳过。 | covered | covered | checker/core与成组tests；本review owner错绑反例现已拦截。 [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D23 | D | 数据沿statusOptions→字典/缓存/HTTP定位，不伪造字典，不预设dept同因，无数据库迁移。 | covered | covered | dict.ts items消费；真实response合同及2聚焦tests；UserFormDialog response.data。 [E09, E14] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D24 | D | 安全：已授权本地浏览器、截图不含token、测试提交清理；隔离tarball不registry发布或其他业务lockfile。 | partial | covered | tarball隔离realpaths已证；真实业务测试数据清理/截图安全待浏览器记录。；当前范围收尾：E13, E25。 [E13, E25] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 当前系统/登录资料验证未新建用户、改凭据或提交破坏操作；临时公开站点移出public，视口恢复。此前工程/设备和sys_post本地测试数据明确保留，用户取消后未继续清理，不能把原全范围清理记为完成。 |
| D25 | D | 顺序：库input/主题公开能力先满足，业务input最后批次；任务16在14前；不等正式发布或外部业务升级。 | covered | covered | input最后批次记录、公开source/packed收据先于最终closeout，085dfd安装1648文件一致；本地候选无需正式npm发布，见E10/E13/E18/E25。 [E10, E13, E18, E25] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D26 | D | 三类证据分离；同代表公开样板source+packed，无RuoYiCSS，无alias/fallback，真实版本/hash/路径/单peer。 | covered | covered | 真实隔离receipt类型/build通过且单peer；source及packed runtime待证据。; 最终同源public-source-fixed-autofill-{light,dark}与public-packed-autofill-{light,dark}：raw ElInput与tooltip ZxInput均实际:-webkit-autofill=true，inset shadow与textFill匹配明暗themeSurface/themeText。source修复只在play公开style.css入口，不改变085候选。 [E13, E05, E20] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D27 | D | 复用既有packed-install/hosted-packed、相关生成漂移检查，不用旧widget通过抵扣表单。 | covered | covered | packed-install已复用新表单；compiler最终gate进行中；浏览器仍pending。; 现有packed-install工具已复用并运行本轮form fixture；static-verification记录1458变体漂移/结构检查；未使用widget证据抵扣。 [E13, E04] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| D28 | D | 真实交互包含键盘开关/焦点返回、IME、校验失败、重开、长内容、真实autofill；执行相关lint/type/test/ui门禁。 | covered | covered | 最终系统/公开组件真实交互、N01窄视口键盘/滚动/焦点、IME测试和closeout检查；见E11/E20/E22/E23/E24/E25。 [E02, E05, E15, E11, E20, E22, E23, E24, E25] | N01 Tab焦点/取消返回opener、公开样板Escape关闭/重开、输入IME回归、系统required、N01滚动、真实autofill与最终相关检查组合证据；不宣称整个业务shell移动端全覆盖。 |
| T1 | T | 修复状态选项数据链路并补齐样板基线 | partial | historical-limitation | visual-baseline-comparison.md；browser/matrix-industrial-blue-dark.json/png；completion-report.md。 [E09, E03, E21, E25] | 历史证据限制：旧图1124×1000、新图1280×720，旧DOM未保存viewport；同页面同主题颜色/DOM可比，但严格同视口改前改后无法证明。用户要求不重建旧环境；非阻断披露，保持partial，非待补任务。 一项历史视口证据限制，经R9.AC3、T1.3及T1父项三行追溯；不表示三个独立缺陷。 |
| T1.1 | T | 复用现有添加用户证据：440×600、标签跟主题、radio input 为 0；沿 statusOptions、字典请求/缓存及响应适配确认具体根因并修复，记录业务/库归属。 | covered | covered | src/utils/dict.ts:39; src/utils/dict.test.ts; api/system/dict/data.ts:31; UserFormDialog.vue:195; browser evidence pending; useDict items响应契约已定位修复并测试；UserForm状态0/1两个radio在真实九主题DOM恢复。440×600旧基线来自spec记录，前后图片义务单列T1.3/R9.AC3仍待验。 [E09, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T1.2 | T | 不硬编码字典兜底；deptList.filter 只作为相邻契约线索，不预设同因。恢复选项后检查原提交值与主题可见性。 | covered | covered | 同R9.AC2；无硬编码字典兜底，deptTree由各自items合同修复；真实用户表单radio恢复。 [E09, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T1.3 | T | 重扫库存和非仿真消费者，保存同页面/主题/视口的截图及 DOM，记录浏览器和真实依赖版本；未触达候选不算验收。 | partial | historical-limitation | visual-baseline-comparison.md；browser/matrix-industrial-blue-dark.json/png；completion-report.md。 [E09, E03, E21, E25] | 历史证据限制：旧图1124×1000、新图1280×720，旧DOM未保存viewport；同页面同主题颜色/DOM可比，但严格同视口改前改后无法证明。用户要求不重建旧环境；非阻断披露，保持partial，非待补任务。 一项历史视口证据限制，经R9.AC3、T1.3及T1父项三行追溯；不表示三个独立缺陷。 |
| T2 | T | 建立业务薄布局策略与纯布局 FormGrid（依赖 1） | covered | covered | 见下列 T2.* 子任务证据；当前范围收尾：E01, E02, E22, E25。 [E01, E02, E22, E25] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T2.1 | T | 一份布局策略管理 columns→dialogSize、label-width、横向 gap 与窄容器降列。useFormDialog 从唯一 columns 输入返回 dialogProps/events 与 formProps/layoutProps，不复制模型、提交或 dirty 状态。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T2.2 | T | 保留原生 el-form ref 与 el-form-item。FormGrid 只处理 CSS Grid 和 data-form-full，不包装 ElForm、不新增 FormField、不代理 FormInstance，也不新增 FormModalHandle。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T2.3 | T | 不增加 grid row-gap，纵向节奏由库主题/density 控制；长标签与降列规则在一个策略处维护。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T2.4 | T | 类型排除 width/height；统一入口对非法动态值诊断并剔除。保留合法预设例外及原 useDialog 回调语义。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E02] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T2.5 | T | 通过既有类型检查与实际校验/重置/分步/错误滚动/重开验证；不为纯布局数值新增一批单测。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs；当前范围收尾：E02, E22, E24, E25。 [E01, E02, E22, E24, E25] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T3 | T | 迁移 UserFormDialog 样板（依赖 1、2） | covered | covered | 见下列 T3.* 子任务证据；当前范围收尾：E09, E05, E21, E22, E23。 [E01, E09, E05, E21, E22, E23] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T3.1 | T | columns: 2 驱动同一尺寸/表单/布局绑定，原生 ElFormItem 声明字段与整行意图，删除 height: '60%'。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E09, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T3.2 | T | 核对正常视口 lg、窄容器降列、长标签、间距、错误滚动、状态选项、重开与提交；修正已有 placeholder 一致性。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs；当前范围收尾：E09, E05, E22, E23。 [E01, E09, E05, E22, E23] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T3.3 | T | 默认限高直接沿用库，需要时使用 dialogStyle.maxHeight，不传无效顶层 maxHeight。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs [E01, E09, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T3.4 | T | 留存可对比证据，布局样板通过才复制到其他页面；不抢做最终输入框批量替换。 | covered | covered | src/components/ui/FormDialog/{index.ts,policy.ts,FormGrid.vue}; UserFormDialog.vue; scripts/ui-standards-core.mjs；当前范围收尾：E21, E05, E10。 [E01, E09, E05, E21, E10] | 同页面同主题DOM/计算色对照与基线patch可比较；严格同视口缺证仅保留于R9.AC3/T1.3，不将这条未要求同视口的任务永久判缺证。 |
| T4 | T | 迁移范围内其他表单弹框（依赖 3） | partial | covered | 见下列 T4.* 子任务证据；当前范围收尾：E23, E24, E25。 [E01, E03, E23, E24, E25] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T4.1 | T | 以当前清单迁移项目、部门、通知、设备/端口、克隆、导入等普通表单；不包含仿真专用弹框。 | covered | covered | scripts/check-ui-standards.mjs: 496 files/0 violations; current migration inventory; two ExportDialog initial-open fix [E01, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T4.2 | T | 使用同一业务策略、原生表单与 FormGrid，去掉字段手写 label-width/gutter/span 和固定高度；不改内部表格/编辑器布局。 | covered | covered | scripts/check-ui-standards.mjs: 496 files/0 violations; current migration inventory; two ExportDialog initial-open fix [E01, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T4.3 | T | 逐页核对条件字段、校验、loading、脏数据守卫、关闭重开和提交值，保留范围内未完成项，不加 allowlist。 | partial | covered | scripts/check-ui-standards.mjs: 496 files/0 violations; current migration inventory; two ExportDialog initial-open fix；当前范围收尾：E23, E24。 [E01, E03, E17, E23, E24] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T5 | T | 统一范围内非表单弹框尺寸（依赖 3） | partial | withdrawn-by-user | 见下列 T5.* 子任务证据 [E03, E04] | 原范围尚未逐项验证的部分随用户指令停止；不判通过。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T5.1 | T | 版本预览/详情、DagMatrix、操作日志、生成代码预览等按内容选预设，去掉硬编码宽度及百分比/vh 固定 height。 | covered | withdrawn-by-user | src/components/ui/FormDialog/index.ts sanitizer; scripts/ui-standards-core.mjs; ZXUI dialog structural max-height [E03, E04] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T5.2 | T | 依赖库默认限高，必要时用 dialogStyle.maxHeight；不强套 FormGrid。 | covered | withdrawn-by-user | src/components/ui/FormDialog/index.ts sanitizer; scripts/ui-standards-core.mjs; ZXUI dialog structural max-height [E03, E04] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T5.3 | T | 核对长内容、窄视口、关闭、全屏和挂载等既有行为，不扩展仿真验收。 | partial | withdrawn-by-user | src/components/ui/FormDialog/index.ts sanitizer; scripts/ui-standards-core.mjs; ZXUI dialog structural max-height [E03, E04] | 原范围尚未逐项验证的部分随用户指令停止；不判通过。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T6 | T | 原生 dialog 与生成器表单源头收口（依赖 4、5） | partial | covered | 见下列 T6.* 子任务证据；当前范围收尾：E03, E07, E23, E24。 [E03, E10, E02, E07, E23, E24] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T6.1 | T | 初始 18 个/16 文件仅为非仿真目录候选；按当次确认清单迁移 ZxDialog，并验证 ESC、遮罩、校验、loading、挂载及脏数据守卫。 | partial | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml；当前范围收尾：E03, E07, E23, E24。 [E03, E10, E02, E07, E23, E24] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T6.2 | T | 生成器 dialog 输出改用相同表单组合，完整输出 imports/注册/策略绑定；不把生成字符串当真实页面实例。 | covered | withdrawn-by-user | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E03, E10, E02] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T6.3 | T | 整理现有 html/config/drawingDefalut/render 的有限组件身份对应，为后续 input 迁移准备一个统一来源，不再并行维护预览与导出的不同 tag。 | covered | withdrawn-by-user | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E03, E10, E02] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T6.4 | T | 旧设计配置继续可读取、编辑、预览、导出；代表生成 SFC 解析与页面打开通过，源头不能重新生成旧布局。 | covered | withdrawn-by-user | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml; 旧身份读取/预览与导出聚焦测试、完整代表生成SFC真实mount/打开/校验/重置/提交均通过；实际生成器页面总体交互仍由T13.5逐页验收。 [E03, E10, E02] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T7 | T | **[ZXUI]** 修实证主题缺口及通用 autofill | covered | covered | 见下列 T7.* 子任务证据 [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T7.1 | T | 复用公开 API 建立一个不加载 RuoYi 补丁的表单弹框代表样板，同时用于后续源码与打包消费检查。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T7.2 | T | 核对全局 alias、局部 scope 与标签/必填/错误/禁用/选中/焦点；已有继承不重复造 token，业务覆盖在业务清理，通用缺口在库源文件修复并生成。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; 最终公开样板明暗/选中/禁用/required/error/focus及局部scope截图、DOM与computed；仅实际通用缺口修库。 [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T7.3 | T | 通用 autofill 验证背景/文字明暗，覆盖 ElInput 与最终 ZxInput；不得只用登录页覆盖当库能力。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; 最终同源public-source-fixed-autofill-{light,dark}与public-packed-autofill-{light,dark}：raw ElInput与tooltip ZxInput均实际:-webkit-autofill=true，inset shadow与textFill匹配明暗themeSurface/themeText。source修复只在play公开style.css入口，不改变085候选。 [E04, E05, E20] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T7.4 | T | 真实业务源码直连对照库样板，保存九主题明暗的代表表单证据；不复制整套全排列测试。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; 业务18个九主题明暗用户表单记录，与最终公开source/packed的代表default/defense三density和状态截图相互独立留证。 [E04, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T8 | T | **[ZXUI]** EP density、scope 与尺寸告警（衔接 7） | covered | covered | 见下列 T8.* 子任务证据 [E04, E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T8.1 | T | 保留核心 density 轴，补 EP 度量消费；默认 size 测量三档差异，保留 EP 原有有效 size 解析链（组件、既有 fallback、FormItem/Form、Provider、默认），验证表单级尺寸继承；density 只作用于最终有效 size 下的主题度量，不改写继承链或两次缩放。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; library/browser/observed-evidence-2026-09-22.json 24组旧候选度量（明确历史）; 最终24组度量与Form继承记录齐全，原size解析源码和聚焦测试仍成立。 [E04, E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T8.2 | T | 复用已有 scope/Portal 能力验证嵌套弹框和内部二级浮层、打开中换肤、关闭重开；不能用 body mirrored 替代局部 scope 归属。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog; 最终同样板scope/Portal全部真实交互记录，非body mirrored推断。 [E04, E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T8.3 | T | useDialog 开发态对 formRef 无显式 dialogSize/width 告警，业务 wrapper 推导后不误报，不修改所有 ZxDialog 的 small 默认值。 | covered | covered | ZXUI theme-compiler/src/adapters/element-plus/{density.ts,mapping.ts,index.ts}; theme-chalk/src/structural.css:6062; hooks/use-dialog [E04, E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T9 | T | 清理业务重复主题来源（依赖 4–8、15 与覆盖证据） | covered | covered | 见下列 T9.* 子任务证据；当前范围收尾：E06, E05, E20, E21。 [E06, E05, E20, E21] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T9.1 | T | 清理 theme.module.css/tailwind.css 等反向 alias 与主色竞争写入，保留领域色和用户正文色；现有页面壳直接消费公开 surface/token，不增加业务映射层。 | covered | covered | src/main.ts; src/assets/styles/{tailwind.css,theme.module.css}; src/theme/zx-theme-config.ts; docs/reports/.../baseline/business.patch [E06, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T9.2 | T | 状态/明暗覆盖通过后删除 EP dark/css-vars.css、clearBusinessPrimaryOverrides 及调用，确保旧写入不会重新覆盖。 | covered | covered | src/main.ts; src/assets/styles/{tailwind.css,theme.module.css}; src/theme/zx-theme-config.ts; docs/reports/.../baseline/business.patch；当前范围收尾：E06, E05, E20, E21。 [E06, E05, E20, E21] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T9.3 | T | 保留 EP 必需基础样式和正确加载顺序；库 autofill 已成立时移除重复的业务处理。 | covered | covered | src/main.ts; src/assets/styles/{tailwind.css,theme.module.css}; src/theme/zx-theme-config.ts; docs/reports/.../baseline/business.patch [E06, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T9.4 | T | 对比实际非仿真页面的删除前后颜色，记录影响边界，不声称仿真通过。 | covered | covered | src/main.ts; src/assets/styles/{tailwind.css,theme.module.css}; src/theme/zx-theme-config.ts; docs/reports/.../baseline/business.patch; 工厂蓝深色添加用户基线及终态DOM比较证明dialog背景和11字段label色相同；颜色对照完成且不声明仿真。旧图viewport未存且图片像素不同，所以R9.AC3同视口配对仍partial。 [E06, E05, E21] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T10 | T | 接入薄而严格的门禁（依赖 3–6、9、15） | covered | covered | 见下列 T10.* 子任务证据 [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T10.1 | T | 新增 check-ui-standards.mjs 薄入口，复用 Vue/TS 解析器和一个模板检查核心；源码与生成后 SFC 共用。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T10.2 | T | 只检查明确的模板/局部对象/统一入口。复杂间接配置改为受类型和运行时校验的入口，不做通用全程序分析，不静默跳过未知形状。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T10.3 | T | 覆盖 dialog 尺寸/高度绕过、表单策略、竞争主题写入和私有主题路径；不要误报页内布局、el-input-number、领域色或文档注释。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T10.4 | T | 无 baseline/allowlist，少量成组正反例防误报/漏报；存量通过再接入 package.json、GitHub/GitLab CI。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T10.5 | T | no-raw-el-input 待任务 13 完成启用；不因规则尚未启用标记输入迁移完成。 | covered | covered | scripts/{check-ui-standards,ui-standards-core}.mjs; tests/ui-standards.test.ts; package.json; .github/workflows/ci.yml; .gitlab-ci.yml [E07] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T11 | T | 完善公开示例和迁移说明（依赖 9、10、12、15） | covered | covered | 见下列 T11.* 子任务证据 [E08, E10] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T11.1 | T | **[ZXUI]** 写明原生输入、数值步进、增强搜索的职责和旧→新迁移差异，明确下一主版本候选边界与外部升级要求。 | covered | covered | ZXUI docs/{zh-CN,en-US}/component/input*.md; docs/zh-CN/{component/dialog,guide/theme-tools}.md; business AGENTS.md:90 [E08, E10] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T11.2 | T | **[ZXUI]** docs 示例使用公开 Host/Provider/部署资产，说明 density/size 与 scope/Portal，不能要求其他业务复制 RuoYi 私有路径、类型补丁或 CSS。 | covered | covered | ZXUI docs/{zh-CN,en-US}/component/input*.md; docs/zh-CN/{component/dialog,guide/theme-tools}.md; business AGENTS.md:90 [E08, E10] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T11.3 | T | 业务 AGENTS.md 写薄表单组合、主题唯一入口和仿真排除范围，指向 spec；业务标签宽度/gap 不成为全库规定。 | covered | covered | ZXUI docs/{zh-CN,en-US}/component/input*.md; docs/zh-CN/{component/dialog,guide/theme-tools}.md; business AGENTS.md:90 [E08, E10] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T11.4 | T | 生成器示例与手写页面采用同一组合，库/业务契约说明与最终 Cursor 迁移目标一致。 | covered | covered | ZXUI docs/{zh-CN,en-US}/component/input*.md; docs/zh-CN/{component/dialog,guide/theme-tools}.md; business AGENTS.md:90 [E08, E10] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T12 | T | **[ZXUI]** 拆清输入职责并完成公开契约（可与表单/主题任务并行） | covered | covered | 见下列 T12.* 子任务证据 [E11, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T12.1 | T | 先记录下一主版本目标和旧行为对应表，不在现有 2.x 补丁中偷改。ZxInput 固定 ElInput，type 只表示原生输入类型，不新增永久 native/legacy 路由开关。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T12.2 | T | tooltip 两种路径透传四类 slots 与参数；expose 对齐 ElInput 的已承诺方法/属性，保持响应性，不暴露任意内部状态包。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T12.3 | T | 移除 number 路由和隐式 search append 分支，一并清除 ::icon。数值步进能力承接为小型 ZxInputNumber，补齐必要公开入口、类型、样式和库内已知调用迁移；不批量迁业务 el-input-number。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T12.4 | T | 旧增强搜索按需求复用 ZxSearch 或显式 append 按钮组合；核对 trim、清空触发、string 与对象载荷，保持已知消费者的业务行为，不重构所有搜索栏。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T12.5 | T | 统一 v-model 所有者与属性/事件目标；聚焦验证输入法组合输入、输入/清空事件只触发一次、name/id/aria、禁用、焦点和 flex。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review [E11, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T12.6 | T | 更新库内已知消费者与 docs 示例；聚焦回归覆盖真实契约，不按184个业务点复制测试。复用任务 7 的公开样板，源码直连验证业务兼容后放行。 | covered | covered | ZXUI packages/components/{input,input-number}; public root/leaf/type/style exports; input tests 13 + numeric 4; business_theme_deployment peer cross-review; 库内已知消费者/docs迁移已核，22项真实聚焦与同一公开样板source/packed slots/expose/native/数值/payload回归齐；业务源码直连真实用户/克隆输入和外部Popover支持成立。逐页全部消费者义务仍属T13.4/T13.5，不以该项代替。 [E11, E08] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T13 | T | Cursor 最后批量迁移 el-input（依赖 1–12、15） | partial | covered | 见下列 T13.* 子任务证据；当前范围收尾：E10, E11, E23, E25。 [E10, E11, E03, E23, E25] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T13.1 | T | 重新核对候选184个/68文件，静态textarea28个、17个input的18个slots为重叠分类，不按旧257前缀数替换。 | covered | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment [E10, E11, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T13.2 | T | 精确替换 el-input 为最终 ZxInput，number/search/动态type按已通过的原生语义方案逐项确认；不替换 el-input-number 或 el-select。 | covered | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment [E10, E11, E03] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T13.3 | T | 同步生成器统一组件身份及配置/预览/输出，转换2处legacy append和生成器旧slot语法；已有设计配置读取与重新导出仍正常。 | covered | withdrawn-by-user | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment [E10, E11, E03] | 已有实现与历史证据保留；本条不计入当前适用验收通过数。 用户取消该项后续工作/验收；不以缺少这些证据阻塞当前范围，也不把取消当通过。 |
| T13.4 | T | 核对 slots、实例方法、空值与事件、布局及动态类型，范围内一次迁完，不给复杂调用加白名单。 | partial | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment；当前范围收尾：E11, E22, E23。 [E10, E11, E03, E22, E23] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T13.5 | T | 启用 no-raw-el-input，共用模板检查器核验生成输出，逐页真实验证。前置是库本地候选通过，不是正式发布或所有外部消费者升级。 | partial | covered | input-migration.json; input-generator/implementation.md; gate 496/0; generator-form-contract.test.ts; input/generator cross review by business_theme_deployment；当前范围收尾：E07, E23, E25。 [E10, E11, E03, E17, E07, E23, E25] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T14 | T | 三类证据终验与状态回写（依赖 16） | partial | covered | 见下列 T14.* 子任务证据；当前范围收尾：E13, E23, E25。 [E15, E05, E13, E23, E25] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T14.1 | T | 汇总库公开能力、真实业务页面、本地可安装产物证据，分别说明证明范围，不能拿导航旧矩阵或widget协议通过抵扣表单验收。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json；当前范围收尾：E13, E18, E23, E25。 [E15, E05, E13, E18, E23, E25] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T14.2 | T | 逐页核对数据、尺寸、降列、滚动、校验、焦点、重开、输入及明暗；代表表单覆盖九主题明暗与代表主题三档density，异常再扩展，不做全排列。 | partial | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json；当前范围收尾：E05, E20, E22, E23。 [E15, E05, E13, E17, E20, E22, E23] | 原始范围仍有已被用户取消的未验分支/清理义务；仅当前系统/通用能力部分完成。设备、工程、监控、生成器不再待办，不将整条原始义务冒称全覆盖。 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T14.3 | T | 运行业务相关 lint/type-check/test:run/ui:standards 及 ZXUI 相关聚焦回归、既有生成/漂移检查；记录实际结果，不用新增测试数量代替质量。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json; 原文要求运行并记录实际结果，已完成相关lint/type/test/ui标准、ZXUI聚焦/生成漂移检查；全量lint860error/1232warning与单个存量Vitest失败如实披露，不宣称全仓全绿。新增generator repository Ruff前后均134同项问题、新增0，聚焦回归修前失败/修后通过。 [E15, E05, E13] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T14.4 | T | 核对全部验收项后更新状态；未触达候选、外部升级要求及包交付限制明确记录。完成不代表已发布 npm，不代表仿真已验收。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json；当前范围收尾：E23, E25。 [E15, E05, E13, E23, E25] | 最终范围与未完成原范围、npm/生产/外部升级边界已经completion-report和tasks明确回写；不把被取消路线改记通过。 |
| T15 | T | 统一公开主题接入与资产交付（9、10、11、13 的前置） | covered | covered | 见下列 T15.* 子任务证据；当前范围收尾：E12, E05, E20, E23。 [E12, E05, E20, E23] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T15.1 | T | 将现有主题选择器、Host和Vite包列表改为从一个登记源派生；登记依赖显式存在，缺包/manifest不可静默略过。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue [E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T15.2 | T | 构建端复用 emitThemeDeployment，浏览器用 createThemeDeploymentResolver；manifest/CSS共同交付，核对base路径，构建工具不进浏览器。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue [E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T15.3 | T | 移除业务运行时 generated glob、export→私有路径转换和 portalContainerScope 类型补丁；公开类型缺口在ZXUI补齐，开发alias只在工具边界保留。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue [E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T15.4 | T | 将偏好更新收敛为一个入口交Host/Provider，document属性为投影，去掉页面拼variant与重复状态写入；不新增另一套主题框架或必须的density设置UI。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue [E12, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T15.5 | T | 实际业务验证登记的九主题、登录/主框架/表单及二级浮层；公开样板无需RuoYi修补CSS，发现差异按归属修复。 | covered | covered | src/theme/{zx-theme-packages,zx-theme-config,zx-theme-host}.ts; src/App.tsx; vite/zxui-theme-packages.ts; ZXUI docs/examples/dialog/public-form-contract.vue；当前范围收尾：E12, E05, E20, E23。 [E12, E05, E20, E23] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T16 | T | 验证本地候选包可供其他业务安装（依赖 13） | covered | covered | 见下列 T16.* 子任务证据 [E13, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T16.1 | T | 用本轮源码生成真实本地tarball和主题部署资产，记录包版本、哈希、实际解析路径及Vue/EP/ZXUI版本；先核对peer契约，不靠声明合并或重复运行时掩盖问题。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json [E13, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T16.2 | T | 复用已有packed-install/hosted-packed工具的安装/构建/浏览器能力，在隔离临时目录运行任务7/12的同一代表表单，禁止source alias/workspace fallback。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json; rApuws真隔离public安装，复制相同public-form-contract.vue，无alias/fallback；新hash source/packed外部Popover均打开，其他维度T16.3仍待终验。 [E13, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T16.3 | T | 核对公开imports/类型/样式及slots/expose/native类型、代表主题明暗、三档density、嵌套scope/二级浮层和真实autofill；无需在包fixture重复全部业务页面。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json; 最终同源public-source-fixed-autofill-{light,dark}与public-packed-autofill-{light,dark}：raw ElInput与tooltip ZxInput均实际:-webkit-autofill=true，inset shadow与textFill匹配明暗themeSurface/themeText。source修复只在play公开style.css入口，不改变085候选。 [E13, E05, E20] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |
| T16.4 | T | 没有正式npm发布、外部仓改动或外部全部升级前置；输出本地主版本候选消费证据及外部升级说明，交任务14终验。 | covered | covered | ZXUI packages/zxui/package.json 3.0.0-next.0; library/packed-receipt.json (rApuws); /private/tmp/zxui-popover-packed-check.log; business-theme-deployment.json [E13, E05] | 按当前用户保留范围判断；证据边界见对应Evidence项，取消模块的旧记录不替代当前真实页面。 |

## Verification Log

- V1：本人初轮 strict gate：496 files / 0 violations；两控制器反例修复复核成功。
- V2：本人初轮4文件14tests通过（dict/UserFormDialog/portal/gate）；90秒显式timeout。
- V3：本人新轮6文件21tests通过，包含完整生成SFC真实mount/校验/重置/confirm；vue-tsc exit0；gate496/0。原始命令和输出：verification/peer-static-2026-09-23.log，每命令timeout120秒。
- V4：本人数据链frontend6tests和backend14tests通过；data-contract-fixes.md记录精确命令/服务契约。
- V5：本人ZXUI input18+number4通过；输入聚焦eslint、公开样板source tsc均exit0；日志/private/tmp/zxui-popover-{final-tests,lint,source-types}.log。
- V6：本人pnpm build exit0（timeout600秒），真实packed-install exit0（timeout600秒）；读取并重算rApuws tarball SHA一致；隔离依赖路径及单peer已核。library/packed-receipt.json；/private/tmp/zxui-popover-{candidate-build,packed-check}.log。
- V7：主线程持久化build日志/private/tmp/zxui-final-business-build.log：27.86s成功；typecheck/standards结果已由V3独立复核。
- V8：读取全量日志：lint860errors/1232warnings；最终Vitest1fail/694pass（mocks/store/datasource期望4实际6）。主线程说明为基线问题，本报告不将其等价为全绿，T14.3按“运行并记录实际结果”的原文已covered，未把历史失败冒称全绿。
- V9：本人逐项读取九主题18份业务DOM，核对880宽/两列/两radio/主题variant与autofill记录；抽查对应截图。public历史24度量为旧hash，明确不直接当新边界最终通过。
- V10：本人只读HTTP遍历172模块、14个504，见verification/project-import-http-before.json；未发起认证/业务写请求。
- V11：本人读取最终085dfd库记录：24度量、4外部Popover、Form尺寸、expose/payload、scope/二级浮层/切肤重开；抽查明暗截图。独立端口autofill未触发仅作失败尝试；同源source（公开style.css修复后）与packed两种输入的明暗真实autofill均已成立，E20。
- V12：本人读C/F/G01和真实FormGrid容器证据，1100/650/320分别3/2/1列，长标签与full整行无溢出；明确不抵扣完整移动视口。
- V13：ContentDetailWrap SFC及scoped Less编译exit0；验证不再产生fill height:auto/100%覆盖。真实高度已由root浏览器复验，B25-clone-*记录640宽/校验/输入；没有用JSDOM零layout冒称视觉通过。
- V14：末轮补读N01真实640/390视口与B01–B13路线证据，原窄视口缺口已补。其他模块未验分支随用户指令取消，原表保留partial；严格历史同视口配对不可证明，保持非阻断限制。

- V15：本地仅两缺表checkfirst创建（45秒timeout、DDL guard），真实repository只读查询10items/total34通过；verification/generator-schema-init.json记录完整DDL及35旧表保留。用户随后取消生成器后续验收；本记录只保留已执行事实。

- V16：generator COUNT cache回归先复现缓存0导致total0，限定metadata list use_count_cache=False后1passed；新测试ruff通过。旧repository Ruff基线/现值均134且逐code/message/source行差异0，见verification/generator-count-cache-{check.log,ruff-baseline.json}。前端3SFC lint0error/1旧warning；当轮完整typecheck因并行fixture2处optional调用失败，该失败保留为历史；owner修复后最终完整typecheck已由V17的exit0覆盖。用户缩减后未再推进生成器。

- V17：本人读取最终`verification/closeout-results.json`及5份closeout原始日志：typecheck exit0；standards496文件0违规、14 tests；系统聚焦42 tests；最后批lint0 errors/4 warnings；build26.78s成功。历史全量860 errors/1232 warnings与1 failed/694 passed照实保留，不称全仓全绿。
- V18：本人末轮只读核对系统UserForm选项、useDialog默认遮罩/guard映射和已有聚焦测试、公开浏览器Escape关闭记录；不从一次Escape后的空尺寸推导density通过。N01实际Tab/取消返回焦点及滚动与该库行为证据分开标注。

## 最终处置与边界

- 当前保留范围没有待实施或待运行验证事项，无未解决阻断代码问题。本人实施的input/generator/data修复与其非作者交叉复核仍按首节明确分开。
- 用户取消项：设备、工程、监控、生成器的后续验证停止，已有改动/历史数据/证据保留；B14–B27、C01–C04、F01–F09/F12及N02–N06未验分支不标通过，不再列待办。门禁已覆盖的更大静态集合不被范围调整倒改成豁免。
- 历史证据限制：R9.AC3严格同视口前后配对缺证，连带T1.3/T1为三行追溯的一项限制；已有同主题颜色与DOM对照支持已陈述的结论。按用户要求不重建旧源码/补拍，不能把当前截图当原始基线。
- 本地测试工程/设备及sys_post生成元数据按completion-report如实保留；取消范围后的停止不冒称完成原测试数据清理。未提交、未发布npm、未生产部署，外部业务仍需按下一主版本输入语义迁移。
- 原始全范围表仍有partial，因此本报告不签发原始165条全量PASS；当前缩减范围完成结论与原始范围缺证分开陈述。

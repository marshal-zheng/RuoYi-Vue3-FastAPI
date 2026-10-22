# 前端、SchemaForm 与生成器验证

日期：2026-10-22。实施位于应用本地 worktree `/.worktrees/generic-remark-rich-text`；ZXUI 位于其独立同名 task worktree。输入快照分别为应用 `9c25bcd410be6fbeb53af41da540135848e665c1`、ZXUI host `146d18ab3b48ef6b2871189161fb778543a722de`，实现仍为工作区改动。没有向原始 checkout 写入、提交实现或发布 npm。

本报告区分静态代码、真实组件 DOM 探针、生成代码执行及真实界面验收。**真实浏览器、明暗主题、density、portal 焦点及实际业务操作尚未验收**；本轮未获 computer use 授权，没有调用该能力。

## 实现与证据边界

| 范围 | 实现 | 自动化证据 |
| --- | --- | --- |
| 共享字段 | `RemarkEditor` 消费公开 `ZxTextEditorField`，父表单持有唯一文档；继承真实 ElForm disabled；标准校验转接 field.validate | 实际 ElForm/Field 挂载，disabled 开关改变 editor.isEditable；原生规则与 submit pending 测试 |
| 只读/摘要 | `RemarkDisplay` 经 A 接纳后使用公开 safe-html；服务端 remarkText 优先；草稿缺少派生值时用公开文本投影；摘要 160 grapheme | Unicode/组合 emoji、null、错误与草稿摘要回归；同组合法向量安全渲染 |
| 七入口 | 用户、角色、岗位、字典类型、字典数据、参数、生成器表配置使用文档/null | mounted 读取/失败/重试/替换及写入测试；用户/角色另由主执行者补充未保存保护 |
| 原生表单保护 | 参数、字典类型/数据复用 useFormDialog 的实际 isDirty，并将字段未完成状态纳入同一 canDiscard；取消、遮罩关闭和跨记录重用保护；写入中拒绝退休 | 现有 EditorReadLifecycle/RemainingEditorReadLifecycle 增补 dirty cancel/replacement；字典数据提交不夹带 remarkText |
| Formily | 岗位 `composite:true, group:false`，值为 object/null，壳层没有另一份编辑正文；pending 纳入取消保护 | 真正 public SchemaForm + 业务 RemarkEditor + public Field 的 5 项 DOM 探针，无 SchemaForm stub |
| 生成配置 | `useEditorRead` 会话、规范写 DTO 快照、取消/路由保护、读取错误重试、保存后接收权威详情建立新基线；返回按钮与该次 navigation 共用一次放弃决定，finally 撤销临时许可 | GenEditSession 4 项 mounted 探针；路由 guard 回调被调用，真实导航 UI 未测 |
| 生成产物 | 显式 htmlType=remark；普通/树/主子表、任意字段名；只读 Text 不回写；子行 DTO 逐合法字段挑选、显示序号不污染模型、删除依赖行身份 | 实际 Python import/ORM/service/DTO 执行与实际 Vue SFC compileScript/transpile 后调用 submit；不是仅模板字符串断言 |
| 公开读契约 | 生成 controller 的 create/detail/update 使用 ReadModel，列表/树返回有类型的 ReadModel 集合 | 独立 `test_remark_generated_openapi.py` 实际导入生成 controller/VO 并调用 FastAPI.openapi，8 项测试 |

## SchemaForm 通用根因修复

真实探针暴露两个所属库生命周期问题，均修在 `ZXUI/packages/schema-form/src/formily/`：

1. ref 退场与 adapter beforeUnmount 会重复 dispose；第二次 capture 可能覆盖第一次保存的交互草稿。runtime port 现在幂等退休，先标记 disposed，后续 report/restore 忽略退休 port。
2. 在 ref callback 立即 restore 早于子字段 mounted。现在由 adapter `onMounted` 恢复，子字段资源已就绪且保留一次 nextTick 的既有时序；未使用业务副本正文或延时器。

恢复阶段遵循 Vue 官方的同步子组件 mounted 时序；异步资源的就绪由字段自身恢复协议接续，不由业务 timer 推迟。参见 [Vue 生命周期 API](https://vuejs.org/api/composition-api-lifecycle#onmounted)。

新增 `formily-composite-disposal.test.ts` 先证实 capture 调用两次、恢复发生于 child mounted 前，再验证只 capture 一次且恢复发生于 mounted 后。库完整测试 **11 文件 125 项通过**；typecheck、build 和所属三个文件 ESLint 均退出 0。候选 `zxio-schema-form-0.1.0-remark-a.20261022.1.tgz` SHA-256：`1fadc9526ab14583a82172a88216fc126a1cf731b0479ca386be6c29c7545be2`。

执行命令（ZXUI task 根目录）：

```sh
pnpm exec vitest run --config packages/schema-form/vitest.config.mts
pnpm -C packages/schema-form typecheck
pnpm -C packages/schema-form build
```

日志：`/tmp/remark-schemaform-all-tests.log`、`/tmp/remark-schemaform-typecheck.log`、`/tmp/remark-schemaform-build.log`、`/tmp/remark-schemaform-lint.log`。从 package 子目录运行旧测试会改变 fixture cwd，已有 field-library 测试因此读取错误路径；上述仓库根目录命令覆盖全部测试。

## 真实 Formily 与公开字段往返

`tests/unit/components/RemarkFormilyIntegration.test.ts` 使用真实 `@zxio/schema-form/formily`、真实业务 `RemarkEditor`、公开 Field/TextEditor；唯一替身是公开主题 owner/portal port，测试宿主显式提供 shortcut platform。没有为 DOM 环境空 platform 向业务增加全局基础设施。

5 项探针证明：

- 原生 ElForm disabled 向公开字段传递。
- null/object 唯一值所有权；首次回填不 dirty，格式编辑 dirty；submit 取 canonical document，authority/null 回填重置基线。
- composition 未结束时阻止 submit，结束后保留中文并提交。
- composition 输入后隐藏/显示仍保留中文；字段在 capture 边界发布稳定父值，恢复没有另存正文。
- 链接草稿隐藏/显示恢复，验证短暂 disabled 不丢草稿，未完成时 submit=false，显式取消后才可提交。

`RemarkPackageRoundtrip.test.ts` 消费 `shared/remarks/remark-a-v1/manifest.json` 的**全部 25 个合法文档向量**，每个经过公开 `/core` 接纳 → JSON stringify/parse → public Field 挂载 → public getDocument 再接纳 → 卸载重挂 → safe-html 输出。两次 canonical document 精确相等；单空段归 null 后比较，避免随机空块 ID。safe-html 无 script/javascript。manifest 当前为 102 项：25 valid、73 invalid、4 plaintext，故文档向量共 98 项；非法向量由库/Python 共享向量测试覆盖。

源码模式以公开 `zxuiSourcePlugin` 同时启用 `@zxio/text-editor`、`@zxio/schema-form`，并 dedupe Vue/Formily。两文件 **30/30 通过**，最终可重放配置为 `ruoyi-fastapi-frontend/vitest.remark-source.config.ts`，日志 `/tmp/remark-public-source-release-roundtrip.log`（早期探针 `/tmp/remark-public-source-roundtrip.log` 亦为 30/30）。源码模式存在 Vue `Missing ref owner context` warning；不以这一模式声称真实主题或焦点行为已通过。最终实际安装 text-editor `1.0.0-remark-a.20261022.3`（tarball SHA-256 `488ba07bc021622efa282fab9a063136acf3c48e252908b0c65d0ee26dd9443b`）和 SchemaForm `0.1.0-remark-a.20261022.1` 后，使用普通 `vitest.config.ts`、无源码 alias 运行**同两文件 30/30 通过**（`/tmp/remark-public-installed-roundtrip.log`），该 warning 未出现。

复现命令（frontend 根目录；ZXUI 路径须指向已准备的 task checkout）：

```sh
VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus/.worktrees/generic-remark-rich-text yarn vitest run --config vitest.remark-source.config.ts
yarn vitest run tests/unit/components/RemarkPackageRoundtrip.test.ts tests/unit/components/RemarkFormilyIntegration.test.ts
```

## 生成器真实执行验证

命令（应用 backend）：

```sh
./venv/bin/python -m pytest tests/unit/module_generator/test_editor_templates.py tests/unit/module_generator/test_remark_generated_openapi.py -q -n0 --no-cov
```

结果：**69/69 通过**，日志 `/tmp/remark-generator-final-tests.log`。覆盖：

- Vue3 crud/tree/sub 主字段、独立子字段及任意名称；insert/edit/list 标志，显式语义、真实 nullable JSON 来源，Vue2 所有入口拒绝，非备注 JSON 与旧 editor 回归。
- 全部 Python 模板 AST；实际生成 Vue SFC 经 `@vue/compiler-sfc` compileScript/compileTemplate 编译。
- 实际生成 VO 的文档/null/遗漏往返、只读派生 Text 拒绝；实际生成 ORM 的 SQLite JSON/null 保存读回；实际生成 service/repository 父子写入读取。
- 实际生成 Vue submitForm 执行、JSON 序列化后进入实际生成 VO，额外注入旧 row.index 仍不会泄漏到写 DTO。修复前为 extra_forbidden 422，修复后通过。
- 生成子表 FK 使用主表真实主键，保存子行前关联新父 ID；读取直接用 ReadModel.model_validate(ORM)，保留 snake_case 文档来源与派生投影。
- 主表/子表的派生 `_text` Python 名或 `Text` 客户端名与真实列冲突时，policy 明确拒绝；4 例先红后绿，不生成无法导入或覆盖真实列的产物。
- 实际 FastAPI.openapi 公开 readOnly `${field}Text`；create 201 和 CRUD/tree/sub 各响应模型接受并保留文档与子行投影。

SQLite/内存 service 探针不等于真实 MySQL 生成应用验收；后者与本规格数据库演练分别记录。

## 应用质量门禁

| 命令/范围 | 当前证据 |
| --- | --- |
| 4 文件 focused lifecycle/GenEdit/Post/Remark | 65/65，通过 `/tmp/remark-current-focused-tests.log` |
| Config/Dict 新 dirty guard 两例 | 2/2，通过 `/tmp/remark-config-dict-guards.log` |
| ui:standards | 541 文件 0 违规；相关 25 tests 通过，`/tmp/remark-agent-ui-standards.log` |
| mock:contracts | 75/75 critical contracts；247 operations，`/tmp/remark-agent-mock-contracts.log`；缺少完整 schema coverage 的既有项由工具原样报告 |
| 最终候选包双文件 30 tests | 30/30，无源码 alias；`/tmp/remark-public-installed-roundtrip.log` |
| yarn lint:check / yarn type-check | 均 exit 0；`/tmp/remark-final-lint.log`、`/tmp/remark-final-typecheck.log` |
| yarn test:run | exit 1；154 文件中 149 通过 / 5 失败；1434 tests 中 1422 通过 / 12 失败，失败集合与输入基线精确相等，0 新增；`/tmp/remark-final-tests.log` |
| yarn mock:overlays | exit 0；11 overlays、0 failures、65 个工具列明的 warning；`/tmp/remark-final-mock-overlays.log` |
| 源码生产构建 | exit 0，8743 modules，2m 2s；`/tmp/remark-source-release-build.log` |
| 安装候选包生产构建 | exit 0，7735 modules，1m；`/tmp/remark-installed-release-build.log` |

最终全量在两候选包安装及用户/角色改动收敛后执行，12 条失败测试的名称与输入快照集合精确一致（added=0，removed=0），无 unhandled errors。本轮相关测试全部通过；全量命令仍如实记为 exit 1。用户/角色及相邻生命周期专组另有 67/67 通过证据 `/tmp/remark-native-guards-final.log`。GenEdit 返回双询问回归先红 1 例，再 4/4 通过 `/tmp/remark-gen-return-green.log`。

### 可复现历史基线

从输入 HEAD `git archive` 提取 frontend 到仓库外临时目录，仅 symlink 当前 task node_modules，未修改源工作区。基线目录引用 `/tmp/remark-frontend-input-baseline-path`，日志 `/tmp/remark-frontend-input-baseline.log`。同组 6 文件 69 tests 中 **5 文件 12 项失败，57 项通过**，输入版本 EditorReadLifecycle 通过：

| 既有测试文件 | 失败数 | 原因 |
| --- | --- | --- |
| generator-form-runtime | 1 | 既有 HTML runtime fixture import map 缺 `@zxio/zxui/core` |
| project.test | 1 | locked/mismatch 场景期望 400，实际 409 |
| WebSocketSession | 2 | disconnect 后迟到 reconnect/ticket 生命周期 |
| devMenuHotSync | 2 | SSE probe/fallback poll 时序 |
| user store | 6 | CSRF/getSecuritySessionVersion 测试 mock 不全 |

这些失败与最终失败需逐项比较，不能将其他新失败笼统记为基线。测试日志位于本机 `/tmp`，属于执行证据索引，不是发布运行依赖。

## 未验证与交接

- 最终 text-editor/SchemaForm 两包的同组 30 项公开 DOM 探针已通过；应用最终质量门禁结果见上表。
- 用户/角色脏状态修复已由主执行者收敛；最终源码与安装包构建均已通过。OpenAPI/生成客户端由 contract 执行者统一生成，本分工未并发生成。
- 真实七入口操作、生成应用浏览器操作、明暗主题/density、链接浮层归属/焦点、外部粘贴和键盘交互仍需获授权的真实界面证据。任务 22 不因 DOM/编译/HTTP 证据勾选完成。
- 本分工不实施生产迁移，不将 SQLite 探针、模拟 JSON 持久化或公开 owner port 测试替身表述为生产数据库/真实主题验收。

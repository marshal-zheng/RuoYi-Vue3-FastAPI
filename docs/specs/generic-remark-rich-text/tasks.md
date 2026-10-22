# 通用备注富文本与 JSON 存储实现任务

## 执行依据与边界

- 输入：[需求规格](requirements.md)、[技术设计](design.md)。需求与设计已获用户确认；2026-10-22 按用户的 SSD auto 授权自动完成本任务拆分，不再等待规格阶段确认。
- SSD 路径为 `auto-spec`，本轮终点是 `execution_ready`。以下复选框代表待实施工作，生成本文件不代表应用、ZXUI 或数据库已修改。
- 独立只读澄清未发现关键歧义；设计复审第 2 轮通过，覆盖 59/59 条验收标准。复审补充的 Vue2/主子表能力边界见需求的 Clarifications；详细证据见 [规格检查记录](spec-review.md)。
- 业务仓路径相对仓库根目录。`ZXUI/` 指 `/Users/hqz/Downloads/element-plus/`；它是独立工作区，应遵循其指令并保留同期修改。下文“新增”文件、接口与参数是实现目标。
- 仅迁移 `sys_user.remark`、`sys_role.remark`、`sys_post.remark`、`sys_dict_type.remark`、`sys_dict_data.remark`、`sys_config.remark`、`gen_table.remark`。字段语义、领域排除项及范围外正文消费者以需求为准。
- **任务 6–10 是数据库启动门槛**：转换器、前置阻断、正式 revision、所有初始化/受管写入源及编排未共同就绪前，不对有数据的环境启动新 ORM、自动 dev-sync 或部署。任务顺序是代码实施顺序，不是逐任务发布顺序。
- 每项只在其变更与验证证据齐全后勾选。验证失败先修复责任模块；未验证项不得以“编译通过”或 checkbox 代替。真实迁移只在隔离库或可恢复副本演练，生产变更不属于本规格编写授权。

## 依赖安排

| 阶段 | 任务 | 输出及后续门槛 |
| --- | --- | --- |
| 契约与库能力 | 1–5 | 消费者清单、共享样例、ZXUI A 配置与字段适配、Python 契约 |
| 数据转换与写入源 | 6–10 | 可恢复转换、Atlas 前置保护、JSON 映射与正式迁移、稳定种子/发布包、统一 verify |
| API 与派生输出 | 11–13 | 七字段读写契约、导入导出与缓存、OpenAPI/客户端/mock |
| 业务与生成器 | 14–19 | 公开组件接入、七处编辑入口、生成配置及全部支持模板 |
| 验收与交付准备 | 20–23 | 真实数据库演练、候选包与质量门禁、真实业务矩阵、文档和独立最终审查 |

每项“依赖”均为必须完成的前置任务；编号已按拓扑顺序排列。无直接依赖的任务可以独立实施，但同一文件/工作区的修改与数据库运行不得并发冲突。源码直连用于联调，候选包验证用于确认实际交付形态，两者都要有证据。

## 任务清单

- [x] 1. 复核七字段消费者与实施基线
  - 依赖：无。
  - 读取当前 AGENTS、适用前后端约定、已确认规格和两仓状态；保存已有改动基线，按实施技能选择安全写入位置，不覆盖同期工作，不默认创建到 `.codex`。
  - 沿七字段逐项列出编辑入口、写入 DTO/内部模型、DO、读取/嵌套响应、列表、Excel、缓存、种子、脚本和生成模板；记录真实调用和无需改动项的依据。
  - 特别核对岗位当前 Formily、用户写入转入 `EditUserModel`、生成器版本/主子表路由和已有完整数据备份消费者；排除领域描述、菜单/任务/通知备注及通知正文。
  - 新增 `docs/reports/generic-remark-rich-text/consumer-matrix.md` 与环境基线，区分源码 revision、dirty 状态、库包版本、数据库标识，不存正文或密钥。
  - 验证：七行主清单均有读写和数据源去向；范围外共享消费者列明回归点，现有失败与本轮问题可区分。
  - _需求追溯: R1.AC1, R1.AC2, R1.AC4, R7.AC5, R11.AC4, R11.AC5_

- [x] 2. 固定跨语言契约样例与边界期望
  - 依赖：任务 1。
  - 新增 `shared/remarks/remark-a-v1/{valid,invalid,plaintext}/` 及 manifest，固定 Document v2 封套、meta、节点/标记精确属性、块 ID 与规范输出；不另建编辑器内核。
  - 覆盖 A 全部格式、hardBreak 标记、嵌套/编号列表、同标记文本合并、单空段落归 null、多空段落/空白保留、Unicode 与 CRLF/CR 归一化、HTML/JSON/公式外观字面量。
  - 给出共享拒绝样例：旧字符串、裸树、错误版本、未知/缺失属性、重复/非法 ID、非空资源、危险/混淆链接、非法父子结构、控制字符、孤立代理码点。
  - 对 5,000 码点、256 KiB、2,000 节点、3 层列表、树深 12、原始容器深 32、href 2,048 分别设置边界与超界样例；注明计数口径、紧凑 UTF-8 序列化及 SQL NULL 语义。
  - 记录保真文本与列表显示文本的独立精确期望、确定性 identity_key/段落 ID 向量；区分“ZXUI 结构可接纳”与“A 策略应拒绝”，避免误要求两套接纳集合相同。
  - 验证：样例 JSON 可解析且版本明确，合法样例通过当前 ZXUI 公开 `/core`；未实现的 A 策略检查标为待实现，后续两端消费同一组向量。
  - _需求追溯: R2.AC6, R5.AC1, R5.AC2, R5.AC3, R5.AC4, R6.AC1, R6.AC2, R6.AC3, R6.AC4, R6.AC6, R9.AC2, R11.AC1_

- [x] 3. 在 ZXUI 实现基础富文本配置与一致的内容接纳
  - 依赖：任务 2。
  - 修改 `ZXUI/packages/text-editor/src/{props.ts,editor/runtime-extensions.ts,core/}` 及所属命令、粘贴、工具栏入口；新增公开 `contentProfile`、`BASIC_RICH_TEXT_PROFILE`、`contentLimits`，更新公开类型与文档。
  - 保持统一 schema 和现有 full 模式消费者；basic-rich-text 只装配 A 的交互，不启动上传、提及、协作、页式布局、AI、斜杠菜单或二进制导出服务。
  - 对工具栏、快捷键、输入规则、粘贴、公开插入及程序化替换使用同一内容策略；协调结构接纳、稳定 ID 修复、完整校验和 update 事件顺序，合法分段不能被瞬时缺 ID 拦截。
  - 实现设计规定的粘贴投影：标题/引用转正文，代码保留文字换行，表格按行与 TAB 保留文字，危险链接去标记，图片/文件不产生资源并提示；程序化非法输入直接拒绝。
  - 普通输入超限保留当前编辑并阻止提交，极大粘贴整次拒绝保留原内容；IME 未结束不误提交。错误分别说明正文与资源限制，不静默截断。
  - 验证：针对各内容入口、粘贴、预算和 ID 修复补必要回归；执行共享向量，证明 A 之外无法绕过，full 模式的真实消费者不受影响。
  - _需求追溯: R1.AC4, R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC6, R3.AC1, R3.AC3, R3.AC5, R6.AC6, R11.AC1_

- [x] 4. 在 ZXUI 实现标准编辑字段并完成 Formily 接入探针
  - 依赖：任务 3。
  - 在 text-editor 新增并公开 `ZxTextEditorField`：标准 modelValue、focus/blur、disabled/readonly、messages、id/aria、edit-state 及 focus/validate/captureEdit/restoreEdit，转接既有 documentValue。
  - null 展示合法空段落但挂载不 emit；外部回填不制造 ID/元数据变化和 dirty；清空输出 null、撤销恢复；记录会话重建清除撤销栈。
  - 将 composition、链接浮层草稿、焦点、临时隐藏恢复和卸载归字段生命周期管理；captureEdit 不保存另一份权威正文，text-editor 不反向依赖 schema-form。
  - 以 `ZXUI/packages/schema-form/src/formily/{SchemaForm.vue,bindings.ts}` 的真实协议试接对象/null、`composite:true, group:false`、错误路径与 submit blocking；若发现通用缺口修所属库，不用字符串或页面双状态绕过。
  - 验证：null/文档回填不 dirty，格式编辑会 dirty；隐藏恢复、切换记录、只读/禁用、错误 focus、中文输入及弹框链接浮层行为有可复现证据。未做真实界面验证的项保留至任务 22。
  - _需求追溯: R2.AC2, R2.AC5, R3.AC1, R3.AC3, R3.AC4, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R11.AC2_

- [x] 5. 实现 Python 受限文档、稳定转换与两类文本投影
  - 依赖：任务 2。
  - 新增 `ruoyi-fastapi-backend/common/remark_document_v1.py` 和 `module_admin/entity/vo/remark_vo.py`，落实设计的 validate_remark、plain_to_remark、remark_literal_text、remark_display_text、remark_to_storage。
  - 以判别联合和 extra forbid 定义精确封套/节点/标记；递归解析前迭代检查预算，严格整数、ID 唯一性、链接安全、控制字符和资源为空，失败走现有可定位错误协议且不回显全文。
  - 严格区分运行时对象输入与显式纯文本转换；完整对象序列化保留必需 null 属性，不二次编码，不让别名策略改写文档键；只把设计规定的单空段落归 null。
  - 固定纯文本换行转换和基于表/主键/全文/段号的 SHA-256 ID；literal 投影不 trim，display 投影保留列表编号、缩进与空白，链接仅输出显示文字。
  - v1 codec 保持无 ORM/业务服务依赖，可供正式历史迁移冻结重放；不引入 ProseMirror 复刻或常驻 Node 服务。
  - 验证：同一向量的 Python/ZXUI 接纳与规范输出一致；新增拒绝、预算前置、纯文本精确相等和重复构造确定性测试；测试不把上游结构校验等同链接安全。
  - _需求追溯: R5.AC1, R5.AC2, R5.AC3, R5.AC4, R6.AC1, R6.AC2, R6.AC3, R6.AC4, R6.AC6, R7.AC3, R8.AC4, R9.AC2, R9.AC3, R11.AC1_

- [x] 6. 实现七列历史数据转换器与可恢复物理状态
  - 依赖：任务 5。
  - 新增 `ruoyi-fastapi-backend/scripts/data_migrations/remark_document_v2.py`，使用同步 SQLAlchemy Core 与冻结 codec，固定七表/主键清单，不导入最新业务 ORM。
  - 先只读预检类型、行数、NULL/空串、长度、控制字符、预算、临时列冲突与目标方言；输出数据库/schema 指纹、阶段、主键和备份引用，报告不含完整正文。
  - 按设计识别缺表、旧列、回填中、已切换、JSON 完成与异常组合；绑定目标库备份 manifest、真实停写声明、二次源摘要检查和迁移互斥锁。锁不能代替停止旧应用、导入、脚本及热同步。
  - 实现加 `remark__json_v2`、每批 500 行 keyset 回填、已有值精确核对、逐行正文等价与主键集合/计数验证；SQL NULL 与 JSON null 分开检查，不用空目标跳过源行。
  - 核验后按方言改名，保留 `remark__text_v1` 至全局验证和报告持久化；全部七表通过再清旧列。中断按物理状态恢复，不依据单个本地报告猜进度，不覆盖已验证 JSON。
  - 验证：定向测试每种状态、异常冲突、摘要不符、超限、重复运行和失败定位；任何错误均保留原值/备份。真实 MySQL DDL 与恢复证据留到任务 20，不用 mock 冒充。
  - _需求追溯: R5.AC3, R9.AC1, R9.AC2, R9.AC3, R9.AC4, R9.AC5, R9.AC6, R10.AC4, R11.AC3_

- [x] 7. 在数据库统一入口先接入迁移前置保护
  - 依赖：任务 6。
  - 修改 `ruoyi-fastapi-backend/scripts/db.py`、`scripts/internal/db_workflow/dev_sync_service.py`：声明验证后、Atlas schema apply 前执行备注预检/转换；本任务先落保护，任务 8 才修改 ORM 类型。
  - 新增设计中的 remark-migration-check 只读子命令及 dev-sync/deploy 的 remark-backup-manifest、remark-writers-stopped 参数；CLI help 说明它们是前置凭据，不能自动停止其他进程。
  - 自动启动发现非空旧库且缺备份/停写条件时退出并输出统一恢复入口；不得先改列、启动旧结构或调用 seed 补救。空库与已验证 JSON 的检查路径单独处理。
  - 为 Alembic `Config.attributes` 约定传入已核对上下文；临时 finalize 库用显式隔离上下文，不能将豁免传播至普通目标库。
  - 验证：调用顺序证明迁移在 schema apply 之前；缺前提或转换失败时 schema runner/受管写入完全不执行；只读命令不写库，错误能定位当前阶段与下一动作。
  - _需求追溯: R9.AC1, R9.AC6, R10.AC2, R10.AC3, R10.AC4, R11.AC3_

- [x] 8. 交付七字段 JSON 映射、metadata 与手工正式 revision
  - 依赖：任务 7。
  - 修改实际 `module_admin/entity/do/{user_do,role_do,post_do,dict_do,config_do}.py` 与 `module_generator/entity/do/gen_do.py` 的七列为 `JSON(none_as_null=True)`、nullable、无随机默认；其余同名字段不动。
  - 将生成器既有模型纳入 `scripts/internal/db_workflow/schema_apply_atlas.py` 和 `alembic/env.py`；明确空库 gen_table/gen_table_column 建表完整性，不因 metadata 补登记重建已有数据。
  - 按实施时真实 head 编写手工 revision，调用冻结转换器；缺表走审核后的新建结构，有数据旧列须有任务 7 上下文。直接 upgrade 缺条件必须拒绝；downgrade 明确拒绝有损自动回退并指向恢复流程。
  - 在实际 autogenerate 集成处增加仅针对七列的字符串→JSON AlterColumnOp 保护，禁止未经数据转换的裸 ALTER；不扩展成通用迁移框架。
  - 验证：MySQL/PostgreSQL DDL 编译、SQL NULL/整文档替换映射、正式 revision 链及空库结构；检查 revision 不导入最新 DTO/业务服务。尚未完成任务 9–10 时保持启动门槛关闭。
  - _需求追溯: R1.AC2, R5.AC1, R5.AC3, R5.AC5, R8.AC1, R10.AC1, R10.AC3, R10.AC5_

- [x] 9. 收敛种子、受管声明与历史发布包的写入边界
  - 依赖：任务 5、任务 8。
  - 修改 `scripts/internal/bootstrap_seed.py` 与 `scripts/internal/db_workflow/capability_declaration_compiler.py`，初始用户/角色/岗位及字典类型/字典数据/配置在明确入库或编译边界转完整 JSON；声明可继续写文本。
  - 所有构造使用最终表及稳定主键的 identity_key；先规范化再计算新产物 checksum，不写时间戳或随机 ID，重复编译与迁移结果一致。
  - 在 `finalize_release_service.py`、`deploy_release_service.py` 的真实历史产物消费边界，先校验原始 checksum，再仅对三类受管实体且目标列已为 JSON 的文本 remark 作内存转换。
  - 保留历史 artifact ID/文件/checksum/账本；新产物直接 JSON，planner/applier 比较规范对象，不重置 managed_scope/所有权，不以种子覆盖非受管备注。
  - 验证：两次编译/同步无无意义差异，旧发布包原文件不变且可重放，受管内容修改与纯格式转换分别报告，非受管记录保真；补受影响种子夹具。
  - _需求追溯: R1.AC3, R8.AC3, R8.AC4, R8.AC5, R9.AC2, R10.AC1, R10.AC3, R11.AC3_

- [x] 10. 闭合 dev-sync、finalize、deploy 与 verify 编排
  - 依赖：任务 7、任务 8、任务 9。
  - 在 `scripts/db.py` 与 `scripts/internal/db_workflow/{dev_sync_service,finalize_release_service,deploy_release_service,workflow_verify_service}.py` 完成共享前置/后置核验，避免入口各写一份转换。
  - dev-sync 固定为声明验证→转换→Atlas→受管对齐→备注后验；临时旧列未清理或任一步失败不得进入后一步。
  - finalize 在隔离库先升正式 head 再生成受管产物，七列不再产生自动类型漂移；deploy 先正式 revision 再发布包，正式环境不调用开发 Atlas 同步。
  - verify 同时报告结构、文档接纳、SQL NULL、迁移残留状态及受管目标态；输出具体阶段，保留失败上下文，不承诺跨 DDL/数据/产物自动全局回滚。
  - 验证：更新现有 db_workflow/finalize/deploy/managed 测试；空库、旧库、JSON 库与失败重入路径有可判定结果，数据写入源全部就绪才开放后续受控集成运行。
  - _需求追溯: R8.AC3, R8.AC4, R9.AC5, R9.AC6, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R11.AC3_

- [x] 11. 同步七业务写入 DTO、读取投影与事务契约
  - 依赖：任务 5、任务 8、任务 10。
  - 覆盖 `module_admin/entity/vo/`、`modules/system/application/{read_models,services}/`、实际命令/查询处理器及 `module_generator/entity/vo/gen_vo.py` 和生成器服务。沿任务 1 清单改真实路径，不仅改旧通用模型。
  - remark 仅接文档/null，创建遗漏为空、更新遗漏保持、显式 null 清空；整份 JSON 替换，避免嵌套原地修改漏写。同步用户写入内部 EditUserModel，状态/权限专用接口不顺带写备注。
  - 查询模型从实体写模型解耦，保留真实筛选/分页，不让递归文档经 as_query 进入 GET；读模型输出完整 remark 与服务端只读 remarkText，写边界拒绝 remarkText。
  - 覆盖详情、分页、用户资料及用户关联角色/岗位等嵌套响应；读取到旧字符串或损坏 JSON 明确报一致性错误，不能以 null 回显后覆盖。
  - 保持现有权限、字段白名单与事务；文档校验失败不部分保存其他字段，ProblemDetails 定位 remark，日志不回显全文。
  - 验证：七业务创建/修改/读回契约、遗漏/清空/仅改状态、内部二次验证、嵌套读取、非法文档/无权限无写入与 GET/OpenAPI 参数；使用受控测试库，不碰日常历史库。
  - _需求追溯: R1.AC1, R1.AC3, R5.AC1, R5.AC3, R5.AC4, R5.AC5, R5.AC6, R6.AC1, R6.AC3, R6.AC5, R7.AC6, R8.AC1, R11.AC1_

- [x] 12. 改造服务端 Excel、既有导入和缓存消费者
  - 依赖：任务 11。
  - 各真实导出服务从已校验文档派生 display 文本，再交 `utils/excel_util.py`；扩展显式文字列处理，保证 `= + - @` 开头仍为字符串单元格，不给原文添加可见前缀。
  - 仅在任务 1 确认已有备注列导入的入口显式 plain_to_remark；不存在则记录无需变更，不新增模板/接口。HTML、JSON 和公式外观均按字面文字。
  - 对包含七字段的完整备份/序列化链路保存 JSON；Excel 定位为文本交换，文档说明不承诺格式无损。
  - 更新字典记录缓存序列化与精准刷新流程，禁止 default=str 掩盖模型；配置键值缓存保持值语义，只清理确有旧记录的缓存，不全清 Redis。
  - 验证：实际 xlsx 读回内容/单元格类型无公式、空白换行和列表顺序正确；导入不解析字面量；刷新后关联读取不返回旧字符串、不混淆字典标签或配置值。
  - _需求追溯: R7.AC1, R7.AC3, R7.AC4, R7.AC5, R7.AC6, R8.AC5, R11.AC2_

- [x] 13. 生成 OpenAPI、客户端并收敛手写类型与 mock
  - 依赖：任务 11、任务 12。
  - 通过 `ruoyi-fastapi-backend/scripts/export_openapi.py` 生成 `shared/openapi.json`，再通过 `scripts/generate-api-types.sh` 生成前端 `src/api/_generated/`；不手改生成文件，也不把 RemarkDocument 简化为 any/object。
  - 标明 remarkText readOnly，检查递归判别结构、nullable、请求必填/遗漏语义、七路径及关联响应；公开 ZXUI 文档类型由库提供，业务只做必要类型收窄。
  - 同步 `ruoyi-fastapi-frontend/src/api/` 手写适配、`src/mocks/` handler/store/seed、测试夹具与示例；删除范围内字符串 fallback，不误改领域 mock 或已有正文 editor。
  - 使用仓库 artifact 为默认输入；如核对 live API，显式使用 8088，不能照搬现有脚本的 8000 默认值。
  - 验证：重新生成无漂移，前后端契约测试及 mock:contracts/mock:overlays 通过；请求/响应样例证明 JSON 未二次编码、readonly 字段不进写 DTO。
  - _需求追溯: R1.AC3, R1.AC4, R3.AC1, R5.AC6, R8.AC5, R11.AC1_

- [x] 14. 接入公开包与统一 Remark 编辑/只读组件
  - 依赖：任务 3、任务 4、任务 13。
  - 在前端 package.json/锁文件声明 `@zxio/text-editor`，经 `vite/zxui-theme-packages.ts` 现有功能包机制登记源码模式，消费 `src/theme/zx-theme-packages.ts` 的统一主题策略与公开样式出口。
  - 新增 `src/components/ui/Remark/{RemarkEditor.vue,RemarkDisplay.vue,contract.ts}`：编辑器只选择 A profile/预算及业务提示，值仍由父表单拥有；不复制内核或补写库类型。
  - 只读组件调用公开根出口 `renderDocumentToHTML` 的 safe-html 策略并处理诊断；v-html 仅此安全结果边界。无备注与加载/渲染失败分别显示，列表使用服务端 remarkText。
  - 统一 160 字素簇摘要，不拆组合字符或 emoji；完整内容仍可阅读。摘要不挂编辑实例，完整展示不初始化上传或协作服务。
  - 复用 FormDialog/FormGrid 及现有错误入口，适配字段焦点与未完成编辑状态；主题、密度和浮层归属由 ZXUI 处理，不加核心 CSS 变量覆盖或私有 alias。
  - 验证：源码直连 `VITE_ZXUI_LOCAL=true`、`VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` 下公开导入/样式有效；只读安全、Unicode 摘要、null/错误区分与无重复 emit 回归通过。实际包模式另见任务 21。
  - _需求追溯: R3.AC1, R3.AC2, R3.AC3, R3.AC4, R3.AC5, R4.AC1, R4.AC3, R4.AC4, R6.AC2, R7.AC1, R7.AC2_

- [x] 15. 迁移用户弹框与角色抽屉
  - 依赖：任务 14。
  - 修改 `src/views/system/user/components/UserFormDialog.vue`、`src/views/system/role/components/RoleFormDrawer.vue` 及真实读取/提交适配：原字符串初值改 null，完整文档绑定，整行字段布局与原 FormInstance 不变。
  - 沿原记录身份/加载会话处理读取、快速切换、失败重试、关闭重开与未保存保护；仅用户编辑产生 dirty，换记录重建编辑器会话，不携带撤销栈。
  - 沿用保存结果核对，校验失败或结果未知保留输入；成功后使用权威响应或重新读取重置基线，不能以客户端摘要替代文档。
  - 更新相邻列表/详情消费者和关联响应适配，移除两入口的字符串校验、maxlength=500 等旧假设。
  - 验证：用户/角色分别覆盖创建、保存重开、格式修改、清空/撤销、仅修改其他字段、加载/提交失败、取消保护及只读权限；真实界面证据汇入任务 22。
  - _需求追溯: R1.AC1, R1.AC3, R2.AC1, R2.AC2, R2.AC5, R2.AC6, R4.AC1, R4.AC3, R4.AC4, R4.AC5, R7.AC1, R7.AC2, R11.AC2_

- [x] 16. 迁移字典类型、字典数据与参数设置
  - 依赖：任务 14。
  - 修改 `src/views/system/dict/components/DictDlg.vue`、`src/views/system/dict/data.vue`、`src/views/system/config/components/ConfigDlg.vue` 及真实列表/详情/提交路径，统一 RemarkEditor、null 初值和文档 DTO。
  - 原生表单遵循整行布局、单一列数策略和字段反馈，不为本次控件重复设置标签、间距或字段 span；保留既有权限与读取会话。
  - 字典列表/提示使用 remarkText、完整内容使用 RemarkDisplay；字典标签、字典值、配置键值保持业务原义，缓存刷新使用任务 12 链路。
  - 验证：三个入口分别完成保存/重开/清空、回填不 dirty、格式编辑 dirty、快速切换、保存失败保留值；关联使用字典/配置的页面不受对象值污染。
  - _需求追溯: R1.AC1, R1.AC3, R2.AC1, R4.AC1, R4.AC3, R4.AC4, R4.AC5, R7.AC1, R7.AC2, R7.AC6, R11.AC2_

- [x] 17. 迁移岗位 Formily Schema 表单
  - 依赖：任务 4、任务 14。
  - 修改 `src/views/system/post/components/{PostDlg.vue,post-form.ts,post-form.test.ts}`：PostValues、initialPost、toPostDto、字段 schema 与错误映射共同改为文档/null。
  - 使用实际 Formily bindings 注册 `RemarkEditor`，对象字段无内部 properties 展开、null 初值，`composite:true, group:false`；SchemaForm 独占值与验证，业务壳不另存文档也不切换表单引擎。
  - 对接 edit-state、messages、captureEdit/restoreEdit、validate/focus 与已有 submit/result 流程，composition/链接草稿未完成时阻止误提交；错误按 remark 路径归属，不解析文本消息。
  - 验证：现有岗位测试升级并覆盖对象/null 往返、回填 dirty、格式 dirty、隐藏恢复、换记录撤销隔离、失败保留与权威基线。若探针失败修所属 ZXUI 机制再继续，不能降回字符串。
  - _需求追溯: R1.AC1, R2.AC2, R2.AC5, R3.AC3, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R11.AC2_

- [x] 18. 迁移生成器表配置备注
  - 依赖：任务 14。
  - 修改 `src/views/tool/gen/basicInfoForm.vue` 及上层 `editTable.vue` 的配置读取/保存、初值、校验与脏状态，接入同一 RemarkEditor，使用任务 11 的 gen_table 文档契约。
  - 复用当前表配置身份与错误反馈；读取失败不以空文档覆盖，跨表切换销毁旧会话，保存成功重新建立权威基线。
  - 区分“生成器自身 gen_table.remark”与“为业务字段选择 html_type=remark”；本项只完成前者，生成模板改造由任务 19 承担。
  - 验证：表配置详情/保存/重开/清空、富文本格式、加载/提交失败与取消保护；既有生成选项及字段配置不被备注 DTO 顺带覆盖。
  - _需求追溯: R1.AC1, R1.AC3, R2.AC1, R4.AC1, R4.AC3, R4.AC4, R4.AC5, R8.AC1, R11.AC2_

- [x] 19. 交付显式 remark 代码生成与版本/主子表约束
  - 依赖：任务 5、任务 13、任务 14、任务 18。
  - 在 `src/views/tool/gen/editTable.vue` 增加明确 remark 选项；后端 `module_generator/service/gen_service.py` 在保存与所有预览/下载/生成路径装配完整主子表后统一校验：Vue3、nullable JSON、合法字段用途。不能凭名称、长度或 JSON 类型自动选择。
  - Vue2 + 任意主/子 remark 字段明确拒绝并提示 Vue3；保留 Vue2 的其他字段及原 editor 职责。拒绝树身份/关联键/字符串查询等无法满足文档契约的组合，不静默退回 textarea。
  - 更新 `utils/template_util.py` 与 `module_generator/templates/vue/v3/{index.vue,index-tree.vue}.jinja2`、Python DO/VO/service 等实际依赖模板：公开组件导入、null 初值、完整文档 DTO、JSON(none_as_null=True)、共享校验、独立查询模型、只读文本投影及 Excel 输出共同生成。
  - 覆盖 crud/tree/sub 主字段与独立子表循环；子表默认摘要，激活字段才挂编辑器，值属于行模型，稳定会话身份不使用行号。切换处理未完成输入，所有行均校验并定位错误；新增子行默认 null，序列化不变成字符串。
  - 用非固定名称的显式备注字段验证语义选项有效；生成只读文本与字段准确对应，不把任何 JSON 都命名或处理成 remark。普通/树形预览和下载复用同一模板结果。
  - 验证：扩展现有 `tests/unit/module_generator/test_editor_templates.py` 与前端 `tests/generator-form-contract.test.ts`，覆盖支持矩阵、主/子字段、insert/edit/list 标志、Vue2 拒绝及非备注 JSON/旧 editor 回归；实际生成的前后端代码通过解析、类型/构建与保存读回探针，不能只断言字符串片段。
  - _需求追溯: R1.AC2, R1.AC4, R3.AC1, R3.AC5, R5.AC1, R5.AC3, R5.AC6, R6.AC1, R7.AC1, R7.AC2, R7.AC3, R8.AC2, R8.AC5, R11.AC1, R11.AC2_

- [x] 20. 完成隔离 MySQL 升级、空库、故障恢复与 PostgreSQL 路径验证
  - 依赖：任务 6、任务 7、任务 8、任务 9、任务 10、任务 11、任务 12。
  - 使用独立数据库或可恢复副本，明确 DSN/数据库标识与禁止目标；不得把日常 ruoyi-fastapi 数据库、未授权生产或无关数据当演练库。通过统一 db.py 入口，备份正文与恢复资料置于仓库外受限位置。
  - 旧库样例覆盖七表、NULL、空串、前后空格、连续/尾部空行、中文/emoji、CRLF、HTML/JSON/公式样式文本及非受管数据；执行正式 revision 与 dev-sync 各自真实路径，逐行比对 PK、计数、SQL NULL、正文等价、摘要和列状态。
  - 在加列、批次回填、部分表切换、旧列清理处分别注入中断并重跑；同时验证文档超限、控制字符、冲突列、已有目标不符、缺/错 manifest、未停写声明、锁竞争和源摘要变化均阻断，不丢原值。
  - 新库执行 schema→bootstrap→managed→verify，确认七列直接 JSON、生成器表齐全；重复 dev-sync/正式部署保持稳定，旧发布包 checksum/所有权不变，JSON 完成态再执行不覆盖新内容。
  - 验证真实停止写入清单、备份可恢复到相配旧版本；恢复新写入后的故障另做“停写→备份当前→向前修复”演练，确认不存在自动 JSON→VARCHAR 或旧快照覆盖新数据路径。
  - PostgreSQL 至少执行方言映射、参数绑定、NULL、事务改名及恢复分支检查；若有隔离环境执行同等真实演练，否则报告“真实 PostgreSQL 未验证”，不能用编译通过替代。
  - 验证产物：`docs/reports/generic-remark-rich-text/migration-rehearsal.md` 与脱敏分阶段报告，含版本/环境、命令、计数/摘要、失败注入和恢复结果；只有满足前提的环境才可放行后续真实应用验证。
  - _需求追溯: R9.AC1, R9.AC2, R9.AC3, R9.AC4, R9.AC5, R9.AC6, R10.AC1, R10.AC2, R10.AC3, R10.AC4, R10.AC5, R11.AC3, R11.AC4_

- [ ] 21. 完成源码模式、实际候选包与质量门禁
  - 依赖：任务 3、任务 4、任务 13、任务 15、任务 16、任务 17、任务 18、任务 19。
  - ZXUI 按所属仓库工具链执行受影响测试、类型/打包、公开出口与声明边界检查；打出真实候选 tarball，记录源 revision/dirty patch、版本和文件摘要，不以 npm 发布作为前置。
  - 业务仓先用源码直连验证，再关闭 VITE_ZXUI_LOCAL、使用实际 tarball/锁文件完成公开根、core、样式消费及生产构建；如 schema-form 同步修复，候选包一并纳入。避免源码 alias 让缺失的发布出口假通过。
  - 执行同组文档接纳→保存→重新编辑→派生输出检查，确保候选包和源码契约一致；版本变化不可无损接纳时停止并提供显式转换，不开多版本写入旁路。
  - 先跑受影响 Vitest/Pytest 与生成器测试，再完成前端 `yarn lint:check`、`yarn type-check`、`yarn test:run`、`yarn build:prod`、`yarn ui:standards`、mock 契约检查以及后端 Ruff/相关测试门禁。按现有 CI 要求补全必要检查，不反复扩大无关测试。
  - 验证：记录实际命令、退出码、包哈希及两个模式；已有失败单列基线，不把本轮新增失败解释为历史问题，也不声称本地包已发布。
  - _需求追溯: R1.AC4, R3.AC1, R3.AC2, R3.AC3, R3.AC4, R6.AC6, R8.AC5, R11.AC1, R11.AC4_

- [ ] 22. 完成七入口与实际消费者业务验收
  - 依赖：任务 15、任务 16、任务 17、任务 18、任务 19、任务 20、任务 21。
  - 基于已验证数据库和候选应用，用户/角色/岗位/字典类型/字典数据/参数/生成器配置逐行验证新增或编辑、A 格式保存重开及清空；生成器配置无新增入口时记录其真实编辑流程，不虚构页面动作。
  - 至少分别覆盖原生弹框、抽屉、Formily、生成器：中文 composition/Unicode、焦点快捷键、清空撤销、只读禁用、快速切换、回填不 dirty、格式 dirty、取消保护、读取失败、保存失败/结果未知与成功权威回填。
  - 通过实际粘贴、快捷键及程序化内容入口核对 A 限制和超限保留；明暗主题、不同 density、链接浮层归属/焦点需有界面证据。
  - 验证真实列表/提示不出现 JSON、富文本只读保留格式/安全链接、无备注与错误区分、Excel 文件内容/类型、现有备注导入和精准缓存刷新。生成器抽检支持的普通/树形/主子表产物及 Vue2 拒绝。
  - 针对任务 1 的范围外消费者做必要回归：通知正文、任务备注透传、非备注 JSON 和仍在使用的 editor 分支；不将范围外未验收内容计入完成。
  - 使用用户允许的界面验收方式；当前 computer use 未获授权，执行者不得擅自使用。若无其他有效界面证据，将相关项保持未验收并说明，不能用单元测试或截图存在替代真实交互。
  - 验证产物：`docs/reports/generic-remark-rich-text/business-acceptance.md` 按入口/场景记录环境、结果与证据，覆盖以下矩阵；实际失败修复后只重验受影响范围。
  - _需求追溯: R1.AC1, R1.AC4, R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R2.AC6, R3.AC4, R3.AC5, R4.AC1, R4.AC2, R4.AC3, R4.AC4, R4.AC5, R7.AC1, R7.AC2, R7.AC3, R7.AC4, R7.AC6, R8.AC1, R8.AC2, R11.AC2, R11.AC4_

- [ ] 23. 收敛文档、残留路径与独立最终审查
  - 依赖：任务 20、任务 21、任务 22。
  - 更新实际使用/公开接入文档与 `docs/reports/generic-remark-rich-text/acceptance.md`，写清 A 能力、预算、空值、JSON/只读文本、Excel 文本交换限制、备份完整 JSON、生成器能力矩阵和排除范围。
  - 新增或更新升级恢复手册，列出按环境预检、真实停写进程、备份验证、正式迁移、受管/缓存、verify、新应用只读冒烟及恢复写入顺序；分别给出回填/切换/清理/新写入后失败的恢复动作。
  - 全量核对七字段的旧字符串编辑/API/mock/template 分支已清理；只在无真实调用证据时删旧 Editor/依赖，不删除范围外 Quill、wangEditor 或 Vue2 既有职责。
  - 建立每条 AC→实现位置→验证命令/实际证据的最终映射；明确静态、内存、单元/集成、真实业务、真实数据库层级、失败和未验证项。PG 未实测单列，UI 缺证据不得通过。
  - 按 executing-task 的最终审查契约交给独立 reviewer 核对全部 59 条、两仓变更、正式迁移与交付物；修复真实缺口并按需要复验，不用主代理自评代替独立结论。
  - 完成条件：全部实施任务与必要验收有证据、独立审查无阻塞；报告仅声明实际已达到的状态。提交、外部发布、生产迁移和交付清理遵守各自授权边界，不由本文件自动执行。
  - _需求追溯: R1.AC1, R1.AC3, R1.AC4, R6.AC6, R7.AC5, R8.AC5, R9.AC6, R10.AC3, R10.AC5, R11.AC4, R11.AC5_

## 业务验收最小矩阵

所有行都须记录保存重开、清空、格式保持、错误保留与记录身份检查，不能用一个共享组件测试替代七行实际消费者。

| 实际入口 | 主要责任任务 | 额外必须核对 |
| --- | --- | --- |
| 用户 UserFormDialog | 11–15、22 | 内部 EditUserModel、关联角色/岗位、导出与既有导入映射 |
| 角色 RoleFormDrawer | 11–15、22 | 抽屉会话、权限/状态专用更新不清空备注 |
| 岗位 PostDlg / post-form | 11–14、17、22 | Formily 唯一值、对象/null、隐藏恢复、submit blocking |
| 字典类型 DictDlg | 11–14、16、22 | 列表/导出、受管声明稳定性 |
| 字典数据 data.vue | 11–14、16、22 | 字典记录缓存刷新、标签/值不受污染 |
| 参数 ConfigDlg | 11–14、16、22 | 配置键值语义、记录与值缓存区分 |
| 生成器 basicInfoForm | 11–14、18、22 | gen_table 编辑保存与生成选项不互相覆盖 |
| 生成器显式 remark 输出 | 19、22 | Vue3 crud/tree/sub 主子字段；Vue2 拒绝；预览/下载一致 |

## 验证与证据规则

- 本文件中的命令是实施阶段的检查入口，未在规格编写阶段执行。数据库新增子命令/参数只有任务 7 实现并通过验证后才可使用；禁止把设计命令当作当前已存在功能。
- 单元/集成测试优先复用现有 `tests/unit/scripts/`、`tests/unit/module_generator/`、前端表单/生成器测试和 ZXUI 所属包测试；只补契约、状态、跨语言与恢复等有实际回归价值的检查。
- 数据库报告保存脱敏标识、计数、摘要和阶段结果；正文备份不入 Git。UI 验收只使用已获授权的方式，未经授权不用 computer use。
- 任务 23 的证据映射应同时满足“所有 AC 有实现”和“每项通过有正确层级的证据”；规格追溯覆盖不等于实现覆盖，更不等于已部署。

## 验收标准反向索引

以下为任务追溯的反向索引；同一 AC 的实现与验收可能分布于多项任务，列出不代表已通过。

| 验收标准 | 关联任务 |
| --- | --- |
| R1.AC1 | 1, 11, 15, 16, 17, 18, 22, 23 |
| R1.AC2 | 1, 8, 19 |
| R1.AC3 | 9, 11, 13, 15, 16, 18, 23 |
| R1.AC4 | 1, 3, 13, 19, 21, 22, 23 |
| R2.AC1 | 3, 15, 16, 18, 22 |
| R2.AC2 | 3, 4, 15, 17, 22 |
| R2.AC3 | 3, 22 |
| R2.AC4 | 3, 22 |
| R2.AC5 | 4, 15, 17, 22 |
| R2.AC6 | 2, 3, 15, 22 |
| R3.AC1 | 3, 4, 13, 14, 19, 21 |
| R3.AC2 | 14, 21 |
| R3.AC3 | 3, 4, 14, 17, 21 |
| R3.AC4 | 4, 14, 21, 22 |
| R3.AC5 | 3, 14, 19, 22 |
| R4.AC1 | 14, 15, 16, 18, 22 |
| R4.AC2 | 4, 17, 22 |
| R4.AC3 | 4, 14, 15, 16, 17, 18, 22 |
| R4.AC4 | 4, 14, 15, 16, 17, 18, 22 |
| R4.AC5 | 4, 15, 16, 17, 18, 22 |
| R5.AC1 | 2, 5, 8, 11, 19 |
| R5.AC2 | 2, 5 |
| R5.AC3 | 2, 5, 6, 8, 11, 19 |
| R5.AC4 | 2, 5, 11 |
| R5.AC5 | 8, 11 |
| R5.AC6 | 11, 13, 19 |
| R6.AC1 | 2, 5, 11, 19 |
| R6.AC2 | 2, 5, 14 |
| R6.AC3 | 2, 5, 11 |
| R6.AC4 | 2, 5 |
| R6.AC5 | 11 |
| R6.AC6 | 2, 3, 5, 21, 23 |
| R7.AC1 | 12, 14, 15, 16, 19, 22 |
| R7.AC2 | 14, 15, 16, 19, 22 |
| R7.AC3 | 5, 12, 19, 22 |
| R7.AC4 | 12, 22 |
| R7.AC5 | 1, 12, 23 |
| R7.AC6 | 11, 12, 16, 22 |
| R8.AC1 | 8, 11, 18, 22 |
| R8.AC2 | 19, 22 |
| R8.AC3 | 9, 10 |
| R8.AC4 | 5, 9, 10 |
| R8.AC5 | 9, 12, 13, 19, 21, 23 |
| R9.AC1 | 6, 7, 20 |
| R9.AC2 | 2, 5, 6, 9, 20 |
| R9.AC3 | 5, 6, 20 |
| R9.AC4 | 6, 20 |
| R9.AC5 | 6, 10, 20 |
| R9.AC6 | 6, 7, 10, 20, 23 |
| R10.AC1 | 8, 9, 10, 20 |
| R10.AC2 | 7, 10, 20 |
| R10.AC3 | 7, 8, 9, 10, 20, 23 |
| R10.AC4 | 6, 7, 10, 20 |
| R10.AC5 | 8, 20, 23 |
| R11.AC1 | 2, 3, 5, 11, 13, 19, 21 |
| R11.AC2 | 4, 12, 15, 16, 17, 18, 19, 22 |
| R11.AC3 | 6, 7, 9, 10, 20 |
| R11.AC4 | 1, 20, 21, 22, 23 |
| R11.AC5 | 1, 23 |

## 规格状态

- tasks.md：按 SSD auto 自动生成；23 项任务、59/59 验收追溯、依赖拓扑与结构检查通过，已进入 `execution_ready`。
- 实施进度：隔离工作区中已落地库、协议、数据库及七消费者代码，正在最终自动验证与独立审查；真实 UI 由用户接管手测（用户：你完成任务告诉我 交付到源分支我自己测），任务 22 保持未验收。进度证据见 docs/reports/generic-remark-rich-text/acceptance.md，不以代码或勾选替代验收。
- 下一实施入口：继续最终候选包/质量门禁，汇总数据库和前端报告，独立核对59条AC；真实 UI 交由用户手测；已授权交付源分支，正在进行同期依赖保真与集成复验。发布和日常数据库迁移未请求。

## 2026-10-22 交付指令与审查补项

用户明确要求“你完成任务告诉我 交付到源分支我自己测”。据此继续安全合回源分支，真实 UI 归用户手工验收，不将其标为通过；未授权 computer use。任务 21 待最终交付候选和源分支复验，任务 22/23 的完整验收继续保留未完成。

| 审查发现 | 已完成修复及证据 |
| --- | --- |
| 生成子行显示 index 泄漏写 DTO | 逐声明字段构造 DTO，真实 SFC submit→生成 VO；生成器69项通过 |
| 生成只读模型/OpenAPI与派生名冲突 | 真实 controller OpenAPI，主/子派生字段冲突拒绝 |
| 原生和生成配置脏状态、返回重复询问 | 生命周期67项，GenEdit独立4项，通过 |
| 粘贴空白损失、超限删除选中文本 | 实际 clipboard HTML/text、字节拒绝保留选区，库157项通过 |
| Formily隐藏丢IME/链接、超限重挂失败 | 所属库稳定父值、幂等退场、mounted恢复、受控草稿hydration；source/installed各31项通过 |
| 数据库只读失败无报告、恢复列注释、新写后恢复链 | 69项含20真实MySQL +正式metadata专项；见migration报告 |
| 数据库异常和操作/变更审计泄漏正文 | 真实HTTP及持久化审计脱敏；相关后端496项通过 |

这些记录对应本轮连续只读审查中发现、修复和复验的事实，不代替独立最终结论或用户界面验收。

# 文件资产规格 SSD auto 审查记录

前一轮记录保留作历史证据；其 72 条 AC、421 行设计及旧摘要不代表当前版本。当前定向修订见文末“附件类型与回收复查修订”。

## 范围与授权

- 日期：2026-10-22。
- 目标：`docs/specs/file-assets-minio/` 现有 requirements、design、tasks，补齐正式 SSD 流程。
- 用户指令：“使用ssd auto, 该用clarify的用clarify”。记录为 `AUTONOMY: auto-spec`，边界为 `execution_ready`，不启动实现。
- 子代理授权：会话中的用户 AGENTS 指令“任何时候都授权子代理工具使用权限”，结合 SSD 技能要求的只读 clarify 和 evaluator 门禁。本轮不授权子代理改文件。
- 模型策略：遵循用户要求继承主代理模型和推理强度；运行时未暴露可核验具体值，不宣称独立验证了最高配置。
- 工作区已有 438 项改动/未跟踪条目；本轮只编辑目标 spec 及其 SSD 状态和审查记录，不覆盖其他内容。
- 未绑定 work item/initiative；相关北极星工作流指针不可用，本轮以根 AGENTS、已确定方案和当前 spec 为边界。
- `.ssd-run.json` 记录阶段和门禁，不是实现、测试或生产完成证明。

## clarify 扫描与主代理决策

CLARIFY_SCAN_MODE: read-only-subagent
TARGET_REQUIREMENTS: docs/specs/file-assets-minio/requirements.md
SUBAGENT: /root/ssd_asset_clarify
REQUESTED_MODEL: inherit-parent（用户要求）
REQUESTED_REASONING: inherit-parent（用户要求）
ACTUAL_MODEL: unavailable
ACTUAL_REASONING: unavailable
OUTSTANDING_HIGH_IMPACT_AMBIGUITY: none（主代理完成下述写回后）

子代理完整阅读需求并定向核对设计与 `ruoyi-fastapi-frontend/src/utils/session.ts:165–180`，返回两项建议；未编辑文件、未向用户提问、未宣称澄清完成。主代理逐项复核并按 SSD auto 规则采纳默认值，均标记待用户集中复核，不伪装为用户逐条回答。

| 编号 | 歧义与风险 | 采用默认值 | 写回范围 | 待复核 |
| --- | --- | --- | --- | --- |
| CL-01 | 请求取消/响应丢失与提交失败混淆，可能误删已经 READY 或已绑定头像 | 以服务端持久化提交点为准；提交结果不明先核对；提交后取消不撤销，未绑定项按草稿规则回收 | R2.AC4、R6.AC2、R14.AC1、Clarifications | 是：数据与取消语义 |
| CL-02 | “禁止盲重试”未定义与现有 401 单次刷新重发的关系，可能重复写或错误禁用认证恢复 | 上传写接口 401 必须发生在资产行和 PUT 之前；未取消且同主体时刷新后只重发一次；网络/超时/5xx/响应丢失不自动重发 | R2.AC5、R8.AC2、R14.AC1、Clarifications | 是：认证重发与兼容边界 |

### clarify 完成记录

STATUS: CLARIFICATION_COMPLETE
TARGET_REQUIREMENTS_PATH: docs/specs/file-assets-minio/requirements.md
MODIFIED_FILES: docs/specs/file-assets-minio/requirements.md
QUESTIONS: ASKED=0, ANSWERED=2（auto-adopted default）
SESSION: ACCEPTED_BEFORE=4, ACCEPTED_TOTAL=6
DECISION_POSTURE: best-current（提交状态）/ compatibility-first（保留已确认的单次认证恢复）
DECISION_EVIDENCE: 需求提交顺序；现有 session.ts 的明确 401 单次重发与会话隔离
SECTIONS_TOUCHED: R2、R6、R8、R14、Clarifications
NEXT_ACTION: resume writing-specs downstream update
BLOCK_REASON: none
UNBLOCK_ACTION: none

| Category | Status | Evidence/Decision | Next Handling |
| --- | --- | --- | --- |
| 核心目标与业务结果 | Clear | 资产模块、头像、公告及真实生成字段 | 保持 |
| 范围与非目标 | Clear | 后端代理上传、私有桶、单归属、完整硬切 | 保持 |
| 用户角色及差异 | Clear | 草稿上传者与当前业务读取权限分离 | 设计门禁核验 |
| 完整性与一致性 | Clear after writeback | CL-01 区分取消与已提交结果 | 下游同步 |
| 验收可测试性 | Clear after writeback | CL-02 定义可重发与结果不明 | 下游同步 |
| 边界及失败场景 | Clear after writeback | 提交前后取消、竞争、迟到写入 | 故障测试任务 |
| 非功能约束 | Clear | 有界资源、授权、短签名和隔离 | 设计/验证落实 |
| 数据与领域假设 | Clear | 单归属、绑定唯一真源 | 保持 |
| 外部依赖 | Clear within scope | 生产 TBD 有明确阻塞边界 | 不提前选型 |
| 兼容及迁移 | Clear after writeback | 冻结迁移、异常阻断、现有认证重发 | 下游同步 |
| 术语及占位项 | Clear | 领域术语一致，生产 TBD 明确 | 保持 |

## 设计修订与独立 evaluator

- 主代理先同步 CL-01、CL-02 的提交点、错误码、客户端行为和故障验证要求。
- 额外修复容量矛盾：公告允许 1 MiB HTML，但普通 MySQL TEXT 上限不足；改为文本语义 + MySQL MEDIUMTEXT variant。已用现有 venv 中 SQLAlchemy 做纯静态 dialect 编译探针：Text → TEXT，选定 variant → MEDIUMTEXT；未连接数据库。
- 独立 evaluator：`/root/ssd_asset_design_evaluator`，首次评审 PASS；阻塞项 0、需要修订后重审的其他项 0。逐项核验 72 条 AC，覆盖 72、缺失 0，与 6 条 Clarifications 无冲突。评审对象 design.md 共 421 行，其精确 SHA-256 保存在 `.ssd-run.json` 的 evaluator 记录中。
- 主代理在独立 PASS 后同步 tasks，补齐提交前后取消、提交应答不明、401 无副作用及单次重发、未知结果不重发、MEDIUMTEXT/多字节内容容量验证。没有把旧任务未同步本身冒充设计缺陷。
- 子代理只读定向核对了 get_db、头像接口、session.ts、Outbox 模型/消费/调度，未修改任何文件、未运行应用/存储集成测试。模型/推理配置继承父代理，具体值运行时不可核验；本次不存在主代理 fallback 或自评冒充独立 PASS。

### evaluator 的逐项 AC 映射

以下为独立 evaluator 返回的设计行号映射，指向评审时的 421 行 design.md。

| 需求组 | 覆盖 | 设计行号映射 |
| --- | --- | --- |
| R1 | 4/4 | AC1→22–41；AC2→7–18、353–357；AC3→304–318；AC4→43–58、184–196、378–386 |
| R2 | 5/5 | AC1→81–103、204–223；AC2→91–94、268–280、368；AC3→154–160；AC4→156–160、320–327；AC5→169、238、401 |
| R3 | 5/5 | AC1→244–258、342–349；AC2→248–249；AC3→138–148、186–194、250–256；AC4→130、242、248–269、368；AC5→229–238、347、161–170 |
| R4 | 5/5 | AC1→142–152、207–210；AC2→14、209、225、242、340；AC3→208、232–233、367；AC4→132、209、242、337–340；AC5→120、150、312、369 |
| R5 | 5/5 | AC1→136–137、161–164；AC2→146–152、160–163；AC3→161–163、282–294；AC4→11–13、168、190–192、282–300；AC5→161–170、182、401 |
| R6 | 4/4 | AC1→103、146、211；AC2→156–163、397、401；AC3→24、173、298；AC4→137、146、164、298、378–384 |
| R7 | 5/5 | AC1→176–182、299；AC2→11、152、180–182；AC3→166–182、397；AC4→147、397；AC5→161–170、182、380–386 |
| R8 | 5/5 | AC1→168–171；AC2→169、238；AC3→169–171；AC4→172、396；AC5→174、180–182、365–371 |
| R9 | 4/4 | AC1→184–186；AC2→188–194、300；AC3→188–196、398；AC4→186、300、378–386 |
| R10 | 5/5 | AC1→308–313；AC2→160–164、308–316；AC3→314–318；AC4→318、327、407；AC5→320–327、401 |
| R11 | 4/4 | AC1→198–240；AC2→392、403；AC3→49–58、174、298、378–384；AC4→161–163、210–213 |
| R12 | 5/5 | AC1→331–347；AC2→351–357；AC3→359–361；AC4→236、240–242、357；AC5→337、365–372 |
| R13 | 5/5 | AC1→376–381；AC2→380–386；AC3→382–384；AC4→380–386；AC5→382–386、399、411 |
| R14 | 4/4 | AC1→390–401；AC2→394–395；AC3→396–398；AC4→390–403、409–411 |
| R15 | 4/4 | AC1→158–159、342–349；AC2→156、313、320–327、342–349；AC3→242、278、369、407；AC4→24、135、138、171–173、208 |
| R16 | 3/3 | AC1→5、361、411、417；AC2→361、409；AC3→411 |

## 最终结构与追溯验证

独立设计评审 PASS、tasks 同步后，主代理执行 Python 结构/追溯校验与 `git diff --check -- docs/specs/file-assets-minio`，全部通过：

- 三份标题、设计七个必需章节、代码围栏、空白和本地链接有效。
- 16 项需求、72 个唯一 AC；72 个均被 tasks 覆盖，无未知任务引用。
- 19 项任务保持未勾选，74 条依赖边有效，每项均有依赖、产物、验证和追溯。
- 当日 Clarifications 共 6 条；本轮新增 2 条 auto-adopted default，未超过每轮 5 条及当日 10 条上限。
- 独立 evaluator 的精确 design.md SHA-256 与最终设计文件一致；没有在 PASS 后静默修改已评审设计。
- 三份规格均保留 TBD-PROD-01，开发与生产门禁未混淆。

另完成一次现有 SQLAlchemy 环境的静态 dialect 编译探针，确认 MySQL 类型选择；该探针未连接数据库。未运行应用、MySQL/MinIO 业务集成或生产迁移。本轮完成的是规格澄清和独立设计评审，全部实现任务仍未开始。

## SSD 停止点

STATUS: PHASE_READY
ROUTE: spec
PHASE: execution_ready
AUTONOMY: auto-spec
ARTIFACT: docs/specs/file-assets-minio/
NORTH_STAR_CONTEXT: unavailable；适用根 AGENTS.md 与当前规格
NEXT_SKILL: executing-task docs/specs/file-assets-minio/
NEXT_ACTION: 获得实施指令后从任务 1 开始执行
EVIDENCE_BOUNDARY: 只读 clarify 与独立设计 PASS、结构和追溯检查已完成；规格、运行状态及任务勾选不能证明实现或生产完成
PENDING_REVIEW: CL-01 提交后取消不撤销；CL-02 仅写入前 401 单次刷新重发，未知结果不自动重发
BLOCK_REASON: none；生产发行版 TBD-PROD-01 仅阻塞后续生产阶段


## 附件类型与回收复查修订

### 授权与范围

用户明确要求：“先把附件类型和回收复查策略这两处完善到 spec，继续用 ssd auto，该 clarify 的 clarify，修完再让 subagent 复审，生产 MinIO 发行版继续待定。”本轮仍为 auto-spec，只写当前规格和 SSD 记录，不实施、不部署、不启动容器。开始时工作区已有 455 项改动/未跟踪条目，已保存目标文档临时副本，不覆盖其他工作。

- [x] 读取根 AGENTS、三份规格与当前代码，记录本轮修订与旧评审失效范围。
- [x] 只读 clarify 扫描，主代理逐项采纳 CL-03/CL-04，更新 requirements 并逐次校验。
- [x] 同步 design 与 tasks；76/76 AC 双向追溯、19 项未勾选任务、74 条依赖、8 条澄清的初检通过。
- [x] 当前版本独立 evaluator 复审与必要修复：首轮 1 项 P2，修订后第 2 次 PASS。
- [x] 最终校验、摘要对齐与 execution_ready 状态同步。

### 本轮 clarify 证据

CLARIFY_SCAN_MODE: read-only-subagent
TARGET_REQUIREMENTS: docs/specs/file-assets-minio/requirements.md
SUBAGENT: /root/asset_revision_clarify
REQUESTED_MODEL: inherit-parent（用户要求）
REQUESTED_REASONING: inherit-parent（用户要求）
ACTUAL_MODEL: unavailable
ACTUAL_REASONING: unavailable
LIMITATIONS: 未核实生产消费者、真实 Office 样本或存储行为；静态源码和官方资料是规格依据，不是实现验收。

| 编号 | 子代理分类 | 主代理采纳与理由 | 写回 |
| --- | --- | --- | --- |
| CL-03 | user-decision-required | 保留已有八类附件能力及 CSV/图片，字段显式选子集；Office 有界结构/宏检测，拒绝不可验证与宏内容；缺失/通用 MIME 允许经内容判定；仅下载，不宣称杀毒。组件与四套生成器证据明确，但不据此推断生产使用。 | R3、R9、Clarifications；下游同步解析、组件/生成器、迁移与验证任务 |
| CL-04 | user-decision-required | 墓碑保留与主动复查分离，可靠写入终态之后最终删除并确认不存在才关闭；未知项有预算退避追踪。SDK 最后一次成功不能掩盖先前未知重试，因此采用单 PUT 许可与禁自动重试。 | 领域约定、R10、R14、R15、Clarifications；下游同步证据字段、恢复算法、预算/监控与任务 |

两项按 SSD auto 采纳，均注明 source: auto-adopted default 并列入 pending-review，不伪装为用户逐条回答。逐次写回验证 AC ID 不变、澄清不重复、已解决行为进入正文；本轮新增 R3.AC6、R10.AC6/7、R14.AC5，原 72 个 ID 全部保留。

STATUS: CLARIFICATION_COMPLETE
TARGET_REQUIREMENTS_PATH: docs/specs/file-assets-minio/requirements.md
MODIFIED_FILES: docs/specs/file-assets-minio/requirements.md
QUESTIONS: ASKED=0, ANSWERED=2
SESSION: ACCEPTED_BEFORE=6, ACCEPTED_TOTAL=8
DECISION_POSTURE: best-current；现有组件能力是消费者盘点信号，不为未知部署增加兼容旁路
DECISION_EVIDENCE: FileUpload/index.vue:81–84、四套 Vue 模板；旧设计永久逐日 HEAD；OWASP/S3/Boto3 官方边界
SECTIONS_TOUCHED: 来源证据、领域约定、R3、R9、R10、R14、R15、Clarifications
OUTSTANDING_HIGH_IMPACT_AMBIGUITY: none（主代理完成写回后的判断）
NEXT_ACTION: resume writing-specs downstream update
BLOCK_REASON: none
UNBLOCK_ACTION: none

| Category | Status | Evidence/Decision | Next Handling |
| --- | --- | --- | --- |
| 核心业务目标 | Clear | 统一资产与长期维护 | 保持 |
| 范围与非目标 | Clear after writeback | CL-03 明确类型能力，不加预览/杀毒平台 | 设计复审 |
| 角色与权限 | Clear | 既有上传/读取/运维分工 | 保持 |
| 完整性与一致性 | Clear after writeback | Office 基线及复查关闭条件写入正文 | 独立复审 |
| 可测试性 | Clear after writeback | 新增格式样本、关闭与预算验收 | 任务追溯 |
| 边界与失败 | Clear after writeback | 宏/加密/损坏、未知写入及迟到重开 | 故障矩阵 |
| 非功能约束 | Clear after writeback | 解析和复查均有预算 | 实施验证 |
| 数据与领域假设 | Clear after writeback | DELETED 与关闭分离、全部写入终态 | 独立复审 |
| 外部依赖 | Clear within scope | 实例需兼容验证；生产发行版待定 | 保留 TBD-PROD-01 |
| 兼容与迁移 | Clear after writeback | 现有能力保留，新限制下存量异常阻断切换 | 实施时重新盘点 |
| 术语与待定项 | Clear after writeback | 墓碑/主动复查定义明确 | 保持 |

### 定向代码与官方资料核对

- 仓库：FileUpload 默认 doc/docx/xls/xlsx/ppt/pptx/txt/pdf；四套模板未覆盖类型参数；config/env.py:445 的全局后缀表更宽，不据此直接开放全部持久附件类型。当前已有 python-docx/docxtpl 不能覆盖 Excel/PPT 容器校验。
- [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)、[zipfile](https://docs.python.org/3.11/library/zipfile.html)、[defusedxml](https://pypi.org/project/defusedxml/)、[olefile](https://olefile.readthedocs.io/en/latest/Howto.html)：业务白名单、类型辅助信号、受限容器/XML 解析。
- [oletools 源码](https://raw.githubusercontent.com/decalage2/oletools/master/oletools/olevba.py)：XLM 通用分析可能进入模拟分支，设计明确禁用该分支，仅结构检测；旧 wiki 的 PPT 限制不能替代锁定版本样本验证。
- [Boto3](https://docs.aws.amazon.com/boto3/latest/guide/retries.html)、[S3 一致性](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#ConsistencyModel)：单次尝试的配置语义及终态后确认边界；仍需所选实例实际兼容验收。

### 本轮独立 evaluator

已委派 /root/asset_revision_evaluator，只读核验 requirements/design/tasks；旧版 PASS 不作为本轮通过依据。最终结论及精确摘要待下文写入。


首轮结论：FAIL，1 项 P2，76/76 AC 文本覆盖、8 条澄清一致，但单 PUT 的 SDK 保证不充分。审查摘要：requirements=108839ad6c1fda2eb2fd0c3734468920853cd12f4684d0a3efc906eb12a9f8e5；design=8d1d9964177bb49420272aceba02c2c5a8a1879c4aec90dd0d70c92ceb0a9975；tasks=c090840372d4d58785c127e248534f171d0ffa02d56000e6e7f90cae18ee3263。

- 反例：S3RegionRedirectorv2 可通过 needs-retry.s3 独立请求重发，total_max_attempts=1 不能单独证明物理单 PUT。
- 修复：明确固定注册 before-send.s3.PutObject 守卫、SDK 线程内按调用隔离计数、第二次发送前拒绝、finally 清理；触发后 UNKNOWN，不写 ACK/READY 或猜成 NO_WRITE。补充 301/307/AuthorizationHeaderMalformed、5xx、超时、并发和异常清理的 HTTP 计数验收。
- 同时明确既有幂等约束：DELETE handler 在 I/O 后结果回写也重查关闭与代次，不能被迟到同代事件重置复查。
- 未修改 requirements 或新增产品默认值；修复在 design/tasks 内收敛，已请求同一独立 evaluator 第 2 次复审。主代理未把自身修订宣称为 PASS。
- 主代理另执行相对链接、围栏、空白与旧 AC ID 保留校验。因目标规格当前为未跟踪文件，使用临时基线与 git diff --no-index --check 检查实际变更，不依赖对未跟踪文件无效的普通 git diff。


第 2 次独立复审结论：**PASS，OPEN_FINDINGS: none**。首轮 P2 已关闭；同时确认迟到同代删除结果不会重开已关闭复查。76/76 AC 均有设计覆盖和任务追溯，8 条澄清一致，19 项任务全部未勾选、74 条依赖边无循环；生产 TBD 与任务 18/19 门禁保持。评审者未运行 Office 样本、SDK HTTP 探针、应用、MySQL 或 S3 测试。

| 文件 | 最终被独立评审的 SHA-256 |
| --- | --- |
| requirements.md | 108839ad6c1fda2eb2fd0c3734468920853cd12f4684d0a3efc906eb12a9f8e5 |
| design.md | 6c5df382f776180ef61fd2cf766abe7c6cb866f0d8d9acc22f304d6088bfa463 |
| tasks.md | f9f5cb2b1b0c6b90cd8ca5b99eaec1fd668c15c20ec7637fdb520b0a16551909 |

本版 AC 覆盖计数：R1 4/4、R2 5/5、R3 6/6、R4 5/5、R5 5/5、R6 4/4、R7 5/5、R8 5/5、R9 4/4、R10 7/7、R11 4/4、R12 5/5、R13 5/5、R14 5/5、R15 4/4、R16 3/3。关键设计定位：附件类型与受限校验、写入终态证据、正常关闭与迟到重开、异常退避/预算与运维、测试策略。最终独立修复定位：design.md:353、361、470 和 tasks.md:40。

### 本轮最终验证

- Python 结构/追溯命令最终退出码 0：16 项需求、76 个唯一 AC，全部任务覆盖且无未知引用；原 72 个 AC ID 全部保留。
- 19 项实现任务未勾选；74 条依赖指向先行任务；新增场景已进入任务 3/5/8/12/14/15/17。
- 当日澄清总数 8，本轮写回 2，符合每轮 5/当日 10 上限。
- 三份标题、设计必需章节、Markdown 围栏、相对链接与空白校验通过；git diff --no-index --check 对本轮临时基线无空白诊断（有内容差异的退出码 1 不作为错误）。
- 主代理本地核验摘要与第 2 次独立评审逐一一致。PASS 后仅更新本记录与 .ssd-run.json，未再改三份被评审规格。
- 校验辅助脚本曾因 no-index 差异退出码和不必要的精确字段文本匹配报错，已修正校验方式后完整重跑通过；未通过改动已评审文档来迁就脚本。
- 未实施应用代码、数据库迁移、Office 解析、SDK 发送探针、MinIO 集成或生产操作；全部属于后续实现验收，不将本次静态检查称作真实业务通过。

### 当前 SSD 停止点

STATUS: PHASE_READY
ROUTE: spec
PHASE: execution_ready
AUTONOMY: auto-spec
ARTIFACT: docs/specs/file-assets-minio/
NORTH_STAR_CONTEXT: unavailable；根 AGENTS.md 与已绑定规格约束本轮范围
NEXT_SKILL: executing-task docs/specs/file-assets-minio/
NEXT_ACTION: 收到实施指令后执行任务 1 的真实消费者与数据盘点
EVIDENCE_BOUNDARY: 当前摘要版本独立规格评审 PASS 与结构/追溯检查通过；规格、SSD 状态、任务勾选不能证明实现或生产完成
PENDING_REVIEW: CL-01 提交后取消不撤销；CL-02 仅写入前明确 401 刷新重发一次、未知结果不重发；CL-03 保留 Office 等类型并受限检测/仅下载、历史异常阻断切换；CL-04 可靠终态后删除确认才关闭复查，未知项有预算持续追踪并支持证据核对
BLOCK_REASON: none；TBD-PROD-01 继续仅阻塞生产部署及生产验收

## 用户集中复核（2026-10-24）

用户原话：“我认为可以澄清按照你推荐来”。据此将 CL-01～CL-04 四项 auto-adopted default 全部确认为用户决策，采用内容与上文记录一致，未改任何默认值。

| 编号 | 确认内容 | 状态 |
| --- | --- | --- |
| CL-01 | 以服务端持久化提交点为准；提交后取消不撤销，结果不明先核对，未绑定项按草稿回收 | user-confirmed |
| CL-02 | 仅写入前明确 401、同主体且未取消时刷新重发一次；未知结果不自动重发 | user-confirmed |
| CL-03 | 保留 doc/docx/xls/xlsx/ppt/pptx/txt/pdf 及 UTF-8 CSV、JPEG/PNG/WebP，字段显式选子集；Office 有界结构与宏检测，仅下载交付，历史异常报告后处理 | user-confirmed |
| CL-04 | 可靠写入终态之后删除并确认不存在才关闭主动复查；未知项持久化退避、有界预算追踪与告警，不靠超时、固定期限或多次 404 关闭 | user-confirmed |

- 写回范围：仅 requirements.md Clarifications 中四条的 source 标注追加 `user-confirmed 2026-10-24`；`diff` 确认共 4 行变化且全部为该标注，需求正文、AC、design.md、tasks.md 均未修改。
- requirements.md 摘要因标注变化由 108839ad… 变为新值（见 `.ssd-run.json` 的 `final_spec_sha256`）；design.md、tasks.md 摘要与第 2 次独立评审一致。标注变更不涉及行为或追溯，不重新发起 evaluator。
- 本次确认不包含实施授权：`execution_authorized` 仍为 false，任务 1–19 均未开始。

### 当前 SSD 停止点（复核后）

STATUS: PHASE_READY
ROUTE: spec
PHASE: execution_ready
AUTONOMY: auto-spec
ARTIFACT: docs/specs/file-assets-minio/
NEXT_SKILL: executing-task docs/specs/file-assets-minio/
NEXT_ACTION: 收到实施指令后执行任务 1 的真实消费者与数据盘点
EVIDENCE_BOUNDARY: 澄清已获用户确认；规格、SSD 状态、任务勾选不能证明实现或生产完成
PENDING_REVIEW: none
BLOCK_REASON: none；TBD-PROD-01 继续仅阻塞生产部署及生产验收

## 长期方案定向修订（2026-10-24）

### 授权与范围

用户先确认 CL-01～CL-04，随后要求复查规格并参考 Plane 与 OpenCloud；在助手给出长期收益最大的方案后回复“我认可”，认可内容包括重开 CL-04、头像登录可读，以及“按 SSD 流程修订三份文档并重新独立评审”。本轮仍为 auto-spec，只改本规格及 SSD 记录，不实施、不部署、不启动容器。开始时工作区有 231 项改动/未跟踪条目，目标文档已备份到会话临时目录，未覆盖其他工作。

- [x] 只读核对 Plane（本机 steamer-plane foundation 分支源码）与 OpenCloud（reva @7c65339、opencloud @ef9c6e7 源码，子代理只读检索），以及 Mastodon / GitLab 的孤儿清理文档。
- [x] 按用户决策写回 requirements（Session 2026-10-24，7 条用户决策），原 CL-04 标注为已取代；同步 design 与 tasks。
- [x] 独立 evaluator 三轮：第 1、2 轮 FAIL，按发现修订；第 3 轮 PASS。
- [x] 最终结构、追溯与摘要核对。

### 澄清证据

CLARIFY_SCAN_MODE: accepted-prior-answer
TARGET_REQUIREMENTS: docs/specs/file-assets-minio/requirements.md
说明：本轮澄清由用户在对话中直接决策，未另行运行 clarify 子代理；独立 evaluator 每轮同时检查需求是否仍有高影响歧义，第 3 轮结论为无阻塞歧义。
OUTSTANDING_HIGH_IMPACT_AMBIGUITY: none

| 编号 | 内容 | 来源 / 状态 |
| --- | --- | --- |
| CL-05 | 取消逐次写入终态证据与复查预算；上传中门禁 + 后台删除 + 墓碑 30 天 + 每日孤儿清扫 + 只报告的全桶核对（取代 CL-04） | 用户决策 |
| CL-06 | 内容读取改为后端同源流式，ETag=SHA-256，private, no-cache，304 不访问存储；不签发预签名 | 用户决策 |
| CL-07 | 已绑定头像任何已登录用户可读 | 用户决策 |
| CL-08 | 上传限流档 + 每用户未绑定草稿 50 个 / 200 MiB，超限 429 | 用户决策 |
| CL-09 | 软删除视同删除并释放绑定 | 用户决策 |
| CL-10 | 图片统一转正重编码去元数据，头像 512 像素 PNG | 用户决策 |
| CL-11 | Office 有界线程内进程内解析，不建子进程 | 用户决策 |
| CL-12 | 无主对象不自动删除；桶归属安装标识，不一致则文件能力不可用并拒绝删除 | 评审后自动采纳，待用户确认 |
| CL-13 | 生成器字段容量不得超过草稿配额；迁移资产用不可登录的迁移主体，不计配额 | 评审后自动采纳，待用户确认 |
| CL-14 | 删除不经 Outbox，由调度器按资产行状态执行，持久化退避、无终止状态 | 评审后自动采纳，待用户确认 |
| CL-15 | 图片规范化超限降级：JPEG/WebP 质量 80、PNG 最高压缩，再缩至 4096 像素，仍超限 422 | 评审第 3 轮指出未登记为澄清；已写入 R3.AC2 与设计，仅在本记录与运行状态中登记，待用户确认 |

CL-12 与 CL-14 修改了用户 CL-05 原文中“无记录对象自动删除”和“经 Outbox 删除”两处；requirements.md 中用户原文保持不变，并已标注两处由后续自动采纳项修改、待用户确认。

### 独立 evaluator

同一只读子代理三轮评审，模型与推理沿用既有用户指令继承主代理，具体值运行时不可核验。

| 轮次 | 结论 | 要点 |
| --- | --- | --- |
| 1 | FAIL | P2：删除入队依赖 Outbox 唯一键，现有 add_events 遇重复回滚整批，删除可全局停滞；P2：清扫删除无记录对象缺少桶归属不变量，误配置环境可永久删除共享桶对象；另 7 项 P3 |
| 2 | FAIL | 第 1 轮 P2 已关闭；新 P2：Outbox 进入 manual_intervention 后没有重新入队入口（replay 只读 event_history），删除可永久停在 DELETING；另 5 项 P3 |
| 3 | PASS | 无 P0/P1/P2；79/79 AC 覆盖；无澄清冲突；结构通过；5 项 P3 见下 |

主代理核实了评审引用的代码事实：`events/repositories.py` 的 add_events 只做 add + flush；`events/runtime.py` 的 replay 只读 event_history；`server.py:226` 的 max_retry_count=6；`module_generator/` 中没有 del_flag 或软删除路径。

| 文件 | 第 3 轮被独立评审的 SHA-256 |
| --- | --- |
| requirements.md | ef895e33d72db7aab4af097d46b0c0ea8494e986ba8d967d246af4d7dc87fce5 |
| design.md | 2b84406e11a77c71336efe9a1e7d991c49a935cee575f6999b099167e2fd60c6 |
| tasks.md | b315432f（完整值见 `.ssd-run.json`） |

### 第 3 轮遗留 P3（PASS 后未改动被评审文档）

为保持评审摘要一致，PASS 后未再修改三份规格。以下 P3 在实施对应任务前先收敛，或经用户同意后另起一轮修订与复审：

1. R10.AC4 写“存储不可用期间不消耗尝试次数”，但设计中只有归属状态会暂停删除，存储故障时每轮仍最多计入 3 次失败。实施任务 8 前二选一：被“连续 3 次错误”提前结束的那一轮不计次数，或把 R10.AC4 改写为“每轮最多计 3 次”。
2. 删除轮次时长未与 5 分钟租约绑定：轮次执行上限应低于租约（约 4 分钟），调度任务登记为非并发，失败回写也以 `state=DELETING` 为条件；仍有绑定的 DELETING 行应加租约并告警（任务 8）。
3. 归属三态的细节：“无效”后是否继续复核、`--take-over` 是否无需重启即生效、403 AccessDenied 的归类、首次核对是否在开始服务前完成（避免工作进程重启时短暂 503）（任务 3）。
4. 文字残留：design.md 中“对象由删除事件或孤儿清扫回收”两处应改为“删除任务”；tasks.md 任务 15 的“事件丢失”；requirements.md 现状表仍把 Outbox 列为优先复用的基础设施（随下一次修订一并清理）。
5. 图片降级规则未登记为澄清：已在上表登记为 CL-15，待用户确认后写入 requirements.md 的 Clarifications。

### 最终验证

- Python 结构/追溯：16 项需求、79 个唯一 AC（原 76 个 ID 全部保留，新增 R5.AC6、R12.AC6、R15.AC5），全部有任务追溯，无未知引用；19 项任务全部未勾选，依赖只指向先行任务；Session 2026-10-24 共 10 条澄清，未超过当日 10 条上限。
- 三份文档代码围栏成对、相对链接有效；`git diff --no-index --check` 对本轮基线无空白诊断。
- 当前三份文件摘要与第 3 轮被评审的版本一致。
- 未实施应用代码、数据库迁移、解析器样本、MinIO 集成或生产操作；全部属于后续实现验收。

### 当前 SSD 停止点

STATUS: PHASE_READY
ROUTE: spec
PHASE: execution_ready
AUTONOMY: auto-spec
ARTIFACT: docs/specs/file-assets-minio/
NORTH_STAR_CONTEXT: unavailable；根 AGENTS.md 与本规格约束范围
NEXT_SKILL: executing-task docs/specs/file-assets-minio/
NEXT_ACTION: 用户确认 CL-12～CL-15 后，收到实施指令即从任务 1 的真实消费者与数据盘点开始
EVIDENCE_BOUNDARY: 第 3 轮独立规格评审 PASS 与结构/追溯检查通过；规格、SSD 状态、任务勾选不能证明实现或生产完成
PENDING_REVIEW: CL-12 无主对象不自动删除 + 桶归属标识；CL-13 生成字段容量与迁移主体；CL-14 删除不经 Outbox；CL-15 图片规范化降级规则；另有 5 项 P3 待实施前收敛
BLOCK_REASON: none；TBD-PROD-01 继续仅阻塞生产部署及生产验收

## 用户确认与 P3 收敛（2026-10-24）

用户回复“关于1. 按照你的推荐来 完成后告诉我”：确认 CL-12～CL-15，并要求修复第 3 轮遗留 P3 后复审。本轮只改规格与 SSD 记录。

- CL-12、CL-13、CL-14 在 requirements.md 中标注 user-confirmed；CL-15（图片超限降级）并入 Session 2026-10-24 的图片规范化条目，条目数保持 10，未超过当日上限。
- 修复第 3 轮 5 项 P3：删除任务存储故障计数与 R10.AC4 一致、轮次时长与租约、禁止并发登记、条件回写、仍有绑定的 DELETING 行、归属三态细节、文字残留。

| 轮次 | 结论 | 要点 |
| --- | --- | --- |
| 1 | FAIL | P2：用户确认的 CL-14（存储或归属不可用不计次数）与 R10.AC4、设计步骤 4（存储故障每轮最多计 3 次）矛盾；另 3 项 P3 |
| 2 | PASS | 按 CL-14 原文收敛：存储不可用类失败（连接、超时、5xx）不计次数、1 分钟后重试，只有对象级失败计数；新增 delete_failing_since 与“持续失败超过 1 小时”告警；认领 3 分钟后不再发起 DELETE，维护 client 单次约 30 秒；R12.AC6 补 403；三套 client。无 P0/P1/P2，79/79 AC，无澄清冲突 |

| 文件 | 第 2 轮被独立评审的 SHA-256 |
| --- | --- |
| requirements.md | 62df6b103780bb2045be4b303d12b67a7b49cde11791d0b4214b0ac6f4b63795 5c2d18d9863f666e218b590bb6f6d998ffd25dc09caba0eab1269ccfb34672e9 f54c9afad2c8e249a368e564d96ce5897b356d323ec457cdd913aad87882a379 |
| design.md |  |
| tasks.md |  |

### 遗留 P3（PASS 后未改动被评审文档，实施对应任务时收敛）

1. 存储不可用类失败固定 1 分钟重试、无退避：若部分磁盘离线导致数十个 key 持续 5xx，相邻的 3 个即可提前结束本轮，健康行只能等租约，与 R10.AC3“任一资产的失败不阻塞其他到期资产”有张力。任务 8 实施时按 delete_failing_since 做不计次数的封顶退避（例如 1 分钟起翻倍到 15 分钟），或仅在连接级错误时提前结束本轮。
2. 租约覆盖 delete_after，会掩盖积压时长：反复被认领却未执行的行既不算“到期未认领”，也没有 delete_failing_since。任务 8 实施时把租约放到独立列（例如 delete_lease_until），delete_after 保持到期时间，供积压告警与 oldest_delete_due_age 使用。
3. 任务 15 的告警核验清单需补“持续失败超过 1 小时”与 binding_invariant_violation。
4. 设计步骤 2 仍写“多实例不会重复执行同一行”，与步骤 5“偶发重叠无害”的措辞不一致，实施时以步骤 5 为准。

### 当前 SSD 停止点

STATUS: PHASE_READY
ROUTE: spec
PHASE: execution_ready
AUTONOMY: auto-spec
ARTIFACT: docs/specs/file-assets-minio/
NORTH_STAR_CONTEXT: unavailable；根 AGENTS.md 与本规格约束范围
NEXT_SKILL: executing-task docs/specs/file-assets-minio/
NEXT_ACTION: 收到实施指令后从任务 1 的真实消费者与数据盘点开始
EVIDENCE_BOUNDARY: 本轮第 2 次独立规格评审 PASS 与结构/追溯检查通过；规格、SSD 状态、任务勾选不能证明实现或生产完成
PENDING_REVIEW: none（CL-01～CL-15 均已由用户确认）；4 项 P3 在任务 8、15 实施时收敛
BLOCK_REASON: none；TBD-PROD-01 继续仅阻塞生产部署及生产验收

## PASS 后按用户指示收敛遗留 P3（2026-10-24）

用户原话：“4个小问题就按照长久受益最大的方案就行, 不用在review了”。据此直接修改 design.md 与 tasks.md，未再发起独立评审；requirements.md 未改动。以下修改不在任何一次独立评审的覆盖范围内，这一点由用户明确豁免。

1. 存储不可用类删除失败改为不计次数的封顶退避：下次时刻 = now + min(max(1 分钟, now − delete_failing_since), 15 分钟)；只有连续 3 次连接级错误才结束本轮，单个对象 5xx 或读超时只退避该行。部分磁盘离线时健康对象的删除不受影响，符合 R10.AC3。
2. 新增 delete_next_attempt_at 承载租约与退避，delete_after 只表示到期时间、释放后不再改动；删除积压告警只统计未处于失败重试的到期行；retry-deletes 只改 delete_next_attempt_at，不缩短宽限期。
3. 任务 15 的告警核验补齐“持续失败超过 1 小时”“仍有绑定的 DELETING 行”及清扫相关告警。
4. 设计第 2 步措辞与第 5 步对齐：正常情况下不并发执行，偶发重叠无害。

结构与追溯复核：79/79 AC 追溯、19 项任务未勾选、代码围栏与相对链接有效、`git diff --no-index --check` 无空白诊断。

STATUS: PHASE_READY
PHASE: execution_ready
EVIDENCE_BOUNDARY: 最近一次独立评审 PASS 覆盖到 requirements 62df6b10 / design 5c2d18d9 / tasks f54c9afa；其后对 design 与 tasks 的 P3 收敛经用户豁免未复审
PENDING_REVIEW: none
NEXT_ACTION: 收到实施指令后从任务 1 开始

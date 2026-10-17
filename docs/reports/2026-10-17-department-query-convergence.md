# 部门管理与用户部门选择闭环

当前状态：实现检查与两轮独立审查已通过，保留首次真实接口刷新超时这一未定诊断。实现位于项目本地工作树 `codex/department-query-convergence`，基线 `94528292c3483af52cdfeab6a95cb0d76d87bbb9`；本阶段没有合入源分支或发布，工作树保留供用户验收。

## 范围与方案依据

先读取真实部门 API、用户树消费者、已有 user/menu 查询模式、原生控件实现和后端权限，再收敛调用。复用已有单一 QueryClient、会话 scope、TanStack Query 原生 options、ZXUI 查询失效工具、受控 GridList 和 FormDialog，不增加资源缓存或 CRUD 框架。

- 管理列表、详情、排除自身及后代的上级选项，以及用户可选部门树，分别使用部门资源下的原生查询键。管理列表/排除接口要求 `system:dept:list`；用户树要求 `system:user:list`，正常部门筛选仍由后端负责。
- 新增、修改、删除在确认前捕获会话和 DTO，写入前校验会话；成功后异步失效部门资源与嵌入部门名称的用户列表。刷新失败不把已成功写入改报为失败。
- 列表区分首次加载、后台刷新、失败与等待联网；编辑器每次打开只读取一次快照，后续选项刷新不覆盖未保存字段。关闭只结束当前打开的等待，不取消其他订阅者共享的读取。
- 页面侧栏和用户编辑器共用用户部门树。树投影复制节点，避免 `handleTree` 或控件元数据污染共享数据；当前停用部门缺席于正常选项时，保留原值和详情提供的名称。
- 本轮发现的问题属于 RuoYi 资源与消费者接入，没有证明需要修改 ZXUI 通用机制。部门领域规则保留在 RuoYi，未修改 steamer-front、仿真模块、角色数据范围树、后端契约或生成器。

代价是维护明确的部门写入依赖和各权限端点的查询键；收益是共享读取、统一失效和编辑草稿保护可以被真实调用验证，而不用给通用组件加入业务知识。

## 真实发现与验证边界

1. 实际原生控件回归发现两处问题：初始空选择会生成 `[null]` 缓存节点并在读取 `id` 时异常；`CacheOptions` 只插入尚不存在的项，异步详情选中折叠后代后，即使 `data/cacheData` 更新，已选可见标签仍可能旧值。已先观察 RED，再加非空守卫并使用公开 `label` 插槽消费当前编辑器标签元数据；保留 `cacheData` 的停用部门回退职责，不操作私有缓存、不重挂控件。实际 UserFormDialog 与真实 ElTreeSelect/ElSelect/ElOption 的 3 条回归通过，覆盖初始空值、可见名称刷新、失败保留、停用值新详情回退、控件身份、选中标记及键盘选择；整份用户表单回归 22 条通过。契约依据：[Select slots](https://element-plus.org/en-US/component/select.html#select-slots)、[TreeSelect API](https://element-plus.org/en-US/component/tree-select.html#api)。
2. 本地 Redis 容器与 Colima 虚机内正常，但宿主 6379 不可达。Lima 日志记录原有 SSH master 创建该转发失败；在同一 master 上重试相同 `-O forward` 后宿主 `PING` 返回 `PONG`。没有重启共享虚机、修改配置或引入额外代理。Lima 明确将 SSH 列为原生端口转发器：[Port Forwarding](https://lima-vm.io/docs/config/port/)。恢复详情见 `evidence/2026-10-17-department-query-convergence/runtime-recovery.json`。
3. 首次本地产物真实探针在连续创建父子部门后等待刷新超时；实际管理列表和用户树刷新请求均已发生，2 条临时记录已清理。失败当时未采集足够的列表/树缓存内容，无法确定根因。保留 `installed-initial-failure.json`；没有根据未证实的后端缓存竞争推断修改生产代码。随后相同时序的源码模式 3 轮、本地产物模式 4 轮全部通过，无额外等待或手动失效，每轮 2 条临时记录均删除并核对不存在。该初次超时仍作为未定诊断保留，不宣称已消除所有竞争边界。

真实探针调用本轮业务 commands、query factories、原生 `useQuery` 订阅和 HTTP 适配，连接现有本地 FastAPI；没有 MSW 或 HTTP mock。它验证双订阅共享一次读取、创建/改名自动更新、用户列表重读、停用/启用筛选、后代排除、详情快照、真实 HTTP 422 与清理。不修改已有用户或权限，不能证明既有用户行的视觉标签或浏览器交互。

本轮没有 computer use。组件/原生控件内存测试、真实 HTTP 探针与浏览器视觉验收分开记录；浏览器人工交互未验证。

## 验证记录

原生标签修复后，所有已声明的最终检查通过：

| 检查 | 结果 |
| --- | --- |
| 全量前端测试 | 133 文件 / 1252 tests |
| lint / type-check | exit 0 |
| UI 规范 | 严格规则检查与 23 tests 通过 |
| 源码直连 / 本地产物生产构建 | r2 均 exit 0 |
| 独立复审轻量复验 | 4 文件 / 53 tests、type-check、diff-check 均通过 |
| 真实 HTTP | 后续源码 3 轮、本地产物 4 轮通过；初次超时保留，不重复计算副本 |
| 清理 | 8 轮 16 条自建部门均经现有 API 软删除并核对列表不存在；自建会话退出，任务后端进程停止 |

命令、环境变量、退出码与原日志 hash 见 [验证摘要](/Users/hqz/dev/RuoYi-Vue3-FastAPI/.worktrees/department-query-convergence/docs/reports/evidence/2026-10-17-department-query-convergence/verification-summary.json)。原始日志持久化于 Git metadata，仓库只保存有限摘要和有意义的 RED/GREEN 记录。新工作树未包含忽略的 UI fixture，验证时复用了同一已验收 compiler/vendor 输入生成的源目录 fixture；其 SHA 与原因在 metadata 的 `fixture-input.json`，没有将生成 JSON 纳入产品修改。实际生产构建仍执行其正常资产生成。

源码构建使用 `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus`，本地产物构建使用 `VITE_ZXUI_LOCAL=false`，复用 THEME 已验收的本地 vendor 包，其 SHA 见证据 `consumption-inputs.json`。最终构建输出分别为 `/tmp/department-query-source-20261017-r2`、`/tmp/department-query-packed-20261017-r2`。两种构建仍报告既有大 chunk 与 Browserslist 数据陈旧诊断；本轮没有调整阈值隐藏诊断，也没有扩展到仿真/编辑器的拆包工作。

独立审查第 1 轮发现 P1 空缓存节点异常与 P2 异步已选标签旧值，已通过实际组件 RED/GREEN 修复。第 2 轮 `RESULT: PASS`、`RERUN_REQUIRED: no`，无剩余 P0/P1/P2。详见 [最终独立审查](/Users/hqz/dev/RuoYi-Vue3-FastAPI/.git/worktrees/department-query-convergence/department-final-review-round2.md)。该批准只证明本轮实现及列明验证，不扩大到浏览器验收、受限账号端到端验证、源分支交付或发布。

完成证明已从持久化上下文实际执行：`review mode: independent-subagent`，`review rounds: 2`，`subagentAttempt.tool/status: collaboration.spawn_agent/succeeded`，`final-review-proof: pass`，`claim-proof --claim implementation-complete: pass`。执行上下文为 [codex-execution-context.json](/Users/hqz/dev/RuoYi-Vue3-FastAPI/.git/worktrees/department-query-convergence/codex-execution-context.json)；对应原始 proof JSON 在同目录。首次 proof 因审查报告 V1 行的机器格式不匹配而拦下，独立审查者只修正格式后重新执行通过；未修改 guard 或证据结论。

范围核对见 `scope-audit.json`：18 个前端实现/测试文件均在计划范围内，原源目录中相应路径与部门阶段起点字节一致；没有把源目录其他未提交工作引入任务工作树。计划阶段证据为 READ（真实 API/消费者、原生库实现、已有查询契约），SEARCH（真实调用与旧工厂/查询键残留），COMMAND（RED/GREEN、最终质量检查和两种构建）；任务与约束见 [执行计划](/Users/hqz/dev/RuoYi-Vue3-FastAPI/.worktrees/department-query-convergence/docs/plans/2026-10-17-department-query-convergence.md)。

完整执行与审查 metadata：`.git/worktrees/department-query-convergence/`。证据目录只收录脱敏、有限的检查摘要与日志，不收录令牌、请求头、完整用户响应、数据库转储或后端原始日志。

## THEME 前置交付事实

THEME 实现已快进合入记录的 ZXUI `codex/http-vue-query-phase-a` 与 RuoYi `std` 源分支，并通过源目录基线验证；两仓共 6 个工作树、4 个临时分支已清理。未发布或推送。详见 [THEME 源分支记录](/Users/hqz/Downloads/element-plus/docs/specs/THEME-runtime-payload/delivery.md)。

两仓 `delivery-proof` 通过，但 `delivery-status` 因源目录保留的无关未提交内容返回 `delivery_incomplete`、`finalClaimAllowed:false`。保留该原始工具状态，不将其改写成 `delivered_clean`，不把其他任务的工作纳入交付。本部门任务的工作树与该已清理的 THEME 任务独立。

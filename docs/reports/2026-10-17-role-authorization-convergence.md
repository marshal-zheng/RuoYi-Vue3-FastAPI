# 角色管理与双向用户授权闭环

候选实现与独立审查已完成；源分支交付及标准源基线验证由本文末尾与持久化交付账本记录。任务起点为 RuoYi `std@3e6936e1a839d21ebb17ac5eec36721772d8862f`，项目本地工作树为 `.worktrees/role-authorization-convergence`。ZXUI 源为 `codex/http-vue-query-phase-a@67e13c6cfa413d4c7a57bfa5d728dabc750d2972`。

## 根因与实现

- 旧授权页读取 GridList 的扁平 `page/size`，实际契约在 `pager` 中；用户角色页还同时从 GridList mounted 与页面 mounted 发起读取。角色列表将异常转换为成功空列表，筛选未重置页码，状态开关直接改写行。角色已分配用户、选择用户、用户角色及角色主列表现使用已有 controlled GridList，分页和提交条件由业务持有，原生 Query 负责参数身份、共享、取消与错误状态。
- selector 旧并发搜索仅检查 visible/scope，不能区分同次打开的不同搜索。现在请求 key 捕获角色、筛选和页码，选择集合独立于结果页，仅响应真实表格 select/select-all 意图；跨页与搜索保留选择，关闭重开清空，旧写完成不会关闭新打开弹框。
- 用户角色页从首次完整快照初始化全部已授权角色，分页及后台刷新不覆盖草稿，用户取消选择不会被旧 `flag` 再次勾回。保存继续采用完整替换及显式空数组；角色侧采用增量授权与单条/批量撤销。
- `role.ts` 提供角色列表/详情、菜单树、数据范围树及 scoped commands；不同权限端点保持各自身份。角色写入失效 roles 和 users，覆盖用户编辑器嵌入目录与双向授权；原有 userCommands 的 users 根失效覆盖新增授权读取。成功写入不等待刷新成功，后读失败以读取状态反馈。
- 两角色抽屉复用原 `useEditorRead`，加入共享读取、会话隔离、错误/暂停/重试；详情与树复制为本次打开的草稿，后续后台读不改用户输入。
- 用户/角色主列表在进入授权前，仅把已提交条件与分页存入 Pinia 返回状态，返回时消费并重建筛选显示。会话变化清空；未启用全局 KeepAlive，也不缓存编辑器、选择集或未提交筛选。
- 前端权限入口与真实源后端身份一致：角色定义的管理员操作受限；关联授权时管理员身份是捕获会话的用户 ID 1，角色名 `admin` 不代替此身份。独立审查首轮发现了两者混淆，已用三条 non-root + admin 角色的真实组件回归修复。

方案复用既有 QueryClient、`queryOptions`、`queryRequest`、分组失效与 controlled GridList，没有确认需要扩展 ZXUI 通用 API。本轮未修改 ZXUI 产品源码、steamer-front、仿真、THEME、岗位 CRUD。维护代价是明确的业务查询键和失效关系；它们由 RuoYi 管理，组件库不接收业务身份。依据：[TanStack query keys](https://tanstack.com/query/latest/docs/framework/vue/guides/query-keys)、[invalidation](https://tanstack.com/query/latest/docs/framework/vue/guides/query-invalidation)。

## 后端实际证据与范围

新增服务回归先观察 10 项失败，修复后通过。受控真实 HTTP/MySQL/Redis A/B 使用任务命名空间、仓库 SELECT 完成后的 barrier 和自有用户/部门/角色；没有增加产品 API，也没有修改现有账号权限或数据库配置。

| 检查 | 原实现 | 候选修复 |
| --- | --- | --- |
| role:list、role:detail、menu:role_tree 旧 SQL 读取在写入后返回，再发独立 GET | 独立 GET 命中旧值 | 旧在途 GET 可返回旧快照；后续 GET 读到当前值 |
| 两个自建部门范围的角色列表 | 绑定值不同，`str(data_scope_sql)` 同形，缓存 key 相同，第二范围得到第一范围结果 | 各范围分别执行真实查询，返回各自结果 |
| 具有接口权限但目标越数据范围的 authRole GET | HTTP 200 | HTTP 403 |
| 已关联停用角色 | 从可选目录和已关联标记中缺失 | 仍可见且 `flag=true` |

因此移除六类角色相关结果缓存：role list/select/detail、menu list/tree/role_tree；角色写端无用途失效同时移除，菜单 detail 缓存保留。三类 HTTP A/B 之外的 select、menu list/tree 有服务内存回归与消费者链验证，不宣称每一类都做了 HTTP barrier。权限 guard 每次请求的身份检查仍由原服务执行；前端入口缺陷不等于写越权成功。

authRole GET 在读取前检查目标用户数据范围，对不存在用户返回 404；目录取正常非管理员选项与所有已有有效角色关联的并集，flag 来自真实关联表。源现有 JSON DTO/UserRoleService 的完整替换/增量写规则保留。后端现有写规则允许保留已关联停用角色，本轮不改 source-only 的关联写服务，不声称新增了后端停用角色授予限制。

选型比较：仅修缓存键不能解决旧读回填及关联写后的菜单陈旧；仅把删除移到提交后也不能阻止更晚完成的旧读写回。直接移除这些小管理查询的重复状态，成本低于新增锁、分布式版本或通用失效框架。本机只读观测为 2 个有效角色、94 个菜单，正常角色选项查询约 1.407 ms；这是本机数据，不是部署容量承诺。Redis 官方说明 cache-aside 使用 TTL 约束陈旧窗口，[cache-aside 文档](https://redis.io/docs/latest/develop/use-cases/cache-aside/)与[一致性讨论](https://redis.io/blog/cache-consistency-strategies/)用于核对方案，并非本项目实际复现的替代证据。

## 验证及失败记录

| 检查 | 候选结果 |
| --- | --- |
| 最终全量前端 | 136 文件 / 1297 tests 通过 |
| lint / type-check | exit 0 |
| UI standards | 517 文件零违规，23 tests 通过 |
| 源码直连 / 本地 vendor 生产构建 | 均 exit 0 |
| 独立二轮复验 | 8 前端文件 / 105 tests；后端 19 tests；无剩余 P0/P1/P2 |
| 真实业务源码与本地产物探针 | 均通过，分页/双向写/清空/目录/停用关联/编辑快照/422；每轮自建 3 用户和 3 角色均清理 |
| 后端扩大候选回归 | 49 tests 通过；新增一致性/读取契约 10 tests 包含在相关验证中 |

[验证摘要](evidence/2026-10-17-role-authorization-convergence/verification-summary.json)记录命令、退出码和原日志 SHA；[消费输入](evidence/2026-10-17-role-authorization-convergence/consumption-inputs.json)记录源码及本地包。没有 npm 发布依赖，没有推送。构建保留既有大 chunk 和 Browserslist 数据陈旧诊断。测试工作树复用源 node_modules/venv；缺失的忽略生成 UI fixture 取自相同现有 compiler/vendor 输入，并记录 SHA，未提交生成 fixture。

原始失败全部保留：第一次前端真实探针误把用户创建响应当作顶层用户 ID，已改为独立唯一名称列表确认身份，该次 1 用户/1 角色清理成功。第二次证明停用关联读取缺失，但并行同账号登录替换了会话，finally 清理遇 401；随后串行新会话删除该 marker 的 3 用户/3 角色并确认列表为空，独立[恢复记录](evidence/2026-10-17-role-authorization-convergence/frontend-r2-cleanup-recovery.json)不覆盖原失败。之后实际探针串行登录。第一候选 installed 证据的 transport 文本误称 standard，实际为 candidate overlay；修正探针加入明确 runtime 字段后重跑的 source / installed-r2 才是准确标识，旧记录仍保留。

首轮完整 UI 规范检查发现 selector 在页面覆盖 staleTime；已把未授权列表新鲜度移到公共工厂，最后全套检查通过。独立首轮 FAIL、第二轮 PASS 报告持久化于 `.git/codex-delivery-preservation/role-authorization-convergence/`。第二轮机器格式补齐只改变报告格式，不增加审查轮或测试计数。

源当前存在未提交后端业务/测试，与工作树 HEAD 不相同。候选测试不能冒充源全库全绿：对源额外 126 项测试做 A/B，原版 2 failed / 124 passed，候选 6 failed / 120 passed。原两项为已交付部门缓存删除的旧断言；新增四项为 patch 已删除的角色缓存符号/要求缓存删除的实现耦合断言及旧授权目录 mock。源这些未跟踪测试完整保留，未整份纳入本轮提交，也未保留无用途缓存兼容符号来刷绿。详见 [源测试对照](evidence/2026-10-17-role-authorization-convergence/backend-source-tests-comparison.json)。

没有 computer use。真实 GridList/ElTable jsdom 回归、受控后端 A/B、正常前端真实 HTTP 业务探针与浏览器视觉验收明确区分；本轮未做浏览器视觉/人工交互验收。

## 源交付与保留

新的初始快照覆盖 RuoYi 756 个脏路径和 ZXUI 906 个脏路径的内容、权限、状态及 index。四个后端文件与源未提交工作重叠：user_controller、role_service、menu_service、user_service。候选只应用本轮增量，保留源 JSON 写、停用详情及 404 等规则；独立审查核对了 source-preserving.patch。

以实际四文件做隔离 Git 预演，目标 index entry 配合普通 fast-forward 能同时保留源业务修改、其他暂存内容及未跟踪内容，[保留预演](evidence/2026-10-17-role-authorization-convergence/dirty-fast-forward-preservation-proof.json)通过。实际源 HEAD gate、逐路径保留、源无 overlay 验证及工作树/分支清理由后续交付记录确认。

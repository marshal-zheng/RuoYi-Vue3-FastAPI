# 分页 COUNT 总数滞后修复

本轮已完成。后端移除透明的跨事务 COUNT 结果缓存，分页 `total` 和 `items` 使用同一 SQLAlchemy Session 查询数据库。没有改业务事务、其他缓存、前端或 ZXUI，没有新增依赖，也没有提交或发布。

## 根因：失效不等于提交，缓存不属于当前事务快照

参数链路为 controller → mediator/transaction behavior → ConfigService → ConfigRepository。`BaseRepository.add` 原来在 `flush/refresh` 后立即删除 COUNT 缓存，服务内事务可能只是保存点，最外层事务最终由 `get_db` 或实际持有者提交，仓储返回不能代表数据已对其他事务可见。

| 问题 | 证据 |
| --- | --- |
| 参数删除漏失效 | ConfigRepository 覆盖 `delete_by_id/delete_by_ids`，绕过基础仓储的失效调用；真实删除后 items 为 0，total 仍为 1 |
| 新增过早失效 | 真实 MySQL/Redis：写事务 flush → 失效 → 另一请求在提交前读到 0 并回填 → 写事务提交 → 新请求 items 为 1、total 仍为 0 |
| 筛选字段更新不失效 | BaseRepository.update 原来不失效；筛选字段变化后，旧条件和新条件的缓存总数都可能错误 |
| 未提交总数跨事务泄漏 | 写事务分页可将自己的未提交总数写入共享缓存；回滚后其他事务仍可能命中该值，修前针对性回归已复现 |
| 提交后删除也不足以解决所有竞态 | 旧 loader 可在失效之后完成并写回；即便总数缓存是最新值，它仍可能与已有 REPEATABLE READ 事务的旧快照不同 |

前两项有真实链路证据：[删除前后](evidence/2026-10-16-count-consistency/before-real.json)、[提交前回填](evidence/2026-10-16-count-consistency/before-transaction.json)。后三项结合静态调用审查、针对性回归及独立内存探针确认，没有把推断都称为真实业务测试。

SQLAlchemy 明确区分 flush 与 commit：[after_flush 在提交前触发，after_commit 才发生在提交后](https://docs.sqlalchemy.org/en/20/orm/events.html#sqlalchemy.orm.SessionEvents.after_commit)。MySQL 默认 REPEATABLE READ 下，同一事务的一致性读取使用既有快照；共享 Redis 值不会自动加入该快照。[MySQL 官方说明](https://dev.mysql.com/doc/refman/8.0/en/innodb-consistent-read.html)

## 方案选择与实现边界

没有只给参数删除补失效，也没有新增提交回调、缓存版本号或回填协调框架。经全仓盘点，COUNT 缓存的唯一生产读取方是 PageUtil，没有显式开启缓存的真实调用；生成器反而已因总数错误单独关闭它。没有找到必须保留这套机制的性能基准。

因此硬切移除透明 COUNT 缓存：PageUtil 对原查询构造 COUNT 子查询，并通过传入的 Session 执行。只在 COUNT 子查询中去除排序，保留 WHERE、JOIN、DISTINCT 等原查询语义；items 的排序和分页协议不变。已有 SQLAlchemy 与 PageUtil 足够，不另接分页框架。这也与 [fastapi-pagination 的 SQLAlchemy 实现](https://github.com/uriyyo/fastapi-pagination/blob/main/fastapi_pagination/ext/sqlalchemy.py)采用当前连接执行 COUNT、保留子查询统计的方式一致。

必要收敛包括：

- 删除 `utils/count_cache.py`、COUNT 专属配置、容器 provider/readiness 和服务启动接线。
- 删除 BaseRepository 的 COUNT 失效逻辑、专用成员与无效空分支，保持返回值和 CRUD 语义。
- 删除 PageUtil 的 `use_count_cache` 内部参数及分支；生成器移除不再需要的单点旁路，迁移其现有回归。
- ConfigRepository、ConfigService、TransactionManager、get_db 未改；参数键值 Redis 缓存和 query_cache 未改。旧 `count_cache:*` 键不再读写，按原 TTL 自行过期，无需清空 Redis。

收益是消除各写入口、提交、回滚和跨事务共享总数之间的失效责任，避免逐业务补丁。代价是原缓存命中的分页现在也执行一次数据库 COUNT。性能仍应以实际查询与数据量为依据；本轮不引入近似总数、分页框架或新的缓存模式。

## 验证结果

| 验证 | 结果 |
| --- | --- |
| 新增必要回归 | 修前 3 项失败；覆盖提交增删分页、回滚后不泄漏总数、更新筛选字段 |
| 受影响后端测试 | 91 项通过，覆盖分页、生成器、基础仓储、参数服务、事务、容器与命令管线 |
| 独立复核 | 无待处理问题；独立定向测试 87 项通过 |
| 后端约定脚本 | `validate.sh --changed` 通过 |
| 测试文件 Ruff／格式检查、修改 Python 编译 | 通过 |
| 旧文件全量 Ruff 对照 | 468 项降至 431 项，无新增诊断；未趁机格式化或修复整批历史代码 |
| 真实业务 | 7 项检查通过 |
| 真实 MySQL | 5 项检查通过，含清理 |

详见[验证记录](evidence/2026-10-16-count-consistency/verification.json)、[修前回归](evidence/2026-10-16-count-consistency/red.log)、[修后测试](evidence/2026-10-16-count-consistency/focused-final.log)、[约定检查](evidence/2026-10-16-count-consistency/conventions.log)和[Ruff 增量对照](evidence/2026-10-16-count-consistency/ruff-delta.json)。没有执行无关的前端构建或全仓测试。

## 真实参数与分页验证

使用生产业务 API/HTTP 模块、源码直连 @zxio/http、实际 FastAPI、MySQL 和 Redis；没有 browser/computer use 或原生表单视觉验证。

1. 连续新增 4 条参数，筛选总数立即从 0 依次变为 1、2、3、4，全表总数从 7 变为 8、9、10、11；GridList pager.total 同步正确。
2. 页大小为 1／2 时跨页核对记录 ID，没有重复或漏项；末尾空页保留正确 total；参数名、键名和类型组合筛选计数正确。
3. 在当前筛选对应的旧 COUNT 键中放入 0，列表仍返回实际总数 4，旧键保持 0，证明修复不依赖手工清缓存。
4. 修改本轮临时参数类型后，普通／内置筛选总数分别为 3／1。
5. 批量删除时先删除普通临时参数，再遇内置临时参数而返回 409：前一删除随事务回滚，总数和明细均保持 4；内置参数限制及参数键值读取保持有效。
6. 单删后 total 立即为 3，页大小 2 时页长度为 2／1／0；随后批删剩余 3 条，不同页大小均立即返回 total 0，全表恢复 7。
7. 每次清理后与原有参数明细逐项比较，原有 7 条记录未变，临时记录和探针旧缓存键均已删除。

详见[真实业务结果](evidence/2026-10-16-count-consistency/actual.json)。

## 真实事务与性能观察

在实际 MySQL REPEATABLE READ 下：

- 写事务未提交时，另一事务读到 total/items 0/0；写事务提交并开始新读取后得到 1/1，不再被提交前的 0 污染。
- 保持既有读事务，另一写事务提交第二条记录后，旧事务仍读到 1/1；读事务结束后，新事务读到 2/2。
- 保存点释放后，外层事务仍持有未提交新增记录：本事务读到 3，其他事务读到 2；外层回滚后仍为 2，没有把局部总数泄漏给其他事务。

这沿用现有数据库隔离语义，不代表跨请求固定快照，也没有更改其他数据库隔离级别。

本机实际 9 条参数数据（含探针临时记录）的 19 次 COUNT SQL，执行耗时中位数 **0.493 ms**、最大 **2.358 ms**。这是小数据量 SQL 耗时观察，不包含整个请求，也不是大表性能基准。[MySQL 验证结果](evidence/2026-10-16-count-consistency/mysql-actual.json)

## 清理与工作区保护

真实业务探针的 4 条参数记录和数据库事务探针的 2 条已提交记录均已清理；直接 MySQL 查询确认共 7 条原有参数、0 条探针记录。仅停止本轮启动的旧／新后端进程 63071、64669，8088 已无监听，没有改变 MySQL 和 Redis 容器状态。

本轮之外既有工作区修改保留，前端与 ZXUI 无改动，见[工作区保护](evidence/2026-10-16-count-consistency/baseline-preservation.json)。

## 计划检查点（实施前）

STATUS: PLAN_DRAFTED

FILES_WRITTEN:
- docs/plans/2026-10-16-count-consistency.md

EVIDENCE:
- READ: Repository guidance, COUNT cache, pagination, repository, service, session and container ownership.
- SEARCH: All COUNT readers, invalidation calls and explicit cache switches; no explicit enabled consumer found.
- COMMAND: Plan structure checks passed; real API deletion and MySQL/Redis precommit refill reproduced; three regressions failed before implementation.

PLAN_CHANGES:
- Remove unsupported cross-transaction COUNT sharing and retain existing SQLAlchemy transaction semantics.

WORK_ITEM_SYNC_SUGGESTION:
- none

NEXT_ACTION: current-session execution (completed with evidence above)

BLOCK_REASON: none

UNBLOCK_ACTION: none

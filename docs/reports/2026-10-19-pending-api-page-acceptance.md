# RuoYi 待执行项补验结果

已为上轮报告的 **35 个待执行操作补齐证据**：28 项通过当前本地运行服务执行，7 项共享清空/刷新操作在隔离存储上验证。发现的缓存误删、生成器事务/结构读取、字典读取污染和失败日志回滚问题均已修复。现有改动保留，未提交、推送或发布。

后续复验已将下表中 41 项历史证据全部替换为当前执行证据，见 [历史 41 项复验报告](2026-10-19-historical-api-page-revalidation.md)。本文件保留其完成当时的分类。

## 覆盖结果与边界

| 目录项分类 | 数量 | 解释 |
| --- | ---: | --- |
| 本轮本地运行服务请求 | 28 | 实际响应、落库/读回、下载与页面操作；预期拒绝响应也明确记录。 |
| 本轮隔离存储集成验证 | 7 | 四类日志全量清理、字典/参数刷新、全部缓存清理。使用生产路由、服务和仓储，通过 ASGI 发请求；数据库为临时 SQLite，Redis 为独立临时 Docker 实例。认证依赖覆盖为测试身份，没有冒充共享环境页面操作或完整认证验收。 |
| 上轮真实执行证据 | 93 | 保留上轮证据，没有声称本轮全部重跑。 |
| 既往模块证据 | 41 | 仍为历史证据，不等同于逐接口新执行。 |

合计 169 个目录操作。原 35 项不再是“未执行”，但执行证据不等于穷尽所有分支：`/dev/menu/sync` 只执行 `dryRun=true`，没有修改共享菜单；本地文件生成在当前 `allow_overwrite=false` 配置下实测返回 403，没有开启覆盖分支。空菜单 ID、空配置 ID 与旧工程导出入口按契约返回 422。健康入口另行记录。

逐项状态、响应与证据见 [coverage.json](evidence/2026-10-19-pending-api-page-acceptance/coverage.json)。

## 修复与根因

| 问题 | 根因、方案与复验 |
| --- | --- |
| 缓存清理误删相似键 | 名称清理使用无分隔边界的前缀匹配，单键清理使用后缀通配符。四个自有碰撞键中原本应保留的两个相邻键也被删除。改用转义后的 `名称:` 命名空间扫描与完整键精确 DEL；页面/API 同步传递名称和键，Redis 端口及现有 fake 同步声明扫描能力。复验两个相邻键保留，页面删除 `sys_config:zxqa_mvet0wd2` 返回 204。没有新增缓存框架。 |
| 合法建表 500 或假成功、缺字段 | MySQL DDL 隐式提交破坏请求保存点；拆开 DDL 后，请求事务中的旧信息模式快照又看不到新表或字段。DDL 使用独立连接，表/字段发现使用新连接；元数据写入仍由原事务处理。真实页面最终创建后立即读到全部 3 个字段；添加自有字段后页面同步得到 4 个，保留备注。MySQL 回归从已开启的请求事务验证保存点、字段导入和重复表 409。DDL 与元数据在 MySQL 中无法作为一个可回滚事务，未声称跨两者原子性；若后续元数据导入失败，已创建表可经现有导入入口处理。 |
| 非法 SQL 返回 500、混合语句可通过旧校验 | 将语法/类型错误作为 422；只接受当前库中有字段定义的 CREATE TABLE，拒绝混合语句、视图、查询建表、跨库目标、替换和重复表名。已存在表返回 409，引导使用现有导入入口。实际页面 422 保留弹框，单份错误文本，无未处理页面异常。 |
| 字典刷新读取时产生 UPDATE | `find_all` 直接把受 ORM 管理的时间属性改成字符串，读取污染实体并在 autoflush/commit 时写回；SQLite 会直接失败。返回原始 ORM 对象，交给已有响应/JSON 序列化边界处理时间。真实 Redis + 临时数据库的字典刷新、全部缓存重建通过。 |
| 失败登录/操作日志随异常回滚 | 日志与失败请求使用同一个事务，重新抛出原异常后日志也被回滚。复用容器已有独立会话保存失败日志；成功日志沿用请求事务，日志存储失败不替换原业务/认证错误。真实锁定错误仍为 401，但失败记录可见；页面解锁 204 后登录 200，再强退自有目标 204，目标读取 401。失败操作的 422 日志也保留。 |

方案参考：[MySQL 隐式提交](https://dev.mysql.com/doc/refman/8.0/en/implicit-commit.html)、[SQLAlchemy 异步连接](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncEngine.begin)、[Redis SCAN](https://redis.io/docs/latest/commands/scan/)。

## 真实页面与产物

- 服务看板：保存默认布局；编辑第一块仪表精度并保存为版本 2；重新加载；旧版本写入返回 409；恢复默认并保存为版本 3；删除本人布局后读回 null。检查 1440×1000、1100×800 工具栏与面板，按钮可见，无横向溢出。
- 生成器：创建临时表 A、编辑备注、增加一个自有字段后页面同步、导入临时表 B、下载 ZIP、批量删除两张表的生成元数据。参考 `sys_post` 的信息和字段保持不变，选择器清单正常减少两项。生成编辑页两个视口的字段和提交/返回入口可见。
- 缓存：从真实名称列表选 `sys_config`，点击本轮键并删除；完整键已在网络记录确认。名称清理的碰撞验证通过 API 完成，没有清空共享 `sys_config` 名称。
- 日志与会话：筛选自有账号，选择锁定失败日志执行解锁；页面分别删除自有登录日志 472、操作日志 1738、审计记录 48736，并确认不存在；页面仅强退自有目标会话。
- API 备用入口：菜单/角色菜单树、部门树及排除列表、部门导出、开发态状态/预演、JSON 工程导入。部门 103 在树中存在，在排除列表中消失；角色选中 ID 均属于返回树。JSON 导入工程 17 后读到版本 21，项目和版本字段匹配。没有把 API 调用标成页面点击。
- ZIP 共 8 个条目，5 个 Python 文件可解析，Vue SFC 和模板编译无错误；仅验证生成内容语法，没有部署生成的业务模块。部门 Excel 的中文列和研发部门行逐列匹配。

[看板小视口](evidence/2026-10-19-pending-api-page-acceptance/02-dashboard-small-reset.png)、[生成字段页](evidence/2026-10-19-pending-api-page-acceptance/03-generator-fields.png)、[缓存页](evidence/2026-10-19-pending-api-page-acceptance/05-cache-own-key.png)、[语义核对](evidence/2026-10-19-pending-api-page-acceptance/semantic-inspection.json)、[下载检查](evidence/2026-10-19-pending-api-page-acceptance/artifact-inspection.json)。

## 验证与保留

- 后端主回归 **56 项通过**，本地 MySQL 与私有 Redis 的显式 opt-in 均开启；额外 Redis 端口/fake 与缓存边界 **6 项通过**，其中 2 项与主回归重叠，合计 60 个不同用例。临时 Redis 已移除。
- 前端 **32 项通过**，完整 `vue-tsc --noEmit` 和本轮 ESLint 通过。前端未改变构建配置，本轮未重复生产构建；上轮构建证据继续保留。
- 5 个新增 Python 测试文件 Ruff 与格式检查通过。既有 Python 文件仍有原诊断；按规则计数与本轮文件基线比较无新增，日志装饰器原有分支/语句复杂度没有增长。
- 浏览器共记录 188 个响应，无未处理页面异常。记录中的两次建表 500 属于修复前探针，最终合法/非法建表分别为 200/422，并有修复后 MySQL 回归；未将旧错误记录删掉。
- 保存 1,949 个源码文件摘要与业务整文件基线。本轮改动 9 个既有源码文件、新增 6 个回归文件；ZXUI 源码摘要未变化，既有 Excel、会话、上传和表单改动保留。

[最终核对 13/13](evidence/2026-10-19-pending-api-page-acceptance/verification-summary.json)、[后端测试](evidence/2026-10-19-pending-api-page-acceptance/backend-final-tests.log)、[端口补验](evidence/2026-10-19-pending-api-page-acceptance/redis-port-tests.log)、[前端测试](evidence/2026-10-19-pending-api-page-acceptance/frontend-tests.log)、[类型检查](evidence/2026-10-19-pending-api-page-acceptance/typecheck.log)、[增量检查](evidence/2026-10-19-pending-api-page-acceptance/backend-lint-comparison.json)、[保留核对](evidence/2026-10-19-pending-api-page-acceptance/preservation.json)、[源码增量](evidence/2026-10-19-pending-api-page-acceptance/source-delta.patch)。

## 清理与运行状态

本轮账号 132、133 已删除，自有会话元数据、活动指针和 CSRF 均为 0；浏览器和 API 上下文已关闭。工程 17 的活动版本和拓扑为 0；临时物理表、生成表及字段为 0；本地 MySQL 回归另建的随机临时表也已清理。看板按已有删除契约保留 **1 个空内容删除标记**，活动布局和历史版本均为 0。登录、操作和审计轨迹保留，未清空共享日志。

80 前端、8088 后端均为 200，原 MySQL/Redis 保持运行。未创建提交，未推送。

[存储清理](evidence/2026-10-19-pending-api-page-acceptance/cleanup-storage.json)、[最终账号/会话核对](evidence/2026-10-19-pending-api-page-acceptance/cleanup-final.json)、[运行状态](evidence/2026-10-19-pending-api-page-acceptance/services-final.json)。

## Plan-stage checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN:
- docs/plans/2026-10-19-pending-api-page-acceptance.md
EVIDENCE:
- READ: previous report/coverage, repository AGENTS, production controller/service/repository and current page consumers.
- SEARCH: pending operations, cache-key callers, generator DDL/schema queries and transaction/log ownership.
- COMMAND: plan structural checks passed; source snapshot and runtime health reads passed.
PLAN_CHANGES:
- Added a focused continuation plan for all 35 pending rows and isolated global maintenance checks.
WORK_ITEM_SYNC_SUGGESTION:
- none; no bound work item.
NEXT_ACTION: current-session execution (performed; execution evidence above).
BLOCK_REASON: none
UNBLOCK_ACTION: none

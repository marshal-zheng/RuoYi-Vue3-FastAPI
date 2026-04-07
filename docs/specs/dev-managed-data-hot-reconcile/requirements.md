# 开发态受管数据近实时热对齐需求规格

## 简介
本规格定义“开发态受管数据近实时热对齐（Hot Reconcile）”能力：在 `DB_WORKFLOW_MODE=development` 下，将 `capabilities/modules/*.module.yaml` 中的菜单、角色授权、字典、配置与运行时 gate 变更自动感知、快速落库，并通过开发态 `SSE` 事件通道让前端动态路由近实时更新。该能力只作用于开发态，不改变正式发布阶段的 `finalize -> deploy` 治理链路，也不将业务受管数据交给 Atlas 管理。

## 需求列表

### R1: 开发态声明变更自动感知
**用户故事:** 作为开发者，我希望保存模块声明后系统能自动识别新增、修改、删除，以便无需手动执行 `dev-sync` 才能验证页面效果。  
**验收标准 (EARS):**
- R1.AC1: WHEN 应用运行于 `APP_ENV=dev` 且 `DB_WORKFLOW_MODE=development` THEN 系统 SHALL 启动开发态受管数据热对齐代理。
- R1.AC2: WHEN `capabilities/modules/*.module.yaml` 发生新增、修改或删除 THEN 系统 SHALL 自动感知该变化并触发一次热对齐判定。
- R1.AC3: WHEN 连续发生多次文件保存事件 THEN 系统 SHALL 对触发进行防抖合并，而 NOT 为每次保存分别执行完整同步。
- R1.AC4: IF 重新编译后的 capability checksum 与上次成功状态一致 THEN 系统 SHALL 跳过数据库写入与前端路由刷新。
- R1.AC5: IF `APP_ENV!=dev` 或 `DB_WORKFLOW_MODE!=development` THEN 系统 SHALL 禁用热对齐代理、开发态事件接口与相关自动行为。

### R2: 受管数据快路径同步
**用户故事:** 作为开发者，我希望菜单、授权、字典和配置类变更通过轻量快路径生效，以便避免每次保存都重复执行 Atlas schema 同步。  
**验收标准 (EARS):**
- R2.AC1: WHEN 热对齐代理检测到仅受管数据声明发生变化 THEN 系统 SHALL 执行受管数据快路径同步，而 SHALL NOT 触发 Atlas schema apply。
- R2.AC2: WHEN 受管数据快路径同步成功 THEN 系统 SHALL 按当前开发态全量目标态对齐 `sys_menu`、`sys_role_menu`、`sys_dict_type`、`sys_dict_data` 与 `sys_config`。
- R2.AC3: IF 同步过程中任一步骤失败 THEN 系统 SHALL 回滚本次数据库写入，并保留上一次成功状态。
- R2.AC4: IF 某记录不属于 capability 受管范围 THEN 系统 SHALL NOT 在热对齐过程中删除或改写该记录。
- R2.AC5: WHEN 开发者显式执行 `python scripts/db.py dev-sync` THEN 系统 SHALL 继续保留当前统一全量同步能力，作为人工兜底入口。

### R3: 基于 SSE 的前端动态路由更新
**用户故事:** 作为开发者，我希望后端完成热对齐后前端无需重登即可自动更新菜单，以便接近实时地验证页面导航结果。  
**验收标准 (EARS):**
- R3.AC1: WHEN 后端热对齐导致当前用户菜单签名发生变化 THEN 系统 SHALL 通过开发态 `SSE` 事件通道主动通知前端。
- R3.AC2: WHEN 前端收到菜单变更事件 THEN 前端 SHALL 自动重建动态路由，而 NOT 要求用户退出登录再登录。
- R3.AC3: IF 当前访问路由在重建后不再可访问 THEN 前端 SHALL 自动跳转到首个仍可访问菜单。
- R3.AC4: WHEN 开发者仅修改菜单/角色授权/字典/配置等受管数据声明 THEN 系统 SHALL 在正常本地开发环境下于 1 秒内使前端可见结果发生变化。
- R3.AC5: IF 开发态 `SSE` 通道临时不可用 THEN 系统 SHALL 提供低频兜底检查或手动刷新入口，但 SHALL NOT 以高频轮询作为主路径。

### R4: 开发体验与性能约束
**用户故事:** 作为开发者，我希望自动生效足够快且不会拖慢本地开发环境，以便提升而不是损害开发效率。  
**验收标准 (EARS):**
- R4.AC1: WHEN 系统处于空闲且声明未变化 THEN 系统 SHALL NOT 周期性执行数据库写入、全量 `dev-sync` 或全量动态路由重建。
- R4.AC2: WHEN 浏览器处于开发态热更新模式 THEN 每个标签页 SHALL 只维护一个轻量事件订阅连接，而 NOT 持续拉取完整路由树。
- R4.AC3: WHEN 连续保存同一声明文件 THEN 系统 SHALL 将短时间内的多次变更合并为一次快路径热对齐。
- R4.AC4: WHEN 热对齐完成 THEN 系统 SHALL 输出可观测的耗时与触发来源，以便团队评估是否满足近实时目标。
- R4.AC5: IF 变更仅影响受管数据 THEN 热对齐能力 SHALL 不阻塞正常的后端接口调试、前端 HMR 和数据库查询调试。

### R5: 日志降噪与调试可见性
**用户故事:** 作为开发者，我希望自动热对齐不会刷屏日志，以便在正常联调时仍然容易定位业务日志和错误信息。  
**验收标准 (EARS):**
- R5.AC1: WHEN 开发态 `SSE` 通道建立、保活或重连 THEN 系统 SHALL NOT 为每次连接活动输出 info 级业务日志。
- R5.AC2: WHEN 自动热对齐执行 THEN 系统 SHALL 只输出结构化摘要日志，包括触发来源、耗时、是否成功与变更计数。
- R5.AC3: IF 需要对象级 diff、checksum 对比或详细 reconcile 清单 THEN 系统 SHALL 仅在 debug 级别输出这些明细。
- R5.AC4: WHEN 浏览器订阅开发态 `SSE` 接口 THEN 系统 SHALL 提供访问日志降噪策略，避免该接口淹没正常调试日志。
- R5.AC5: IF 热对齐失败 THEN 系统 SHALL 输出单条可定位失败原因的错误日志，并保留人工兜底执行路径。

### R6: 与正式发布链路的边界一致性
**用户故事:** 作为维护者，我希望开发态热对齐只优化本地体验，而不改变正式环境的治理和发布方式。  
**验收标准 (EARS):**
- R6.AC1: WHEN 团队执行 `finalize` THEN 系统 SHALL 继续从正式声明生成 Alembic migration 与 release bundle，而不依赖开发态热对齐记录。
- R6.AC2: WHEN 团队执行 `deploy` 或 `verify` THEN 系统 SHALL 保持现有正式受管数据与 schema 校验行为不变。
- R6.AC3: IF 代码运行于测试、预发、生产或客户环境 THEN 系统 SHALL 不暴露开发态热对齐事件接口与文件监听能力。
- R6.AC4: WHEN 新能力交付完成 THEN 团队 SHALL 仍然遵循“开发态自动热对齐，正式态 `finalize -> deploy`”这一双阶段心智模型。

## Clarifications

### Session 2026-04-06
- Q: 本轮要不要把菜单、字典、配置这类受管数据交给 Atlas 统一处理？ -> A: 不要；Atlas 仍只负责 schema/DDL，受管数据由 capability/module 声明和 release bundle 管理。
- Q: 开发态热更新的主路径该选高频 polling 还是事件驱动？ -> A: 选事件驱动；高频 polling 只允许作为临时降级兜底，而不是主路径。
- Q: 菜单热更新是否需要达到“保存即见效”的体感？ -> A: 需要；纯受管数据变更在正常本地开发环境下以 1 秒内前端可见为目标。
- Q: schema 变更是否也要像菜单一样持续监听并自动热同步？ -> A: 不需要；schema 仍按现有双阶段边界处理，不引入持续自动 Atlas apply。
- Q: 自动热更新会不会污染联调日志？ -> A: 不能；必须提供日志降噪策略，只保留真正同步动作的摘要日志。
- Q: 开发态事件通道是否在需求层直接锁定为 SSE？ -> A: 是；开发态事件通道固定为 SSE，仅限开发环境，不影响正式部署链路。

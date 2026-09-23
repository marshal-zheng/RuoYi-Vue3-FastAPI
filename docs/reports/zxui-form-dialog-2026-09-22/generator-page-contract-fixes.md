# 生成器真实页面直接契约修复（B22/B23）

2026-09-23，root在真实业务导入sys_post元数据后发现序号NaN、修改按钮不导航、编辑字典选项异常。本代理核对公开GridList、HTTP适配和后端controller后，限定三SFC修复。

- `src/views/tool/gen/index.vue`：序号使用grid.pager.page/size；`loadTableData`保留GridList的{pager,query}交既有HTTP适配器，日期使用已有serializeDateRange query-transform；不再捕获失败后伪造空成功页。编辑按钮用公开getStateSnapshot().pager.page，替代不存在的getState()。搜索和日期过滤通过updateState键路径重置pager.page。
- `src/views/tool/gen/importTable.vue`：搜索/重置用公开updateState('pager.page',1)和updateState('query',{})，替代错误的对象参数。
- `src/views/tool/gen/editTable.vue`：字典optionselect后端ResponseUtil.ok_resource(list)返回collection，消费response.items。

仅只读查询确认本次sys_post元数据table_id=1，未修改原sys_post数据。未修改HTTP公共适配器、GridList库或生成器架构。总数0是否完全消除仍以root真实列表为准；后端PageUtil存在COUNT缓存，而生成器导入未见失效调用，未凭猜测扩展修复。

验证：三个SFC ESLint exit0（0 errors；importTable已有unused proxy 1 warning），记录verification/generator-contract-lint.log。首次完整vue-tsc仅报并行fixture App.vue:301/303两个TS2722，已交其owner修复；不冒称首次类型检查全绿。修复后的类型与真实UI结果继续追加。

只读补证：在真实DB已有sys_post元数据1条时，当前Redis `count_cache:gen_table:b326b5062b2f0e69` 值为0、TTL221秒；确认列表total0还受到服务COUNT缓存影响。此处仅读取明确COUNT键数值，不读认证键；尚未执行缓存清理或修改后端策略，已交root裁定直接必要修复。

root随后授权最小修复COUNT缓存：仅GenTableRepository.paginate_with_filters传use_count_cache=False，不动全局策略/导入事务/其他业务。自包含SQLite回归注入真实可返回0的共享缓存，导入1条再2条元数据，修前total0失败，修后total1/2且缓存未调用，1passed。新测试ruff通过；原repository整体134项Ruff与HEAD逐条对照无新增，见verification/generator-count-cache-ruff-baseline.json。后端源和测试已冻结并通知root恢复服务，未为此重启服务。

# 本地生成器元数据初始化（B22/B23）

2026-09-23，root明确授权仅本地dev新增缺失生成器表，不改已有表/数据/认证。本代理执行，与此前peer只读角色分开记录。

根因：后端 `logs/2026-09-23_error.log` 的02:55:15、02:55:35记录ProgrammingError1146，`ruoyi-fastapi.gen_table`不存在；第二次SQL包含真实浏览器搜索条件。`module_generator/repository/gen_repository.py:get_db_table_list`读取information_schema时排除已导入的gen_table，因缺表而500。首次show/nextTick和搜索均已发出请求，不是组件挂载或items适配遗漏。

核对现有模型 `module_generator/entity/do/gen_do.py`：只有GenTableDO→gen_table、GenTableColumnDO→gen_table_column（外键关联前者）。后端显式工作流要求非测试启动不自动create_all，因此没有启动全库dev-sync。

在本地127.0.0.1:3306、ruoyi-fastapi库使用既有SQLAlchemy连接，断言host/port/database后调用 `Base.metadata.create_all(connection, tables=[GenTableDO.__table__, GenTableColumnDO.__table__], checkfirst=True)`。连接事件guard只允许这两表的CREATE TABLE，拒绝其他DDL/DML。45秒显式timeout。两个表均缺失，实际只执行2条CREATE；35张旧表全部保留，总表数37，两新表均0行。没有登录、读token或改auth。

完整实际DDL、创建前后清单/计数收据：`verification/generator-schema-init.json`。随后通过真实GenTableRepository只读调用分页查询，10items/total34，字典项keys为tableName/tableComment/createTime/updateTime；未读取业务行内容。ZxGridList明确支持items。

真实浏览器B22/B23复验由root继续。当前自定义ElTable未消费GridList.error/renderEmpty导致500仅显示默认空表，这是已有错误展示局限；未为本轮扩大库组件修复。新增的本地元数据表是必要环境状态，保留供生成器使用，未创建用于生成测试的业务表。

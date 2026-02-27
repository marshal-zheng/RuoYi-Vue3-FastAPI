# 数据源接入管理 实现任务

- [x] 1. 创建数据源实体模型与数据库迁移
  - 新建 `module_admin/entity/do/datasource_do.py`，定义 `DataSourceDO` 继承 `BaseModel`，包含 name/type/host/port/username/password(sensitive_string)/database_name/description/status/extra_config(JSON) 字段
  - 新建 Alembic 迁移脚本创建 `sys_datasource` 表
  - 在 `module_admin/entity/do/__init__.py`（如有）中导出新实体
  _需求追溯: R2.AC6, R3.AC2, R6.AC1_

- [x] 2. 创建视图对象（VO）模型
  - 新建 `module_admin/entity/vo/datasource_vo.py`，定义 `DataSourceQueryModel`（查询参数）、`DataSourceModel`（新增/编辑）、`DataSourceDetailModel`（详情返回，密码脱敏）、`TestConnectionModel`（连通性测试请求体）
  - 所有模型继承 `CamelModelBase`，`DataSourceQueryModel` 使用 `@as_query` 装饰器
  _需求追溯: R1.AC1, R1.AC2, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R5.AC1, R6.AC1_

- [x] 3. 创建 Repository 层与端口接口
  - 新建 `module_admin/repository/datasource_repository.py`，继承 `BaseRepository[DataSourceDO]`，实现 `paginate_with_filters` 和 `find_by_name` 方法
  - 在 `ports/repositories.py` 新增 `IDataSourceRepository` 接口
  - 在 `ports/__init__.py` 中导出新接口
  - 在 `module_admin/repository/__init__.py` 中导出 `DataSourceRepository`
  _需求追溯: R1.AC1, R1.AC2, R2.AC6, R2.AC7, R4.AC1_

- [x] 4. 实现连通性测试工具
  - 新建 `module_admin/service/datasource_connector.py`，实现 `test_connection()` 分发函数
  - 分别实现 `_test_mysql`（aiomysql）、`_test_postgresql`（asyncpg）、`_test_mongodb`（motor）、`_test_minio`（miniopy-async）四个连接测试函数
  - 每个函数设置 5 秒超时，返回 `TestResult(success, message, latency_ms)`
  - 在 `requirements.txt` 中确认或新增 `aiomysql`、`asyncpg`、`motor`、`miniopy-async` 依赖
  _需求追溯: R5.AC1, R5.AC2, R5.AC3_

- [x] 5. 实现 Service 层业务逻辑
  - 新建 `module_admin/service/datasource_service.py`，构造函数注入 `IDataSourceRepository` + `AsyncSession`
  - 实现 `get_datasource_list_services`（分页查询）
  - 实现 `datasource_detail_services`（详情，密码字段置空）
  - 实现 `add_datasource_services`（名称唯一校验 + 新增）
  - 实现 `edit_datasource_services`（密码为空则跳过更新）
  - 实现 `delete_datasource_services`（软删除）
  - 实现 `test_connection_services`（代理到 Connector）
  - 在 `ports/services.py` 新增 `IDataSourceService` 接口并在 `ports/__init__.py` 导出
  _需求追溯: R1.AC1, R2.AC6, R2.AC7, R3.AC2, R3.AC3, R4.AC1, R5.AC4, R6.AC1_

- [x] 6. 实现 Controller 层与 DI 注册
  - 新建 `module_admin/controller/datasource_controller.py`，路由前缀 `/datasource`，实现 6 个接口（list/detail/add/edit/delete/test-connection）
  - 所有接口添加 `CheckUserInterfaceAuth('datasource:*')` 权限校验
  - 新增/编辑/删除接口添加 `@Log` 操作日志注解
  - 在 `container/providers.py` 新增 `_datasource_service_factory` 工厂函数并注册到 `SERVICE_FACTORY_REGISTRY`
  - 在路由注册入口文件中挂载 `datasourceController`
  _需求追溯: R1.AC1, R1.AC2, R2.AC6, R3.AC2, R4.AC1, R4.AC2, R5.AC4, R6.AC1_

- [x] 7. 创建前端 API 模块
  - 新建 `src/api/datasource/datasource.ts`，定义 `listDataSource`/`getDataSource`/`addDataSource`/`updateDataSource`/`delDataSource`/`testDataSourceConnection` 六个函数
  _需求追溯: R1.AC1, R2.AC6, R3.AC2, R4.AC1, R5.AC1_

- [x] 8. 实现前端数据源列表页
  - 新建 `src/views/datasource/index.vue` 入口页
  - 新建 `src/views/datasource/components/DataSourceList.vue`，使用 `ZxGridList` 展示分页表格
  - 实现搜索栏（名称输入框 + 类型下拉筛选）
  - 实现操作列按钮（编辑/测试/删除），删除带二次确认
  - 实现列表测试按钮点击后更新连接状态
  - 实现空状态引导
  _需求追溯: R1.AC1, R1.AC2, R1.AC3, R4.AC1, R4.AC2, R5.AC4_

- [x] 9. 实现前端新增向导与编辑表单
  - 新建 `src/views/datasource/components/DataSourceWizard.vue`，实现两步向导 Dialog
  - Step 1：四张数据源类型卡片（带图标），选中高亮，"下一步"按钮
  - Step 2：动态表单根据类型渲染通用字段 + 特有字段（MySQL/PG 显示数据库名，MongoDB 显示数据库名+认证源，MinIO 显示存储桶+SSL 开关）
  - 表单底部"测试连接"按钮，带加载状态和成功/失败反馈
  - 新建 `src/views/datasource/components/DataSourceForm.vue`，编辑时复用的表单组件，类型字段只读，密码字段显示掩码占位符
  _需求追溯: R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R2.AC6, R2.AC7, R3.AC1, R3.AC3, R5.AC1, R5.AC2, R5.AC3_

- [ ] 10. 补齐后端单元测试
  - 新建 `tests/unit/services/test_datasource_service.py`：覆盖 CRUD 全流程、名称唯一校验失败、密码跳过更新、软删除
  - 新建 `tests/unit/services/test_datasource_connector.py`：mock 四种数据源连接库，覆盖成功/失败/超时场景
  - 新建 `tests/unit/repositories/test_datasource_repository.py`：覆盖分页查询、按名称查找、软删除过滤
  _需求追溯: R1.AC1, R2.AC6, R2.AC7, R3.AC3, R4.AC1, R5.AC1, R5.AC2, R5.AC3, R6.AC1_

- [ ] 11. 补齐前端组件测试
  - 新建 `src/views/datasource/__tests__/DataSourceWizard.spec.ts`：覆盖类型选择、动态表单渲染、字段校验
  - 新建 `src/views/datasource/__tests__/DataSourceList.spec.ts`：覆盖列表加载、搜索筛选、删除确认交互
  _需求追溯: R1.AC1, R1.AC2, R2.AC1, R2.AC2, R4.AC1_

- [ ] 12. 集成验证与路由/菜单配置
  - 在前端路由配置中注册 `/datasource` 页面路由
  - 在菜单表中插入"数据源中心"菜单项及 `datasource:list`/`datasource:query`/`datasource:add`/`datasource:edit`/`datasource:remove` 权限标识
  - 运行后端 `pytest` 与前端 `yarn lint:check && yarn type-check && yarn test:run` 确认无回归
  - 复核需求追溯矩阵，确保所有 AC ID 已覆盖
  _需求追溯: R1.AC1, R1.AC2, R1.AC3, R2.AC1, R2.AC2, R2.AC3, R2.AC4, R2.AC5, R2.AC6, R2.AC7, R3.AC1, R3.AC2, R3.AC3, R4.AC1, R4.AC2, R5.AC1, R5.AC2, R5.AC3, R5.AC4, R6.AC1_

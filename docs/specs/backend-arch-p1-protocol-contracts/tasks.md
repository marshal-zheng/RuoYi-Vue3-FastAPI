# Protocol 接口契约实现任务

- [x] 1. 创建 `ports` 包并建立统一导出入口
  - 新增 `ruoyi-fastapi-backend/ports/__init__.py`，定义统一导出规范。
  - 建立 `ports/repositories.py`、`ports/services.py`、`ports/external.py` 三个契约文件骨架。
  - 约束后续新契约必须从 `ports` 入口导出。
  _需求追溯: R1.AC1, R1.AC4, R5.AC1, R5.AC4_

- [x] 2. 完成 Repository Protocol 全量定义与签名对齐
  - 以 `module_admin/repository` 公开仓储为范围，逐个定义 `I*Repository` Protocol。
  - 对齐方法参数、返回类型与语义 docstring。
  - 修复调用侧类型注解，确保依赖方引用接口类型。
  _需求追溯: R1.AC2, R1.AC3, R2.AC1, R2.AC2, R2.AC3, R2.AC4_

- [x] 3. 完成 Service Protocol 全量定义与签名对齐
  - 为 `module_admin/service` 与 `module_generator/service` 对外能力建立 `I*Service` Protocol。
  - 清理调用侧实现类类型依赖，统一替换为服务接口类型。
  - 对内部辅助方法进行隔离，不纳入对外 Protocol。
  _需求追溯: R1.AC2, R3.AC1, R3.AC2, R3.AC3, R3.AC4_

- [x] 4. 建立基础设施 Protocol 并替换业务调用依赖
  - 定义 `IRedisClient`、`ICacheProvider`、`IAuditLogger`、`IEventBus` 契约。
  - 将服务层对外部依赖引用改为接口类型。
  - 准备最小 fake/stub 实现用于单元测试注入。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4_

- [x] 5. 统一契约命名与组织规则并补充文档
  - 规范接口命名（`I` 前缀、领域后缀）与导入路径。
  - 确认公共契约与上下文私有契约划分标准。
  - 在架构文档中记录“一次跳转可达”检索规则。
  _需求追溯: R5.AC2, R5.AC3, R5.AC4, R1.AC4_

- [x] 6. 实现契约治理脚本与 CI 门禁
  - 补齐协议更新与覆盖率历史治理脚本（现已移除）。
  - 输出覆盖率与缺口列表，并在当时接入 CI。
  - 阻断新增实现耦合导入与未同步契约变更。
  _需求追溯: R6.AC1, R6.AC2, R6.AC3, R6.AC4_

- [x] 7. 执行回归并完成验收
  - 运行类型检查、目标模块单测与关键集成测试。
  - 校验运行时行为不变（仅类型边界变化）。
  - 归档契约覆盖率报告与整改清单。
  _需求追溯: R2.AC3, R3.AC1, R4.AC3, R6.AC2, R6.AC3_

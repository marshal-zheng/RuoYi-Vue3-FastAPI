# 数据库双阶段工作流 实现任务

> 注：当前仓库已完成进一步收口，公开入口为 `scripts/db.py`，开发态以 `dev-sync` 取代公开 `push` 命令。本文保留阶段性任务记录。

- [x] 1. 引入数据库工作流配置并统一模式入口
  - 在 `ruoyi-fastapi-backend/config/env.py` 新增 `DB_WORKFLOW_MODE`、`DB_PUSH_ON_STARTUP`、`DB_PUSH_ENGINE` 配置项，默认值分别为 `migration`、`true`、`atlas`
  - 在配置加载阶段保持“默认 migration、显式开启 push”的约束，不依赖 `APP_ENV` 自动推断工作流模式
  - 提供统一的工作流状态读取函数，供启动脚本、CLI 与运行时日志复用
  _需求追溯: R1.AC4, R2.AC3, R2.AC4, R5.AC1, R5.AC4_

- [x] 2. 实现高层数据库工作流 CLI
  - 新建 `ruoyi-fastapi-backend/scripts/db.py`，统一暴露历史快速同步、正式化、部署、状态查询四类能力
  - `status` 输出当前模式、目标数据库、是否启用启动前 `db push`、当前 deploy 路径
  - `push` 在非 `push` 模式下直接失败，在 `push` 模式下输出目标数据库和破坏性变更风险边界
  - `deploy` 包装现有 Alembic `upgrade` 行为，作为共享环境和正式环境的统一入口
  _需求追溯: R1.AC1, R2.AC2, R5.AC1, R5.AC2, R5.AC4, R5.AC6, R6.AC1_

- [x] 3. 接入开发态 `db push` 适配器
  - 新建 `ruoyi-fastapi-backend/scripts/db_push_atlas.py` 与 `ruoyi-fastapi-backend/atlas.hcl`
  - 使用 SQLAlchemy `Base.metadata` 作为 schema 源，驱动 Atlas Script Mode 执行 `schema apply`
  - 在历史快速同步阶段调用该适配器，并透传当前 `DB_*` 连接配置
  - 明确输出本次 `db push` 的执行结果、目标库摘要和破坏性变更提示
  _需求追溯: R1.AC1, R1.AC2, R1.AC7, R5.AC2, R5.AC3, R5.AC6_

- [x] 4. 改造本地启动脚本为模式分发
  - 修改 `scripts/start.sh`，在启动后端前先调用 `python scripts/db.py status`
  - 当 `DB_WORKFLOW_MODE=push` 且 `DB_PUSH_ON_STARTUP=true` 时，在启动应用前执行一次历史快速同步阶段
  - 当模式为 `migration` 时，改为执行 `python scripts/db.py deploy --revision head`
  - 保留现有数据库连通性检查、Redis 检查和前后端启动行为
  - 在脚本输出中明确标识本次是否执行了启动前 `db push`，以及当前阶段不支持持续监听自动同步
  _需求追溯: R1.AC5, R1.AC6, R2.AC4, R5.AC1, R5.AC5_

- [x] 5. 移除非测试环境运行时 `create_all()` 隐式补表逻辑
  - 调整 `ruoyi-fastapi-backend/config/get_db.py` 中的 `init_create_table()`，使其在测试环境以外不再执行 `Base.metadata.create_all()`
  - 保持测试环境与现有单元测试、SQLite 内存库用例兼容
  - 更新 `ruoyi-fastapi-backend/server.py` 对该入口的语义说明，使其仅承担运行时数据库初始化与连接校验职责
  _需求追溯: R1.AC2, R2.AC4, R5.AC3, R7.AC3_

- [x] 6. 实现 `finalize` 正式化流程
  - 在 `db.py finalize` 中创建临时 finalize 数据库，并基于正式 `alembic/versions` 的 head 执行 `alembic upgrade head`
  - 在临时 finalize 数据库上执行 `alembic revision --autogenerate -m "<描述>"`，生成正式 migration 文件
  - 生成后对新 migration 执行升级验证与 drift 校验，确保结果代表“正式 head -> 当前 models”的差异
  - finalize 成功后清理临时数据库并输出 revision 文件路径
  _需求追溯: R3.AC1, R3.AC2, R3.AC3, R4.AC2, R6.AC2, R6.AC3, R7.AC2, R7.AC3_

- [x] 7. 维持共享环境与正式部署的 migration-only 链路
  - 保持 `ruoyi-fastapi-backend/docker-entrypoint.sh` 的正式迁移语义，只允许 `deploy`/`alembic upgrade head`
  - 如需统一入口，改为在 Docker 中调用 `python scripts/db.py deploy --revision head`，但不引入 `push`
  - 明确共享开发库、联调、测试、预发、生产和客户现场升级都以正式 migration 为标准交付路径
  _需求追溯: R2.AC1, R2.AC2, R3.AC3, R4.AC3, R6.AC1, R6.AC2_

- [x] 8. 加固 CI 漂移校验与提交流程
  - 复用 `ruoyi-fastapi-backend/scripts/db.py verify`，确保 PR、主干、发布分支继续只校验正式 migration 历史
  - 在开发文档和提交流程中明确：进入 Git、共享环境或发布前必须先执行 `finalize`
  - 确保存在未正式化 drift 时，CI 阻止合并和发布
  _需求追溯: R2.AC1, R3.AC1, R6.AC3, R7.AC1, R7.AC2_

- [x] 9. 补齐自动化测试
  - 新建 `db.py` 相关单元测试，覆盖快速同步 / `finalize` / `deploy` / `status` 参数、模式分发与错误码
  - 为 `scripts/start.sh` 增加集成验证，覆盖 `migration` 模式与 `push` 模式下的启动分支
  - 为 `init_create_table()` 增加回归测试，确保非测试环境不再执行 `create_all()`
  - 为 `finalize` 增加临时数据库升级与 drift 校验测试
  _需求追溯: R1.AC2, R1.AC5, R1.AC7, R2.AC2, R3.AC2, R5.AC3, R5.AC5, R7.AC3_

- [x] 10. 更新开发与发布文档
  - 更新 `scripts/README.md`、`ruoyi-fastapi-backend/scripts/README.md` 与相关数据库迁移文档，说明 `push / finalize / deploy` 的使用边界
  - 说明“默认 migration、显式开启 push、启动脚本可自动执行一次 push、不做持续监听”的行为
  - 补充客户升级与共享环境只走正式 migration 的操作说明
  - 补充长期工作流示例：`push -> finalize -> deploy`
  _需求追溯: R1.AC3, R1.AC6, R4.AC1, R4.AC3, R5.AC4, R6.AC1_

# 验收追溯与交付边界

状态：代码与最终候选自动验证已收敛；真实 UI 尚未验收，不能声明 23 项或整个 spec 已完成。用户已授权交付源分支后自行手测；本表不将该授权当作 UI 通过。源分支事务与自动验证另见 source-delivery.md；未发布 npm、未执行日常/生产迁移。

证据层级：静态=调用/契约核对；DOM=真实组件内存运行；HTTP=真实 ASGI/DI/repository 与隔离 SQLite；MySQL=本机 Docker 中一次性数据库；UI=真实用户界面交互。前四种均不能代替最后一种。

实现、测试与失败详情分别见 [契约](contract-verification.md)、[后端 API](backend-api-verification.md)、[前端/生成器](frontend-generator-verification.md)、[库/包](library-package-verification.md)、[数据库演练](migration-rehearsal.md)、[真实业务待验矩阵](business-acceptance.md)。[使用说明](usage.md) 与 [恢复手册](upgrade-recovery.md) 是交付文档。

| AC | 实现位置/机制 | 证据与状态 |
| --- | --- | --- |
| R1.AC1 | consumer-matrix.md；七表 DO/DTO、七入口、生成器显式策略 | 消费者静态矩阵；HTTP 7 项；范围外 Editor regression；界面另验；自动化部分有证据；真实 UI 待验 |
| R1.AC2 | consumer-matrix.md；七表 DO/DTO、七入口、生成器显式策略 | 消费者静态矩阵；HTTP 7 项；范围外 Editor regression；界面另验；按所列层级验证；不推定界面或部署完成 |
| R1.AC3 | consumer-matrix.md；七表 DO/DTO、七入口、生成器显式策略 | 消费者静态矩阵；HTTP 7 项；范围外 Editor regression；界面另验；按所列层级验证；不推定界面或部署完成 |
| R1.AC4 | consumer-matrix.md；七表 DO/DTO、七入口、生成器显式策略 | 消费者静态矩阵；HTTP 7 项；范围外 Editor regression；界面另验；自动化部分有证据；真实 UI 待验 |
| R2.AC1 | ZXUI text-editor/src/text-editor-field.vue、editor/basic-rich-text-extension.ts | 共享 102 vectors；Field 16 real-runtime DOM tests；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R2.AC2 | ZXUI text-editor/src/text-editor-field.vue、editor/basic-rich-text-extension.ts | 共享 102 vectors；Field 16 real-runtime DOM tests；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R2.AC3 | ZXUI text-editor/src/text-editor-field.vue、editor/basic-rich-text-extension.ts | 共享 102 vectors；Field 16 real-runtime DOM tests；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R2.AC4 | ZXUI text-editor/src/text-editor-field.vue、editor/basic-rich-text-extension.ts | 共享 102 vectors；Field 16 real-runtime DOM tests；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R2.AC5 | ZXUI text-editor/src/text-editor-field.vue、editor/basic-rich-text-extension.ts | 共享 102 vectors；Field 16 real-runtime DOM tests；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R2.AC6 | ZXUI text-editor/src/text-editor-field.vue、editor/basic-rich-text-extension.ts | 共享 102 vectors；Field 16 real-runtime DOM tests；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R3.AC1 | 公开 root/core/style、vite/zxui-theme-packages.ts、ZXUI source.ts | library-package-verification.md；源码生产构建；实际候选包门禁；按所列层级验证；不推定界面或部署完成 |
| R3.AC2 | 公开 root/core/style、vite/zxui-theme-packages.ts、ZXUI source.ts | library-package-verification.md；源码生产构建；实际候选包门禁；按所列层级验证；不推定界面或部署完成 |
| R3.AC3 | 公开 root/core/style、vite/zxui-theme-packages.ts、ZXUI source.ts | library-package-verification.md；源码生产构建；实际候选包门禁；按所列层级验证；不推定界面或部署完成 |
| R3.AC4 | 公开 root/core/style、vite/zxui-theme-packages.ts、ZXUI source.ts | library-package-verification.md；源码生产构建；实际候选包门禁；自动化部分有证据；真实 UI 待验 |
| R3.AC5 | 公开 root/core/style、vite/zxui-theme-packages.ts、ZXUI source.ts | library-package-verification.md；源码生产构建；实际候选包门禁；自动化部分有证据；真实 UI 待验 |
| R4.AC1 | Remark/useRemarkField.ts、七入口会话、Formily public binding/control port | frontend-generator-verification.md；FormilyIntegration；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R4.AC2 | Remark/useRemarkField.ts、七入口会话、Formily public binding/control port | frontend-generator-verification.md；FormilyIntegration；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R4.AC3 | Remark/useRemarkField.ts、七入口会话、Formily public binding/control port | frontend-generator-verification.md；FormilyIntegration；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R4.AC4 | Remark/useRemarkField.ts、七入口会话、Formily public binding/control port | frontend-generator-verification.md；FormilyIntegration；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R4.AC5 | Remark/useRemarkField.ts、七入口会话、Formily public binding/control port | frontend-generator-verification.md；FormilyIntegration；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R5.AC1 | common/remark_document_v1.py、remark_vo.py、七 DO/DTO/read_models、OpenAPI/client | backend-api-verification.md；真实 MySQL 七 ORM CRUD；OpenAPI 再生；按所列层级验证；不推定界面或部署完成 |
| R5.AC2 | common/remark_document_v1.py、remark_vo.py、七 DO/DTO/read_models、OpenAPI/client | backend-api-verification.md；真实 MySQL 七 ORM CRUD；OpenAPI 再生；按所列层级验证；不推定界面或部署完成 |
| R5.AC3 | common/remark_document_v1.py、remark_vo.py、七 DO/DTO/read_models、OpenAPI/client | backend-api-verification.md；真实 MySQL 七 ORM CRUD；OpenAPI 再生；按所列层级验证；不推定界面或部署完成 |
| R5.AC4 | common/remark_document_v1.py、remark_vo.py、七 DO/DTO/read_models、OpenAPI/client | backend-api-verification.md；真实 MySQL 七 ORM CRUD；OpenAPI 再生；按所列层级验证；不推定界面或部署完成 |
| R5.AC5 | common/remark_document_v1.py、remark_vo.py、七 DO/DTO/read_models、OpenAPI/client | backend-api-verification.md；真实 MySQL 七 ORM CRUD；OpenAPI 再生；按所列层级验证；不推定界面或部署完成 |
| R5.AC6 | common/remark_document_v1.py、remark_vo.py、七 DO/DTO/read_models、OpenAPI/client | backend-api-verification.md；真实 MySQL 七 ORM CRUD；OpenAPI 再生；按所列层级验证；不推定界面或部署完成 |
| R6.AC1 | 共享 validate_remark、public validateBasicRichTextDocument/Href、鉴权与事务 handler | contract-verification.md；backend-api-verification.md；按所列层级验证；不推定界面或部署完成 |
| R6.AC2 | 共享 validate_remark、public validateBasicRichTextDocument/Href、鉴权与事务 handler | contract-verification.md；backend-api-verification.md；按所列层级验证；不推定界面或部署完成 |
| R6.AC3 | 共享 validate_remark、public validateBasicRichTextDocument/Href、鉴权与事务 handler | contract-verification.md；backend-api-verification.md；按所列层级验证；不推定界面或部署完成 |
| R6.AC4 | 共享 validate_remark、public validateBasicRichTextDocument/Href、鉴权与事务 handler | contract-verification.md；backend-api-verification.md；按所列层级验证；不推定界面或部署完成 |
| R6.AC5 | 共享 validate_remark、public validateBasicRichTextDocument/Href、鉴权与事务 handler | contract-verification.md；backend-api-verification.md；按所列层级验证；不推定界面或部署完成 |
| R6.AC6 | 共享 validate_remark、public validateBasicRichTextDocument/Href、鉴权与事务 handler | contract-verification.md；backend-api-verification.md；按所列层级验证；不推定界面或部署完成 |
| R7.AC1 | RemarkDisplay、六 export service、ExcelUtil text_columns、dict cache | Excel workbook 值及 data_type=s；HTTP/cache；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R7.AC2 | RemarkDisplay、六 export service、ExcelUtil text_columns、dict cache | Excel workbook 值及 data_type=s；HTTP/cache；真实 UI 待验；自动化部分有证据；真实 UI 待验 |
| R7.AC3 | RemarkDisplay、六 export service、ExcelUtil text_columns、dict cache | Excel workbook 值及 data_type=s；HTTP/cache；真实 UI 待验；按所列层级验证；不推定界面或部署完成 |
| R7.AC4 | RemarkDisplay、六 export service、ExcelUtil text_columns、dict cache | Excel workbook 值及 data_type=s；HTTP/cache；真实 UI 待验；按所列层级验证；不推定界面或部署完成 |
| R7.AC5 | RemarkDisplay、六 export service、ExcelUtil text_columns、dict cache | Excel workbook 值及 data_type=s；HTTP/cache；真实 UI 待验；按所列层级验证；不推定界面或部署完成 |
| R7.AC6 | RemarkDisplay、六 export service、ExcelUtil text_columns、dict cache | Excel workbook 值及 data_type=s；HTTP/cache；真实 UI 待验；按所列层级验证；不推定界面或部署完成 |
| R8.AC1 | remark_policy、Vue3/Python templates、gen_service、bootstrap/compiler/remark_inputs | frontend-generator-verification.md；migration-rehearsal.md；自动化部分有证据；真实 UI 待验 |
| R8.AC2 | remark_policy、Vue3/Python templates、gen_service、bootstrap/compiler/remark_inputs | frontend-generator-verification.md；migration-rehearsal.md；自动化部分有证据；真实 UI 待验 |
| R8.AC3 | remark_policy、Vue3/Python templates、gen_service、bootstrap/compiler/remark_inputs | frontend-generator-verification.md；migration-rehearsal.md；按所列层级验证；不推定界面或部署完成 |
| R8.AC4 | remark_policy、Vue3/Python templates、gen_service、bootstrap/compiler/remark_inputs | frontend-generator-verification.md；migration-rehearsal.md；按所列层级验证；不推定界面或部署完成 |
| R8.AC5 | remark_policy、Vue3/Python templates、gen_service、bootstrap/compiler/remark_inputs | frontend-generator-verification.md；migration-rehearsal.md；按所列层级验证；不推定界面或部署完成 |
| R9.AC1 | scripts/data_migrations/remark_document_v2.py、正式 20261022 revision | migration-rehearsal.md；upgrade-recovery.md；按所列层级验证；不推定界面或部署完成 |
| R9.AC2 | scripts/data_migrations/remark_document_v2.py、正式 20261022 revision | migration-rehearsal.md；upgrade-recovery.md；按所列层级验证；不推定界面或部署完成 |
| R9.AC3 | scripts/data_migrations/remark_document_v2.py、正式 20261022 revision | migration-rehearsal.md；upgrade-recovery.md；按所列层级验证；不推定界面或部署完成 |
| R9.AC4 | scripts/data_migrations/remark_document_v2.py、正式 20261022 revision | migration-rehearsal.md；upgrade-recovery.md；按所列层级验证；不推定界面或部署完成 |
| R9.AC5 | scripts/data_migrations/remark_document_v2.py、正式 20261022 revision | migration-rehearsal.md；upgrade-recovery.md；按所列层级验证；不推定界面或部署完成 |
| R9.AC6 | scripts/data_migrations/remark_document_v2.py、正式 20261022 revision | migration-rehearsal.md；upgrade-recovery.md；按所列层级验证；不推定界面或部署完成 |
| R10.AC1 | db.py、dev_sync/finalize/deploy/workflow_verify、Alembic env/impl | migration-rehearsal.md；原目录既有 artifact/schema 门禁失败单列；按所列层级验证；不推定界面或部署完成 |
| R10.AC2 | db.py、dev_sync/finalize/deploy/workflow_verify、Alembic env/impl | migration-rehearsal.md；原目录既有 artifact/schema 门禁失败单列；按所列层级验证；不推定界面或部署完成 |
| R10.AC3 | db.py、dev_sync/finalize/deploy/workflow_verify、Alembic env/impl | migration-rehearsal.md；原目录既有 artifact/schema 门禁失败单列；按所列层级验证；不推定界面或部署完成 |
| R10.AC4 | db.py、dev_sync/finalize/deploy/workflow_verify、Alembic env/impl | migration-rehearsal.md；原目录既有 artifact/schema 门禁失败单列；按所列层级验证；不推定界面或部署完成 |
| R10.AC5 | db.py、dev_sync/finalize/deploy/workflow_verify、Alembic env/impl | migration-rehearsal.md；原目录既有 artifact/schema 门禁失败单列；按所列层级验证；不推定界面或部署完成 |
| R11.AC1 | 本表、四类验证报告、usage/upgrade-recovery、tasks.md | 本目录报告；真实 UI 待验；真实 PostgreSQL 未验证；按所列层级验证；不推定界面或部署完成 |
| R11.AC2 | 本表、四类验证报告、usage/upgrade-recovery、tasks.md | 本目录报告；真实 UI 待验；真实 PostgreSQL 未验证；自动化部分有证据；真实 UI 待验 |
| R11.AC3 | 本表、四类验证报告、usage/upgrade-recovery、tasks.md | 本目录报告；真实 UI 待验；真实 PostgreSQL 未验证；按所列层级验证；不推定界面或部署完成 |
| R11.AC4 | 本表、四类验证报告、usage/upgrade-recovery、tasks.md | 本目录报告；真实 UI 待验；真实 PostgreSQL 未验证；自动化部分有证据；真实 UI 待验 |
| R11.AC5 | 本表、四类验证报告、usage/upgrade-recovery、tasks.md | 本目录报告；真实 UI 待验；真实 PostgreSQL 未验证；按所列层级验证；不推定界面或部署完成 |

## 未验证与已知基线

- 用户未授权 computer use；七入口真实保存/重开/清空、主题/density/portal/焦点/真实粘贴等保持未验收。
- PostgreSQL 仅方言映射、参数/NULL、事务改名和故障回滚分支探针；真实 PostgreSQL 未验证。
- 全量门禁若含既有失败，须附与输入 HEAD 的同命令对比。原历史 release baseline 的原始 checksum 与正文已不一致；不重写历史产物。原正式链还有与本轮无关的全局 schema drift。仓库外副本完整 finalize/deploy/verify 通过，只证明对应路径，不能把原目录门禁标绿。
- StrictInt 的 JSON 1.0 词法差异及 URL parser 版本边界见契约报告；正常编辑器整数经 JSON.stringify 序列化为 1。
- 独立最终审查与 completion proof 尚待所有可执行验证和报告齐备后进行；没有该证明不作 implementation-complete 声明。

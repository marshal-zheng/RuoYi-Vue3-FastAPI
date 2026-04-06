# 能力纳管与发布选择 实现任务

- [x] 1. 建立 capability 纳管底座与元数据模型
  - 在 `scripts/internal/db_workflow/` 下新增 capability 编译与解析的核心模型，定义模块声明、编译结果、发布选择结果、运行时 gate 等内部数据结构。
  - 为 `sys_db_workflow_object` 增补 `module_key`、`object_domain`、`source_checksum` 等字段，并补齐对应 DO、migration 与仓库读写逻辑。
  - 收紧 ownership 规则，明确 `sys_db_workflow_object` 为唯一受管 authority，移除 `managed_by_seed` 参与 prune 判定的控制职责。
  - 为新增数据结构和元数据表扩展补齐单元测试，覆盖对象归属、checksum 和非受管对象保护语义。
  _需求追溯: R1.AC2, R5.AC1, R7.AC1, R7.AC3, R8.AC1_

- [x] 2. 实现模块声明编译层并移除 legacy 双轨输入
  - 新增 `CapabilityDeclarationCompiler`，支持扫描 `capabilities/modules/*.module.yaml` 并产出稳定排序的 capability target state。
  - 仅保留 `ModuleManifestAdapter` 作为正式运行入口，停止 `menus.registry.yaml`、`dict_types.yaml`、`dict_data.yaml`、`configs.yaml` 参与正式编译链路。
  - 设计并实现 `menu_key`、模块依赖、父级菜单依赖、授权归属、字典/配置 ownership 的编译规则。
  - 输出结构化 checksum 与声明校验结果，供 `dev-sync/finalize/verify` 复用。
  _需求追溯: R1.AC1, R1.AC2, R2.AC1, R2.AC2, R3.AC4, R8.AC2, R9.AC1_

- [x] 3. 将 `release-plan.yaml` 升级为模块级发布选择解析器
  - 将 `scripts/seed_data/release-plan.yaml` 从对象级输入升级为模块级两态输入，并实现向后不兼容的解析与验证逻辑。
  - 新增 `ReleasePlanResolver`，只接受模块 `true/false`，自动展开模块依赖、父级菜单依赖和运行时 gate 配置。
  - 明确能力组/profile 仅作模板来源，不进入日常主入口，并在校验层阻止对象级 `menu_ids/role_grants/dict_types/config_keys` 回流。
  - 补齐解析器测试，覆盖未知模块、依赖缺失、循环依赖、非法值与模板预填场景。
  _需求追溯: R1.AC5, R3.AC1, R3.AC2, R3.AC3, R3.AC5, R3.AC6, R3.AC7, R3.AC8_

- [x] 4. 重构 `dev-sync` 为真正的 capability state reconcile
  - 在 `dev-sync` 中接入 capability 编译器，使用编译后的全量目标态替代现有分散声明输入。
  - 复用现有 schema apply 能力后，执行 capability 级 planner/applier，对菜单、授权、字典、配置和 gate 进行全量收敛。
  - 新增 `PostconditionVerifier`，在 apply 后重新读库并对目标态做二次规划；若仍存在待执行差异或元数据漂移，则整体失败。
  - 扩展 `dev-sync` 输出，增加 `compiled_checksum`、后置校验结果、残留对象列表，修复“假成功但页面仍旧可见”的问题。
  _需求追溯: R4.AC1, R4.AC2, R4.AC3, R4.AC4, R7.AC2, R7.AC4, R9.AC2, R9.AC3_

- [x] 5. 重构 `finalize/deploy/verify` 以消费 capability 编译结果
  - 在 `finalize` 中接入 capability 编译器和模块级 `release-plan`，基于模块选择生成 release target state。
  - 将 release bundle 生成逻辑切换为从 release target state 下沉出 `managed-data.yaml` 与 `release.manifest.yaml`，不再从对象级选择直接投影。
  - 在 `deploy` 中加入 capability postcondition verify，并把编译 checksum、release-plan checksum 和对象级 drift 写入结果与 artifact history。
  - 在 `verify --ci` 中输出声明合法性、release-plan 校验、对象级 drift 与 bundle/release manifest 校验结果，形成 AI harness 可消费的结构化结果。
  _需求追溯: R1.AC3, R3.AC4, R6.AC1, R6.AC2, R6.AC3, R6.AC4, R8.AC4, R9.AC1, R9.AC2, R9.AC3_

- [x] 6. 增加运行时能力门控并保持菜单消费链稳定
  - 新增 `CapabilityGateService`，基于 `sys_config` 中的 `capability.<module>.enabled` 控制运行时模块是否对外生效。
  - 在模块级接口接入 gate 检查，确保“代码保留但模块禁用”时 API 不可调用。
  - 保持 `/getRouters` 与前端动态路由消费方式不变，只通过数据库最终状态与 gate 收敛实现页面不展示。
  - 为运行时 gate 增加集成测试，覆盖菜单不返回、接口禁用、配置缺失默认禁用等场景。
  _需求追溯: R2.AC3, R5.AC2, R5.AC3, R5.AC4, R6.AC3_

- [x] 7. 演进 `menu.py` 与声明迁移工具链
  - 让 `menu.py add/remove/check` 只支持新模块声明，并增加 `--module` 入口。
  - 提供从中心化 `menus.registry.yaml` 与 `base/*.yaml` 向 `*.module.yaml` 的导出/迁移工具，要求冲突即失败、双写即失败。
  - 将脚手架继续保持为最低心智入口，自动维护 `menu_id`，避免把对象级概念重新暴露给开发者。
  - 更新脚本说明和迁移文档，说明模块声明、单一 `release-plan` 和现有 `db.py` 的协作方式。
  _需求追溯: R1.AC4, R2.AC1, R2.AC2, R8.AC2, R8.AC3_

- [x] 8. 完成端到端验证、回归与性能守护
  - 为 capability 编译、模块级发布选择、`dev-sync` 后置校验、`finalize/deploy`、运行时 gate 分别补齐单元与集成测试。
  - 增加迁移回归用例，证明模块声明是唯一正式入口，旧声明残留会被阻断。
  - 增加性能与 no-op 回归，确保 `dev-sync` 无差异时耗时接近当前实现，`deploy` 无 bundle 时保持 no-op 幂等。
  - 更新 `status --format json` / `verify --ci` 的稳定输出契约，作为 AI harness 和后续自动化的基线。
  _需求追溯: R4.AC3, R6.AC4, R8.AC4, R9.AC1, R9.AC2, R9.AC3_

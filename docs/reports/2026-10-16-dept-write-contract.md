# 部门 HTTP 写入契约与层级边界

本轮完成部门新增、编辑的输入隔离、写字段白名单及层级校验。范围仅限部门写入及其真实调用；ZXUI 源码未改动。

## 契约与业务行为

- 新增使用 `DeptCreateModel`，必需 `parentId/deptName/orderNum`；编辑使用 `DeptUpdateModel`，`deptId` 必须为正整数。未知字段、客户端 ID（新增）、删除标记、祖级及创建/更新审计字段均返回原有 Problem Details 422。
- 可写业务字段仅限父部门、名称、排序、负责人、电话、邮箱和状态。编辑字段未提供则保留；联系人字段允许 null/空字符串清空。结构字段及状态不接受显式 null。审计信息由认证身份生成，祖级由服务端计算。
- 目标或真实父部门不存在返回 404；目标、新父或实际将被启用的祖先不在数据范围内返回 403；自指、父链成环及停用规则失败返回 422。沿真实 `parent_id` 链检查环，不信任客户端或缓存的祖级。
- `parentId=0` 为虚拟根。已有根部门可正常编辑；管理员可新增或迁入根部门，受限用户不能借虚拟根绕过数据权限。旧父未变时，普通编辑无需额外取得旧父权限。
- 正常换父在原有事务中更新目标及整棵子树。正常部门省略状态换父与完整表单行为一致；启用仍恢复祖先状态，但先校验实际停用祖先的权限。正常祖先不重复写入，避免误改其更新时间。
- 保留“停用父下不能新增”“有正常后代不能停用”的语义。前端仍使用现有 `useEditorRead/useFormDialog` 和统一反馈，只显式提交该操作字段。

## 必要修复与方案依据

真实子树换父暴露已有 SQLAlchemy 批量更新绑定名冲突，导致 500。已在部门 Repository 内改为 Core executemany 和独立绑定名，并补真实 SQL 回归；没有引入新基础设施。该用法依据 [SQLAlchemy 批量更新说明](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#disabling-bulk-orm-update-by-primary-key-for-an-update-statement-with-multiple-parameter-sets)。

输入模型、异常及局部更新复用本项目用户/角色已有实现；未提供字段的处理遵循 [FastAPI/Pydantic exclude_unset](https://fastapi.tiangolo.com/tutorial/body-updates/#using-pydantics-exclude_unset-parameter)。子树祖级更新和启用祖先沿用 [RuoYi 部门服务](https://github.com/yangzongzhuan/RuoYi-Vue/blob/master/ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDeptServiceImpl.java) 的业务规则，补齐权限预检。代价是换父时按层级深度读取父链；未新增缓存、调度或兼容双轨。

## 验证证据

[验证汇总](evidence/2026-10-16-dept-write-contract/verification.json)、[真实业务结果](evidence/2026-10-16-dept-write-contract/actual.json)：

- 后端聚焦 124 项通过，覆盖原部门服务、详情契约、命令、HTTP 输入及 SQL 更新。回归先红后绿。
- 前端聚焦 240 项通过；全局 `lint:check`、`type-check` 和 ZXUI 源码直连生产构建通过。
- 38 项真实业务检查通过：生产 DeptDlg 的 setup/确认、实际 API/统一反馈、源码 ZXUI hook/HTTP、Axios XHR、FastAPI、本地 MySQL。覆盖新增/编辑污染字段、身份缺失、根部门、子树换父、停启用、空联系人、受限账号、祖先启用越权和正常祖先审计字段不变。
- 错误返回保持 Problem Details、请求上下文和单次反馈；403/422 不触发重新登录。临时部门、角色及用户已清理，原有用户/角色/岗位/部门列表及总数与验证前完全一致。
- OpenAPI 只改变部门 POST/PUT 及两个输入 schema；17 个生成文件/契约文件重复生成哈希一致。独立复核的两项问题已修复，最终无阻塞发现。
- 新 Python 文件 Ruff/格式检查通过；既有文件 Ruff 诊断无新增。后端约定脚本通过；前端约定脚本仍被本轮未改动的 `VersionList.vue` 既有 console 使用阻挡，独立全局 lint/type 检查通过。

未使用 computer use，未渲染真实浏览器、原生表单校验或视觉界面；上述真实业务验证不代表视觉验收。完整全仓测试未运行。构建保留既有大 chunk 提示。

## 工作区边界

按本轮起点逐文件比较：3533 个业务文件中仅 15 个本轮已有文件发生变化；7938 个 ZXUI 文件无变化；无基线文件丢失，HEAD 和暂存区保持原样。本轮新增 DTO、三份聚焦测试、计划及本报告/证据。未创建提交或发布；验证专用后端进程已停止，原有服务未动。

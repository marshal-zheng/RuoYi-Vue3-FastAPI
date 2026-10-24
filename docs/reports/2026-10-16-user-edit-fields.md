# 用户编辑可选字段与关联更新修复

本轮已完成，未提交 Git、未发布。生产代码只修改后端 `edit_user_services` 和业务 `UserFormDialog` 的编辑提交分支，没有修改 ZXUI、HTTP、认证、权限、数据库结构或 API 类型。

## 契约与根因

核对了实际表单、`updateUser`、生成的 `EditUserModel` 类型、后端 VO、控制器、命令 handler、服务及关联仓储。

| 字段 | 当前职责与本轮处理 |
| --- | --- |
| `role` | 可选的角色展示数据，不用于写入角色关联，也不应要求编辑表单补传 |
| `roleIds` / `postIds` | 独立控制角色/岗位关联：未传保留，非空数组替换，`[]` 或显式 `null` 清空 |
| 普通可选标量字段 | 沿用 `exclude_unset=True`；未传保留，显式传值按原契约更新 |
| 表单 `password` | 用户弹框中仅供新增使用；编辑提交从 payload 副本中移除，不修改表单原数据，新增仍提交密码 |
| `type` / `admin` | 操作标记和派生字段，不写入用户记录 |

后端先使用 `model_dump(exclude_unset=True)` 排除未提供字段，随后却无条件 `del role/role_ids/post_ids`。真实表单没有 `role`，因此报 KeyError；其他关联字段未传也会触发同类异常。仅改成安全 `pop` 仍不足以解决问题：若继续无条件删除关联，会将缺省字段误当成清空指令。

修复从序列化入口排除展示、关联和操作字段，再使用 Pydantic 既有 `model_fields_set` 分别判断关联更新意图。`status/avatar/pwd` 分支继续不修改角色、岗位，原事务和权限检查保留。没有新增字段状态框架或重复查询机制。取舍依据参照 [FastAPI 的部分更新说明](https://fastapi.tiangolo.com/tutorial/body-updates/#using-pydantics-exclude_unset-parameter)和 [Pydantic 字段提供状态](https://docs.pydantic.dev/latest/concepts/serialization/#excluding-and-including-fields-based-on-their-value)，沿用现有 PUT 入口与模型形状。

核对完整弹框状态时还确认，业务 `useFormDialog → ZXUI useDialog.open` 会合并默认数据，编辑状态中因此带有创建专用的 `password: ''`。后端不接受空密码，且普通资料编辑不应改密码。编辑分支现在复制 payload 并删除该字段，保留新增分支和专用密码更新路径。组件库默认值合并行为符合现有契约，无需改库。

## 回归与检查

在两个既有测试文件中补必要回归，没有新增测试目录或基础设施：

- 后端新增 9 项，使用真实 SQLite、UserService 及用户/角色/岗位仓储：普通表单缺少 `role`、缺省关联保留、单独替换角色/岗位、空数组与 null 清空、状态/头像/密码更新保留关联。原实现先出现 4 项预期 KeyError，随后服务文件 13 项通过。
- 前端新增 3 项，实际挂载弹框与 useDialog：正常/停用编辑均不发送默认空密码，创建仍保留密码。先观察两项密码字段断言失败，再修复通过。

| 检查 | 结果 |
| --- | --- |
| 后端定向回归 | 8 文件、51 项通过 |
| 前端定向回归 | 4 文件、18 项通过 |
| 前端全量 ESLint / type-check | 通过 |
| ZXUI 源码直连生产构建 | 通过，27.01 秒；存在既有构建提示，未扩展修复 |
| 修改测试 Ruff / 格式检查、后端 Python 编译 | 通过 |
| 修改后端文件静态诊断对比 | 原 34 项、现 29 项，没有新增诊断；既有格式问题仍在 |
| 两仓库差异空白检查 | 通过 |
| 独立只读审查 | 无阻塞，另跑后端 15 项、前端弹框 4 项通过 |

changed 规范脚本没有整体通过：后端全工作区目标仍有 233 项 Ruff 诊断及 3 个文件格式问题，前端仍被既有 `VersionList.vue` console 检查阻挡；其余 guardrails 通过。未改这些范围外文件，没有全文件格式化后端服务。前端全量 ESLint/type-check 已单独通过。

## 真实业务验证

使用 Vue SFC 编译后的完整 `UserFormDialog.setup`、业务 `useFormDialog`、ZXUI 源码 `useDialog`、实际 API 和源码 `@zxio/http`，通过 JSDOM XMLHttpRequest 访问真实本地 FastAPI/MySQL。覆盖默认值合并、编辑 payload、confirm loading 和 success；没有只提取孤立的提交函数。

正常用户、停用用户各完成下列 6 组，保存及回读均成功：

1. 打开实际编辑状态，确认含默认空密码且不含 `role`，修改昵称后保存；请求不带密码和展示字段，角色/岗位保留，loading 释放、success 一次。
2. 关联字段均未传，原角色/岗位保持；`email:null` 清空邮箱，未传的备注保留。
3. 只提交角色：空数组清空、非空数组重新关联，岗位不变。
4. 只提交岗位：替换为另一个现有岗位、空数组清空，角色不变。
5. 显式 `roleIds:null/postIds:null/role:null`，角色和岗位清空，不报 KeyError。
6. 通过实际弹框重新分配角色/岗位，保存后再次打开，回显与持久化结果一致，启停状态保持。

另验证正常用户编辑后仍能用原密码登录并获取当前用户，停用用户仍返回 401/“用户已停用”。总计 13 组通过。

仅创建两个专用标记的临时用户，复用既有普通角色、部门和岗位；验证后经业务 API 软删除，并查询确认可见遗留为 0，探针会话已退出。既有角色/部门/岗位没有变更，正常软删除与审计历史保留。探针初次加载时补齐目录 index 解析，并将测试邮箱从不被现有校验接受的 `.test` 域改为 `example.com`；未因此改变生产实现。

未使用 computer use、浏览器点击或视觉验收；没有渲染 FormGrid，也没有执行原生表单验证，不能据此声称浏览器端到端验收。仅停止本轮启动的后端及子进程，保留原有 Docker/Redis。任务开始时已有的 484 个业务文件、141 个 ZXUI 文件按 hash 核对保持不变。

证据：[真实结果](evidence/2026-10-16-user-edit-fields/actual.json)、[检查命令](evidence/2026-10-16-user-edit-fields/checks.json)、[静态对比](evidence/2026-10-16-user-edit-fields/static-comparison.json)、[基线保留](evidence/2026-10-16-user-edit-fields/baseline-preservation.json)。

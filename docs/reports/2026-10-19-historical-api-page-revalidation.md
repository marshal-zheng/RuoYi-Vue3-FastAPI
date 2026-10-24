# RuoYi 历史证据 41 项复验结果

原报告仅有历史证据的 **41 个 API 操作已全部重新执行**：39 项补齐对应真实页面流程；2 项协议备用入口没有页面调用，采用真实认证 API 验证。发现并修复 4 个问题。保留已有改动，本轮未执行提交或推送。

后续跟进：用户“分配角色”偶发 404 已复现，确认是开发模式 Router 实例分叉并完成修复，见 [根因与修复报告](2026-10-19-user-role-route-404.md)。本报告保留当时的观察与结论。

## 范围与结果

沿用当前本地 MySQL、Redis、后端 8088、前端 80，前端使用 `VITE_ZXUI_LOCAL=true` 直连 `/Users/hqz/Downloads/element-plus`。使用独立账号、角色、协议及临时菜单，未改业务既有资料或仿真流程。

| 169 项目录的证据分类 | 数量 |
| --- | ---: |
| 上轮真实请求证据 | 93 |
| 前次补验真实请求证据 | 28 |
| 前次隔离存储集成验证 | 7 |
| 本次重跑原历史项 | 41 |
| 仍仅有历史证据 | 0 |

[完整覆盖矩阵](evidence/2026-10-19-historical-api-page-revalidation/coverage.json)、[本轮逐项索引](evidence/2026-10-19-historical-api-page-revalidation/revalidated-operations.json)、[浏览器请求清单](evidence/2026-10-19-historical-api-page-revalidation/browser-receipts.json)。这是实际操作证据，不代表穷尽所有业务、权限或失败分支；前次隔离验证、dry run、禁止覆盖文件等边界不变。

## 修复与根因

| 问题 | 根因、处理与复验 |
| --- | --- |
| 自定数据权限越界 | 部门树把半选祖先与全选节点一起提交。仅勾选研发 103 时，100、101 也进入角色部门关联；受限账号因此可读到部门 100 的用户。只提交 `getCheckedKeys()`，菜单权限祖先逻辑不变。真实树回归确认半选 `[100,101]` 不进入授权；真实 MySQL/Redis 账号复验范围外用户从 1 条变为 0 条，范围内仍为 1 条。保存后部门集合为 `[103]`。 |
| 协议导入弹框被抽屉遮挡 | Dialog 使用独立计数器，父 Drawer/Select 使用 Element Plus 计数器，实测子弹框 2000 低于父抽屉 2016。Dialog 复用 Element Plus `useZIndex`，保留显式层级覆盖；没有业务硬编码层级。真实页面父 2006、子 2009，模板下载、文件选择及确认可正常点击；真实组件回归覆盖 Drawer→Dialog 顺序。 |
| 损坏协议 Excel 返回 500 | 预览入口已有部分输入校验，但共享工作簿/JSON 解析及单文件导入仍抛默认 500 的旧 `ServiceException`。将这些已知文件输入失败统一为现有 `ValidationException`，内部解析信息留给开发日志。损坏预览和单文件导入均实测 422，页面保留导入框并显示可读提示；有效工作簿/JSON 仍通过。批量有效+损坏文件返回 200 的逐项结果：1 成功、1 失败，页面显示“部分完成”，失败项无落库。 |
| 个人资料窄栏横向溢出 | 左栏仍依赖缺少样式的旧列表类，长邮箱撑出卡片滚动条。改成语义化资料列表并允许长值换行；初始角色/岗位值用空字符串，空岗位不再留下分隔符。长邮箱账号在 1100×800 与 1440×1000 真实页面复验；列表及各值 `scrollWidth == clientWidth`，整页横向宽度 1100/1100。 |

关键证据：[权限修复前](evidence/2026-10-19-historical-api-page-revalidation/scope-boundary-before.json)、[修复后范围正反例](evidence/2026-10-19-historical-api-page-revalidation/scope-boundary-after.json)、[部门读回](evidence/2026-10-19-historical-api-page-revalidation/role-data-scope-after.json)、[协议损坏文件 422](evidence/2026-10-19-historical-api-page-revalidation/protocol-corrupt-preview-after.json)、[批量部分完成](evidence/2026-10-19-historical-api-page-revalidation/protocol-batch-page-feedback.json)、[个人资料布局](evidence/2026-10-19-historical-api-page-revalidation/profile-layout-page-after.json)。

方案依据：[Element Plus Tree 的全选与半选 API](https://element-plus.org/en-US/component/tree.html)、[Element Plus 共享层级实现](https://github.com/element-plus/element-plus/blob/dev/packages/hooks/use-z-index/index.ts)。归因同时核对了本地安装版本、实际调用和真实请求。

## 页面验收

- 用户：新增必填阻断、详情读取、编辑取消重开/保存、停启、重置密码后独立登录；模板/筛选导出读取真实工作簿；导入 2 条成功+1 条无效部门失败，失败账号不存在；单项及批量删除、授权关联归零。
- 个人资料：基本信息保存读回、头像裁剪上传后真实图片加载、修改密码后退出并以新密码登录；资料及协议编辑器检查两种视口。
- 角色：新增菜单授权、编辑取消重开、状态/导出、自定义数据权限；角色侧添加用户、单项/批量撤销；用户侧分配角色及清空角色。删除用户后角色已分配列表为 0，再删除角色。
- 协议：RS422 新增/读取/编辑，配置预览/模板下载、导出/回导、批量部分失败及提示、单行删除取消/确认和批量删除。导出工作簿逐单元格核对温度字段、2 字节、字节序号、℃、UINT16、比例尺及备注；单文件 `/import`、直接 `DELETE` 是无页面消费者的备用 API，未冒充页面按钮执行。

一次用户“分配角色”导航曾显示 404。未改路由源码；完整重载后连续 3 次从真实按钮进入、一次直接刷新均正常，GET/PUT 授权及清空通过，浏览器未记录未处理页面异常。该次现象未稳定复现，**根因未确认，也不声称已修复**。[导航复验记录](evidence/2026-10-19-historical-api-page-revalidation/authorization-route-repeat.json)。尝试改临时菜单名称未在等待窗口内观察到热更新事件，不计为热更新验收。

## 验证与清理

- 后端 **43 项通过**：现有角色/协议服务及新增真实文件解析回归。新增文件 Ruff/格式检查通过；原协议服务 Ruff 为 90→90，无新增诊断。
- 业务前端 **27 项通过**：真实部门树、角色表单、双向授权；完整及严格 TypeScript 检查、受影响 ESLint 通过。
- ZXUI **70 项通过 / 7 文件**：Dialog、混合弹层及主题 Portal 集成；web TypeScript 和受影响 ESLint 通过。
- 本轮原 4 个账号及 2 个布局复验账号（134–139）、角色 94、协议 15–19、菜单 1079 活动记录归零；用户角色/角色部门/角色菜单关联归零；头像文件精确删除，已知会话及 CSRF 状态清理。保留正常登录/操作/审计轨迹，未清共享日志。
- 开始时记录 1955 份文件摘要，无原文件缺失；本轮只修改 5 个已有源码/测试文件并新增 2 个测试文件。另有并行出现的看板/包清单变化，原样保留，不归因本轮。开始/结束 HEAD 有变化，来自并行工作的新提交（RuoYi 的岗位 Schema 表单、ZXUI 的 SchemaForm 交付记录等）；本轮未执行提交或推送，也未回退这些提交。

[后端测试](evidence/2026-10-19-historical-api-page-revalidation/backend-tests.log)、[业务前端测试](evidence/2026-10-19-historical-api-page-revalidation/frontend-tests.log)、[ZXUI 测试](evidence/2026-10-19-historical-api-page-revalidation/zxui-tests.log)、[数据库及会话清理](evidence/2026-10-19-historical-api-page-revalidation/cleanup-storage.json)、[最终账号清理](evidence/2026-10-19-historical-api-page-revalidation/cleanup-final.json)、[源码保留核对](evidence/2026-10-19-historical-api-page-revalidation/preservation.json)。

## 41 项对应证据

| # | API 操作 | 执行面 | 当前动作/断言 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | `PUT /system/user` | 真实页面 | 用户编辑保存并读回 | [user-edit.json](evidence/2026-10-19-historical-api-page-revalidation/user-edit.json) |
| 2 | `POST /system/user` | 真实页面 | 用户新增并读回 | [user-create.json](evidence/2026-10-19-historical-api-page-revalidation/user-create.json) |
| 3 | `DELETE /system/user/{user_ids}` | 真实页面 | 单项及批量删除 | [user-delete.json](evidence/2026-10-19-historical-api-page-revalidation/user-delete.json) |
| 4 | `PUT /system/user/resetPwd` | 真实页面 | 重置密码后独立登录 | [user-reset-password.json](evidence/2026-10-19-historical-api-page-revalidation/user-reset-password.json) |
| 5 | `PUT /system/user/changeStatus` | 真实页面 | 停用及启用 | [user-status.json](evidence/2026-10-19-historical-api-page-revalidation/user-status.json) |
| 6 | `GET /system/user/profile` | 真实页面 | 打开个人中心 | [profile-final-page.json](evidence/2026-10-19-historical-api-page-revalidation/profile-final-page.json) |
| 7 | `PUT /system/user/profile` | 真实页面 | 修改昵称/手机/邮箱 | [profile-update.json](evidence/2026-10-19-historical-api-page-revalidation/profile-update.json) |
| 8 | `GET /system/user/` | 真实页面 | 打开新增用户读取选项 | [user-create.json](evidence/2026-10-19-historical-api-page-revalidation/user-create.json) |
| 9 | `GET /system/user/{user_id}` | 真实页面 | 打开编辑读取详情 | [user-edit.json](evidence/2026-10-19-historical-api-page-revalidation/user-edit.json) |
| 10 | `POST /system/user/profile/avatar` | 真实页面 | 裁剪上传头像并确认图片加载 | [avatar-upload.json](evidence/2026-10-19-historical-api-page-revalidation/avatar-upload.json) |
| 11 | `PUT /system/user/profile/updatePwd` | 真实页面 | 修改密码、退出后新密码登录 | [profile-password.json](evidence/2026-10-19-historical-api-page-revalidation/profile-password.json) |
| 12 | `POST /system/user/importData` | 真实页面 | 下载模板填入两条有效和一条无效部门数据后导入 | [user-import.json](evidence/2026-10-19-historical-api-page-revalidation/user-import.json) |
| 13 | `POST /system/user/importTemplate` | 真实页面 | 用户导入弹框下载模板 | [user-template.xlsx](evidence/2026-10-19-historical-api-page-revalidation/user-template.xlsx) |
| 14 | `POST /system/user/export` | 真实页面 | 用户列表按名称筛选导出 | [user-export.xlsx](evidence/2026-10-19-historical-api-page-revalidation/user-export.xlsx) |
| 15 | `GET /system/user/authRole/{user_id}` | 真实页面 | 用户页进入角色授权 | [user-assign-role.json](evidence/2026-10-19-historical-api-page-revalidation/user-assign-role.json) |
| 16 | `PUT /system/user/authRole` | 真实页面 | 角色勾选保存及清空保存 | [user-clear-roles.json](evidence/2026-10-19-historical-api-page-revalidation/user-clear-roles.json) |
| 17 | `GET /system/role/deptTree/{role_id}` | 真实页面 | 打开数据权限树并保存后重读 | [role-data-scope-after.json](evidence/2026-10-19-historical-api-page-revalidation/role-data-scope-after.json) |
| 18 | `GET /system/role/list` | 真实页面 | 角色列表/筛选 | [role-create.json](evidence/2026-10-19-historical-api-page-revalidation/role-create.json) |
| 19 | `PUT /system/role` | 真实页面 | 角色修改、取消重开、保存 | [role-edit.json](evidence/2026-10-19-historical-api-page-revalidation/role-edit.json) |
| 20 | `POST /system/role` | 真实页面 | 新增角色并配置菜单 | [role-create.json](evidence/2026-10-19-historical-api-page-revalidation/role-create.json) |
| 21 | `PUT /system/role/dataScope` | 真实页面 | 只勾选研发部门并验证受限账号边界 | [role-data-scope-after.json](evidence/2026-10-19-historical-api-page-revalidation/role-data-scope-after.json) |
| 22 | `DELETE /system/role/{role_ids}` | 真实页面 | 删除验收角色并读列表 | [role-delete.json](evidence/2026-10-19-historical-api-page-revalidation/role-delete.json) |
| 23 | `GET /system/role/{role_id}` | 真实页面 | 角色编辑详情读取 | [role-edit.json](evidence/2026-10-19-historical-api-page-revalidation/role-edit.json) |
| 24 | `POST /system/role/export` | 真实页面 | 角色筛选后导出 | [role-export.xlsx](evidence/2026-10-19-historical-api-page-revalidation/role-export.xlsx) |
| 25 | `PUT /system/role/changeStatus` | 真实页面 | 角色停用及启用 | [role-status.json](evidence/2026-10-19-historical-api-page-revalidation/role-status.json) |
| 26 | `GET /system/role/authUser/allocatedList` | 真实页面 | 角色分配用户列表 | [role-after-user-delete.json](evidence/2026-10-19-historical-api-page-revalidation/role-after-user-delete.json) |
| 27 | `GET /system/role/authUser/unallocatedList` | 真实页面 | 添加用户对话框查询未分配用户 | [role-grant-users.json](evidence/2026-10-19-historical-api-page-revalidation/role-grant-users.json) |
| 28 | `PUT /system/role/authUser/selectAll` | 真实页面 | 勾选三位自有用户并授权 | [role-grant-users.json](evidence/2026-10-19-historical-api-page-revalidation/role-grant-users.json) |
| 29 | `PUT /system/role/authUser/cancel` | 真实页面 | 单项取消授权 | [role-revoke-users.json](evidence/2026-10-19-historical-api-page-revalidation/role-revoke-users.json) |
| 30 | `PUT /system/role/authUser/cancelAll` | 真实页面 | 批量取消授权 | [role-revoke-users.json](evidence/2026-10-19-historical-api-page-revalidation/role-revoke-users.json) |
| 31 | `GET /system/protocol/list` | 真实页面 | 协议列表及名称筛选 | [owned-protocols.json](evidence/2026-10-19-historical-api-page-revalidation/owned-protocols.json) |
| 32 | `PUT /system/protocol` | 真实页面 | 协议编辑取消重开及保存 | [protocol-edit.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-edit.json) |
| 33 | `POST /system/protocol` | 真实页面 | 新建 RS422 协议并导入字段配置 | [protocol-create.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-create.json) |
| 34 | `DELETE /system/protocol/{protocol_ids}` | API 直验 | 直接 DELETE 备用入口，无页面调用 | [protocol-direct-delete.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-direct-delete.json) |
| 35 | `POST /system/protocol/deleteBatch` | 真实页面 | 页面单项及批量删除均调用 deleteBatch | [protocol-page-batch-delete.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-page-batch-delete.json) |
| 36 | `GET /system/protocol/importTemplate` | 真实页面 | 协议配置导入弹框下载模板 | [protocol-template.xlsx](evidence/2026-10-19-historical-api-page-revalidation/protocol-template.xlsx) |
| 37 | `POST /system/protocol/importPreview` | 真实页面 | 有效文件预览与损坏文件 422 反馈 | [protocol-corrupt-preview-after.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-corrupt-preview-after.json) |
| 38 | `POST /system/protocol/export` | 真实页面 | 导出后逐单元格读取并回导 | [protocol-export.xlsx](evidence/2026-10-19-historical-api-page-revalidation/protocol-export.xlsx) |
| 39 | `POST /system/protocol/import` | API 直验 | 直接 multipart 单文件导入，无页面调用 | [protocol-single-import.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-single-import.json) |
| 40 | `POST /system/protocol/importBatch` | 真实页面 | 页面上传两份文件，1 成功/1 失败且有可见通知 | [protocol-batch-page-feedback.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-batch-page-feedback.json) |
| 41 | `GET /system/protocol/{protocol_id}` | 真实页面 | 打开协议编辑读取详情 | [protocol-edit.json](evidence/2026-10-19-historical-api-page-revalidation/protocol-edit.json) |

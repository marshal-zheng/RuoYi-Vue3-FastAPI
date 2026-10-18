# 角色管理与双向授权整体审计：首轮 FAIL

**BASE_SHA:** `991631e1b7947642612e023ca154c26a4c75d68f`。本次重新读取干净最新 std 对应项目工作树并执行独立探针；不是复述历史报告，也没有把实际源 dirty 后端当成已交付实现。已读文件和 HEAD SHA256 保留于 `independent-round1-reviewed.json`。

**P0=0 / P1=0 / P2=1。当前不能判阶段完整收尾。** 该 P2 为普通角色四个写入操作的已公开 typed DTO 与 runtime 整体失配，已实际复现八种症状；需要当前授权范围内修复、再独立复验。未据此要求迁入普通 user/dept/profile 的全部未提交改动。

## P2：角色四写端仍使用旧 AddRoleModel，违反已提交 typed API 的字段与关系缺省契约

已提交 `src/api/system/role.ts` 和 `src/queries/system/role.ts` 分别消费 RoleCreateModel、RoleUpdateModel、RoleStatusUpdateModel、RoleDataScopeUpdateModel。`_generated/types.gen.ts` 声明 partial update、菜单/部门数组 null 清空与省略保留、必需状态及数据范围 1-5。然而干净 HEAD 四个 controller 都使用 AddRoleModel；shared/openapi.json 也仍 ref AddRoleModel，甚至不存在四个新 schema。前端生成类型与实际 schema/runtime 不一致。源工作区另有未提交 role_write_vo/白名单/关系缺省修正，不能当作干净 HEAD 已具备。

真实 FastAPI 路由、生产 provide_system_mediator/handler/service/repository 与 SQLite 内存库独立复现：

| 操作/请求 | 声明契约预期 | 干净 HEAD 实际 |
| --- | --- | --- |
| PUT role `{roleId,remark}`，省略 menuIds | 更新备注并保留菜单 | 500，edit_role_services 的 `del edit_role['menu_ids']` KeyError |
| POST role，合法基本字段 + `menuIds:null` | 201，空菜单 | 422 list_type |
| PUT role `{roleId,remark,menuIds:null}` | 200，清空菜单 | 422 list_type |
| PUT dataScope `{roleId,dataScope:'2',deptIds:null}` | 200，清空部门 | 422 list_type |
| PUT dataScope `{roleId,dataScope:'2'}`，已有部门 201 | 200，省略保留已有部门 | 200，却删除已有部门关联，结果 `[]` |
| PUT role `{roleId,roleName:null,menuIds:[]}` | 422，不向非空列写 null | 500 |
| PUT changeStatus `{roleId}`，缺状态 | 422 | 500 |
| PUT dataScope `{roleId,dataScope:'9',deptIds:[]}` | 422，非法数据范围 | 200，并将 dataScope 写为 9 |

这不是只以静态字段名猜缺陷；有效 typed payload 的错误响应/静默关系删除和非法输入的错误持久化均已实际执行。当前 Drawer 总发送完整 menuIds/deptIds，故不能把这些 API 契约缺口误称为当前正常 UI 保存全部失败。反过来，UI 主流程通过也不能证明公开 partial/null/校验契约正确。

## 主流程独立 GREEN（与失败分开）

对 RoleFormDrawer 实际 onConfirm 字段执行默认 `roleSort=0` 创建，以及完整编辑菜单、五种数据范围往返（自定义部门保存、切离清空）、状态停用/恢复、停用详情可读、菜单/数据范围不被状态写损坏、已分配角色禁止删除、解除关联后删除和删除后 404：**2 passed**。

测试保留真实生产 mediator 注册/命令 pipeline、RoleService 和 SQLite 仓储；只有身份/接口权限/数据范围依赖与不使用的其他领域 service 采用替身。没有 HTTP 外部服务器/真实数据库。此 GREEN 表明现有全量 UI payload 无需普通源 dirty 写规则也能完成这些正常流程，不代表所有角色 API 契约已覆盖。

初次探索探针 1 pass/2 fail 中有一项是共享 SQLite 测试命名碰撞，已只在 meta 探针内使用独立名称修正；另一项 partial edit 500 为真实缺陷。稳定日志为 `independent-role-crud-probe.log`（2 pass/1 fail），七项补充矩阵为 `independent-role-dto-probe.log`（7 fail）；正向单独日志为 `independent-role-mainflow-green.log`（2 pass）。完整命令、退出码和日志 SHA 在各同名 JSON。初始探针源码仍保留 `.initial.py`，不将操作错误归为产品问题。

## 其他实际读取与验证边界

本轮重新读取角色列表、表单/数据范围抽屉、查询资源、返回状态 store、角色已授权列表/选择用户/用户角色授权组件，以及双向授权 service 和读取投影。角色列表稳定 row-key、按已提交筛选与页码查询；编辑树采用本次打开草稿；授权使用完整角色快照和独立跨页选择、写目标捕获、会话/重开代际隔离；两向投影含 createTime。这些静态读取未发现新的独立 P0/P1/P2。

8cc5912 已提交的 JSON 授权 DTO→command/handler/DI→UserRoleService→repository 链当前存在，不再是上一轮依靠 dirty 才工作的四个授权写端；本轮尚未重复整个授权测试集合，主代理会鲜跑完整相关后端、前端 122/类型/lint/UI及双消费构建。本首轮不把历史 99 项等算成本轮新测试。

未做新浏览器/视觉验收、真实 MySQL/Redis、并发部署或手机端验证；本代理没有登录、启服务、改 source/工作树产品、提交或清理无关 dirty。已将具体缺陷及时交主代理，接下来暂停产品相关执行，等待修复候选就绪再独立复核。旧缓存兼容与其他 ordinary user/dept/profile 改动不属于这个发现所需的修复范围。

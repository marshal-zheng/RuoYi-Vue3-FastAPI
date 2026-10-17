# 角色授权阶段最终独立复核：首轮 FAIL

审查基线：`std@7b6fbd0ab8f1b9475e6401a3dc10362f926c32a4`，以及源工作区三个测试文件差量。结论：**P0=0、P1=1、P2=0；暂不能宣布干净 std 完整交付/阶段收尾。**

本报告保留首轮阻断发现。原 `independent-review.md` 为尚未识别完整交付依赖时的初稿，其“可收尾”结论已由本报告推翻，不能作最终 PASS 依据；三个测试差量的局部审查结论仍有效。历史原始日志与证据不覆盖、不改写。

## P1：已提交前端 JSON 授权写入依赖未交付后端

### 复核证据

使用 `git show HEAD:<path>` 读取干净提交，不以当前 dirty 工作区内容替代 HEAD：

- `ruoyi-fastapi-frontend/src/api/system/user.ts` 的 `updateAuthRole` 发送 JSON `UserRolesAssignModel`，包含 `userId` 和 `roleIds` 数组；`src/api/system/role.ts` 的增量授权/批量撤销发送 JSON `roleId` 和 `userIds` 数组。
- 已提交 `src/api/role-authorization-contract.test.ts` 明确断言这些写调用使用 `data` 且不含 `params`。`src/utils/request.ts` 将 `data` 原样交给 `http.put`，不存在自动转 Query 的适配层。
- `HEAD:ruoyi-fastapi-backend/modules/system/api/user_controller.py` 的 `PUT /system/user/authRole` 仍要求 `user_id: int = Query(alias='userId')`、`role_ids: str = Query(alias='roleIds')`；相同前端请求缺少必填 Query，在依赖校验阶段即会 422，不能进入授权写业务。
- `HEAD:modules/system/api/role_controller.py` 的 `selectAll`、`cancelAll` 仍使用 `Depends(CrudUserRoleModel.as_query)`，不消费该 JSON 授权数组；`cancel` 虽使用 body，但仍是旧宽松 DTO。
- `HEAD:module_admin/entity/vo/user_vo.py` 的 `CrudUserRoleModel` 使用可空字符串 `user_ids`/`role_ids`。`AssignUserRolesCommand`、`AddRoleUserCommand`、`CancelRoleUserCommand` 及其 handler 仍是旧 DTO 和 `UserService` 路径。新的 JSON DTO、关联业务服务和关联 command/handler/DI 是工作区已有但未完整提交的依赖；`modules/system/application/services/user_role_service.py` 不在 HEAD 的受跟踪文件中。

因此只改 controller 签名不足，必须把 JSON DTO→commands/handlers→关联 service→DI 及必要契约回归作为一致的依赖链交付，并在干净候选里验证。没有证据支持恢复 Query 兼容层来掩盖这个差异。

### 影响与结论边界

角色管理和双向授权是本阶段明确业务目标；干净 std 无法完成已提交前端的授权写路径，这是交付功能阻断而非纯文档问题。此前浏览器验收、实际源后端 210 项等均运行于带原 dirty 的工作区，能证明当时实际源业务正确，不能证明干净提交无需这些写端依赖。

五个源 dirty 文件匹配此前 source-candidate，证明了保留正确，不证明这些文件的未交付部分可以从完整业务运行中缺省。六提交 ancestry、截图 hash、链接、资源清理和独立复审均有各自证明力，不能替代干净提交的契约一致性。原严格 delivery-status 的 dirty 限制保持历史真实状态，也不能作为本次实际接口失配的豁免。

主代理后续已报告：在新项目本地隔离工作树使用真实 TestClient，5 项 RED 均复现失败；用户授权 422，selectAll/cancelAll 204 但 payload 字段全 None，单撤销旧宽松 DTO。该 RED 是主代理/实现代理证据，本审查代理未独立重跑，不计为独立测试结果。后续候选完成后应另起第二轮独立复审，保留本轮 FAIL。

## 三个测试差量：独立通过

- `tests/list-export-query-parity.test.ts`：按现有 ESLint 内嵌 Prettier 规则排版。独立 TypeScript AST 比较 HEAD/工作区，忽略位置与原始引号格式后相等；列表/导出一致性、字段清空、排序和分页断言不变。
- `tests/role-query-list.test.ts`、`tests/user-query-export.test.ts`：以明确 state 结构替代 `Record<string, any>`；角色 modal 补齐真实类型要求的未用方法替身，保留原 confirm mock。未复制业务算法、放宽断言或跳过测试。
- 独立运行三个文件：3 suite / **19 passed**；三文件 ESLint：exit 0、零诊断；范围内 `git diff --check` 通过。
- 本代理读取 `index-before.z` 时一度误将 `git ls-files --stage -z` 快照与 `git diff --cached --raw -z` 比较，临时审计 JSON 产生 false。重新按相同 `git ls-files --stage -z` 格式比较为 **true**，当前索引无暂存改动。该工具格式误配不是源索引改变；本轮仅此报告授权写入，未改初稿 JSON。

局部独立证据保留在本目录 `independent-three-tests.{json,log}`、`independent-three-eslint.{json,log}`、`independent-format-ast.json`。主代理额外全阶段 22 文件 ESLint、11 suite/122、类型检查等记录已读，但不与本代理 19 项相加。

## 只读收尾盘点

独立确认六提交 ancestry 通过、14 张截图文件大小和 SHA256 相同、三报告 33 个本地链接存在；任务工作树和分支清理当时符合记录。本代理未使用 computer use、登录、服务或真实 DB，也未编辑产品、提交或改写历史 raw 证据。这些非功能核对保持有效，不能消除上述 P1。

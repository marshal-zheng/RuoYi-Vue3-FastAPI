# 角色授权阶段最终独立复核：第二轮 PASS

**BASE_SHA:** `7b6fbd0ab8f1b9475e6401a3dc10362f926c32a4`。

**候选:** 项目本地 `.worktrees/role-auth-delivery-closeout` 的未提交差量。最终复核共 24 文件：后端 20 Python + `shared/openapi.json` + 3 前端测试；逐文件 SHA256 见 `independent-round2-candidate.json`。后端/共享产物 21 文件逐项匹配实现代理的冻结 manifest，3 个前端测试逐项匹配已审源版本。本结论只针对这些 hash，不等同于已交付 std。

**P0=0 / P1=0 / P2=0。RERUN：通过。首轮 P1 已在隔离候选解决，可以继续安全交付及最终源验证。** 首轮 FAIL 保留在 `independent-review-round1.md`，未覆盖原失败或 raw delivery 证据。

## 首轮 P1 的完整闭环

四个真实授权 PUT 均接收各自固定 JSON DTO，required 数组/ID、空集合语义和 extra 字段限制在 Pydantic 层明确。单条撤销不再与批量撤销共用宽松 DTO。四条链路均为 controller→typed command→生产 `provide_system_mediator` 注册→handler→`UserRoleService`→已有仓储，缺失的批量撤销 command/handler/注册已补齐；没有 Query 兼容通路，也不再借源 dirty 业务文件让候选刷绿。

新增真实 FastAPI HTTP 用例验证请求体进入正确字段、204 空响应、旧 query-only 与非法输入在 dispatch 前 422；另一个用例保留生产 mediator/handler/service/repository，在 SQLite 真实关系表完成完整替换、增量授权、单撤销、批量撤销和显式空集合往返。该用例只覆盖身份/权限依赖替身，未手工替换授权 service 或 mediator，足以证明原“204 但 JSON 丢失”不再存在。

关联 service 使用现有事务装饰器，先检查完整目标集合，再写关系；用户/角色不存在或软删除、管理员保护、用户/角色双重数据范围均在写前拒绝。完整替换连同移除的角色一起校验；SQLite 回归验证错误批次无 SQL 写入、幂等增量、定点撤销和第二条写失败的事务回滚。用户保护和数据范围拒绝从 AuthException 改为 PermissionException，使这些实际授权拒绝维持 403，而不是会话失效 401；两处改动未带入普通用户 CRUD/profile 的其他源 dirty 行为。

## 硬切与契约收敛

- 旧 `CrudUserRoleModel`、旧 `add_user_role_services`/`delete_user_role_services` 已删除并迁移全部真实调用。末尾清查后，无消费者的 `detail_user_role_services`、其专用 `UserRoleModel` 和相应 port 声明也删除。全候选非文档搜索旧写入口只留下对旧 schema 不存在的测试断言字符串；没有遗留执行路径。
- 独立比较旧/新 `shared/openapi.json`：仅四个授权 PUT operation 及四个新增 DTO、一个旧 DTO schema 删除；其他路径与顶层语义不变。运行时 schema 测试逐项对照注册路由与 checked-in OpenAPI 的 requestBody、responses、parameters 及模型 schema，204 不含 content。现有前端 `_generated/types.gen.ts` 已含四个对应数组 DTO，不需要把其他 source-only CRUD 产物改动纳入本轮。
- `user_vo.py` 剩余 **18 个模型**由独立实际 `model_json_schema` 比较，全部与 HEAD 相同；只删已无消费者的两个 DTO，其余修改为导入/等价注解/格式。末尾 helper 清理的额外 11 项复验覆盖生产 DI 往返、用户 guard/read 和 port；未发现清理引入行为回退。
- 三个前端测试维持首轮局部审查结论：格式及明确类型，不弱化业务断言。用户/角色普通 CRUD、profile 未被整片移植。

## 本代理独立复验

| RERUN | 结果 | 证据 |
| --- | --- | --- |
| 隔离候选后端 11 文件，包括 HTTP、schema、写前检查/回滚、原读写与 port | **99 passed** | `independent-round2-backend.{json,log}` |
| 隔离候选前端 4 suite，包括 JSON API 和三个测试差量 | **23 passed** | `independent-round2-frontend.{json,log}` |
| 末尾删除 helper/DTO/port 后的必要子集 | **11 passed**，属于上面 99 项的子集，不相加 | `independent-round2-final-delta.{json,log}` |
| 最终 20 Python Ruff check / format check | 均 exit 0 | `independent-round2-ruff.json` 与对应日志 |
| 剩余 18 模型 schema、24 文件 hash、关键 runtime module 位置 | 全部符合；模块来自隔离候选 | `independent-round2-candidate.json` |
| 候选 diff check | 通过 | 已读取实际命令退出码 |

本代理的服务/API 模块位置探针开始按任意顺序直接 import service 时触发 repository 包循环导入，之后按仓库 `tests/conftest.py` 的 container-first 引导顺序重跑成功。该失败不是 HTTP/生产 DI 回归失败，不据此修改无关包结构；探针边界记在候选 JSON。上述 pytest 真实生产 DI 回归独立通过。

## 边界与交付要求

已阅读实现代理的最终 222 项相关后端、20 Python 约定检查，以及主代理干净候选 122 前端、22 文件零警告 lint、类型检查记录；不把这些当本代理重跑或叠加计数。扩大邻域 236 集合中的 config refresh 2 项、dev/menu envelope 5 项失败，已在纯 HEAD 临时归档基线独立复现为相同 7 项（实现代理证据已检查），本轮不修，不能声称全库全绿。

本复审未使用 computer use、登录、服务或真实 DB；SQLite/ASGI 验证没有网络外部调用。本代理未修改产品、不提交。最终仍需主代理将这 24 文件及必要报告证据精确交付 std，保留其他源 dirty，核对提交内容/源验证/资源清理。原始严格 delivery-status 标签保持历史真实状态；祖先证明与完整契约一致性在本轮分别核对，不能互相替代。

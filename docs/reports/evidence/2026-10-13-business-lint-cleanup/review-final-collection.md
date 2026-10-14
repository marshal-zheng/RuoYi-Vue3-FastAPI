# 最终 collection 增量独立审查

审查时间：2026-10-13。对比业务基线 `/tmp/ruoyi-lint-cleanup-baseline-20261013` 与后端增量基线 `/tmp/ruoyi-lint-backend-baseline`。审查仅修改本报告与验证证据，未编辑实现或启动 computer use。

## 结论

已审查增量无剩余 P0/P1/P2。过程中发现设备分类静态路由被 detail 动态路由捕获的 P1；主代理完成修复，独立复核确认关闭。

- `common/http_contracts.py` 的 `CollectionResult[CollectionItem]` 将泛型实用于 `items: list[CollectionItem]`。菜单列表、部门列表与排除列表、字典 optionselect，以及设备分类 options，均以实际 DTO 参数化；OpenAPI items 引用真实模型，未使用 Any 别名假造公开契约。
- `CollectionResult.items` 现为必填，无 default_factory。独立验证空对象 `{}` 被 Pydantic 拒绝、OpenAPI `required` 包含 items、显式 `items=[]` 有效；重新生成的四类 collection DTO 均声明必填 `items: Array<真实模型>`，和前端 `HttpCollection<T>` 一致。
- `ResponseUtil.ok_resource(list)` 的实际 wire format 为 `{ items: [...] }`；对象内部的普通数组仍为数组。四个原有 schema 声明调整与新增 category options 声明和该出口一致，没有把服务层原始数组误认为 HTTP 响应数组。
- `CategorySelector` 只消费 `/device/category/options` 返回的 `items`，无旧 `business_type=9999` 参数或 array/items 双契约。选项 DTO 来自生成的 `DeviceCategoryOptionModel`，保持真实 camelCase 字段。
- 设备分类 `/options`、`/checkNameUnique` 已排在 `/{category_id}` 前；排除自身的唯一性查询使用实际参数 `category_id`。模块 registry 使用真实 `device_category_router` 导出，设备模块仍被正常登记。
- 仿真 fixture 的生成脚本已再次运行，10 个当前 controller/factory 响应与已保存 fixture 完全一致；启动/停止返回 HTTP 202 accepted command 与 Location，未伪装为轮询状态。服务使用只读夹具，跳过审计装饰器，未调用真实仿真引擎或写数据库。比对见 [wire 证明](./review-final-simulation-wire-proof.json)。
- frontend 公共 `HttpCollection<T>` 的 T 实用于 items；API、消费者及 MSW 对应 envelope 一致。六个仿真集合通过实际 controller/ResponseUtil 记录的 wire fixture 接入公共 HTTP client，原对象内的数组保持原语义；带宽过滤同时由 API 和 MSW 使用真实 controller 的 `port_id`。
- ESLint、两个 tsconfig 与 Vitest 配置的字节均与业务基线相同。本次 collection 增量未引入关闭规则、logger 搬运、任意断言或 any 同义类型。

## 已关闭的 P1 与真实路由复核

原始 Starlette `route.matches()` 对 `/device/category/options` 和 `/device/category/checkNameUnique` 的第一个 FULL 匹配均为 detail，后续 int 校验会 422。修复后两个静态 handler 均为第一个 FULL 匹配，数字 ID 仍命中 detail。对 menu、dept、dict、category 四个 router 的全部静态路径和真实 HTTP methods 扫描，未发现剩余静态路由遮挡。

独立 ASGI 请求同时断言选项 handler 被调用、detail 未被误调用、参数 category_id 被传递到真实服务接口，以及数字 detail 的资源返回保持不变。仅覆写认证和服务依赖，没有数据库写入；验证的是实际路由注册、参数解析和统一序列化出口。

## 独立验证

| 验证 | 结果 | 证据 |
| --- | --- | --- |
| collection OpenAPI + category ASGI，两文件 | 8/8 通过 | [后端日志](./review-final-collection-backend.log) |
| CategorySelector + MSW/OpenAPI，两文件 | 5/5 通过 | [前端日志](./review-final-collection-frontend.log) |
| 仿真 controller/factory wire + MSW集合，两文件 | 11/11 通过 | [仿真日志](./review-final-collection-project.log) |

## E2E 证据边界

现有 demo-offline E2E 验证工程/版本/拓扑/仿真主路径；此前真实业务浏览器矩阵覆盖 Role Drawer 和 User Dialog。它们并不单独证明设备分类 options 的后端路由。该缺口本次以实际注册 router 的 ASGI 回归和组件消费者测试覆盖，不能把 ASGI 的认证依赖覆写描述为完整真实数据库/权限 E2E。

本审查的三组聚焦验证不替代主代理最终全量 lint/type/test/build、SDK 再生成验证及正式 E2E 门禁。

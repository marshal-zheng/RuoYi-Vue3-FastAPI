# Application 组 lint 清理与契约核验

范围为原 `application-scope.json` 的 83 个文件、382 条警告，以及收紧公开边界后必要的下游类型、测试与生成拥有者。未修改 ESLint/TypeScript 规则、未增加 disable/ts-ignore、未用同义 any 或整 Client/handler 断言绕过检查。

## 实现与新契约

- API 输入从 `Record<string, any>` 切到仓库 OpenAPI model、endpoint query 与确切 DTO；资源/collection/offset page/batch/no-content 返回均显式声明。真实 backend controller/read model 决定签名，mock 不作为返回形状的唯一依据。分页接收实际 HTTP 注入的只读 `pager`/`__httpMeta`。
- `getConfigKey` 从旧 string 切为 `{configKey, configValue}`；config/dict refresh 为 `{status:'refreshed'}`；role dataScope/status 为角色 resource；role cancel 为 204/null；部门树为 `{depts,checkedKeys}`；用户 profile update 返回 profile resource。mock 与相应 API 测试同步真实返回。
- 设备/分类 list 声明为 offset page；分类 options 使用 `/device/category/options` 的 canonical collection `HttpCollection<{deviceCategoryId,name}>`，消费点由 business_components/root 同步，不保留无效 `9999` 参数或 array/items 双形状。
- 生成器详情使用 backend 的 `{info,columns,tables}`，导入/创建分别返回 count resource，代码生成/同步声明确切 resource；protocol 批量删除为 batch，预览使用 `{header,fields,protocolType}`。
- VXE schema/validation 保留具体 Row 与 Context 泛型，不要求业务实体增加任意字段索引。事件、列和 edit rules 消费 VXE 公开类型。任意单元格值仅在校验边界为 unknown；`Reflect.get` 读取动态字段，未强制转换业务行。校验失败为可检查的 `VxeValidationError`。动态消息不再以空行求值。
- CRUD grid ref 使用 ZXUI 公开实例，dialog/drawer ref 使用真实组件实例。`updateState({[field]:value})` 硬切为公开 `updateState('query.' + field,value)`，sort 同样更新 query path。loadData 接收真正 `{query,pager}`，明确映射为 flat HTTP query，树列表保留 nested grid query 读取。
- FormDialog 泛型接受真实 object entity；非法 width/height 不再 console 忽略，运行时 TypeError 拒绝（JS 调用负例亦覆盖）。布局尺寸沿 columns/preset/maxHeight 契约。
- 删除确定无消费者的变量、导入、函数及 dashboard 演示残留。上传 adapter 明确 `Promise<File|null>` loader 和 URL resource，null file 拒绝上传。
- Settings 只接收实际支持的 chrome boolean preferences；未知/退休 `fixedHeader` 不再被持久化。真实 metadata 由类型与运行时校验共同约束，未保留颜色设置等旧入口。
- Route API 仅接受 HTTP collection；转换时不改写原树、不经过 JSON 隐式 any 复制。路由错误、CSRF 与 logout 错误成为可观察的 Pinia 状态；未用 console 替代错误契约，授权判定未更改。

## 响应工厂核验与 mock 修正

最初只核对 controller 的 `ok_resource(...)` 调用与 service 返回值，曾把路由、部门、分类 options 和字典 options 判为裸数组；该判断遗漏了响应工厂。`ruoyi-fastapi-backend/utils/response_util.py:71` 对外层 list/tuple/set 调用 `coerce_collection_result` 后返回 `ok_collection`，实际 HTTP wire 为 `{items}`。数组判断已撤回；未修改 backend 来迁就 mock，也未引入 array/items/data 兼容分支。嵌套数组仍保持其业务资源结构。

最终 `/getRouters`、部门 list/tree、菜单 list/tree、字典 options 和分类 options 均消费 collection。system mock 的旧裸数组改为真实 collection；部门 list 删除不真实的 total/page/pageSize，保留 `{items}`。仿真 messages/bandwidth/alarms/faults/events/strategies 的外层响应同样改为 collection，status/create/export 对象和 WebSocket data 不改变。仿真 API 与消费者由 project 组同步。

`src/api/menu-contract.test.ts` 使用真实 mainline MSW、请求客户端、Pinia 和内存 Vue Router 验证新登录能生成并注册菜单、HTTP 快照未被改写；裸数组与旧 data 包装是明确拒绝的负控。路由 collection 回归先 RED（1/2），修复 mock 后 GREEN；字典 options 回归先 RED（1/5），修复后 GREEN。仿真 raw HTTP 回归先 RED（2/3），修复后 GREEN（3/3）。相邻接口测试也同步 `{items}`。

公开 OpenAPI 的 menu list/dict optionselect response schema 仍曾声明 array，与真实响应工厂不符；已交 root 修复 schema 拥有者并重生 shared/SDK，未把错误 schema 断言放宽或降低门禁。

## 生成拥有者与 Fetch SDK

维护源为 `ruoyi-fastapi-frontend/scripts/openapi-client/*.template`，生成脚本 `scripts/generate-api-types.sh` 在锁定的 `@hey-api/openapi-ts 0.97.0` 后执行 `postprocess-openapi.mjs`。manifest 绑定三个上游 helper 原始 hash；未经审核的生成结构变化拒绝处理，全部文件检查完成后才写入。重复执行幂等，不会在下次生成时丢失修复。

`Client['request']`、各 HTTP method 继续受公开泛型约束，完整返回对象 `satisfies Client`；条件结果收敛为实际单一 `Promise<RequestResultValue<...>>`。有限断言只位于真实 response 解析/返回组合边界，不存在整 Client/handler 断言。成功 fields 明确 `error:undefined`，失败 fields 明确 `data:undefined`。

204 在 auto/no-content 和显式 JSON 模式返回 null，200 空 JSON 仍为 `{}`。显式 JSON 204 新回归先真实 RED（1/12 失败），修复后 GREEN。SSE 正常完成值为 void，错误 hook 保留 unknown；删除无真实用途的 SSE `TError` 泛型，网络 TypeError 和 HTTP 503 Error 不再被声称为 ApiError。

实际 CLI 在独立目录重生全部 16 个 SDK 文件，连续两次后处理、正式格式参数、逐文件 ESLint 与 strict TypeScript 检查：均 0 错误/警告；三个 SDK helper 与当前 source 逐字节一致。异常 source 漂移负控退出 1，三个 target 均保持原字节。

## 验证

- 限定 application/必要下游文件：严格 ESLint 0 error / 0 warning（最后全量结果由 root 汇总）。
- 公开类型收紧后的全 `vue-tsc --noEmit`：0 diagnostic。
- 相关 16 文件、67 项测试通过；最后 SDK 增补 native network/HTTP SSE 两项后专门 14/14 通过（root 全量测试统一计数）。
- 新增 FormDialog 5 项、VXE validation 5 项、GridList query 4 项，API/status/config 真实契约测试同步。
- 最后 collection 修改限定 11 文件严格 ESLint 0 error / 0 warning；真实菜单 API/store 集成 5/5、simulation/mock API 2 文件 7/7、相关 system/menu/dict/permission 6 文件 25/25 通过。最后一次全 typecheck 仅 root 正在同步的 CategorySelector test 裸数组 fixture 一项诊断，本组无新增诊断；全门禁最终结果由 root 汇总。
- frontend-conventions 的旧 `validate.sh --changed` 额外执行过；它先收集已删除 TSX 导致 ESLint no-files，另外报告 simulation hex 与 project detail console policy。未把此脚本报告为通过，已交 root 修正适用边界/拥有者；正式 lint/type/test 与这些辅助 policy 分开记录。

全量 build、业务 E2E、mock/UI 门禁由 root 在最终冻结源码上集中验证。本组未运行 computer use、未提交/发布、未写真实业务记录。

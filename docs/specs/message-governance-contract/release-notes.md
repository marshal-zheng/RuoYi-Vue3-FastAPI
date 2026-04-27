# 平台消息治理与 API 反馈契约 发布说明

## 变更类型

- 本次为现有路径上的 hard cut。
- 不新增 `/v2` 或并行成功响应结构。
- 保留现有动作型 URL，仅统一成功/错误契约与前端默认反馈 ownership。

## 受影响范围

### 后端

- `ruoyi-fastapi-backend/utils/response_util.py`
- `ruoyi-fastapi-backend/exceptions/handle.py`
- `ruoyi-fastapi-backend/middlewares/*`
- `ruoyi-fastapi-backend/modules/**/api/*`
- `ruoyi-fastapi-backend/module_admin/controller/*`
- `ruoyi-fastapi-backend/module_generator/templates/**`

### 前端

- `ruoyi-fastapi-frontend/src/utils/http.ts`
- `ruoyi-fastapi-frontend/src/utils/request.ts`
- `ruoyi-fastapi-frontend/src/utils/feedback/*`
- `ruoyi-fastapi-frontend/src/api/**`
- `ruoyi-fastapi-frontend/src/views/system/**`
- `ruoyi-fastapi-frontend/src/views/project/**`
- `ruoyi-fastapi-frontend/src/views/device/**`
- `ruoyi-fastapi-frontend/src/views/protocol/**`
- `ruoyi-fastapi-frontend/src/views/monitor/**`
- `ruoyi-fastapi-frontend/src/components/business/**`

## 契约变化

- 成功响应不再使用全局 `{ data, message, requestId }` success envelope。
- 列表主字段统一为 `items`；offset 分页字段统一为 `total/page/pageSize`。
- 错误响应统一为 RFC 9457 Problem Details，错误扩展字段限定为 `errorCode/requestId/traceId/errors`。
- 成功链路中的 `requestId/traceId` 通过响应头暴露，不再写入成功 body。
- 删除默认使用 `204 No Content`；异步受理接口使用 `202 Accepted + Location`；批量/部分成功接口使用 `results[] + summary`。
- system command handlers 不再把 service 层 `message/msg` 写入 `CommandResult.data`；controller 不再直接透传 command result data 作为成功响应。
- `/system/user/importData` 返回结构化批量结果 `{results,summary}`，部分失败以逐项 `error.errorCode/title/detail` 表达。

## 前端行为变化

- 服务端 CRUD 默认成功提示由 API wrapper `feedback` 配置和统一 feedback presenter 负责。
- 页面层不再直接处理标准 CRUD 成功 toast。
- `201/202/204/422/429` 等状态由 `src/utils/http.ts` 统一识别并交由反馈层处理。
- `feedback registry` 为单一真源；dev 环境缺 key 抛错，prod 回退为 `操作成功` 并告警。
- `src/plugins/modal.js` 不再暴露 `msg* / notify*` 废弃消息 API；业务路径本地提示改用 `ElMessage/ElNotification`，默认 CRUD 提示继续由 wrapper feedback 接管。
- `device/protocol/project` 导入类批量结果与 `simulation` 事件 CRUD 已回归统一 feedback ownership，不再由页面层重复消费服务端结果后再弹一遍提示。
- 用户导入弹窗消费 `results/summary` 并展示逐行成功/失败明细，不再读取 `response.msg`。

## 排除范围

以下链路不强制套用本次 success 结构：

- `health` / `metrics` / `docs`
- 二进制下载
- streaming
- WebSocket / SSE
- 其他协议型、非业务 JSON 响应

## 外部调用方假设

- 本次 hard cut 仅面向仓库内 `ruoyi-fastapi-frontend` 消费方。
- 不承诺移动端、第三方 SDK、CLI 或外部系统兼容。
- 因此前次发布不提供 `Deprecation` / `Sunset` 头，也不保留旧 success message 兼容窗口。

## 本次验收结果

- 前端治理扫描通过：`node scripts/check_message_governance_frontend.mjs`
- 后端治理扫描通过：`python3 scripts/check_message_governance_backend.py`
- 前端类型检查通过：`cd ruoyi-fastapi-frontend && yarn type-check`
- 前端反馈层定向回归通过：`cd ruoyi-fastapi-frontend && yarn test:run src/utils/http.test.ts src/utils/feedback/presenter.test.ts src/utils/feedback/registry.test.ts`
  结果：`16 passed`
- 后端定向契约回归通过：`cd ruoyi-fastapi-backend && ./.venv/bin/python -m pytest tests/unit/services/test_project_service.py tests/unit/services/test_project_version_service.py tests/integration/test_success_contract_responses.py -q`
  结果：`23 passed`
- 用户导入与 command 边界回归通过：`cd ruoyi-fastapi-backend && ./.venv/bin/python -m pytest tests/integration/test_success_contract_responses.py -q -n0 --no-cov`
  结果：`14 passed`
- system command handler 回归通过：`cd ruoyi-fastapi-backend && ./.venv/bin/python -m pytest modules/system/tests/test_user_write_commands.py modules/system/tests/test_role_write_commands.py modules/system/tests/test_menu_write_commands.py modules/system/tests/test_dict_write_commands.py modules/system/tests/test_config_write_commands.py modules/system/tests/test_dept_write_commands.py modules/system/tests/test_post_write_commands.py modules/system/tests/test_notice_write_commands.py -q -n0 --no-cov`
  结果：`35 passed`

## 已知限制

- 页面和业务组件中仍保留少量 `ElMessage.*` 用于本地交互、上传下载、WebSocket 实时事件或编辑器内部提示；这些调用不再承担服务端 CRUD 默认反馈职责。
- 后端定向 pytest 仍会输出既有的 pydantic alias / coverage warning，但本次消息治理相关断言均已通过，不阻断当前 hard cut 收口结论。

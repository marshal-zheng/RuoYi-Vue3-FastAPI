# Project / simulation HTTP wire 最终复核

本轮纠正了前次仅依据 service 的 list 返回值判断为裸数组的遗漏。实际 `ResponseUtil.ok_resource` 在 `ruoyi-fastapi-backend/utils/response_util.py:71` 将外层 list/tuple/set 投射为 collection，最终 HTTP body 为 `{ items: [...] }`。API、消费者和 Mock 全部按该唯一契约硬切，未恢复旧 envelope 或裸数组兼容分支。

| 接口 | controller / service / factory 结果 | 前端落点 |
| --- | --- | --- |
| messages | `read_messages_with_fallback` 返回 list，经 factory 为 collection | `HttpCollection<SimulationMessage>` / `.items` |
| bandwidth | `read_bandwidth_with_fallback` 返回 list，经 factory 为 collection；query 为 `port_id` | `HttpCollection<SimulationBandwidth>` / `.items` / `port_id` |
| alarms | `read_alarms_with_fallback` 返回 list，经 factory 为 collection | `HttpCollection<SimulationAlarm>` / `.items` |
| faults、session faults | `list_faults` 返回 list，经 factory 为 collection | `HttpCollection<FaultWire>` / `.items` |
| events | `list_events` 返回 list，经 factory 为 collection | `HttpCollection<SimulationEvent>` / `.items` |
| strategies | controller 从真实 `STRATEGY_DEFINITIONS` 构建 list，经 factory 为 collection | `HttpCollection<SimulationFillStrategy>` |
| start、stop | `accepted_job` 原样返回 controller 的 `{ sessionId, action, status: 'accepted' }`，HTTP 202 + Location 状态 URL | `SimulationSessionCommandAccepted<'start' / 'stop'>` |

项目和版本列表仍是实际分页资源。topology、alarm details 等对象内部数组，以及 WebSocket frame 内数组，保持实际结构。

修改覆盖 API、`useSimulationApi`、`useEventTrigger`、`useFaultInjection` 与只读仿真页面的数据读取。Mock 投射层使用公开业务类型，时间戳转为数值，历史事件具有名称、触发状态和触发时间，策略列表与后端五项定义一致，并按 `port_id` 过滤带宽。`SimulationSessionData` 删除了真实创建资源没有的 projectId/versionId/createdAt 必填字段，保留实际 sessionId/status/message。

`useSimulationApi` 返回 accepted acknowledgement；`useSimulationControl` 不读取 command response 的状态字段，其原有成功后乐观 running/stopped 和 WS 状态同步流程保持原行为。此次没有扩展仿真 UI、状态机或轮询功能。

## 真实产物与回归

`ruoyi-fastapi-frontend/tests/fixtures/simulation-http-wire.py` 调用实际 controller 和 ResponseUtil，依赖替换为无数据库、无写入的 service fixture。start/stop 跳过审计 decorator，避免创建日志数据库记录。生成命令：

```sh
cd ruoyi-fastapi-backend
PYTHONPATH=. ./venv/bin/python ../ruoyi-fastapi-frontend/tests/fixtures/simulation-http-wire.py
```

最终记录的 JSON 与 `tests/fixtures/simulation-http-wire.json` 完全相等，证明 fixture 不是手写的假返回形态。Vitest 使用 MSW 传输这些实际 factory bytes，调用真实 HTTP 客户端及 composables。前端常规测试无需安装后端 Python 环境。

- `project-wire-red.log`：修正前 4 失败 / 2 通过，复现数据消费者收到 collection 对象、事件对象被当成数组、故障被静默丢弃及错误 portId 参数。
- `project-accepted-types-red.log`：4 项 TS2344，复现 API 与 composable 将 accepted command 错误声明为 session status。
- `project-wire-mock-red.log`：Mock 时间戳与 port_id 筛选的行为回归先失败。
- `project-wire-green.log` / `project-wire-tests.json`：最终 13 文件、159 测试全部通过，exit 0。包括七项真实 wire 回归、项目/仿真 API、控制/事件/data、WebSocket、health check 与 Mock/invariants。
- `project-wire-lint.log` / `project-wire-lint.json`：最终限定 54 文件，errors 0、warnings 0，exit 0；没有关闭规则或添加 disable。
- `project-wire-types.log`：`vue-tsc --noEmit` exit 0。
- `project-wire-factory.json` / `project-wire-factory-receipt.json`：真实 controller/factory 再生成成功、fixture 相等、七个集合和两项 accepted command 被验证，数据库写入为 0。

源码已冻结；全库构建、全量测试和最终业务浏览器验证由主任务统一验收。

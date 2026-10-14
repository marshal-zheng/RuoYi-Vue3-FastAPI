# 组件与业务独立审查

日期：2026-10-14。审查起点是 `/tmp/ruoyi-lint-cleanup-baseline-20261013`，不是脏工作区的 Git HEAD，也未将上一轮测试通过当作行为正确的证据。

本代理负责 components、views、基础 utils、directives、Vue 全局声明；request/http、API/store/mock/SDK 和 ZXUI 源码由另外两个独立审查者负责。起始增量盘点为 177 个文件、12,490 行 diff。重点逐项审查运行行为与消费边界，并针对发现的问题执行实际函数或挂载回归；这不代表逐行证明 177 个文件的每个潜在输入。

## 清 lint 引入的回归

| 问题 | 独立证明 | 修复 |
| --- | --- | --- |
| P1 注册验证码响应变量被误删 | 真实 `getCode` 源码执行：baseline 设置图片与 uuid，清理后抛 `ReferenceError: res is not defined`。开启/关闭验证码两个分支均 RED。 | 恢复实际 Promise 回调的 `res` 参数；不是重新引入无用变量。 |
| P2 只读仿真快照错误降级二次抛错 | 真实 SFC 私有函数注入失败的 API：baseline 正常完成 catch，清理后抛 `ReferenceError: err is not defined`。 | catch 给出用户可见提示并正常完成降级，取消失效的 console 引用。 |
| P2 报文源/目标端口筛选被白名单遗漏 | ProtocolAnalyzer 确实提供 `senderPortId/receiverPortId`。同一报文运行真实 before/after 匹配函数从 true 变 false。真实 useSimulationData 挂载后，AND/OR 两个结果 RED。 | 将两个实际端口字段加入明确的白名单；AND/OR 和“只命中源端口”场景通过，保留筛选重置历史数据的既有语义。 |
| P1/P2 停止后实时状态整帧被新 decoder 丢弃 | 内存实例化真实 SimulationService：移除引擎、保留配置的 stopped 分支返回 snake_case；实际 decoder 返回 null，旧消费者仍能读取 status。未连接 DB/Redis。 | 已将证据交主代理，在服务输出 owner 硬切为 canonical camelCase。本代理未增加前端 alias 兼容。最终验证见主报告。 |

证明文件：[注册 before/after](/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/2026-10-14-independent-review/business-register-before-after.json)、[快照 before/after](/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/2026-10-14-independent-review/business-readonly-before-after.json)、[端口 before/after](/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/2026-10-14-independent-review/business-port-filter-before-after.json)、[真实 stopped 状态被丢弃](/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/2026-10-14-independent-review/business-stopped-status-before.json)。

## 同一改动范围内的历史缺陷与旧原型

- 下载文件名的原正则未正确匹配 RFC5987 `filename*`。真实后端导出控制器确实发出该头部。已优先解析 UTF-8 扩展名称，同时存在 ASCII 名称时保留中文；扩展编码损坏时仍可用 ASCII 名称下载。有效二进制内容与文件名的现有回归继续通过。
- ProtocolAnalyzer 自动滚动按钮调用两个根本不存在的 restart/stop 函数。挂载真实 SFC 的三个回归先全部 RED；现在启用走已有 `scrollToBottom`，nextTick 与 rAF 都检查开关，关闭中途动画或快速 on/off 均不再滚动。
- TopoExport 原有文件级 `eslint-disable`、`response: any`、PNG 参数断言和 FileReader 断言已撤销。GET 拓扑合法返回 `{}`，不能伪造一个必有数据的 DTO；工具保留 unknown 边界，检查资源、graph、cells 的结构，再交 X6 处理元数据。合法空资源仍返回可选缺图结果；非法 cells 不创建 renderer；有效 attrs/data 保留，图片 bytes 和资源释放通过。渲染器被单测替身隔离，不据此声称已验证真实位图视觉质量。
- NodeEditDrawer 不再禁用 unused 规则。实际分组 computed 的 before/after probe 深相等：两个有序组、重复协议只保留一条、UI payload 无 seenKeys。
- DeviceClazzDialog、ProjectEditDialog 和两个模拟 ExportDialog 的全仓活跃消费者只有 barrel/fixture。旧 ID、description 参数、假成功导出没有继续公开；已删除四个文件、导出与 F04/F05/F07/F08 夹具及相关 handler。全局 d.ts 没有遗留引用。真实 CategoryFormDialog、ProjectFormDialog、VersionExportDialog 和业务导出页面继续使用实际服务。夹具 AST 实数为 23 → 19，历史编号未重排。

DeviceCategoryModel 实际同时有 descr/remark，本轮没有依据“缺少 descr”的错误判断更改现有分类表单。

## 类型与行为覆盖

已核对：删除的 defineComponent/propsFactory/大段 helpers 没有实际消费者；剩余四个颜色 helper 保留实际调用。debounce 保留最新参数与接收者；handleTree 的数字/字符串 ID 和原型名称处理保持有意义的行为。权限工具对非法输入失败关闭，复制/下载失败没有假成功。表单 FormInstance、FormDialog geometry、VXE 列/事件/规则消费真实公开类型；协议值标准化、字典选中实体、图模型标识不变式与状态不被误写均有现有回归重新执行。动态 Reflect.get 读字段的出口是 unknown，并在使用前检查；没有把整个动态对象断言成业务 DTO。

最终扫描的 owned 生产域（排除按分工交给 HTTP reviewer 的 request/http）中，`eslint-disable`、`@ts-ignore`、`@ts-nocheck`、`as any`、`as unknown as`、`as never` 和 explicit any 残留为 0。这是指定危险模式与改动边界的审查结果，不是对未变更 JSON import 工具或第三方类型实现的全域形式化证明。

未覆盖：API/store/request/mock/生成 SDK 与 ZXUI 组件库内部归其他审查者；未执行真实用户/角色写操作、真实仿真启停/持久化、位图导出视觉测试或所有图形模型输入组合。旧 GridList 能接受多种内部展示结果，但未将这种库能力当作 HTTP API 兼容分支保留的理由，HTTP 契约归对应 reviewer 复核。

## 收口证据

| 验证 | 当前源码结果 |
| --- | --- |
| 严格 targeted ESLint，`--max-warnings 0` | exit 0 |
| 全量 `yarn type-check` | exit 0；首次发现的旧 API 测试引用由 HTTP reviewer 修正 |
| 四个新回归测试文件 | 16/16 通过 |
| 十一个相关测试文件，含协议/图/仿真/FormDialog/VXE | 84/84，exit 0 |
| 额外 no-undef 增量审查 | 93 个保留的改动 Vue 文件，0 新增未定义引用 |
| NodeEditDrawer 实际分组等价 probe | 通过 |
| 四个旧原型、所有活跃 import/夹具/global 声明 | 0 遗留引用 |

规则配置未更改，没有通过关闭规则消除检查。额外 no-undef 是只读审查覆盖：Vue 的 getCurrentInstance/resolveComponent 属于实际 Vite 自动导入，未当作运行错误。既有 useSimulationData 测试仍输出未在 setup 中调用生命周期 hook 的 Vue 提示；本轮新增的行为测试使用真实挂载，未屏蔽这些存量提示。

完整日志、RED 证据和最终 source SHA manifest 见 [验证摘要](/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/2026-10-14-independent-review/business-review-validation.json)、[最终聚焦测试](/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/2026-10-14-independent-review/business-focused-final.log)、[源码冻结清单](/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/evidence/2026-10-14-independent-review/business-review-source-final.json)。组件库与业务全量构建/E2E 验证由主代理在全部 reviewer 源码冻结后统一执行。

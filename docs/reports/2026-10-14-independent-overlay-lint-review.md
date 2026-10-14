# 组件库与业务改动独立审查

本轮独立审查发现了上一轮测试未覆盖的业务回归，以及被类型声明、mock 和 lint 豁免掩盖的契约缺口。发现项均已修复，并在全部实现冻结后重新执行组件库、业务前端的标准全量门禁。审查范围内没有留下未处理的 P0/P1/P2；这不是对整个仓库所有历史功能和输入组合的正确性证明。

## 审查方式与起点

委派三名新的审查者，分别检查库布局/生命周期、HTTP/API/store/SDK/mock、业务组件/工具/视图。以真实调用者、controller → service → response factory 和起始源码对照推导行为，没有把上一轮 PASS 当作审查结论。根代理核验发现、处理后台输出与协议导出，并统一执行最终验证。

业务 lint 起点为 `/tmp/ruoyi-lint-cleanup-baseline-20261013`；库使用本轮 overlay 与 full-validation 起始快照，避免把两个 dirty 工作区原有改动归入此次修复。此轮业务实际源码增量 48 文件，包含新增回归与删除的死入口，见 [增量清单](evidence/2026-10-14-independent-review/business-source-review-delta.json)。未提交、发布或修改正常业务记录。

完成检查：

- [x] 重新核对运行行为、公开类型与实际消费边界。
- [x] 用真实函数、挂载组件、Python owner、native XHR 或实际 SDK 复现缺陷，再修复。
- [x] 清理规则关闭、类型绕过和审查范围内的旧契约入口。
- [x] 源码冻结后重跑完整门禁、布局矩阵与当前业务验证。

## 清 lint 引入的实际回归

| 问题 | 影响与修复 |
| --- | --- |
| P1 注册验证码回调删掉 `res` 参数，却继续读取 `res` | 注册初始化出现 ReferenceError，图片与 uuid 无法更新。恢复真正使用的回调参数；验证码开/关分支均有源码执行 RED/GREEN。 |
| P2 只读仿真快照 catch 删掉异常绑定，却继续读取 `err` | 请求失败时错误降级再次抛错。移除失效日志引用，给出可见提示并正常完成降级；真实 SFC 函数失败路径回归通过。 |
| P2 报文筛选白名单漏掉源、目标端口 | UI 仍提供两个端口条件，正常报文被过滤。加入实际字段，真实 composable 的 AND/OR 与单端命中场景通过。 |
| P1 停止状态被新增 WebSocket decoder 丢弃 | 无引擎但有配置时，后台 owner 输出 snake_case；decoder 要求 camelCase，其他客户端无法同步停止。后台 stopped 分支统一 camelCase，not_found 补齐真实会话标识与零计数；没有在前端加入双形态兼容。 |

真实 Python owner 和实际前端 decoder 对照：修复前 stopped/not_found 两帧均被拒绝，修复后两帧均正确接收。见 [状态帧前后对照](evidence/2026-10-14-independent-review/ws-decoder-before-after.json)。

## 类型、规则和旧契约收口

- 库布局测试的 `as any` / `ref<any>` 改为实际 Provider、padding 和 scroll 类型，两个 Hook 的响应式输入仍受公开签名检查。
- 移除库四处新增的规则禁用，恢复原测试 matcher。夹具组件按正常模块拆分，没有搬到豁免目录躲过规则。原来的路由功能断言保留；浏览器警告与渲染异常改为显式数组读取，新增负控证明异常仍会让门禁失败。库 ESLint 配置与本轮起始规则逐字节一致，见 [规则恢复证明](evidence/2026-10-14-independent-review/library-rule-restoration.json)。
- SSE callback 原来退成 never/unknown，控制帧又会发送 undefined 数据。修改维护模板并正式再生 SDK，使状态映射、callback、stream 共享正确泛型。只有带 data 的帧分发数据事件，id/retry 继续更新，符合 [WHATWG event stream interpretation](https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation)。真实类型失败与多派发负控均已闭环。
- 删除无消费者的伪 Axios 双重断言适配器、重复认证入口、错误拓扑 API/MSW 别名和旧 mock 信封类型。保留有限且可核验的 transport 解析边界断言，没有用整个 Client 或 callback 强转绕过检查。
- TopoExport 移除文件级规则禁用、any 与未经校验的参数断言，检查真实拓扑/cells 结构后交给 X6。NodeEditDrawer 用实际对象拷贝/删除去重字段，分组前后等价。
- 移除只有 barrel/fixture 消费的四个旧原型：DeviceClazzDialog、ProjectEditDialog 和两个模拟 ExportDialog。其旧 ID/描述字段、样例记录和假成功导出不再公开；实际业务表单和导出入口保留。活跃夹具 23 → 19，历史编号未重排。

同一触及范围内还修复了两项历史行为问题：RFC5987 文件名正确优先 UTF-8 扩展名，损坏编码可用 ASCII fallback；ProtocolAnalyzer 自动滚动使用实际函数，nextTick 与 rAF 均受开关控制，快速开关不再抛错或继续滚动。

协议导出现在发送真实 Form 参数并启用 Blob 解码。MSW/jsdom 的 XHR shim 会把高字节经 UTF-8 text 转换，因此另用隔离 native 浏览器 XHR 验证真实 API 模块：表单、POST、MIME 和包含 0xff/0x80 的 7 字节全部保留，未请求真实导出后台。见 [二进制证据](evidence/2026-10-14-independent-review/protocol-export-browser.json)。

缓存两条 `List[...]` schema 改为实际 `CollectionResult[CacheInfoModel]/CollectionResult[str]`，更新公开 OpenAPI artifact，再用锁定 generator/维护模板正式生成 SDK。独立目录 16 文件逐字节一致；重复后处理幂等，未知结构拒绝且无部分写入。

## 离线行为的明确变化

system mock 数据源只读，原有 22 项状态写入只是 echo 或空成功，GET 数据不变。此次硬切为明确 501 ProblemDetails，registry 同步能力状态，不能再假报保存成功。其正常读取和真正有 session 状态效果的 auth logout 保留。此变化限于未实现的离线系统写操作；本轮没有实现系统 CRUD 持久化。

已实现 Dexie 持久化的项目/版本创建与克隆返回真实 201、Location 和资源，DELETE 为 204 空 body，并能用 Location GET 读回。克隆消费真实 sourceVersionId/versionNumber/versionName，拒绝旧别名，保存请求版本号，复制拓扑；重复号 409 拒绝且不新增记录。

unsupported、unhandled 和 overlay 错误统一 `application/problem+json`，撤销 code/msg/data 信封；User 部门树 mock 统一 items。mock gate 当前 244 operations：64 handled、29 real-only、35 unsupported、116 missing；75 critical 0 failures。未实现能力仍明确可见，不把它们算成完整后端模拟。

## 冻结后的全量验证

| 入口 | 本轮结果 |
| --- | --- |
| 业务 `yarn lint:check` | 599 文件，0 错误、0 警告 |
| 业务 `yarn type-check` | 0 类型诊断；另跑 mock strict 与 SSE strict consumer |
| 业务 `yarn test:run` | 102 文件，805/805 通过 |
| `yarn ui:standards` | 502 文件，0 违规；14/14 回归通过 |
| `yarn mock:contracts` / `yarn mock:overlays` | 两项严格门禁 exit 0 |
| `yarn build:prod` | exit 0 |
| 两套官方离线 E2E | core 1/1、page-state 8/8 通过 |
| 库 `pnpm lint` / `pnpm typecheck` / `pnpm ui-contracts:check` | 全部 exit 0 |
| 库 `pnpm test:run` | 主 Vitest 2478 项通过；Node 39/39、MCP 84/84、authority 21 阶段通过 |
| 库 `pnpm build:theme` / `pnpm build` | 均 exit 0 |
| 两个 opt-in composition timing 文件 | 另按单进程正式环境运行，3/3 通过 |
| 源码与安装包 Drawer/Dialog 矩阵 | 各 156 场景通过，0 页面异常 |
| 源码与安装包 divider | 各 26 场景通过 |
| 当前业务 Role Drawer / User Dialog | 两主题、桌面/移动端共 8 场景通过，0 页面异常、0 角色/用户写操作 |

主库默认保留 opt-in 的 1 文件/2 测试 skip，对应计时检查已另跑；没有把 skip 算成执行。authority 是 dirty 工作区的 local-working-source-validation，不是 clean release 准入。两个独立 packed/hosted consumer 门禁也通过，浏览器使用隔离 headless launch，未连接用户浏览器。

业务全量门禁前后 3803 个源码、夹具和配置 hash 无变化；业务规则配置与起始快照相同，库规则恢复原字节。最后 80/8088 均 HTTP 200，未手动重启开发服务。当前业务验证包含登录，不能把“0 角色/用户写操作”扩大成“0 数据库写入”。离线 E2E 的状态写入发生于测试 mock。

入口、退出码和日志：[业务全量](evidence/2026-10-14-independent-review/business-validation.json)、[库全量](evidence/2026-10-14-independent-review/library-validation.json)、[布局矩阵](evidence/2026-10-14-independent-review/overlay-matrix-execution.json)、[冻结检查](evidence/2026-10-14-independent-review/business-gates-source-integrity.json)。

后台相关 service/controller、schema、response factory、exporter 和分类回归共 70 项通过；修改的 cache 路由、registry 和测试文件 Ruff/format 通过。模拟服务整文件仍有任务起始即存在的 228 条 Python 风格/复杂度诊断，wire 修正未新增，见 [增量对照](evidence/2026-10-14-independent-review/simulation-service-lint-delta.json)。没有运行或声称后台全库 pytest/mypy/Ruff 通过。

旧 frontend-conventions helper 仍会把已删除文件交给 ESLint、对此前已有 simulation 颜色/detail 日志报错；backend helper 也报告上述整文件存量 lint/format。这两项辅助脚本未计为通过，未修改规则绕过。正式前端/组件库全量门禁与这些存量辅助检查分别记录。mock overlay 65 条非 Core 覆盖提示及构建工具提示也没有伪装成零提示。

## 独立证据与覆盖边界

[库独立审查](evidence/2026-10-14-independent-review/library-review.md)、[业务独立审查](evidence/2026-10-14-independent-review/business-review.md)、[HTTP 独立审查](evidence/2026-10-14-independent-review/http-review.md) 均保留原始失败、修复后通过、类型探针和差异证明。

额外 no-undef 覆盖 93 个保留的改动 Vue 文件，无新增未定义引用；这补充 JavaScript 路径审查，不把所有未变更模块变成形式化验证。未声称六个独立包全仓审查、真实仿真启停/数据库持久化、完整 SSE grammar fuzz 或所有图形模型/位图视觉输入组合已验证。

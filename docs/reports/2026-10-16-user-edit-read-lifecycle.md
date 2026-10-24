# 用户编辑回读生命周期修复

日期：2026-10-16。已实施并完成验证，未提交 Git、未发布 npm。

## 根因与责任

原 UserFormDialog 在请求返回后才 open，读取前的 setLoading(true) 又会被 open 重置。每次读取均无 AbortSignal、打开操作身份或关闭失效机制。因此先点 A 再点 B 时，A 的慢响应仍可覆盖 B；关闭后仍可被旧响应重新打开；旧 finally 也可释放新读取的 loading。

盘点了当前用户页的两个真实入口（新增、编辑），以及角色、参数、字典、岗位、部门和通知的类似回读代码。本轮实施边界是用户编辑弹窗及其真实入口，未将其他领域的读取批量迁移，也不将这些入口宣称为已修复。

| 层级 | 责任与结论 |
| --- | --- |
| ZXUI HTTP | 已支持每次请求的 AbortSignal、原始取消原因与错误上下文；没有证据需要新增全局取消／请求共享策略 |
| ZXUI useDialog | 已提供可见状态、body loading、禁用确认和完整 open 的初始快照；关闭／确认也有自己的会话守卫；不应负责猜测业务详情请求 |
| 业务 useFormDialog | 继续承接既有布局与 Dialog 契约，没有新增通用异步加载抽象 |
| 用户编辑业务 | 知道本次 userId、字段映射与何时结果过期；负责将一次回读绑定到一次打开意图，并在失败时提供重试 |

定向核对 [Vue 异步副作用清理](https://vuejs.org/guide/essentials/watchers.html#side-effect-cleanup) 与 [Axios AbortController](https://axios.rest/pages/advanced/cancellation)，并阅读本地实际实现。复用取消、同步可见状态监听和结果身份检查即可覆盖目标；不需要引入新依赖、请求框架或向 @zxio/http 放入弹窗规则。本轮无需修改 ZXUI 或后端。

## 修复内容

1. `getUser` 在原 API 上增加可选的 signal/silentError 配置透传，保留现有详情 URL 和返回结构。
2. 打开用户弹窗时立即显示本次 userId 的空白占位和加载态，清空旧角色／岗位选项并禁用确认。加载或失败时，业务确认回调也明确返回 false，不能保存占位数据。
3. 每次打开创建独立 activeRead 和 AbortController。新打开、关闭或卸载先使旧操作失效，再取消其请求；成功、错误及 finally 均核对身份。旧结果不能写表单／选项、弹提示或释放新 loading。
4. 当前读取成功后通过既有 open(fullData) 写入完整数据，重新建立表单初始快照，避免把服务器回读值当成用户修改。正常／停用用户字段、角色／岗位和新增专属密码语义继续保留。
5. 当前读取失败保持弹窗打开，显示错误和“重试”，确认仍禁用；重试读取同一 userId。全局读取反馈静默，只有仍有效的读取负责呈现错误。原 open Promise 保留原始拒绝；页面新增／编辑入口和重试事件终点承接已反馈的失败或取消，避免重复上报。

收益是表单始终对应最后一次打开意图，且慢网、关闭和失败下都不会串数据；代价是业务新增少量读取状态与明确的失败重试界面。操作范围保留在当前消费者，不引入全局 URL 防重、读取缓存或跨业务调度。

## 回归与检查

在既有 UserFormDialog.test.ts 中增加 6 项必要回归：A/B 响应乱序、旧失败不清新 loading、关闭重开、编辑切新增、当前失败重试、卸载。以本轮开始时保存的旧组件执行，6 项失败、原有 4 项通过，无未处理错误；恢复修复组件后 10 项通过。延迟 Promise 故意不响应 abort，用于锁定“取消失效时仍须忽略旧结果”的边界。

| 检查 | 结果 |
| --- | --- |
| 用户编辑回归 | 10 项通过，其中新增 6 项 |
| 受影响回归 | 4 文件、39 项通过，包含已有导入、HTTP 和上传契约 |
| 全量 lint / type-check | 通过 |
| 测试文件定向 ESLint | 通过 |
| ZXUI 源码直连生产构建 | 通过，23.50 秒，仅现有 chunk 大小提示 |
| 独立只读审查 | 无阻塞项，另跑用户编辑回归 10 项通过；确认无需修改通用库 |
| git diff --check | 通过 |
| changed 规范脚本 | 仍被既有 VersionList.vue console 调用阻断；该文件本轮 hash 未变 |

命令、退出码和旧实现失败输出见 [checks.json](evidence/2026-10-16-user-edit-read-lifecycle/checks.json) 及同目录的 regression-red.txt / focused-tests.txt。不把存在既有失败的规范脚本整体报告为通过。

## 真实业务验证

通过编译后的生产 UserFormDialog setup／读取与保存函数、用户页实际事件函数、源码 useFormDialog/useDialog/@zxio/http，请求真实本地 FastAPI 和 Docker MySQL。网关只延迟真实后端响应，没有构造用户详情。没有使用 computer use；未挂载原生表单校验和完整视觉界面，不声称完成浏览器点击或视觉验收。

本轮最终验证 7 项通过：

| 场景 | 实际结果 |
| --- | --- |
| 快速 A → B | 两个详情都由真实后端返回 200，A 的 XHR 被取消；B 保持最终选中。加载前确认被拒绝；保存后只修改停用用户 B，用户 A 不变，角色／岗位保留 |
| 关闭后重开同一用户 | 旧请求取消，旧完成不解除新 loading；新回读正确，保存正常用户 A 并由真实详情读回，角色／岗位保留 |
| 当前读取失败重试 | 将一次实际请求指向不存在的用户，得到真实 404；保留 Axios cause、配置及 Problem Details，反馈一次；占位数据不可保存；恢复地址后同用户重试成功 |
| 编辑切新增 | 新增元数据由真实 API 返回，旧编辑请求取消；新增 userId、用户名和密码不被旧编辑结果覆盖 |
| 用户页事件终点 | 原生产 handleUpdate 承接已反馈的真实 404；再次经同一入口读取成功，无重复反馈或未处理拒绝 |
| 卸载 | 暂存真实 200 后卸载，XHR 取消并保留 reason；无迟到结果或失败提示 |
| 数据清理 | 本次创建的 2 个专用临时用户已由业务 API 删除，回读遗留为 0；原有 1 条用户数据逐项比较不变 |

详情见 [actual.json](evidence/2026-10-16-user-edit-read-lifecycle/actual.json)。确定性旧成功／旧失败乱序由组件回归验证，真实取消和最终保存目标由实际 XHR／后端验证，两类证据分别记录。

## 范围与收尾

本轮仅修改用户 API、用户编辑弹窗、用户页两个打开事件及既有测试文件。此前的用户导入、HTTP、后端和 ZXUI 改动保持不变；其他原有工作区文件通过 SHA256 比较保护。任务账号已退出，只停止本轮启动的后端，保留已有 Docker MySQL、Redis 等服务。收尾数据和文件边界见 checks.json 的 completion 记录。

执行计划为 [user-edit-read-lifecycle](../plans/2026-10-16-user-edit-read-lifecycle.md)，计划结构验证与后续执行信息记录在 checks.json 的 planStageCheckpoint；完成结论来自回归、真实 API 和独立审查证据。

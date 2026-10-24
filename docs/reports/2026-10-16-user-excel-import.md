# 用户 Excel 导入链路收敛

日期：2026-10-16。已修复并完成本轮验证，未提交 Git、未发布 npm。

## 结果与责任

本轮修改业务 API 和用户导入弹窗两个生产文件。ZXUI HTTP 已能保留 FormData、鉴权、请求进度、AbortSignal 和原始错误；问题在业务继续使用 Upload 自带 XHR，同时缺少失败、取消及旧回调的处理。因此复用已有能力，无需修改 ZXUI 或后端。

| 责任 | 当前处理 |
| --- | --- |
| ZXUI Upload | 保持通用选文件组件；`autoUpload=false`，不调用 submit，不启动第二条传输链路 |
| ZXUI HTTP / Axios | 复用现有请求准备、鉴权、multipart boundary、进度、取消和错误分类能力 |
| 业务 API | `importUserExcel(file, updateSupport, config)` 使用既有 request/FormData 上传；字段名 file、查询参数 updateSupport 与真实后端一致 |
| 业务操作 | 一个 activeUpload 拥有 controller、task 和 loading；重复触发返回同一 task；关闭、重开和卸载先使操作失效再 abort |
| 业务反馈 | 只让当前操作展示错误和批次结果；HTTP 全局反馈静默，避免关闭后的错误提示；原始请求拒绝继续保留 |

## 根因与实现

原弹窗手写 action、Bearer header，仅监听 Upload 的 success/progress；没有 error 回调，loading 直到收到进度才占用，失败也不会释放。关闭只清空界面状态，不终止请求或作废回调，迟到的成功可能关闭新弹窗、显示旧结果或触发列表刷新。

现在业务直接读取 Upload 的公开文件列表数据，经现有 `validateFile` 验证 Excel 扩展名和 10MB 大小限制，并调用 HTTP API。`raw/status/percentage` 沿用现有 Upload 文件项契约，不另建文件队列或传输适配器。失败恢复文件为 ready，保留原文件，允许直接重试。上传期间禁用文件选择和更新选项，loading 从操作开始到本次请求处理结束。

操作对象用 shallowRef 保存，进度、结果、错误及 finally 都检查对象身份。关闭／重开／卸载清除当前对象后调用原生 AbortController；普通请求失败交给既有 Problem Details presenter，取消不提示失败。原始 task 保持拒绝，点击事件终点承接已经反馈的失败，避免 Vue 重复上报。

所有关闭路径通过真实 useDialog 的 state.visible 同步监听覆盖，包括页脚取消、X／ESC／外部关闭；组件卸载另作释放。批次统计、逐行结果、HTML 转义及模板下载均保留。结果弹框的关闭不作为导入失败。

原生 Upload XHR 默认 timeout 为 0。HTTP 库识别 FormData 后默认上传超时为 60000ms，而不是普通请求的 10000ms；接入时显式设置 `timeout: 0` 保留旧上传的等待语义，由 signal 支持用户取消，避免将这次链路收敛变成批量处理等待时间的缩短。没有改变库的超时优先级或全局配置。

已定向核对 [Element Plus Upload API](https://element-plus.org/en-US/component/upload.html#api) 和 [Axios 取消契约](https://axios.rest/pages/advanced/cancellation)，并读取本地实际安装版本及 ZXUI 源码。选择“文件选择 + 现有 HTTP 请求”，是因为本业务需要保留失败文件、独立控制弹窗会话，并且现有 HTTP 已覆盖传输能力；避免再维护 Upload XHR 与统一 HTTP 两套错误／取消流程。没有为本轮新增上传框架或通用调度机制。

## 定向回归与质量检查

- 新增一个必要的组件回归文件，共 7 项：失败后保留文件重试、进度前占用 loading、重复点击、旧成功／失败／进度不影响新操作、关闭／卸载取消、文件选择校验。原实现运行时观察到 7 项预期失败，再完成修复。
- 在既有 upload.contract.test.ts 增加 1 项真实 Axios adapter 回归，覆盖导入接口、query、FormData、signal、进度和等待时间。先观察到 timeout=60000 与预期 0 不符，再显式配置后通过。
- 最终 5 个文件、42 项定向测试通过，包含既有 HTTP、下载和用户编辑回归；全量 ESLint 和 type-check 通过。
- `VITE_ZXUI_LOCAL=true`、`VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` 源码直连生产构建通过，22.54 秒，仅现有 chunk 大小提示。
- 独立只读审查通过，审查方另跑组件回归 7 项；增量确认 timeout=0 可保留且取消有效，没有本轮必须修改的通用库问题。
- changed 规范脚本仍被既有 VersionList.vue 的 console 调用阻断；本轮没有修改该文件。全量 lint/type-check 已单独通过，不把该脚本整体报告为通过。

命令、退出码和审查记录见 [checks.json](evidence/2026-10-16-user-excel-import/checks.json)，回归输出保留在同目录。

## 真实业务验证

通过编译后的生产 UserImportDialog setup／操作函数、源码 useDialog、源码 @zxio/http、真实 Axios XHR 请求本地 FastAPI 与 Docker MySQL。UI 展示／选文件由探针记录，没有使用 computer use，没有进行浏览器点击或视觉验收。

真实后端下载的 Excel 模板有 7 列；所有成功导入文件均从该模板填充，性别／状态使用模板约定的“男／正常”。验证结果共 8 项：

| 场景 | 实际结果 |
| --- | --- |
| 模板下载 | 正常下载和解析；7 列匹配，作为本轮导入文件来源 |
| 成功导入、重复触发 | 仅发出一次 multipart；创建成功并由真实列表读回；批次结果显示一次，loading 释放 |
| updateSupport | false 时既有用户不变，显示失败明细；true 时真实更新并回读确认 |
| 请求失败后重试 | 对真实请求注入非法 updateSupport 触发后端 422；保留原始 Axios cause、请求配置和 Problem Details，反馈一次、文件保留、loading 释放；恢复参数后同文件重试成功并回读 |
| 请求中取消、重开 | 网关只暂存真实后端 200 响应；真实 XHR 被取消，reason 保留、无失败反馈；新导入仍保持 loading，最终只显示新结果 |
| 派发前关闭、点击终点 | 关闭同一事件周期内待执行的导入，没有派发请求；真实 422 经点击终点承接，无重复上报 |
| 卸载 | 暂存真实后端响应后卸载组件，XHR 取消；无迟到结果或失败提示 |
| 数据清理 | 本轮成功创建的 5 个带专用标记用户已通过业务删除接口清理，回读遗留数为 0；原有 1 条用户数据逐项比较不变 |

详见 [actual.json](evidence/2026-10-16-user-excel-import/actual.json)。旧成功／失败／进度与新操作的确定性乱序由组件延迟 Promise 回归锁定；真实请求取消由实际 XHR 和真实后端响应验证，两者不混称。

客户端取消不等于服务端回滚：本轮专门在后端已经提交后取消等待，确认记录仍存在，但前端不显示迟到结果。这些记录也已正常清理。没有修改后端导入事务或引入服务端任务取消协议。

## 范围与收尾

未变更后端、ZXUI、其他上传入口、重试策略、缓存、请求共享或编辑回读策略。保留原有工作区；只停止本轮启动的后端，保留 Docker MySQL、Redis 等原有服务。临时 Excel 已删除，验证账号已退出。文件 hash 与最终清理结果见 checks.json 的收尾记录。

计划阶段的路径核对、结构校验及后续执行记录见 [执行计划](../plans/2026-10-16-user-excel-import.md) 和 checks.json 的 planStageCheckpoint；完成结论以本报告的实际回归、真实 API 和独立审查为依据。

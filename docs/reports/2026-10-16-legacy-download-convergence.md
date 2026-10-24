# 旧下载入口收敛与代码生成 ZIP 验证

日期：2026-10-16。本轮只收敛旧下载入口，未提交 Git、未发布包。

## 调用链与责任

代码生成页的两个按钮调用 `handleGenTable → useOperation → $download.zip → GET /tool/gen/batchGenCode → GenTableService.batch_gen_code_services`，后端在内存中渲染并返回 ZIP。

旧 `src/plugins/download.js` 自己维护文件识别、JSON 错误解析、提示和一个全局 loading 句柄；错误与取消均被 catch 吞掉，`application/problem+json` 还可能被当成 ZIP 保存。它与已修好的 Excel 下载执行逻辑分开，不能共同管理全屏 loading。

真实消费者另有表单构建页的 `Download.saveAs`；因此保留 ZIP 和直接保存两个薄入口。已核对没有真实消费者的 `name/resource/printErrMsg` 分支移除。不是因为假设消费者保留兼容路径。

ZXUI 的二进制错误解码及业务 `downloadFromResponse` 已具备所需能力，本轮无需修改库或后端。责任在业务重复实现及页面事件边界。

## 实现

- 从 `src/utils/request.ts` 已有下载逻辑提取 `downloadFile(config, filename)`，统一请求、原生响应解析、保存、失败反馈和并行任务 loading 计数。原 `download(url, params, filename, config)` 继续按既有 POST 表单语义调用它。
- ZIP 薄入口委托同一流程，保持 GET，支持第三个请求配置参数透传 `signal` 等设置。复用 `downloadFromResponse → @zxio/http`，不再自行解析错误或保存错误正文。
- 下载 Promise 保留原始拒绝；主动取消不提示失败，普通失败只提示一次，保存异常也正常透传。loading 直到请求、解析和保存结束才释放，ZIP 和 Excel 共用计数。
- 审查发现 Vue 点击事件还需要承接 `useOperation` 产生的派生拒绝。两个 ZIP 点击入口改为 `handleGenTableClick`，在事件终点承接已经由下载入口反馈的失败／取消，避免 Vue 再上报未处理错误。`handleGenTable` 本身、下载函数和 `useOperation` 继续保留原始拒绝及 pending 语义；自定义路径生成分支保留原行为。

收益是消除两套下载执行流程，而不是新增下载框架。仅改三个生产前端文件及一份已有回归测试；未混入 HTTP 重试、通用日志／通知隔离或新的提交策略。

## 回归与检查

先增加 4 项 ZIP 回归，在原入口观察到 4 项预期失败，再修复通过：取消、原始错误、Problem JSON、ZIP/Excel 混合并发。随后增加事件边界回归，先确认取消会两次到达 Vue 错误处理器，再修复为零；同时确认操作函数直接调用仍拒绝原始错误。

| 检查 | 结果 |
| --- | --- |
| 定向回归 | 4 文件、44 项通过，新增 5 项；下载生命周期自身 9 项通过 |
| 全量 ESLint / type-check | 通过 |
| ZXUI 源码直连生产构建 | 通过，25.57 秒；既有构建提示保留 |
| 独立只读审查 | 无阻塞项，另行运行下载生命周期 9 项通过 |
| `git diff --check` | 通过 |
| changed 规范脚本 | 既有 `VersionList.vue` console 检查未通过；该文件 hash 未变 |
| 原有工作区保留 | 除本轮四个目标文件外，原有业务文件 hash 不变；ZXUI 原有文件 hash 全部不变 |

## 真实业务验证

执行真实代码生成页的操作声明、点击函数和业务 `useOperation`，经旧 ZIP 入口、共用下载流程、ZXUI 源码 `@zxio/http`、Axios 1.20.0 和 JSDOM XMLHttpRequest 访问本机 FastAPI/MySQL。使用 Python 校验实际 ZIP CRC、条目内容和实际用户 Excel。

| 场景 | 结果 |
| --- | --- |
| 页面批量生成 ZIP | 保存 `vfadmin.zip`，8 个非空文件、CRC 正确，pending/loading 释放 |
| 缺参 422 经旧 ZIP 入口 | 不保存错误正文，原始 Blob、Axios 错误及请求上下文保留，提示真实错误一次 |
| 页面失败后重试 | 失败后 pending 释放；随后真实生成并保存有效 ZIP |
| 请求进行中取消 | 真实 XHR 取消，原因保留，不提示失败、不保存，pending/loading 释放 |
| ZIP 和 Excel 并行 | ZIP 完成后遮罩继续覆盖 Excel；两者结束后关闭一次；ZIP 有效，Excel 为 1 行、13 列 |
| 取消 ZIP，同时 Excel 未完成 | 取消无提示，遮罩继续保持至 Excel 完成；只保存 Excel |
| ZIP 保存出口失败 | 原始保存错误透传，反馈一次，pending/loading 均释放 |
| 发送前已取消 | 安静拒绝，不保存，loading 释放 |
| 页面点击经 Vue 异步事件处理 | 真实失败被事件终点承接，没有再进入 Vue 未处理错误路径，pending 释放 |

共 9 个场景通过。为了可重复地验证取消和并发，部分请求经过本地临时网关：它实际请求后端并取得真实字节，只延迟向 XHR 返回。这里验证的是客户端请求取消和业务生命周期，不声称取消已在服务端完成的生成任务。

反馈、loading、文件保存出口由探针记录；请求和 ZIP/Excel 内容来自真实后端。没有 computer use、浏览器点击或视觉验收。

## 数据与运行收尾

现有 `sys_post` 生成配置的 options 不完整，后端会正确返回“请先完善生成配置信息”。本轮未修改这份现有配置，也没有把配置问题当作下载成功。

为验证成功链路，通过正常业务 API 将既有 `sys_config` 表结构导入为任务自有生成元数据，完善生成选项后执行 ZIP 生成，随后通过业务 API 删除该生成元数据及字段。只操作生成器元数据，没有修改实际业务表结构或数据。准备探针时曾因临时元数据缺少表描述被正常校验拒绝，补全测试元数据后通过，所有尝试均已清理。

最终生成器元数据与验证前完整比对一致，既有配置保留；正常登录、导入、更新、生成、删除及导出审计历史保留。验证会话已退出、临时 ZIP/Excel 已删除、本地网关已关闭，仅停止本轮启动的后端，保留原有 Docker/Redis。

证据：[真实结果](evidence/2026-10-16-legacy-download-convergence/actual.json)、[检查命令](evidence/2026-10-16-legacy-download-convergence/checks.json)、[工作区保留](evidence/2026-10-16-legacy-download-convergence/baseline-preservation.json)。

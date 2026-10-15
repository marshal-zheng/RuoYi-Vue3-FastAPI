# 用户 Excel 导出卡住：根因排查

日期：2026-10-15。本轮按用户最新要求只排查原因，没有修改业务、ZXUI 或后端运行代码。

## 已确认的根因

阻塞发生在后端流式响应阶段。`TokenSourceGuardASGIMiddleware` 为检查表单中的非法 token 来源，先读完请求体，再向下游回放。其 `_build_replay_receive` 在首次回放结束后，持续立即返回空的 `http.request`，既不等待，也不再委托服务器原始 receive。因此下游永远收不到真实的 `http.disconnect`。

本机 Starlette 0.45.3 的 StreamingResponse 在 ASGI spec < 2.4 时，并行执行文件发送和断连监听；当前 Uvicorn 0.35.0 的 HTTP scope 使用 spec 2.3。断连监听循环不断 await replay_receive，但该协程立即返回，没有真正挂起，导致事件循环持续执行空请求循环。文件发送任务无法正常推进，客户端超时与断开也无法终止它。

源码定位：

- `ruoyi-fastapi-backend/middlewares/token_source_guard_middleware.py:36`：预读表单；`:45`：替换 receive；`:108–115`：问题回放实现。
- `ruoyi-fastapi-backend/modules/system/api/user_controller.py:564–567`：Excel 字节生成后打印“导出成功”，随后返回 StreamingResponse。
- 当前安装的 `starlette/responses.py:231–235`：断连循环；`:252–268`：当前 ASGI 版本对应的任务执行分支。

## 真实请求证据

启动原项目开发后端，仅通过临时 Python sitecustomize 注册 faulthandler 信号抓栈，没有替换中间件或修改处理逻辑。使用独立 Node fetch 登录并调用真实接口，全程绕过 Axios、ZXUI 和业务前端。

| 对照 | 结果 |
| --- | --- |
| 同一 `/system/user/export` 发送 JSON `{}`，走默认筛选参数 | 181 ms 返回 200、5326 字节；openpyxl 可正常读取，1 张表、含表头 2 行、13 列 |
| 正式表单请求 `page=1&pageSize=10`，不带 Idempotency-Key | 2503 ms 客户端超时；后端已输出“导出成功” |
| 超时后访问 `/docs` | 601 ms 再次超时，说明同一事件循环已受影响 |
| 工作进程 CPU 与两次抓栈 | CPU 达 100%；实际热栈为 `replay_receive → listen_for_disconnect → StreamingResponse.__call__` |

JSON 请求只作为隔离 token-source 表单预读的因果对照；它不会按正式 Form 契约接收筛选条件，不能作为生产修复方案。此对照确认 Excel 生成及响应发送在未触发表单回放缺陷时能完成。

[真实结果](evidence/2026-10-15-user-excel-export-diagnosis/actual-results.json) · [真实热栈](evidence/2026-10-15-user-excel-export-diagnosis/actual-hot-stack.txt)

## 隔离复现与关联范围

使用本机安装的中间件及 Starlette，去掉数据库、登录和 Excel 生成，仅返回 10 字节流式内容；每个案例在独立子进程运行，忙循环由父进程超时终止。

| 组合 | 结果 |
| --- | --- |
| 无 token-source guard，表单＋流式响应 | 3 ms 完成 |
| 有 guard，表单＋流式响应 | 已读完请求体，随后卡住；1.8 秒后终止，热栈在 guard 回放函数 |
| 有 guard，JSON＋流式响应 | 3 ms 完成 |
| 有 guard，表单＋普通 JSON 响应 | 完成 |
| 幂等中间件，不带幂等键，JSON＋流式响应 | 2 ms 完成 |
| 幂等中间件，带幂等键，JSON＋流式响应 | 同样卡住，热栈在幂等中间件回放函数 |

`idempotency_middleware.py:233–240` 有相同缺陷，但真实用户导出请求未带幂等键，真实栈也明确经过该中间件 `:98` 的直通分支。它是已复现的同类缺陷，不是此次请求的直接触发点。普通 JSON 错误响应能结束，因此之前非法分页 422 验证成功，并不能证明合法流式导出正常。

[隔离结果](evidence/2026-10-15-user-excel-export-diagnosis/minimal-results.json)

## 后续最小修复边界

应修复后端 receive 回放的生命周期：缓存请求体只回放一次，后续读取委托原始 receive，让真实服务器负责等待与断连事件；不得用立即伪造断连或反复返回空请求替代。相同错误的两个回放点应保持一致，保留认证来源检查与幂等行为。

不需要改 Axios/ZXUI、提高超时时间、修改 Excel 生成或改变用户导出 Form 契约。修复时只需围绕流式响应、真实断连以及既有安全/幂等行为锁定必要回归，再跑正式表单的真实用户 Excel 导出。

本轮未实施修复，也未新增仓库测试；只增加本报告和脱敏证据。已停止本轮启动的开发后端及卡住的工作进程，原有 MySQL/Redis 保持。临时导出文件已删除，证据不含 token、认证头或用户明细。

后续已按用户授权完成两处最小修复，正式表单用户 Excel 导出通过；修复与验证见[后续报告](2026-10-15-user-excel-export-fix.md)。本报告保留修复前的排查记录。

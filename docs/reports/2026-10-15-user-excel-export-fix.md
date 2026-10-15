# 用户 Excel 导出：中间件最小修复与验证

日期：2026-10-15。承接[根因排查](2026-10-15-user-excel-export-diagnosis.md)，本轮仅修复两个中间件的请求体回放生命周期。

## 最终改动

- `middlewares/token_source_guard_middleware.py`：缓存表单只回放一次，之后 await 原始 receive；用 None 区分未预读与已读完的空表单，确保空请求体也能完整回放。
- `middlewares/idempotency_middleware.py`：缓存请求体只回放一次，之后 await 原始 receive。
- 在两个既有测试文件各增加一个参数化回归，覆盖非空/空请求体、回放后的真实等待及原始断连事件传递。

生产代码变更共 9 行新增、7 行删除，没有增加共享抽象。安全检查规则、排除路径、认证权限、幂等键/指纹/锁/缓存/冲突处理均未改动。未修改用户导出 Form 契约、Excel 生成、响应类型、Axios、ZXUI 或业务前端。

修复保留服务器真实的等待及断连语义：既不反复立即返回空请求，也不提前伪造断连，因此 Starlette 的文件发送任务可以推进，客户端断开仍能被流式响应观察到。

## 回归与复查

4 个新增参数化案例先观察到全部失败：非空请求体回放后立即返回假事件，空表单在原实现中被消费后无法回放。最小修复后两个测试文件 16 项通过。

同时验证既有安全检查、幂等相同负载重放/不同负载冲突、并发重试只执行一次、用户隔离、超限直通及锁归属；中间件装配和 CSRF 兼容用例也通过。命令：

```bash
cd ruoyi-fastapi-backend
./venv/bin/python -m pytest -o addopts='' \
  tests/unit/middlewares/test_token_source_guard_middleware.py \
  tests/unit/middlewares/test_idempotency_middleware.py \
  tests/unit/middlewares/test_handle_middleware.py \
  tests/unit/middlewares/test_csrf_guard_middleware.py -q
```

结果：21 项通过。修改的生产文件 compileall 通过，git diff --check 通过。只读复查没有发现待处理的 P0/P1/P2 问题，复查者独立复跑两个目标测试文件，16 项通过。

上轮隔离探针的 6 个场景本轮全部完成，包含此前必定卡住的“安全 guard＋表单＋流式响应”和“幂等键＋JSON＋流式响应”，均为约 3 ms。[隔离证据](evidence/2026-10-15-user-excel-export-fix/minimal-results.json)

## 正式用户 Excel 导出

启动原项目开发后端，连接既有 Docker MySQL 与 Redis。通过真实业务 `download('/system/user/export', ...)`、HTTP 适配及 Axios 1.20.0 发出正式 `application/x-www-form-urlencoded` 请求；没有使用上轮诊断时的 JSON 对照替代正式接口契约。

源码直连和安装包模式分别在独立进程完成 7 项检查：

| 检查 | 结果 |
| --- | --- |
| 登录与用户信息 | admin 登录、查询和退出正常 |
| `page=1&pageSize=10` 正式用户导出 | 分别 79 ms / 78 ms 完成；5327 / 5326 字节，保存入口收到原响应字节，无失败提示，loading 关闭一次 |
| 带幂等键首次导出及重放 | 两次文件字节一致；按请求 trace 关联后端生成日志，首次执行 1 次、重放执行 0 次；两次 loading 都结束 |
| 同键改为 `page=2` | 保持 409/40901 冲突，原 Blob 可查，一次反馈，loading 结束 |
| query/cookie/form 非法 token 来源 | 三种请求均保持 HTTP 400、错误码 10013 |
| 空表单用户导出 | 200，正常返回 XLSX，未丢失已读完的空请求体 |
| 导出后的服务可用性 | `/docs` 与鉴权查询均可及时完成；工作进程未出现持续满核，收尾时 CPU 0.3% |

openpyxl 实际读取两种模式保存入口收到的文件，均为 1 张工作表、含表头 2 行、13 列，包含 admin 用户记录；不仅检查 ZIP 文件头。临时工作簿验证后删除，证据不保存用户明细。

验证使用 JSDOM XMLHttpRequest 连接真实 FastAPI :8088，只替换反馈/loading/file-saver 入口；没有 computer use、浏览器点击或系统保存对话框验收。仅执行登录、查询、导出及退出，没有修改用户或其他业务记录。

[源码证据](evidence/2026-10-15-user-excel-export-fix/source-actual.json) · [安装包证据](evidence/2026-10-15-user-excel-export-fix/installed-actual.json)

## 质量检查的既有基线

已运行 `bash .cursor/skills/backend-conventions/scripts/validate.sh --changed`，并使用后端 venv 中的 Ruff。脚本仍因既有基线问题失败：

- 修改前后均为 62 条 Ruff 诊断；按文件、规则和消息归一化比较，新增诊断为 0。
- 修改前后相同两个文件不满足当前格式规则：幂等中间件及其既有测试文件。
- Guardrails 检查全部通过，没有新增 print、eval/exec、控制器 SQL 或宽泛异常捕获。

为保留最小修复，没有批量迁移旧类型注解或重排整个幂等文件。不能据此声称全量 lint/format 通过。[质量摘要](evidence/2026-10-15-user-excel-export-fix/quality-summary.json)

## 范围与运行收尾

本轮只修改上述两个中间件及对应测试，其他 HTTP 优化未混入。没有发布 npm、提交 Git 或修改数据库结构。已正常停止本轮启动的开发后端，MySQL/Redis 保持原状态；本轮未再出现需要强杀忙循环工作进程的情况。

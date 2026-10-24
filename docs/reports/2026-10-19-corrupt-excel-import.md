# 损坏 Excel 用户导入错误修复与真实页面验收

状态：修复、定向回归、真实页面验收及数据清理完成。保留原有改动，未提交或推送。

## 根因与处理

用户导入在进入逐行处理前直接调用 `pandas.read_excel`。空文件、改名文本、损坏 ZIP/XML 等解析异常越过了业务错误边界，被全局异常处理转换成 500；失败时上传句柄也没有按原代码执行关闭。

现在由用户服务内的 `_read_user_import_workbook` 负责文件解析边界：校验 XLS/XLSX 扩展名，使用对应引擎，捕获明确的解析异常，返回现有 `ValidationException` 契约：**HTTP 422、errorCode=10005、errors[].field=file**。用户看到“Excel 文件无法读取，可能已损坏或加密，请使用未加密的导入模板重新保存后重试”。错误格式和现有前端反馈直接兼容，无需修改页面或全局异常处理。

读取和解析以 `finally` 保证关闭文件；读取失败、缺依赖或内部 RuntimeError 保留原有服务错误分类。实际测试发现工作簿 XML 可能由 lxml 解析，工作表 XML 则可能由标准库解析，两类 XML 语法异常均覆盖。解析成功但缺少必需模板列时，也在进入用户写入前返回明确的文件校验错误；原有逐行导入结果保持。

同时发现页面承诺支持 XLS，但 MySQL/PostgreSQL 两份依赖清单均缺少 xlrd，正常旧格式会因缺引擎失败。两份清单增加 `xlrd==2.0.2`，本地 venv 已安装；XLSX 沿用 openpyxl，XLS 使用 xlrd。这是 pandas 的既有成熟引擎方案，不增加新的导入框架。依据：[pandas 2.2.3 read_excel 引擎说明](https://pandas.pydata.org/pandas-docs/version/2.2/reference/api/pandas.read_excel.html)、[xlrd 官方支持范围](https://xlrd.readthedocs.io/en/latest/)。

## 验证

- 后端 **30 项通过**，其中新增文件包含 13 项解析边界回归：真实空文件、改名文本、截断 ZIP、普通 ZIP、损坏工作簿/工作表 XML、截断 BIFF8 XLS、错误模板，以及正常 XLS/XLSX、逐行校验、内部错误不被误分类和读取失败关闭文件。真实 XLS 测试夹具由 xlwt 1.3.0 一次性生成，运行测试不需要 xlwt。
- 前端源码直连的现有 UserImportDialog **8 项通过**。前端实现未改动。
- 受影响 Python 实现和新增测试 Ruff 零诊断，格式检查通过。上一轮会话修复的 15 个实现/测试文件 SHA256 全部保持。

运行命令：

```bash
# ruoyi-fastapi-backend
./venv/bin/python -m pytest -o addopts='' tests/unit/services/test_user_import.py tests/unit/services/test_user_service.py -q
./venv/bin/ruff check modules/system/application/services/user_service.py tests/unit/services/test_user_import.py
./venv/bin/ruff format --check modules/system/application/services/user_service.py tests/unit/services/test_user_import.py
# ruoyi-fastapi-frontend
./node_modules/.bin/vitest run --config ../docs/reports/evidence/2026-10-19-upload-stream-session/source.vitest.config.mts tests/unit/components/UserImportDialog.test.ts
```

## 真实页面结果

沿用本地 MySQL/Redis、8088 后端和 80 前端，启用 ZXUI 源码直连。使用独占验收账号，在真实用户管理页面下载模板、选择文件并点击确定，没有使用临时页面夹具。

| 操作 | 实际结果 |
| --- | --- |
| 提交改名文本 XLSX | 422，明确中文文件错误；窗口和所选文件保留，确定按钮恢复可用，“更新已有用户”未勾选 |
| 提交结构损坏的 XLSX 工作簿 XML | 422，按同一契约反馈，无 500 |
| 提交截断 XLS | 422；1100×800 下提示、文件列表及确定/取消按钮可见 |
| 移除坏文件，换下载模板生成的有效 XLSX 重试 | 仅一次成功导入，200、成功 1 条；回读用户 ID 129、账号和邮箱一致 |
| 重开后选择有效 BIFF8 XLS | 仅一次成功导入，200、成功 1 条；回读用户 ID 130 和账号一致 |
| 选择文件、勾选更新后取消，再次打开 | 文件数 0，更新选项 false，无请求写入 |

正式验收共有 7 次导入提交：5 次预期 422（含截图复核重复提交）、2 次 200，没有 500。全部损坏文件提交后、正常导入前，用户总数仍为原管理员和验收账号共 2 个。成功后分别核对落库身份，没有修改已有用户。

视觉检查覆盖 1440×1000 与 1100×800。[错误反馈截图](evidence/2026-10-19-corrupt-excel-import/01-corrupt-file-error.png)、[小视口损坏 XLS](evidence/2026-10-19-corrupt-excel-import/03-corrupt-xls-small.png)、[正常 XLS 结果](evidence/2026-10-19-corrupt-excel-import/05-valid-xls-result.png)均已检查。工作簿 XML 的小视口截图还保留了文件移除过渡状态。开发后端重载期间曾有一次无响应请求；服务就绪后重载页面开始正式验收，正式阶段 pageerror 为空，未将准备阶段错误混入导入结果。

## 清理与证据

核对用户名和 ID 后删除了本轮账号 128、129、130，API 中本轮账号剩余 0；验收与清理管理员会话均 logout 204，已知验收会话键剩余 0，自身 CSRF 已清理。自建浏览器/API contexts 已关闭；本地 MySQL/Redis 保留运行，前端与后端 /docs 均为 200。没有普通上传文件或临时业务页面需要残留清理。

原文件均先保存独立基线，本轮 5 个实现/依赖/测试文件的摘要及文本增量补丁已保存，包含用户服务中先前未提交的改动而不覆盖它们。证据不包含 token、Cookie 或 Authorization header。自动核对 20 项通过：[汇总](evidence/2026-10-19-corrupt-excel-import/verification-summary.json)、[页面/API 结果](evidence/2026-10-19-corrupt-excel-import/browser-acceptance.json)、[清理](evidence/2026-10-19-corrupt-excel-import/cleanup.json)。

本轮处理损坏或错误格式工作簿的错误分类与恢复流程，没有实现加密工作簿解密，也没有改变现有逐行校验和更新已有用户策略。

# 字典数据分页排序稳定性修复

日期：2026-10-16。本轮只修字典数据分页排序；未提交 Git、未发布包。

## 根因与排序契约

问题在业务后端，ZXUI、前端页码和导出参数无需调整。

`DictDataRepository.paginate_with_filters` 原先声明 `dict_sort ASC`。继续检查 `PageUtil.paginate` 发现，它会通过 `_prepend_update_time_order` 前置 `update_time DESC`，然后才执行 `(page - 1) * page_size` 的 OFFSET 和 LIMIT。因此既有有效排序是：

```sql
ORDER BY update_time DESC, dict_sort ASC
```

多条记录的更新时间和排序号相同时，顺序没有唯一约束。不同 LIMIT/OFFSET 下，相同排序值的记录可以改变顺序，导致分页重复和漏项；已有 DISTINCT 无法解决跨请求重叠。这与 [MySQL 官方说明](https://dev.mysql.com/doc/refman/8.0/en/limit-optimization.html) 一致：需要在 ORDER BY 中补充能确定顺序的列。

列表和 Excel 导出均调用 `DictDataService.get_dict_data_list_services → DictDataRepository.paginate_with_filters → PageUtil.paginate`。导出复用同一查询，只使用既有第 1 页、每页 10000 条的上限。

## 修复

仅修改后端 Repository 一行，追加非空唯一主键 `dict_code ASC`，实际 SQL 为：

```sql
ORDER BY update_time DESC, dict_sort ASC, dict_code ASC
```

保留既有两层排序优先级、NULL 排序、筛选、分页算法、DISTINCT 和导出上限。选择器用的 `find_by_type` 不涉及本次分页路径，未改；未引入游标、缓存、索引或共享分页器重构。

该方案在定义排序的业务查询处补足唯一顺序，列表和导出同时受益。没有把领域排序规则放进 ZXUI，也无需在所有分页调用点加新配置。

## 真实复现与修后验证

先在原后端运行真实探针，再修改、重启同一后端并重跑。使用现有 84 条字典数据，没有新增、编辑或删除字典记录。

修前每页 1 条遍历 84 页：得到 84 次记录，但仅 52 个唯一编号，漏了 32 条；13 个不同编号重复出现，共 32 次重复。分页记录和实际 Excel 的集合、顺序不一致，验收按预期失败。

修后通过生产字典数据页面 handler、ZXUI 源码 GridList 和 `@zxio/http`、业务 API/下载模块，经 JSDOM XMLHttpRequest 访问本机 FastAPI/MySQL；通过 openpyxl 读取实际 Excel 的字典编号，比较完整集合及顺序。

| 场景 | 每页条数 | 总条数 / 主遍历页数 | 重复 / 漏项 | Excel 顺序 |
| --- | --- | --- | --- | --- |
| 全部类型 | 1 | 84 / 84 | 0 / 0 | 一致 |
| 全部类型 | 2 | 84 / 42 | 0 / 0 | 一致 |
| 全部类型 | 10 | 84 / 9 | 0 / 0 | 一致 |
| 全部类型 | 20 | 84 / 5 | 0 / 0 | 一致 |
| 再次每页 1 条完整遍历 | 1 | 84 / 84 | 0 / 0 | 一致 |
| 指定字典类型 | 1 | 10 / 10 | 0 / 0 | 一致 |
| 正常状态筛选 | 3 | 84 / 28 | 0 / 0 | 一致 |
| 标签筛选 | 1 | 3 / 3 | 0 / 0 | 一致 |
| 清空类型、标签、状态 | 7 | 84 / 12 | 0 / 0 | 一致 |
| 无匹配标签 | 1 | 0 / 1 | 0 / 0 | 一致 |

共 10 组、278 页主遍历；另对各组重访首页／中间页／末页，结果不变，并验证越界页为空、total 正确。每组均保留原有效排序，并与“原排序后追加唯一编号”的参考顺序一致。验证前后全部字典数据内容未变。

反馈、loading、保存入口由探针记录；实际请求和 Excel 来自真实后端。没有 computer use、浏览器点击或视觉验收。验证针对数据不变时的稳定分页，不宣称跨请求期间并发增删也具备快照一致性。

## 检查与收尾

- 现有字典服务回归：9 项通过。本次未新增镜像 ORDER BY 实现的 mock 测试，以真实修前失败／修后通过验收作为主要证据。
- 生产 Repository 的 MySQL 方言 SQL 对比：仅新增最终唯一排序键，既有排序、过滤、OFFSET/LIMIT 不变。
- 独立只读审查：无阻塞项，另核对 4 组过滤场景的有效 SQL。
- `git diff --check` 通过；后端 changed 规范脚本 guardrails 通过。脚本 PATH 未找到 Ruff，因此额外使用 venv Ruff 检查：原文件 40 项既有诊断，修后仍为相同 40 项，没有新增，未混入整文件格式修复。
- 工作区 hash 核对：原有业务文件仅本次 Repository 改变，ZXUI 原有文件全部不变。
- 验证会话均已退出，临时 Excel 已删除，仅停止本轮启动的后端，保留原有 Docker/Redis 服务。未新增领域数据；正常登录／导出审计记录保留。

证据：[修前结果](evidence/2026-10-16-dict-pagination-order/red.json)、[修后结果](evidence/2026-10-16-dict-pagination-order/green.json)、[有效 SQL](evidence/2026-10-16-dict-pagination-order/sql-comparison.json)、[检查命令](evidence/2026-10-16-dict-pagination-order/checks.json)、[工作区保留](evidence/2026-10-16-dict-pagination-order/baseline-preservation.json)。

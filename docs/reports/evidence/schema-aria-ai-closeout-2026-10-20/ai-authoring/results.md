# Schema AI 作者对照结果

四次预定 ABBA 调用均完成，原样生成代码均通过对应版本类型检查、业务行为检查和独立人工审查。这个普通 CRUD 样本没有证明当前 schema 更省 token：当前版平均总 token 增加约 **5.22%**，两版首次质量成功率均为 **2/2**。没有人工修补生成代码，也没有模型重试。

## 实际 usage

固定模型 `gpt-6-astra`、推理 `xhigh`、CLI `0.163.0-alpha.10.2`。每次独立空目录，只有一轮生成。input、output、reasoning 和缓存值均来自原始 `turn.completed.usage`；reasoning 已包含在 output 中，不能再相加。

| 样本 | input | cached input | uncached input | output | 其中 reasoning | total | 秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 baseline | 15,571 | 0 | 15,571 | 5,611 | 4,142 | 21,182 | 171.176 |
| B1 current | 17,320 | 0 | 17,320 | 3,706 | 2,225 | 21,026 | 113.874 |
| B2 current | 17,318 | 0 | 17,318 | 4,957 | 3,462 | 22,275 | 148.996 |
| A2 baseline | 15,569 | 0 | 15,569 | 4,400 | 2,900 | 19,969 | 139.743 |
| baseline 均值 | 15,570 | 0 | 15,570 | 5,005.5 | 3,521 | 20,575.5 | 155.4595 |
| current 均值 | 17,319 | 0 | 17,319 | 4,331.5 | 2,843.5 | 21,650.5 | 131.435 |

四次 cache write input 均为 0。四次实验合计 **84,452 tokens = 65,778 input + 18,674 output**，其中 reasoning 为 12,729，已计入 output；总运行时间为 573.789 秒。不含先前 smoke，也不按未知账户价格推算费用。

| 当前版减 baseline | input / uncached | cached | output | reasoning 子集 | total | 秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 第 1 对 B1−A1 | +1,749 | 0 | −1,905 | −1,917 | −156 | −57.302 |
| 第 2 对 B2−A2 | +1,749 | 0 | +557 | +562 | +2,306 | +9.253 |
| 均值差 | +1,749 | 0 | −674 | −677.5 | +1,075 | −24.0245 |

当前版平均 output 更少、耗时更短，但第二对方向相反。只有一个任务、每版两次重复，不能据此声称稳定减少推理、稳定加速或推广到复杂企业表单。完整 README 和公共类型一起投喂时，当前版输入更长；现有类型与架构收益不能直接等同于 token 节省。

## 质量与审计

- 四次首次生成全部通过：baseline **2/2**、current **2/2**；独立修正后 checker 各 **30/30**，人工审查全部通过。验证范围为真实公开声明、内存业务行为和 SFC 静态契约，没有运行浏览器或完整表单引擎。详见 [质量分析](quality-analysis.md)、[quality-summary.json](quality-summary.json) 与每个 run 的 `manual-review.md`。
- 原始 checker 把 `col={span:24,md:12}` 在 lg/xl 的累计断点语义误判。原始结果保留（A1/A2 为 29/30，B1/B2 为 30/30）；复制 checker v2 修正评分器并补 oracle，四份统一重评。没有改业务要求、模型输出或通过标准，详见 `checker/freeze-v2.json` 和质量报告。
- 原始 runner 的 `protocol_valid` 为 **0/4**：它把 CLI 启动时的 experimental-feature 提示误计为工具 item。所有 raw 和原始字段保持不变。
- [协议补充 1](protocol-amendment-1.md) 记录真实冻结时间，限定仅豁免第一个 `turn.started` 前、完整事件精确相同的这条 CLI 告警，四次同待遇；所有真实工具及其他错误仍不豁免。冻结时 A1 输出已刚出现，但尚未评分。审计后 `audited_protocol_valid` 为 **4/4**，实际工具调用 **0**。
- 结束后再次核验：四份 raw SHA、冻结输入、runner、原协议和 CLI 二进制均未改变。未覆盖上一轮失败实验。

## 可支持的结论

这次完成了真实模型 usage 与代码正确性的对照，结果支持“当前版仍能正确完成同一普通 CRUD”，不支持“schema 升级已经节省 token”。后续最值得验证的是按任务提供公开接入材料，减少每次加载完整架构文档；应建立独立的新协议后比较，不能删除本轮不利数据或把更短代码当作 token 收益。

原始数据与可复算结果：[manifest](manifest.json)、[usage-summary](usage-summary.json)、[协议](protocol.md)、[重算脚本](summarize.py)。所有四次调用的 argv、stdout JSONL、stderr、final JSON、原始运行结果和独立审计结果均在 `runs/`。

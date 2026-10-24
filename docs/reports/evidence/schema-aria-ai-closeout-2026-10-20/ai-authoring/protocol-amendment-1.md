# 协议补充 1：CLI 启动告警的事件分类

冻结时间：2026-10-20T09:19:15.951559+00:00。正式调用已经开始，冻结时已出现的 final.json：["runs/01-baseline/final.json"]。

冻结 runner 把所有非消息/推理 item 计为工具；本次 CLI 在 turn.started 之前发出如下预检告警，没有执行模型工具：

```text
Under-development features enabled: skip_host_skill_discovery. Under-development features are incomplete and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in /Users/hqz/.codex/config.toml.
```

该完整事件的规范 JSON SHA-256：`e0669ec64b87edf4af5c17fcb31bcb6eff51aa7bcfff15e6c2ac3986008a21cd`。原始行 SHA-256：`3feb090f9743bb4462ec40c1c5f6f8ca04f398ac0164d6925cdbd26c29d0d02e`。

四个预定样本一律适用相同规则：仅在第一个 turn.started 前出现、且完整解析事件与 JSON 文件中 exempt_event 完全相同的这条告警可豁免。其他错误、工具调用、畸形事件仍不合格。

原 protocol_valid、tool_item_count、runner、协议与所有 raw 保留不改；另给 audited_protocol_valid 和豁免明细。没有更改生成任务、质量标准、模型设置或样本，也不允许重跑。这是客户端事件分类器的修正，不是依据生成效果调整验收。

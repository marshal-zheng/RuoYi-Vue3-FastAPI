# 04-baseline 原样输出审查

结论：本固定任务的一次生成通过。v2 自动检查 30/30；人工审查未发现任务遗漏或作者缺陷。

- 使用旧版支持的非泛型 Save/SchemaFormInstance，以及 RuleFor<PostValues>[]；公开声明检查通过，没有类型抑制。
- col={span:24,md:12} 在 md 及更宽屏幕为两列，备注 span24 整行；原 checker 对 lg 的误报由统一 v2 正确处理。
- DTO 逐项收窄 Values | PostValues，拒绝空白、长度超限、非整数或负数、非法状态和非字符串备注；白名单和可信 postId 参数保持隔离。
- 错误映射采用 Map 的五个明确键，未知及空字段统一为旧契约的 field 空字符串，原消息保留。
- initial 只在 setup 中作为初始快照创建，没有后续编辑写入或 v-model；save 同样只创建一次。表单编辑值、校验和提交状态属于 SchemaForm。
- 保存/恢复使用公开 submit/reset，pending 禁用按钮；服务仅调用 api.write 并原样转发 signal，无额外 GET、HTTP 实现或私有 API。

范围：真实版本公开声明、领域函数与原生校验、内存中的宿主组件接线。未执行浏览器或完整引擎交互；不据此推广为复杂业务的普遍成功率。authored/ 是 final.json 两个源码字段的逐字提取，没有修补。

# 01-baseline 原样输出审查

结论：本固定任务的一次生成通过。v2 自动检查 30/30；人工审查未发现任务遗漏或作者缺陷。

- RuleFor<PostValues>[] 检查字段名；五个规则包含空白、长度、非负整数和状态枚举校验，排序 0 被保留。
- 原生 col={span:24,md:12} 在 md 及以上为半宽；remark col={span:24} 为整行。初始 checker 的 lg 回退是评估器错误，已由保留原结果的 v2 累积断点校验修正。
- DTO 逐项收窄 Values | PostValues 并显式构造五字段白名单；postId 只来自 createPostSave 参数，0 不会丢失。
- 服务端 snake_case 映射及未知/空字段消息按旧 FieldIssue.field 契约处理；使用 switch，不存在对象原型属性误取。
- 组件 setup 中只创建一次 save；initial 是冻结输入快照，未维护第二份可编辑值。SchemaForm 通过公开 ref.submit/reset 操作，pending 禁用两个按钮。
- 仅一次 api.write(dto,原signal)，无额外 GET、私有 API、类型抑制或业务页面壳。

范围：真实版本公开声明、领域函数与原生校验、内存中的宿主组件接线。未执行浏览器或完整引擎交互；不据此推广为复杂业务的普遍成功率。authored/ 是 final.json 两个源码字段的逐字提取，没有修补。

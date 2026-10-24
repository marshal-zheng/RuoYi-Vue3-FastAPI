# 02-current 原样输出审查

结论：本固定任务的一次生成通过。v2 自动检查 30/30；人工审查未发现任务遗漏或作者缺陷。

- RuleFor<PostValues>[] 检查字段名；五个规则覆盖空白、长度、非负整数和状态枚举，排序 0 被保留。
- columns=2 和 remark.fullWidth=true 使用当前公开布局契约，避免逐字段重复 col。
- DTO 从 unknown 检查属性存在及业务合法性后显式构造五字段白名单；postId 只来自可信参数，0 被保留。
- FieldIssue 使用明确的五种后端字段分支；未知/空字段返回仅 message，按当前契约进入摘要。
- Save<PostValues> 与 SchemaFormInstance<PostValues> 正确使用公开泛型；props.initial 交给唯一编辑值 owner，未创建可写副本。
- 保存/恢复通过公开 submit/reset，pending 禁用按钮；setup 中仅创建一次 save，仅调用 api.write 并原样转发 signal。ZxSelect 的 options 是 ZXUI 已有公开能力，宿主主题由任务前置条件保证。

范围：真实版本公开声明、领域函数与原生校验、内存中的宿主组件接线。未执行浏览器或完整引擎交互；不据此推广为复杂业务的普遍成功率。authored/ 是 final.json 两个源码字段的逐字提取，没有修补。

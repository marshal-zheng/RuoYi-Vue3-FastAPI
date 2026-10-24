# 01-baseline 完整文档组原样输出审查

结论：固定任务首轮通过。冻结评估器30/30，人工未发现遗漏或作者缺陷。两组API均为current。

- 当前API的RuleFor<PostValues>、Save<PostValues>与SchemaFormInstance<PostValues>均正确；baseline标签仅指完整文档组。
- 原生规则覆盖空白/长度/非负整数/状态枚举，textarea与columns=2/fullWidth布局满足固定任务。
- DTO即使参数静态标注PostValues仍逐项运行时校验，白名单只含五个字段，postId仅来自可信参数且保留0。
- 后端字段采用switch明确映射，未知或空标识只保留message进入摘要，无对象原型属性误取。
- props.initial交给SchemaForm，setup仅创建一次save，无第二份可编辑draft/v-model、watch同步或私有引擎调用。
- 按钮通过公开submit/reset且pending禁用；唯一请求为api.write，signal原样转发，无额外GET或HTTP实现。

authored/ 为final.json源码字段的逐字提取，未修补。检查覆盖真实声明、领域函数、原生校验与内存宿主接线，不冒充浏览器或完整引擎验收。

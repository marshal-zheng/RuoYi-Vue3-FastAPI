# 真实业务验收状态

当前状态：**尚未完成真实界面验收**。用户已明确由自己手工测试界面并要求代码先合回源分支；本轮没有 computer use 授权，也没有调用该能力。下表的自动化证据属于 DOM/组件或 HTTP/数据库层级；它们不等于用户在浏览器中的真实业务操作。下表逐行交接用户手测；代码交付和完整 spec 验收分别记录。

| 实际入口 | 自动化证据 | 真实界面状态 |
| --- | --- | --- |
| 用户 UserFormDialog | mounted 生命周期、七资源 HTTP JSON 保存/遗漏/清空/拒绝非法、状态更新保留 | 待验收 |
| 角色 RoleFormDrawer | mounted 抽屉读取/提交、HTTP、关系/事务 123 项组的一部分 | 待验收 |
| 岗位 PostDlg / Formily | 真实 SchemaForm + RemarkEditor 对象/null、回填/格式 dirty、composition submit blocking；隐藏链接恢复另有库回归 | 待验收 |
| 字典类型 DictDlg | mounted 读取失败/重试、HTTP、Excel 字符串单元格 | 待验收 |
| 字典数据 data.vue | mounted 路由/详情、HTTP、精准缓存重建、Excel | 待验收 |
| 参数 ConfigDlg | mounted 生命周期、HTTP、键值读取与 JSON 备注分离 | 待验收 |
| 生成器 basicInfoForm | 配置 HTTP 编辑/遗漏/清空、异步读取保护；无虚构的新建表配置入口 | 待验收 |
| 显式 remark 产物 | 真正 Python 执行/ORM 探针、Vue SFC 编译、Vue2 拒绝、主子按需编辑静态核对 | 待验收 |

各入口都必须检查保存重开、清空与撤销、A 格式保持、前后空白与 Unicode、保存失败保留、切换记录/撤销隔离、读取失败不覆盖和成功权威回填。分别覆盖原生弹框、抽屉、Formily 和生成器取消保护；另验中文输入法、键盘焦点/快捷键、外部粘贴/资源拒绝、只读/禁用、明暗主题、density 和链接 portal 的归属/焦点。

列表/选择器、只读安全链接、无备注与错误区分、Excel 实际下载与现有导入、字典/配置消费、通知正文、任务字符串备注及非备注 JSON 还需在候选应用中抽验。没有界面证据的项目全部保留待验收，不由构建或截图文件存在推定通过。

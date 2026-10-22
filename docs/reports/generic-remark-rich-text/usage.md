# 通用备注使用与接入

范围是 sys_user、sys_role、sys_post、sys_dict_type、sys_dict_data、sys_config、gen_table 的 remark。菜单、任务、通知备注及通知正文、工程、协议、设备、仿真内容不在本轮。旧正文 Editor 仍有消费者，继续保留。

编辑支持段落、软换行、粗体、斜体、三级有序/无序列表、安全链接、撤销和重做。图片与附件不上传；表格粘贴为制表符分隔的行，代码按文字段落导入，不能表示的资源有提示。只读内容使用 ZXUI 安全渲染，列表使用最多 160 个 grapheme cluster 的摘要。

前端分别从 `@/components/ui/Remark/RemarkEditor.vue`、`@/components/ui/Remark/RemarkDisplay.vue` 和 `@/components/ui/Remark/contract.ts` 使用 RemarkEditor、RemarkDisplay 与 readRemark；公开库组件为 `@zxio/text-editor` 的 ZxTextEditorField，文档接纳函数来自公开 `/core`。业务只维护权限、记录与会话、布局和提交。原生表单使用真实 ElForm 与既有 FormDialog/FormGrid，Schema 表单通过真实 Formily binding 注册对象字段，`composite:true, group:false`，由 SchemaForm 单独管理编辑值。不要把编辑器 ref 冒充 FormInstance，不维护另一份文档。

`remark` 唯一权威值是完整 Document v2 对象或 null：version 2，body.format=json，assets/annotations 为空，meta 仅 stable-block-identity/v2，所有可寻址块有唯一合法 ID。不要 JSON.stringify 后写入，不接受 HTML 字符串或裸正文树。写入遗漏 remark 保留原值，显式 null 清空；单一空段落归一为 null，空格与多个空段落保留。SQL 层保存 SQL NULL，不保存 JSON null。

`remarkText` 仅服务端派生，不能写入；提交只包含写 DTO。正文最多 5,000 Unicode code points，compact UTF-8 JSON 最多 262,144 字节、2,000 节点，列表深度 3、树深度 12、原始容器深度 32，链接 2,048 code points。输入超限保留内容并阻止提交。链接仅 http/https/mailto/tel，不接受相对或裸域名持久值；链接编辑框可将用户输入的裸域名明确补全为 https。禁止凭据、空白、控制字符、反斜杠和危险协议。

Excel 是纯文本交换：保留文字、段落、换行与列表顺序，公式样式文字通过真正的字符串单元格交付，不加可见前缀；不承诺富文本格式无损往返。目前用户 Excel 导入没有备注列，不新增映射。完整备份必须保存原生 JSON；Excel 不是完整备份。

生成器须显式选 html_type=remark，字段名称任意。仅支持 Vue3 普通、树形与主子表；子行默认摘要、激活后才挂载编辑器，身份不取行号。实际数据库列必须是 nullable JSON，不能用于主键、关联键、必填、唯一或字符串查询字段。Vue2+remark 在保存、预览、下载与本地生成统一拒绝。其他 JSON 和既有 editor 字段沿用自己的用途。

升级必须先读 [升级恢复手册](upgrade-recovery.md)，使用统一 scripts/db.py 入口。不要手工裸 ALTER 七列，不要修改历史发布产物或校验和来绕过门禁。Schema 与声明的职责分别保留，历史文本转换只存在于迁移、种子、声明和经 checksum 核验后的历史受管产物边界。

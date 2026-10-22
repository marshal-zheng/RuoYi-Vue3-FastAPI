# 通用备注消费者核对

2026-10-22，静态核对当前快照，非运行验收。

| 表/主键 | 前端编辑 | 写入/内部模型 | 读取/派生 | 输出/数据源 |
| --- | --- | --- | --- | --- |
| sys_user/user_id | UserFormDialog | user_write_vo → EditUserModel | user_read_models、UserInfo/UserDetail、角色/岗位关联 | user_service Excel；bootstrap 用户；导入映射未包含备注，不新增 |
| sys_role/role_id | RoleFormDrawer | role_vo/role_write_vo | role_read_models、用户嵌套角色 | role_service Excel；bootstrap 角色；专用权限/状态写入白名单 |
| sys_post/post_id | PostDlg/post-form | post_vo | post_read_models、用户嵌套岗位 | post_service Excel；bootstrap 岗位；当前 Formily 单一值 |
| sys_dict_type/dict_id | DictDlg | dict_vo | dict_read_models、列表 | dict_type_service Excel；capability compiler/planner/历史发布包 |
| sys_dict_data/dict_code | dict/data.vue | dict_vo | dict_read_models、字典记录缓存 | dict_data_service Excel；capability compiler/planner/历史发布包 |
| sys_config/config_id | ConfigDlg | config_vo | config_read_models、列表；键值缓存只存 config_value | config_service Excel；capability compiler/planner/历史发布包 |
| gen_table/table_id | basicInfoForm | gen_vo/GenService | 表配置详情/列表 | gen_do、正式 metadata；生成配置及模板 |

实际 DO 位于 module_admin/entity/do/{user,role,post,dict,config}_do.py 与 module_generator/entity/do/gen_do.py。独立 QueryModel 当前有继承实体的路径，须拆出查询字段，避免递归 remark 进入 GET。

生成器使用 utils/template_util.py 按 frontendVersion、tplCategory 路由；Vue3 crud/tree/sub 主子列都需显式 html_type=remark。Vue2 同组合在后端拒绝。非备注 JSON 及 editor 维持既有语义。

范围外回归：sys_menu/sys_job/sys_notice 的 remark 仍为字符串；通知 notice_content 保留现有 Editor；工程、版本、协议、设备、仿真描述与备注不迁移。没有发现包含七字段的业务级全库 JSON 备份入口；数据库工作流发布包保存受管三类实体的完整目标态，数据库外部备份必须保留原生 JSON。Excel 仅文本交换。

核对入口：rg remark module_admin/entity/vo modules/system/application/{services,read_models} module_generator；rg remark scripts/internal；rg remark src/views/system src/views/tool/gen。详细位置以实施代码及最终映射为准。

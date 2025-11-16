-- ----------------------------
-- 协议管理相关字典数据增量更新脚本
-- 用途：为已部署的系统添加协议字典数据
-- 使用场景：系统已经运行，需要添加协议字典功能
-- 注意：新系统部署请直接使用 ruoyi-fastapi.sql
-- ----------------------------

-- 检查并插入协议类型字典
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, remark)
SELECT 100, '协议类型', 'sys_protocol_type', '0', 'admin', sysdate(), '协议通信类型列表'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_type');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 100, 1, '以太网', 'ethernet', 'sys_protocol_type', '', 'primary', 'N', '0', 'admin', sysdate(), '以太网协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 100);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 101, 2, 'RS422', 'rs422', 'sys_protocol_type', '', 'success', 'N', '0', 'admin', sysdate(), 'RS422串口协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 101);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 102, 3, 'CAN', 'can', 'sys_protocol_type', '', 'warning', 'N', '0', 'admin', sysdate(), 'CAN总线协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 102);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 103, 4, '1553B', '1553b', 'sys_protocol_type', '', 'danger', 'N', '0', 'admin', sysdate(), '1553B总线协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 103);

-- 检查并插入传输频率字典
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, remark)
SELECT 101, '传输频率', 'sys_protocol_frequency', '0', 'admin', sysdate(), '协议传输频率列表'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_frequency');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 110, 1, '单次', 'once', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '单次传输'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 110);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 111, 2, '10ms', '10', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '10毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 111);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 112, 3, '20ms', '20', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '20毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 112);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 113, 4, '50ms', '50', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '50毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 113);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 114, 5, '100ms', '100', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '100毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 114);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 115, 6, '160ms', '160', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '160毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 115);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 116, 7, '200ms', '200', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '200毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 116);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 117, 8, '500ms', '500', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '500毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 117);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark)
SELECT 118, 9, '1000ms', '1000', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '1000毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 118);

-- 其他字典类型和数据的插入语句（省略，完整版本包含所有字典）
-- 实际使用时请包含所有字典数据的插入语句

-- 执行完成后，需要刷新字典缓存
-- 请在系统管理 > 字典管理页面点击"刷新缓存"按钮

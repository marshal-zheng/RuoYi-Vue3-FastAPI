-- 查看当前的协议类型数据
SELECT dict_code, dict_sort, dict_label, dict_value, dict_type 
FROM sys_dict_data 
WHERE dict_type = 'sys_protocol_type' 
ORDER BY dict_sort;

-- 删除重复的协议类型数据，只保留 dict_code 最小的那个
DELETE FROM sys_dict_data 
WHERE dict_type = 'sys_protocol_type' 
AND dict_code NOT IN (
    SELECT min_code FROM (
        SELECT MIN(dict_code) as min_code
        FROM sys_dict_data
        WHERE dict_type = 'sys_protocol_type'
        GROUP BY dict_value
    ) AS temp
);

-- 确保只有以下协议类型（清理后重新插入标准数据）
DELETE FROM sys_dict_data WHERE dict_type = 'sys_protocol_type';

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
VALUES 
(100, 1, '以太网', 'ethernet', 'sys_protocol_type', '', 'primary', 'N', '0', 'admin', NOW(), '', NULL, '以太网协议'),
(101, 2, 'RS422', 'rs422', 'sys_protocol_type', '', 'success', 'N', '0', 'admin', NOW(), '', NULL, 'RS422串口协议'),
(102, 3, 'RS485', 'rs485', 'sys_protocol_type', '', 'success', 'N', '0', 'admin', NOW(), '', NULL, 'RS485串口协议'),
(103, 4, 'CAN', 'can', 'sys_protocol_type', '', 'warning', 'N', '0', 'admin', NOW(), '', NULL, 'CAN总线协议'),
(104, 5, '1553B', '1553b', 'sys_protocol_type', '', 'danger', 'N', '0', 'admin', NOW(), '', NULL, '1553B总线协议')
ON DUPLICATE KEY UPDATE
    dict_sort = VALUES(dict_sort),
    dict_label = VALUES(dict_label),
    dict_value = VALUES(dict_value),
    update_time = NOW();

-- 查看修复后的结果
SELECT dict_code, dict_sort, dict_label, dict_value 
FROM sys_dict_data 
WHERE dict_type = 'sys_protocol_type' 
ORDER BY dict_sort;

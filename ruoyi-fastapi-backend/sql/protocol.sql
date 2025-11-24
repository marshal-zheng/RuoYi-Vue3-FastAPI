-- 设置客户端字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_client = utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_results = utf8mb4;

-- ============================================
-- 协议模块（表结构 + 字典 + 菜单）
-- ============================================

-- 1. 协议表
CREATE TABLE IF NOT EXISTS `sys_protocol` (
  `protocol_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '协议ID',
  `protocol_name` varchar(100) NOT NULL COMMENT '协议名称',
  `protocol_type` varchar(50) NOT NULL COMMENT '协议类型（以太网、RS422、CAN、1553B）',
  `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态（0正常 1停用）',
  `description` varchar(500) DEFAULT NULL COMMENT '协议描述',
  `protocol_config` json DEFAULT NULL COMMENT '协议配置（JSON格式）',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `del_flag` char(1) DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  PRIMARY KEY (`protocol_id`),
  KEY `idx_protocol_type` (`protocol_type`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='协议管理表';

START TRANSACTION;
SET @has_is_locked := (
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'sys_protocol'
      AND COLUMN_NAME = 'is_locked'
);
SET @ddl_is_locked := IF(
    @has_is_locked = 1,
    'ALTER TABLE `sys_protocol` MODIFY COLUMN `is_locked` TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''是否固化'';',
    'DO 0;'
);
PREPARE stmt FROM @ddl_is_locked;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
COMMIT;

-- 演示数据
INSERT INTO `sys_protocol` (`protocol_name`, `protocol_type`, `status`, `description`, `protocol_config`, `create_by`, `create_time`)
SELECT '以太网协议', 'LAN', '0', '标准以太网通信协议，支持10/100/1000Mbps传输', '{}', 'admin', NOW()
WHERE NOT EXISTS (SELECT 1 FROM `sys_protocol` WHERE `protocol_name` = '以太网协议');

INSERT INTO `sys_protocol` (`protocol_name`, `protocol_type`, `status`, `description`, `protocol_config`, `create_by`, `create_time`)
SELECT 'RS422串行协议', 'RS422', '0', 'RS422差分信号串行通信协议，支持长距离传输', '{}', 'admin', NOW()
WHERE NOT EXISTS (SELECT 1 FROM `sys_protocol` WHERE `protocol_name` = 'RS422串行协议');

INSERT INTO `sys_protocol` (`protocol_name`, `protocol_type`, `status`, `description`, `protocol_config`, `create_by`, `create_time`)
SELECT 'CAN总线协议', 'CAN', '0', '控制器局域网总线协议，广泛应用于汽车和工业控制', '{}', 'admin', NOW()
WHERE NOT EXISTS (SELECT 1 FROM `sys_protocol` WHERE `protocol_name` = 'CAN总线协议');

INSERT INTO `sys_protocol` (`protocol_name`, `protocol_type`, `status`, `description`, `protocol_config`, `create_by`, `create_time`)
SELECT 'MIL-STD-1553B协议', '1553B', '1', '军用标准数据总线协议，用于航空航天设备通信', '{}', 'admin', NOW()
WHERE NOT EXISTS (SELECT 1 FROM `sys_protocol` WHERE `protocol_name` = 'MIL-STD-1553B协议');

-- 2. 字典数据
-- Dict helper macros are implemented via INSERT ... SELECT ... WHERE NOT EXISTS to keep scripts idempotent.

-- 2.1 协议类型
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 100, '协议类型', 'sys_protocol_type', '0', 'admin', NOW(), '', NULL, '协议通信类型列表'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_type');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 100, 1, 'LAN', 'LAN', 'sys_protocol_type', '', 'primary', 'N', '0', 'admin', NOW(), '', NULL, '以太网协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 100);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 101, 2, 'RS422', 'RS422', 'sys_protocol_type', '', 'success', 'N', '0', 'admin', NOW(), '', NULL, 'RS422串口协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 101);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 102, 3, 'RS485', 'RS485', 'sys_protocol_type', '', 'success', 'N', '0', 'admin', NOW(), '', NULL, 'RS485串口协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 102);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 103, 4, 'CAN', 'CAN', 'sys_protocol_type', '', 'warning', 'N', '0', 'admin', NOW(), '', NULL, 'CAN总线协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 103);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 104, 5, '1553B', '1553B', 'sys_protocol_type', '', 'danger', 'N', '0', 'admin', NOW(), '', NULL, '1553B总线协议'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 104);

-- 2.2 传输频率
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 101, '传输频率', 'sys_protocol_frequency', '0', 'admin', NOW(), '', NULL, '协议传输频率列表'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_frequency');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 110, 1, '单次', 'once', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '单次传输'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 110);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 111, 2, '10ms', '10', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '10毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 111);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 112, 3, '20ms', '20', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '20毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 112);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 113, 4, '50ms', '50', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '50毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 113);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 114, 5, '100ms', '100', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '100毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 114);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 115, 6, '160ms', '160', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '160毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 115);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 116, 7, '200ms', '200', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '200毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 116);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 117, 8, '500ms', '500', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '500毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 117);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 118, 9, '1000ms', '1000', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', NOW(), '', NULL, '1000毫秒周期'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 118);

-- 2.3 以太网速率
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 102, '以太网传输速率', 'sys_protocol_speed_ethernet', '0', 'admin', NOW(), '', NULL, '以太网协议传输速率'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_speed_ethernet');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 120, 1, '10M', '10M', 'sys_protocol_speed_ethernet', '', '', 'N', '0', 'admin', NOW(), '', NULL, '10Mbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 120);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 121, 2, '100M', '100M', 'sys_protocol_speed_ethernet', '', '', 'Y', '0', 'admin', NOW(), '', NULL, '100Mbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 121);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 122, 3, '1000M', '1000M', 'sys_protocol_speed_ethernet', '', '', 'N', '0', 'admin', NOW(), '', NULL, '1000Mbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 122);

-- 2.4 RS422速率
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 103, 'RS422传输速率', 'sys_protocol_speed_rs422', '0', 'admin', NOW(), '', NULL, 'RS422协议传输速率'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_speed_rs422');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 130, 1, '9.6K', '9.6K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', NOW(), '', NULL, '9600bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 130);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 131, 2, '19.2K', '19.2K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', NOW(), '', NULL, '19200bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 131);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 132, 3, '38.4K', '38.4K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', NOW(), '', NULL, '38400bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 132);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 133, 4, '57.6K', '57.6K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', NOW(), '', NULL, '57600bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 133);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 134, 5, '115.2K', '115.2K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', NOW(), '', NULL, '115200bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 134);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 135, 6, '230.4K', '230.4K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', NOW(), '', NULL, '230400bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 135);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 136, 7, '460.8K', '460.8K', 'sys_protocol_speed_rs422', '', '', 'Y', '0', 'admin', NOW(), '', NULL, '460800bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 136);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 137, 8, '921.6K', '921.6K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', NOW(), '', NULL, '921600bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 137);

-- 2.5 RS485速率
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 111, 'RS485传输速率', 'sys_protocol_speed_rs485', '0', 'admin', NOW(), '', NULL, 'RS485协议传输速率'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_speed_rs485');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 138, 1, '9.6K', '9.6K', 'sys_protocol_speed_rs485', '', '', 'N', '0', 'admin', NOW(), '', NULL, '9600bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 138);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 139, 2, '19.2K', '19.2K', 'sys_protocol_speed_rs485', '', '', 'N', '0', 'admin', NOW(), '', NULL, '19200bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 139);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 140, 3, '38.4K', '38.4K', 'sys_protocol_speed_rs485', '', '', 'N', '0', 'admin', NOW(), '', NULL, '38400bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 140);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 141, 4, '57.6K', '57.6K', 'sys_protocol_speed_rs485', '', '', 'N', '0', 'admin', NOW(), '', NULL, '57600bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 141);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 142, 5, '115.2K', '115.2K', 'sys_protocol_speed_rs485', '', '', 'Y', '0', 'admin', NOW(), '', NULL, '115200bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 142);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 143, 6, '230.4K', '230.4K', 'sys_protocol_speed_rs485', '', '', 'N', '0', 'admin', NOW(), '', NULL, '230400bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 143);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 144, 7, '460.8K', '460.8K', 'sys_protocol_speed_rs485', '', '', 'N', '0', 'admin', NOW(), '', NULL, '460800bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 144);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 145, 8, '921.6K', '921.6K', 'sys_protocol_speed_rs485', '', '', 'N', '0', 'admin', NOW(), '', NULL, '921600bps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 145);

-- 2.6 CAN速率
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 112, 'CAN传输速率', 'sys_protocol_speed_can', '0', 'admin', NOW(), '', NULL, 'CAN协议传输速率'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_speed_can');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 150, 1, '125K', '125K', 'sys_protocol_speed_can', '', '', 'N', '0', 'admin', NOW(), '', NULL, '125Kbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 150);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 151, 2, '250K', '250K', 'sys_protocol_speed_can', '', '', 'N', '0', 'admin', NOW(), '', NULL, '250Kbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 151);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 152, 3, '500K', '500K', 'sys_protocol_speed_can', '', '', 'Y', '0', 'admin', NOW(), '', NULL, '500Kbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 152);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 153, 4, '1000K', '1000K', 'sys_protocol_speed_can', '', '', 'N', '0', 'admin', NOW(), '', NULL, '1000Kbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 153);

-- 2.7 1553B速率
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 113, '1553B传输速率', 'sys_protocol_speed_1553b', '0', 'admin', NOW(), '', NULL, '1553B协议传输速率'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_speed_1553b');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 160, 1, '1M', '1M', 'sys_protocol_speed_1553b', '', '', 'Y', '0', 'admin', NOW(), '', NULL, '1Mbps'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 160);

-- 2.8 以太网传输方式
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 114, '以太网传输方式', 'sys_protocol_method_ethernet', '0', 'admin', NOW(), '', NULL, '以太网协议传输方式'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_method_ethernet');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 170, 1, 'UDP单播', 'udp_unicast', 'sys_protocol_method_ethernet', '', '', 'N', '0', 'admin', NOW(), '', NULL, 'UDP单播传输'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 170);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 171, 2, 'UDP组播', 'udp_multicast', 'sys_protocol_method_ethernet', '', '', 'Y', '0', 'admin', NOW(), '', NULL, 'UDP组播传输'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 171);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 172, 3, 'UDP广播', 'udp_broadcast', 'sys_protocol_method_ethernet', '', '', 'N', '0', 'admin', NOW(), '', NULL, 'UDP广播传输'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 172);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 173, 4, 'TCP', 'tcp', 'sys_protocol_method_ethernet', '', '', 'N', '0', 'admin', NOW(), '', NULL, 'TCP传输'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 173);

-- 2.9 CAN传输方式
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 115, 'CAN传输方式', 'sys_protocol_method_can', '0', 'admin', NOW(), '', NULL, 'CAN协议传输方式'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_method_can');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 180, 1, 'CAN标准帧', 'can_standard', 'sys_protocol_method_can', '', '', 'N', '0', 'admin', NOW(), '', NULL, 'CAN标准帧'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 180);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 181, 2, 'CAN扩展帧', 'can_extended', 'sys_protocol_method_can', '', '', 'Y', '0', 'admin', NOW(), '', NULL, 'CAN扩展帧'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 181);

-- 2.10 数据类型
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 116, '数据类型', 'sys_protocol_data_type', '0', 'admin', NOW(), '', NULL, '协议字段数据类型'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_data_type');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 190, 1, 'uint8', 'uint8', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '无符号8位整数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 190);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 191, 2, 'uint16', 'uint16', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '无符号16位整数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 191);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 192, 3, 'uint32', 'uint32', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '无符号32位整数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 192);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 193, 4, 'int8', 'int8', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '有符号8位整数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 193);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 194, 5, 'int16', 'int16', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '有符号16位整数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 194);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 195, 6, 'int32', 'int32', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '有符号32位整数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 195);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 196, 7, 'float', 'float', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '单精度浮点数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 196);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 197, 8, 'double', 'double', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '双精度浮点数'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 197);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 198, 9, 'string', 'string', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '字符串'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 198);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 199, 10, 'bool', 'bool', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', NOW(), '', NULL, '布尔值'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 199);

-- 2.11 错误处理
INSERT INTO sys_dict_type (dict_id, dict_name, dict_type, status, create_by, create_time, update_by, update_time, remark)
SELECT 117, '错误处理', 'sys_protocol_error_handling', '0', 'admin', NOW(), '', NULL, '协议错误处理策略'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_type WHERE dict_type = 'sys_protocol_error_handling');

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 200, 1, '不判断', 'none', 'sys_protocol_error_handling', '', 'info', 'N', '0', 'admin', NOW(), '', NULL, '不进行错误判断'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 200);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 201, 2, '超时重传', 'timeout_retry', 'sys_protocol_error_handling', '', 'warning', 'N', '0', 'admin', NOW(), '', NULL, '超时后重传'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 201);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 202, 3, 'CRC校验', 'crc_check', 'sys_protocol_error_handling', '', 'primary', 'N', '0', 'admin', NOW(), '', NULL, 'CRC循环冗余校验'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 202);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 203, 4, '奇偶校验', 'parity_check', 'sys_protocol_error_handling', '', 'success', 'N', '0', 'admin', NOW(), '', NULL, '奇偶校验'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 203);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 204, 5, '超时重传 3 次, 100ms', 'timeout_retry_3_100ms', 'sys_protocol_error_handling', '', 'warning', 'Y', '0', 'admin', NOW(), '', NULL, '超时重传3次，间隔100ms'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 204);

INSERT INTO sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, update_by, update_time, remark)
SELECT 205, 6, '-', 'default', 'sys_protocol_error_handling', '', '', 'N', '0', 'admin', NOW(), '', NULL, '默认处理'
WHERE NOT EXISTS (SELECT 1 FROM sys_dict_data WHERE dict_code = 205);

-- 3. 菜单（幂等）
START TRANSACTION;

-- 清理旧菜单
DELETE FROM sys_role_menu 
WHERE menu_id IN (
    SELECT menu_id FROM (
        SELECT menu_id FROM sys_menu 
        WHERE (
            menu_name = '协议管理'
            OR perms LIKE 'protocol:%'
        )
        AND menu_id NOT IN (2100, 2101, 2102, 2103, 2104, 2105)
    ) AS tmp
);

DELETE FROM sys_menu 
WHERE menu_name = '协议管理' AND menu_id <> 2100;

DELETE FROM sys_menu 
WHERE perms LIKE 'protocol:%' AND menu_id NOT IN (2101, 2102, 2103, 2104, 2105);

-- 固定 ID 菜单
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2100, '协议管理', 0, 5, 'protocol', 'protocol/index', 1, 0, 'C', '0', '0', 'protocol:list', 'documentation', 'admin', NOW(), 'admin', NOW(), '协议管理菜单')
ON DUPLICATE KEY UPDATE 
    parent_id = VALUES(parent_id),
    order_num = VALUES(order_num),
    path = VALUES(path),
    component = VALUES(component),
    perms = VALUES(perms),
    icon = VALUES(icon),
    remark = VALUES(remark),
    update_time = NOW();

-- 按钮
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2101, '协议查询', 2100, 1, '', '', 1, 0, 'F', '0', '0', 'protocol:query', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2102, '协议新增', 2100, 2, '', '', 1, 0, 'F', '0', '0', 'protocol:add', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2103, '协议修改', 2100, 3, '', '', 1, 0, 'F', '0', '0', 'protocol:edit', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2104, '协议删除', 2100, 4, '', '', 1, 0, 'F', '0', '0', 'protocol:remove', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2105, '协议导出', 2100, 5, '', '', 1, 0, 'F', '0', '0', 'protocol:export', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

-- 角色绑定
DELETE FROM sys_role_menu WHERE role_id = 1 AND menu_id IN (2100, 2101, 2102, 2103, 2104, 2105);

INSERT INTO sys_role_menu (role_id, menu_id)
VALUES 
    (1, 2100),
    (1, 2101), (1, 2102), (1, 2103), (1, 2104), (1, 2105)
ON DUPLICATE KEY UPDATE menu_id = VALUES(menu_id);

COMMIT;

-- ----------------------------
-- 协议管理相关字典数据初始化脚本
-- ----------------------------

-- ----------------------------
-- 1、协议类型字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(100, '协议类型', 'sys_protocol_type', '0', 'admin', sysdate(), '', NULL, '协议通信类型列表');

INSERT INTO sys_dict_data VALUES(100, 1, '以太网', 'ethernet', 'sys_protocol_type', '', 'primary', 'N', '0', 'admin', sysdate(), '', NULL, '以太网协议');
INSERT INTO sys_dict_data VALUES(101, 2, 'RS422', 'rs422', 'sys_protocol_type', '', 'success', 'N', '0', 'admin', sysdate(), '', NULL, 'RS422串口协议');
INSERT INTO sys_dict_data VALUES(102, 3, 'CAN', 'can', 'sys_protocol_type', '', 'warning', 'N', '0', 'admin', sysdate(), '', NULL, 'CAN总线协议');
INSERT INTO sys_dict_data VALUES(103, 4, '1553B', '1553b', 'sys_protocol_type', '', 'danger', 'N', '0', 'admin', sysdate(), '', NULL, '1553B总线协议');

-- ----------------------------
-- 2、传输频率字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(101, '传输频率', 'sys_protocol_frequency', '0', 'admin', sysdate(), '', NULL, '协议传输频率列表');

INSERT INTO sys_dict_data VALUES(110, 1, '单次', 'once', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '单次传输');
INSERT INTO sys_dict_data VALUES(111, 2, '10ms', '10', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '10毫秒周期');
INSERT INTO sys_dict_data VALUES(112, 3, '20ms', '20', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '20毫秒周期');
INSERT INTO sys_dict_data VALUES(113, 4, '50ms', '50', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '50毫秒周期');
INSERT INTO sys_dict_data VALUES(114, 5, '100ms', '100', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '100毫秒周期');
INSERT INTO sys_dict_data VALUES(115, 6, '160ms', '160', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '160毫秒周期');
INSERT INTO sys_dict_data VALUES(116, 7, '200ms', '200', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '200毫秒周期');
INSERT INTO sys_dict_data VALUES(117, 8, '500ms', '500', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '500毫秒周期');
INSERT INTO sys_dict_data VALUES(118, 9, '1000ms', '1000', 'sys_protocol_frequency', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '1000毫秒周期');

-- ----------------------------
-- 3、以太网传输速率字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(102, '以太网传输速率', 'sys_protocol_speed_ethernet', '0', 'admin', sysdate(), '', NULL, '以太网协议传输速率');

INSERT INTO sys_dict_data VALUES(120, 1, '10M', '10M', 'sys_protocol_speed_ethernet', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '10Mbps');
INSERT INTO sys_dict_data VALUES(121, 2, '100M', '100M', 'sys_protocol_speed_ethernet', '', '', 'Y', '0', 'admin', sysdate(), '', NULL, '100Mbps');
INSERT INTO sys_dict_data VALUES(122, 3, '1000M', '1000M', 'sys_protocol_speed_ethernet', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '1000Mbps');

-- ----------------------------
-- 4、RS422传输速率字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(103, 'RS422传输速率', 'sys_protocol_speed_rs422', '0', 'admin', sysdate(), '', NULL, 'RS422协议传输速率');

INSERT INTO sys_dict_data VALUES(130, 1, '9.6K', '9.6K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '9600bps');
INSERT INTO sys_dict_data VALUES(131, 2, '19.2K', '19.2K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '19200bps');
INSERT INTO sys_dict_data VALUES(132, 3, '38.4K', '38.4K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '38400bps');
INSERT INTO sys_dict_data VALUES(133, 4, '57.6K', '57.6K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '57600bps');
INSERT INTO sys_dict_data VALUES(134, 5, '115.2K', '115.2K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '115200bps');
INSERT INTO sys_dict_data VALUES(135, 6, '230.4K', '230.4K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '230400bps');
INSERT INTO sys_dict_data VALUES(136, 7, '460.8K', '460.8K', 'sys_protocol_speed_rs422', '', '', 'Y', '0', 'admin', sysdate(), '', NULL, '460800bps');
INSERT INTO sys_dict_data VALUES(137, 8, '921.6K', '921.6K', 'sys_protocol_speed_rs422', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '921600bps');

-- ----------------------------
-- 5、CAN传输速率字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(104, 'CAN传输速率', 'sys_protocol_speed_can', '0', 'admin', sysdate(), '', NULL, 'CAN协议传输速率');

INSERT INTO sys_dict_data VALUES(140, 1, '125K', '125K', 'sys_protocol_speed_can', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '125Kbps');
INSERT INTO sys_dict_data VALUES(141, 2, '250K', '250K', 'sys_protocol_speed_can', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '250Kbps');
INSERT INTO sys_dict_data VALUES(142, 3, '500K', '500K', 'sys_protocol_speed_can', '', '', 'Y', '0', 'admin', sysdate(), '', NULL, '500Kbps');
INSERT INTO sys_dict_data VALUES(143, 4, '1000K', '1000K', 'sys_protocol_speed_can', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '1000Kbps');

-- ----------------------------
-- 6、1553B传输速率字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(105, '1553B传输速率', 'sys_protocol_speed_1553b', '0', 'admin', sysdate(), '', NULL, '1553B协议传输速率');

INSERT INTO sys_dict_data VALUES(150, 1, '1M', '1M', 'sys_protocol_speed_1553b', '', '', 'Y', '0', 'admin', sysdate(), '', NULL, '1Mbps');

-- ----------------------------
-- 7、以太网传输方式字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(106, '以太网传输方式', 'sys_protocol_method_ethernet', '0', 'admin', sysdate(), '', NULL, '以太网协议传输方式');

INSERT INTO sys_dict_data VALUES(160, 1, 'UDP单播', 'udp_unicast', 'sys_protocol_method_ethernet', '', '', 'N', '0', 'admin', sysdate(), '', NULL, 'UDP单播传输');
INSERT INTO sys_dict_data VALUES(161, 2, 'UDP组播', 'udp_multicast', 'sys_protocol_method_ethernet', '', '', 'Y', '0', 'admin', sysdate(), '', NULL, 'UDP组播传输');
INSERT INTO sys_dict_data VALUES(162, 3, 'UDP广播', 'udp_broadcast', 'sys_protocol_method_ethernet', '', '', 'N', '0', 'admin', sysdate(), '', NULL, 'UDP广播传输');
INSERT INTO sys_dict_data VALUES(163, 4, 'TCP', 'tcp', 'sys_protocol_method_ethernet', '', '', 'N', '0', 'admin', sysdate(), '', NULL, 'TCP传输');

-- ----------------------------
-- 8、CAN传输方式字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(107, 'CAN传输方式', 'sys_protocol_method_can', '0', 'admin', sysdate(), '', NULL, 'CAN协议传输方式');

INSERT INTO sys_dict_data VALUES(170, 1, 'CAN标准帧', 'can_standard', 'sys_protocol_method_can', '', '', 'N', '0', 'admin', sysdate(), '', NULL, 'CAN标准帧');
INSERT INTO sys_dict_data VALUES(171, 2, 'CAN扩展帧', 'can_extended', 'sys_protocol_method_can', '', '', 'Y', '0', 'admin', sysdate(), '', NULL, 'CAN扩展帧');

-- ----------------------------
-- 9、数据类型字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(108, '数据类型', 'sys_protocol_data_type', '0', 'admin', sysdate(), '', NULL, '协议字段数据类型');

INSERT INTO sys_dict_data VALUES(180, 1, 'uint8', 'uint8', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '无符号8位整数');
INSERT INTO sys_dict_data VALUES(181, 2, 'uint16', 'uint16', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '无符号16位整数');
INSERT INTO sys_dict_data VALUES(182, 3, 'uint32', 'uint32', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '无符号32位整数');
INSERT INTO sys_dict_data VALUES(183, 4, 'int8', 'int8', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '有符号8位整数');
INSERT INTO sys_dict_data VALUES(184, 5, 'int16', 'int16', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '有符号16位整数');
INSERT INTO sys_dict_data VALUES(185, 6, 'int32', 'int32', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '有符号32位整数');
INSERT INTO sys_dict_data VALUES(186, 7, 'float', 'float', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '单精度浮点数');
INSERT INTO sys_dict_data VALUES(187, 8, 'double', 'double', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '双精度浮点数');
INSERT INTO sys_dict_data VALUES(188, 9, 'string', 'string', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '字符串');
INSERT INTO sys_dict_data VALUES(189, 10, 'bool', 'bool', 'sys_protocol_data_type', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '布尔值');

-- ----------------------------
-- 10、错误处理字典
-- ----------------------------
INSERT INTO sys_dict_type VALUES(109, '错误处理', 'sys_protocol_error_handling', '0', 'admin', sysdate(), '', NULL, '协议错误处理策略');

INSERT INTO sys_dict_data VALUES(190, 1, '不判断', 'none', 'sys_protocol_error_handling', '', 'info', 'N', '0', 'admin', sysdate(), '', NULL, '不进行错误判断');
INSERT INTO sys_dict_data VALUES(191, 2, '超时重传', 'timeout_retry', 'sys_protocol_error_handling', '', 'warning', 'N', '0', 'admin', sysdate(), '', NULL, '超时后重传');
INSERT INTO sys_dict_data VALUES(192, 3, 'CRC校验', 'crc_check', 'sys_protocol_error_handling', '', 'primary', 'N', '0', 'admin', sysdate(), '', NULL, 'CRC循环冗余校验');
INSERT INTO sys_dict_data VALUES(193, 4, '奇偶校验', 'parity_check', 'sys_protocol_error_handling', '', 'success', 'N', '0', 'admin', sysdate(), '', NULL, '奇偶校验');
INSERT INTO sys_dict_data VALUES(194, 5, '超时重传 3 次, 100ms', 'timeout_retry_3_100ms', 'sys_protocol_error_handling', '', 'warning', 'Y', '0', 'admin', sysdate(), '', NULL, '超时重传3次，间隔100ms');
INSERT INTO sys_dict_data VALUES(195, 6, '-', 'default', 'sys_protocol_error_handling', '', '', 'N', '0', 'admin', sysdate(), '', NULL, '默认处理');

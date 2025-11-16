-- 协议管理表
CREATE TABLE IF NOT EXISTS `sys_protocol` (
  `protocol_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '协议ID',
  `protocol_name` varchar(100) NOT NULL COMMENT '协议名称',
  `protocol_type` varchar(50) NOT NULL COMMENT '协议类型（以太网、RS422、CAN、1553B）',
  `version` varchar(50) NOT NULL DEFAULT '1.0' COMMENT '版本号',
  `status` char(1) NOT NULL DEFAULT '0' COMMENT '状态（0正常 1停用）',
  `is_locked` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否固化（0未固化 1已固化）',
  `description` varchar(500) DEFAULT NULL COMMENT '协议描述',
  `protocol_config` json DEFAULT NULL COMMENT '协议配置（JSON格式）',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `del_flag` char(1) DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  PRIMARY KEY (`protocol_id`),
  KEY `idx_protocol_name_version` (`protocol_name`, `version`),
  KEY `idx_protocol_type` (`protocol_type`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='协议管理表';

-- 插入测试数据
INSERT INTO `sys_protocol` (`protocol_name`, `protocol_type`, `version`, `status`, `is_locked`, `description`, `protocol_config`, `create_by`, `create_time`) VALUES
('以太网协议', '以太网', '1.0', '0', 0, '标准以太网通信协议，支持10/100/1000Mbps传输', '{}', 'admin', NOW()),
('RS422串行协议', 'RS422', '1.0', '0', 1, 'RS422差分信号串行通信协议，支持长距离传输', '{}', 'admin', NOW()),
('CAN总线协议', 'CAN', '1.0', '0', 0, '控制器局域网总线协议，广泛应用于汽车和工业控制', '{}', 'admin', NOW()),
('MIL-STD-1553B协议', '1553B', '1.0', '1', 1, '军用标准数据总线协议，用于航空航天设备通信', '{}', 'admin', NOW());

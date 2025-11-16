-- ----------------------------
-- 项目版本管理表
-- ----------------------------
DROP TABLE IF EXISTS `sys_project_version`;
CREATE TABLE `sys_project_version` (
  `version_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '版本ID',
  `project_id` int(11) NOT NULL COMMENT '项目ID',
  `version_number` varchar(50) NOT NULL COMMENT '版本号',
  `version_name` varchar(100) NOT NULL COMMENT '版本名称',
  `description` text COMMENT '版本描述',
  `status` char(1) DEFAULT '1' COMMENT '状态（0停用 1启用）',
  `is_locked` char(1) DEFAULT '0' COMMENT '是否固化（0否 1是）',
  `locked_time` datetime DEFAULT NULL COMMENT '固化时间',
  `locked_by` varchar(64) DEFAULT NULL COMMENT '固化人',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `del_flag` char(1) DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  PRIMARY KEY (`version_id`),
  KEY `idx_project_id` (`project_id`),
  KEY `idx_version_number` (`version_number`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='项目版本管理表';

-- ----------------------------
-- 初始化项目版本数据
-- ----------------------------
INSERT INTO `sys_project_version` VALUES 
(1, 1, 'v1.0.0', '初始版本', '项目初始版本，包含基础功能模块', '1', '0', NULL, NULL, 'admin', '2024-01-15 10:30:00', 'admin', '2024-01-15 10:30:00', '0'),
(2, 1, 'v1.1.0', '功能增强版', '新增用户管理模块，优化系统性能', '1', '0', NULL, NULL, 'admin', '2024-02-20 14:20:00', 'admin', '2024-02-20 14:20:00', '0'),
(3, 1, 'v2.0.0', '重大更新版', '架构重构，新增多租户支持，UI全面升级', '1', '1', '2024-03-10 09:15:00', 'admin', 'admin', '2024-03-10 09:15:00', 'admin', '2024-03-10 09:15:00', '0');

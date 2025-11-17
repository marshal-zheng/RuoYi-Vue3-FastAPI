-- ============================================
-- 项目模块（表结构 + 菜单 + 权限）
-- ============================================

-- 1. 工程管理表
CREATE TABLE IF NOT EXISTS `sys_project` (
  `project_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '工程编号',
  `project_desc` text COMMENT '工程描述',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `del_flag` char(1) DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  PRIMARY KEY (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工程管理表';

-- 2. 项目版本管理表
CREATE TABLE IF NOT EXISTS `sys_project_version` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目版本管理表';

-- 3. 演示版本数据（仅在缺失时写入）
INSERT INTO `sys_project_version`
    (`version_id`, `project_id`, `version_number`, `version_name`, `description`, `status`, `is_locked`, `locked_time`, `locked_by`, `create_by`, `create_time`, `update_by`, `update_time`, `del_flag`)
SELECT 1, 1, 'v1.0.0', '初始版本', '项目初始版本，包含基础功能模块', '1', '0', NULL, NULL, 'admin', '2024-01-15 10:30:00', 'admin', '2024-01-15 10:30:00', '0'
WHERE NOT EXISTS (SELECT 1 FROM `sys_project_version` WHERE `version_id` = 1);

INSERT INTO `sys_project_version`
    (`version_id`, `project_id`, `version_number`, `version_name`, `description`, `status`, `is_locked`, `locked_time`, `locked_by`, `create_by`, `create_time`, `update_by`, `update_time`, `del_flag`)
SELECT 2, 1, 'v1.1.0', '功能增强版', '新增用户管理模块，优化系统性能', '1', '0', NULL, NULL, 'admin', '2024-02-20 14:20:00', 'admin', '2024-02-20 14:20:00', '0'
WHERE NOT EXISTS (SELECT 1 FROM `sys_project_version` WHERE `version_id` = 2);

INSERT INTO `sys_project_version`
    (`version_id`, `project_id`, `version_number`, `version_name`, `description`, `status`, `is_locked`, `locked_time`, `locked_by`, `create_by`, `create_time`, `update_by`, `update_time`, `del_flag`)
SELECT 3, 1, 'v2.0.0', '重大更新版', '架构重构，新增多租户支持，UI全面升级', '1', '1', '2024-03-10 09:15:00', 'admin', 'admin', '2024-03-10 09:15:00', 'admin', '2024-03-10 09:15:00', '0'
WHERE NOT EXISTS (SELECT 1 FROM `sys_project_version` WHERE `version_id` = 3);

-- 4. 菜单/权限修复（幂等）
START TRANSACTION;

-- 清理历史随机 ID 菜单
DELETE FROM sys_role_menu 
WHERE menu_id IN (
    SELECT menu_id FROM (
        SELECT menu_id FROM sys_menu 
        WHERE (
            menu_name = '工程管理'
            OR perms LIKE 'project:%'
            OR (menu_name = '操作日志' AND parent_id = 4)
        )
        AND menu_id NOT IN (4, 118, 119, 1061, 1062, 1063, 1064)
    ) AS tmp
);

DELETE FROM sys_menu 
WHERE menu_name = '工程管理' AND menu_id <> 4;

DELETE FROM sys_menu 
WHERE parent_id = 4 AND menu_id NOT IN (118, 119)
  AND (menu_name IN ('工程列表', '操作日志') OR perms LIKE 'project:%' OR perms LIKE 'monitor:operlog%');

-- 固定 ID 菜单
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (4, '工程管理', 0, 4, 'project', NULL, 1, 0, 'M', '0', '0', '', 'build', 'admin', NOW(), 'admin', NOW(), '工程管理目录')
ON DUPLICATE KEY UPDATE 
    parent_id = VALUES(parent_id),
    order_num = VALUES(order_num),
    path = VALUES(path),
    component = VALUES(component),
    icon = VALUES(icon),
    remark = VALUES(remark),
    update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (118, '工程列表', 4, 1, 'project', 'project/index', 1, 0, 'C', '0', '0', 'project:project:list', 'list', 'admin', NOW(), 'admin', NOW(), '工程列表菜单')
ON DUPLICATE KEY UPDATE 
    parent_id = VALUES(parent_id),
    order_num = VALUES(order_num),
    path = VALUES(path),
    component = VALUES(component),
    perms = VALUES(perms),
    icon = VALUES(icon),
    remark = VALUES(remark),
    update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (119, '操作日志', 4, 2, 'operlog', 'project/operlog/index', 'projectOperLog', 1, 0, 'C', '0', '0', 'monitor:operlog:list', 'form', 'admin', NOW(), 'admin', NOW(), '工程操作日志')
ON DUPLICATE KEY UPDATE 
    parent_id = VALUES(parent_id),
    order_num = VALUES(order_num),
    path = VALUES(path),
    component = VALUES(component),
    route_name = VALUES(route_name),
    perms = VALUES(perms),
    icon = VALUES(icon),
    remark = VALUES(remark),
    update_time = NOW();

-- 固定 ID 按钮
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1061, '工程查询', 118, 1, '#', '', 1, 0, 'F', '0', '0', 'project:project:query', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1062, '工程新增', 118, 2, '#', '', 1, 0, 'F', '0', '0', 'project:project:add', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1063, '工程修改', 118, 3, '#', '', 1, 0, 'F', '0', '0', 'project:project:edit', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1064, '工程删除', 118, 4, '#', '', 1, 0, 'F', '0', '0', 'project:project:remove', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

-- 恢复管理员角色菜单
DELETE FROM sys_role_menu WHERE role_id = 1 AND menu_id IN (4, 118, 119, 1061, 1062, 1063, 1064);

INSERT INTO sys_role_menu (role_id, menu_id)
VALUES 
    (1, 4),
    (1, 118), (1, 119),
    (1, 1061), (1, 1062), (1, 1063), (1, 1064)
ON DUPLICATE KEY UPDATE menu_id = VALUES(menu_id);

COMMIT;

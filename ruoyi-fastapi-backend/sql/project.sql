-- 设置客户端字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_client = utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_results = utf8mb4;

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

-- 3. 工程拓扑数据表
CREATE TABLE IF NOT EXISTS `sys_project_topology` (
  `topology_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '拓扑ID',
  `project_id` int(11) NOT NULL COMMENT '工程编号',
  `version_id` int(11) DEFAULT NULL COMMENT '版本ID',
  `topology_data` json NOT NULL COMMENT '拓扑数据（包含图结构、总线设计、接口控制等）',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`topology_id`),
  KEY `idx_project_topology_project_id` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工程拓扑数据表';

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

-- 版本管理按钮权限（挂在工程列表下，用于工程详情页Tab）
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1065, '版本查询', 118, 5, '#', '', 1, 0, 'F', '0', '0', 'project:version:query', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1066, '版本新增', 118, 6, '#', '', 1, 0, 'F', '0', '0', 'project:version:add', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1067, '版本编辑', 118, 7, '#', '', 1, 0, 'F', '0', '0', 'project:version:edit', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1068, '版本删除', 118, 8, '#', '', 1, 0, 'F', '0', '0', 'project:version:remove', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1069, '版本克隆', 118, 9, '#', '', 1, 0, 'F', '0', '0', 'project:version:clone', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1070, '版本固化', 118, 10, '#', '', 1, 0, 'F', '0', '0', 'project:version:lock', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (1071, '版本列表', 118, 11, '#', '', 1, 0, 'F', '0', '0', 'project:version:list', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

-- 恢复管理员角色菜单
DELETE FROM sys_role_menu WHERE role_id = 1 AND menu_id IN (4, 118, 119, 1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070, 1071);

INSERT INTO sys_role_menu (role_id, menu_id)
VALUES 
    (1, 4),
    (1, 118), (1, 119),
    (1, 1061), (1, 1062), (1, 1063), (1, 1064),
    (1, 1065), (1, 1066), (1, 1067), (1, 1068), (1, 1069), (1, 1070), (1, 1071)
ON DUPLICATE KEY UPDATE menu_id = VALUES(menu_id);

COMMIT;

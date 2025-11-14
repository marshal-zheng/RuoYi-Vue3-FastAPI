-- ----------------------------
-- 工程管理表
-- ----------------------------
DROP TABLE IF EXISTS `sys_project`;
CREATE TABLE `sys_project` (
  `project_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '工程编号',
  `project_desc` text COMMENT '工程描述',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `del_flag` char(1) DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  PRIMARY KEY (`project_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='工程管理表';

-- ----------------------------
-- 工程管理菜单 SQL
-- ----------------------------
-- 1. 插入顶层"工程管理"目录菜单
INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES('工程管理', 0, 5, 'project', NULL, 1, 0, 'M', '0', '0', '', 'build', 'admin', sysdate(), '', NULL, '工程管理菜单');

-- 获取刚插入的目录菜单ID
SET @parentId = LAST_INSERT_ID();

-- 2. 插入"工程管理"子菜单页面
INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES('工程管理', @parentId, 1, 'project', 'project/index', 1, 0, 'C', '0', '0', 'project:project:list', 'list', 'admin', sysdate(), '', NULL, '工程管理菜单');

-- 获取刚插入的菜单页面ID
SET @menuId = LAST_INSERT_ID();

-- 3. 插入按钮权限
INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES('工程查询', @menuId, 1, '#', '', 1, 0, 'F', '0', '0', 'project:project:query', '#', 'admin', sysdate(), '', NULL, '');

INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES('工程新增', @menuId, 2, '#', '', 1, 0, 'F', '0', '0', 'project:project:add', '#', 'admin', sysdate(), '', NULL, '');

INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES('工程修改', @menuId, 3, '#', '', 1, 0, 'F', '0', '0', 'project:project:edit', '#', 'admin', sysdate(), '', NULL, '');

INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES('工程删除', @menuId, 4, '#', '', 1, 0, 'F', '0', '0', 'project:project:remove', '#', 'admin', sysdate(), '', NULL, '');

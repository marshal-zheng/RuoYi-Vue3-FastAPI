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
-- 注意：这些菜单已经包含在 ruoyi-fastapi.sql 主文件中
-- 如果你已经执行过主SQL文件，不需要再执行下面的菜单SQL
-- 如果你只想单独添加工程管理模块，可以执行下面的SQL

-- 1. 插入顶层"工程管理"目录菜单 (ID=4)
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(4, '工程管理', 0, 4, 'project', NULL, 1, 0, 'M', '0', '0', '', 'build', 'admin', sysdate(), '', NULL, '工程管理目录');

-- 2. 插入"工程列表"子菜单页面 (ID=118)
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(118, '工程列表', 4, 1, 'project', 'project/index', 1, 0, 'C', '0', '0', 'project:project:list', 'list', 'admin', sysdate(), '', NULL, '工程列表菜单');

-- 3. 插入"操作日志"子菜单页面 (ID=119)
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(119, '操作日志', 4, 2, 'operlog', 'monitor/operlog/index', 1, 0, 'C', '0', '0', 'monitor:operlog:list', 'form', 'admin', sysdate(), '', NULL, '工程操作日志');

-- 4. 插入工程管理按钮权限
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1061, '工程查询', 118, 1, '#', '', 1, 0, 'F', '0', '0', 'project:project:query', '#', 'admin', sysdate(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1062, '工程新增', 118, 2, '#', '', 1, 0, 'F', '0', '0', 'project:project:add', '#', 'admin', sysdate(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1063, '工程修改', 118, 3, '#', '', 1, 0, 'F', '0', '0', 'project:project:edit', '#', 'admin', sysdate(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1064, '工程删除', 118, 4, '#', '', 1, 0, 'F', '0', '0', 'project:project:remove', '#', 'admin', sysdate(), '', NULL, '');

-- ----------------------------
-- 更新工程管理菜单到固定ID
-- ----------------------------
-- 此脚本用于将已存在的工程管理菜单更新为固定ID
-- 如果你之前执行过 sys_project.sql，菜单ID可能是动态生成的
-- 执行此脚本可以将菜单ID统一为固定值

-- 1. 先删除角色菜单关联（避免外键约束）
DELETE FROM sys_role_menu WHERE menu_id IN (
    SELECT menu_id FROM sys_menu WHERE perms LIKE 'project:project:%'
);
DELETE FROM sys_role_menu WHERE menu_id IN (
    SELECT menu_id FROM sys_menu WHERE menu_name = '工程列表'
);
DELETE FROM sys_role_menu WHERE menu_id IN (
    SELECT menu_id FROM sys_menu WHERE menu_name = '工程管理' AND parent_id = 0
);
DELETE FROM sys_role_menu WHERE menu_id IN (
    SELECT menu_id FROM sys_menu WHERE menu_name = '操作日志' AND path = 'operlog' AND parent_id != 108
);

-- 2. 删除旧的工程管理菜单按钮权限
DELETE FROM sys_menu WHERE perms LIKE 'project:project:%';

-- 3. 删除旧的工程管理二级菜单
DELETE FROM sys_menu WHERE menu_name = '工程列表' AND path = 'project';
DELETE FROM sys_menu WHERE menu_name = '操作日志' AND path = 'operlog' AND parent_id != 108;

-- 4. 删除旧的工程管理一级菜单
DELETE FROM sys_menu WHERE menu_name = '工程管理' AND parent_id = 0;

-- 5. 删除可能存在的固定ID记录（避免主键冲突）
DELETE FROM sys_menu WHERE menu_id IN (4, 118, 119, 1061, 1062, 1063, 1064);

-- 6. 插入固定ID的菜单
-- 一级菜单：工程管理 (ID=4)
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(4, '工程管理', 0, 4, 'project', NULL, 1, 0, 'M', '0', '0', '', 'build', 'admin', now(), '', NULL, '工程管理目录');

-- 7. 二级菜单：工程列表 (ID=118)
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(118, '工程列表', 4, 1, 'project', 'project/index', 1, 0, 'C', '0', '0', 'project:project:list', 'list', 'admin', now(), '', NULL, '工程列表菜单');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(119, '操作日志', 4, 2, 'operlog', 'monitor/operlog/index', 'projectOperLog', 1, 0, 'C', '0', '0', 'monitor:operlog:list', 'form', 'admin', now(), '', NULL, '工程操作日志');

-- 9. 按钮权限
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1061, '工程查询', 118, 1, '#', '', 1, 0, 'F', '0', '0', 'project:project:query', '#', 'admin', now(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1062, '工程新增', 118, 2, '#', '', 1, 0, 'F', '0', '0', 'project:project:add', '#', 'admin', now(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1063, '工程修改', 118, 3, '#', '', 1, 0, 'F', '0', '0', 'project:project:edit', '#', 'admin', now(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES(1064, '工程删除', 118, 4, '#', '', 1, 0, 'F', '0', '0', 'project:project:remove', '#', 'admin', now(), '', NULL, '');

-- 9. 更新角色菜单关联
-- 删除无效的关联
DELETE FROM sys_role_menu WHERE menu_id NOT IN (SELECT menu_id FROM sys_menu);

-- 为admin角色添加新的工程管理权限
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) 
SELECT 1, menu_id FROM sys_menu WHERE menu_id IN (4, 118, 119, 1061, 1062, 1063, 1064);

-- 协议管理菜单 SQL
-- 菜单 ID 使用 2100 开始，避免与现有菜单冲突
-- 为保证脚本可重复执行，先清理可能已存在的旧数据
DELETE FROM sys_role_menu WHERE menu_id BETWEEN 2100 AND 2105;
DELETE FROM sys_menu WHERE menu_id BETWEEN 2100 AND 2105;

-- 一级菜单：协议管理（直接作为页面菜单，无二级菜单）
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2100, '协议管理', 0, 5, 'protocol', 'protocol/index', 1, 0, 'C', '0', '0', 'protocol:list', 'documentation', 'admin', NOW(), '', NULL, '协议管理菜单');

-- 按钮权限
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2101, '协议查询', 2100, 1, '', '', 1, 0, 'F', '0', '0', 'protocol:query', '#', 'admin', NOW(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2102, '协议新增', 2100, 2, '', '', 1, 0, 'F', '0', '0', 'protocol:add', '#', 'admin', NOW(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2103, '协议修改', 2100, 3, '', '', 1, 0, 'F', '0', '0', 'protocol:edit', '#', 'admin', NOW(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2104, '协议删除', 2100, 4, '', '', 1, 0, 'F', '0', '0', 'protocol:remove', '#', 'admin', NOW(), '', NULL, '');

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (2105, '协议导出', 2100, 5, '', '', 1, 0, 'F', '0', '0', 'protocol:export', '#', 'admin', NOW(), '', NULL, '');

-- 为管理员角色分配协议管理权限（避免重复插入）
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT 1, menu_id FROM sys_menu WHERE menu_id BETWEEN 2100 AND 2105;

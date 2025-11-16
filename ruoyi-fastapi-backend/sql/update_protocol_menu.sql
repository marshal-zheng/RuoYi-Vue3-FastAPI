-- ----------------------------
-- 协议管理菜单：固定 ID 增量修复脚本
-- 背景：新协议模块上线后，需要给已运行环境补齐固定 ID 菜单与按钮，便于授权与部署。
-- 可重复执行，执行前建议备份 sys_menu / sys_role_menu 相关数据。
-- ----------------------------

START TRANSACTION;

-- 1. 清理历史遗留的随机 ID 菜单及其角色绑定
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

-- 2. 固定 ID 菜单
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

-- 3. 固定 ID 按钮
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

-- 4. 恢复管理员角色权限
DELETE FROM sys_role_menu WHERE role_id = 1 AND menu_id IN (2100, 2101, 2102, 2103, 2104, 2105);

INSERT INTO sys_role_menu (role_id, menu_id)
VALUES 
    (1, 2100),
    (1, 2101), (1, 2102), (1, 2103), (1, 2104), (1, 2105)
ON DUPLICATE KEY UPDATE menu_id = VALUES(menu_id);

COMMIT;

-- 如需回滚请执行 ROLLBACK;（限本事务内）

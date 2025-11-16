-- ----------------------------
-- 工程管理菜单：固定 ID 增量修复脚本
-- 背景：早期版本的菜单 ID 由雪花算法生成，升级后需统一到固定 ID，方便部署与授权。
-- 可重复执行，执行前建议备份 sys_menu / sys_role_menu 相关数据。
-- ----------------------------

START TRANSACTION;

-- 1. 清理历史遗留的随机 ID 菜单及其角色绑定
DELETE FROM sys_role_menu 
WHERE menu_id IN (
    SELECT menu_id FROM (
        SELECT menu_id FROM sys_menu 
        WHERE (
            menu_name IN ('工程管理', '工程列表', '操作日志')
            OR perms LIKE 'project:project:%'
            OR perms = 'monitor:operlog:list'
        )
        AND menu_id NOT IN (4, 118, 119, 1061, 1062, 1063, 1064)
    ) AS tmp
);

DELETE FROM sys_menu 
WHERE menu_name = '工程管理' AND menu_id <> 4;

DELETE FROM sys_menu 
WHERE menu_name = '工程列表' AND menu_id <> 118;

DELETE FROM sys_menu 
WHERE menu_name = '操作日志' AND menu_id <> 119;

DELETE FROM sys_menu 
WHERE perms LIKE 'project:project:%' AND menu_id NOT IN (1061, 1062, 1063, 1064);

-- 2. 用固定 ID 回填/更新菜单
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (4, '工程管理', 0, 4, 'project', NULL, 1, 0, 'M', '0', '0', '', 'build', 'admin', NOW(), 'admin', NOW(), '工程管理目录')
ON DUPLICATE KEY UPDATE 
    parent_id = VALUES(parent_id),
    order_num = VALUES(order_num),
    path = VALUES(path),
    component = VALUES(component),
    menu_type = VALUES(menu_type),
    visible = VALUES(visible),
    status = VALUES(status),
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

-- 3. 固定 ID 按钮
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

-- 4. 恢复角色权限（role_id=1 管理员，可按需复制到其他角色）
DELETE FROM sys_role_menu WHERE role_id = 1 AND menu_id IN (4, 118, 119, 1061, 1062, 1063, 1064);

INSERT INTO sys_role_menu (role_id, menu_id)
VALUES 
    (1, 4), (1, 118), (1, 119),
    (1, 1061), (1, 1062), (1, 1063), (1, 1064)
ON DUPLICATE KEY UPDATE menu_id = VALUES(menu_id);

COMMIT;

-- 如需回滚请执行 ROLLBACK;（限本事务内）

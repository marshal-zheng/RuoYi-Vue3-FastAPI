-- 设置客户端字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_client = utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_results = utf8mb4;

-- ============================================
-- 设备模块（表结构 + 菜单 + 权限）
-- ============================================

-- 1. 设备分类表
CREATE TABLE IF NOT EXISTS sys_device_category (
    device_category_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '设备分类ID',
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    descr VARCHAR(255) DEFAULT NULL COMMENT '分类描述',
    status CHAR(1) DEFAULT '0' COMMENT '状态（0正常 1停用）',
    create_by VARCHAR(64) DEFAULT NULL COMMENT '创建者',
    create_time DATETIME DEFAULT NULL COMMENT '创建时间',
    update_by VARCHAR(64) DEFAULT NULL COMMENT '更新者',
    update_time DATETIME DEFAULT NULL COMMENT '更新时间',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    UNIQUE KEY uk_name (name),
    KEY idx_status (status),
    KEY idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备分类表';

-- 默认分类数据移除（不再初始化内置分类）

-- 2. 设备表
CREATE TABLE IF NOT EXISTS sys_device (
    device_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '设备ID',
    device_name VARCHAR(100) NOT NULL COMMENT '设备名称',
    device_category_id BIGINT DEFAULT NULL COMMENT '设备分类ID',
    category_name VARCHAR(50) DEFAULT NULL COMMENT '分类名称（冗余字段）',
    device_type VARCHAR(50) DEFAULT NULL COMMENT '设备类型',
    manufacturer VARCHAR(100) DEFAULT NULL COMMENT '制造商',
    model VARCHAR(100) DEFAULT NULL COMMENT '型号',
    version VARCHAR(50) DEFAULT NULL COMMENT '版本',
    bus_type VARCHAR(50) DEFAULT NULL COMMENT '总线类型',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    create_by VARCHAR(64) DEFAULT NULL COMMENT '创建者',
    create_time DATETIME DEFAULT NULL COMMENT '创建时间',
    update_by VARCHAR(64) DEFAULT NULL COMMENT '更新者',
    update_time DATETIME DEFAULT NULL COMMENT '更新时间',
    KEY idx_device_name (device_name),
    KEY idx_category_id (device_category_id),
    KEY idx_bus_type (bus_type),
    KEY idx_update_time (update_time),
    CONSTRAINT fk_device_category FOREIGN KEY (device_category_id) REFERENCES sys_device_category(device_category_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备表';

-- 3. 设备接口表
CREATE TABLE IF NOT EXISTS sys_device_interface (
    interface_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '接口ID',
    device_id BIGINT NOT NULL COMMENT '设备ID',
    interface_name VARCHAR(50) NOT NULL COMMENT '接口名称',
    interface_type VARCHAR(20) NOT NULL COMMENT '接口类型（RS422/RS485/CAN/LAN/1553B）',
    position VARCHAR(20) DEFAULT 'right' COMMENT '端口位置（left/right/top/bottom）',
    description VARCHAR(255) DEFAULT NULL COMMENT '接口描述',
    params JSON DEFAULT NULL COMMENT '接口参数配置（JSON格式）',
    message_config JSON DEFAULT NULL COMMENT '报文配置（JSON格式）',
    create_time DATETIME DEFAULT NULL COMMENT '创建时间',
    update_time DATETIME DEFAULT NULL COMMENT '更新时间',
    KEY idx_device_id (device_id),
    KEY idx_interface_type (interface_type),
    CONSTRAINT fk_device_interface FOREIGN KEY (device_id) REFERENCES sys_device(device_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备接口表';

-- 4. 菜单 & 权限（幂等）
START TRANSACTION;

-- 清理历史随机 ID 菜单
DELETE FROM sys_role_menu 
WHERE menu_id IN (
    SELECT menu_id FROM (
        SELECT menu_id FROM sys_menu 
        WHERE (menu_name LIKE '设备%' OR menu_name LIKE '分类管理%' OR perms LIKE 'device:%')
        AND menu_id NOT IN (5000, 5001, 50011, 50012, 50013, 50014, 50015, 5002, 50021, 50022, 50023, 50024, 50025, 50026)
    ) AS tmp
);

DELETE FROM sys_menu 
WHERE (menu_name LIKE '设备%' OR menu_name LIKE '分类管理%' OR perms LIKE 'device:%')
  AND menu_id NOT IN (5000, 5001, 50011, 50012, 50013, 50014, 50015, 5002, 50021, 50022, 50023, 50024, 50025, 50026);

-- 设备中心一级菜单
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (5000, '设备中心', 0, 5, 'device', NULL, 1, 0, 'M', '0', '0', '', 'component', 'admin', NOW(), 'admin', NOW(), '设备管理菜单')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), path = VALUES(path), component = VALUES(component), update_time = NOW();

SET @device_center_id = 5000;

-- 分类管理菜单与按钮
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (5001, '分类管理', @device_center_id, 1, 'category', 'device/category/index', 1, 0, 'C', '0', '0', 'device:category:list', 'list', 'admin', NOW(), 'admin', NOW(), '设备分类管理菜单')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), path = VALUES(path), component = VALUES(component), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES 
(50011, '设备分类查询', 5001, 1, '#', '', 1, 0, 'F', '0', '0', 'device:category:query', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50012, '设备分类新增', 5001, 2, '#', '', 1, 0, 'F', '0', '0', 'device:category:add', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50013, '设备分类修改', 5001, 3, '#', '', 1, 0, 'F', '0', '0', 'device:category:edit', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50014, '设备分类删除', 5001, 4, '#', '', 1, 0, 'F', '0', '0', 'device:category:remove', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50015, '设备分类导出', 5001, 5, '#', '', 1, 0, 'F', '0', '0', 'device:category:export', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

-- 设备管理菜单与按钮
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (5002, '设备管理', @device_center_id, 2, 'list', 'device/index', 1, 0, 'C', '0', '0', 'device:list:list', 'build', 'admin', NOW(), 'admin', NOW(), '设备管理菜单')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), path = VALUES(path), component = VALUES(component), perms = VALUES(perms), update_time = NOW();

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES 
(50021, '设备查询', 5002, 1, '#', '', 1, 0, 'F', '0', '0', 'device:list:query', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50022, '设备新增', 5002, 2, '#', '', 1, 0, 'F', '0', '0', 'device:list:add', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50023, '设备修改', 5002, 3, '#', '', 1, 0, 'F', '0', '0', 'device:list:edit', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50024, '设备删除', 5002, 4, '#', '', 1, 0, 'F', '0', '0', 'device:list:remove', '#', 'admin', NOW(), 'admin', NOW(), ''),
(50025, '设备导出', 5002, 5, '#', '', 1, 0, 'F', '0', '0', 'device:list:export', '#', 'admin', NOW(), 'admin', NOW(), '')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), perms = VALUES(perms), update_time = NOW();

-- 设备详情隐藏菜单
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark)
VALUES (50026, '设备详情', 5002, 6, 'detail', 'device/detail', 1, 0, 'C', '1', '0', 'device:list:query', '#', 'admin', NOW(), 'admin', NOW(), '设备详情配置页面')
ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), order_num = VALUES(order_num), path = VALUES(path), component = VALUES(component), update_time = NOW();

-- 角色绑定
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(1, 5000),
(1, 5001), (1, 50011), (1, 50012), (1, 50013), (1, 50014), (1, 50015),
(1, 5002), (1, 50021), (1, 50022), (1, 50023), (1, 50024), (1, 50025), (1, 50026);

COMMIT;

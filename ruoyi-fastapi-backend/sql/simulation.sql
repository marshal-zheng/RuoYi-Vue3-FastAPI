-- ----------------------------
-- 仿真模块数据库表
-- ----------------------------

-- ----------------------------
-- 仿真管理菜单和权限
-- ----------------------------
-- 仿真管理菜单（使用较大的ID避免冲突）
INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES (3100, '仿真管理', 0, 10, 'simulation', NULL, NULL, 'Simulation', 1, 0, 'M', '0', '0', '', 'monitor', 'admin', NOW(), '', NULL, '仿真管理目录');

-- 仿真会话管理
INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES (3101, '创建会话', 3100, 1, '', NULL, NULL, '', 1, 0, 'F', '0', '0', 'simulation:session:create', '#', 'admin', NOW(), '', NULL, '创建仿真会话');

INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES (3102, '启动仿真', 3100, 2, '', NULL, NULL, '', 1, 0, 'F', '0', '0', 'simulation:session:start', '#', 'admin', NOW(), '', NULL, '启动仿真会话');

INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES (3103, '停止仿真', 3100, 3, '', NULL, NULL, '', 1, 0, 'F', '0', '0', 'simulation:session:stop', '#', 'admin', NOW(), '', NULL, '停止仿真会话');

INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES (3104, '查询状态', 3100, 4, '', NULL, NULL, '', 1, 0, 'F', '0', '0', 'simulation:session:query', '#', 'admin', NOW(), '', NULL, '查询仿真状态');

INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES (3105, '查询数据', 3100, 5, '', NULL, NULL, '', 1, 0, 'F', '0', '0', 'simulation:data:query', '#', 'admin', NOW(), '', NULL, '查询仿真数据');

INSERT IGNORE INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, update_by, update_time, remark) 
VALUES (3106, '导出数据', 3100, 6, '', NULL, NULL, '', 1, 0, 'F', '0', '0', 'simulation:data:export', '#', 'admin', NOW(), '', NULL, '导出仿真数据');

-- 为管理员角色分配仿真权限
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3100);
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3101);
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3102);
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3103);
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3104);
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3105);
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES (1, 3106);

-- ----------------------------
-- 1、仿真会话表
-- ----------------------------
DROP TABLE IF EXISTS sys_simulation_session;
CREATE TABLE sys_simulation_session (
  session_id        VARCHAR(64)     NOT NULL                   COMMENT '会话ID',
  project_id        BIGINT(20)      NOT NULL                   COMMENT '项目ID',
  version_id        BIGINT(20)      NOT NULL                   COMMENT '版本ID',
  status            VARCHAR(20)     DEFAULT 'created'          COMMENT '状态（created/running/stopped）',
  start_time        DATETIME                                   COMMENT '开始时间',
  end_time          DATETIME                                   COMMENT '结束时间',
  create_by         VARCHAR(64)     DEFAULT ''                 COMMENT '创建者',
  create_time       DATETIME                                   COMMENT '创建时间',
  PRIMARY KEY (session_id),
  INDEX idx_project_version (project_id, version_id),
  INDEX idx_create_time (create_time)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COMMENT='仿真会话表';

-- ----------------------------
-- 2、仿真报文记录表
-- ----------------------------
DROP TABLE IF EXISTS sys_simulation_message;
CREATE TABLE sys_simulation_message (
  message_id        VARCHAR(64)     NOT NULL                   COMMENT '报文ID',
  session_id        VARCHAR(64)     NOT NULL                   COMMENT '会话ID',
  sender_node_id    VARCHAR(64)                                COMMENT '发送节点ID',
  sender_port_id    VARCHAR(64)                                COMMENT '发送端口ID',
  receiver_node_id  VARCHAR(64)                                COMMENT '接收节点ID',
  receiver_port_id  VARCHAR(64)                                COMMENT '接收端口ID',
  protocol_type     VARCHAR(20)                                COMMENT '协议类型（LAN/RS422/RS485/CAN/1553B）',
  size_bytes        INT             DEFAULT 0                  COMMENT '报文大小（字节）',
  send_timestamp    DOUBLE                                     COMMENT '发送时间戳（秒）',
  receive_timestamp DOUBLE                                     COMMENT '接收时间戳（秒）',
  create_time       DATETIME                                   COMMENT '创建时间',
  PRIMARY KEY (message_id),
  INDEX idx_session_id (session_id),
  INDEX idx_send_timestamp (send_timestamp)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COMMENT='仿真报文记录表';

-- ----------------------------
-- 3、仿真带宽数据表
-- ----------------------------
DROP TABLE IF EXISTS sys_simulation_bandwidth;
CREATE TABLE sys_simulation_bandwidth (
  id                BIGINT(20)      NOT NULL AUTO_INCREMENT    COMMENT '主键ID',
  session_id        VARCHAR(64)     NOT NULL                   COMMENT '会话ID',
  node_id           VARCHAR(64)                                COMMENT '节点ID',
  port_id           VARCHAR(64)                                COMMENT '端口ID',
  timestamp         DOUBLE                                     COMMENT '时间戳（秒）',
  bandwidth_mbps    DOUBLE          DEFAULT 0                  COMMENT '带宽（Mbps）',
  message_count     INT             DEFAULT 0                  COMMENT '报文数量',
  create_time       DATETIME                                   COMMENT '创建时间',
  PRIMARY KEY (id),
  INDEX idx_session_port (session_id, port_id),
  INDEX idx_timestamp (timestamp)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COMMENT='仿真带宽数据表';

-- ----------------------------
-- 4、仿真告警记录表
-- ----------------------------
DROP TABLE IF EXISTS sys_simulation_alarm;
CREATE TABLE sys_simulation_alarm (
  alarm_id          VARCHAR(64)     NOT NULL                   COMMENT '告警ID',
  session_id        VARCHAR(64)     NOT NULL                   COMMENT '会话ID',
  alarm_type        VARCHAR(50)                                COMMENT '告警类型（loopback/multi_connection）',
  severity          VARCHAR(20)     DEFAULT 'warning'          COMMENT '严重程度（info/warning/error）',
  affected_nodes    JSON                                       COMMENT '受影响节点（JSON数组）',
  message           VARCHAR(500)                               COMMENT '告警消息',
  timestamp         DOUBLE                                     COMMENT '时间戳（秒）',
  create_time       DATETIME                                   COMMENT '创建时间',
  PRIMARY KEY (alarm_id),
  INDEX idx_session_id (session_id),
  INDEX idx_alarm_type (alarm_type)
) ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COMMENT='仿真告警记录表';

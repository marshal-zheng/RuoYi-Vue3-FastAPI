-- ----------------------------
-- 仿真模块数据库表
-- ----------------------------

-- ----------------------------
-- 仿真管理菜单和权限
-- ----------------------------
-- 注意：仿真功能已集成在工程管理中，通过 工程列表 -> 工程详情 -> 版本仿真 进入
-- 不需要独立的仿真管理菜单

-- 清理可能存在的旧菜单数据
DELETE FROM sys_role_menu WHERE menu_id IN (3100, 3101, 3102, 3103, 3104, 3105, 3106);
DELETE FROM sys_menu WHERE menu_id IN (3100, 3101, 3102, 3103, 3104, 3105, 3106);

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

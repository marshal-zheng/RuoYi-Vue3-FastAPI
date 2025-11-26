from datetime import datetime
from sqlalchemy import Column, DateTime, String, BigInteger, Integer, Double, JSON
from config.database import Base


class SimulationSessionDO(Base):
    """
    仿真会话数据对象
    """
    __tablename__ = 'sys_simulation_session'

    session_id = Column(String(64), primary_key=True, comment='会话ID')
    project_id = Column(BigInteger, nullable=False, comment='项目ID')
    version_id = Column(BigInteger, nullable=False, comment='版本ID')
    status = Column(String(20), default='created', comment='状态（created/running/stopped）')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    create_by = Column(String(64), default='', comment='创建者')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')


class SimulationMessageDO(Base):
    """
    仿真报文记录数据对象
    """
    __tablename__ = 'sys_simulation_message'

    message_id = Column(String(64), primary_key=True, comment='报文ID')
    session_id = Column(String(64), nullable=False, comment='会话ID')
    sender_node_id = Column(String(64), comment='发送节点ID')
    sender_port_id = Column(String(64), comment='发送端口ID')
    receiver_node_id = Column(String(64), comment='接收节点ID')
    receiver_port_id = Column(String(64), comment='接收端口ID')
    protocol_type = Column(String(20), comment='协议类型（LAN/RS422/RS485/CAN/1553B）')
    size_bytes = Column(Integer, default=0, comment='报文大小（字节）')
    send_timestamp = Column(Double, comment='发送时间戳（秒）')
    receive_timestamp = Column(Double, comment='接收时间戳（秒）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')


class SimulationBandwidthDO(Base):
    """
    仿真带宽数据对象
    """
    __tablename__ = 'sys_simulation_bandwidth'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    session_id = Column(String(64), nullable=False, comment='会话ID')
    node_id = Column(String(64), comment='节点ID')
    port_id = Column(String(64), comment='端口ID')
    timestamp = Column(Double, comment='时间戳（秒）')
    bandwidth_mbps = Column(Double, default=0, comment='带宽（Mbps）')
    message_count = Column(Integer, default=0, comment='报文数量')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')


class SimulationAlarmDO(Base):
    """
    仿真告警记录数据对象
    """
    __tablename__ = 'sys_simulation_alarm'

    alarm_id = Column(String(64), primary_key=True, comment='告警ID')
    session_id = Column(String(64), nullable=False, comment='会话ID')
    alarm_type = Column(String(50), comment='告警类型（loopback/multi_connection）')
    severity = Column(String(20), default='warning', comment='严重程度（info/warning/error）')
    affected_nodes = Column(JSON, comment='受影响节点（JSON数组）')
    message = Column(String(500), comment='告警消息')
    timestamp = Column(Double, comment='时间戳（秒）')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')

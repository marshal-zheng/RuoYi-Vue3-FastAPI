from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Boolean, JSON
from config.database import Base


class SysProtocol(Base):
    """
    协议管理表
    """

    __tablename__ = 'sys_protocol'

    protocol_id = Column(Integer, primary_key=True, autoincrement=True, comment='协议ID')
    protocol_name = Column(String(100), nullable=False, comment='协议名称')
    protocol_type = Column(String(50), nullable=False, comment='协议类型')
    status = Column(String(1), nullable=False, default='0', comment='状态（0正常 1停用）')
    description = Column(String(500), nullable=True, comment='协议描述')
    protocol_config = Column(JSON, nullable=True, comment='协议配置')
    create_by = Column(String(64), nullable=True, default='', comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    del_flag = Column(String(1), nullable=True, default='0', comment='删除标志')

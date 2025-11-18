from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from config.database import Base


class SysProjectTopology(Base):
    """
    工程拓扑数据表
    """

    __tablename__ = 'sys_project_topology'

    topology_id = Column(Integer, primary_key=True, autoincrement=True, comment='拓扑ID')
    project_id = Column(Integer, nullable=False, comment='工程编号')
    version_id = Column(Integer, nullable=True, comment='版本ID')
    topology_data = Column(JSON, nullable=False, comment='拓扑数据（包含图结构、总线设计、接口控制等）')
    create_by = Column(String(64), nullable=True, default='', comment='创建人')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')

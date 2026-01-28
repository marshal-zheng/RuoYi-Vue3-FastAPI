from sqlalchemy import JSON, Column, DateTime, Integer, String
from module_admin.entity.do.base import LegacyBaseModel


class SysProjectTopology(LegacyBaseModel):
    """
    工程拓扑数据表
    """

    __tablename__ = 'sys_project_topology'

    topology_id = Column(Integer, primary_key=True, autoincrement=True, comment='拓扑ID')
    project_id = Column(Integer, nullable=False, comment='工程编号')
    version_id = Column(Integer, nullable=True, comment='版本ID')
    topology_data = Column(JSON, nullable=False, comment='拓扑数据（包含图结构、总线设计、接口控制等）')

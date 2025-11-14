from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from config.database import Base


class SysProject(Base):
    """
    工程管理表
    """

    __tablename__ = 'sys_project'

    project_id = Column(Integer, primary_key=True, autoincrement=True, comment='工程编号')
    project_name = Column(String(100), nullable=True, comment='工程名称')
    project_code = Column(String(50), nullable=True, comment='工程编码')
    project_desc = Column(Text, nullable=True, comment='工程描述')
    create_by = Column(String(64), nullable=True, default='', comment='创建人')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
    update_by = Column(String(64), nullable=True, default='', comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')
    del_flag = Column(String(1), nullable=True, default='0', comment='删除标志（0代表存在 2代表删除）')
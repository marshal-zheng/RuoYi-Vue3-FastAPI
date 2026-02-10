from sqlalchemy import Column, DateTime, Integer, String, Text
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import EnableStatusEnum, DelFlagEnum


class ProjectVersionDO(LegacyBaseModel):
    """
    项目版本管理表
    """

    __tablename__ = 'sys_project_version'

    version_id = Column(Integer, primary_key=True, autoincrement=True, comment='版本ID')
    project_id = Column(Integer, nullable=False, comment='项目ID')
    version_number = Column(String(50), nullable=False, comment='版本号')
    version_name = Column(String(100), nullable=False, comment='版本名称')
    description = Column(Text, nullable=True, comment='版本描述')
    status = Column(String(1), nullable=True, default=EnableStatusEnum.ENABLED.value, comment='状态（0停用 1启用）')
    is_locked = Column(String(1), nullable=True, default='0', comment='是否固化（0否 1是）')
    locked_time = Column(DateTime, nullable=True, comment='固化时间')
    locked_by = Column(String(64), nullable=True, comment='固化人')
    del_flag = Column(String(1), nullable=True, default=DelFlagEnum.EXIST.value, comment='删除标志（0代表存在 2代表删除）')

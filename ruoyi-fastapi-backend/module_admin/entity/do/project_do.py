from sqlalchemy import Column, DateTime, Integer, String, Text
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import DelFlagEnum


class SysProject(LegacyBaseModel):
    """
    工程管理表
    """

    __tablename__ = 'sys_project'

    project_id = Column(Integer, primary_key=True, autoincrement=True, comment='工程编号')
    project_name = Column(String(100), nullable=True, comment='工程名称')
    project_code = Column(String(50), nullable=True, comment='工程编码')
    project_desc = Column(Text, nullable=True, comment='工程描述')
    del_flag = Column(String(1), nullable=True, default=DelFlagEnum.EXIST.value, comment='删除标志（0代表存在 2代表删除）')

    def __init__(self, **kwargs):
        description = kwargs.pop('description', None)
        status = kwargs.pop('status', None)
        super().__init__(**kwargs)
        if description is not None and self.project_desc is None:
            self.project_desc = description
        if status is not None:
            self.status = status

    @property
    def description(self):
        return self.project_desc

    @description.setter
    def description(self, value):
        self.project_desc = value


# Backward-compatible alias for tests/imports expecting Project
Project = SysProject

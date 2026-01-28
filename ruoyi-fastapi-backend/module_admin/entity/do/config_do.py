from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import YesNoEnum


class SysConfig(LegacyBaseModel):
    """
    参数配置表
    """

    __tablename__ = 'sys_config'

    config_id = Column(Integer, primary_key=True, autoincrement=True, comment='参数主键')
    config_name = Column(String(100), nullable=True, default='', comment='参数名称')
    config_key = Column(String(100), nullable=True, default='', comment='参数键名')
    config_value = Column(String(500), nullable=True, default='', comment='参数键值')
    config_type = Column(String(1), nullable=True, default=YesNoEnum.NO.value, comment='系统内置（Y是 N否）')
    remark = Column(String(500), nullable=True, default=None, comment='备注')

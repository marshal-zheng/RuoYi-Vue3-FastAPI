from sqlalchemy import JSON, Column, Integer, String, UniqueConstraint

from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import StatusEnum, YesNoEnum


class DictTypeDO(LegacyBaseModel):
    """
    字典类型表
    """

    __tablename__ = 'sys_dict_type'

    dict_id = Column(Integer, primary_key=True, autoincrement=True, comment='字典主键')
    dict_name = Column(String(100), nullable=True, default='', comment='字典名称')
    dict_type = Column(String(100), nullable=True, default='', comment='字典类型')
    status = Column(String(1), nullable=True, default=StatusEnum.NORMAL.value, comment='状态（0正常 1停用）')
    remark = Column(JSON(none_as_null=True), nullable=True, default=None, comment='备注文档')

    __table_args__ = (UniqueConstraint('dict_type', name='uq_sys_dict_type_dict_type'),)


class DictDataDO(LegacyBaseModel):
    """
    字典数据表
    """

    __tablename__ = 'sys_dict_data'

    dict_code = Column(Integer, primary_key=True, autoincrement=True, comment='字典编码')
    dict_sort = Column(Integer, nullable=True, default=0, comment='字典排序')
    dict_label = Column(String(100), nullable=True, default='', comment='字典标签')
    dict_value = Column(String(100), nullable=True, default='', comment='字典键值')
    dict_type = Column(String(100), nullable=True, default='', comment='字典类型')
    css_class = Column(String(100), nullable=True, default=None, comment='样式属性（其他样式扩展）')
    list_class = Column(String(100), nullable=True, default=None, comment='表格回显样式')
    is_default = Column(String(1), nullable=True, default=YesNoEnum.NO.value, comment='是否默认（Y是 N否）')
    status = Column(String(1), nullable=True, default=StatusEnum.NORMAL.value, comment='状态（0正常 1停用）')
    remark = Column(JSON(none_as_null=True), nullable=True, default=None, comment='备注文档')

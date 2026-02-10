from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum
from utils.sensitive import sensitive_string_with_hash


class DeptDO(LegacyBaseModel):
    """
    部门表
    """

    __tablename__ = 'sys_dept'

    dept_id = Column(Integer, primary_key=True, autoincrement=True, comment='部门id')
    parent_id = Column(Integer, default=0, comment='父部门id')
    ancestors = Column(String(50), nullable=True, default='', comment='祖级列表')
    dept_name = Column(String(30), nullable=True, default='', comment='部门名称')
    order_num = Column(Integer, default=0, comment='显示顺序')
    leader = Column(String(20), nullable=True, default=None, comment='负责人')
    phone, phone_hash = sensitive_string_with_hash(
        'phone',
        nullable=True,
        default=None,
        comment='联系电话',
    )
    email = Column(String(50), nullable=True, default=None, comment='邮箱')
    status = Column(String(1), nullable=True, default=StatusEnum.NORMAL.value, comment='部门状态（0正常 1停用）')
    del_flag = Column(String(1), nullable=True, default=DelFlagEnum.EXIST.value, comment='删除标志（0代表存在 2代表删除）')

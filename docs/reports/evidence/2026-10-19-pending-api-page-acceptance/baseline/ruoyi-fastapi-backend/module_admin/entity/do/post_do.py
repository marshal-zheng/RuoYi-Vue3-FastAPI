from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import StatusEnum


class PostDO(LegacyBaseModel):
    """
    岗位信息表
    """

    __tablename__ = 'sys_post'

    post_id = Column(Integer, primary_key=True, autoincrement=True, comment='岗位ID')
    post_code = Column(String(64), nullable=False, comment='岗位编码')
    post_name = Column(String(50), nullable=False, comment='岗位名称')
    post_sort = Column(Integer, nullable=False, comment='显示顺序')
    status = Column(String(1), nullable=False, default=StatusEnum.NORMAL.value, comment='状态（0正常 1停用）')
    remark = Column(String(500), nullable=True, default=None, comment='备注')

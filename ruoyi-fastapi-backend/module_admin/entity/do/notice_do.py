from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, LargeBinary, String
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import StatusEnum


class NoticeDO(LegacyBaseModel):
    """
    通知公告表
    """

    __tablename__ = 'sys_notice'

    notice_id = Column(Integer, primary_key=True, autoincrement=True, comment='公告ID')
    notice_title = Column(String(50), nullable=False, comment='公告标题')
    notice_type = Column(String(1), nullable=False, comment='公告类型（1通知 2公告）')
    notice_content = Column(LargeBinary, comment='公告内容')
    status = Column(String(1), default=StatusEnum.NORMAL.value, comment='公告状态（0正常 1关闭）')
    remark = Column(String(255), comment='备注')

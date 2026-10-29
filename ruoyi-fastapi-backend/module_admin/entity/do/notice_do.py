from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
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
    # UTF-8 HTML up to 1 MiB: MySQL needs MEDIUMTEXT (plain TEXT holds only 64 KiB).
    notice_content = Column(Text().with_variant(MEDIUMTEXT(), 'mysql'), comment='公告内容（净化后的HTML）')
    status = Column(String(1), default=StatusEnum.NORMAL.value, comment='公告状态（0正常 1关闭）')
    remark = Column(String(255), comment='备注')

from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.orm import relationship
from module_admin.entity.do.base import LegacyBaseModel
from module_admin.entity.do.enums import StatusEnum


class DeviceCategoryDO(LegacyBaseModel):
    """
    设备分类数据对象
    """
    __tablename__ = 'sys_device_category'

    device_category_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='设备分类ID')
    name = Column(String(50), nullable=False, unique=True, comment='分类名称')
    descr = Column(String(255), comment='分类描述')
    status = Column(String(1), default=StatusEnum.NORMAL.value, comment='状态（0正常 1停用）')
    remark = Column(String(500), comment='备注')

    # 关系：一个分类可以有多个设备
    devices = relationship("DeviceDO", back_populates="category")

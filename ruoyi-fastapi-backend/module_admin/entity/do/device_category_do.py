from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.orm import relationship
from config.database import Base


class DeviceCategoryDO(Base):
    """
    设备分类数据对象
    """
    __tablename__ = 'sys_device_category'

    device_category_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='设备分类ID')
    name = Column(String(50), nullable=False, unique=True, comment='分类名称')
    descr = Column(String(255), comment='分类描述')
    status = Column(String(1), default='0', comment='状态（0正常 1停用）')
    create_by = Column(String(64), comment='创建者')
    create_time = Column(DateTime, comment='创建时间')
    update_by = Column(String(64), comment='更新者')
    update_time = Column(DateTime, comment='更新时间')
    remark = Column(String(500), comment='备注')

    # 关系：一个分类可以有多个设备
    devices = relationship("DeviceDO", back_populates="category")

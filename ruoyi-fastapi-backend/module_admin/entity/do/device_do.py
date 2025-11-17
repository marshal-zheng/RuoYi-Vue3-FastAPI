from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from config.database import Base


class DeviceDO(Base):
    """
    设备数据对象
    """
    __tablename__ = 'sys_device'

    device_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='设备ID')
    device_name = Column(String(100), nullable=False, comment='设备名称')
    device_category_id = Column(BigInteger, ForeignKey('sys_device_category.device_category_id'), comment='设备分类ID')
    category_name = Column(String(50), comment='分类名称（冗余字段）')
    device_type = Column(String(50), comment='设备类型')
    manufacturer = Column(String(100), comment='制造商')
    model = Column(String(100), comment='型号')
    version = Column(String(50), comment='版本')
    bus_type = Column(String(50), comment='总线类型')
    remark = Column(String(500), comment='备注')
    create_by = Column(String(64), comment='创建者')
    create_time = Column(DateTime, comment='创建时间')
    update_by = Column(String(64), comment='更新者')
    update_time = Column(DateTime, comment='更新时间')

    # 关系：设备属于一个分类
    category = relationship("DeviceCategoryDO", back_populates="devices")
    # 关系：一个设备有多个接口
    interfaces = relationship("DeviceInterfaceDO", back_populates="device", cascade="all, delete-orphan")


class DeviceInterfaceDO(Base):
    """
    设备接口数据对象
    """
    __tablename__ = 'sys_device_interface'

    interface_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='接口ID')
    device_id = Column(BigInteger, ForeignKey('sys_device.device_id'), nullable=False, comment='设备ID')
    interface_name = Column(String(50), nullable=False, comment='接口名称')
    interface_type = Column(String(20), nullable=False, comment='接口类型（RS422/RS485/CAN/LAN/1553B）')
    position = Column(String(20), default='right', comment='端口位置（left/right/top/bottom）')
    description = Column(String(255), comment='接口描述')
    params = Column(JSON, comment='接口参数配置（JSON格式）')
    message_config = Column(JSON, comment='报文配置（JSON格式）')
    create_time = Column(DateTime, comment='创建时间')
    update_time = Column(DateTime, comment='更新时间')

    # 关系：接口属于一个设备
    device = relationship("DeviceDO", back_populates="interfaces")

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DeviceQueryModel(BaseModel):
    """
    设备查询模型
    """
    device_name: Optional[str] = Field(None, description="设备名称")
    bus_type: Optional[str] = Field(None, description="总线类型")
    begin_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    page_num: int = Field(1, description="页码")
    page_size: int = Field(10, description="每页数量")


class DeviceInterfaceModel(BaseModel):
    """
    设备接口模型
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    interface_id: Optional[int] = Field(None, description="接口ID")
    device_id: Optional[int] = Field(None, description="设备ID")
    interface_name: str = Field(..., description="接口名称")
    interface_type: str = Field(..., description="接口类型（RS422/RS485/CAN/LAN/1553B）")
    position: str = Field('right', description="端口位置（left/right/top/bottom）")
    description: Optional[str] = Field(None, description="接口描述")
    params: Optional[Dict[str, Any]] = Field(None, description="接口参数配置")
    message_config: Optional[Dict[str, Any]] = Field(None, description="报文配置")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")


class DeviceModel(BaseModel):
    """
    设备模型
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    device_id: Optional[int] = Field(None, description="设备ID")
    device_name: str = Field(..., description="设备名称")
    device_category_id: Optional[int] = Field(None, description="设备分类ID")
    category_name: Optional[str] = Field(None, description="分类名称")
    device_type: Optional[str] = Field(None, description="设备类型")
    manufacturer: Optional[str] = Field(None, description="制造商")
    model: Optional[str] = Field(None, description="型号")
    version: Optional[str] = Field(None, description="版本")
    bus_type: Optional[str] = Field(None, description="总线类型")
    remark: Optional[str] = Field(None, description="备注")
    create_by: Optional[str] = Field(None, description="创建者")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_by: Optional[str] = Field(None, description="更新者")
    update_time: Optional[datetime] = Field(None, description="更新时间")
    interfaces: List[DeviceInterfaceModel] = Field(default_factory=list, description="设备接口列表")


class DeviceListModel(BaseModel):
    """
    设备列表模型（不包含接口详情）
    """
    device_id: int = Field(..., description="设备ID")
    device_name: str = Field(..., description="设备名称")
    category_name: Optional[str] = Field(None, description="分类名称")
    bus_interfaces: Optional[str] = Field(None, description="总线接口（格式化显示）")
    create_by: Optional[str] = Field(None, description="创建者")
    update_time: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True

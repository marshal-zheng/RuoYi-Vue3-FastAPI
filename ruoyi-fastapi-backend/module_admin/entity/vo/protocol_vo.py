from datetime import datetime
from pydantic import ConfigDict, Field
from module_admin.entity.vo.base import CamelModelBase
from pydantic.alias_generators import to_camel
from typing import Optional, Any
from module_admin.annotation.pydantic_annotation import as_query


class ProtocolModel(CamelModelBase):
    """
    协议管理表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    protocol_id: Optional[int] = Field(default=None, description='协议ID')
    protocol_name: Optional[str] = Field(default=None, description='协议名称')
    protocol_type: Optional[str] = Field(default=None, description='协议类型')
    status: Optional[str] = Field(default='0', description='状态')
    description: Optional[str] = Field(default=None, description='协议描述')
    protocol_config: Optional[Any] = Field(default=None, description='协议配置')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    del_flag: Optional[str] = Field(default='0', description='删除标志')


class ProtocolQueryModel(ProtocolModel):
    """
    协议管理不分页查询模型
    """

    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class ProtocolPageQueryModel(ProtocolQueryModel):
    """
    协议管理分页查询模型
    """

    page: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddProtocolModel(CamelModelBase):
    """
    新增协议模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    protocol_name: Optional[str] = Field(default=None, description='协议名称')
    protocol_type: Optional[str] = Field(default=None, description='协议类型')

    # 1553B fields
    bus_speed: Optional[int] = Field(default=None, description='总线速率')
    word_length: Optional[int] = Field(default=None, description='字长')
    rt_address: Optional[int] = Field(default=None, description='RT地址')
    sub_address: Optional[int] = Field(default=None, description='子地址')
    word_count: Optional[int] = Field(default=None, description='字数')

    # CAN fields
    baud_rate: Optional[int] = Field(default=None, description='波特率')
    can_id: Optional[int] = Field(default=None, description='CAN ID')
    data_length: Optional[int] = Field(default=None, description='数据长度')

    # RS422 fields
    data_bits: Optional[int] = Field(default=None, description='数据位')
    stop_bits: Optional[int] = Field(default=None, description='停止位')
    parity: Optional[str] = Field(default=None, description='校验位')

    # Ethernet fields
    ip_address: Optional[str] = Field(default=None, description='IP地址')
    port: Optional[int] = Field(default=None, description='端口')
    protocol: Optional[str] = Field(default=None, description='传输协议')


class DeleteProtocolModel(CamelModelBase):
    """
    删除协议模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    protocol_ids: str = Field(description='需要删除的协议ID')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

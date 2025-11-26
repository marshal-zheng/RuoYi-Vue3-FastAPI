from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional, List, Any


class SimulationSessionModel(BaseModel):
    """
    仿真会话模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    session_id: Optional[str] = Field(default=None, description='会话ID')
    project_id: int = Field(description='项目ID')
    version_id: int = Field(description='版本ID')
    status: Optional[str] = Field(default='created', description='状态')
    start_time: Optional[datetime] = Field(default=None, description='开始时间')
    end_time: Optional[datetime] = Field(default=None, description='结束时间')
    create_by: Optional[str] = Field(default=None, description='创建者')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class CreateSimulationSessionModel(BaseModel):
    """
    创建仿真会话请求模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    project_id: int = Field(description='项目ID')
    version_id: int = Field(description='版本ID')
    create_by: Optional[str] = Field(default=None, description='创建者')


class SimulationMessageModel(BaseModel):
    """
    仿真报文模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    message_id: Optional[str] = Field(default=None, description='报文ID')
    session_id: str = Field(description='会话ID')
    sender_node_id: Optional[str] = Field(default=None, description='发送节点ID')
    sender_port_id: Optional[str] = Field(default=None, description='发送端口ID')
    receiver_node_id: Optional[str] = Field(default=None, description='接收节点ID')
    receiver_port_id: Optional[str] = Field(default=None, description='接收端口ID')
    protocol_type: Optional[str] = Field(default=None, description='协议类型')
    size_bytes: Optional[int] = Field(default=0, description='报文大小（字节）')
    send_timestamp: Optional[float] = Field(default=None, description='发送时间戳')
    receive_timestamp: Optional[float] = Field(default=None, description='接收时间戳')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class SimulationBandwidthModel(BaseModel):
    """
    仿真带宽数据模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: Optional[int] = Field(default=None, description='主键ID')
    session_id: str = Field(description='会话ID')
    node_id: Optional[str] = Field(default=None, description='节点ID')
    port_id: Optional[str] = Field(default=None, description='端口ID')
    timestamp: Optional[float] = Field(default=None, description='时间戳')
    bandwidth_mbps: Optional[float] = Field(default=0, description='带宽（Mbps）')
    message_count: Optional[int] = Field(default=0, description='报文数量')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class SimulationAlarmModel(BaseModel):
    """
    仿真告警模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    alarm_id: Optional[str] = Field(default=None, description='告警ID')
    session_id: str = Field(description='会话ID')
    alarm_type: Optional[str] = Field(default=None, description='告警类型')
    severity: Optional[str] = Field(default='warning', description='严重程度')
    affected_nodes: Optional[List[str]] = Field(default=None, description='受影响节点')
    message: Optional[str] = Field(default=None, description='告警消息')
    timestamp: Optional[float] = Field(default=None, description='时间戳')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class SimulationQueryModel(BaseModel):
    """
    仿真数据查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    session_id: str = Field(description='会话ID')
    start_time: Optional[float] = Field(default=None, description='开始时间戳')
    end_time: Optional[float] = Field(default=None, description='结束时间戳')


class SimulationExportModel(BaseModel):
    """
    仿真数据导出模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    session_id: str = Field(description='会话ID')
    export_format: str = Field(default='json', description='导出格式（json/csv）')
    data_type: str = Field(default='messages', description='数据类型（messages/bandwidth/alarms）')

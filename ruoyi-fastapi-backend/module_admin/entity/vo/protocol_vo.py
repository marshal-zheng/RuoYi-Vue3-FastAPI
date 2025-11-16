from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional, Any
from module_admin.annotation.pydantic_annotation import as_query


class ProtocolModel(BaseModel):
    """
    协议管理表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    protocol_id: Optional[int] = Field(default=None, description='协议ID')
    protocol_name: Optional[str] = Field(default=None, description='协议名称')
    protocol_type: Optional[str] = Field(default=None, description='协议类型')
    version: Optional[str] = Field(default='1.0', description='版本号')
    status: Optional[str] = Field(default='0', description='状态')
    is_locked: Optional[bool] = Field(default=False, description='是否固化')
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

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteProtocolModel(BaseModel):
    """
    删除协议模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    protocol_ids: str = Field(description='需要删除的协议ID')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')


class LockProtocolModel(BaseModel):
    """
    固化/解除固化协议模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    protocol_id: int = Field(description='协议ID')
    is_locked: bool = Field(description='是否固化')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

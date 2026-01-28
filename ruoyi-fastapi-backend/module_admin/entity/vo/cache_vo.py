from pydantic import ConfigDict, Field
from module_admin.entity.vo.base import CamelModelBase
from pydantic.alias_generators import to_camel
from typing import Any, List, Optional


class CacheMonitorModel(CamelModelBase):
    """
    缓存监控信息对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    command_stats: Optional[List] = Field(default=[], description='命令统计')
    db_size: Optional[int] = Field(default=None, description='Key数量')
    info: Optional[dict] = Field(default={}, description='Redis信息')


class CacheInfoModel(CamelModelBase):
    """
    缓存监控对象对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cache_key: Optional[str] = Field(default=None, description='缓存键名')
    cache_name: Optional[str] = Field(default=None, description='缓存名称')
    cache_value: Optional[Any] = Field(default=None, description='缓存内容')
    remark: Optional[str] = Field(default=None, description='备注')
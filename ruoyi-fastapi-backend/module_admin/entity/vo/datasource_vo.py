from pydantic import Field
from module_admin.entity.vo.base import CamelModelBase
from typing import Optional
from datetime import datetime
from module_admin.annotation.pydantic_annotation import as_query


@as_query
class DataSourceQueryModel(CamelModelBase):
    name: Optional[str] = Field(None, description='数据源名称')
    type: Optional[str] = Field(None, description='数据源类型')
    status: Optional[str] = Field(None, description='连接状态')
    page_num: int = Field(1, description='页码')
    page_size: int = Field(10, description='每页数量')


class DataSourceModel(CamelModelBase):
    id: Optional[int] = Field(None, description='数据源ID')
    name: str = Field(..., min_length=1, max_length=100, description='数据源名称')
    type: str = Field(..., description='数据源类型')
    host: str = Field(..., description='主机地址')
    port: int = Field(..., description='端口')
    username: Optional[str] = Field(None, description='用户名')
    password: Optional[str] = Field(None, description='密码')
    database_name: Optional[str] = Field(None, description='数据库名/存储桶')
    description: Optional[str] = Field(None, max_length=500, description='描述')
    extra_config: Optional[dict] = Field(default_factory=dict, description='类型独有配置')


class TestConnectionModel(CamelModelBase):
    type: str = Field(..., description='数据源类型')
    host: str = Field(..., description='主机地址')
    port: int = Field(..., description='端口')
    username: Optional[str] = Field(None, description='用户名')
    password: Optional[str] = Field(None, description='密码')
    database_name: Optional[str] = Field(None, description='数据库名/存储桶')
    extra_config: Optional[dict] = Field(default_factory=dict, description='类型独有配置')

from datetime import datetime
from pydantic import ConfigDict, Field
from module_admin.entity.vo.base import CamelModelBase
from pydantic.alias_generators import to_camel
from typing import Optional, Literal
from module_admin.annotation.pydantic_annotation import as_query


class AuditLogModel(CamelModelBase):
    """
    审计日志表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    audit_id: Optional[int] = Field(default=None, description='审计日志主键')
    action: Optional[Literal['READ', 'INSERT', 'UPDATE', 'DELETE']] = Field(default=None, description='动作类型')
    table_name: Optional[str] = Field(default=None, description='表名')
    pk: Optional[str] = Field(default=None, description='主键标识')
    before_data: Optional[str] = Field(default=None, description='变更前数据(JSON)')
    after_data: Optional[str] = Field(default=None, description='变更后数据(JSON)')
    changed_fields: Optional[str] = Field(default=None, description='变更字段(JSON)')
    query: Optional[str] = Field(default=None, description='读操作SQL/描述')
    operator_id: Optional[str] = Field(default=None, description='操作人ID')
    operator_name: Optional[str] = Field(default=None, description='操作人')
    operator_ip: Optional[str] = Field(default=None, description='操作IP')
    request_id: Optional[str] = Field(default=None, description='请求ID')
    trace_id: Optional[str] = Field(default=None, description='链路ID')
    request_method: Optional[str] = Field(default=None, description='请求方法')
    request_path: Optional[str] = Field(default=None, description='请求路径')
    user_agent: Optional[str] = Field(default=None, description='User-Agent')
    create_time: Optional[datetime] = Field(default=None, description='记录时间')


class AuditLogQueryModel(AuditLogModel):
    """
    审计日志不分页查询模型
    """

    order_by_column: Optional[str] = Field(default=None, description='排序字段')
    is_asc: Optional[Literal['ascending', 'descending']] = Field(default=None, description='排序方式')
    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class AuditLogPageQueryModel(AuditLogQueryModel):
    """
    审计日志分页查询模型
    """

    page: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteAuditLogModel(CamelModelBase):
    """
    删除审计日志模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    audit_ids: str = Field(description='需要删除的审计日志主键')

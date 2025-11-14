from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional
from module_admin.annotation.pydantic_annotation import as_query


class ProjectModel(BaseModel):
    """
    工程管理表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    project_id: Optional[int] = Field(default=None, description='工程编号')
    project_name: Optional[str] = Field(default=None, description='工程名称')
    project_code: Optional[str] = Field(default=None, description='工程编码')
    project_desc: Optional[str] = Field(default=None, description='工程描述')
    create_by: Optional[str] = Field(default=None, description='创建人')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    del_flag: Optional[str] = Field(default='0', description='删除标志（0代表存在 2代表删除）')


class ProjectQueryModel(ProjectModel):
    """
    工程管理不分页查询模型
    """

    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class ProjectPageQueryModel(ProjectQueryModel):
    """
    工程管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteProjectModel(BaseModel):
    """
    删除工程模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    project_ids: str = Field(description='需要删除的工程id')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
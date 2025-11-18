from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import Optional
from module_admin.annotation.pydantic_annotation import as_query


class ProjectVersionModel(BaseModel):
    """
    项目版本管理表对应pydantic模型
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )

    version_id: Optional[int] = Field(default=None, description='版本ID')
    project_id: Optional[int] = Field(default=None, description='项目ID')
    version_number: Optional[str] = Field(default=None, description='版本号')
    version_name: Optional[str] = Field(default=None, description='版本名称')
    description: Optional[str] = Field(default=None, description='版本描述')
    status: Optional[str] = Field(default='1', description='状态（0停用 1启用）')
    is_locked: Optional[str] = Field(default='0', description='是否固化（0否 1是）')
    locked_time: Optional[datetime] = Field(default=None, description='固化时间')
    locked_by: Optional[str] = Field(default=None, description='固化人')
    create_by: Optional[str] = Field(default=None, description='创建人')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')
    del_flag: Optional[str] = Field(default='0', description='删除标志（0代表存在 2代表删除）')


class ProjectVersionQueryModel(ProjectVersionModel):
    """
    项目版本管理不分页查询模型
    """

    begin_time: Optional[str] = Field(default=None, description='开始时间')
    end_time: Optional[str] = Field(default=None, description='结束时间')


@as_query
class ProjectVersionPageQueryModel(ProjectVersionQueryModel):
    """
    项目版本管理分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteProjectVersionModel(BaseModel):
    """
    删除项目版本模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_ids: str = Field(description='需要删除的版本ID')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')


class CloneProjectVersionModel(BaseModel):
    """
    克隆项目版本模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source_version_id: int = Field(description='源版本ID')
    version_number: str = Field(description='新版本号')
    version_name: str = Field(description='新版本名称')
    description: Optional[str] = Field(default=None, description='版本描述')
    create_by: Optional[str] = Field(default=None, description='创建人')
    create_time: Optional[datetime] = Field(default=None, description='创建时间')


class LockProjectVersionModel(BaseModel):
    """
    固化/解除固化项目版本模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    version_id: int = Field(description='版本ID')
    is_locked: str = Field(description='是否固化（0否 1是）')
    locked_by: Optional[str] = Field(default=None, description='固化人')
    locked_time: Optional[datetime] = Field(default=None, description='固化时间')
    update_by: Optional[str] = Field(default=None, description='更新者')
    update_time: Optional[datetime] = Field(default=None, description='更新时间')

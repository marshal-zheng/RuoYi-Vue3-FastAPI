from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size

from module_admin.annotation.pydantic_annotation import as_query
from module_admin.entity.vo.base import CamelModelBase
from module_admin.entity.vo.remark_vo import RemarkReadProjection, RemarkValue, RemarkWriteGuard


class PostModel(RemarkWriteGuard):
    """
    岗位信息表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    post_id: int | None = Field(default=None, description='岗位ID')
    post_code: str | None = Field(default=None, description='岗位编码')
    post_name: str | None = Field(default=None, description='岗位名称')
    post_sort: int | None = Field(default=None, description='显示顺序')
    status: Literal['0', '1'] | None = Field(default=None, description='状态（0正常 1停用）')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: RemarkValue = Field(default=None, description='备注')

    @NotBlank(field_name='post_code', message='岗位编码不能为空')
    @Size(field_name='post_code', min_length=0, max_length=64, message='岗位编码长度不能超过64个字符')
    def get_post_code(self):
        return self.post_code

    @NotBlank(field_name='post_name', message='岗位名称不能为空')
    @Size(field_name='post_name', min_length=0, max_length=50, message='岗位名称长度不能超过50个字符')
    def get_post_name(self):
        return self.post_name

    @NotBlank(field_name='post_sort', message='显示顺序不能为空')
    def get_post_sort(self):
        return self.post_sort

    def validate_fields(self):
        self.get_post_code()
        self.get_post_name()
        self.get_post_sort()


class PostInfoModel(PostModel, RemarkReadProjection):
    """Post projection used in nested user-detail responses."""


class PostQueryModel(CamelModelBase):
    post_id: int | None = Field(default=None, description='岗位ID')
    post_code: str | None = Field(default=None, description='岗位编码')
    post_name: str | None = Field(default=None, description='岗位名称')
    post_sort: int | None = Field(default=None, description='显示顺序')
    status: Literal['0', '1'] | None = Field(default=None, description='状态（0正常 1停用）')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    """
    岗位管理不分页查询模型
    """

    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')


@as_query
class PostPageQueryModel(PostQueryModel):
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')
    """
    岗位管理分页查询模型
    """

    page: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeletePostModel(CamelModelBase):
    """
    删除岗位模型
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    post_ids: str = Field(description='需要删除的岗位ID')

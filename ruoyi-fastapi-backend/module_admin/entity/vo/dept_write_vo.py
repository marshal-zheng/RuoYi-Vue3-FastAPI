"""Public department writes, separated from the read/audit model."""

from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic_validation_decorator import FieldValidationError

from module_admin.entity.vo.base import CamelModelBase
from module_admin.entity.vo.dept_vo import DeptModel


class _DeptEditorFields(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    # Omission preserves existing values; explicit null cannot clear structural fields.
    parent_id: int = Field(default=None, ge=0, description='父部门ID, 0为根部门')
    dept_name: str = Field(default=None, min_length=1, max_length=30, description='部门名称')
    order_num: int = Field(default=None, description='显示顺序')
    leader: str | None = Field(default=None, max_length=20, description='负责人')
    phone: str | None = Field(default=None, max_length=11, description='联系电话')
    email: str | None = Field(default=None, max_length=50, description='邮箱')
    status: Literal['0', '1'] = Field(default=None, description='部门状态(0正常 1停用)')

    @model_validator(mode='after')
    def validate_input_fields(self):
        if 'dept_name' in self.model_fields_set and not self.dept_name.strip():
            raise ValueError('部门名称不能为空')
        try:
            DeptModel(**self.model_dump(exclude_unset=True)).validate_fields()
        except FieldValidationError as error:
            raise ValueError(error.message) from error
        return self


class DeptCreateModel(_DeptEditorFields):
    parent_id: int = Field(ge=0, description='父部门ID, 0为根部门')
    dept_name: str = Field(min_length=1, max_length=30, description='部门名称')
    order_num: int = Field(description='显示顺序')


class DeptUpdateModel(_DeptEditorFields):
    dept_id: int = Field(gt=0, description='部门ID')

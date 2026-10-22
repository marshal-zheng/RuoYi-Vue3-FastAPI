"""Public role write inputs, separated by business operation."""

from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic_validation_decorator import FieldValidationError

from module_admin.entity.vo.base import CamelModelBase
from module_admin.entity.vo.remark_vo import RemarkValue
from module_admin.entity.vo.role_vo import RoleModel


class _RoleEditorFields(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    # Missing fields are excluded from the update; supplied null cannot reach non-null columns.
    role_name: str = Field(default=None, max_length=30, description='角色名称')
    role_key: str = Field(default=None, max_length=100, description='角色权限字符串')
    role_sort: int = Field(default=None, description='显示顺序')
    status: Literal['0', '1'] = Field(default=None, description='角色状态')
    menu_check_strictly: bool | None = Field(default=None, description='菜单树选择项是否关联显示')
    remark: RemarkValue = Field(default=None, description='备注')
    menu_ids: list[int] | None = Field(default=None, description='菜单ID; 未提供保留, 空数组或null清空')

    @model_validator(mode='after')
    def validate_input_fields(self):
        role = RoleModel(**self.model_dump(exclude_unset=True))
        try:
            for field in ('role_name', 'role_key', 'role_sort'):
                if field in self.model_fields_set:
                    getattr(role, f'get_{field}')()
        except FieldValidationError as error:
            raise ValueError(error.message) from error
        return self


class RoleCreateModel(_RoleEditorFields):
    role_name: str = Field(min_length=1, max_length=30, description='角色名称')
    role_key: str = Field(min_length=1, max_length=100, description='角色权限字符串')
    role_sort: int = Field(description='显示顺序')


class RoleUpdateModel(_RoleEditorFields):
    role_id: int = Field(gt=0, description='角色ID')


class RoleStatusUpdateModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    role_id: int = Field(gt=0, description='角色ID')
    status: Literal['0', '1'] = Field(description='角色状态')


class RoleDataScopeUpdateModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    role_id: int = Field(gt=0, description='角色ID')
    data_scope: Literal['1', '2', '3', '4', '5'] = Field(description='数据范围')
    dept_check_strictly: bool | None = Field(default=None, description='部门树选择项是否关联显示')
    dept_ids: list[int] | None = Field(default=None, description='部门ID; 未提供保留, 空数组或null清空')

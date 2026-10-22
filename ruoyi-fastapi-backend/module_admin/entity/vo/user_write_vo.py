"""Public user write inputs; persistence and response fields stay in user_vo."""

from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic_validation_decorator import FieldValidationError

from module_admin.entity.vo.base import CamelModelBase
from module_admin.entity.vo.remark_vo import RemarkValue
from module_admin.entity.vo.user_role_write_vo import AuthorizationIds
from module_admin.entity.vo.user_vo import EditUserModel


class UserProfileUpdateModel(CamelModelBase):
    """The authenticated user can edit these profile fields only."""

    model_config = ConfigDict(extra='forbid')

    # An omitted field stays unset; explicitly supplied null is invalid for non-null columns.
    nick_name: str = Field(default=None, max_length=30, description='用户昵称')
    email: str | None = Field(default=None, max_length=50, description='邮箱')
    phonenumber: str | None = Field(default=None, max_length=11, description='手机号码')
    sex: Literal['0', '1', '2'] | None = Field(default=None, description='用户性别')

    @model_validator(mode='after')
    def validate_input_fields(self):
        # Reuse existing domain rules before the controller's audit/error wrapper runs.
        user = EditUserModel(**self.model_dump(exclude_unset=True))
        try:
            user.validate_fields()
        except FieldValidationError as error:
            raise ValueError(error.message) from error
        return self


class _UserEditorFields(UserProfileUpdateModel):
    dept_id: int | None = Field(default=None, description='部门ID')
    user_name: str = Field(default=None, max_length=30, description='用户账号')
    id_card: str | None = Field(default=None, max_length=18, description='身份证号')
    status: Literal['0', '1'] | None = Field(default=None, description='帐号状态')
    remark: RemarkValue = Field(default=None, description='备注')
    role_ids: AuthorizationIds | None = Field(default=None, description='角色ID; 未提供保留, 空数组或null清空')
    post_ids: list[int] | None = Field(default=None, description='岗位ID; 未提供保留, 空数组或null清空')


class UserCreateModel(_UserEditorFields):
    nick_name: str = Field(min_length=1, max_length=30, description='用户昵称')
    user_name: str = Field(min_length=1, max_length=30, description='用户账号')
    password: str = Field(min_length=1, pattern=r"""^[^<>"'|\\]+$""", description='初始密码')


class UserUpdateModel(_UserEditorFields):
    user_id: int = Field(gt=0, description='用户ID')


class UserStatusUpdateModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    user_id: int = Field(gt=0, description='用户ID')
    status: Literal['0', '1'] = Field(description='帐号状态')

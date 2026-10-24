"""Fixed user/role authorization operations; collections are required JSON arrays."""

from typing import Annotated

from pydantic import AfterValidator, ConfigDict, Field

from module_admin.entity.vo.base import CamelModelBase

# Match the integer identities stored by UserDO and RoleDO; do not coerce bool/string/float IDs.
AuthorizationId = Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]
AuthorizationIds = Annotated[list[AuthorizationId], AfterValidator(lambda ids: list(dict.fromkeys(ids)))]


class UserRolesAssignModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    user_id: AuthorizationId = Field(description='用户ID')
    role_ids: AuthorizationIds = Field(description='完整角色ID集合, 空数组清空; 缺失或null无效')


class RoleUsersGrantModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    role_id: AuthorizationId = Field(description='角色ID')
    user_ids: AuthorizationIds = Field(min_length=1, description='增量授权用户ID集合, 不影响其他角色关联')


class RoleUserRevokeModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    role_id: AuthorizationId = Field(description='角色ID')
    user_id: AuthorizationId = Field(description='取消授权的用户ID')


class RoleUsersRevokeModel(CamelModelBase):
    model_config = ConfigDict(extra='forbid')

    role_id: AuthorizationId = Field(description='角色ID')
    user_ids: AuthorizationIds = Field(min_length=1, description='取消授权用户ID集合, 只删除指定关联')

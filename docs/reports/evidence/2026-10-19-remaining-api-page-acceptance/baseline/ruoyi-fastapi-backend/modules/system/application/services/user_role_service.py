"""User-role authorization with complete preflight before transactional relation changes."""

from typing import TYPE_CHECKING

from config.error_codes import ErrorCode
from exceptions.exception import ResourceNotFoundException
from module_admin.entity.do.user_do import UserRoleDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.role_vo import RoleModel
from module_admin.entity.vo.user_vo import UserModel
from modules.system.infrastructure.user_repository import UserRepository
from modules.system.infrastructure.user_role_repository import UserRoleRepository
from utils.transaction_manager import transactional

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from module_admin.entity.vo.user_role_write_vo import (
        RoleUserRevokeModel,
        RoleUsersGrantModel,
        RoleUsersRevokeModel,
        UserRolesAssignModel,
    )
    from modules.system.application.services.role_service import RoleService
    from modules.system.application.services.user_service import UserService


class UserRoleService:
    def __init__(self, user_service: 'UserService', role_service: 'RoleService'):
        self.user_service = user_service
        self.role_service = role_service

    async def _check_users(self, db, user_ids, *, enforce_scope_checks, user_data_scope_sql, **_):
        repo = UserRepository(db)
        for user_id in user_ids:
            user = await repo.get_by_id(user_id)
            if user is None or user.del_flag == '2':
                raise ResourceNotFoundException(error_code=ErrorCode.USER_NOT_FOUND, user_message='用户不存在')
            await self.user_service.check_user_allowed_services(UserModel(userId=user_id))
            if enforce_scope_checks:
                await self.user_service.check_user_data_scope_services(db, user_id, user_data_scope_sql)

    async def _check_roles(self, role_ids, *, enforce_scope_checks, role_data_scope_sql, **_):
        for role_id in role_ids:
            role = await self.role_service.role_repo.find_by_id(role_id)
            if role is None or role.del_flag == '2':
                raise ResourceNotFoundException(error_code=ErrorCode.ROLE_NOT_FOUND, user_message='角色不存在')
            if enforce_scope_checks:
                # Admin may assign/revoke the admin role; its definition remains protected elsewhere.
                await self.role_service.check_role_allowed_services(RoleModel(roleId=role_id))
        if enforce_scope_checks and role_ids:
            await self.role_service.check_role_data_scope_services(','.join(map(str, role_ids)), role_data_scope_sql)

    async def check_user_roles(self, query_db, user_id, role_ids, *, enforce_scope_checks, role_data_scope_sql):
        """Also used by ordinary user editors when they explicitly change role associations."""
        existing = await UserRoleRepository(query_db).find_by_user_id(user_id) if user_id is not None else []
        affected = list(dict.fromkeys([*(role_ids or []), *(row.role_id for row in existing)]))
        await self._check_roles(
            affected, enforce_scope_checks=enforce_scope_checks, role_data_scope_sql=role_data_scope_sql
        )

    @transactional()
    async def assign_user_roles(self, query_db: 'AsyncSession', payload: 'UserRolesAssignModel', **scope):
        await self._check_users(query_db, [payload.user_id], **scope)
        repo = UserRoleRepository(query_db)
        # Replacement checks removed roles too; clearing cannot bypass their scope/protection.
        await self.check_user_roles(
            query_db,
            payload.user_id,
            payload.role_ids,
            enforce_scope_checks=scope['enforce_scope_checks'],
            role_data_scope_sql=scope['role_data_scope_sql'],
        )
        await repo.delete_by_user_id(payload.user_id)
        for role_id in payload.role_ids:
            await repo.add(UserRoleDO(user_id=payload.user_id, role_id=role_id))
        return CrudResponseModel(is_success=True, message='分配成功')

    @transactional()
    async def grant_role_users(self, query_db: 'AsyncSession', payload: 'RoleUsersGrantModel', **scope):
        await self._check_roles([payload.role_id], **scope)
        await self._check_users(query_db, payload.user_ids, **scope)
        repo = UserRoleRepository(query_db)
        for user_id in payload.user_ids:
            if not await repo.find_by_user_and_role(user_id, payload.role_id):
                await repo.add(UserRoleDO(user_id=user_id, role_id=payload.role_id))
        return CrudResponseModel(is_success=True, message='分配成功')

    @transactional()
    async def revoke_role_user(self, query_db: 'AsyncSession', payload: 'RoleUserRevokeModel', **scope):
        await self._check_roles([payload.role_id], **scope)
        await self._check_users(query_db, [payload.user_id], **scope)
        await UserRoleRepository(query_db).delete_by_user_and_role(payload.user_id, payload.role_id)
        return CrudResponseModel(is_success=True, message='取消授权成功')

    @transactional()
    async def revoke_role_users(self, query_db: 'AsyncSession', payload: 'RoleUsersRevokeModel', **scope):
        await self._check_roles([payload.role_id], **scope)
        await self._check_users(query_db, payload.user_ids, **scope)
        repo = UserRoleRepository(query_db)
        for user_id in payload.user_ids:
            await repo.delete_by_user_and_role(user_id, payload.role_id)
        return CrudResponseModel(is_success=True, message='取消授权成功')

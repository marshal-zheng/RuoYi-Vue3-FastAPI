"""User-role relation repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from module_admin.entity.do.user_do import UserRoleDO
from module_admin.repository.base_repository import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserRoleRepository(BaseRepository[UserRoleDO]):
    """用户角色关联 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, UserRoleDO)

    async def find_by_user_id(self, user_id: int) -> list[UserRoleDO]:
        """根据用户ID查找关联。"""
        stmt = select(UserRoleDO).where(UserRoleDO.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_by_user_id(self, user_id: int) -> int:
        """根据用户ID删除关联。"""
        stmt = delete(UserRoleDO).where(UserRoleDO.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def delete_by_user_and_role(self, user_id: int, role_id: int) -> int:
        """根据用户ID和角色ID删除关联。"""
        conditions = []
        if user_id:
            conditions.append(UserRoleDO.user_id == user_id)
        if role_id:
            conditions.append(UserRoleDO.role_id == role_id)

        stmt = delete(UserRoleDO).where(*conditions)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def find_by_user_and_role(self, user_id: int, role_id: int) -> UserRoleDO | None:
        """根据用户ID和角色ID查找关联。"""
        stmt = select(UserRoleDO).where(UserRoleDO.user_id == user_id, UserRoleDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

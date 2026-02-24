"""User-post relation repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from module_admin.entity.do.user_do import UserPostDO
from module_admin.repository.base_repository import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserPostRepository(BaseRepository[UserPostDO]):
    """用户岗位关联 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, UserPostDO)

    async def find_by_user_id(self, user_id: int) -> list[UserPostDO]:
        """根据用户ID查找关联。"""
        stmt = select(UserPostDO).where(UserPostDO.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_by_user_id(self, user_id: int) -> int:
        """根据用户ID删除关联。"""
        stmt = delete(UserPostDO).where(UserPostDO.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.rowcount

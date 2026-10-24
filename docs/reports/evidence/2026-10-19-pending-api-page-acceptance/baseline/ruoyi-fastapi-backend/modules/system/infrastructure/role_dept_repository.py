"""Role-dept relation repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, delete, select

from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.role_do import RoleDeptDO
from module_admin.repository.base_repository import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class RoleDeptRepository(BaseRepository[RoleDeptDO]):
    """角色部门关联 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, RoleDeptDO)

    async def find_by_role_id(self, role_id: int) -> list[RoleDeptDO]:
        """根据角色ID查找关联。"""
        stmt = select(RoleDeptDO).where(RoleDeptDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def find_depts_by_role(self, role_id: int, check_strictly: bool = False) -> list[DeptDO]:
        """获取角色关联的部门。"""
        conditions = [RoleDeptDO.role_id == role_id]

        if check_strictly:
            conditions.append(
                ~DeptDO.dept_id.in_(
                    select(DeptDO.parent_id).select_from(DeptDO).join(
                        RoleDeptDO,
                        and_(
                            RoleDeptDO.dept_id == DeptDO.dept_id,
                            RoleDeptDO.role_id == role_id,
                        ),
                    )
                )
            )

        stmt = (
            select(DeptDO)
            .join(RoleDeptDO, RoleDeptDO.dept_id == DeptDO.dept_id)
            .where(*conditions)
            .order_by(DeptDO.parent_id, DeptDO.order_num)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_by_role_id(self, role_id: int) -> int:
        """根据角色ID删除关联。"""
        stmt = delete(RoleDeptDO).where(RoleDeptDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def batch_add(self, role_id: int, dept_ids: list[int]):
        """批量添加角色部门关联。"""
        for dept_id in dept_ids:
            self.db.add(RoleDeptDO(role_id=role_id, dept_id=dept_id))
        await self.db.flush()

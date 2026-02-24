"""Role-menu relation repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, delete, select

from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleMenuDO
from module_admin.repository.base_repository import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class RoleMenuRepository(BaseRepository[RoleMenuDO]):
    """角色菜单关联 Repository。"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, RoleMenuDO)

    async def find_by_role_id(self, role_id: int) -> list[RoleMenuDO]:
        """根据角色ID查找关联。"""
        stmt = select(RoleMenuDO).where(RoleMenuDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def find_menus_by_role(self, role_id: int, check_strictly: bool = False) -> list[MenuDO]:
        """获取角色关联的菜单。"""
        conditions = [RoleMenuDO.role_id == role_id]

        if check_strictly:
            conditions.append(
                ~MenuDO.menu_id.in_(
                    select(MenuDO.parent_id).select_from(MenuDO).join(
                        RoleMenuDO,
                        and_(
                            RoleMenuDO.menu_id == MenuDO.menu_id,
                            RoleMenuDO.role_id == role_id,
                        ),
                    )
                )
            )

        stmt = (
            select(MenuDO)
            .join(RoleMenuDO, RoleMenuDO.menu_id == MenuDO.menu_id)
            .where(*conditions)
            .order_by(MenuDO.parent_id, MenuDO.order_num)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_by_role_id(self, role_id: int) -> int:
        """根据角色ID删除关联。"""
        stmt = delete(RoleMenuDO).where(RoleMenuDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def batch_add(self, role_id: int, menu_ids: list[int]):
        """批量添加角色菜单关联。"""
        for menu_id in menu_ids:
            self.db.add(RoleMenuDO(role_id=role_id, menu_id=menu_id))
        await self.db.flush()

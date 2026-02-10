"""
菜单 Repository
提供菜单相关的数据访问操作
"""
from typing import Optional, List
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from utils.db_filters import not_deleted


class MenuRepository(BaseRepository[MenuDO]):
    """
    菜单 Repository
    
    继承 BaseRepository 并扩展菜单特有的查询方法
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, MenuDO)
    
    async def find_by_id(self, menu_id: int) -> Optional[MenuDO]:
        """根据ID查找菜单"""
        stmt = select(MenuDO).where(MenuDO.menu_id == menu_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_parent_and_name(
        self,
        parent_id: Optional[int],
        menu_name: Optional[str],
        menu_type: Optional[str] = None
    ) -> Optional[MenuDO]:
        """根据父菜单ID、菜单名称、菜单类型查找菜单"""
        conditions = []
        if parent_id is not None:
            conditions.append(MenuDO.parent_id == parent_id)
        if menu_name:
            conditions.append(MenuDO.menu_name == menu_name)
        if menu_type:
            conditions.append(MenuDO.menu_type == menu_type)
        
        stmt = select(MenuDO).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_all_active(self) -> List[MenuDO]:
        """获取所有有效菜单"""
        stmt = (
            select(MenuDO)
            .where(MenuDO.status == StatusEnum.NORMAL.value)
            .order_by(MenuDO.order_num)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_menus_by_user(self, user_id: int, is_admin: bool = False) -> List[MenuDO]:
        """
        根据用户获取菜单列表
        
        Args:
            user_id: 用户ID
            is_admin: 是否为管理员
        
        Returns:
            菜单列表
        """
        if is_admin:
            return await self.find_all_active()
        
        stmt = (
            select(MenuDO)
            .select_from(UserDO)
            .join(UserRoleDO, UserDO.user_id == UserRoleDO.user_id, isouter=True)
            .join(
                RoleDO,
                and_(
                    UserRoleDO.role_id == RoleDO.role_id,
                    RoleDO.status == StatusEnum.NORMAL.value,
                    not_deleted(RoleDO.del_flag)
                ),
                isouter=True
            )
            .join(RoleMenuDO, RoleDO.role_id == RoleMenuDO.role_id, isouter=True)
            .join(
                MenuDO,
                and_(
                    RoleMenuDO.menu_id == MenuDO.menu_id,
                    MenuDO.status == StatusEnum.NORMAL.value
                )
            )
            .where(
                UserDO.user_id == user_id,
                UserDO.status == StatusEnum.NORMAL.value,
                not_deleted(UserDO.del_flag)
            )
            .order_by(MenuDO.order_num)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_with_filters(
        self,
        user_id: int = None,
        is_admin: bool = False,
        status: Optional[str] = None,
        menu_name: Optional[str] = None,
        visible: Optional[str] = None
    ) -> List[MenuDO]:
        """
        查询菜单列表（带过滤条件）
        
        Args:
            user_id: 用户ID
            is_admin: 是否为管理员
            status: 状态
            menu_name: 菜单名称
            visible: 显示状态
        
        Returns:
            菜单列表
        """
        if is_admin:
            conditions = []
            if status:
                conditions.append(MenuDO.status == status)
            if menu_name:
                conditions.append(MenuDO.menu_name.like(f'%{menu_name}%'))
            if visible:
                conditions.append(MenuDO.visible == visible)
            
            stmt = (
                select(MenuDO)
                .where(*conditions) if conditions else select(MenuDO)
            ).order_by(MenuDO.order_num).distinct()
        else:
            menu_conditions = [
                RoleMenuDO.menu_id == MenuDO.menu_id
            ]
            if status:
                menu_conditions.append(MenuDO.status == status)
            if menu_name:
                menu_conditions.append(MenuDO.menu_name.like(f'%{menu_name}%'))
            if visible:
                menu_conditions.append(MenuDO.visible == visible)
            
            stmt = (
                select(MenuDO)
                .select_from(UserDO)
                .join(UserRoleDO, UserDO.user_id == UserRoleDO.user_id, isouter=True)
                .join(
                    RoleDO,
                    and_(
                        UserRoleDO.role_id == RoleDO.role_id,
                        RoleDO.status == StatusEnum.NORMAL.value,
                        not_deleted(RoleDO.del_flag)
                    ),
                    isouter=True
                )
                .join(RoleMenuDO, RoleDO.role_id == RoleMenuDO.role_id, isouter=True)
                .join(MenuDO, and_(*menu_conditions))
                .where(
                    UserDO.user_id == user_id,
                    UserDO.status == StatusEnum.NORMAL.value,
                    not_deleted(UserDO.del_flag)
                )
                .order_by(MenuDO.order_num)
                .distinct()
            )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_by_id(self, menu_id: int) -> int:
        """根据ID删除菜单"""
        stmt = delete(MenuDO).where(MenuDO.menu_id == menu_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def count_children(self, menu_id: int) -> int:
        """统计子菜单数量"""
        stmt = (
            select(func.count())
            .select_from(MenuDO)
            .where(MenuDO.parent_id == menu_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_roles(self, menu_id: int) -> int:
        """统计关联角色数量"""
        stmt = (
            select(func.count())
            .select_from(RoleMenuDO)
            .where(RoleMenuDO.menu_id == menu_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

"""
菜单 Repository
提供菜单相关的数据访问操作
"""
from typing import Optional, List
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.menu_do import SysMenu
from module_admin.entity.do.role_do import SysRole, SysRoleMenu
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from utils.db_filters import not_deleted


class MenuRepository(BaseRepository[SysMenu]):
    """
    菜单 Repository
    
    继承 BaseRepository 并扩展菜单特有的查询方法
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysMenu)
    
    async def find_by_id(self, menu_id: int) -> Optional[SysMenu]:
        """根据ID查找菜单"""
        stmt = select(SysMenu).where(SysMenu.menu_id == menu_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_parent_and_name(
        self,
        parent_id: Optional[int],
        menu_name: Optional[str],
        menu_type: Optional[str] = None
    ) -> Optional[SysMenu]:
        """根据父菜单ID、菜单名称、菜单类型查找菜单"""
        conditions = []
        if parent_id is not None:
            conditions.append(SysMenu.parent_id == parent_id)
        if menu_name:
            conditions.append(SysMenu.menu_name == menu_name)
        if menu_type:
            conditions.append(SysMenu.menu_type == menu_type)
        
        stmt = select(SysMenu).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_all_active(self) -> List[SysMenu]:
        """获取所有有效菜单"""
        stmt = (
            select(SysMenu)
            .where(SysMenu.status == StatusEnum.NORMAL.value)
            .order_by(SysMenu.order_num)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_menus_by_user(self, user_id: int, is_admin: bool = False) -> List[SysMenu]:
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
            select(SysMenu)
            .select_from(SysUser)
            .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
            .join(
                SysRole,
                and_(
                    SysUserRole.role_id == SysRole.role_id,
                    SysRole.status == StatusEnum.NORMAL.value,
                    not_deleted(SysRole.del_flag)
                ),
                isouter=True
            )
            .join(SysRoleMenu, SysRole.role_id == SysRoleMenu.role_id, isouter=True)
            .join(
                SysMenu,
                and_(
                    SysRoleMenu.menu_id == SysMenu.menu_id,
                    SysMenu.status == StatusEnum.NORMAL.value
                )
            )
            .where(
                SysUser.user_id == user_id,
                SysUser.status == StatusEnum.NORMAL.value,
                not_deleted(SysUser.del_flag)
            )
            .order_by(SysMenu.order_num)
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
    ) -> List[SysMenu]:
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
                conditions.append(SysMenu.status == status)
            if menu_name:
                conditions.append(SysMenu.menu_name.like(f'%{menu_name}%'))
            if visible:
                conditions.append(SysMenu.visible == visible)
            
            stmt = (
                select(SysMenu)
                .where(*conditions) if conditions else select(SysMenu)
            ).order_by(SysMenu.order_num).distinct()
        else:
            menu_conditions = [
                SysRoleMenu.menu_id == SysMenu.menu_id
            ]
            if status:
                menu_conditions.append(SysMenu.status == status)
            if menu_name:
                menu_conditions.append(SysMenu.menu_name.like(f'%{menu_name}%'))
            if visible:
                menu_conditions.append(SysMenu.visible == visible)
            
            stmt = (
                select(SysMenu)
                .select_from(SysUser)
                .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
                .join(
                    SysRole,
                    and_(
                        SysUserRole.role_id == SysRole.role_id,
                        SysRole.status == StatusEnum.NORMAL.value,
                        not_deleted(SysRole.del_flag)
                    ),
                    isouter=True
                )
                .join(SysRoleMenu, SysRole.role_id == SysRoleMenu.role_id, isouter=True)
                .join(SysMenu, and_(*menu_conditions))
                .where(
                    SysUser.user_id == user_id,
                    SysUser.status == StatusEnum.NORMAL.value,
                    not_deleted(SysUser.del_flag)
                )
                .order_by(SysMenu.order_num)
                .distinct()
            )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_by_id(self, menu_id: int) -> int:
        """根据ID删除菜单"""
        stmt = delete(SysMenu).where(SysMenu.menu_id == menu_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def count_children(self, menu_id: int) -> int:
        """统计子菜单数量"""
        stmt = (
            select(func.count())
            .select_from(SysMenu)
            .where(SysMenu.parent_id == menu_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_roles(self, menu_id: int) -> int:
        """统计关联角色数量"""
        stmt = (
            select(func.count())
            .select_from(SysRoleMenu)
            .where(SysRoleMenu.menu_id == menu_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

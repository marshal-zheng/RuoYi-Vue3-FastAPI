"""
角色 Repository
提供角色相关的数据访问操作
"""
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete, update, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.role_do import RoleDO, RoleMenuDO, RoleDeptDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from utils.page_util import PageUtil
from utils.db_filters import not_deleted


class RoleRepository(BaseRepository[RoleDO]):
    """
    角色 Repository
    
    继承 BaseRepository 并扩展角色特有的查询方法
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, RoleDO)
    
    async def find_by_name(self, role_name: str) -> Optional[RoleDO]:
        """
        根据角色名查找角色
        
        Args:
            role_name: 角色名
        
        Returns:
            角色对象或 None
        """
        stmt = (
            select(RoleDO)
            .where(
                RoleDO.status == StatusEnum.NORMAL.value,
                not_deleted(RoleDO.del_flag),
                RoleDO.role_name == role_name
            )
            .order_by(desc(RoleDO.create_time))
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_key(self, role_key: str) -> Optional[RoleDO]:
        """根据角色标识查找角色"""
        stmt = (
            select(RoleDO)
            .where(
                not_deleted(RoleDO.del_flag),
                RoleDO.role_key == role_key
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def find_by_id(self, role_id: int) -> Optional[RoleDO]:
        """根据角色ID查找角色（兼容旧接口）"""
        return await self.get_by_id(role_id)
    
    async def find_active_by_id(self, role_id: int) -> Optional[RoleDO]:
        """根据ID查找有效角色"""
        stmt = (
            select(RoleDO)
            .where(
                RoleDO.role_id == role_id,
                RoleDO.status == StatusEnum.NORMAL.value,
                not_deleted(RoleDO.del_flag)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_all_active(self, exclude_admin: bool = True) -> List[RoleDO]:
        """
        获取所有有效角色
        
        Args:
            exclude_admin: 是否排除超级管理员角色
        
        Returns:
            角色列表
        """
        conditions = [
            RoleDO.status == StatusEnum.NORMAL.value,
            not_deleted(RoleDO.del_flag)
        ]
        if exclude_admin:
            conditions.append(RoleDO.role_id != 1)
        
        stmt = select(RoleDO).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def paginate_with_filters(
        self,
        page: int,
        page_size: int,
        role_id: Optional[int] = None,
        role_name: Optional[str] = None,
        role_key: Optional[str] = None,
        status: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        data_scope_sql: str = "True"
    ):
        """
        分页查询角色
        
        Args:
            page: 页码
            page_size: 每页数量
            其他参数: 过滤条件
        
        Returns:
            分页结果
        """
        conditions = [not_deleted(RoleDO.del_flag)]
        
        if role_id is not None:
            conditions.append(RoleDO.role_id == role_id)
        if role_name:
            conditions.append(RoleDO.role_name.like(f'%{role_name}%'))
        if role_key:
            conditions.append(RoleDO.role_key.like(f'%{role_key}%'))
        if status:
            conditions.append(RoleDO.status == status)
        if begin_time and end_time:
            conditions.append(
                RoleDO.create_time.between(
                    datetime.combine(datetime.strptime(begin_time, '%Y-%m-%d'), time(0, 0, 0)),
                    datetime.combine(datetime.strptime(end_time, '%Y-%m-%d'), time(23, 59, 59))
                )
            )
        
        # 数据权限 - 安全实现（不使用 eval）
        if data_scope_sql != "True" and data_scope_sql is not True:
            conditions.append(data_scope_sql)
        
        query = (
            select(RoleDO)
            .join(UserRoleDO, UserRoleDO.role_id == RoleDO.role_id, isouter=True)
            .join(UserDO, UserDO.user_id == UserRoleDO.user_id, isouter=True)
            .join(DeptDO, DeptDO.dept_id == UserDO.dept_id, isouter=True)
            .where(*conditions)
            .order_by(RoleDO.role_sort)
            .distinct()
        )
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def soft_delete(self, role_id: int, update_by: str) -> bool:
        """
        软删除角色
        
        Args:
            role_id: 角色ID
            update_by: 更新者
        
        Returns:
            是否成功
        """
        stmt = (
            update(RoleDO)
            .where(RoleDO.role_id == role_id)
            .values(
                del_flag=DelFlagEnum.DELETED.value,
                update_by=update_by,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
    
    async def count_users(self, role_id: int) -> int:
        """统计角色关联的用户数量"""
        stmt = (
            select(func.count())
            .select_from(UserRoleDO)
            .where(UserRoleDO.role_id == role_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def get_role_with_menus(self, role_id: int) -> Dict[str, Any]:
        """
        P1-018: 优化的角色权限查询
        
        使用单次查询获取角色及其菜单权限
        
        Args:
            role_id: 角色ID
        
        Returns:
            角色信息及其菜单列表
        """
        # 获取角色基本信息
        role_stmt = (
            select(RoleDO)
            .where(
                RoleDO.role_id == role_id,
                not_deleted(RoleDO.del_flag)
            )
        )
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalars().first()
        
        if not role:
            return {'role': None, 'menus': [], 'menu_ids': []}
        
        # 获取角色关联的菜单
        menu_stmt = (
            select(MenuDO)
            .join(RoleMenuDO, RoleMenuDO.menu_id == MenuDO.menu_id)
            .where(
                RoleMenuDO.role_id == role_id,
                MenuDO.status == StatusEnum.NORMAL.value
            )
            .order_by(MenuDO.parent_id, MenuDO.order_num)
        )
        menu_result = await self.db.execute(menu_stmt)
        menus = menu_result.scalars().all()
        
        return {
            'role': role,
            'menus': menus,
            'menu_ids': [m.menu_id for m in menus]
        }
    
    async def get_roles_menus_batch(self, role_ids: List[int]) -> Dict[int, List[MenuDO]]:
        """
        P1-018: 批量获取角色菜单（避免 N+1 查询）
        
        Args:
            role_ids: 角色ID列表
        
        Returns:
            角色ID到菜单列表的映射
        """
        if not role_ids:
            return {}
        
        stmt = (
            select(RoleMenuDO.role_id, MenuDO)
            .join(MenuDO, RoleMenuDO.menu_id == MenuDO.menu_id)
            .where(
                RoleMenuDO.role_id.in_(role_ids),
                MenuDO.status == StatusEnum.NORMAL.value
            )
            .order_by(MenuDO.parent_id, MenuDO.order_num)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # 组织成 {role_id: [menus]} 的映射
        role_menus: Dict[int, List[MenuDO]] = {rid: [] for rid in role_ids}
        for role_id, menu in rows:
            role_menus[role_id].append(menu)
        
        return role_menus
    
    async def get_user_permissions_optimized(self, user_id: int) -> List[str]:
        """
        P1-018: 优化的用户权限查询
        
        使用单次联合查询获取用户所有权限标识
        
        Args:
            user_id: 用户ID
        
        Returns:
            权限标识列表
        """
        stmt = (
            select(MenuDO.perms)
            .select_from(UserRoleDO)
            .join(RoleMenuDO, UserRoleDO.role_id == RoleMenuDO.role_id)
            .join(MenuDO, RoleMenuDO.menu_id == MenuDO.menu_id)
            .join(RoleDO, and_(
                UserRoleDO.role_id == RoleDO.role_id,
                RoleDO.status == StatusEnum.NORMAL.value,
                not_deleted(RoleDO.del_flag)
            ))
            .where(
                UserRoleDO.user_id == user_id,
                MenuDO.status == StatusEnum.NORMAL.value,
                MenuDO.perms.isnot(None),
                MenuDO.perms != ''
            )
            .distinct()
        )
        result = await self.db.execute(stmt)
        perms = result.scalars().all()
        
        # 展开多个权限（某些菜单的 perms 可能包含逗号分隔的多个权限）
        all_perms = []
        for perm in perms:
            if perm:
                all_perms.extend([p.strip() for p in perm.split(',') if p.strip()])
        
        return list(set(all_perms))


class RoleMenuRepository(BaseRepository[RoleMenuDO]):
    """角色菜单关联 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, RoleMenuDO)
    
    async def find_by_role_id(self, role_id: int) -> List[RoleMenuDO]:
        """根据角色ID查找关联"""
        stmt = select(RoleMenuDO).where(RoleMenuDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_menus_by_role(
        self,
        role_id: int,
        check_strictly: bool = False
    ) -> List[MenuDO]:
        """
        获取角色关联的菜单
        
        Args:
            role_id: 角色ID
            check_strictly: 是否严格检查（排除父菜单）
        
        Returns:
            菜单列表
        """
        conditions = [RoleMenuDO.role_id == role_id]
        
        if check_strictly:
            # 排除作为父菜单的菜单
            conditions.append(
                ~MenuDO.menu_id.in_(
                    select(MenuDO.parent_id)
                    .select_from(MenuDO)
                    .join(
                        RoleMenuDO,
                        and_(
                            RoleMenuDO.menu_id == MenuDO.menu_id,
                            RoleMenuDO.role_id == role_id
                        )
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
        """根据角色ID删除关联"""
        stmt = delete(RoleMenuDO).where(RoleMenuDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def batch_add(self, role_id: int, menu_ids: List[int]):
        """批量添加角色菜单关联"""
        for menu_id in menu_ids:
            self.db.add(RoleMenuDO(role_id=role_id, menu_id=menu_id))
        await self.db.flush()


class RoleDeptRepository(BaseRepository[RoleDeptDO]):
    """角色部门关联 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, RoleDeptDO)
    
    async def find_by_role_id(self, role_id: int) -> List[RoleDeptDO]:
        """根据角色ID查找关联"""
        stmt = select(RoleDeptDO).where(RoleDeptDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_depts_by_role(
        self,
        role_id: int,
        check_strictly: bool = False
    ) -> List[DeptDO]:
        """
        获取角色关联的部门
        
        Args:
            role_id: 角色ID
            check_strictly: 是否严格检查（排除父部门）
        
        Returns:
            部门列表
        """
        conditions = [RoleDeptDO.role_id == role_id]
        
        if check_strictly:
            conditions.append(
                ~DeptDO.dept_id.in_(
                    select(DeptDO.parent_id)
                    .select_from(DeptDO)
                    .join(
                        RoleDeptDO,
                        and_(
                            RoleDeptDO.dept_id == DeptDO.dept_id,
                            RoleDeptDO.role_id == role_id
                        )
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
        """根据角色ID删除关联"""
        stmt = delete(RoleDeptDO).where(RoleDeptDO.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def batch_add(self, role_id: int, dept_ids: List[int]):
        """批量添加角色部门关联"""
        for dept_id in dept_ids:
            self.db.add(RoleDeptDO(role_id=role_id, dept_id=dept_id))
        await self.db.flush()

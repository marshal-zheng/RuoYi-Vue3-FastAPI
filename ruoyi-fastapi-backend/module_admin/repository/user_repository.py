"""
用户 Repository
提供用户相关的数据访问操作
"""
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete, update, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from module_admin.entity.do.user_do import SysUser, SysUserRole, SysUserPost
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.role_do import SysRole, SysRoleMenu
from module_admin.entity.do.post_do import SysPost
from module_admin.entity.do.menu_do import SysMenu
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from module_admin.repository.specification import Specification, equals, like
from utils.page_util import PageUtil
from utils.sensitive import sensitive_equals
from utils.db_filters import not_deleted


class UserRepository(BaseRepository[SysUser]):
    """
    用户 Repository
    
    继承 BaseRepository 并扩展用户特有的查询方法
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysUser)
    
    async def find_by_username(self, username: str) -> Optional[SysUser]:
        """
        根据用户名查找用户
        
        Args:
            username: 用户名
        
        Returns:
            用户对象或 None
        """
        stmt = (
            select(SysUser)
            .where(
                SysUser.status == StatusEnum.NORMAL.value,
                not_deleted(SysUser.del_flag),
                SysUser.user_name == username
            )
            .order_by(desc(SysUser.create_time))
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_phone(self, phone: str) -> Optional[SysUser]:
        """根据手机号查找用户"""
        if not phone:
            return None
        phone_condition = sensitive_equals(SysUser, 'phonenumber', phone)
        stmt = (
            select(SysUser)
            .where(
                not_deleted(SysUser.del_flag),
                phone_condition
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_email(self, email: str) -> Optional[SysUser]:
        """根据邮箱查找用户"""
        if not email:
            return None
        email_condition = sensitive_equals(SysUser, 'email', email)
        stmt = (
            select(SysUser)
            .where(
                not_deleted(SysUser.del_flag),
                email_condition
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def find_by_id_card(self, id_card: str) -> Optional[SysUser]:
        """根据身份证号查找用户"""
        if not id_card:
            return None
        id_condition = sensitive_equals(SysUser, 'id_card', id_card)
        stmt = (
            select(SysUser)
            .where(
                not_deleted(SysUser.del_flag),
                id_condition
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_with_relations(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户及其关联信息（部门、角色、岗位、菜单）
        
        P1-016: 优化 N+1 查询，使用批量查询减少数据库访问次数
        
        Args:
            user_id: 用户ID
        
        Returns:
            包含用户基本信息和关联信息的字典
        """
        # 使用单次联合查询获取用户、部门信息
        user_dept_stmt = (
            select(SysUser, SysDept)
            .outerjoin(SysDept, and_(
                SysUser.dept_id == SysDept.dept_id,
                SysDept.status == StatusEnum.NORMAL.value,
                not_deleted(SysDept.del_flag)
            ))
            .where(
                SysUser.user_id == user_id,
                SysUser.status == StatusEnum.NORMAL.value,
                not_deleted(SysUser.del_flag)
            )
        )
        user_dept_result = await self.db.execute(user_dept_stmt)
        user_dept_row = user_dept_result.first()
        
        user_info = user_dept_row[0] if user_dept_row else None
        dept_info = user_dept_row[1] if user_dept_row else None
        
        if not user_info:
            return {
                'user_basic_info': None,
                'user_dept_info': None,
                'user_role_info': [],
                'user_post_info': [],
                'user_menu_info': [],
            }
        
        # 使用单次查询获取角色信息
        role_stmt = (
            select(SysRole)
            .join(SysUserRole, SysUserRole.role_id == SysRole.role_id)
            .where(
                SysUserRole.user_id == user_id,
                SysRole.status == StatusEnum.NORMAL.value,
                not_deleted(SysRole.del_flag)
            )
            .distinct()
        )
        role_result = await self.db.execute(role_stmt)
        role_info = role_result.scalars().all()
        
        # 使用单次查询获取岗位信息
        post_stmt = (
            select(SysPost)
            .join(SysUserPost, SysUserPost.post_id == SysPost.post_id)
            .where(
                SysUserPost.user_id == user_id,
                SysPost.status == StatusEnum.NORMAL.value
            )
            .distinct()
        )
        post_result = await self.db.execute(post_stmt)
        post_info = post_result.scalars().all()
        
        # 获取菜单信息
        role_ids = [r.role_id for r in role_info]
        menu_info = await self._get_user_menus(user_id, role_ids)
        
        return {
            'user_basic_info': user_info,
            'user_dept_info': dept_info,
            'user_role_info': role_info,
            'user_post_info': post_info,
            'user_menu_info': menu_info,
        }
    
    async def _get_active_user(self, user_id: int) -> Optional[SysUser]:
        """获取有效的用户"""
        stmt = (
            select(SysUser)
            .where(
                SysUser.user_id == user_id,
                SysUser.status == StatusEnum.NORMAL.value,
                not_deleted(SysUser.del_flag)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def _get_user_dept(self, user_id: int) -> Optional[SysDept]:
        """获取用户所属部门"""
        stmt = (
            select(SysDept)
            .select_from(SysUser)
            .join(
                SysDept,
                and_(
                    SysUser.dept_id == SysDept.dept_id,
                    SysDept.status == StatusEnum.NORMAL.value,
                    not_deleted(SysDept.del_flag)
                )
            )
            .where(
                SysUser.user_id == user_id,
                SysUser.status == StatusEnum.NORMAL.value,
                not_deleted(SysUser.del_flag)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def _get_user_roles(self, user_id: int) -> List[SysRole]:
        """获取用户角色列表"""
        stmt = (
            select(SysRole)
            .select_from(SysUser)
            .join(SysUserRole, SysUser.user_id == SysUserRole.user_id, isouter=True)
            .join(
                SysRole,
                and_(
                    SysUserRole.role_id == SysRole.role_id,
                    SysRole.status == StatusEnum.NORMAL.value,
                    not_deleted(SysRole.del_flag)
                )
            )
            .where(
                SysUser.user_id == user_id,
                SysUser.status == StatusEnum.NORMAL.value,
                not_deleted(SysUser.del_flag)
            )
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def _get_user_posts(self, user_id: int) -> List[SysPost]:
        """获取用户岗位列表"""
        stmt = (
            select(SysPost)
            .select_from(SysUser)
            .join(SysUserPost, SysUser.user_id == SysUserPost.user_id, isouter=True)
            .join(
                SysPost,
                and_(
                    SysUserPost.post_id == SysPost.post_id,
                    SysPost.status == StatusEnum.NORMAL.value
                )
            )
            .where(
                SysUser.user_id == user_id,
                SysUser.status == StatusEnum.NORMAL.value,
                not_deleted(SysUser.del_flag)
            )
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def _get_user_menus(self, user_id: int, role_ids: List[int]) -> List[SysMenu]:
        """获取用户菜单列表"""
        # 超级管理员获取所有菜单
        if 1 in role_ids:
            stmt = (
                select(SysMenu)
                .where(SysMenu.status == StatusEnum.NORMAL.value)
                .distinct()
            )
        else:
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
    
    async def paginate_with_dept(
        self,
        page: int,
        page_size: int,
        user_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        user_name: Optional[str] = None,
        nick_name: Optional[str] = None,
        email: Optional[str] = None,
        phonenumber: Optional[str] = None,
        status: Optional[str] = None,
        sex: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        data_scope_sql: str = "True"
    ):
        """
        分页查询用户（带部门信息）
        
        Args:
            page: 页码
            page_size: 每页数量
            其他参数: 过滤条件
        
        Returns:
            分页结果
        """
        conditions = [not_deleted(SysUser.del_flag)]
        
        if user_id:
            conditions.append(SysUser.user_id == user_id)
        
        if dept_id:
            conditions.append(
                or_(
                    SysUser.dept_id == dept_id,
                    SysUser.dept_id.in_(
                        select(SysDept.dept_id).where(func.find_in_set(dept_id, SysDept.ancestors))
                    )
                )
            )
        
        if user_name:
            conditions.append(SysUser.user_name.like(f'%{user_name}%'))
        if nick_name:
            conditions.append(SysUser.nick_name.like(f'%{nick_name}%'))
        if email:
            email_condition = sensitive_equals(SysUser, 'email', email)
            if email_condition is not None:
                conditions.append(email_condition)
        if phonenumber:
            phone_condition = sensitive_equals(SysUser, 'phonenumber', phonenumber)
            if phone_condition is not None:
                conditions.append(phone_condition)
        if status:
            conditions.append(SysUser.status == status)
        if sex:
            conditions.append(SysUser.sex == sex)
        if begin_time and end_time:
            conditions.append(
                SysUser.create_time.between(
                    datetime.combine(datetime.strptime(begin_time, '%Y-%m-%d'), time(0, 0, 0)),
                    datetime.combine(datetime.strptime(end_time, '%Y-%m-%d'), time(23, 59, 59))
                )
            )
        
        # 数据权限 - 安全实现（不使用 eval）
        # data_scope_sql 应该是一个 SQLAlchemy 条件对象，而不是字符串
        # 如果传入的是字符串 "True"，则不添加额外条件
        if data_scope_sql != "True" and data_scope_sql is not True:
            # 如果是 SQLAlchemy 条件对象，直接添加
            conditions.append(data_scope_sql)
        
        query = (
            select(SysUser, SysDept)
            .join(
                SysDept,
                and_(
                    SysUser.dept_id == SysDept.dept_id,
                    SysDept.status == StatusEnum.NORMAL.value,
                    not_deleted(SysDept.del_flag)
                ),
                isouter=True
            )
            .where(*conditions)
            .order_by(SysUser.user_id)
            .distinct()
        )
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def soft_delete(self, user_id: int, update_by: str) -> bool:
        """
        软删除用户
        
        Args:
            user_id: 用户ID
            update_by: 更新者
        
        Returns:
            是否成功
        """
        stmt = (
            update(SysUser)
            .where(SysUser.user_id == user_id)
            .values(
                del_flag=DelFlagEnum.DELETED.value,
                update_by=update_by,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
    
    async def paginate_allocated_by_role(
        self,
        role_id: int,
        page: int,
        page_size: int,
        user_name: Optional[str] = None,
        phonenumber: Optional[str] = None,
        data_scope_sql: str = "True"
    ):
        """
        分页查询已分配该角色的用户
        
        Args:
            role_id: 角色ID
            page: 页码
            page_size: 每页数量
            user_name: 用户名（模糊匹配）
            phonenumber: 手机号（精确匹配）
            data_scope_sql: 数据权限SQL
        
        Returns:
            分页结果
        """
        conditions = [
            not_deleted(SysUser.del_flag),
            SysUserRole.role_id == role_id
        ]
        
        if user_name:
            conditions.append(SysUser.user_name.like(f'%{user_name}%'))
        if phonenumber:
            phone_condition = sensitive_equals(SysUser, 'phonenumber', phonenumber)
            if phone_condition is not None:
                conditions.append(phone_condition)
        
        # 数据权限 - 安全实现（不使用 eval）
        if data_scope_sql != "True" and data_scope_sql is not True:
            conditions.append(data_scope_sql)
        
        query = (
            select(SysUser, SysDept)
            .join(SysUserRole, SysUser.user_id == SysUserRole.user_id)
            .join(
                SysDept,
                and_(
                    SysUser.dept_id == SysDept.dept_id,
                    SysDept.status == StatusEnum.NORMAL.value,
                    not_deleted(SysDept.del_flag)
                ),
                isouter=True
            )
            .where(*conditions)
            .order_by(SysUser.user_id)
            .distinct()
        )
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)
    
    async def paginate_unallocated_by_role(
        self,
        role_id: int,
        page: int,
        page_size: int,
        user_name: Optional[str] = None,
        phonenumber: Optional[str] = None,
        data_scope_sql: str = "True"
    ):
        """
        分页查询未分配该角色的用户
        
        Args:
            role_id: 角色ID
            page: 页码
            page_size: 每页数量
            user_name: 用户名（模糊匹配）
            phonenumber: 手机号（精确匹配）
            data_scope_sql: 数据权限SQL
        
        Returns:
            分页结果
        """
        # 已分配该角色的用户ID子查询
        allocated_user_ids = (
            select(SysUserRole.user_id)
            .where(SysUserRole.role_id == role_id)
        )
        
        conditions = [
            not_deleted(SysUser.del_flag),
            SysUser.user_id.notin_(allocated_user_ids)
        ]
        
        if user_name:
            conditions.append(SysUser.user_name.like(f'%{user_name}%'))
        if phonenumber:
            phone_condition = sensitive_equals(SysUser, 'phonenumber', phonenumber)
            if phone_condition is not None:
                conditions.append(phone_condition)
        
        # 数据权限 - 安全实现（不使用 eval）
        if data_scope_sql != "True" and data_scope_sql is not True:
            conditions.append(data_scope_sql)
        
        query = (
            select(SysUser, SysDept)
            .join(
                SysDept,
                and_(
                    SysUser.dept_id == SysDept.dept_id,
                    SysDept.status == StatusEnum.NORMAL.value,
                    not_deleted(SysDept.del_flag)
                ),
                isouter=True
            )
            .where(*conditions)
            .order_by(SysUser.user_id)
            .distinct()
        )
        
        return await PageUtil.paginate(self.db, query, page, page_size, True)


    async def get_users_roles_batch(self, user_ids: List[int]) -> Dict[int, List[SysRole]]:
        """
        P1-016: 批量获取用户角色（避免 N+1 查询）
        
        Args:
            user_ids: 用户ID列表
        
        Returns:
            用户ID到角色列表的映射
        """
        if not user_ids:
            return {}
        
        stmt = (
            select(SysUserRole.user_id, SysRole)
            .join(SysRole, SysUserRole.role_id == SysRole.role_id)
            .where(
                SysUserRole.user_id.in_(user_ids),
                SysRole.status == StatusEnum.NORMAL.value,
                not_deleted(SysRole.del_flag)
            )
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # 组织成 {user_id: [roles]} 的映射
        user_roles: Dict[int, List[SysRole]] = {uid: [] for uid in user_ids}
        for user_id, role in rows:
            user_roles[user_id].append(role)
        
        return user_roles
    
    async def get_users_posts_batch(self, user_ids: List[int]) -> Dict[int, List[SysPost]]:
        """
        P1-016: 批量获取用户岗位（避免 N+1 查询）
        
        Args:
            user_ids: 用户ID列表
        
        Returns:
            用户ID到岗位列表的映射
        """
        if not user_ids:
            return {}
        
        stmt = (
            select(SysUserPost.user_id, SysPost)
            .join(SysPost, SysUserPost.post_id == SysPost.post_id)
            .where(
                SysUserPost.user_id.in_(user_ids),
                SysPost.status == StatusEnum.NORMAL.value
            )
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # 组织成 {user_id: [posts]} 的映射
        user_posts: Dict[int, List[SysPost]] = {uid: [] for uid in user_ids}
        for user_id, post in rows:
            user_posts[user_id].append(post)
        
        return user_posts


class UserRoleRepository(BaseRepository[SysUserRole]):
    """用户角色关联 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysUserRole)
    
    async def find_by_user_id(self, user_id: int) -> List[SysUserRole]:
        """根据用户ID查找关联"""
        stmt = select(SysUserRole).where(SysUserRole.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_by_user_id(self, user_id: int) -> int:
        """根据用户ID删除关联"""
        stmt = delete(SysUserRole).where(SysUserRole.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def delete_by_user_and_role(self, user_id: int, role_id: int) -> int:
        """根据用户ID和角色ID删除关联"""
        conditions = []
        if user_id:
            conditions.append(SysUserRole.user_id == user_id)
        if role_id:
            conditions.append(SysUserRole.role_id == role_id)
        
        stmt = delete(SysUserRole).where(*conditions)
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def find_by_user_and_role(self, user_id: int, role_id: int) -> Optional[SysUserRole]:
        """根据用户ID和角色ID查找关联"""
        stmt = (
            select(SysUserRole)
            .where(
                SysUserRole.user_id == user_id,
                SysUserRole.role_id == role_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()


class UserPostRepository(BaseRepository[SysUserPost]):
    """用户岗位关联 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysUserPost)
    
    async def find_by_user_id(self, user_id: int) -> List[SysUserPost]:
        """根据用户ID查找关联"""
        stmt = select(SysUserPost).where(SysUserPost.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_by_user_id(self, user_id: int) -> int:
        """根据用户ID删除关联"""
        stmt = delete(SysUserPost).where(SysUserPost.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.rowcount

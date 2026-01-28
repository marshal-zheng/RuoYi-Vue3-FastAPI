"""
部门 Repository
提供部门相关的数据访问操作
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, func, bindparam, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import immutabledict

from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum
from module_admin.repository.base_repository import BaseRepository
from utils.db_filters import not_deleted


class DeptRepository(BaseRepository[SysDept]):
    """
    部门 Repository
    
    继承 BaseRepository 并扩展部门特有的查询方法
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SysDept)
    
    async def find_by_id(self, dept_id: int) -> Optional[SysDept]:
        """根据ID查找部门"""
        stmt = select(SysDept).where(SysDept.dept_id == dept_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_active_by_id(self, dept_id: int) -> Optional[SysDept]:
        """根据ID查找有效部门"""
        stmt = (
            select(SysDept)
            .where(
                SysDept.dept_id == dept_id,
                not_deleted(SysDept.del_flag)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_parent_and_name(
        self,
        parent_id: Optional[int],
        dept_name: Optional[str]
    ) -> Optional[SysDept]:
        """根据父部门ID和部门名称查找部门"""
        conditions = []
        if parent_id is not None:
            conditions.append(SysDept.parent_id == parent_id)
        if dept_name:
            conditions.append(SysDept.dept_name == dept_name)
        
        stmt = select(SysDept).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_children(self, dept_id: int) -> List[SysDept]:
        """查找所有子部门"""
        stmt = (
            select(SysDept)
            .where(func.find_in_set(dept_id, SysDept.ancestors))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_direct_children(self, dept_id: int) -> List[SysDept]:
        """查找直接子部门"""
        stmt = (
            select(SysDept)
            .where(
                SysDept.parent_id == dept_id,
                not_deleted(SysDept.del_flag)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_all_for_tree(
        self,
        dept_name: Optional[str] = None,
        data_scope_sql: str = "True"
    ) -> List[SysDept]:
        """
        获取部门树列表
        
        Args:
            dept_name: 部门名称过滤
            data_scope_sql: 数据权限SQL
        
        Returns:
            部门列表
        """
        conditions = [
            SysDept.status == StatusEnum.NORMAL.value,
            not_deleted(SysDept.del_flag),
        ]
        
        # 数据权限 - 安全实现（不使用 eval）
        if data_scope_sql != "True" and data_scope_sql is not True:
            conditions.append(data_scope_sql)
        
        if dept_name:
            conditions.append(SysDept.dept_name.like(f'%{dept_name}%'))
        
        stmt = (
            select(SysDept)
            .where(*conditions)
            .order_by(SysDept.order_num)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_for_edit_option(
        self,
        exclude_dept_id: int,
        data_scope_sql: str = "True"
    ) -> List[SysDept]:
        """
        获取编辑时可选的部门列表（排除自身及子部门）
        
        Args:
            exclude_dept_id: 要排除的部门ID
            data_scope_sql: 数据权限SQL
        
        Returns:
            部门列表
        """
        stmt = select(SysDept).where(
            SysDept.dept_id != exclude_dept_id,
            ~SysDept.dept_id.in_(
                select(SysDept.dept_id).where(
                    func.find_in_set(exclude_dept_id, SysDept.ancestors)
                )
            ),
            not_deleted(SysDept.del_flag),
            SysDept.status == StatusEnum.NORMAL.value,
        )
        # 数据权限 - 安全实现（不使用 eval）
        if data_scope_sql != "True" and data_scope_sql is not True:
            stmt = stmt.where(data_scope_sql)
        
        stmt = stmt.order_by(SysDept.order_num).distinct()
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def find_with_filters(
        self,
        dept_id: Optional[int] = None,
        status: Optional[str] = None,
        dept_name: Optional[str] = None,
        data_scope_sql: str = "True"
    ) -> List[SysDept]:
        """
        查询部门列表（带过滤条件）
        
        Args:
            dept_id: 部门ID
            status: 状态
            dept_name: 部门名称
            data_scope_sql: 数据权限SQL
        
        Returns:
            部门列表
        """
        conditions = [
            not_deleted(SysDept.del_flag),
        ]
        
        # 数据权限 - 安全实现（不使用 eval）
        if data_scope_sql != "True" and data_scope_sql is not True:
            conditions.append(data_scope_sql)
        
        if dept_id is not None:
            conditions.append(SysDept.dept_id == dept_id)
        if status:
            conditions.append(SysDept.status == status)
        if dept_name:
            conditions.append(SysDept.dept_name.like(f'%{dept_name}%'))
        
        stmt = (
            select(SysDept)
            .where(*conditions)
            .order_by(SysDept.order_num)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_children_ancestors(self, updates: List[dict]):
        """
        批量更新子部门的祖先路径
        
        Args:
            updates: 更新数据列表，格式为 [{'dept_id': 1, 'ancestors': '0,1'}]
        """
        if not updates:
            return
        
        stmt = (
            update(SysDept)
            .where(SysDept.dept_id == bindparam('dept_id'))
            .values(ancestors=bindparam('ancestors'))
        )
        await self.db.execute(
            stmt,
            updates,
            execution_options=immutabledict({'synchronize_session': None})
        )
    
    async def update_status_normal(self, dept_ids: List[int]):
        """批量更新部门状态为正常"""
        if not dept_ids:
            return
        
        stmt = (
            update(SysDept)
            .where(SysDept.dept_id.in_(dept_ids))
            .values(status=StatusEnum.NORMAL.value)
        )
        await self.db.execute(stmt)
    
    async def soft_delete(self, dept_id: int, update_by: str) -> bool:
        """
        软删除部门
        
        Args:
            dept_id: 部门ID
            update_by: 更新者
        
        Returns:
            是否成功
        """
        stmt = (
            update(SysDept)
            .where(SysDept.dept_id == dept_id)
            .values(
                del_flag=DelFlagEnum.DELETED.value,
                update_by=update_by,
                update_time=datetime.now()
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
    
    async def count_normal_children(self, dept_id: int) -> int:
        """统计正常状态的子部门数量"""
        stmt = (
            select(func.count())
            .select_from(SysDept)
            .where(
                SysDept.status == StatusEnum.NORMAL.value,
                not_deleted(SysDept.del_flag),
                func.find_in_set(dept_id, SysDept.ancestors)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_direct_children(self, dept_id: int) -> int:
        """统计直接子部门数量"""
        stmt = (
            select(func.count())
            .select_from(SysDept)
            .where(
                not_deleted(SysDept.del_flag),
                SysDept.parent_id == dept_id
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def count_users(self, dept_id: int) -> int:
        """统计部门下的用户数量"""
        stmt = (
            select(func.count())
            .select_from(SysUser)
            .where(
                SysUser.dept_id == dept_id,
                not_deleted(SysUser.del_flag)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def build_dept_tree_optimized(
        self,
        dept_name: Optional[str] = None,
        status: Optional[str] = None,
        data_scope_sql: str = "True"
    ) -> List[dict]:
        """
        P1-017: 优化的部门树查询
        
        使用单次查询获取所有部门，然后在内存中构建树结构
        避免递归查询或多次使用 FIND_IN_SET
        
        Args:
            dept_name: 部门名称过滤
            status: 状态过滤
            data_scope_sql: 数据权限SQL
        
        Returns:
            部门树结构
        """
        conditions = [
            not_deleted(SysDept.del_flag),
        ]
        
        if status:
            conditions.append(SysDept.status == status)
        
        if dept_name:
            conditions.append(SysDept.dept_name.like(f'%{dept_name}%'))
        
        # 数据权限
        if data_scope_sql != "True" and data_scope_sql is not True:
            conditions.append(data_scope_sql)
        
        # 单次查询获取所有部门
        stmt = (
            select(SysDept)
            .where(*conditions)
            .order_by(SysDept.parent_id, SysDept.order_num)
        )
        result = await self.db.execute(stmt)
        depts = result.scalars().all()
        
        # 在内存中构建树
        return self._build_tree_in_memory(depts)
    
    def _build_tree_in_memory(self, depts: List[SysDept]) -> List[dict]:
        """
        在内存中构建部门树
        
        Args:
            depts: 部门列表
        
        Returns:
            树形结构的部门列表
        """
        # 创建 ID 到部门的映射
        dept_map = {}
        for dept in depts:
            dept_dict = {
                'dept_id': dept.dept_id,
                'parent_id': dept.parent_id,
                'dept_name': dept.dept_name,
                'order_num': dept.order_num,
                'leader': dept.leader,
                'phone': dept.phone,
                'email': dept.email,
                'status': dept.status,
                'ancestors': dept.ancestors,
                'children': []
            }
            dept_map[dept.dept_id] = dept_dict
        
        # 构建树结构
        roots = []
        for dept_id, dept_dict in dept_map.items():
            parent_id = dept_dict['parent_id']
            if parent_id == 0 or parent_id not in dept_map:
                roots.append(dept_dict)
            else:
                dept_map[parent_id]['children'].append(dept_dict)
        
        return roots
    
    async def find_children_by_ancestors_prefix(self, dept_id: int) -> List[SysDept]:
        """
        P1-017: 使用 ancestors LIKE 查询子部门
        
        比 FIND_IN_SET 更高效，可以利用索引
        
        Args:
            dept_id: 部门ID
        
        Returns:
            子部门列表
        """
        # 先获取当前部门的 ancestors
        current_dept = await self.find_by_id(dept_id)
        if not current_dept:
            return []
        
        # 构建新的 ancestors 前缀
        if current_dept.ancestors:
            prefix = f"{current_dept.ancestors},{dept_id}"
        else:
            prefix = str(dept_id)
        
        # 使用 LIKE 查询（可以使用索引）
        stmt = (
            select(SysDept)
            .where(
                or_(
                    SysDept.ancestors.like(f'{prefix},%'),
                    SysDept.ancestors == prefix,
                    SysDept.ancestors.like(f'%,{dept_id},%'),
                    SysDept.ancestors.like(f'%,{dept_id}'),
                ),
                not_deleted(SysDept.del_flag)
            )
            .order_by(SysDept.order_num)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_dept_id_and_children(self, dept_id: int) -> List[int]:
        """
        P1-017: 获取部门ID及其所有子部门ID
        
        用于数据权限过滤
        
        Args:
            dept_id: 部门ID
        
        Returns:
            部门ID列表（包含自身和所有子部门）
        """
        children = await self.find_children_by_ancestors_prefix(dept_id)
        dept_ids = [dept_id]
        dept_ids.extend([child.dept_id for child in children])
        return dept_ids

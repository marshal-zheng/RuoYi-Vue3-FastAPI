"""
登录 Repository
"""
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.user_do import UserDO
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.enums import StatusEnum, DelFlagEnum
from utils.db_filters import not_deleted


class LoginRepository:
    """登录 Repository"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_user_with_dept(
        self,
        user_name: str
    ) -> Optional[Tuple[UserDO, Optional[DeptDO]]]:
        """
        根据用户名查询用户信息（包含部门）
        
        Args:
            user_name: 用户名
        
        Returns:
            (用户对象, 部门对象) 元组或 None
        """
        stmt = (
            select(UserDO, DeptDO)
            .where(
                UserDO.user_name == user_name,
                not_deleted(UserDO.del_flag)
            )
            .join(
                DeptDO,
                and_(
                    UserDO.dept_id == DeptDO.dept_id,
                    DeptDO.status == StatusEnum.NORMAL.value,
                    not_deleted(DeptDO.del_flag)
                ),
                isouter=True
            )
            .distinct()
        )
        result = await self.db.execute(stmt)
        return result.first()

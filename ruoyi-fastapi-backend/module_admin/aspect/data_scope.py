"""
数据权限获取器

返回 SQLAlchemy 条件表达式而非字符串，避免 SQL 注入和 eval() 安全风险
"""
from fastapi import Depends
from typing import Optional, Union, Any
from sqlalchemy import or_, and_, select, func, literal
from sqlalchemy.sql.elements import ColumnElement
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.role_do import SysRoleDept
from module_admin.entity.do.user_do import SysUser


# 特殊标记值，表示不需要数据权限过滤（管理员或全部数据权限）
DATA_SCOPE_ALL_MARKER = True


class GetDataScope:
    """
    获取当前用户数据权限对应的 SQLAlchemy 查询条件
    
    返回值类型:
    - True: 管理员或全部数据权限，不需要过滤
    - SQLAlchemy ColumnElement: 需要添加到 WHERE 条件的表达式
    """

    DATA_SCOPE_ALL = '1'
    DATA_SCOPE_CUSTOM = '2'
    DATA_SCOPE_DEPT = '3'
    DATA_SCOPE_DEPT_AND_CHILD = '4'
    DATA_SCOPE_SELF = '5'

    def __init__(
        self,
        query_alias: Optional[str] = '',
        db_alias: Optional[str] = 'db',
        user_alias: Optional[str] = 'user_id',
        dept_alias: Optional[str] = 'dept_id',
    ):
        """
        获取当前用户数据权限对应的查询条件

        :param query_alias: 所要查询表对应的 sqlalchemy 模型名称（SysUser/SysDept 等）
        :param db_alias: orm 对象别名，默认为 'db'（保留兼容性，未使用）
        :param user_alias: 用户 id 字段别名，默认为 'user_id'
        :param dept_alias: 部门 id 字段别名，默认为 'dept_id'
        """
        self.query_alias = query_alias
        self.db_alias = db_alias
        self.user_alias = user_alias
        self.dept_alias = dept_alias
        
        # 根据 query_alias 获取模型类
        self._model_map = {
            'SysUser': SysUser,
            'SysDept': SysDept,
        }

    def _get_model_class(self) -> Any:
        """获取对应的模型类"""
        return self._model_map.get(self.query_alias)

    def __call__(
        self, current_user: CurrentUserModel = Depends(LoginService.get_current_user)
    ) -> Union[bool, ColumnElement]:
        """
        根据当前用户信息构建数据权限查询条件
        
        Returns:
            - True: 管理员或全部数据权限，不需要过滤
            - SQLAlchemy ColumnElement: WHERE 条件表达式
        """
        user_id = current_user.user.user_id
        dept_id = current_user.user.dept_id
        
        # 获取模型类
        model_class = self._get_model_class()
        
        # 检查模型是否有对应字段
        has_dept_id = model_class and hasattr(model_class, self.dept_alias)
        has_user_id = model_class and hasattr(model_class, self.user_alias)
        
        # 收集自定义权限的角色ID
        custom_data_scope_role_ids = [
            item.role_id for item in current_user.user.role 
            if item.data_scope == self.DATA_SCOPE_CUSTOM
        ]
        
        conditions = []
        
        for role in current_user.user.role:
            # 管理员或全部数据权限 - 直接返回 True
            if current_user.user.admin or role.data_scope == self.DATA_SCOPE_ALL:
                return DATA_SCOPE_ALL_MARKER
            
            # 自定义数据权限
            elif role.data_scope == self.DATA_SCOPE_CUSTOM:
                if has_dept_id and custom_data_scope_role_ids:
                    dept_id_col = getattr(model_class, self.dept_alias)
                    # 查询角色关联的部门ID
                    subquery = select(SysRoleDept.dept_id).where(
                        SysRoleDept.role_id.in_(custom_data_scope_role_ids)
                    )
                    conditions.append(dept_id_col.in_(subquery))
            
            # 本部门数据权限
            elif role.data_scope == self.DATA_SCOPE_DEPT:
                if has_dept_id and dept_id:
                    dept_id_col = getattr(model_class, self.dept_alias)
                    conditions.append(dept_id_col == dept_id)
            
            # 本部门及以下数据权限
            elif role.data_scope == self.DATA_SCOPE_DEPT_AND_CHILD:
                if has_dept_id and dept_id:
                    dept_id_col = getattr(model_class, self.dept_alias)
                    # 查询本部门及所有子部门的ID
                    subquery = select(SysDept.dept_id).where(
                        or_(
                            SysDept.dept_id == dept_id,
                            func.find_in_set(dept_id, SysDept.ancestors)
                        )
                    )
                    conditions.append(dept_id_col.in_(subquery))
            
            # 仅本人数据权限
            elif role.data_scope == self.DATA_SCOPE_SELF:
                if has_user_id:
                    user_id_col = getattr(model_class, self.user_alias)
                    conditions.append(user_id_col == user_id)
        
        # 去重并合并条件
        # 使用 set 无法对 SQLAlchemy 表达式去重，这里保持原逻辑
        if not conditions:
            # 没有任何权限条件，返回 False（不返回任何数据）
            return literal(False)
        
        # 多个条件用 OR 连接
        if len(conditions) == 1:
            return conditions[0]
        return or_(*conditions)

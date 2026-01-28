"""
数据权限 SQL 构建器
安全地构建数据权限查询条件，替代 eval() 的不安全实现

Google 工程标准：
- 零容忍代码注入
- 类型安全的 SQL 构建
- 可测试、可审计的权限逻辑
"""
from typing import List, Optional, Any
from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser


class DataScopeType:
    """数据权限范围类型"""
    ALL = "1"  # 全部数据权限
    CUSTOM = "2"  # 自定义数据权限
    DEPT_ONLY = "3"  # 本部门数据权限
    DEPT_AND_BELOW = "4"  # 本部门及以下数据权限
    SELF_ONLY = "5"  # 仅本人数据权限


class DataScopeBuilder:
    """
    数据权限 SQL 条件构建器
    
    使用 SQLAlchemy 表达式 API 安全地构建查询条件
    完全避免字符串拼接和 eval() 的安全风险
    """
    
    @staticmethod
    def build_dept_scope(
        scope_type: str,
        user_id: int,
        dept_id: Optional[int] = None,
        dept_ids: Optional[List[int]] = None,
        model_class: Any = None
    ) -> BooleanClauseList:
        """
        构建部门数据权限条件
        
        Args:
            scope_type: 权限范围类型
            user_id: 当前用户ID
            dept_id: 当前用户部门ID
            dept_ids: 自定义部门ID列表（用于自定义权限）
            model_class: 查询的模型类（用于获取 dept_id 字段）
        
        Returns:
            SQLAlchemy 查询条件
        """
        if not model_class:
            model_class = SysDept
        
        # 获取模型的 dept_id 字段
        dept_id_column = getattr(model_class, 'dept_id', None)
        if not dept_id_column:
            # 如果模型没有 dept_id 字段，返回 True（不限制）
            return and_(True)
        
        # 全部数据权限
        if scope_type == DataScopeType.ALL:
            return and_(True)
        
        # 自定义数据权限
        if scope_type == DataScopeType.CUSTOM:
            if dept_ids:
                return dept_id_column.in_(dept_ids)
            return and_(False)  # 没有自定义部门时，不返回任何数据
        
        # 本部门数据权限
        if scope_type == DataScopeType.DEPT_ONLY:
            if dept_id:
                return dept_id_column == dept_id
            return and_(False)
        
        # 本部门及以下数据权限
        if scope_type == DataScopeType.DEPT_AND_BELOW:
            if dept_id:
                # 需要查询部门表获取所有子部门
                # 这里返回条件，实际查询在 Repository 层处理
                return or_(
                    dept_id_column == dept_id,
                    # 子部门条件需要通过 ancestors 字段判断
                    # 在实际使用时需要 join SysDept 表
                )
            return and_(False)
        
        # 仅本人数据权限
        if scope_type == DataScopeType.SELF_ONLY:
            # 需要检查模型是否有 create_by 或 user_id 字段
            if hasattr(model_class, 'create_by'):
                return model_class.create_by == str(user_id)
            if hasattr(model_class, 'user_id'):
                return model_class.user_id == user_id
            return and_(False)
        
        # 默认：不返回任何数据
        return and_(False)
    
    @staticmethod
    def build_user_scope(
        scope_type: str,
        user_id: int,
        dept_id: Optional[int] = None,
        dept_ids: Optional[List[int]] = None
    ) -> BooleanClauseList:
        """
        构建用户数据权限条件（用于用户列表查询）
        
        Args:
            scope_type: 权限范围类型
            user_id: 当前用户ID
            dept_id: 当前用户部门ID
            dept_ids: 自定义部门ID列表
        
        Returns:
            SQLAlchemy 查询条件
        """
        return DataScopeBuilder.build_dept_scope(
            scope_type=scope_type,
            user_id=user_id,
            dept_id=dept_id,
            dept_ids=dept_ids,
            model_class=SysUser
        )
    
    @staticmethod
    def build_role_scope(
        scope_type: str,
        user_id: int,
        dept_id: Optional[int] = None,
        dept_ids: Optional[List[int]] = None
    ) -> BooleanClauseList:
        """
        构建角色数据权限条件
        
        角色通常不直接关联部门，通过用户-角色关联间接关联
        """
        # 角色权限通常基于创建者
        if scope_type == DataScopeType.SELF_ONLY:
            from module_admin.entity.do.role_do import SysRole
            return SysRole.create_by == str(user_id)
        
        # 其他情况返回全部
        return and_(True)


class DataScopeContext:
    """
    数据权限上下文
    
    封装当前用户的权限信息，用于构建查询条件
    """
    
    def __init__(
        self,
        user_id: int,
        dept_id: Optional[int] = None,
        role_scopes: Optional[List[dict]] = None
    ):
        """
        初始化数据权限上下文
        
        Args:
            user_id: 当前用户ID
            dept_id: 当前用户部门ID
            role_scopes: 用户角色的数据权限列表
                格式: [{"scope_type": "1", "dept_ids": [1, 2, 3]}, ...]
        """
        self.user_id = user_id
        self.dept_id = dept_id
        self.role_scopes = role_scopes or []
    
    def build_condition(self, model_class: Any) -> BooleanClauseList:
        """
        根据用户的所有角色权限构建最终查询条件
        
        多个角色的权限使用 OR 连接（取并集）
        
        Args:
            model_class: 查询的模型类
        
        Returns:
            SQLAlchemy 查询条件
        """
        if not self.role_scopes:
            # 没有角色权限，仅返回本人数据
            return DataScopeBuilder.build_dept_scope(
                scope_type=DataScopeType.SELF_ONLY,
                user_id=self.user_id,
                model_class=model_class
            )
        
        conditions = []
        for role_scope in self.role_scopes:
            scope_type = role_scope.get("scope_type")
            dept_ids = role_scope.get("dept_ids")
            
            condition = DataScopeBuilder.build_dept_scope(
                scope_type=scope_type,
                user_id=self.user_id,
                dept_id=self.dept_id,
                dept_ids=dept_ids,
                model_class=model_class
            )
            conditions.append(condition)
        
        # 多个角色权限取并集
        return or_(*conditions) if len(conditions) > 1 else conditions[0]


# 使用示例
"""
# 在 Service 层获取用户权限信息
data_scope_context = DataScopeContext(
    user_id=current_user.user_id,
    dept_id=current_user.dept_id,
    role_scopes=[
        {"scope_type": "4", "dept_ids": None},  # 本部门及以下
        {"scope_type": "2", "dept_ids": [1, 2, 3]},  # 自定义部门
    ]
)

# 在 Repository 层使用
condition = data_scope_context.build_condition(SysUser)
query = select(SysUser).where(condition)
"""

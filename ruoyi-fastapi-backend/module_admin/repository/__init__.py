"""
Repository 模块

提供统一的数据访问层抽象，使用 Repository 模式替代传统 DAO。

Repository 相比 DAO 的优势：
1. 实例化设计 - 支持依赖注入和单元测试
2. 统一的基类 - 减少重复代码
3. 支持 Specification 模式 - 灵活的查询条件组合
4. 集成软删除 - 统一处理删除逻辑
5. 类型安全 - 完整的类型注解

使用示例:
    from module_admin.repository.user_repository import UserRepository
    
    # 在 Service 中使用
    class UserService:
        def __init__(self, db: AsyncSession):
            self.user_repo = UserRepository(db)
        
        async def get_user(self, user_id: int):
            return await self.user_repo.get_by_id(user_id)
"""

# 基础类
from module_admin.repository.base_repository import IRepository, BaseRepository
from module_admin.repository.specification import (
    Specification,
    BaseSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    equals,
    not_equals,
    like,
    in_,
    not_in,
    between,
    gt,
    gte,
    lt,
    lte,
    is_null,
    is_not_null,
    order_by,
    limit,
    offset,
)
from module_admin.repository.query_builder import QueryBuilder

# 业务 Repository
from module_admin.repository.user_repository import (
    UserRepository,
    UserRoleRepository,
    UserPostRepository,
)
from module_admin.repository.role_repository import (
    RoleRepository,
    RoleMenuRepository,
    RoleDeptRepository,
)
from module_admin.repository.dept_repository import DeptRepository
from module_admin.repository.menu_repository import MenuRepository
from module_admin.repository.config_repository import ConfigRepository
from module_admin.repository.post_repository import PostRepository
from module_admin.repository.notice_repository import NoticeRepository
from module_admin.repository.dict_repository import DictTypeRepository, DictDataRepository
from module_admin.repository.log_repository import OperLogRepository, LoginLogRepository
from module_admin.repository.audit_log_repository import AuditLogRepository
from module_admin.repository.job_repository import JobRepository, JobLogRepository
from module_admin.repository.project_repository import ProjectRepository
from module_admin.repository.project_version_repository import ProjectVersionRepository
from module_admin.repository.project_topology_repository import ProjectTopologyRepository
from module_admin.repository.protocol_repository import ProtocolRepository
from module_admin.repository.device_repository import DeviceRepository, DeviceInterfaceRepository
from module_admin.repository.device_category_repository import DeviceCategoryRepository
from module_admin.repository.simulation_repository import (
    SimulationSessionRepository,
    SimulationMessageRepository,
    SimulationBandwidthRepository,
    SimulationAlarmRepository,
)
from module_admin.repository.login_repository import LoginRepository

__all__ = [
    # 基础类
    'IRepository',
    'BaseRepository',
    'Specification',
    'BaseSpecification',
    'AndSpecification',
    'OrSpecification',
    'NotSpecification',
    'QueryBuilder',
    # 规范工厂函数
    'equals',
    'not_equals',
    'like',
    'in_',
    'not_in',
    'between',
    'gt',
    'gte',
    'lt',
    'lte',
    'is_null',
    'is_not_null',
    'order_by',
    'limit',
    'offset',
    # 业务 Repository
    'UserRepository',
    'UserRoleRepository',
    'UserPostRepository',
    'RoleRepository',
    'RoleMenuRepository',
    'RoleDeptRepository',
    'DeptRepository',
    'MenuRepository',
    'ConfigRepository',
    'PostRepository',
    'NoticeRepository',
    'DictTypeRepository',
    'DictDataRepository',
    'OperLogRepository',
    'LoginLogRepository',
    'AuditLogRepository',
    'JobRepository',
    'JobLogRepository',
    'ProjectRepository',
    'ProjectVersionRepository',
    'ProjectTopologyRepository',
    'ProtocolRepository',
    'DeviceRepository',
    'DeviceInterfaceRepository',
    'DeviceCategoryRepository',
    'SimulationSessionRepository',
    'SimulationMessageRepository',
    'SimulationBandwidthRepository',
    'SimulationAlarmRepository',
    'LoginRepository',
]

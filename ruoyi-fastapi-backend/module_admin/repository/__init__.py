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
    from modules.system.infrastructure.user_repository import UserRepository
    
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
from modules.system.infrastructure.user_repository import (
    UserRepository,
)
from modules.system.infrastructure.role_repository import (
    RoleRepository,
)
from modules.system.infrastructure.role_dept_repository import RoleDeptRepository
from modules.system.infrastructure.role_menu_repository import RoleMenuRepository
from modules.system.infrastructure.user_post_repository import UserPostRepository
from modules.system.infrastructure.user_role_repository import UserRoleRepository
from modules.system.infrastructure.dept_repository import DeptRepository
from modules.system.infrastructure.menu_repository import MenuRepository
from modules.system.infrastructure.config_repository import ConfigRepository
from modules.system.infrastructure.post_repository import PostRepository
from modules.system.infrastructure.notice_repository import NoticeRepository
from modules.system.infrastructure.dict_repository import DictTypeRepository, DictDataRepository
from modules.system.infrastructure.common_repository import CommonRepository
from modules.system.infrastructure.log_repository import OperLogRepository, LoginLogRepository
from modules.system.infrastructure.audit_log_repository import AuditLogRepository
from modules.scheduler.infrastructure.job_repository import JobRepository, JobLogRepository
from modules.project.infrastructure.project_repository import ProjectRepository
from modules.project.infrastructure.project_version_repository import ProjectVersionRepository
from modules.project.infrastructure.project_topology_repository import ProjectTopologyRepository
from module_admin.repository.protocol_repository import ProtocolRepository
from module_admin.repository.device_repository import DeviceRepository, DeviceInterfaceRepository
from module_admin.repository.device_category_repository import DeviceCategoryRepository
from module_admin.repository.simulation_repository import (
    SimulationSessionRepository,
    SimulationMessageRepository,
    SimulationBandwidthRepository,
    SimulationAlarmRepository,
)
from modules.identity.infrastructure.login_repository import LoginRepository

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
    'CommonRepository',
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

"""
Alembic 环境配置

用于配置数据库连接和元数据，支持 MySQL 和 PostgreSQL。

此文件配置了 Alembic 的运行环境，包括：
- 数据库连接配置（支持 MySQL 和 PostgreSQL）
- ORM 模型导入（确保 Alembic 能检测到所有表）
- 在线和离线迁移模式
- 自定义命名约定
"""

import os
import sys
from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import engine_from_config, pool, MetaData

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量配置
from config.env import DataBaseConfig

# 导入 Base 类（包含元数据）
from config.database import Base

# ============================================================================
# 导入所有 ORM 模型
# ============================================================================
# 必须导入所有模型，确保 Alembic 能检测到表结构变化
# 按模块分组导入，保持代码整洁

# 用户相关模型
from module_admin.entity.do.user_do import (  # noqa: F401
    UserDO,
    UserRoleDO,
    UserPostDO,
)

# 角色相关模型
from module_admin.entity.do.role_do import (  # noqa: F401
    RoleDO,
    RoleMenuDO,
    RoleDeptDO,
)

# 菜单模型
from module_admin.entity.do.menu_do import MenuDO  # noqa: F401

# 部门模型
from module_admin.entity.do.dept_do import DeptDO  # noqa: F401

# 岗位模型
from module_admin.entity.do.post_do import PostDO  # noqa: F401

# 字典模型
from module_admin.entity.do.dict_do import (  # noqa: F401
    DictTypeDO,
    DictDataDO,
)

# 配置模型
from module_admin.entity.do.config_do import ConfigDO  # noqa: F401

# 通知公告模型
from module_admin.entity.do.notice_do import NoticeDO  # noqa: F401

# 日志模型
from module_admin.entity.do.log_do import (  # noqa: F401
    OperLogDO,
    LogininforDO,
)

# 审计日志模型
from module_admin.entity.do.audit_log_do import AuditLogDO  # noqa: F401

# 定时任务模型
from module_admin.entity.do.job_do import (  # noqa: F401
    JobDO,
    JobLogDO,
)

# 项目相关模型
from module_admin.entity.do.project_do import ProjectDO  # noqa: F401
from module_admin.entity.do.project_version_do import ProjectVersionDO  # noqa: F401
from module_admin.entity.do.project_topology_do import ProjectTopologyDO  # noqa: F401

# 设备相关模型
from module_admin.entity.do.device_do import DeviceDO  # noqa: F401
from module_admin.entity.do.device_category_do import DeviceCategoryDO  # noqa: F401

# 协议模型
from module_admin.entity.do.protocol_do import ProtocolDO  # noqa: F401

# 仿真模型
from module_admin.entity.do.simulation_do import (  # noqa: F401
    SimulationSessionDO,
    SimulationMessageDO,
    SimulationBandwidthDO,
    SimulationAlarmDO,
)

# ============================================================================
# Alembic 配置
# ============================================================================

# Alembic Config 对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
target_metadata = Base.metadata

# 自定义命名约定（确保约束名称一致）
# 这对于跨数据库迁移和约束管理很重要
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# 应用命名约定到元数据
if target_metadata is not None:
    target_metadata.naming_convention = naming_convention


def get_database_url() -> str:
    """
    获取同步数据库 URL

    Alembic 需要使用同步驱动，因此需要转换异步驱动为同步驱动：
    - asyncmy (MySQL async) -> pymysql (MySQL sync)
    - asyncpg (PostgreSQL async) -> psycopg2 (PostgreSQL sync)

    Returns:
        str: 同步数据库连接 URL
    """
    db_type = DataBaseConfig.db_type
    host = DataBaseConfig.db_host
    port = DataBaseConfig.db_port
    username = DataBaseConfig.db_username
    password = quote_plus(DataBaseConfig.db_password)
    database = DataBaseConfig.db_database

    if db_type == 'postgresql':
        # PostgreSQL: 使用 psycopg2 同步驱动
        return f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}'
    else:
        # MySQL: 使用 pymysql 同步驱动
        return f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4'


def run_migrations_offline() -> None:
    """
    离线模式运行迁移

    仅生成 SQL 脚本，不连接数据库。
    用于预览迁移 SQL 或在无法直接连接数据库的环境中使用。

    使用场景：
    - 预览迁移将执行的 SQL 语句
    - 在受限环境中生成 SQL 脚本供 DBA 执行
    - 审计和文档化数据库变更

    命令示例:
        alembic upgrade head --sql > migration.sql
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,  # 检测字段类型变化
        compare_server_default=True,  # 检测默认值变化
        render_as_batch=True,  # 支持 SQLite 批量模式
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移

    直接连接数据库并执行迁移。
    这是正常使用的模式，用于开发和生产环境。

    特性：
    - 自动事务管理（失败时回滚）
    - 类型变化检测
    - 默认值变化检测
    - 连接池管理

    命令示例:
        alembic upgrade head          # 升级到最新版本
        alembic upgrade +1            # 升级一个版本
        alembic downgrade -1          # 回滚一个版本
        alembic current               # 查看当前版本
    """
    # 构建连接配置
    configuration = config.get_section(config.config_ini_section) or {}
    configuration['sqlalchemy.url'] = get_database_url()

    # 创建引擎（使用 NullPool 避免连接池问题）
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 检测字段类型变化
            compare_server_default=True,  # 检测默认值变化
            render_as_batch=True,  # 支持 SQLite 批量模式
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================================
# 主入口：根据模式选择运行方式
# ============================================================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

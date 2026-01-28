from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from urllib.parse import quote_plus
from config.env import DataBaseConfig
from module_admin.entity.do.enums import DelFlagEnum
from utils.soft_delete_filter import init_soft_delete_filter


def _build_connect_args() -> dict:
    """
    构建数据库连接参数
    
    Google 工程标准：
    - 必须配置语句超时，防止长时间查询阻塞
    - 必须配置锁超时，防止死锁
    - PostgreSQL 和 MySQL 使用不同的参数名
    
    Returns:
        dict: 连接参数字典
    """
    if DataBaseConfig.db_type == 'postgresql':
        return {
            "server_settings": {
                "jit": "off",  # PostgreSQL JIT 优化
                "statement_timeout": str(DataBaseConfig.db_statement_timeout),  # SQL 超时（毫秒）
                "lock_timeout": str(DataBaseConfig.db_lock_timeout),  # 锁超时（毫秒）
            }
        }
    else:  # MySQL
        return {
            "init_command": (
                f"SET SESSION max_execution_time={DataBaseConfig.db_statement_timeout};"  # SQL 超时
                f"SET SESSION innodb_lock_wait_timeout={DataBaseConfig.db_lock_timeout // 1000};"  # 锁超时（秒）
            )
        }


ASYNC_SQLALCHEMY_DATABASE_URL = (
    f'mysql+asyncmy://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
    f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
)
if DataBaseConfig.db_type == 'postgresql':
    ASYNC_SQLALCHEMY_DATABASE_URL = (
        f'postgresql+asyncpg://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )

async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    echo=DataBaseConfig.db_echo,
    # 连接池配置 - Google 标准
    pool_size=DataBaseConfig.db_pool_size,  # 核心连接数
    max_overflow=DataBaseConfig.db_max_overflow,  # 额外连接数
    pool_timeout=DataBaseConfig.db_pool_timeout,  # 获取连接超时
    pool_recycle=DataBaseConfig.db_pool_recycle,  # 连接回收时间
    pool_pre_ping=True,  # 🔧 连接健康检查（防止使用已断开的连接）
    # 性能优化
    echo_pool=False,  # 生产环境关闭连接池日志
    # 连接参数 - 包含查询超时和锁超时配置
    connect_args=_build_connect_args()
)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    expire_on_commit=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


# Register global soft-delete filtering for ORM SELECTs
init_soft_delete_filter(Base, del_flag_value=DelFlagEnum.EXIST.value)

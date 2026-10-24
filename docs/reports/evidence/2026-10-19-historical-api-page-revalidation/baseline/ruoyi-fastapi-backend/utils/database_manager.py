"""
数据库管理器
支持读写分离和多数据源配置
"""
import random
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置"""
    
    def __init__(
        self,
        url: str,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_recycle: int = 3600,
        pool_timeout: int = 30,
        pool_pre_ping: bool = True
    ):
        """
        初始化数据库配置
        
        Args:
            url: 数据库连接 URL
            echo: 是否打印 SQL
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_recycle: 连接回收时间（秒）
            pool_timeout: 连接超时时间（秒）
            pool_pre_ping: 连接前是否 ping
        """
        self.url = url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_timeout = pool_timeout
        self.pool_pre_ping = pool_pre_ping


class DatabaseManager:
    """
    数据库管理器
    
    支持读写分离：
    - 写操作使用主库
    - 读操作使用从库（支持多个从库负载均衡）
    """
    
    def __init__(
        self,
        write_config: DatabaseConfig,
        read_configs: Optional[List[DatabaseConfig]] = None,
        read_strategy: str = 'round_robin'
    ):
        """
        初始化数据库管理器
        
        Args:
            write_config: 写库配置
            read_configs: 读库配置列表（如果为空，则读写都用主库）
            read_strategy: 读库选择策略（'round_robin' 或 'random'）
        """
        self.write_config = write_config
        self.read_configs = read_configs or []
        self.read_strategy = read_strategy
        
        # 创建写引擎
        self.write_engine = self._create_engine(write_config)
        self.write_session_factory = async_sessionmaker(
            bind=self.write_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        # 创建读引擎
        self.read_engines: List[AsyncEngine] = []
        self.read_session_factories: List[async_sessionmaker] = []
        
        if self.read_configs:
            for config in self.read_configs:
                engine = self._create_engine(config)
                self.read_engines.append(engine)
                
                session_factory = async_sessionmaker(
                    bind=engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False
                )
                self.read_session_factories.append(session_factory)
        else:
            # 如果没有配置读库，使用写库
            self.read_engines.append(self.write_engine)
            self.read_session_factories.append(self.write_session_factory)
        
        # 轮询索引（用于 round_robin 策略）
        self._read_index = 0
        
        logger.info(f"数据库管理器初始化完成: 写库 1 个, 读库 {len(self.read_engines)} 个")
    
    def _create_engine(self, config: DatabaseConfig) -> AsyncEngine:
        """
        创建数据库引擎
        
        Args:
            config: 数据库配置
        
        Returns:
            AsyncEngine 实例
        """
        return create_async_engine(
            config.url,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_recycle=config.pool_recycle,
            pool_timeout=config.pool_timeout,
            pool_pre_ping=config.pool_pre_ping
        )
    
    def get_write_session(self) -> AsyncSession:
        """
        获取写会话（连接到主库）
        
        Returns:
            AsyncSession 实例
        """
        return self.write_session_factory()
    
    def get_read_session(self) -> AsyncSession:
        """
        获取读会话（连接到从库）
        
        使用配置的策略选择从库
        
        Returns:
            AsyncSession 实例
        """
        if not self.read_session_factories:
            # 没有读库，使用写库
            return self.write_session_factory()
        
        # 选择读库
        factory = self._select_read_factory()
        return factory()
    
    def _select_read_factory(self) -> async_sessionmaker:
        """
        选择读库工厂
        
        Returns:
            async_sessionmaker 实例
        """
        if len(self.read_session_factories) == 1:
            return self.read_session_factories[0]
        
        if self.read_strategy == 'random':
            # 随机选择
            return random.choice(self.read_session_factories)
        else:
            # 轮询（round_robin）
            factory = self.read_session_factories[self._read_index]
            self._read_index = (self._read_index + 1) % len(self.read_session_factories)
            return factory
    
    @asynccontextmanager
    async def write_session(self):
        """
        写会话上下文管理器
        
        自动管理会话的创建和关闭
        
        Yields:
            AsyncSession 实例
        """
        session = self.get_write_session()
        async with session.begin():
            yield session
        await session.close()
    
    @asynccontextmanager
    async def read_session(self):
        """
        读会话上下文管理器
        
        Yields:
            AsyncSession 实例
        """
        session = self.get_read_session()
        yield session
        await session.close()
    
    async def close_all(self):
        """关闭所有数据库连接"""
        await self.write_engine.dispose()
        for engine in self.read_engines:
            if engine != self.write_engine:
                await engine.dispose()
        logger.info("所有数据库连接已关闭")
    
    async def health_check(self) -> dict:
        """
        健康检查
        
        检查所有数据库连接是否正常
        
        Returns:
            健康检查结果
        """
        from sqlalchemy import text
        
        result = {
            'write_db': True,
            'read_dbs': [],
            'healthy': True
        }

        async with self.write_session() as session:
            await session.execute(text("SELECT 1"))

        for i, factory in enumerate(self.read_session_factories):
            async with factory() as session:
                await session.execute(text("SELECT 1"))
            result['read_dbs'].append({'index': i, 'healthy': True})

        result['healthy'] = result['write_db'] and all(db['healthy'] for db in result['read_dbs'])
        return result


# 单例实例（可选）
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    获取数据库管理器单例
    
    Returns:
        DatabaseManager 实例
    """
    global _db_manager
    if _db_manager is None:
        raise RuntimeError("数据库管理器未初始化，请先调用 init_db_manager()")
    return _db_manager


def init_db_manager(
    write_config: DatabaseConfig,
    read_configs: Optional[List[DatabaseConfig]] = None,
    read_strategy: str = 'round_robin'
) -> DatabaseManager:
    """
    初始化数据库管理器单例
    
    Args:
        write_config: 写库配置
        read_configs: 读库配置列表
        read_strategy: 读库选择策略
    
    Returns:
        DatabaseManager 实例
    """
    global _db_manager
    _db_manager = DatabaseManager(write_config, read_configs, read_strategy)
    return _db_manager


# 使用示例
"""
from utils.database_manager import DatabaseConfig, DatabaseManager, init_db_manager

# 1. 配置数据库
write_config = DatabaseConfig(
    url="mysql+asyncmy://user:pass@host:3306/db_write",
    pool_size=20,
    max_overflow=40
)

read_configs = [
    DatabaseConfig(
        url="mysql+asyncmy://user:pass@host1:3306/db_read1",
        pool_size=10
    ),
    DatabaseConfig(
        url="mysql+asyncmy://user:pass@host2:3306/db_read2",
        pool_size=10
    )
]

# 2. 初始化管理器
db_manager = init_db_manager(write_config, read_configs, read_strategy='round_robin')

# 3. 使用写会话
async with db_manager.write_session() as session:
    device = DeviceDO(device_name="传感器01")
    session.add(device)
    # 自动提交

# 4. 使用读会话
async with db_manager.read_session() as session:
    devices = await session.execute(select(DeviceDO))
    # 自动关闭

# 5. 或者手动获取会话
write_session = db_manager.get_write_session()
read_session = db_manager.get_read_session()

# 6. 健康检查
health = await db_manager.health_check()
print(f"数据库健康状态: {health}")

# 7. 关闭所有连接
await db_manager.close_all()

# 8. 在 Repository 中使用
class DeviceRepository:
    def __init__(self, use_read: bool = False):
        self.db_manager = get_db_manager()
        self.use_read = use_read
    
    async def find_all(self):
        # 读操作使用读库
        async with self.db_manager.read_session() as session:
            result = await session.execute(select(DeviceDO))
            return result.scalars().all()
    
    async def create(self, device: DeviceDO):
        # 写操作使用写库
        async with self.db_manager.write_session() as session:
            session.add(device)
            # 自动提交
            return device
"""

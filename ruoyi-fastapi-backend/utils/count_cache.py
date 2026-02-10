"""
COUNT 查询缓存

将 SELECT COUNT(*) 的结果独立缓存到 Redis，避免每次分页都查数据库统计总数。

核心设计：
1. COUNT 缓存与数据缓存分离 - 翻页时复用 COUNT 结果
2. 缓存 key 基于表名+查询条件 - 不包含分页参数
3. 写操作时按表名批量失效 - 保证数据一致性
4. 支持单飞锁 - 防止缓存击穿

使用示例：
    # 在 PageUtil.paginate() 中自动使用
    # 或手动使用：
    count_cache = get_count_cache()
    total = await count_cache.get_or_load(
        table='sys_user',
        query_hash='abc123',
        loader=lambda: db.execute(count_stmt)
    )
    
    # 写操作后失效缓存
    await count_cache.invalidate_table('sys_user')
"""
import asyncio
import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CountCache:
    """
    COUNT 查询缓存管理器
    
    专门用于缓存 SELECT COUNT(*) 结果，与分页数据缓存分离。
    """
    
    def __init__(
        self,
        redis_client=None,
        default_ttl: int = 600,
        key_prefix: str = "count_cache",
        enabled: bool = True
    ):
        """
        初始化 COUNT 缓存
        
        Args:
            redis_client: Redis 客户端（异步）
            default_ttl: 默认缓存时间（秒），COUNT 缓存可以设置较长
            key_prefix: 缓存键前缀
            enabled: 是否启用缓存
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._enabled = enabled and redis_client is not None
        self._locks: Dict[str, asyncio.Lock] = {}
        
        if not self._enabled:
            logger.info("COUNT 缓存未启用（Redis 未配置或已禁用）")
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def build_key(self, table: str, query_hash: str) -> str:
        """
        构建缓存 key
        
        Args:
            table: 表名
            query_hash: 查询条件的 hash 值
        
        Returns:
            缓存 key，格式：count_cache:{table}:{hash}
        """
        return f"{self.key_prefix}:{table}:{query_hash}"
    
    @staticmethod
    def hash_query(conditions: Dict[str, Any]) -> str:
        """
        计算查询条件的 hash 值
        
        Args:
            conditions: 查询条件字典（不含分页参数）
        
        Returns:
            MD5 hash 字符串
        """
        # 过滤掉 None 值和分页参数
        filtered = {
            k: v for k, v in conditions.items() 
            if v is not None and k not in ('page', 'page_num', 'page_size', 'offset', 'limit')
        }
        key_str = json.dumps(filtered, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """获取单飞锁（防止缓存击穿）"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    async def get(self, key: str) -> Optional[int]:
        """
        从缓存获取 COUNT 结果
        
        Args:
            key: 缓存键
        
        Returns:
            缓存的总数或 None
        """
        if not self._enabled:
            return None
        
        cached = await self.redis.get(key)
        if cached is not None:
            if isinstance(cached, bytes):
                cached = cached.decode()
            logger.debug(f"COUNT 缓存命中: {key} = {cached}")
            return int(cached)
        
        logger.debug(f"COUNT 缓存未命中: {key}")
        return None
    
    async def set(self, key: str, value: int, ttl: Optional[int] = None):
        """
        设置 COUNT 缓存
        
        Args:
            key: 缓存键
            value: COUNT 结果
            ttl: 过期时间（秒）
        """
        if not self._enabled:
            return
        
        ttl = ttl or self.default_ttl
        await self.redis.setex(key, ttl, str(value))
        logger.debug(f"COUNT 缓存已设置: {key} = {value}, TTL: {ttl}s")
    
    async def get_or_load(
        self,
        table: str,
        query_hash: str,
        loader: Callable[[], Any],
        ttl: Optional[int] = None,
        use_lock: bool = True
    ) -> int:
        """
        获取 COUNT 缓存，如未命中则执行 loader 并缓存结果
        
        Args:
            table: 表名
            query_hash: 查询条件 hash
            loader: 加载函数（执行 COUNT 查询）
            ttl: 缓存时间
            use_lock: 是否使用单飞锁
        
        Returns:
            COUNT 结果
        """
        key = self.build_key(table, query_hash)
        
        # 尝试从缓存获取
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # 未命中，需要加载
        if use_lock and self._enabled:
            lock = self._get_lock(key)
            async with lock:
                # 双重检查
                cached = await self.get(key)
                if cached is not None:
                    return cached
                
                # 执行查询
                result = await loader()
                total = result if isinstance(result, int) else int(result)
                
                # 写入缓存
                await self.set(key, total, ttl)
                return total
        
        # 不使用锁或缓存未启用
        result = await loader()
        total = result if isinstance(result, int) else int(result)
        
        if self._enabled:
            await self.set(key, total, ttl)
        
        return total
    
    async def invalidate(self, key: str):
        """
        删除单个缓存
        
        Args:
            key: 缓存键
        """
        if not self._enabled:
            return
        
        await self.redis.delete(key)
        logger.debug(f"COUNT 缓存已删除: {key}")
    
    async def invalidate_table(self, table: str):
        """
        删除指定表的所有 COUNT 缓存
        
        Args:
            table: 表名
        """
        if not self._enabled:
            return
        
        pattern = f"{self.key_prefix}:{table}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
            logger.info(f"已删除表 '{table}' 的 {len(keys)} 个 COUNT 缓存")
    
    async def invalidate_tables(self, tables: List[str]):
        """
        批量删除多个表的 COUNT 缓存
        
        Args:
            tables: 表名列表
        """
        for table in tables:
            await self.invalidate_table(table)
    
    async def clear_all(self):
        """清空所有 COUNT 缓存"""
        if not self._enabled:
            return
        
        pattern = f"{self.key_prefix}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
            logger.info(f"已清空所有 COUNT 缓存，共 {len(keys)} 个")


def invalidate_count_cache(*tables: str):
    """
    写操作后自动失效 COUNT 缓存的装饰器
    
    Args:
        *tables: 要失效的表名列表
    
    使用示例：
        @invalidate_count_cache('sys_user', 'sys_user_role')
        async def add_user(self, user: UserDO):
            self.db.add(user)
            await self.db.flush()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # 获取缓存实例并失效
            cache = get_count_cache()
            if cache.enabled:
                await cache.invalidate_tables(list(tables))
            
            return result
        return wrapper
    return decorator


# 单例实例
_count_cache: Optional[CountCache] = None


def get_count_cache() -> CountCache:
    """获取 COUNT 缓存单例"""
    global _count_cache
    if _count_cache is None:
        return CountCache(redis_client=None, enabled=False)
    return _count_cache


def init_count_cache(
    redis_client,
    default_ttl: int = 600,
    key_prefix: str = "count_cache",
    enabled: bool = True
) -> CountCache:
    """
    初始化 COUNT 缓存单例
    
    Args:
        redis_client: Redis 客户端
        default_ttl: 默认过期时间（秒）
        key_prefix: 键前缀
        enabled: 是否启用
    
    Returns:
        CountCache 实例
    """
    global _count_cache
    _count_cache = CountCache(redis_client, default_ttl, key_prefix, enabled)
    return _count_cache


def extract_table_from_query(query) -> Optional[str]:
    """
    从 SQLAlchemy 查询中提取主表名
    
    Args:
        query: SQLAlchemy Select 对象
    
    Returns:
        表名或 None
    """
    try:
        # 尝试从 column_descriptions 获取
        for desc in getattr(query, 'column_descriptions', []):
            entity = desc.get('entity')
            if entity is not None and hasattr(entity, '__tablename__'):
                return entity.__tablename__
        
        # 尝试从 froms 获取
        froms = query.get_final_froms()
        if froms:
            first_from = froms[0]
            if hasattr(first_from, 'name'):
                return first_from.name
            if hasattr(first_from, 'element') and hasattr(first_from.element, 'name'):
                return first_from.element.name
    except Exception as e:
        logger.debug(f"提取表名失败: {e}")
    
    return None


def extract_conditions_hash(query) -> str:
    """
    从 SQLAlchemy 查询中提取查询条件并计算 hash
    
    Args:
        query: SQLAlchemy Select 对象
    
    Returns:
        条件的 hash 值
    """
    try:
        # 获取 WHERE 子句
        whereclause = getattr(query, 'whereclause', None)
        if whereclause is not None:
            condition_str = str(whereclause.compile(compile_kwargs={"literal_binds": True}))
        else:
            condition_str = ""
        
        return hashlib.md5(condition_str.encode()).hexdigest()[:16]
    except Exception as e:
        logger.debug(f"提取查询条件失败: {e}")
        # 使用整个查询语句作为 fallback
        return hashlib.md5(str(query).encode()).hexdigest()[:16]

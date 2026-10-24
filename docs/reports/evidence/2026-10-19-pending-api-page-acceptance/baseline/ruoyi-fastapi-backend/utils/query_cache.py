"""
查询缓存管理器
基于 Redis 的查询结果缓存
"""
import asyncio
import json
import hashlib
from typing import Any, Optional, Callable, TypeVar, List, Dict
from inspect import iscoroutinefunction
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class QueryCache:
    """
    查询缓存管理器
    
    使用 Redis 缓存查询结果，减少数据库压力
    """
    
    def __init__(
        self,
        redis_client=None,
        default_ttl: int = 300,
        key_prefix: str = "query_cache",
        is_async: Optional[bool] = None
    ):
        """
        初始化查询缓存
        
        Args:
            redis_client: Redis 客户端实例（支持 redis-py 或 aioredis）
            default_ttl: 默认缓存过期时间（秒）
            key_prefix: 缓存键前缀
        """
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self._enabled = redis_client is not None
        self._is_async = self._detect_async(redis_client) if is_async is None else is_async
        self._locks: Dict[str, asyncio.Lock] = {}
        
        if not self._enabled:
            logger.warning("Redis 客户端未配置，查询缓存将被禁用")

    def _detect_async(self, redis_client) -> bool:
        """判断 Redis 客户端是否为异步客户端"""
        if redis_client is None:
            return False
        get_func = getattr(redis_client, 'get', None)
        return iscoroutinefunction(get_func)
    
    def _generate_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            func_name: 函数名
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            缓存键
        """
        # 构建键数据
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': str(sorted(kwargs.items()))
        }
        
        # 序列化并生成哈希
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"{self.key_prefix}:{func_name}:{key_hash}"

    def build_key(self, namespace: str, parts: Dict[str, Any]) -> str:
        """
        生成稳定的缓存键（避免包含不可序列化对象）

        Args:
            namespace: 业务命名空间（如 role:list）
            parts: 参与缓存键计算的参数

        Returns:
            缓存键
        """
        key_str = json.dumps(parts, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{self.key_prefix}:{namespace}:{key_hash}"

    def _get_lock(self, key: str) -> asyncio.Lock:
        """获取单飞锁（防止缓存击穿）"""
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock
    
    async def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键
        
        Returns:
            缓存的数据或 None
        """
        if not self._enabled:
            return None
        
        if self._is_async:
            cached = await self.redis.get(key)
        else:
            cached = self.redis.get(key)

        if cached:
            if isinstance(cached, (bytes, bytearray)):
                cached = cached.decode()
            logger.debug(f"缓存命中: {key}")
            return json.loads(cached)

        logger.debug(f"缓存未命中: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 要缓存的数据
            ttl: 过期时间（秒）
        """
        if not self._enabled:
            return
        
        ttl = ttl or self.default_ttl
        serialized = json.dumps(value, default=str, ensure_ascii=False)

        if self._is_async:
            await self.redis.setex(key, ttl, serialized)
        else:
            self.redis.setex(key, ttl, serialized)

        logger.debug(f"缓存已设置: {key}, TTL: {ttl}s")

    async def get_or_set(
        self,
        key: str,
        loader: Callable[[], Any],
        ttl: Optional[int] = None,
        use_lock: bool = False
    ):
        """
        获取缓存，如未命中则执行 loader 并写入缓存

        Args:
            key: 缓存键
            loader: 异步加载函数
            ttl: 过期时间
            use_lock: 是否启用单飞锁
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        if use_lock:
            lock = self._get_lock(key)
            async with lock:
                cached = await self.get(key)
                if cached is not None:
                    return cached
                result = await loader()
                await self.set(key, result, ttl)
                return result

        result = await loader()
        await self.set(key, result, ttl)
        return result
    
    async def delete(self, key: str):
        """
        删除缓存
        
        Args:
            key: 缓存键
        """
        if not self._enabled:
            return
        
        if self._is_async:
            await self.redis.delete(key)
        else:
            self.redis.delete(key)
        logger.debug(f"缓存已删除: {key}")
    
    async def delete_pattern(self, pattern: str):
        """
        根据模式删除缓存
        
        Args:
            pattern: 键模式（支持通配符）
        """
        if not self._enabled:
            return
        
        if self._is_async:
            keys = await self.redis.keys(pattern)
        else:
            keys = self.redis.keys(pattern)

        if keys:
            if self._is_async:
                await self.redis.delete(*keys)
            else:
                self.redis.delete(*keys)
            logger.info(f"已删除 {len(keys)} 个缓存: {pattern}")
    
    async def clear_all(self):
        """清空所有缓存"""
        await self.delete_pattern(f"{self.key_prefix}:*")
    
    def cached(
        self,
        ttl: Optional[int] = None,
        key_builder: Optional[Callable] = None,
        use_lock: bool = False
    ):
        """
        查询缓存装饰器
        
        Args:
            ttl: 缓存过期时间（秒）
            key_builder: 自定义键生成函数
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                if use_lock:
                    lock = self._get_lock(cache_key)
                    async with lock:
                        # 双重检查，避免并发重复计算
                        cached_result = await self.get(cache_key)
                        if cached_result is not None:
                            return cached_result
                        result = await func(*args, **kwargs)
                        await self.set(cache_key, result, ttl)
                        return result

                # 执行函数
                result = await func(*args, **kwargs)

                # 缓存结果
                await self.set(cache_key, result, ttl)

                return result
            
            return wrapper
        return decorator
    
    def invalidate_on_write(self, patterns: List[str]):
        """
        写操作缓存失效装饰器
        
        Args:
            patterns: 要失效的缓存键模式列表
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 执行写操作
                result = await func(*args, **kwargs)
                
                # 使缓存失效
                for pattern in patterns:
                    await self.delete_pattern(pattern)
                
                return result
            
            return wrapper
        return decorator


class CacheManager:
    """
    缓存管理器
    
    提供更高级的缓存管理功能
    """
    
    def __init__(self, query_cache: QueryCache):
        """
        初始化缓存管理器
        
        Args:
            query_cache: QueryCache 实例
        """
        self.cache = query_cache
        self._cache_groups = {}
    
    def register_group(self, group_name: str, patterns: List[str]):
        """
        注册缓存组
        
        Args:
            group_name: 组名
            patterns: 键模式列表
        """
        self._cache_groups[group_name] = patterns
    
    async def invalidate_group(self, group_name: str):
        """
        使缓存组失效
        
        Args:
            group_name: 组名
        """
        patterns = self._cache_groups.get(group_name, [])
        for pattern in patterns:
            await self.cache.delete_pattern(pattern)
        logger.info(f"缓存组 '{group_name}' 已失效")
    
    async def warm_up(self, func: Callable, params_list: List[tuple]):
        """
        缓存预热
        
        Args:
            func: 要预热的函数
            params_list: 参数列表
        """
        logger.info(f"开始预热缓存: {func.__name__}")
        for params in params_list:
            args, kwargs = params if isinstance(params, tuple) and len(params) == 2 else (params, {})
            await func(*args, **kwargs)
        logger.info(f"缓存预热完成: {func.__name__}")


# 单例实例
_query_cache: Optional[QueryCache] = None


def get_query_cache() -> QueryCache:
    """
    获取查询缓存单例
    
    Returns:
        QueryCache 实例
    """
    global _query_cache
    if _query_cache is None:
        logger.warning("查询缓存未初始化，将返回禁用的缓存实例")
        return QueryCache(redis_client=None)
    return _query_cache


def init_query_cache(
    redis_client,
    default_ttl: int = 300,
    key_prefix: str = "query_cache",
    is_async: Optional[bool] = None
) -> QueryCache:
    """
    初始化查询缓存单例
    
    Args:
        redis_client: Redis 客户端
        default_ttl: 默认过期时间
        key_prefix: 键前缀
    
    Returns:
        QueryCache 实例
    """
    global _query_cache
    _query_cache = QueryCache(redis_client, default_ttl, key_prefix, is_async=is_async)
    return _query_cache


# 使用示例
"""
import redis.asyncio as redis
from utils.query_cache import QueryCache, init_query_cache, get_query_cache

# 1. 初始化 Redis 和查询缓存
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
query_cache = init_query_cache(redis_client, default_ttl=600)

# 2. 使用装饰器缓存查询
@query_cache.cached(ttl=300)
async def get_device_by_id(db: AsyncSession, device_id: int):
    result = await db.execute(select(DeviceDO).where(DeviceDO.device_id == device_id))
    return result.scalar_one_or_none()

# 3. 写操作时使缓存失效
@query_cache.invalidate_on_write([
    "query_cache:get_device_by_id:*",
    "query_cache:get_device_list:*"
])
async def create_device(db: AsyncSession, device: DeviceDO):
    db.add(device)
    await db.flush()
    return device

# 4. 在 Repository 中使用
class DeviceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_query_cache()
    
    async def find_by_id(self, device_id: int):
        # 使用缓存装饰器
        @self.cache.cached(ttl=300)
        async def _query():
            result = await self.db.execute(
                select(DeviceDO).where(DeviceDO.device_id == device_id)
            )
            return result.scalar_one_or_none()
        
        return await _query()
    
    async def create(self, device: DeviceDO):
        self.db.add(device)
        await self.db.flush()
        
        # 清除相关缓存
        await self.cache.delete_pattern("query_cache:*device*")
        
        return device

# 5. 手动缓存管理
cache = get_query_cache()

# 获取缓存
result = await cache.get("my_key")

# 设置缓存
await cache.set("my_key", {"data": "value"}, ttl=600)

# 删除缓存
await cache.delete("my_key")

# 清空所有缓存
await cache.clear_all()

# 6. 缓存组管理
from utils.query_cache import CacheManager

cache_manager = CacheManager(query_cache)

# 注册缓存组
cache_manager.register_group('device', [
    'query_cache:get_device_*',
    'query_cache:find_device_*'
])

# 使缓存组失效
await cache_manager.invalidate_group('device')

# 7. 缓存预热
async def warm_up_device_cache():
    popular_ids = [1, 2, 3, 4, 5]
    params_list = [((db, device_id), {}) for device_id in popular_ids]
    await cache_manager.warm_up(get_device_by_id, params_list)
"""

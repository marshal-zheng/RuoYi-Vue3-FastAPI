"""
事务管理器 - Google 工程标准

提供：
- 显式事务边界控制
- 嵌套事务支持（Savepoint）
- 事务隔离级别配置
- 事务重试机制
- 事务监控和日志
- @transactional() 装饰器
"""
from contextlib import asynccontextmanager
from typing import Optional, Callable, Any
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event, text
from utils.log_util import logger
import asyncio
import time


class TransactionIsolationLevel:
    """事务隔离级别"""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class TransactionManager:
    """
    事务管理器
    
    Google 标准实践：
    - 显式事务边界
    - 自动重试瞬态错误
    - 事务超时控制
    - 详细的事务日志
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._transaction_start_time: Optional[float] = None
    
    @asynccontextmanager
    async def transaction(
        self,
        isolation_level: Optional[str] = None,
        timeout: Optional[float] = None,
        savepoint: bool = True
    ):
        """
        事务上下文管理器
        
        Args:
            isolation_level: 事务隔离级别
            timeout: 事务超时时间（秒）
            savepoint: 是否使用 Savepoint（嵌套事务）
        
        Usage:
            async with TransactionManager(db).transaction():
                # 数据库操作
                await db.execute(...)
        """
        self._transaction_start_time = time.time()
        transaction_id = id(self.db)
        
        # 设置隔离级别
        if isolation_level:
            await self._set_isolation_level(isolation_level)
        
        # 检查是否已有事务在进行中
        already_in_transaction = self.db.in_transaction()
        
        if already_in_transaction:
            if savepoint:
                # 已有事务默认开启 savepoint，保证内层异常可回滚且不污染外层事务。
                async with self.db.begin_nested() as nested:
                    logger.debug(f"Transaction {transaction_id}: Started nested transaction (savepoint)")
                    try:
                        if timeout:
                            async with asyncio.timeout(timeout):
                                yield nested
                        else:
                            yield nested
                        duration = time.time() - self._transaction_start_time
                        logger.debug(
                            f"Transaction {transaction_id}: Nested transaction committed "
                            f"(duration: {duration:.3f}s)"
                        )
                    except asyncio.TimeoutError:
                        duration = time.time() - self._transaction_start_time
                        logger.error(f"Transaction {transaction_id}: Timeout after {duration:.3f}s")
                        raise
                    except Exception as e:
                        duration = time.time() - self._transaction_start_time
                        logger.error(
                            f"Transaction {transaction_id}: Nested transaction rolled back "
                            f"(duration: {duration:.3f}s) - {e}"
                        )
                        raise
            else:
                logger.debug(f"Transaction {transaction_id}: Joining existing transaction")
                try:
                    if timeout:
                        async with asyncio.timeout(timeout):
                            yield None
                    else:
                        yield None
                    duration = time.time() - self._transaction_start_time
                    logger.debug(
                        f"Transaction {transaction_id}: Joined transaction completed "
                        f"(duration: {duration:.3f}s)"
                    )
                except asyncio.TimeoutError:
                    duration = time.time() - self._transaction_start_time
                    logger.error(f"Transaction {transaction_id}: Timeout after {duration:.3f}s")
                    raise
                except Exception as e:
                    duration = time.time() - self._transaction_start_time
                    logger.error(
                        f"Transaction {transaction_id}: Joined transaction failed "
                        f"(duration: {duration:.3f}s) - {e}"
                    )
                    raise
        else:
            # 无事务：开启新事务
            async with self.db.begin() as trans:
                logger.debug(f"Transaction {transaction_id}: Started transaction")
                try:
                    # 超时控制：包裹调用方在 with 代码块内的执行
                    if timeout:
                        async with asyncio.timeout(timeout):
                            yield trans
                    else:
                        yield trans
                    
                    # 记录事务执行时间
                    duration = time.time() - self._transaction_start_time
                    logger.debug(f"Transaction {transaction_id}: Committed (duration: {duration:.3f}s)")
                    
                except asyncio.TimeoutError:
                    duration = time.time() - self._transaction_start_time
                    logger.error(f"Transaction {transaction_id}: Timeout after {duration:.3f}s")
                    raise
                except Exception as e:
                    duration = time.time() - self._transaction_start_time
                    logger.error(f"Transaction {transaction_id}: Rolled back (duration: {duration:.3f}s) - {e}")
                    raise
    
    async def _execute_with_transaction(self, trans):
        """内部方法：在事务中执行"""
        yield trans
    
    async def _set_isolation_level(self, level: str):
        """设置事务隔离级别"""
        normalized_level = (level or "").strip().upper()
        allowed_levels = {
            TransactionIsolationLevel.READ_UNCOMMITTED,
            TransactionIsolationLevel.READ_COMMITTED,
            TransactionIsolationLevel.REPEATABLE_READ,
            TransactionIsolationLevel.SERIALIZABLE,
        }
        if normalized_level not in allowed_levels:
            raise ValueError(f"Unsupported transaction isolation level: {level}")

        bind = self.db.get_bind()
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "").lower()
        # SQLite 不支持 SET TRANSACTION ISOLATION LEVEL 语句，测试环境下跳过。
        if dialect_name == "sqlite":
            logger.debug(f"Skip setting isolation level for sqlite: {normalized_level}")
            return

        await self.db.execute(text(f"SET TRANSACTION ISOLATION LEVEL {normalized_level}"))
        logger.debug(f"Set transaction isolation level to {normalized_level}")
    
    @staticmethod
    async def retry_on_deadlock(
        func: Callable,
        max_retries: int = 3,
        backoff_factor: float = 0.1
    ) -> Any:
        """
        死锁重试装饰器
        
        Args:
            func: 要执行的异步函数
            max_retries: 最大重试次数
            backoff_factor: 退避因子
        
        Returns:
            函数执行结果
        """
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                error_msg = str(e).lower()
                # 检测死锁错误
                is_deadlock = (
                    'deadlock' in error_msg or
                    'lock wait timeout' in error_msg or
                    '1213' in error_msg  # MySQL deadlock error code
                )
                
                if is_deadlock and attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"Deadlock detected, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise


class TransactionMonitor:
    """
    事务监控器
    
    监控长时间运行的事务和连接泄漏
    """
    
    @staticmethod
    def setup_monitoring(engine):
        """设置事务监控"""
        
        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
            """记录 SQL 执行开始时间"""
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
            """记录慢查询"""
            total_time = time.time() - conn.info['query_start_time'].pop()
            if total_time > 1.0:  # 超过 1 秒的查询
                logger.warning(
                    f"Slow query detected: {total_time:.3f}s\n"
                    f"SQL: {statement}\n"
                    f"Params: {params}"
                )


def transactional(
    isolation_level: Optional[str] = None,
    timeout: Optional[float] = None,
    retry_on_deadlock: bool = False,
    max_retries: int = 3
):
    """
    事务装饰器 - 简化事务管理
    
    Google 工程标准：
    - 自动管理事务边界
    - 支持死锁重试
    - 支持事务超时
    - 详细的错误日志
    
    Args:
        isolation_level: 事务隔离级别
        timeout: 事务超时时间（秒）
        retry_on_deadlock: 是否在死锁时自动重试
        max_retries: 最大重试次数
    
    Usage:
        @transactional()
        async def create_user(db: AsyncSession, user_data: dict):
            user = User(**user_data)
            db.add(user)
            await db.flush()
            return user
        
        @transactional(isolation_level=TransactionIsolationLevel.SERIALIZABLE, retry_on_deadlock=True)
        async def transfer_money(db: AsyncSession, from_id: int, to_id: int, amount: float):
            # 转账操作
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 查找 AsyncSession 参数
            db = None
            for arg in args:
                if isinstance(arg, AsyncSession):
                    db = arg
                    break

            # 支持实例化 service 的构造器注入场景（self.query_db / self.db）
            if db is None and args:
                owner = args[0]
                for attr in ('query_db', 'db'):
                    candidate = getattr(owner, attr, None)
                    if isinstance(candidate, AsyncSession):
                        db = candidate
                        break
            
            if db is None:
                # 尝试从 kwargs 中查找
                for key, value in kwargs.items():
                    if isinstance(value, AsyncSession):
                        db = value
                        break
            
            if db is None:
                # 如果没有找到 AsyncSession，直接执行函数（可能是测试或其他场景）
                logger.warning(f"@transactional: No AsyncSession found in {func.__name__}, executing without transaction")
                return await func(*args, **kwargs)
            
            # 定义执行函数
            async def _execute():
                async with TransactionManager(db).transaction(
                    isolation_level=isolation_level,
                    timeout=timeout
                ):
                    return await func(*args, **kwargs)
            
            # 是否启用死锁重试
            if retry_on_deadlock:
                return await TransactionManager.retry_on_deadlock(
                    _execute,
                    max_retries=max_retries
                )
            else:
                return await _execute()
        
        return wrapper
    return decorator


# 使用示例
"""
# 1. 基本事务（使用装饰器）
@transactional()
async def create_user(db: AsyncSession, user_data: dict):
    user = User(**user_data)
    db.add(user)
    await db.flush()
    return user

# 2. 基本事务（使用上下文管理器）
async def create_user_manual(db: AsyncSession, user_data: dict):
    async with TransactionManager(db).transaction():
        user = User(**user_data)
        db.add(user)
        await db.flush()
        return user

# 3. 嵌套事务（Savepoint）
async def complex_operation(db: AsyncSession):
    async with TransactionManager(db).transaction():
        # 外层事务
        await db.execute(...)
        
        try:
            async with TransactionManager(db).transaction(savepoint=True):
                # 内层事务（Savepoint）
                await db.execute(...)
        except Exception:
            # 内层事务回滚，外层事务继续
            pass
        
        await db.execute(...)

# 4. 死锁重试（使用装饰器）
@transactional(
    isolation_level=TransactionIsolationLevel.SERIALIZABLE,
    retry_on_deadlock=True,
    max_retries=3
)
async def transfer_money(db: AsyncSession, from_id: int, to_id: int, amount: float):
    # 转账操作
    await db.execute(...)

# 5. 事务超时（使用装饰器）
@transactional(timeout=30.0)
async def batch_operation(db: AsyncSession):
    # 必须在 30 秒内完成
    await db.execute(...)

# 6. 手动死锁重试（使用上下文管理器）
async def transfer_money_manual(db: AsyncSession, from_id: int, to_id: int, amount: float):
    async def _transfer():
        async with TransactionManager(db).transaction(
            isolation_level=TransactionIsolationLevel.SERIALIZABLE
        ):
            # 转账操作
            await db.execute(...)
    
    return await TransactionManager.retry_on_deadlock(_transfer, max_retries=3)
"""

"""
事务管理器测试

测试 TransactionManager 和 @transactional() 装饰器的功能

Google 工程标准：
- 测试事务提交和回滚
- 测试嵌套事务（Savepoint）
- 测试死锁重试
- 测试事务超时
- 测试隔离级别
"""
import pytest
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.transaction_manager import (
    TransactionManager,
    TransactionIsolationLevel,
    transactional
)
from module_admin.entity.do.config_do import ConfigDO


class TestTransactionManager:
    """事务管理器测试套件"""

    @pytest.mark.asyncio
    async def test_basic_transaction_commit(self, db_session: AsyncSession):
        """
        测试基本事务提交
        """
        # 创建测试数据
        config = ConfigDO(
            config_name="test_transaction",
            config_key="test.transaction.key",
            config_value="test_value",
            config_type="Y",
            create_by="test",
            remark="Transaction test"
        )
        
        # 使用事务
        async with TransactionManager(db_session).transaction():
            db_session.add(config)
            await db_session.flush()
        
        # 验证数据已提交
        result = await db_session.execute(
            select(ConfigDO).where(ConfigDO.config_key == "test.transaction.key")
        )
        saved_config = result.scalar_one_or_none()
        
        assert saved_config is not None
        assert saved_config.config_value == "test_value"
        
        # 清理
        await db_session.delete(saved_config)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session: AsyncSession):
        """
        测试事务回滚
        """
        config_key = "test.rollback.key"
        
        try:
            async with TransactionManager(db_session).transaction():
                config = ConfigDO(
                    config_name="test_rollback",
                    config_key=config_key,
                    config_value="should_rollback",
                    config_type="Y",
                    create_by="test"
                )
                db_session.add(config)
                await db_session.flush()
                
                # 故意抛出异常触发回滚
                raise ValueError("Test rollback")
        except ValueError:
            pass
        
        # 验证数据已回滚
        result = await db_session.execute(
            select(ConfigDO).where(ConfigDO.config_key == config_key)
        )
        saved_config = result.scalar_one_or_none()
        
        assert saved_config is None

    @pytest.mark.asyncio
    async def test_nested_transaction_savepoint(self, db_session: AsyncSession):
        """
        测试嵌套事务（Savepoint）
        
        外层事务提交，内层事务回滚
        """
        outer_key = "test.outer.key"
        inner_key = "test.inner.key"
        
        async with TransactionManager(db_session).transaction():
            # 外层事务
            outer_config = ConfigDO(
                config_name="outer",
                config_key=outer_key,
                config_value="outer_value",
                config_type="Y",
                create_by="test"
            )
            db_session.add(outer_config)
            await db_session.flush()
            
            # 内层事务（Savepoint）
            try:
                async with TransactionManager(db_session).transaction(savepoint=True):
                    inner_config = ConfigDO(
                        config_name="inner",
                        config_key=inner_key,
                        config_value="inner_value",
                        config_type="Y",
                        create_by="test"
                    )
                    db_session.add(inner_config)
                    await db_session.flush()
                    
                    # 内层事务回滚
                    raise ValueError("Inner transaction rollback")
            except ValueError:
                pass
        
        # 验证外层事务已提交
        result = await db_session.execute(
            select(ConfigDO).where(ConfigDO.config_key == outer_key)
        )
        outer_saved = result.scalar_one_or_none()
        assert outer_saved is not None
        
        # 验证内层事务已回滚
        result = await db_session.execute(
            select(ConfigDO).where(ConfigDO.config_key == inner_key)
        )
        inner_saved = result.scalar_one_or_none()
        assert inner_saved is None
        
        # 清理
        await db_session.delete(outer_saved)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_transaction_timeout(self, db_session: AsyncSession):
        """
        测试事务超时
        """
        with pytest.raises(asyncio.TimeoutError):
            async with TransactionManager(db_session).transaction(timeout=0.1):
                # 模拟长时间操作
                await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_deadlock_retry(self, db_session: AsyncSession):
        """
        测试死锁重试机制
        """
        attempt_count = 0
        
        async def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:
                # 模拟死锁错误
                raise Exception("Deadlock found when trying to get lock")
            
            # 第三次尝试成功
            return "success"
        
        result = await TransactionManager.retry_on_deadlock(
            failing_operation,
            max_retries=3,
            backoff_factor=0.01  # 快速重试用于测试
        )
        
        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_deadlock_retry_max_attempts(self, db_session: AsyncSession):
        """
        测试死锁重试达到最大次数
        """
        async def always_failing_operation():
            raise Exception("Deadlock found when trying to get lock")
        
        with pytest.raises(Exception, match="Deadlock"):
            await TransactionManager.retry_on_deadlock(
                always_failing_operation,
                max_retries=3,
                backoff_factor=0.01
            )


class TestTransactionalDecorator:
    """@transactional() 装饰器测试套件"""

    @pytest.mark.asyncio
    async def test_decorator_basic_commit(self, db_session: AsyncSession):
        """
        测试装饰器基本提交
        """
        @transactional()
        async def create_config(db: AsyncSession, key: str, value: str):
            config = ConfigDO(
                config_name="decorator_test",
                config_key=key,
                config_value=value,
                config_type="Y",
                create_by="test"
            )
            db.add(config)
            await db.flush()
            return config
        
        config_key = "test.decorator.key"
        await create_config(db_session, config_key, "decorator_value")
        
        # 验证数据已提交
        result = await db_session.execute(
            select(ConfigDO).where(ConfigDO.config_key == config_key)
        )
        saved_config = result.scalar_one_or_none()
        
        assert saved_config is not None
        assert saved_config.config_value == "decorator_value"
        
        # 清理
        await db_session.delete(saved_config)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_decorator_rollback(self, db_session: AsyncSession):
        """
        测试装饰器回滚
        """
        @transactional()
        async def create_and_fail(db: AsyncSession, key: str):
            config = ConfigDO(
                config_name="decorator_rollback",
                config_key=key,
                config_value="should_rollback",
                config_type="Y",
                create_by="test"
            )
            db.add(config)
            await db.flush()
            raise ValueError("Test rollback")
        
        config_key = "test.decorator.rollback"
        
        with pytest.raises(ValueError):
            await create_and_fail(db_session, config_key)
        
        # 验证数据已回滚
        result = await db_session.execute(
            select(ConfigDO).where(ConfigDO.config_key == config_key)
        )
        saved_config = result.scalar_one_or_none()
        
        assert saved_config is None

    @pytest.mark.asyncio
    async def test_decorator_with_retry(self, db_session: AsyncSession):
        """
        测试装饰器的死锁重试功能
        """
        attempt_count = 0
        
        @transactional(retry_on_deadlock=True, max_retries=3)
        async def operation_with_retry(db: AsyncSession):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 2:
                raise Exception("Deadlock found when trying to get lock")
            
            return "success"
        
        result = await operation_with_retry(db_session)
        
        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_decorator_with_timeout(self, db_session: AsyncSession):
        """
        测试装饰器的超时功能
        """
        @transactional(timeout=0.1)
        async def slow_operation(db: AsyncSession):
            await asyncio.sleep(0.5)
        
        with pytest.raises(asyncio.TimeoutError):
            await slow_operation(db_session)

    @pytest.mark.asyncio
    async def test_decorator_with_isolation_level(self, db_session: AsyncSession):
        """
        测试装饰器的隔离级别设置
        """
        @transactional(isolation_level=TransactionIsolationLevel.SERIALIZABLE)
        async def serializable_operation(db: AsyncSession, key: str):
            config = ConfigDO(
                config_name="isolation_test",
                config_key=key,
                config_value="serializable",
                config_type="Y",
                create_by="test"
            )
            db.add(config)
            await db.flush()
            return config
        
        config_key = "test.isolation.key"
        await serializable_operation(db_session, config_key)
        
        # 验证数据已提交
        result = await db_session.execute(
            select(ConfigDO).where(ConfigDO.config_key == config_key)
        )
        saved_config = result.scalar_one_or_none()
        
        assert saved_config is not None
        
        # 清理
        await db_session.delete(saved_config)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_decorator_without_db_session(self):
        """
        测试装饰器在没有 AsyncSession 参数时的行为
        """
        @transactional()
        async def operation_without_db(value: str):
            return f"processed: {value}"
        
        # 应该正常执行，只是没有事务
        result = await operation_without_db("test")
        assert result == "processed: test"


class TestTransactionEdgeCases:
    """事务边界测试"""

    @pytest.mark.asyncio
    async def test_multiple_transactions_sequential(self, db_session: AsyncSession):
        """
        测试顺序执行多个事务
        """
        # 第一个事务
        async with TransactionManager(db_session).transaction():
            config1 = ConfigDO(
                config_name="seq1",
                config_key="test.seq.1",
                config_value="value1",
                config_type="Y",
                create_by="test"
            )
            db_session.add(config1)
            await db_session.flush()
        
        # 第二个事务
        async with TransactionManager(db_session).transaction():
            config2 = ConfigDO(
                config_name="seq2",
                config_key="test.seq.2",
                config_value="value2",
                config_type="Y",
                create_by="test"
            )
            db_session.add(config2)
            await db_session.flush()
        
        # 验证两个事务都已提交
        result = await db_session.execute(
            select(ConfigDO).where(
                ConfigDO.config_key.in_(["test.seq.1", "test.seq.2"])
            )
        )
        configs = result.scalars().all()
        
        assert len(configs) == 2
        
        # 清理
        for config in configs:
            await db_session.delete(config)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_transaction_with_query(self, db_session: AsyncSession):
        """
        测试事务中的查询操作
        """
        async with TransactionManager(db_session).transaction():
            # 在事务中查询
            result = await db_session.execute(
                select(ConfigDO).limit(1)
            )
            config = result.scalar_one_or_none()
            
            # 应该能够正常查询
            assert config is None or isinstance(config, ConfigDO)

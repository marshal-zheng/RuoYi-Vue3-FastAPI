import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from config.database import async_engine, AsyncSessionLocal, Base
import events.models as _event_models  # noqa: F401
from utils.log_util import logger

_TEST_ENGINE = None
_TEST_SESSIONMAKER = None


def _is_test_env() -> bool:
    return 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST') is not None


def _get_test_sessionmaker():
    global _TEST_ENGINE, _TEST_SESSIONMAKER
    if _TEST_SESSIONMAKER is None:
        _TEST_ENGINE = create_async_engine(
            'sqlite+aiosqlite:///:memory:',
            echo=False,
            poolclass=StaticPool,
            connect_args={'check_same_thread': False},
        )
        _TEST_SESSIONMAKER = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_TEST_ENGINE,
            expire_on_commit=False,
        )
    return _TEST_SESSIONMAKER


def _get_test_engine():
    _get_test_sessionmaker()
    return _TEST_ENGINE


async def get_db():
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接

    :return:
    """
    session_factory = _get_test_sessionmaker() if _is_test_env() else AsyncSessionLocal
    async with session_factory() as current_db:
        try:
            yield current_db
            # 请求成功完成后提交事务
            if current_db.in_transaction():
                await current_db.commit()
        except Exception:
            # 发生异常时回滚事务
            if current_db.in_transaction():
                await current_db.rollback()
            raise


async def init_create_table():
    """
    应用启动时初始化数据库连接。
    测试环境保留 create_all 以兼容内存 SQLite；
    非测试环境只做连接探活，schema 变更必须由显式工作流处理。

    :return:
    """
    if _is_test_env():
        logger.info('初始化测试环境数据库结构...')
        engine = _get_test_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info('测试环境数据库结构初始化完成')
        return

    logger.info('初始化数据库连接（非测试环境不执行自动建表）...')
    async with async_engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
    logger.info('数据库连接成功')

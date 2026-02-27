import asyncio
import time
from dataclasses import dataclass

from utils.log_util import logger


@dataclass
class TestResult:
    success: bool
    message: str
    latency_ms: int


async def test_connection(
    type: str,
    host: str,
    port: int,
    username: str = '',
    password: str = '',
    database_name: str = '',
    extra_config: dict = None,
) -> TestResult:
    start = time.monotonic()
    try:
        match type:
            case 'mysql':
                return await asyncio.wait_for(_test_mysql(host, port, username, password, database_name), timeout=5)
            case 'postgresql':
                return await asyncio.wait_for(
                    _test_postgresql(host, port, username, password, database_name), timeout=5
                )
            case 'mongodb':
                return await asyncio.wait_for(
                    _test_mongodb(host, port, username, password, database_name, extra_config or {}), timeout=5
                )
            case 'minio':
                return await asyncio.wait_for(
                    _test_minio(host, port, username, password, database_name, extra_config or {}), timeout=5
                )
            case _:
                return TestResult(success=False, message=f'不支持的数据源类型: {type}', latency_ms=0)
    except asyncio.TimeoutError:
        elapsed = int((time.monotonic() - start) * 1000)
        return TestResult(success=False, message='连接超时（5秒）', latency_ms=elapsed)
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        logger.error(f'连通性测试异常: {e}')
        return TestResult(success=False, message=str(e), latency_ms=elapsed)


async def _test_mysql(host, port, username, password, database_name) -> TestResult:
    start = time.monotonic()
    import aiomysql

    conn = await aiomysql.connect(host=host, port=port, user=username, password=password, db=database_name or '')
    try:
        async with conn.cursor() as cur:
            await cur.execute('SELECT 1')
        elapsed = int((time.monotonic() - start) * 1000)
        return TestResult(success=True, message='连接成功', latency_ms=elapsed)
    finally:
        conn.close()


async def _test_postgresql(host, port, username, password, database_name) -> TestResult:
    start = time.monotonic()
    import asyncpg

    conn = await asyncpg.connect(
        host=host, port=port, user=username, password=password, database=database_name or 'postgres'
    )
    try:
        await conn.execute('SELECT 1')
        elapsed = int((time.monotonic() - start) * 1000)
        return TestResult(success=True, message='连接成功', latency_ms=elapsed)
    finally:
        await conn.close()


async def _test_mongodb(host, port, username, password, database_name, extra_config) -> TestResult:
    start = time.monotonic()
    from motor.motor_asyncio import AsyncIOMotorClient

    auth_source = extra_config.get('auth_source', 'admin')
    if username:
        uri = f'mongodb://{username}:{password}@{host}:{port}/{database_name or "admin"}?authSource={auth_source}'
    else:
        uri = f'mongodb://{host}:{port}'
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    try:
        await client.admin.command('ping')
        elapsed = int((time.monotonic() - start) * 1000)
        return TestResult(success=True, message='连接成功', latency_ms=elapsed)
    finally:
        client.close()


async def _test_minio(host, port, username, password, database_name, extra_config) -> TestResult:
    start = time.monotonic()
    from miniopy_async import Minio

    use_ssl = extra_config.get('use_ssl', False)
    client = Minio(f'{host}:{port}', access_key=username, secret_key=password, secure=use_ssl)
    if database_name:
        await client.bucket_exists(database_name)
    else:
        await client.list_buckets()
    elapsed = int((time.monotonic() - start) * 1000)
    return TestResult(success=True, message='连接成功', latency_ms=elapsed)

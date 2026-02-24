from redis import asyncio as aioredis
from redis.exceptions import AuthenticationError, TimeoutError, RedisError

from config.database import AsyncSessionLocal
from config.env import RedisConfig
from module_admin.repository import ConfigRepository, DictDataRepository, DictTypeRepository
from modules.system.application.services.config_service import ConfigService
from modules.system.application.services.dict_data_service import DictDataService
from ports import IRedisClient
from utils.log_util import logger


class RedisUtil:
    """
    Redis相关方法
    """

    @classmethod
    async def create_redis_pool(cls) -> IRedisClient:
        """
        应用启动时初始化redis连接

        :return: Redis连接对象
        """
        logger.info('开始连接redis...')
        redis = await aioredis.from_url(
            url=f'redis://{RedisConfig.redis_host}',
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username,
            password=RedisConfig.redis_password,
            db=RedisConfig.redis_database,
            encoding='utf-8',
            decode_responses=True,
        )
        try:
            connection = await redis.ping()
            if connection:
                logger.info('redis连接成功')
            else:
                logger.error('redis连接失败')
        except AuthenticationError as e:
            logger.error(f'redis用户名或密码错误，详细错误信息：{e}')
        except TimeoutError as e:
            logger.error(f'redis连接超时，详细错误信息：{e}')
        except RedisError as e:
            logger.error(f'redis连接错误，详细错误信息：{e}')
        return redis

    @classmethod
    async def close_redis_pool(cls, app):
        """
        应用关闭时关闭redis连接

        :param app: fastapi对象
        :return:
        """
        await app.state.redis.close()
        logger.info('关闭redis连接成功')

    @classmethod
    async def init_sys_dict(cls, redis: IRedisClient):
        """
        应用启动时缓存字典表

        :param redis: redis对象
        :return:
        """
        async with AsyncSessionLocal() as session:
            await DictDataService(
                dict_type_repo=DictTypeRepository(session),
                dict_data_repo=DictDataRepository(session),
            ).init_cache_sys_dict_services(redis)

    @classmethod
    async def init_sys_config(cls, redis: IRedisClient):
        """
        应用启动时缓存参数配置表

        :param redis: redis对象
        :return:
        """
        async with AsyncSessionLocal() as session:
            await ConfigService(config_repo=ConfigRepository(session), query_db=session).init_cache_sys_config_services(redis)

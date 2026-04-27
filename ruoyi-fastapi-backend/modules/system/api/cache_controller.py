from fastapi import APIRouter, Depends, Request
from typing import List
from container.dependencies import service_provider
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.cache_vo import CacheInfoModel, CacheMonitorModel
from modules.system.application.services.cache_service import CacheService
from modules.identity.ports import get_current_user
from utils.log_util import logger
from utils.response_util import ResponseUtil


cacheController = APIRouter(prefix='/monitor/cache', dependencies=[Depends(get_current_user)])


@cacheController.get(
    '', response_model=CacheMonitorModel, dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))]
)
async def get_monitor_cache_info(
    request: Request,
    cache_service: CacheService = Depends(service_provider('cache_service', require_session=False)),
):
    # 获取全量数据
    cache_info_query_result = await cache_service.get_cache_monitor_statistical_info_services(request)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(cache_info_query_result)


@cacheController.get(
    '/getNames',
    response_model=List[CacheInfoModel],
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def get_monitor_cache_name(
    request: Request,
    cache_service: CacheService = Depends(service_provider('cache_service', require_session=False)),
):
    # 获取全量数据
    cache_name_list_result = await cache_service.get_cache_monitor_cache_name_services()
    logger.info('获取成功')

    return ResponseUtil.ok_resource(cache_name_list_result)


@cacheController.get(
    '/getKeys/{cache_name}',
    response_model=List[str],
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def get_monitor_cache_key(
    request: Request,
    cache_name: str,
    cache_service: CacheService = Depends(service_provider('cache_service', require_session=False)),
):
    # 获取全量数据
    cache_key_list_result = await cache_service.get_cache_monitor_cache_key_services(request, cache_name)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(cache_key_list_result)


@cacheController.get(
    '/getValue/{cache_name}/{cache_key}',
    response_model=CacheInfoModel,
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def get_monitor_cache_value(
    request: Request,
    cache_name: str,
    cache_key: str,
    cache_service: CacheService = Depends(service_provider('cache_service', require_session=False)),
):
    # 获取全量数据
    cache_value_list_result = await cache_service.get_cache_monitor_cache_value_services(request, cache_name, cache_key)
    logger.info('获取成功')

    return ResponseUtil.ok_resource(cache_value_list_result)


@cacheController.delete(
    '/clearCacheName/{cache_name}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))]
)
async def clear_monitor_cache_name(
    request: Request,
    cache_name: str,
    cache_service: CacheService = Depends(service_provider('cache_service', require_session=False)),
):
    clear_cache_name_result = await cache_service.clear_cache_monitor_cache_name_services(request, cache_name)
    logger.info(clear_cache_name_result.message)

    return ResponseUtil.no_content()


@cacheController.delete(
    '/clearCacheKey/{cache_key}', dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))]
)
async def clear_monitor_cache_key(
    request: Request,
    cache_key: str,
    cache_service: CacheService = Depends(service_provider('cache_service', require_session=False)),
):
    clear_cache_key_result = await cache_service.clear_cache_monitor_cache_key_services(request, cache_key)
    logger.info(clear_cache_key_result.message)

    return ResponseUtil.no_content()


@cacheController.delete('/clearCacheAll', dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def clear_monitor_cache_all(
    request: Request,
    cache_service: CacheService = Depends(service_provider('cache_service', require_session=False)),
):
    clear_cache_all_result = await cache_service.clear_cache_monitor_all_services(request)
    logger.info(clear_cache_all_result.message)

    return ResponseUtil.no_content()

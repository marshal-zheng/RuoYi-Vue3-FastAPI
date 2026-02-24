from fastapi import APIRouter, Depends, Request

from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from modules.identity.ports import get_current_user
from utils.log_util import logger
from utils.response_util import ResponseUtil


resilienceController = APIRouter(dependencies=[Depends(get_current_user)])


@resilienceController.get(
    '/resilience/circuit-breakers',
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def get_resilience_circuit_breakers(request: Request):
    runtime = getattr(request.app.state, 'resilience_runtime', None)
    if runtime is None:
        return ResponseUtil.success(message='resilience runtime not initialized', http_status=503)

    circuit_states = await runtime.circuit_registry.list_snapshots()
    logger.info('获取熔断器状态成功')
    return ResponseUtil.success(data=circuit_states)


@resilienceController.get('/saga/instances', dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))])
async def get_saga_instances(request: Request, limit: int = 100):
    runtime = getattr(request.app.state, 'resilience_runtime', None)
    if runtime is None:
        return ResponseUtil.success(message='resilience runtime not initialized', http_status=503)

    instances = await runtime.saga_engine.list_instances(limit=max(limit, 1))
    logger.info('获取 Saga 实例成功')
    return ResponseUtil.success(data=instances)


@resilienceController.post(
    '/saga/{saga_id}/compensate',
    dependencies=[Depends(CheckUserInterfaceAuth('monitor:cache:list'))],
)
async def compensate_saga_instance(request: Request, saga_id: str):
    runtime = getattr(request.app.state, 'resilience_runtime', None)
    if runtime is None:
        return ResponseUtil.success(message='resilience runtime not initialized', http_status=503)

    try:
        instance = await runtime.saga_engine.compensate(saga_id)
    except ValueError as exc:
        return ResponseUtil.success(message=str(exc), http_status=404)

    logger.info(f'Saga 手动补偿成功: {saga_id}')
    return ResponseUtil.success(data=instance, message='补偿请求已提交')

"""
仿真控制器
处理仿真相关的HTTP请求和WebSocket连接
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json
import os
import socket
from typing import Dict, Set
from config.get_db import get_db
from config.enums import BusinessType
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.simulation_vo import (
    CreateSimulationSessionModel,
    SimulationExportModel
)
from module_admin.service.simulation_service import SimulationService, get_simulation_service
from modules.identity.application.services.login_service import LoginService
from module_admin.service.data_injection_strategy import STRATEGY_DEFINITIONS
from utils.log_util import logger
from utils.response_util import ResponseUtil


simulationController = APIRouter(
    prefix='/simulation'
)


# WebSocket连接管理
class ConnectionManager:
    """WebSocket connection manager with session-level producer tasks."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._producer_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            self.active_connections[session_id].add(websocket)
    
    async def ensure_session_producer(self, session_id: str, simulation_service: SimulationService):
        async with self._lock:
            task = self._producer_tasks.get(session_id)
            if task and not task.done():
                return
            task = asyncio.create_task(push_simulation_data(session_id, simulation_service))
            self._producer_tasks[session_id] = task
            task.add_done_callback(lambda done_task, sid=session_id: self._cleanup_producer_task(sid, done_task))

    def _cleanup_producer_task(self, session_id: str, task: asyncio.Task):
        if not task.cancelled():
            try:
                exc = task.exception()
            except Exception:
                exc = None
            if exc:
                logger.error(f'会话级推送任务异常退出: {session_id}, error={exc}')
        current = self._producer_tasks.get(session_id)
        if current is task:
            self._producer_tasks.pop(session_id, None)

    async def disconnect(self, websocket: WebSocket, session_id: str):
        should_stop_producer = False
        async with self._lock:
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    should_stop_producer = True
        if should_stop_producer:
            await self.stop_session_producer(session_id)

    async def has_connections(self, session_id: str) -> bool:
        async with self._lock:
            return bool(self.active_connections.get(session_id))

    async def stop_session_producer(self, session_id: str):
        task = None
        async with self._lock:
            task = self._producer_tasks.pop(session_id, None)
        if task and not task.done():
            current_task = asyncio.current_task()
            if current_task is task:
                task.cancel()
                return
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    async def broadcast(self, session_id: str, message: dict):
        async with self._lock:
            targets = list(self.active_connections.get(session_id, set()))
        if not targets:
            return

        disconnected = []
        for connection in targets:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            await self.disconnect(connection, session_id)


manager = ConnectionManager()
SESSION_PRODUCER_OWNER_TTL_SECONDS = 10
SESSION_PRODUCER_WORKER_ID = f'{socket.gethostname()}:{os.getpid()}'


@simulationController.get(
    '/strategies',
    dependencies=[
        Depends(LoginService.get_current_user)
    ]
)
async def get_fill_strategies(request: Request):
    """
    获取可用的数据填充策略列表
    
    返回:
        策略列表，包含名称、描述、图标、参数配置等信息
    """
    strategies = []
    for key, definition in STRATEGY_DEFINITIONS.items():
        strategies.append({
            'value': key,
            'label': definition['name'],
            'description': definition['description'],
            'icon': definition['icon'],
            'params': definition['params']
        })
    return ResponseUtil.success(data=strategies)


@simulationController.post(
    '/sessions',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-创建会话', business_type=BusinessType.INSERT)
async def create_simulation_session(
    request: Request,
    create_request: CreateSimulationSessionModel,
    simulation_service: SimulationService = Depends(get_simulation_service),
    current_user = Depends(LoginService.get_current_user)
):
    """
    创建仿真会话
    
    参数:
        create_request: 创建请求（projectId, versionId）
        
    返回:
        会话信息（sessionId, status）
    """
    result = await simulation_service.create_session(
        create_request,
        operator=current_user.user.user_name if current_user.user else 'system',
    )
    logger.info(f'创建仿真会话成功: {result}')
    
    return ResponseUtil.success(data=result)


@simulationController.post(
    '/sessions/{session_id}/start',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-启动仿真', business_type=BusinessType.UPDATE)
async def start_simulation_session(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    启动仿真会话
    
    参数:
        session_id: 会话ID
        
    返回:
        操作结果
    """
    result = await simulation_service.start_session(session_id)
    logger.info(f'启动仿真会话成功: {session_id}')
    
    return ResponseUtil.success(data=result.model_dump())


@simulationController.post(
    '/sessions/{session_id}/stop',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-停止仿真', business_type=BusinessType.UPDATE)
async def stop_simulation_session(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    停止仿真会话
    
    参数:
        session_id: 会话ID
        
    返回:
        操作结果
    """
    result = await simulation_service.stop_session(session_id)
    logger.info(f'停止仿真会话成功: {session_id}')
    
    return ResponseUtil.success(data=result.model_dump())


@simulationController.get(
    '/sessions/{session_id}/status',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def get_simulation_status(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    获取仿真会话状态
    
    参数:
        session_id: 会话ID
        
    返回:
        状态信息
    """
    status = await simulation_service.get_shared_session_status(session_id)
    return ResponseUtil.success(data=status)


@simulationController.get(
    '/sessions/{session_id}/messages',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def get_simulation_messages(
    request: Request,
    session_id: str,
    limit: int = 100,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    获取仿真报文数据
    
    参数:
        session_id: 会话ID
        limit: 限制数量
        
    返回:
        报文列表
    """
    messages = await simulation_service.read_messages_with_fallback(session_id, limit)
    return ResponseUtil.success(data=messages)


@simulationController.get(
    '/sessions/{session_id}/bandwidth',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def get_simulation_bandwidth(
    request: Request,
    session_id: str,
    port_id: str = None,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    获取仿真带宽数据
    
    参数:
        session_id: 会话ID
        port_id: 端口ID（可选）
        
    返回:
        带宽数据列表
    """
    bandwidth_data = await simulation_service.read_bandwidth_with_fallback(
        session_id,
        port_id=port_id,
        limit=400,
    )
    return ResponseUtil.success(data=bandwidth_data)


@simulationController.get(
    '/sessions/{session_id}/alarms',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def get_simulation_alarms(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    获取仿真告警数据
    
    参数:
        session_id: 会话ID
        
    返回:
        告警列表
    """
    alarms = await simulation_service.read_alarms_with_fallback(session_id, 200)
    return ResponseUtil.success(data=alarms)


@simulationController.post(
    '/sessions/{session_id}/export',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-导出数据', business_type=BusinessType.EXPORT)
async def export_simulation_data(
    request: Request,
    session_id: str,
    export_request: SimulationExportModel,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    导出仿真数据
    
    参数:
        session_id: 会话ID
        export_request: 导出请求（format, dataType）
        
    返回:
        导出数据
    """
    export_request.session_id = session_id
    result = await simulation_service.export_simulation_data(export_request)
    logger.info(f'导出仿真数据成功: {session_id}')
    
    return ResponseUtil.success(data=result)


# ==================== 新增：仿真控制增强 ====================

@simulationController.post(
    '/sessions/{session_id}/pause',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-暂停仿真', business_type=BusinessType.UPDATE)
async def pause_simulation_session(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """暂停仿真会话"""
    result = await simulation_service.pause_session(session_id)
    logger.info(f'暂停仿真会话: {session_id}')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.post(
    '/sessions/{session_id}/resume',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-继续仿真', business_type=BusinessType.UPDATE)
async def resume_simulation_session(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """继续仿真会话"""
    result = await simulation_service.resume_session(session_id)
    logger.info(f'继续仿真会话: {session_id}')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.post(
    '/sessions/{session_id}/speed',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def set_simulation_speed(
    request: Request,
    session_id: str,
    body: dict,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """设置仿真速度（0.5x-4x）"""
    speed = simulation_service.resolve_speed_input(body)
    result = await simulation_service.set_speed(session_id, speed)
    logger.info(f'设置仿真速度: {session_id} -> {speed}x')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.post(
    '/sessions/{session_id}/step',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def step_simulation(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """单步执行"""
    result = await simulation_service.step_once(session_id)
    logger.info(f'单步执行: {session_id}')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.post(
    '/sessions/{session_id}/duration',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def set_simulation_duration(
    request: Request,
    session_id: str,
    duration: float = None,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """设置仿真时长（秒），不传则无限制"""
    normalized_duration = simulation_service.resolve_duration_input(duration=duration, payload=None)
    result = await simulation_service.set_duration(session_id, normalized_duration)
    return ResponseUtil.success(data=result.model_dump())


# ==================== 新增：故障注入 ====================

@simulationController.post(
    '/sessions/{session_id}/faults',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-注入故障', business_type=BusinessType.INSERT)
async def inject_fault(
    request: Request,
    session_id: str,
    fault_type: str = None,
    target_id: str = None,
    payload: dict = Body(None),
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    注入故障

    参数:
        fault_type: disconnect | error_frame | device_failure | packet_loss | delay
        target_id: 链路ID或节点ID
        params: {loss_rate, delay_ms, count 等}
    """
    injection = simulation_service.apply_fault_injection(
        session_id=session_id,
        fault_type=fault_type,
        target_id=target_id,
        payload=payload,
        require_session_id=False,
    )
    logger.info(
        f"注入故障: {injection['session_id']} -> "
        f"{injection['fault_type']}@{injection['target_id']}"
    )
    return ResponseUtil.success(data=injection['result'])


@simulationController.delete(
    '/sessions/{session_id}/faults/{fault_id}',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-清除故障', business_type=BusinessType.DELETE)
async def clear_fault(
    request: Request,
    session_id: str,
    fault_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """清除故障"""
    result = simulation_service.clear_fault(session_id, fault_id)
    logger.info(f'清除故障: {session_id} -> {fault_id}')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.delete(
    '/sessions/{session_id}/faults',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-清除全部故障', business_type=BusinessType.DELETE)
async def clear_all_faults(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """清除指定会话的所有故障"""
    result = simulation_service.clear_all_faults(session_id)
    logger.info(f'清除全部故障: {session_id}')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.get(
    '/sessions/{session_id}/faults',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def list_faults(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """获取故障列表"""
    faults = simulation_service.list_faults(session_id)
    return ResponseUtil.success(data=faults)


# ==================== 新增：统一故障接口（无 session 路径） ====================


@simulationController.post(
    '/faults',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def upsert_fault(
    request: Request,
    payload: dict = Body(...),
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    新增/更新故障规则
    """
    injection = simulation_service.apply_fault_injection(
        payload=payload,
        require_session_id=True,
    )
    logger.info(
        f"注入故障: {injection['session_id']} -> "
        f"{injection['fault_type']}@{injection['target_id']}"
    )
    return ResponseUtil.success(data=injection['result'])


@simulationController.get(
    '/faults',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def query_faults(
    session_id: str = Query(..., alias="sessionId"),
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """查询会话故障"""
    normalized_session_id = simulation_service.require_session_id(session_id)
    faults = simulation_service.list_faults(normalized_session_id)
    return ResponseUtil.success(data=faults)


@simulationController.delete(
    '/faults/{fault_id}',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def delete_fault(
    fault_id: str,
    session_id: str = Query(..., alias="sessionId"),
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """删除会话故障"""
    normalized_session_id = simulation_service.require_session_id(session_id)
    result = simulation_service.clear_fault(normalized_session_id, fault_id)
    logger.info(f'清除故障: {normalized_session_id} -> {fault_id}')
    return ResponseUtil.success(data=result.model_dump())


# ==================== 新增：事件触发 ====================

@simulationController.post(
    '/sessions/{session_id}/events',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-添加事件', business_type=BusinessType.INSERT)
async def add_event(
    request: Request,
    session_id: str,
    event: dict,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    添加事件

    参数:
        event: {
            name: 事件名称,
            condition: {type, value},
            action: {type, params}
        }
        
    动作类型:
        - send_command: 发送指令（A设备给B设备发送指令，如自检、上电等）
        - send_message: 发送报文
        - inject_fault: 注入故障
        - pause: 暂停仿真
        - log: 记录日志
    """
    result = simulation_service.add_event(session_id, event)
    logger.info(f'添加事件: {session_id}')
    return ResponseUtil.success(data=result)


@simulationController.put(
    '/sessions/{session_id}/events/{event_id}',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-更新事件', business_type=BusinessType.UPDATE)
async def update_event(
    request: Request,
    session_id: str,
    event_id: str,
    updates: dict,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    更新事件配置

    参数:
        session_id: 会话ID
        event_id: 事件ID
        updates: 更新内容
    """
    result = simulation_service.update_event(session_id, event_id, updates)
    logger.info(f'更新事件: {session_id} -> {event_id}')
    return ResponseUtil.success(data=result)


@simulationController.post(
    '/sessions/{session_id}/events/{event_id}/trigger',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-触发事件', business_type=BusinessType.UPDATE)
async def trigger_event(
    request: Request,
    session_id: str,
    event_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """
    手动触发事件
    
    用于人为触发预设的事件动作，如：
    - A设备给B设备发送自检指令
    - A设备给B设备发送上电指令
    - A设备给B设备发送报文
    - 注入故障
    - 暂停仿真
    
    参数:
        session_id: 会话ID
        event_id: 事件ID
        
    返回:
        触发结果，包含动作执行信息
    """
    result = simulation_service.trigger_event(session_id, event_id)
    logger.info(f'触发事件: {session_id} -> {event_id}')
    return ResponseUtil.success(data=result)


@simulationController.post(
    '/sessions/{session_id}/events/{event_id}/reset',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def reset_event(
    request: Request,
    session_id: str,
    event_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """重置事件状态为待触发"""
    result = simulation_service.reset_event(session_id, event_id)
    logger.info(f'重置事件: {session_id} -> {event_id}')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.delete(
    '/sessions/{session_id}/events/{event_id}',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
@Log(title='仿真管理-删除事件', business_type=BusinessType.DELETE)
async def remove_event(
    request: Request,
    session_id: str,
    event_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """删除事件"""
    result = simulation_service.remove_event(session_id, event_id)
    logger.info(f'删除事件: {session_id} -> {event_id}')
    return ResponseUtil.success(data=result.model_dump())


@simulationController.get(
    '/sessions/{session_id}/events',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def list_events(
    request: Request,
    session_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """获取事件列表"""
    events = simulation_service.list_events(session_id)
    return ResponseUtil.success(data=events)


# ==================== 新增：拓扑验证 ====================

@simulationController.post(
    '/topology/validate',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def validate_topology(
    request: Request,
    topology_data: dict,
    simulation_service: SimulationService = Depends(get_simulation_service),
):
    """验证拓扑配置完整性"""
    result = simulation_service.validate_topology(topology_data)
    return ResponseUtil.success(data=result)


@simulationController.websocket('/sessions/{session_id}/ws')
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    query_db: AsyncSession = Depends(get_db)
):
    """
    WebSocket端点 - 实时推送仿真数据
    
    参数:
        session_id: 会话ID
        
    消息格式:
        {
            "type": "message" | "bandwidth" | "alarm" | "status",
            "data": {...}
        }
    """
    token = (
        websocket.query_params.get('token')
        or websocket.headers.get('Authorization')
        or websocket.cookies.get('Admin-Token')
    )

    try:
        await LoginService.get_current_user_from_token(websocket, token, query_db)
    except Exception as e:
        logger.warning(f'WebSocket认证失败: {str(e)}')
        await websocket.close(code=1008, reason='Unauthorized')
        return

    container = getattr(websocket.app.state, 'container', None)
    if container is None:
        logger.error('WebSocket容器未初始化，拒绝连接')
        await websocket.close(code=1011, reason='Container unavailable')
        return
    simulation_service: SimulationService = container.simulation_service(query_db)

    await manager.connect(websocket, session_id)
    await manager.ensure_session_producer(session_id, simulation_service)
    logger.info(f'WebSocket连接建立: {session_id}')

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f'WebSocket消息处理错误: {str(e)}')
                break
    except Exception as e:
        logger.error(f'WebSocket错误: {str(e)}')
    finally:
        await manager.disconnect(websocket, session_id)
        logger.info(f'WebSocket连接断开: {session_id}')


async def push_simulation_data(session_id: str, simulation_service: SimulationService):
    """
    推送仿真数据到WebSocket客户端。
    
    参数:
        session_id: 会话ID

    说明:
        具体推送编排逻辑由 SimulationService 统一管理，controller 仅负责转调。
    """
    await simulation_service.stream_session_updates(
        session_id,
        has_connections=manager.has_connections,
        broadcast=manager.broadcast,
        worker_id=SESSION_PRODUCER_WORKER_ID,
        owner_ttl_seconds=SESSION_PRODUCER_OWNER_TTL_SECONDS,
    )

"""
仿真控制器
处理仿真相关的HTTP请求和WebSocket连接
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request, Body, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json
from typing import Dict, Set
from config.get_db import get_db
from config.enums import BusinessType
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.simulation_vo import (
    CreateSimulationSessionModel,
    SimulationQueryModel,
    SimulationExportModel
)
from module_admin.service.simulation_service import SimulationService
from module_admin.service.login_service import LoginService
from module_admin.service.data_injection_strategy import STRATEGY_DEFINITIONS
from utils.log_util import logger
from utils.response_util import ResponseUtil


simulationController = APIRouter(
    prefix='/simulation'
)


# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """连接WebSocket"""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        """断开WebSocket"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def broadcast(self, session_id: str, message: dict):
        """广播消息到所有连接"""
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.disconnect(conn, session_id)


manager = ConnectionManager()


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
    try:
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
    except Exception as e:
        logger.error(f'获取填充策略列表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


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
    query_db: AsyncSession = Depends(get_db),
    current_user = Depends(LoginService.get_current_user)
):
    """
    创建仿真会话
    
    参数:
        create_request: 创建请求（projectId, versionId）
        
    返回:
        会话信息（sessionId, status）
    """
    try:
        # 设置创建人（从CurrentUserModel对象获取用户名）
        create_request.create_by = current_user.user.user_name if current_user.user else 'system'
        
        result = await SimulationService.create_session(query_db, create_request)
        logger.info(f'创建仿真会话成功: {result}')
        
        return ResponseUtil.success(data=result)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f'创建仿真会话失败: {str(e)}\n{error_detail}')
        return ResponseUtil.error(msg=str(e) or '创建仿真会话失败，请检查数据库表是否存在')


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
    query_db: AsyncSession = Depends(get_db)
):
    """
    启动仿真会话
    
    参数:
        session_id: 会话ID
        
    返回:
        操作结果
    """
    try:
        result = await SimulationService.start_session(query_db, session_id)
        logger.info(f'启动仿真会话成功: {session_id}')
        
        return ResponseUtil.success(data=result.model_dump())
    except Exception as e:
        logger.error(f'启动仿真会话失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


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
    query_db: AsyncSession = Depends(get_db)
):
    """
    停止仿真会话
    
    参数:
        session_id: 会话ID
        
    返回:
        操作结果
    """
    try:
        result = await SimulationService.stop_session(query_db, session_id)
        logger.info(f'停止仿真会话成功: {session_id}')
        
        return ResponseUtil.success(data=result.model_dump())
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f'停止仿真会话失败: {str(e)}\n{error_detail}')
        return ResponseUtil.error(msg=str(e) or '停止仿真失败')


@simulationController.get(
    '/sessions/{session_id}/status',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def get_simulation_status(
    request: Request,
    session_id: str
):
    """
    获取仿真会话状态
    
    参数:
        session_id: 会话ID
        
    返回:
        状态信息
    """
    try:
        status = SimulationService.get_session_status(session_id)
        return ResponseUtil.success(data=status)
    except Exception as e:
        logger.error(f'获取仿真状态失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


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
    limit: int = 100
):
    """
    获取仿真报文数据
    
    参数:
        session_id: 会话ID
        limit: 限制数量
        
    返回:
        报文列表
    """
    try:
        messages = SimulationService.get_realtime_messages(session_id, limit)
        return ResponseUtil.success(data=messages)
    except Exception as e:
        logger.error(f'获取报文数据失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


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
    port_id: str = None
):
    """
    获取仿真带宽数据
    
    参数:
        session_id: 会话ID
        port_id: 端口ID（可选）
        
    返回:
        带宽数据列表
    """
    try:
        bandwidth_data = SimulationService.get_realtime_bandwidth(session_id, port_id)
        return ResponseUtil.success(data=bandwidth_data)
    except Exception as e:
        logger.error(f'获取带宽数据失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@simulationController.get(
    '/sessions/{session_id}/alarms',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def get_simulation_alarms(
    request: Request,
    session_id: str
):
    """
    获取仿真告警数据
    
    参数:
        session_id: 会话ID
        
    返回:
        告警列表
    """
    try:
        alarms = SimulationService.get_realtime_alarms(session_id)
        return ResponseUtil.success(data=alarms)
    except Exception as e:
        logger.error(f'获取告警数据失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


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
    query_db: AsyncSession = Depends(get_db)
):
    """
    导出仿真数据
    
    参数:
        session_id: 会话ID
        export_request: 导出请求（format, dataType）
        
    返回:
        导出数据
    """
    try:
        export_request.session_id = session_id
        result = await SimulationService.export_simulation_data(query_db, export_request)
        logger.info(f'导出仿真数据成功: {session_id}')
        
        return ResponseUtil.success(data=result)
    except Exception as e:
        logger.error(f'导出仿真数据失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


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
    query_db: AsyncSession = Depends(get_db)
):
    """暂停仿真会话"""
    result = await SimulationService.pause_session(query_db, session_id)
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
    query_db: AsyncSession = Depends(get_db)
):
    """继续仿真会话"""
    result = await SimulationService.resume_session(query_db, session_id)
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
    body: dict
):
    """设置仿真速度（0.5x-4x）"""
    speed = body.get('speed', 1.0)
    result = SimulationService.set_speed(session_id, speed)
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
    session_id: str
):
    """单步执行"""
    result = await SimulationService.step_once(session_id)
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
    duration: float = None
):
    """设置仿真时长（秒），不传则无限制"""
    result = SimulationService.set_duration(session_id, duration)
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
    payload: dict = Body(None)
):
    """
    注入故障

    参数:
        fault_type: disconnect | error_frame | device_failure | packet_loss | delay
        target_id: 链路ID或节点ID
        params: {loss_rate, delay_ms, count 等}
    """
    if payload:
        fault_type = payload.get('faultType') or payload.get('fault_type') or fault_type
        target_id = payload.get('targetId') or payload.get('target_id') or target_id
        params = payload.get('params') or payload
    else:
        params = None

    if not fault_type or target_id is None:
        return ResponseUtil.error(msg='faultType/targetId 不能为空')

    result = SimulationService.inject_fault(session_id, fault_type, target_id, params)
    logger.info(f'注入故障: {session_id} -> {fault_type}@{target_id}')
    return ResponseUtil.success(data=result)


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
    fault_id: str
):
    """清除故障"""
    result = SimulationService.clear_fault(session_id, fault_id)
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
    session_id: str
):
    """清除指定会话的所有故障"""
    result = SimulationService.clear_all_faults(session_id)
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
    session_id: str
):
    """获取故障列表"""
    faults = SimulationService.list_faults(session_id)
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
    payload: dict = Body(...)
):
    """
    新增/更新故障规则
    """
    session_id = payload.get('sessionId') or payload.get('session_id')
    fault_type = payload.get('faultType') or payload.get('fault_type')
    target_id = payload.get('targetId') or payload.get('target_id')
    params = payload.get('params') or payload
    if not session_id or not fault_type or target_id is None:
        return ResponseUtil.error(msg='sessionId、faultType、targetId 为必填')

    result = SimulationService.inject_fault(session_id, fault_type, target_id, params)
    logger.info(f'注入故障: {session_id} -> {fault_type}@{target_id}')
    return ResponseUtil.success(data=result)


@simulationController.get(
    '/faults',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def query_faults(session_id: str = Query(..., alias="sessionId")):
    """查询会话故障"""
    if not session_id:
        return ResponseUtil.error(msg='sessionId 不能为空')
    faults = SimulationService.list_faults(session_id)
    return ResponseUtil.success(data=faults)


@simulationController.delete(
    '/faults/{fault_id}',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:use'))
    ]
)
async def delete_fault(fault_id: str, session_id: str = Query(..., alias="sessionId")):
    """删除会话故障"""
    result = SimulationService.clear_fault(session_id, fault_id)
    logger.info(f'清除故障: {session_id} -> {fault_id}')
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
    event: dict
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
    result = SimulationService.add_event(session_id, event)
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
    updates: dict
):
    """
    更新事件配置

    参数:
        session_id: 会话ID
        event_id: 事件ID
        updates: 更新内容
    """
    result = SimulationService.update_event(session_id, event_id, updates)
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
    event_id: str
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
    result = SimulationService.trigger_event(session_id, event_id)
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
    event_id: str
):
    """重置事件状态为待触发"""
    result = SimulationService.reset_event(session_id, event_id)
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
    event_id: str
):
    """删除事件"""
    result = SimulationService.remove_event(session_id, event_id)
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
    session_id: str
):
    """获取事件列表"""
    events = SimulationService.list_events(session_id)
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
    topology_data: dict
):
    """验证拓扑配置完整性"""
    result = SimulationService.validate_topology(topology_data)
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

    await manager.connect(websocket, session_id)
    logger.info(f'WebSocket连接建立: {session_id}')
    
    try:
        # 启动数据推送任务
        push_task = asyncio.create_task(push_simulation_data(session_id))
        
        # 保持连接并处理客户端消息
        while True:
            try:
                data = await websocket.receive_text()
                # 处理客户端消息（如心跳）
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f'WebSocket消息处理错误: {str(e)}')
                break
        
        # 取消推送任务
        push_task.cancel()
        
    except Exception as e:
        logger.error(f'WebSocket错误: {str(e)}')
    finally:
        manager.disconnect(websocket, session_id)
        logger.info(f'WebSocket连接断开: {session_id}')


async def push_simulation_data(session_id: str):
    """
    推送仿真数据到WebSocket客户端（增量推送，优化性能）
    
    参数:
        session_id: 会话ID
    
    消息类型:
        - status: 仿真状态
        - messages: 报文数据
        - bandwidth: 带宽数据
        - alarms: 告警数据
        - animation: 动画事件（traffic/error/node_active）
        - event: 事件触发通知
        - faults: 故障事件
    """
    import time
    last_push_time = time.time()
    base_interval = 0.1  # 基础 100ms
    buffer_messages = []
    buffer_bandwidth = []
    buffer_alarms = []
    buffer_animations = []
    buffer_faults = []

    def compute_interval(speed: float) -> float:
        # 根据速度缩放推送频率，限制区间 [20ms, 200ms]
        clamped = max(0.5, min(speed or 1.0, 4.0))
        return max(0.02, min(0.2, base_interval / clamped))

    def compute_limits(speed: float) -> Dict[str, int]:
        """
        根据速度动态调整单次推送批量，避免高倍速堆积/低倍速浪费带宽
        """
        clamped = max(0.5, min(speed or 1.0, 4.0))
        msg_limit = int(50 * clamped)
        bw_limit = int(200 * clamped)
        return {
            "messages": max(50, min(msg_limit, 200)),
            "bandwidth": max(100, min(bw_limit, 400)),
            "animations": 20,
            "faults": 50,
        }

    try:
        while True:
            # 获取实时状态
            status = SimulationService.get_session_status(session_id)

            state = status.get('status')
            engine_present = status.get('engine_present', True)

            if state == 'not_found':
                break

            # 引擎缺失但会话仍在（已停止）时，仅推送状态并等待复活
            if not engine_present or state == 'stopped':
                await manager.broadcast(session_id, jsonable_encoder({
                    'type': 'status',
                    'data': status,
                    'timestamp': time.time()
                }))
                await asyncio.sleep(0.5)
                continue

            push_interval = compute_interval(status.get('speed', 1.0))
            limits = compute_limits(status.get('speed', 1.0))
            current_time = time.time()
            should_push = (current_time - last_push_time) >= push_interval

            # 收集增量数据
            new_messages = SimulationService.get_new_messages(session_id, limit=20)
            if new_messages:
                buffer_messages.extend(new_messages)
                # 为每条新消息生成动画事件
                for msg in new_messages:
                    animation = _build_animation_event(msg)
                    if animation:
                        buffer_animations.append(animation)

            new_bandwidth = SimulationService.get_new_bandwidth(session_id)
            if new_bandwidth:
                buffer_bandwidth.extend(new_bandwidth)

            new_alarms = SimulationService.get_new_alarms(session_id)
            if new_alarms:
                buffer_alarms.extend(new_alarms)
                # 为告警生成错误动画
                for alarm in new_alarms:
                    error_animation = _build_error_animation(alarm)
                    if error_animation:
                        buffer_animations.append(error_animation)

            new_fault_events = SimulationService.get_new_fault_events(session_id)
            if new_fault_events:
                buffer_faults.extend(new_fault_events)

            # 节流：达到推送间隔时批量推送
            if should_push:
                # 推送状态（每次都推送，数据量小）
                await manager.broadcast(session_id, jsonable_encoder({
                    'type': 'status',
                    'data': status,
                    'timestamp': current_time
                }))

                # 推送缓冲的报文
                if buffer_messages:
                    await manager.broadcast(session_id, jsonable_encoder({
                        'type': 'messages',
                        'data': buffer_messages[-limits["messages"]:],  # 动态限制单次推送数量
                        'timestamp': current_time
                    }))
                    buffer_messages.clear()

                # 推送缓冲的带宽数据
                if buffer_bandwidth:
                    await manager.broadcast(session_id, jsonable_encoder({
                        'type': 'bandwidth',
                        'data': buffer_bandwidth[-limits["bandwidth"]:],
                        'timestamp': current_time
                    }))
                    buffer_bandwidth.clear()

                # 推送缓冲的告警
                if buffer_alarms:
                    await manager.broadcast(session_id, jsonable_encoder({
                        'type': 'alarms',
                        'data': buffer_alarms,
                        'timestamp': current_time
                    }))
                    buffer_alarms.clear()

                # 推送动画事件
                if buffer_animations:
                    await manager.broadcast(session_id, jsonable_encoder({
                        'type': 'animation',
                        'data': buffer_animations[-limits["animations"]:],  # 限制动画事件数量
                        'timestamp': current_time
                    }))
                    buffer_animations.clear()

                if buffer_faults:
                    await manager.broadcast(session_id, jsonable_encoder({
                        'type': 'faults',
                        'data': buffer_faults[-limits["faults"]:],
                        'timestamp': current_time
                    }))
                    buffer_faults.clear()

                last_push_time = current_time

            # 短间隔轮询（50ms），但批量推送（100ms）
            await asyncio.sleep(0.05)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f'推送仿真数据错误: {str(e)}')


def _build_animation_event(message: dict) -> dict:
    """根据报文构建动画事件"""
    protocol_type = message.get('protocolType') or message.get('protocol_type', 'LAN')
    sender_node = message.get('senderNodeId') or message.get('sender_node_id')
    receiver_node = message.get('receiverNodeId') or message.get('receiver_node_id')

    if not sender_node or not receiver_node:
        return None

    # 协议颜色映射
    protocol_colors = {
        '1553B': '#F97316',  # 橙色
        'CAN': '#3B82F6',    # 蓝色
        'RS422': '#22C55E',  # 绿色
        'RS485': '#22C55E',  # 绿色
        'LAN': '#FFFFFF',    # 白色
    }

    return {
        'type': 'traffic',
        'edgeId': f"{sender_node}-{receiver_node}",
        'sourceNodeId': sender_node,
        'targetNodeId': receiver_node,
        'protocol': protocol_type,
        'color': protocol_colors.get(protocol_type, '#FFFFFF'),
        'duration': 500,  # 动画时长（毫秒）
    }


def _build_error_animation(alarm: dict) -> dict:
    """根据告警构建错误动画事件"""
    alarm_type = alarm.get('alarmType') or alarm.get('alarm_type')
    affected_nodes = alarm.get('affectedNodes') or alarm.get('affected_nodes', [])
    details = alarm.get('details', {})

    if alarm_type in ('collision', 'bandwidth_exceed', 'congestion'):
        edge_id = details.get('edge_id') or details.get('bus_id')
        if edge_id or affected_nodes:
            return {
                'type': 'error',
                'edgeId': edge_id,
                'nodeIds': affected_nodes,
                'alarmType': alarm_type,
                'duration': 1000,
            }

    return None

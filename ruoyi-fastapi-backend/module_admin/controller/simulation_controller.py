"""
仿真控制器
处理仿真相关的HTTP请求和WebSocket连接
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request
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


@simulationController.post(
    '/sessions',
    dependencies=[
        Depends(LoginService.get_current_user),
        Depends(CheckUserInterfaceAuth('simulation:session:create'))
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
        Depends(CheckUserInterfaceAuth('simulation:session:start'))
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
        Depends(CheckUserInterfaceAuth('simulation:session:stop'))
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
        Depends(CheckUserInterfaceAuth('simulation:session:query'))
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
        Depends(CheckUserInterfaceAuth('simulation:data:query'))
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
        Depends(CheckUserInterfaceAuth('simulation:data:query'))
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
        Depends(CheckUserInterfaceAuth('simulation:data:query'))
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
        Depends(CheckUserInterfaceAuth('simulation:data:export'))
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
    推送仿真数据到WebSocket客户端
    
    参数:
        session_id: 会话ID
    """
    try:
        while True:
            # 获取实时数据
            status = SimulationService.get_session_status(session_id)
            
            if status.get('status') == 'not_found':
                break
            
            # 推送状态
            await manager.broadcast(session_id, {
                'type': 'status',
                'data': status
            })
            
            # 推送最新报文
            messages = SimulationService.get_realtime_messages(session_id, limit=10)
            if messages:
                await manager.broadcast(session_id, {
                    'type': 'messages',
                    'data': messages
                })
            
            # 推送带宽数据
            bandwidth_data = SimulationService.get_realtime_bandwidth(session_id)
            if bandwidth_data:
                await manager.broadcast(session_id, {
                    'type': 'bandwidth',
                    'data': bandwidth_data
                })
            
            # 推送告警
            alarms = SimulationService.get_realtime_alarms(session_id)
            if alarms:
                await manager.broadcast(session_id, {
                    'type': 'alarms',
                    'data': alarms
                })
            
            # 等待1秒后继续推送
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f'推送仿真数据错误: {str(e)}')

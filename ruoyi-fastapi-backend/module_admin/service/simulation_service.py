"""
仿真服务层
整合仿真引擎、带宽计算器、告警检测器
"""
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ValidationException, ResourceNotFoundException, SystemException
from config.error_codes import ErrorCode
from module_admin.entity.do.simulation_do import (
    SimulationSessionDO,
    SimulationMessageDO,
    SimulationBandwidthDO,
    SimulationAlarmDO
)
from module_admin.repository import (
    SimulationSessionRepository,
    SimulationMessageRepository,
    SimulationBandwidthRepository,
    SimulationAlarmRepository,
    ProjectTopologyRepository
)
from module_admin.entity.vo.simulation_vo import (
    CreateSimulationSessionModel,
    SimulationQueryModel,
    SimulationExportModel
)
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.service.simulation_engine import SimulationEngine
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
from utils.transaction_manager import transactional


class SimulationService:
    """
    仿真服务层
    管理仿真会话、引擎实例、数据持久化
    """
    
    # 存储活动的仿真引擎实例
    _active_engines: Dict[str, SimulationEngine] = {}
    # WS 故障事件增量游标
    _fault_event_offsets: Dict[str, int] = {}
    # 会话配置缓存（支撑停止后重建）
    _session_configs: Dict[str, Dict] = {}

    @classmethod
    @transactional()
    async def create_session(
        cls, query_db: AsyncSession, request: CreateSimulationSessionModel
    ) -> Dict:
        """
        创建仿真会话
        
        参数:
            query_db: 数据库会话
            request: 创建请求
            
        返回:
            会话信息
        """
        try:
            # 获取拓扑数据
            topology_repo = ProjectTopologyRepository(query_db)
            topology = await topology_repo.find_by_project_and_version(
                request.project_id, request.version_id
            )
            
            if not topology or not topology.topology_data:
                raise ResourceNotFoundException(
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    message='拓扑数据不存在，请先创建拓扑'
                )
            
            # 解析拓扑数据
            topology_data = topology.topology_data
            if isinstance(topology_data, str):
                topology_data = json.loads(topology_data)
            
            # 创建会话
            session_id = str(uuid.uuid4())
            session_repo = SimulationSessionRepository(query_db)
            db_session = SimulationSessionDO(
                session_id=session_id,
                project_id=request.project_id,
                version_id=request.version_id,
                status='created',
                create_by=request.create_by,
                create_time=datetime.now()
            )
            
            await session_repo.add(db_session)
            
            # 创建仿真引擎实例（传递全局策略配置）
            engine = SimulationEngine(
                session_id, 
                topology_data,
                injection_strategy=request.injection_strategy or 'random',
                injection_params=request.injection_params or {}
            )
            cls._active_engines[session_id] = engine
            # 缓存重建所需配置
            cls._session_configs[session_id] = {
                'project_id': request.project_id,
                'version_id': request.version_id,
                'injection_strategy': request.injection_strategy or 'random',
                'injection_params': request.injection_params or {},
            }
            
            return CamelCaseUtil.transform_result({
                'session_id': session_id,
                'status': 'created',
                'message': '仿真会话创建成功'
            })
            
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            await query_db.rollback()
            # 检查是否是表不存在的错误
            error_msg = str(e)
            if "doesn't exist" in error_msg or "no such table" in error_msg.lower():
                raise SystemException(
                    error_code=ErrorCode.SYSTEM_ERROR,
                    message='仿真数据表不存在，请先执行 sql/simulation.sql 创建数据库表'
                )
            raise SystemException(
                error_code=ErrorCode.SYSTEM_ERROR,
                message=f'创建仿真会话失败: {error_msg}\n{error_detail}'
            )

    @classmethod
    @transactional()
    async def start_session(cls, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        启动仿真会话
        
        参数:
            query_db: 数据库会话
            session_id: 会话ID
            
        返回:
            操作结果
        """
        # 获取引擎实例
        engine = cls._active_engines.get(session_id)
        if (not engine) or getattr(engine, "status", "") == "stopped":
            engine = await cls._rebuild_engine(query_db, session_id)
        
        # 启动引擎
        await engine.start()
        
        # 更新数据库状态
        session_repo = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, 'running', None)
        
        return CrudResponseModel(is_success=True, message='仿真已启动')

    @classmethod
    async def _rebuild_engine(cls, query_db: AsyncSession, session_id: str) -> SimulationEngine:
        """
        当引擎不存在（如停止后被清理）时，基于会话记录与拓扑重建引擎，支持再次启动
        """
        session_repo = SimulationSessionRepository(query_db)
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        cached = cls._session_configs.get(session_id, {})
        if not cached:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                message='仿真会话配置缺失，无法重建引擎，请重新创建会话'
            )

        topology_repo = ProjectTopologyRepository(query_db)
        topology = await topology_repo.find_by_project_and_version(
            session.project_id, session.version_id
        )
        if not topology or not topology.topology_data:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='拓扑数据不存在，无法重建仿真会话'
            )

        topology_data = topology.topology_data
        if isinstance(topology_data, str):
            topology_data = json.loads(topology_data)

        engine = SimulationEngine(
            session_id,
            topology_data,
            injection_strategy=cached.get('injection_strategy', 'random'),
            injection_params=cached.get('injection_params', {})
        )
        cls._active_engines[session_id] = engine
        # 清理故障事件游标，避免引用旧实例
        cls._fault_event_offsets.pop(session_id, None)
        return engine

    @classmethod
    @transactional()
    async def stop_session(cls, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        停止仿真会话
        
        参数:
            query_db: 数据库会话
            session_id: 会话ID
            
        返回:
            操作结果
        """
        # 获取引擎实例
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )
        
        # 停止引擎
        await engine.stop()
        
        # 保存数据到数据库
        await cls._persist_simulation_data(query_db, engine)
        
        # 更新数据库状态
        session_repo = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, 'stopped', datetime.now())
        
        # 移除引擎实例
        del cls._active_engines[session_id]
        cls._fault_event_offsets.pop(session_id, None)
        
        return CrudResponseModel(is_success=True, message='仿真已停止')

    @classmethod
    async def _persist_simulation_data(cls, query_db: AsyncSession, engine: SimulationEngine):
        """
        持久化仿真数据到数据库
        
        参数:
            query_db: 数据库会话
            engine: 仿真引擎实例
        """
        message_repo = SimulationMessageRepository(query_db)
        bandwidth_repo = SimulationBandwidthRepository(query_db)
        alarm_repo = SimulationAlarmRepository(query_db)
        
        # 批量保存报文
        messages = engine.get_messages()
        if messages:
            message_dos = [SimulationMessageDO(**msg) for msg in messages]
            await message_repo.batch_create(message_dos)
        
        # 批量保存带宽数据
        bandwidth_data = engine.get_bandwidth_data()
        if bandwidth_data:
            bandwidth_dos = [SimulationBandwidthDO(**bw) for bw in bandwidth_data]
            await bandwidth_repo.batch_create(bandwidth_dos)
        
        # 批量保存告警
        alarms = engine.get_alarms()
        if alarms:
            alarm_dos = [SimulationAlarmDO(**alarm) for alarm in alarms]
            await alarm_repo.batch_create(alarm_dos)

    @classmethod
    def get_session_status(cls, session_id: str) -> Dict:
        """
        获取仿真会话状态
        
        参数:
            session_id: 会话ID
            
        返回:
            状态信息
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            # 若引擎不存在但会话记录仍在，返回已停止状态，便于WS保持
            cached = cls._session_configs.get(session_id)
            if cached:
                return {
                    'session_id': session_id,
                    'status': 'stopped',
                    'engine_present': False,
                    'message': '仿真已停止',
                    'speed': 1.0,
                    'elapsed_time': 0,
                    'message_count': 0,
                    'bandwidth_data_count': 0,
                    'alarm_count': 0,
                }
            return {'status': 'not_found', 'message': '仿真会话不存在'}
        
        status = engine.get_status()
        status['engine_present'] = True
        return CamelCaseUtil.transform_result(status)

    @classmethod
    def get_realtime_messages(cls, session_id: str, limit: int = 100) -> List[Dict]:
        """
        获取实时报文数据（全量）
        
        参数:
            session_id: 会话ID
            limit: 限制数量
            
        返回:
            报文列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []
        
        messages = engine.get_messages()
        # 返回最新的N条
        messages = messages[-limit:] if len(messages) > limit else messages
        return [CamelCaseUtil.transform_result(msg) for msg in messages]

    @classmethod
    def get_new_messages(cls, session_id: str, limit: int = 20) -> List[Dict]:
        """
        获取增量报文数据（仅返回未推送过的新数据）
        
        参数:
            session_id: 会话ID
            limit: 限制数量
            
        返回:
            新报文列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []
        
        messages = engine.get_new_messages(limit)
        return [CamelCaseUtil.transform_result(msg) for msg in messages]

    @classmethod
    def get_realtime_bandwidth(cls, session_id: str, port_id: Optional[str] = None) -> List[Dict]:
        """
        获取实时带宽数据（全量）
        
        参数:
            session_id: 会话ID
            port_id: 端口ID（可选）
            
        返回:
            带宽数据列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []
        
        bandwidth_data = engine.get_bandwidth_data(port_id=port_id)
        return [CamelCaseUtil.transform_result(bw) for bw in bandwidth_data]

    @classmethod
    def get_new_bandwidth(cls, session_id: str) -> List[Dict]:
        """
        获取增量带宽数据（仅返回未推送过的新数据）
        
        参数:
            session_id: 会话ID
            
        返回:
            新带宽数据列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []
        
        bandwidth_data = engine.get_new_bandwidth_data()
        return [CamelCaseUtil.transform_result(bw) for bw in bandwidth_data]

    @classmethod
    def get_realtime_alarms(cls, session_id: str) -> List[Dict]:
        """
        获取实时告警数据（全量）
        
        参数:
            session_id: 会话ID
            
        返回:
            告警列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []
        
        alarms = engine.get_alarms()
        return [CamelCaseUtil.transform_result(alarm) for alarm in alarms]

    @classmethod
    def get_new_alarms(cls, session_id: str) -> List[Dict]:
        """
        获取增量告警数据（仅返回未推送过的新数据）
        
        参数:
            session_id: 会话ID
            
        返回:
            新告警列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []
        
        alarms = engine.get_new_alarms()
        return [CamelCaseUtil.transform_result(alarm) for alarm in alarms]

    @classmethod
    def get_new_fault_events(cls, session_id: str) -> List[Dict]:
        """
        获取增量故障事件（创建/激活/过期/清除）
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []

        offset = cls._fault_event_offsets.get(session_id, 0)
        events, new_offset = engine.fault_injector.get_new_events(session_id, offset)
        cls._fault_event_offsets[session_id] = new_offset
        return [CamelCaseUtil.transform_result(evt) for evt in events]

    @classmethod
    async def get_historical_messages(
        cls, query_db: AsyncSession, query: SimulationQueryModel
    ) -> List[Dict]:
        """
        获取历史报文数据
        
        参数:
            query_db: 数据库会话
            query: 查询参数
            
        返回:
            报文列表
        """
        message_repo = SimulationMessageRepository(query_db)
        messages = await message_repo.find_by_session(
            query.session_id, query.start_time, query.end_time
        )
        return [CamelCaseUtil.transform_result(msg) for msg in messages]

    @classmethod
    async def export_simulation_data(
        cls, query_db: AsyncSession, export_request: SimulationExportModel
    ) -> Dict:
        """
        导出仿真数据
        
        参数:
            query_db: 数据库会话
            export_request: 导出请求
            
        返回:
            导出数据
        """
        session_id = export_request.session_id
        data_type = export_request.data_type
        export_format = export_request.export_format
        
        # 获取数据
        if data_type == 'messages':
            message_repo = SimulationMessageRepository(query_db)
            data = await message_repo.find_by_session(session_id)
        elif data_type == 'bandwidth':
            bandwidth_repo = SimulationBandwidthRepository(query_db)
            data = await bandwidth_repo.find_by_session(session_id)
        elif data_type == 'alarms':
            alarm_repo = SimulationAlarmRepository(query_db)
            data = await alarm_repo.find_by_session(session_id)
        else:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='data_type',
                message=f'不支持的数据类型: {data_type}'
            )
        
        # 转换格式
        result_data = [CamelCaseUtil.transform_result(item) for item in data]
        
        if export_format == 'json':
            return {
                'format': 'json',
                'data': result_data
            }
        elif export_format == 'csv':
            # CSV格式转换（简化实现）
            return {
                'format': 'csv',
                'data': result_data,
                'message': 'CSV导出功能待实现'
            }
        else:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='export_format',
                message=f'不支持的导出格式: {export_format}'
            )

    # ==================== 新增：仿真控制增强 ====================

    @classmethod
    @transactional()
    async def pause_session(cls, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        暂停仿真会话

        参数:
            query_db: 数据库会话
            session_id: 会话ID

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        await engine.pause()

        session_repo = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, 'paused', None)

        return CrudResponseModel(is_success=True, message='仿真已暂停')

    @classmethod
    @transactional()
    async def resume_session(cls, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        继续仿真会话

        参数:
            query_db: 数据库会话
            session_id: 会话ID

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        await engine.resume()

        session_repo = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, 'running', None)

        return CrudResponseModel(is_success=True, message='仿真已继续')

    @classmethod
    def set_speed(cls, session_id: str, speed: float) -> CrudResponseModel:
        """
        设置仿真速度

        参数:
            session_id: 会话ID
            speed: 速度（0.5-4.0）

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        clamped_speed = max(0.5, min(speed, 4.0))
        engine.set_speed(clamped_speed)

        return CrudResponseModel(is_success=True, message=f'仿真速度已设置为 {clamped_speed}x')

    @classmethod
    async def step_once(cls, session_id: str) -> CrudResponseModel:
        """
        单步执行

        参数:
            session_id: 会话ID

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        await engine.step_once()

        return CrudResponseModel(is_success=True, message='单步执行完成')

    @classmethod
    def set_duration(cls, session_id: str, duration: Optional[float]) -> CrudResponseModel:
        """
        设置仿真时长

        参数:
            session_id: 会话ID
            duration: 时长（秒），None 表示无限制

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        engine.set_duration(duration)

        msg = f'仿真时长已设置为 {duration}秒' if duration else '仿真时长限制已取消'
        return CrudResponseModel(is_success=True, message=msg)

    # ==================== 新增：故障注入 ====================

    @classmethod
    def inject_fault(
        cls,
        session_id: str,
        fault_type: str,
        target_id: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        注入故障

        参数:
            session_id: 会话ID
            fault_type: 故障类型（disconnect, error_frame, device_failure, packet_loss, delay）
            target_id: 目标ID（链路ID或节点ID）
            params: 故障参数

        返回:
            故障信息
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        fault = engine.fault_injector.inject_fault(session_id, fault_type, target_id, params)
        return CamelCaseUtil.transform_result(fault)

    @classmethod
    def clear_fault(cls, session_id: str, fault_id: str) -> CrudResponseModel:
        """
        清除故障

        参数:
            session_id: 会话ID
            fault_id: 故障ID

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        success = engine.fault_injector.clear_fault(session_id, fault_id)
        if success:
            return CrudResponseModel(is_success=True, message='故障已清除')
        else:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='故障不存在或已清除'
            )

    @classmethod
    def clear_all_faults(cls, session_id: str) -> CrudResponseModel:
        """
        清除指定会话的所有故障

        参数:
            session_id: 会话ID

        返回:
            操作结果（包含清除数量）
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        try:
            cleared_count = engine.fault_injector.clear_all_faults(session_id)
        except Exception as e:
            logger.error(f'清除全部故障失败: {e}')
            cleared_count = 0

        return CrudResponseModel(is_success=True, message=f'已清除 {cleared_count} 个故障')

    @classmethod
    def list_faults(cls, session_id: str) -> List[Dict]:
        """
        获取故障列表

        参数:
            session_id: 会话ID

        返回:
            故障列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []

        faults = engine.fault_injector.list_faults(session_id)
        return [CamelCaseUtil.transform_result(f) for f in faults]

    # ==================== 新增：事件触发 ====================

    @classmethod
    def add_event(cls, session_id: str, event: Dict) -> Dict:
        """
        添加事件

        参数:
            session_id: 会话ID
            event: 事件配置

        返回:
            事件信息
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ServiceException(message='仿真会话不存在或已过期')

        # 设置动作执行器
        cls._setup_action_executor(engine)

        event_data = engine.event_service.add_event(session_id, event)
        return CamelCaseUtil.transform_result(event_data)

    @classmethod
    def update_event(cls, session_id: str, event_id: str, updates: Dict) -> Dict:
        """
        更新事件

        参数:
            session_id: 会话ID
            event_id: 事件ID
            updates: 更新内容

        返回:
            更新后的事件信息
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        event_data = engine.event_service.update_event(session_id, event_id, updates)
        if not event_data:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='事件不存在'
            )
        return CamelCaseUtil.transform_result(event_data)

    @classmethod
    def trigger_event(cls, session_id: str, event_id: str) -> Dict:
        """
        手动触发事件

        参数:
            session_id: 会话ID
            event_id: 事件ID

        返回:
            触发结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        # 设置动作执行器
        cls._setup_action_executor(engine)

        result = engine.event_service.trigger_event(session_id, event_id)
        if not result:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='事件不存在'
            )
        return CamelCaseUtil.transform_result(result)

    @classmethod
    def reset_event(cls, session_id: str, event_id: str) -> CrudResponseModel:
        """
        重置事件状态为待触发

        参数:
            session_id: 会话ID
            event_id: 事件ID

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        success = engine.event_service.reset_event(session_id, event_id)
        if success:
            return CrudResponseModel(is_success=True, message='事件已重置')
        else:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='事件不存在'
            )

    @classmethod
    def remove_event(cls, session_id: str, event_id: str) -> CrudResponseModel:
        """
        删除事件

        参数:
            session_id: 会话ID
            event_id: 事件ID

        返回:
            操作结果
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='仿真会话不存在或已过期'
            )

        success = engine.event_service.remove_event(session_id, event_id)
        if success:
            return CrudResponseModel(is_success=True, message='事件已删除')
        else:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                message='事件不存在'
            )

    @classmethod
    def list_events(cls, session_id: str) -> List[Dict]:
        """
        获取事件列表

        参数:
            session_id: 会话ID

        返回:
            事件列表
        """
        engine = cls._active_engines.get(session_id)
        if not engine:
            return []

        events = engine.event_service.list_events(session_id)
        return [CamelCaseUtil.transform_result(e) for e in events]

    @classmethod
    def _setup_action_executor(cls, engine: SimulationEngine):
        """
        设置事件动作执行器

        参数:
            engine: 仿真引擎实例
        """
        def execute_action(session_id: str, action: Dict) -> Dict:
            """
            执行事件动作

            动作类型:
                - send_command: 发送指令/报文（A设备给B设备发指令）
                - send_message: 发送报文
                - inject_fault: 注入故障
                - pause: 暂停仿真
                - log: 记录日志
            """
            from utils.log_util import logger
            import uuid
            from datetime import datetime

            action_type = action.get('type')
            params = action.get('params', {})
            result = {'success': True, 'action_type': action_type}

            if action_type in ('send_command', 'send_message'):
                # 发送指令/报文：A设备给B设备发送指令
                source_node = params.get('sourceNodeId') or params.get('source_node_id')
                target_node = params.get('targetNodeId') or params.get('target_node_id')
                command_type = params.get('commandType') or params.get('command_type', 'custom')
                payload_hex = params.get('payload') or params.get('payloadHex') or params.get('payload_hex', '')
                protocol_type = params.get('protocolType') or params.get('protocol_type', 'LAN')

                # 预定义指令类型
                predefined_commands = {
                    'self_check': 'AA55010100',      # 自检指令
                    'power_on': 'AA55020100',        # 上电指令
                    'power_off': 'AA55020200',       # 断电指令
                    'reset': 'AA55030100',           # 复位指令
                    'status_query': 'AA55040100',    # 状态查询
                    'heartbeat': 'AA55050100',       # 心跳
                }

                if command_type in predefined_commands and not payload_hex:
                    payload_hex = predefined_commands[command_type]

                # 生成报文
                message = {
                    'message_id': str(uuid.uuid4()),
                    'session_id': session_id,
                    'sender_node_id': source_node or 'event_trigger',
                    'sender_node_name': engine._get_node_name(source_node) if source_node else '事件触发器',
                    'sender_port_id': params.get('sourcePortId') or params.get('source_port_id', 'event'),
                    'sender_port_name': '事件端口',
                    'receiver_node_id': target_node or 'broadcast',
                    'receiver_node_name': engine._get_node_name(target_node) if target_node else '广播',
                    'receiver_port_id': params.get('targetPortId') or params.get('target_port_id', 'event'),
                    'receiver_port_name': '事件端口',
                    'protocol_type': protocol_type,
                    'size_bytes': len(payload_hex) // 2 if payload_hex else 8,
                    'send_timestamp': engine.current_timestamp or datetime.now().timestamp(),
                    'receive_timestamp': (engine.current_timestamp or datetime.now().timestamp()) + 0.001,
                    'create_time': datetime.now(),
                    'payload_hex': payload_hex,
                    'field_values': {},
                    'fill_strategy': 'command',
                    'is_command': True,
                    'command_type': command_type,
                }

                engine.messages.append(message)
                result['message_id'] = message['message_id']
                result['command_type'] = command_type
                logger.info(f'事件触发发送指令: {source_node} -> {target_node}, 类型: {command_type}')

            elif action_type == 'inject_fault':
                # 注入故障
                fault_type = params.get('faultType') or params.get('fault_type', 'packet_loss')
                target_id = params.get('targetId') or params.get('target_id')
                if target_id:
                    fault = engine.fault_injector.inject_fault(session_id, fault_type, target_id, params)
                    result['fault_id'] = fault.get('fault_id')
                    logger.info(f'事件触发注入故障: {fault_type} @ {target_id}')

            elif action_type == 'pause':
                # 暂停仿真
                engine.runner.pause()
                engine.status = 'paused'
                logger.info(f'事件触发暂停仿真: {session_id}')

            elif action_type == 'log':
                # 记录日志
                message = params.get('message', '事件触发')
                level = params.get('level', 'info')
                if level == 'warning':
                    logger.warning(f'[事件日志] {message}')
                elif level == 'error':
                    logger.error(f'[事件日志] {message}')
                else:
                    logger.info(f'[事件日志] {message}')
                result['log_message'] = message

            return result

        engine.event_service.set_action_executor(execute_action)

    # ==================== 新增：拓扑验证 ====================

    @classmethod
    def validate_topology(cls, topology_data: Dict) -> Dict:
        """
        验证拓扑配置

        参数:
            topology_data: 拓扑数据

        返回:
            验证结果
        """
        from module_admin.service.alarm_detector import AlarmDetector

        alarms = AlarmDetector.validate_topology(topology_data)
        sorted_alarms = AlarmDetector.sort_alarms_by_severity(alarms)

        errors = [a for a in sorted_alarms if a.get('severity') == 'error']
        warnings = [a for a in sorted_alarms if a.get('severity') == 'warning']

        return {
            'is_valid': len(errors) == 0,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'errors': [CamelCaseUtil.transform_result(e) for e in errors],
            'warnings': [CamelCaseUtil.transform_result(w) for w in warnings],
        }

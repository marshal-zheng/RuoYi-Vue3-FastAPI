"""
仿真服务层
整合仿真引擎、带宽计算器、告警检测器
"""
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_admin.dao.simulation_dao import SimulationDao
from module_admin.dao.project_topology_dao import ProjectTopologyDao
from module_admin.entity.vo.simulation_vo import (
    SimulationSessionModel,
    CreateSimulationSessionModel,
    SimulationMessageModel,
    SimulationBandwidthModel,
    SimulationAlarmModel,
    SimulationQueryModel,
    SimulationExportModel
)
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.service.simulation_engine import SimulationEngine
from utils.common_util import CamelCaseUtil


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
            topology = await ProjectTopologyDao.get_topology_by_project_and_version(
                query_db, request.project_id, request.version_id
            )
            
            if not topology or not topology.topology_data:
                raise ServiceException(message='拓扑数据不存在，请先创建拓扑')
            
            # 解析拓扑数据
            topology_data = topology.topology_data
            if isinstance(topology_data, str):
                topology_data = json.loads(topology_data)
            
            # 创建会话
            session_id = str(uuid.uuid4())
            session = SimulationSessionModel(
                session_id=session_id,
                project_id=request.project_id,
                version_id=request.version_id,
                status='created',
                create_by=request.create_by,
                create_time=datetime.now()
            )
            
            await SimulationDao.create_session(query_db, session)
            await query_db.commit()
            
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
                raise ServiceException(message='仿真数据表不存在，请先执行 sql/simulation.sql 创建数据库表')
            raise ServiceException(message=f'创建仿真会话失败: {error_msg}\n{error_detail}')

    @classmethod
    async def start_session(cls, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        启动仿真会话
        
        参数:
            query_db: 数据库会话
            session_id: 会话ID
            
        返回:
            操作结果
        """
        try:
            # 获取引擎实例
            engine = cls._active_engines.get(session_id)
            if (not engine) or getattr(engine, "status", "") == "stopped":
                engine = await cls._rebuild_engine(query_db, session_id)
            
            # 启动引擎
            await engine.start()
            
            # 更新数据库状态
            await SimulationDao.update_session_status(
                query_db, session_id, 'running', None
            )
            await query_db.commit()
            
            return CrudResponseModel(is_success=True, message='仿真已启动')
            
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'启动仿真失败: {str(e)}')

    @classmethod
    async def _rebuild_engine(cls, query_db: AsyncSession, session_id: str) -> SimulationEngine:
        """
        当引擎不存在（如停止后被清理）时，基于会话记录与拓扑重建引擎，支持再次启动
        """
        session = await SimulationDao.get_session_by_id(query_db, session_id)
        if not session:
            raise ServiceException(message='仿真会话不存在或已过期')

        cached = cls._session_configs.get(session_id, {})
        if not cached:
            raise ServiceException(message='仿真会话配置缺失，无法重建引擎，请重新创建会话')

        topology = await ProjectTopologyDao.get_topology_by_project_and_version(
            query_db, session.project_id, session.version_id
        )
        if not topology or not topology.topology_data:
            raise ServiceException(message='拓扑数据不存在，无法重建仿真会话')

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
    async def stop_session(cls, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        停止仿真会话
        
        参数:
            query_db: 数据库会话
            session_id: 会话ID
            
        返回:
            操作结果
        """
        try:
            # 获取引擎实例
            engine = cls._active_engines.get(session_id)
            if not engine:
                raise ServiceException(message='仿真会话不存在或已过期')
            
            # 停止引擎
            await engine.stop()
            
            # 保存数据到数据库
            await cls._persist_simulation_data(query_db, engine)
            
            # 更新数据库状态
            await SimulationDao.update_session_status(
                query_db, session_id, 'stopped', datetime.now()
            )
            await query_db.commit()
            
            # 移除引擎实例
            del cls._active_engines[session_id]
            cls._fault_event_offsets.pop(session_id, None)
            
            return CrudResponseModel(is_success=True, message='仿真已停止')
            
        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            await query_db.rollback()
            raise ServiceException(message=f'停止仿真失败: {str(e)}\n{error_detail}')

    @classmethod
    async def _persist_simulation_data(cls, query_db: AsyncSession, engine: SimulationEngine):
        """
        持久化仿真数据到数据库
        
        参数:
            query_db: 数据库会话
            engine: 仿真引擎实例
        """
        # 批量保存报文
        messages = engine.get_messages()
        if messages:
            message_models = [SimulationMessageModel(**msg) for msg in messages]
            await SimulationDao.batch_create_messages(query_db, message_models)
        
        # 批量保存带宽数据
        bandwidth_data = engine.get_bandwidth_data()
        if bandwidth_data:
            bandwidth_models = [SimulationBandwidthModel(**bw) for bw in bandwidth_data]
            await SimulationDao.batch_create_bandwidth(query_db, bandwidth_models)
        
        # 批量保存告警
        alarms = engine.get_alarms()
        if alarms:
            alarm_models = [SimulationAlarmModel(**alarm) for alarm in alarms]
            await SimulationDao.batch_create_alarms(query_db, alarm_models)

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
        messages = await SimulationDao.get_messages_by_session(
            query_db, query.session_id, query.start_time, query.end_time
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
            data = await SimulationDao.get_messages_by_session(query_db, session_id)
        elif data_type == 'bandwidth':
            data = await SimulationDao.get_bandwidth_by_session(query_db, session_id)
        elif data_type == 'alarms':
            data = await SimulationDao.get_alarms_by_session(query_db, session_id)
        else:
            raise ServiceException(message=f'不支持的数据类型: {data_type}')
        
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
            raise ServiceException(message=f'不支持的导出格式: {export_format}')

    # ==================== 新增：仿真控制增强 ====================

    @classmethod
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
            raise ServiceException(message='仿真会话不存在或已过期')

        await engine.pause()

        await SimulationDao.update_session_status(query_db, session_id, 'paused', None)
        await query_db.commit()

        return CrudResponseModel(is_success=True, message='仿真已暂停')

    @classmethod
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
            raise ServiceException(message='仿真会话不存在或已过期')

        await engine.resume()

        await SimulationDao.update_session_status(query_db, session_id, 'running', None)
        await query_db.commit()

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
            raise ServiceException(message='仿真会话不存在或已过期')

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
            raise ServiceException(message='仿真会话不存在或已过期')

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
            raise ServiceException(message='仿真会话不存在或已过期')

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
            raise ServiceException(message='仿真会话不存在或已过期')

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
            raise ServiceException(message='仿真会话不存在或已过期')

        success = engine.fault_injector.clear_fault(session_id, fault_id)
        if success:
            return CrudResponseModel(is_success=True, message='故障已清除')
        else:
            raise ServiceException(message='故障不存在或已清除')

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
            raise ServiceException(message='仿真会话不存在或已过期')

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

        event_data = engine.event_service.add_event(session_id, event)
        return CamelCaseUtil.transform_result(event_data)

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
            raise ServiceException(message='仿真会话不存在或已过期')

        success = engine.event_service.remove_event(session_id, event_id)
        if success:
            return CrudResponseModel(is_success=True, message='事件已删除')
        else:
            raise ServiceException(message='事件不存在')

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

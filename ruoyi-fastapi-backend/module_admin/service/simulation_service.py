"""
仿真服务层
整合仿真引擎、带宽计算器、告警检测器
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Dict, List, Optional

from fastapi import Depends, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from config.error_codes import ErrorCode
from config.get_db import get_db
from exceptions.exception import ResourceNotFoundException, ServiceException, SystemException, ValidationException
from module_admin.entity.do.enums import SimulationStatusEnum
from module_admin.entity.do.simulation_do import (
    SimulationAlarmDO,
    SimulationBandwidthDO,
    SimulationMessageDO,
    SimulationSessionDO,
)
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.simulation_vo import (
    CreateSimulationSessionModel,
    SimulationExportModel,
    SimulationQueryModel,
)
from module_admin.repository import (
    ProjectTopologyRepository,
    SimulationAlarmRepository,
    SimulationBandwidthRepository,
    SimulationMessageRepository,
    SimulationSessionRepository,
)
from module_admin.service.simulation_engine import SimulationEngine
from module_admin.service.simulation_runtime_state import get_simulation_runtime_state_store
from modules.project.infrastructure.topology_read_adapter import ProjectTopologyReadAdapter
from modules.simulation.application.acl import to_simulation_topology
from modules.simulation.infrastructure.project_topology_adapter import SimulationProjectTopologyAdapter
from modules.simulation.ports import ISimulationProjectTopologyPort
from ports import (
    IProjectTopologyRepository,
    ISimulationAlarmRepository,
    ISimulationBandwidthRepository,
    ISimulationMessageRepository,
    ISimulationSessionRepository,
)
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
    # 会话配置缓存（支撑停止后重建）
    _session_configs: Dict[str, Dict] = {}
    # 运行态快照写入节流（避免高频轮询持续写Redis）
    _snapshot_write_at: Dict[str, float] = {}
    _snapshot_status: Dict[str, str] = {}
    _snapshot_write_interval_sec: float = 0.5

    def __init__(
        self,
        query_db: Optional[AsyncSession] = None,
        project_topology_repo_factory: Callable[[AsyncSession], IProjectTopologyRepository] | None = None,
    ):
        self.query_db = query_db
        self._project_topology_repo_factory = project_topology_repo_factory

    async def _load_simulation_topology_data(
        self,
        query_db: AsyncSession,
        project_id: int,
        version_id: int | None,
    ) -> dict:
        topology_repository_factory = self._project_topology_repo_factory or ProjectTopologyRepository
        project_topology_reader = ProjectTopologyReadAdapter(topology_repository_factory(query_db))
        topology_port: ISimulationProjectTopologyPort = SimulationProjectTopologyAdapter(project_topology_reader)
        topology_view = await topology_port.load_topology_for_simulation(project_id=project_id, version_id=version_id)
        if topology_view is None or not topology_view.topology_data:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                user_message='拓扑数据不存在，请先创建拓扑',
            )
        return to_simulation_topology(topology_view)

    def _require_query_db(self) -> AsyncSession:
        if self.query_db is None:
            raise ServiceException(message='数据库会话未初始化')
        return self.query_db

    async def create_session(
        self,
        request: CreateSimulationSessionModel,
        operator: Optional[str] = None,
    ) -> Dict:
        return await self.create_session_services(
            self._require_query_db(),
            request,
            operator=operator,
        )

    async def start_session(self, session_id: str) -> CrudResponseModel:
        return await self.start_session_services(self._require_query_db(), session_id)

    async def stop_session(self, session_id: str) -> CrudResponseModel:
        return await self.stop_session_services(self._require_query_db(), session_id)

    async def export_simulation_data(self, request: SimulationExportModel):
        return await self.export_simulation_data_services(self._require_query_db(), request)

    async def pause_session(self, session_id: str) -> CrudResponseModel:
        return await self.pause_session_services(self._require_query_db(), session_id)

    async def resume_session(self, session_id: str) -> CrudResponseModel:
        return await self.resume_session_services(self._require_query_db(), session_id)

    async def get_shared_session_status(self, session_id: str) -> Dict:
        return await self.get_shared_session_status_services(session_id)

    def get_realtime_messages(self, session_id: str, limit: int = 100) -> List[Dict]:
        return self.get_realtime_messages_services(session_id, limit)

    def get_new_messages(self, session_id: str, limit: int = 20) -> List[Dict]:
        return self.get_new_messages_services(session_id, limit)

    async def read_messages_with_fallback(self, session_id: str, limit: int = 100) -> List[Dict]:
        messages = self.get_realtime_messages(session_id, limit)
        if messages:
            return messages
        return await self.get_runtime_latest_events(session_id, 'messages', limit)

    async def get_runtime_latest_events(self, session_id: str, stream: str, limit: int) -> List[Dict]:
        return await self.get_runtime_latest_events_services(session_id, stream, limit)

    async def get_runtime_events_since(
        self,
        session_id: str,
        stream: str,
        offset: int,
        limit: int,
    ) -> tuple[List[Dict], int]:
        return await self.get_runtime_events_since_services(session_id, stream, offset, limit)

    async def append_runtime_events(self, session_id: str, stream: str, events: List[Dict]) -> None:
        await self.append_runtime_events_services(session_id, stream, events)

    async def get_runtime_stream_size(self, session_id: str, stream: str) -> int:
        return await self.get_runtime_stream_size_services(session_id, stream)

    def get_realtime_bandwidth(self, session_id: str, port_id: Optional[str] = None) -> List[Dict]:
        return self.get_realtime_bandwidth_services(session_id, port_id)

    def get_new_bandwidth(self, session_id: str) -> List[Dict]:
        return self.get_new_bandwidth_services(session_id)

    async def read_bandwidth_with_fallback(
        self,
        session_id: str,
        port_id: Optional[str] = None,
        limit: int = 400,
    ) -> List[Dict]:
        bandwidth_data = self.get_realtime_bandwidth(session_id, port_id)
        if bandwidth_data:
            return bandwidth_data

        shared_bandwidth = await self.get_runtime_latest_events(session_id, 'bandwidth', limit)
        if port_id:
            shared_bandwidth = [
                point for point in shared_bandwidth if point.get('portId') == port_id or point.get('port_id') == port_id
            ]
        return shared_bandwidth

    def get_realtime_alarms(self, session_id: str) -> List[Dict]:
        return self.get_realtime_alarms_services(session_id)

    def get_new_alarms(self, session_id: str) -> List[Dict]:
        return self.get_new_alarms_services(session_id)

    async def read_alarms_with_fallback(self, session_id: str, limit: int = 200) -> List[Dict]:
        alarms = self.get_realtime_alarms(session_id)
        if alarms:
            return alarms
        return await self.get_runtime_latest_events(session_id, 'alarms', limit)

    def get_new_fault_events(self, session_id: str, offset: int = 0) -> tuple[List[Dict], int]:
        return self.get_new_fault_events_services(session_id, offset)

    async def set_speed(self, session_id: str, speed: float) -> CrudResponseModel:
        return await self.set_speed_services(session_id, speed)

    async def claim_runtime_producer_owner(
        self,
        session_id: str,
        worker_id: str,
        ttl_seconds: int = 10,
    ) -> bool:
        return await self.claim_runtime_producer_owner_services(session_id, worker_id, ttl_seconds)

    async def release_runtime_producer_owner(self, session_id: str, worker_id: str) -> None:
        await self.release_runtime_producer_owner_services(session_id, worker_id)

    async def step_once(self, session_id: str) -> CrudResponseModel:
        return await self.step_once_services(session_id)

    async def set_duration(self, session_id: str, duration: Optional[float]) -> CrudResponseModel:
        return await self.set_duration_services(session_id, duration)

    def resolve_speed_input(self, payload: Optional[Dict]) -> float:
        normalized_payload = payload or {}
        raw_speed = normalized_payload.get('speed', normalized_payload.get('simulationSpeed', 1.0))
        try:
            return float(raw_speed)
        except (TypeError, ValueError):
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='speed',
                user_message='speed 参数格式错误',
            )

    def resolve_duration_input(
        self,
        *,
        duration: Optional[float] = None,
        payload: Optional[Dict] = None,
    ) -> Optional[float]:
        raw_duration = duration
        if raw_duration is None:
            normalized_payload = payload or {}
            raw_duration = normalized_payload.get(
                'duration',
                normalized_payload.get('durationSeconds', normalized_payload.get('maxDuration')),
            )

        if raw_duration in (None, ''):
            return None

        try:
            normalized = float(raw_duration)
        except (TypeError, ValueError):
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='duration',
                user_message='duration 参数格式错误',
            )

        if normalized <= 0:
            return None
        return normalized

    def build_fault_injection_request(
        self,
        *,
        session_id: Optional[str] = None,
        fault_type: Optional[str] = None,
        target_id: Optional[str] = None,
        payload: Optional[Dict] = None,
        require_session_id: bool = False,
    ) -> Dict:
        return self.build_fault_injection_request_services(
            session_id=session_id,
            fault_type=fault_type,
            target_id=target_id,
            payload=payload,
            require_session_id=require_session_id,
        )

    def require_session_id(self, session_id: Optional[str]) -> str:
        normalized = (session_id or '').strip()
        if not normalized:
            raise ValidationException(
                user_message='必填字段缺失',
                developer_message='sessionId is required',
                field='sessionId',
            )
        return normalized

    def apply_fault_injection(
        self,
        *,
        session_id: Optional[str] = None,
        fault_type: Optional[str] = None,
        target_id: Optional[str] = None,
        payload: Optional[Dict] = None,
        require_session_id: bool = False,
    ) -> Dict:
        fault_request = self.build_fault_injection_request(
            session_id=session_id,
            fault_type=fault_type,
            target_id=target_id,
            payload=payload,
            require_session_id=require_session_id,
        )
        resolved_session_id = self.require_session_id(fault_request.get('session_id') or session_id)
        result = self.inject_fault(
            session_id=resolved_session_id,
            fault_type=fault_request['fault_type'],
            target_id=fault_request['target_id'],
            params=fault_request['params'],
        )
        return {
            'session_id': resolved_session_id,
            'fault_type': fault_request['fault_type'],
            'target_id': fault_request['target_id'],
            'result': result,
        }

    def inject_fault(
        self,
        session_id: str,
        fault_type: str,
        target_id: str,
        params: Optional[Dict] = None,
    ) -> Dict:
        return self.inject_fault_services(session_id, fault_type, target_id, params)

    def clear_fault(self, session_id: str, fault_id: str) -> CrudResponseModel:
        return self.clear_fault_services(session_id, fault_id)

    def clear_all_faults(self, session_id: str) -> CrudResponseModel:
        return self.clear_all_faults_services(session_id)

    def list_faults(self, session_id: str) -> List[Dict]:
        return self.list_faults_services(session_id)

    def add_event(self, session_id: str, event: Dict) -> Dict:
        return self.add_event_services(session_id, event)

    def update_event(self, session_id: str, event_id: str, updates: Dict) -> Dict:
        return self.update_event_services(session_id, event_id, updates)

    def trigger_event(self, session_id: str, event_id: str) -> Dict:
        return self.trigger_event_services(session_id, event_id)

    def reset_event(self, session_id: str, event_id: str) -> CrudResponseModel:
        return self.reset_event_services(session_id, event_id)

    def remove_event(self, session_id: str, event_id: str) -> CrudResponseModel:
        return self.remove_event_services(session_id, event_id)

    def list_events(self, session_id: str) -> List[Dict]:
        return self.list_events_services(session_id)

    def validate_topology(self, topology_data: Dict) -> Dict:
        return self.validate_topology_services(topology_data)

    @staticmethod
    def _compute_push_interval(speed: float, base_interval: float = 0.1) -> float:
        """Compute broadcast interval based on simulation speed."""
        clamped = max(0.5, min(speed or 1.0, 4.0))
        return max(0.02, min(0.2, base_interval / clamped))

    @staticmethod
    def _compute_push_limits(speed: float) -> Dict[str, int]:
        """Compute per-tick payload limits based on simulation speed."""
        clamped = max(0.5, min(speed or 1.0, 4.0))
        msg_limit = int(50 * clamped)
        bw_limit = int(200 * clamped)
        alarm_limit = int(100 * clamped)
        return {
            'messages': max(50, min(msg_limit, 200)),
            'bandwidth': max(100, min(bw_limit, 400)),
            'alarms': max(50, min(alarm_limit, 200)),
            'animations': 20,
            'faults': 50,
        }

    @staticmethod
    def _should_collect_from_engine(
        owner_acquired: bool,
        engine_present: bool,
        state: Optional[str],
    ) -> bool:
        """Select local engine stream only for active owner worker."""
        return bool(owner_acquired and engine_present and state != SimulationStatusEnum.STOPPED.value)

    @staticmethod
    def _trim_to_limit(items: List[Dict], limit: int) -> List[Dict]:
        """Keep latest events only to bound memory and shared-stream pressure."""
        if limit <= 0 or not items:
            return []
        return items[-limit:]

    @staticmethod
    def _build_animation_event(message: Dict) -> Optional[Dict]:
        """根据报文构建动画事件。"""
        protocol_type = message.get('protocolType') or message.get('protocol_type', 'LAN')
        sender_node = message.get('senderNodeId') or message.get('sender_node_id')
        receiver_node = message.get('receiverNodeId') or message.get('receiver_node_id')

        if not sender_node or not receiver_node:
            return None

        protocol_colors = {
            '1553B': '#F97316',  # 橙色
            'CAN': '#3B82F6',  # 蓝色
            'RS422': '#22C55E',  # 绿色
            'RS485': '#22C55E',  # 绿色
            'LAN': '#FFFFFF',  # 白色
        }

        return {
            'type': 'traffic',
            'edgeId': f'{sender_node}-{receiver_node}',
            'sourceNodeId': sender_node,
            'targetNodeId': receiver_node,
            'protocol': protocol_type,
            'color': protocol_colors.get(protocol_type, '#FFFFFF'),
            'duration': 500,
        }

    @staticmethod
    def _build_error_animation(alarm: Dict) -> Optional[Dict]:
        """根据告警构建错误动画事件。"""
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

    async def stream_session_updates(
        self,
        session_id: str,
        *,
        has_connections: Callable[[str], Awaitable[bool]],
        broadcast: Callable[[str, Dict], Awaitable[None]],
        worker_id: str,
        owner_ttl_seconds: int = 10,
    ) -> None:
        """
        会话级实时推送主循环。

        说明：
        - 统一 owner 协调、增量采集、共享流回放与节流广播逻辑。
        - Controller 仅负责连接管理与鉴权。
        """
        last_push_time = time.time()
        buffer_messages: List[Dict] = []
        buffer_bandwidth: List[Dict] = []
        buffer_alarms: List[Dict] = []
        buffer_animations: List[Dict] = []
        buffer_faults: List[Dict] = []
        local_fault_offset = 0

        shared_offsets = {
            'messages': 0,
            'bandwidth': 0,
            'alarms': 0,
            'faults': 0,
        }
        shared_offsets_initialized = False
        owner_acquired = False

        async def initialize_shared_offsets_if_needed():
            nonlocal shared_offsets_initialized
            if shared_offsets_initialized:
                return
            for stream in shared_offsets.keys():
                shared_offsets[stream] = await self.get_runtime_stream_size(session_id, stream)
            shared_offsets_initialized = True

        async def collect_from_engine(limits: Dict[str, int]):
            nonlocal local_fault_offset
            new_messages = self.get_new_messages(session_id, limit=limits['messages'])
            new_bandwidth = self.get_new_bandwidth(session_id)
            new_alarms = self.get_new_alarms(session_id)
            new_fault_events, local_fault_offset = self.get_new_fault_events(
                session_id,
                offset=local_fault_offset,
            )
            new_bandwidth = self._trim_to_limit(new_bandwidth, limits['bandwidth'])
            new_alarms = self._trim_to_limit(new_alarms, limits['alarms'])
            new_fault_events = self._trim_to_limit(new_fault_events, limits['faults'])

            if new_messages:
                await self.append_runtime_events(session_id, 'messages', new_messages)
            if new_bandwidth:
                await self.append_runtime_events(session_id, 'bandwidth', new_bandwidth)
            if new_alarms:
                await self.append_runtime_events(session_id, 'alarms', new_alarms)
            if new_fault_events:
                await self.append_runtime_events(session_id, 'faults', new_fault_events)

            return new_messages, new_bandwidth, new_alarms, new_fault_events

        async def collect_from_shared(limits: Dict[str, int]):
            await initialize_shared_offsets_if_needed()
            messages, shared_offsets['messages'] = await self.get_runtime_events_since(
                session_id, 'messages', shared_offsets['messages'], limits['messages']
            )
            bandwidth, shared_offsets['bandwidth'] = await self.get_runtime_events_since(
                session_id, 'bandwidth', shared_offsets['bandwidth'], limits['bandwidth']
            )
            alarms, shared_offsets['alarms'] = await self.get_runtime_events_since(
                session_id, 'alarms', shared_offsets['alarms'], limits['alarms']
            )
            faults, shared_offsets['faults'] = await self.get_runtime_events_since(
                session_id, 'faults', shared_offsets['faults'], limits['faults']
            )
            return messages, bandwidth, alarms, faults

        try:
            while True:
                if not await has_connections(session_id):
                    break

                status = await self.get_shared_session_status(session_id)
                state = status.get('status')
                engine_present = bool(status.get('enginePresent', status.get('engine_present', False)))

                if state == 'not_found':
                    break

                speed = status.get('speed', 1.0)
                push_interval = self._compute_push_interval(speed)
                limits = self._compute_push_limits(speed)
                current_time = time.time()
                should_push = (current_time - last_push_time) >= push_interval

                owner_acquired = await self.claim_runtime_producer_owner(
                    session_id=session_id,
                    worker_id=worker_id,
                    ttl_seconds=owner_ttl_seconds,
                )

                if self._should_collect_from_engine(owner_acquired, engine_present, state):
                    new_messages, new_bandwidth, new_alarms, new_fault_events = await collect_from_engine(limits)
                else:
                    new_messages, new_bandwidth, new_alarms, new_fault_events = await collect_from_shared(limits)
                    if state == SimulationStatusEnum.STOPPED.value:
                        should_push = should_push or (current_time - last_push_time) >= 0.5

                if new_messages:
                    buffer_messages.extend(new_messages)
                    for msg in new_messages:
                        animation = self._build_animation_event(msg)
                        if animation:
                            buffer_animations.append(animation)

                if new_bandwidth:
                    buffer_bandwidth.extend(new_bandwidth)

                if new_alarms:
                    buffer_alarms.extend(new_alarms)
                    for alarm in new_alarms:
                        error_animation = self._build_error_animation(alarm)
                        if error_animation:
                            buffer_animations.append(error_animation)

                if new_fault_events:
                    buffer_faults.extend(new_fault_events)

                if should_push:
                    await broadcast(
                        session_id,
                        jsonable_encoder(
                            {
                                'type': 'status',
                                'data': status,
                                'timestamp': current_time,
                            }
                        ),
                    )

                    if buffer_messages:
                        await broadcast(
                            session_id,
                            jsonable_encoder(
                                {
                                    'type': 'messages',
                                    'data': buffer_messages[-limits['messages'] :],
                                    'timestamp': current_time,
                                }
                            ),
                        )
                        buffer_messages.clear()

                    if buffer_bandwidth:
                        await broadcast(
                            session_id,
                            jsonable_encoder(
                                {
                                    'type': 'bandwidth',
                                    'data': buffer_bandwidth[-limits['bandwidth'] :],
                                    'timestamp': current_time,
                                }
                            ),
                        )
                        buffer_bandwidth.clear()

                    if buffer_alarms:
                        await broadcast(
                            session_id,
                            jsonable_encoder(
                                {
                                    'type': 'alarms',
                                    'data': buffer_alarms[-limits['alarms'] :],
                                    'timestamp': current_time,
                                }
                            ),
                        )
                        buffer_alarms.clear()

                    if buffer_animations:
                        await broadcast(
                            session_id,
                            jsonable_encoder(
                                {
                                    'type': 'animation',
                                    'data': buffer_animations[-limits['animations'] :],
                                    'timestamp': current_time,
                                }
                            ),
                        )
                        buffer_animations.clear()

                    if buffer_faults:
                        await broadcast(
                            session_id,
                            jsonable_encoder(
                                {
                                    'type': 'faults',
                                    'data': buffer_faults[-limits['faults'] :],
                                    'timestamp': current_time,
                                }
                            ),
                        )
                        buffer_faults.clear()

                    last_push_time = current_time

                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error(f'推送仿真数据错误: session_id={session_id}, error={exc}')
        finally:
            if owner_acquired:
                await self.release_runtime_producer_owner(
                    session_id=session_id,
                    worker_id=worker_id,
                )

    async def _persist_runtime_snapshot(self,
        session_id: str,
        *,
        status: Optional[str] = None,
        engine: Optional[SimulationEngine] = None,
        config: Optional[Dict] = None,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """Persist a session snapshot into shared runtime store."""
        if engine is not None:
            snapshot = dict(engine.get_status())
            snapshot['engine_present'] = True
        else:
            snapshot = {
                'session_id': session_id,
                'engine_present': False,
                'speed': 1.0,
                'elapsed_time': 0,
                'message_count': 0,
                'bandwidth_data_count': 0,
                'alarm_count': 0,
            }

        if status is not None:
            snapshot['status'] = status
        if config is not None:
            snapshot['config'] = config
        effective_message = message if message is not None else user_message
        if effective_message:
            snapshot['message'] = effective_message

        now_ts = time.time()
        current_status = snapshot.get('status')
        if not force:
            last_write_at = self._snapshot_write_at.get(session_id, 0.0)
            last_status = self._snapshot_status.get(session_id)
            if current_status == last_status and (now_ts - last_write_at) < self._snapshot_write_interval_sec:
                return

        snapshot['updated_at'] = now_ts
        store = get_simulation_runtime_state_store()
        await store.save_session_snapshot(session_id, snapshot)
        self._snapshot_write_at[session_id] = now_ts
        if current_status is not None:
            self._snapshot_status[session_id] = current_status

    async def get_shared_session_status_services(self, session_id: str) -> Dict:
        """
        Get session status with Redis-backed fallback for multi-worker visibility.
        """
        local_status = self.get_session_status_services(session_id)
        if local_status.get('status') != 'not_found':
            engine = self._active_engines.get(session_id)
            await self._persist_runtime_snapshot(
                session_id,
                status=local_status.get('status'),
                engine=engine,
                config=self._session_configs.get(session_id),
                message=local_status.get('message'),
            )
            return local_status

        store = get_simulation_runtime_state_store()
        snapshot = await store.get_session_snapshot(session_id)
        if snapshot:
            snapshot['engine_present'] = False
            return CamelCaseUtil.transform_result(snapshot)

        return local_status

    @transactional()
    async def create_session_services(self,
        query_db: AsyncSession,
        request: CreateSimulationSessionModel,
        operator: Optional[str] = None,
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
            topology_data = await self._load_simulation_topology_data(
                query_db,
                project_id=request.project_id,
                version_id=request.version_id,
            )

            # 创建会话
            session_id = str(uuid.uuid4())
            creator = operator or request.create_by or 'system'
            session_repo: ISimulationSessionRepository = SimulationSessionRepository(query_db)
            db_session = SimulationSessionDO(
                session_id=session_id,
                project_id=request.project_id,
                version_id=request.version_id,
                status=SimulationStatusEnum.CREATED.value,
                create_by=creator,
                create_time=datetime.now(),
            )

            await session_repo.add(db_session)

            # 创建仿真引擎实例（传递全局策略配置）
            engine = SimulationEngine(
                session_id,
                topology_data,
                injection_strategy=request.injection_strategy or 'random',
                injection_params=request.injection_params or {},
            )
            self._active_engines[session_id] = engine
            # 缓存重建所需配置
            self._session_configs[session_id] = {
                'project_id': request.project_id,
                'version_id': request.version_id,
                'injection_strategy': request.injection_strategy or 'random',
                'injection_params': request.injection_params or {},
            }

            await self._persist_runtime_snapshot(
                session_id,
                status=SimulationStatusEnum.CREATED.value,
                engine=engine,
                config=self._session_configs[session_id],
                message='仿真会话创建成功',
                force=True,
            )

            return CamelCaseUtil.transform_result(
                {'session_id': session_id, 'status': SimulationStatusEnum.CREATED.value, 'message': '仿真会话创建成功'}
            )

        except ServiceException as e:
            await query_db.rollback()
            raise e
        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            await query_db.rollback()
            # 检查是否是表不存在的错误
            error_msg = str(e)
            if "doesn't exist" in error_msg or 'no such table' in error_msg.lower():
                raise SystemException(
                    error_code=ErrorCode.SYSTEM_ERROR,
                    user_message='仿真数据表不存在，请先执行 sql/simulation.sql 创建数据库表',
                )
            raise SystemException(
                error_code=ErrorCode.SYSTEM_ERROR, user_message=f'创建仿真会话失败: {error_msg}\n{error_detail}'
            )

    @transactional()
    async def start_session_services(self, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        启动仿真会话

        参数:
            query_db: 数据库会话
            session_id: 会话ID

        返回:
            操作结果
        """
        # 获取引擎实例
        engine = self._active_engines.get(session_id)
        if (not engine) or getattr(engine, 'status', '') == SimulationStatusEnum.STOPPED.value:
            engine = await self._rebuild_engine(query_db, session_id)

        # 启动引擎
        await engine.start()

        # 更新数据库状态
        session_repo: ISimulationSessionRepository = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, SimulationStatusEnum.RUNNING.value, None)
        await self._persist_runtime_snapshot(
            session_id,
            status=SimulationStatusEnum.RUNNING.value,
            engine=engine,
            config=self._session_configs.get(session_id),
            message='仿真已启动',
            force=True,
        )

        return CrudResponseModel(is_success=True, message='仿真已启动')

    async def _rebuild_engine(self, query_db: AsyncSession, session_id: str) -> SimulationEngine:
        """
        当引擎不存在（如停止后被清理）时，基于会话记录与拓扑重建引擎，支持再次启动
        """
        session_repo: ISimulationSessionRepository = SimulationSessionRepository(query_db)
        session = await session_repo.find_by_id(session_id)
        if not session:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        cached = self._session_configs.get(session_id, {})
        if not cached:
            store = get_simulation_runtime_state_store()
            snapshot = await store.get_session_snapshot(session_id) or {}
            runtime_config = snapshot.get('config') if isinstance(snapshot, dict) else None
            if isinstance(runtime_config, dict):
                cached = runtime_config
                self._session_configs[session_id] = runtime_config

        if not cached:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, user_message='仿真会话配置缺失，无法重建引擎，请重新创建会话'
            )

        try:
            topology_data = await self._load_simulation_topology_data(
                query_db,
                project_id=session.project_id,
                version_id=session.version_id,
            )
        except ResourceNotFoundException as exc:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                user_message='拓扑数据不存在，无法重建仿真会话',
            ) from exc

        engine = SimulationEngine(
            session_id,
            topology_data,
            injection_strategy=cached.get('injection_strategy', 'random'),
            injection_params=cached.get('injection_params', {}),
        )
        self._active_engines[session_id] = engine
        return engine

    @transactional()
    async def stop_session_services(self, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        停止仿真会话

        参数:
            query_db: 数据库会话
            session_id: 会话ID

        返回:
            操作结果
        """
        # 获取引擎实例
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        # 停止引擎
        await engine.stop()

        # 保存数据到数据库
        await self._persist_simulation_data(query_db, engine)

        # 更新数据库状态
        session_repo: ISimulationSessionRepository = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, SimulationStatusEnum.STOPPED.value, datetime.now())
        await self._persist_runtime_snapshot(
            session_id,
            status=SimulationStatusEnum.STOPPED.value,
            engine=engine,
            config=self._session_configs.get(session_id),
            message='仿真已停止',
            force=True,
        )

        # 移除引擎实例
        del self._active_engines[session_id]

        return CrudResponseModel(is_success=True, message='仿真已停止')

    async def _persist_simulation_data(self, query_db: AsyncSession, engine: SimulationEngine):
        """
        持久化仿真数据到数据库

        参数:
            query_db: 数据库会话
            engine: 仿真引擎实例
        """
        message_repo: ISimulationMessageRepository = SimulationMessageRepository(query_db)
        bandwidth_repo: ISimulationBandwidthRepository = SimulationBandwidthRepository(query_db)
        alarm_repo: ISimulationAlarmRepository = SimulationAlarmRepository(query_db)

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

    def get_session_status_services(self, session_id: str) -> Dict:
        """
        获取仿真会话状态

        参数:
            session_id: 会话ID

        返回:
            状态信息
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            # 若引擎不存在但会话记录仍在，返回已停止状态，便于WS保持
            cached = self._session_configs.get(session_id)
            if cached:
                return {
                    'session_id': session_id,
                    'status': SimulationStatusEnum.STOPPED.value,
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

    def get_realtime_messages_services(self, session_id: str, limit: int = 100) -> List[Dict]:
        """
        获取实时报文数据（全量）

        参数:
            session_id: 会话ID
            limit: 限制数量

        返回:
            报文列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        messages = engine.get_messages()
        # 返回最新的N条
        messages = messages[-limit:] if len(messages) > limit else messages
        return [CamelCaseUtil.transform_result(msg) for msg in messages]

    def get_new_messages_services(self, session_id: str, limit: int = 20) -> List[Dict]:
        """
        获取增量报文数据（仅返回未推送过的新数据）

        参数:
            session_id: 会话ID
            limit: 限制数量

        返回:
            新报文列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        messages = engine.get_new_messages(limit)
        return [CamelCaseUtil.transform_result(msg) for msg in messages]

    def get_realtime_bandwidth_services(self, session_id: str, port_id: Optional[str] = None) -> List[Dict]:
        """
        获取实时带宽数据（全量）

        参数:
            session_id: 会话ID
            port_id: 端口ID（可选）

        返回:
            带宽数据列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        bandwidth_data = engine.get_bandwidth_data(port_id=port_id)
        return [CamelCaseUtil.transform_result(bw) for bw in bandwidth_data]

    def get_new_bandwidth_services(self, session_id: str) -> List[Dict]:
        """
        获取增量带宽数据（仅返回未推送过的新数据）

        参数:
            session_id: 会话ID

        返回:
            新带宽数据列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        bandwidth_data = engine.get_new_bandwidth_data()
        return [CamelCaseUtil.transform_result(bw) for bw in bandwidth_data]

    def get_realtime_alarms_services(self, session_id: str) -> List[Dict]:
        """
        获取实时告警数据（全量）

        参数:
            session_id: 会话ID

        返回:
            告警列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        alarms = engine.get_alarms()
        return [CamelCaseUtil.transform_result(alarm) for alarm in alarms]

    def get_new_alarms_services(self, session_id: str) -> List[Dict]:
        """
        获取增量告警数据（仅返回未推送过的新数据）

        参数:
            session_id: 会话ID

        返回:
            新告警列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        alarms = engine.get_new_alarms()
        return [CamelCaseUtil.transform_result(alarm) for alarm in alarms]

    def get_new_fault_events_services(self, session_id: str, offset: int = 0) -> tuple[List[Dict], int]:
        """
        获取增量故障事件（创建/激活/过期/清除）
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return [], offset

        events, new_offset = engine.fault_injector.get_new_events(session_id, offset)
        return [CamelCaseUtil.transform_result(evt) for evt in events], new_offset

    async def append_runtime_events_services(self, session_id: str, stream: str, events: List[Dict]) -> None:
        """Append runtime events into shared store."""
        if not events:
            return
        store = get_simulation_runtime_state_store()
        await store.append_events(session_id, stream, events)

    async def get_runtime_events_since_services(self,
        session_id: str,
        stream: str,
        offset: int,
        limit: int,
    ) -> tuple[List[Dict], int]:
        """Read shared runtime events from offset."""
        store = get_simulation_runtime_state_store()
        return await store.get_events_since(session_id, stream, offset=offset, limit=limit)

    async def get_runtime_latest_events_services(self,
        session_id: str,
        stream: str,
        limit: int,
    ) -> List[Dict]:
        """Read latest shared runtime events."""
        store = get_simulation_runtime_state_store()
        return await store.get_latest_events(session_id, stream, limit=limit)

    async def get_runtime_stream_size_services(self, session_id: str, stream: str) -> int:
        """Get runtime stream size."""
        store = get_simulation_runtime_state_store()
        return await store.get_stream_size(session_id, stream)

    async def claim_runtime_producer_owner_services(self, session_id: str, worker_id: str, ttl_seconds: int = 10
    ) -> bool:
        """Claim session-level producer ownership in shared runtime store."""
        store = get_simulation_runtime_state_store()
        return await store.claim_session_producer_owner(session_id, worker_id, ttl_seconds=ttl_seconds)

    async def release_runtime_producer_owner_services(self, session_id: str, worker_id: str) -> None:
        """Release session-level producer ownership in shared runtime store."""
        store = get_simulation_runtime_state_store()
        await store.release_session_producer_owner(session_id, worker_id)

    async def get_historical_messages_services(self, query_db: AsyncSession, query: SimulationQueryModel) -> List[Dict]:
        """
        获取历史报文数据

        参数:
            query_db: 数据库会话
            query: 查询参数

        返回:
            报文列表
        """
        message_repo: ISimulationMessageRepository = SimulationMessageRepository(query_db)
        messages = await message_repo.find_by_session(query.session_id, query.start_time, query.end_time)
        return [CamelCaseUtil.transform_result(msg) for msg in messages]

    async def export_simulation_data_services(self, query_db: AsyncSession, export_request: SimulationExportModel
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
            message_repo: ISimulationMessageRepository = SimulationMessageRepository(query_db)
            data = await message_repo.find_by_session(session_id)
        elif data_type == 'bandwidth':
            bandwidth_repo: ISimulationBandwidthRepository = SimulationBandwidthRepository(query_db)
            data = await bandwidth_repo.find_by_session(session_id)
        elif data_type == 'alarms':
            alarm_repo: ISimulationAlarmRepository = SimulationAlarmRepository(query_db)
            data = await alarm_repo.find_by_session(session_id)
        else:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT, field='data_type', user_message=f'不支持的数据类型: {data_type}'
            )

        # 转换格式
        result_data = [CamelCaseUtil.transform_result(item) for item in data]

        if export_format == 'json':
            return {'format': 'json', 'data': result_data}
        elif export_format == 'csv':
            # CSV格式转换（简化实现）
            return {'format': 'csv', 'data': result_data, 'message': 'CSV导出功能待实现'}
        else:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='export_format',
                user_message=f'不支持的导出格式: {export_format}',
            )

    # ==================== 新增：仿真控制增强 ====================

    @transactional()
    async def pause_session_services(self, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        暂停仿真会话

        参数:
            query_db: 数据库会话
            session_id: 会话ID

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        await engine.pause()

        session_repo: ISimulationSessionRepository = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, SimulationStatusEnum.PAUSED.value, None)
        await self._persist_runtime_snapshot(
            session_id,
            status=SimulationStatusEnum.PAUSED.value,
            engine=engine,
            config=self._session_configs.get(session_id),
            message='仿真已暂停',
            force=True,
        )

        return CrudResponseModel(is_success=True, message='仿真已暂停')

    @transactional()
    async def resume_session_services(self, query_db: AsyncSession, session_id: str) -> CrudResponseModel:
        """
        继续仿真会话

        参数:
            query_db: 数据库会话
            session_id: 会话ID

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        await engine.resume()

        session_repo: ISimulationSessionRepository = SimulationSessionRepository(query_db)
        await session_repo.update_status(session_id, SimulationStatusEnum.RUNNING.value, None)
        await self._persist_runtime_snapshot(
            session_id,
            status=SimulationStatusEnum.RUNNING.value,
            engine=engine,
            config=self._session_configs.get(session_id),
            message='仿真已继续',
            force=True,
        )

        return CrudResponseModel(is_success=True, message='仿真已继续')

    async def set_speed_services(self, session_id: str, speed: float) -> CrudResponseModel:
        """
        设置仿真速度

        参数:
            session_id: 会话ID
            speed: 速度（0.5-4.0）

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        clamped_speed = max(0.5, min(speed, 4.0))
        engine.set_speed(clamped_speed)
        await self._persist_runtime_snapshot(
            session_id,
            status=SimulationStatusEnum.RUNNING.value
            if engine.status == SimulationStatusEnum.RUNNING.value
            else engine.status,
            engine=engine,
            config=self._session_configs.get(session_id),
            message=f'仿真速度已设置为 {clamped_speed}x',
            force=True,
        )

        return CrudResponseModel(is_success=True, message=f'仿真速度已设置为 {clamped_speed}x')

    async def step_once_services(self, session_id: str) -> CrudResponseModel:
        """
        单步执行

        参数:
            session_id: 会话ID

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        await engine.step_once()
        await self._persist_runtime_snapshot(
            session_id,
            status=SimulationStatusEnum.PAUSED.value,
            engine=engine,
            config=self._session_configs.get(session_id),
            message='单步执行完成',
            force=True,
        )

        return CrudResponseModel(is_success=True, message='单步执行完成')

    async def set_duration_services(self, session_id: str, duration: Optional[float]) -> CrudResponseModel:
        """
        设置仿真时长

        参数:
            session_id: 会话ID
            duration: 时长（秒），None 表示无限制

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        engine.set_duration(duration)
        await self._persist_runtime_snapshot(
            session_id,
            status=engine.status,
            engine=engine,
            config=self._session_configs.get(session_id),
            message='仿真时长已更新',
            force=True,
        )

        msg = f'仿真时长已设置为 {duration}秒' if duration else '仿真时长限制已取消'
        return CrudResponseModel(is_success=True, message=msg)

    # ==================== 新增：故障注入 ====================

    def build_fault_injection_request_services(self,
        *,
        session_id: Optional[str] = None,
        fault_type: Optional[str] = None,
        target_id: Optional[str] = None,
        payload: Optional[Dict] = None,
        require_session_id: bool = False,
    ) -> Dict:
        """
        统一故障注入请求解析，兼容 camelCase/snake_case。

        返回:
            {
                "session_id": str | None,
                "fault_type": str,
                "target_id": str,
                "params": dict | None,
            }
        """
        normalized_payload = payload or {}
        resolved_session_id = session_id or normalized_payload.get('sessionId') or normalized_payload.get('session_id')
        resolved_fault_type = normalized_payload.get('faultType') or normalized_payload.get('fault_type') or fault_type
        resolved_target_id = normalized_payload.get('targetId') or normalized_payload.get('target_id') or target_id
        params = normalized_payload.get('params') if normalized_payload else None
        if params is None and normalized_payload:
            params = normalized_payload

        if require_session_id and not resolved_session_id:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                user_message='必填字段缺失',
                developer_message='sessionId is required',
                field='sessionId',
            )

        if not resolved_fault_type or resolved_target_id is None:
            required = 'sessionId,faultType,targetId' if require_session_id else 'faultType,targetId'
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                user_message='必填字段缺失',
                developer_message=f'{required} are required',
                field=required,
            )

        return {
            'session_id': resolved_session_id,
            'fault_type': resolved_fault_type,
            'target_id': resolved_target_id,
            'params': params,
        }

    def inject_fault_services(self, session_id: str, fault_type: str, target_id: str, params: Optional[Dict] = None
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
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        fault = engine.fault_injector.inject_fault(session_id, fault_type, target_id, params)
        return CamelCaseUtil.transform_result(fault)

    def clear_fault_services(self, session_id: str, fault_id: str) -> CrudResponseModel:
        """
        清除故障

        参数:
            session_id: 会话ID
            fault_id: 故障ID

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        success = engine.fault_injector.clear_fault(session_id, fault_id)
        if success:
            return CrudResponseModel(is_success=True, message='故障已清除')
        else:
            raise ResourceNotFoundException(error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='故障不存在或已清除')

    def clear_all_faults_services(self, session_id: str) -> CrudResponseModel:
        """
        清除指定会话的所有故障

        参数:
            session_id: 会话ID

        返回:
            操作结果（包含清除数量）
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        try:
            cleared_count = engine.fault_injector.clear_all_faults(session_id)
        except Exception as e:
            logger.error(f'清除全部故障失败: {e}')
            cleared_count = 0

        return CrudResponseModel(is_success=True, message=f'已清除 {cleared_count} 个故障')

    def list_faults_services(self, session_id: str) -> List[Dict]:
        """
        获取故障列表

        参数:
            session_id: 会话ID

        返回:
            故障列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        faults = engine.fault_injector.list_faults(session_id)
        return [CamelCaseUtil.transform_result(f) for f in faults]

    # ==================== 新增：事件触发 ====================

    def add_event_services(self, session_id: str, event: Dict) -> Dict:
        """
        添加事件

        参数:
            session_id: 会话ID
            event: 事件配置

        返回:
            事件信息
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ServiceException(user_message='仿真会话不存在或已过期')

        # 设置动作执行器
        self._setup_action_executor(engine)

        event_data = engine.event_service.add_event(session_id, event)
        return CamelCaseUtil.transform_result(event_data)

    def update_event_services(self, session_id: str, event_id: str, updates: Dict) -> Dict:
        """
        更新事件

        参数:
            session_id: 会话ID
            event_id: 事件ID
            updates: 更新内容

        返回:
            更新后的事件信息
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        event_data = engine.event_service.update_event(session_id, event_id, updates)
        if not event_data:
            raise ResourceNotFoundException(error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='事件不存在')
        return CamelCaseUtil.transform_result(event_data)

    def trigger_event_services(self, session_id: str, event_id: str) -> Dict:
        """
        手动触发事件

        参数:
            session_id: 会话ID
            event_id: 事件ID

        返回:
            触发结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        # 设置动作执行器
        self._setup_action_executor(engine)

        result = engine.event_service.trigger_event(session_id, event_id)
        if not result:
            raise ResourceNotFoundException(error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='事件不存在')
        return CamelCaseUtil.transform_result(result)

    def reset_event_services(self, session_id: str, event_id: str) -> CrudResponseModel:
        """
        重置事件状态为待触发

        参数:
            session_id: 会话ID
            event_id: 事件ID

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        success = engine.event_service.reset_event(session_id, event_id)
        if success:
            return CrudResponseModel(is_success=True, message='事件已重置')
        else:
            raise ResourceNotFoundException(error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='事件不存在')

    def remove_event_services(self, session_id: str, event_id: str) -> CrudResponseModel:
        """
        删除事件

        参数:
            session_id: 会话ID
            event_id: 事件ID

        返回:
            操作结果
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            raise ResourceNotFoundException(
                error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='仿真会话不存在或已过期'
            )

        success = engine.event_service.remove_event(session_id, event_id)
        if success:
            return CrudResponseModel(is_success=True, message='事件已删除')
        else:
            raise ResourceNotFoundException(error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='事件不存在')

    def list_events_services(self, session_id: str) -> List[Dict]:
        """
        获取事件列表

        参数:
            session_id: 会话ID

        返回:
            事件列表
        """
        engine = self._active_engines.get(session_id)
        if not engine:
            return []

        events = engine.event_service.list_events(session_id)
        return [CamelCaseUtil.transform_result(e) for e in events]

    def _setup_action_executor(self, engine: SimulationEngine):
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
            import uuid
            from datetime import datetime

            from utils.log_util import logger

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
                    'self_check': 'AA55010100',  # 自检指令
                    'power_on': 'AA55020100',  # 上电指令
                    'power_off': 'AA55020200',  # 断电指令
                    'reset': 'AA55030100',  # 复位指令
                    'status_query': 'AA55040100',  # 状态查询
                    'heartbeat': 'AA55050100',  # 心跳
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
                engine.status = SimulationStatusEnum.PAUSED.value
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

    def validate_topology_services(self, topology_data: Dict) -> Dict:
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


def get_simulation_service(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
) -> SimulationService:
    container = getattr(request.app.state, 'container', None)
    if container is None:
        raise RuntimeError('Application container is not initialized')
    return container.simulation_service(query_db)

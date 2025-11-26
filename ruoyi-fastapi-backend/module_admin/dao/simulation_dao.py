from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from module_admin.entity.do.simulation_do import (
    SimulationSessionDO,
    SimulationMessageDO,
    SimulationBandwidthDO,
    SimulationAlarmDO
)
from module_admin.entity.vo.simulation_vo import (
    SimulationSessionModel,
    SimulationMessageModel,
    SimulationBandwidthModel,
    SimulationAlarmModel
)


class SimulationDao:
    """
    仿真数据访问层
    """

    # ==================== 会话相关 ====================
    
    @classmethod
    async def create_session(cls, db: AsyncSession, session: SimulationSessionModel) -> SimulationSessionDO:
        """创建仿真会话"""
        session_do = SimulationSessionDO(
            session_id=session.session_id,
            project_id=session.project_id,
            version_id=session.version_id,
            status=session.status,
            start_time=session.start_time,
            create_by=session.create_by,
            create_time=session.create_time
        )
        db.add(session_do)
        await db.flush()
        return session_do

    @classmethod
    async def get_session_by_id(cls, db: AsyncSession, session_id: str) -> Optional[SimulationSessionDO]:
        """根据ID获取会话"""
        query = select(SimulationSessionDO).where(SimulationSessionDO.session_id == session_id)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def update_session_status(cls, db: AsyncSession, session_id: str, status: str, end_time=None):
        """更新会话状态"""
        session = await cls.get_session_by_id(db, session_id)
        if session:
            session.status = status
            if end_time:
                session.end_time = end_time
            await db.flush()
        return session

    @classmethod
    async def get_sessions_by_project(
        cls, db: AsyncSession, project_id: int, version_id: Optional[int] = None
    ) -> List[SimulationSessionDO]:
        """获取项目的仿真会话列表"""
        query = select(SimulationSessionDO).where(SimulationSessionDO.project_id == project_id)
        if version_id:
            query = query.where(SimulationSessionDO.version_id == version_id)
        query = query.order_by(SimulationSessionDO.create_time.desc())
        result = await db.execute(query)
        return result.scalars().all()

    # ==================== 报文相关 ====================

    @classmethod
    async def create_message(cls, db: AsyncSession, message: SimulationMessageModel) -> SimulationMessageDO:
        """创建报文记录"""
        message_do = SimulationMessageDO(
            message_id=message.message_id,
            session_id=message.session_id,
            sender_node_id=message.sender_node_id,
            sender_port_id=message.sender_port_id,
            receiver_node_id=message.receiver_node_id,
            receiver_port_id=message.receiver_port_id,
            protocol_type=message.protocol_type,
            size_bytes=message.size_bytes,
            send_timestamp=message.send_timestamp,
            receive_timestamp=message.receive_timestamp,
            create_time=message.create_time
        )
        db.add(message_do)
        await db.flush()
        return message_do

    @classmethod
    async def batch_create_messages(cls, db: AsyncSession, messages: List[SimulationMessageModel]):
        """批量创建报文记录"""
        message_dos = [
            SimulationMessageDO(
                message_id=msg.message_id,
                session_id=msg.session_id,
                sender_node_id=msg.sender_node_id,
                sender_port_id=msg.sender_port_id,
                receiver_node_id=msg.receiver_node_id,
                receiver_port_id=msg.receiver_port_id,
                protocol_type=msg.protocol_type,
                size_bytes=msg.size_bytes,
                send_timestamp=msg.send_timestamp,
                receive_timestamp=msg.receive_timestamp,
                create_time=msg.create_time
            )
            for msg in messages
        ]
        db.add_all(message_dos)
        await db.flush()

    @classmethod
    async def get_messages_by_session(
        cls, db: AsyncSession, session_id: str, start_time: Optional[float] = None, end_time: Optional[float] = None
    ) -> List[SimulationMessageDO]:
        """获取会话的报文列表"""
        query = select(SimulationMessageDO).where(SimulationMessageDO.session_id == session_id)
        if start_time:
            query = query.where(SimulationMessageDO.send_timestamp >= start_time)
        if end_time:
            query = query.where(SimulationMessageDO.send_timestamp <= end_time)
        query = query.order_by(SimulationMessageDO.send_timestamp)
        result = await db.execute(query)
        return result.scalars().all()

    # ==================== 带宽相关 ====================

    @classmethod
    async def create_bandwidth(cls, db: AsyncSession, bandwidth: SimulationBandwidthModel) -> SimulationBandwidthDO:
        """创建带宽数据"""
        bandwidth_do = SimulationBandwidthDO(
            session_id=bandwidth.session_id,
            node_id=bandwidth.node_id,
            port_id=bandwidth.port_id,
            timestamp=bandwidth.timestamp,
            bandwidth_mbps=bandwidth.bandwidth_mbps,
            message_count=bandwidth.message_count,
            create_time=bandwidth.create_time
        )
        db.add(bandwidth_do)
        await db.flush()
        return bandwidth_do

    @classmethod
    async def batch_create_bandwidth(cls, db: AsyncSession, bandwidths: List[SimulationBandwidthModel]):
        """批量创建带宽数据"""
        bandwidth_dos = [
            SimulationBandwidthDO(
                session_id=bw.session_id,
                node_id=bw.node_id,
                port_id=bw.port_id,
                timestamp=bw.timestamp,
                bandwidth_mbps=bw.bandwidth_mbps,
                message_count=bw.message_count,
                create_time=bw.create_time
            )
            for bw in bandwidths
        ]
        db.add_all(bandwidth_dos)
        await db.flush()

    @classmethod
    async def get_bandwidth_by_session(
        cls, db: AsyncSession, session_id: str, port_id: Optional[str] = None,
        start_time: Optional[float] = None, end_time: Optional[float] = None
    ) -> List[SimulationBandwidthDO]:
        """获取会话的带宽数据"""
        query = select(SimulationBandwidthDO).where(SimulationBandwidthDO.session_id == session_id)
        if port_id:
            query = query.where(SimulationBandwidthDO.port_id == port_id)
        if start_time:
            query = query.where(SimulationBandwidthDO.timestamp >= start_time)
        if end_time:
            query = query.where(SimulationBandwidthDO.timestamp <= end_time)
        query = query.order_by(SimulationBandwidthDO.timestamp)
        result = await db.execute(query)
        return result.scalars().all()

    # ==================== 告警相关 ====================

    @classmethod
    async def create_alarm(cls, db: AsyncSession, alarm: SimulationAlarmModel) -> SimulationAlarmDO:
        """创建告警记录"""
        alarm_do = SimulationAlarmDO(
            alarm_id=alarm.alarm_id,
            session_id=alarm.session_id,
            alarm_type=alarm.alarm_type,
            severity=alarm.severity,
            affected_nodes=alarm.affected_nodes,
            message=alarm.message,
            timestamp=alarm.timestamp,
            create_time=alarm.create_time
        )
        db.add(alarm_do)
        await db.flush()
        return alarm_do

    @classmethod
    async def batch_create_alarms(cls, db: AsyncSession, alarms: List[SimulationAlarmModel]):
        """批量创建告警记录"""
        alarm_dos = [
            SimulationAlarmDO(
                alarm_id=alarm.alarm_id,
                session_id=alarm.session_id,
                alarm_type=alarm.alarm_type,
                severity=alarm.severity,
                affected_nodes=alarm.affected_nodes,
                message=alarm.message,
                timestamp=alarm.timestamp,
                create_time=alarm.create_time
            )
            for alarm in alarms
        ]
        db.add_all(alarm_dos)
        await db.flush()

    @classmethod
    async def get_alarms_by_session(
        cls, db: AsyncSession, session_id: str, alarm_type: Optional[str] = None
    ) -> List[SimulationAlarmDO]:
        """获取会话的告警列表"""
        query = select(SimulationAlarmDO).where(SimulationAlarmDO.session_id == session_id)
        if alarm_type:
            query = query.where(SimulationAlarmDO.alarm_type == alarm_type)
        query = query.order_by(SimulationAlarmDO.timestamp)
        result = await db.execute(query)
        return result.scalars().all()

    # ==================== 清理相关 ====================

    @classmethod
    async def delete_session_data(cls, db: AsyncSession, session_id: str):
        """删除会话及其所有相关数据"""
        # 删除报文
        await db.execute(delete(SimulationMessageDO).where(SimulationMessageDO.session_id == session_id))
        # 删除带宽数据
        await db.execute(delete(SimulationBandwidthDO).where(SimulationBandwidthDO.session_id == session_id))
        # 删除告警
        await db.execute(delete(SimulationAlarmDO).where(SimulationAlarmDO.session_id == session_id))
        # 删除会话
        await db.execute(delete(SimulationSessionDO).where(SimulationSessionDO.session_id == session_id))
        await db.flush()

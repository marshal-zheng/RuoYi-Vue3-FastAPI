"""
仿真 Repository
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.simulation_do import (
    SimulationSessionDO,
    SimulationMessageDO,
    SimulationBandwidthDO,
    SimulationAlarmDO
)
from module_admin.repository.base_repository import BaseRepository


class SimulationSessionRepository(BaseRepository[SimulationSessionDO]):
    """仿真会话 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SimulationSessionDO)
    
    async def find_by_id(self, session_id: str) -> Optional[SimulationSessionDO]:
        """根据ID查找会话"""
        stmt = select(SimulationSessionDO).where(SimulationSessionDO.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def find_by_project(
        self,
        project_id: int,
        version_id: Optional[int] = None
    ) -> List[SimulationSessionDO]:
        """根据项目获取会话列表"""
        conditions = [SimulationSessionDO.project_id == project_id]
        if version_id:
            conditions.append(SimulationSessionDO.version_id == version_id)
        
        stmt = (
            select(SimulationSessionDO)
            .where(*conditions)
            .order_by(desc(SimulationSessionDO.create_time))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_status(
        self,
        session_id: str,
        status: str,
        end_time: Optional[datetime] = None
    ) -> Optional[SimulationSessionDO]:
        """更新会话状态"""
        session = await self.find_by_id(session_id)
        if session:
            session.status = status
            if end_time:
                session.end_time = end_time
            await self.db.flush()
        return session
    
    async def delete_with_data(self, session_id: str):
        """删除会话及其所有相关数据"""
        # 删除报文
        await self.db.execute(delete(SimulationMessageDO).where(SimulationMessageDO.session_id == session_id))
        # 删除带宽数据
        await self.db.execute(delete(SimulationBandwidthDO).where(SimulationBandwidthDO.session_id == session_id))
        # 删除告警
        await self.db.execute(delete(SimulationAlarmDO).where(SimulationAlarmDO.session_id == session_id))
        # 删除会话
        await self.db.execute(delete(SimulationSessionDO).where(SimulationSessionDO.session_id == session_id))
        await self.db.flush()


class SimulationMessageRepository(BaseRepository[SimulationMessageDO]):
    """仿真报文 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SimulationMessageDO)
    
    async def find_by_session(
        self,
        session_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[SimulationMessageDO]:
        """根据会话获取报文列表"""
        conditions = [SimulationMessageDO.session_id == session_id]
        if start_time:
            conditions.append(SimulationMessageDO.send_timestamp >= start_time)
        if end_time:
            conditions.append(SimulationMessageDO.send_timestamp <= end_time)
        
        stmt = (
            select(SimulationMessageDO)
            .where(*conditions)
            .order_by(SimulationMessageDO.send_timestamp)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def batch_create(self, messages: List[SimulationMessageDO]):
        """批量创建报文"""
        self.db.add_all(messages)
        await self.db.flush()


class SimulationBandwidthRepository(BaseRepository[SimulationBandwidthDO]):
    """仿真带宽 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SimulationBandwidthDO)
    
    async def find_by_session(
        self,
        session_id: str,
        port_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[SimulationBandwidthDO]:
        """根据会话获取带宽数据"""
        conditions = [SimulationBandwidthDO.session_id == session_id]
        if port_id:
            conditions.append(SimulationBandwidthDO.port_id == port_id)
        if start_time:
            conditions.append(SimulationBandwidthDO.timestamp >= start_time)
        if end_time:
            conditions.append(SimulationBandwidthDO.timestamp <= end_time)
        
        stmt = (
            select(SimulationBandwidthDO)
            .where(*conditions)
            .order_by(SimulationBandwidthDO.timestamp)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def batch_create(self, bandwidths: List[SimulationBandwidthDO]):
        """批量创建带宽数据"""
        self.db.add_all(bandwidths)
        await self.db.flush()


class SimulationAlarmRepository(BaseRepository[SimulationAlarmDO]):
    """仿真告警 Repository"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SimulationAlarmDO)
    
    async def find_by_session(
        self,
        session_id: str,
        alarm_type: Optional[str] = None
    ) -> List[SimulationAlarmDO]:
        """根据会话获取告警列表"""
        conditions = [SimulationAlarmDO.session_id == session_id]
        if alarm_type:
            conditions.append(SimulationAlarmDO.alarm_type == alarm_type)
        
        stmt = (
            select(SimulationAlarmDO)
            .where(*conditions)
            .order_by(SimulationAlarmDO.timestamp)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def batch_create(self, alarms: List[SimulationAlarmDO]):
        """批量创建告警"""
        self.db.add_all(alarms)
        await self.db.flush()

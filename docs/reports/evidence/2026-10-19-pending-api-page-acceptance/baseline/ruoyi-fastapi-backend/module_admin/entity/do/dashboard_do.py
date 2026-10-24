"""Dashboard layout storage; live telemetry is owned by the host data source."""

from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, false

from config.database import Base


class DashboardDO(Base):
    __tablename__ = 'sys_dashboard'
    __table_args__ = (UniqueConstraint('scope', 'scope_key', 'account_id', name='uq_dashboard_scope_account'),)

    dashboard_id = Column(String(36), primary_key=True)
    scope = Column(String(16), nullable=False)
    scope_key = Column(String(128), nullable=False)
    # Account documents use the authenticated ID; scene documents use zero.
    account_id = Column(BigInteger, nullable=False)
    owner_id = Column(BigInteger, nullable=False)
    document = Column(JSON, nullable=False)
    revision = Column(Integer, nullable=False)
    deleted = Column(Boolean, nullable=False, default=False, server_default=false())
    updated_at = Column(DateTime, nullable=False)
    updated_by = Column(BigInteger, nullable=False)


class DashboardVersionDO(Base):
    __tablename__ = 'sys_dashboard_version'
    __table_args__ = (UniqueConstraint('dashboard_id', 'revision', name='uq_dashboard_version'),)

    version_id = Column(Integer, primary_key=True, autoincrement=True)
    dashboard_id = Column(String(36), ForeignKey('sys_dashboard.dashboard_id', ondelete='CASCADE'), nullable=False)
    revision = Column(Integer, nullable=False)
    document = Column(JSON, nullable=False)
    saved_at = Column(DateTime, nullable=False)
    saved_by = Column(BigInteger, nullable=False)

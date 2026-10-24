"""SQLAlchemy models for outbox/history/idempotency records."""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from config.database import Base


class OutboxEventDO(Base):
    __tablename__ = 'outbox_events'

    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    aggregate_type = Column(String(64), nullable=False)
    aggregate_id = Column(String(128), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(Text, nullable=False)
    event_metadata = Column('metadata', Text, nullable=False, default='{}')
    event_version = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default='pending', index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    trace_id = Column(String(128), nullable=True, index=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_outbox_status_retry', 'status', 'next_retry_at'),
        Index('idx_outbox_aggregate_time', 'aggregate_id', 'occurred_at'),
    )


class EventHistoryDO(Base):
    __tablename__ = 'event_history'

    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    aggregate_type = Column(String(64), nullable=False)
    aggregate_id = Column(String(128), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    payload = Column(Text, nullable=False)
    event_metadata = Column('metadata', Text, nullable=False, default='{}')
    event_version = Column(Integer, nullable=False, default=1)
    trace_id = Column(String(128), nullable=True, index=True)
    source_status = Column(String(32), nullable=False, default='published')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index('idx_event_history_aggregate_time', 'aggregate_id', 'occurred_at'),
        Index('idx_event_history_type_time', 'event_type', 'occurred_at'),
    )


class EventConsumptionLogDO(Base):
    __tablename__ = 'event_consumption_log'

    id = Column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False)
    handler_name = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default='failed')
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('event_id', 'handler_name', name='uq_event_consumption_event_handler'),
        Index('idx_event_consumption_status', 'status'),
    )

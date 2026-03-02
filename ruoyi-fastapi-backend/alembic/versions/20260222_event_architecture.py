"""事件驱动基础表

Revision ID: 20260222_event_arch
Revises: 20260210_complete_simulation
Create Date: 2026-02-22 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260222_event_arch'
down_revision = '20260210_complete_simulation'
branch_labels = None
depends_on = None


def _index_names(inspector, table_name: str) -> set[str]:
    if table_name not in inspector.get_table_names():
        return set()
    return {item.get('name') for item in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'outbox_events' not in inspector.get_table_names():
        op.create_table(
            'outbox_events',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('event_id', sa.String(length=64), nullable=False),
            sa.Column('event_type', sa.String(length=128), nullable=False),
            sa.Column('aggregate_type', sa.String(length=64), nullable=False),
            sa.Column('aggregate_id', sa.String(length=128), nullable=False),
            sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('payload', sa.Text(), nullable=False),
            sa.Column('metadata', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('event_version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('trace_id', sa.String(length=128), nullable=True),
            sa.Column('last_error', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('event_id', name='uq_outbox_events_event_id'),
        )

    outbox_indexes = _index_names(inspector, 'outbox_events')
    if 'ix_outbox_events_event_id' not in outbox_indexes:
        op.create_index('ix_outbox_events_event_id', 'outbox_events', ['event_id'])
    if 'ix_outbox_events_event_type' not in outbox_indexes:
        op.create_index('ix_outbox_events_event_type', 'outbox_events', ['event_type'])
    if 'ix_outbox_events_aggregate_id' not in outbox_indexes:
        op.create_index('ix_outbox_events_aggregate_id', 'outbox_events', ['aggregate_id'])
    if 'ix_outbox_events_status' not in outbox_indexes:
        op.create_index('ix_outbox_events_status', 'outbox_events', ['status'])
    if 'ix_outbox_events_next_retry_at' not in outbox_indexes:
        op.create_index('ix_outbox_events_next_retry_at', 'outbox_events', ['next_retry_at'])
    if 'idx_outbox_status_retry' not in outbox_indexes:
        op.create_index('idx_outbox_status_retry', 'outbox_events', ['status', 'next_retry_at'])
    if 'idx_outbox_aggregate_time' not in outbox_indexes:
        op.create_index('idx_outbox_aggregate_time', 'outbox_events', ['aggregate_id', 'occurred_at'])

    if 'event_history' not in inspector.get_table_names():
        op.create_table(
            'event_history',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('event_id', sa.String(length=64), nullable=False),
            sa.Column('event_type', sa.String(length=128), nullable=False),
            sa.Column('aggregate_type', sa.String(length=64), nullable=False),
            sa.Column('aggregate_id', sa.String(length=128), nullable=False),
            sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('payload', sa.Text(), nullable=False),
            sa.Column('metadata', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('event_version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('trace_id', sa.String(length=128), nullable=True),
            sa.Column('source_status', sa.String(length=32), nullable=False, server_default='published'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('event_id', name='uq_event_history_event_id'),
        )

    history_indexes = _index_names(inspector, 'event_history')
    if 'ix_event_history_event_id' not in history_indexes:
        op.create_index('ix_event_history_event_id', 'event_history', ['event_id'])
    if 'ix_event_history_event_type' not in history_indexes:
        op.create_index('ix_event_history_event_type', 'event_history', ['event_type'])
    if 'ix_event_history_aggregate_id' not in history_indexes:
        op.create_index('ix_event_history_aggregate_id', 'event_history', ['aggregate_id'])
    if 'ix_event_history_occurred_at' not in history_indexes:
        op.create_index('ix_event_history_occurred_at', 'event_history', ['occurred_at'])
    if 'ix_event_history_published_at' not in history_indexes:
        op.create_index('ix_event_history_published_at', 'event_history', ['published_at'])
    if 'idx_event_history_aggregate_time' not in history_indexes:
        op.create_index('idx_event_history_aggregate_time', 'event_history', ['aggregate_id', 'occurred_at'])
    if 'idx_event_history_type_time' not in history_indexes:
        op.create_index('idx_event_history_type_time', 'event_history', ['event_type', 'occurred_at'])

    if 'event_consumption_log' not in inspector.get_table_names():
        op.create_table(
            'event_consumption_log',
            sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column('event_id', sa.String(length=64), nullable=False),
            sa.Column('handler_name', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=32), nullable=False, server_default='failed'),
            sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_error', sa.Text(), nullable=True),
            sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('event_id', 'handler_name', name='uq_event_consumption_event_handler'),
        )

    consumption_indexes = _index_names(inspector, 'event_consumption_log')
    if 'idx_event_consumption_status' not in consumption_indexes:
        op.create_index('idx_event_consumption_status', 'event_consumption_log', ['status'])


def downgrade() -> None:
    op.drop_index('idx_event_consumption_status', table_name='event_consumption_log')
    op.drop_table('event_consumption_log')

    op.drop_index('idx_event_history_type_time', table_name='event_history')
    op.drop_index('idx_event_history_aggregate_time', table_name='event_history')
    op.drop_index('ix_event_history_published_at', table_name='event_history')
    op.drop_index('ix_event_history_occurred_at', table_name='event_history')
    op.drop_index('ix_event_history_aggregate_id', table_name='event_history')
    op.drop_index('ix_event_history_event_type', table_name='event_history')
    op.drop_index('ix_event_history_event_id', table_name='event_history')
    op.drop_table('event_history')

    op.drop_index('idx_outbox_aggregate_time', table_name='outbox_events')
    op.drop_index('idx_outbox_status_retry', table_name='outbox_events')
    op.drop_index('ix_outbox_events_next_retry_at', table_name='outbox_events')
    op.drop_index('ix_outbox_events_status', table_name='outbox_events')
    op.drop_index('ix_outbox_events_aggregate_id', table_name='outbox_events')
    op.drop_index('ix_outbox_events_event_type', table_name='outbox_events')
    op.drop_index('ix_outbox_events_event_id', table_name='outbox_events')
    op.drop_table('outbox_events')

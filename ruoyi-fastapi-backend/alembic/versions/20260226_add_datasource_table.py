"""add sys_datasource table

Revision ID: 20260226_datasource
Revises: 20260222_event_arch
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers
revision = '20260226_datasource'
down_revision = '20260222_event_arch'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'sys_datasource' in inspector.get_table_names():
        return

    op.create_table(
        'sys_datasource',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('password', sa.String(500), nullable=True),
        sa.Column('database_name', sa.String(100), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('status', sa.String(10), server_default='offline', nullable=True),
        sa.Column('extra_config', sa.JSON(), nullable=True),
        sa.Column('create_by', sa.String(64), nullable=True),
        sa.Column('update_by', sa.String(64), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=True),
        sa.Column('update_time', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_sys_datasource_name'),
    )
    op.create_index('ix_sys_datasource_is_deleted', 'sys_datasource', ['is_deleted'])


def downgrade() -> None:
    op.drop_index('ix_sys_datasource_is_deleted', table_name='sys_datasource')
    op.drop_table('sys_datasource')

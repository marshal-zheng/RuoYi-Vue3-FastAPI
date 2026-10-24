"""审计日志表

Revision ID: 20260127_audit_log
Revises: 20260127_perf_idx
Create Date: 2026-01-27 16:30:00.000000

P2-005: 数据库审计日志表
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260127_audit_log'
down_revision = '20260127_perf_idx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'sys_audit_log' not in inspector.get_table_names():
        op.create_table(
            'sys_audit_log',
            sa.Column('audit_id', sa.BigInteger(), primary_key=True, autoincrement=True, comment='审计日志主键'),
            sa.Column('action', sa.String(length=10), nullable=False, server_default='', comment='动作类型（READ/INSERT/UPDATE/DELETE）'),
            sa.Column('table_name', sa.String(length=64), nullable=False, server_default='', comment='表名'),
            sa.Column('pk', sa.String(length=128), nullable=True, server_default='', comment='主键标识'),
            sa.Column('before_data', sa.Text(), nullable=True, comment='变更前数据(JSON)'),
            sa.Column('after_data', sa.Text(), nullable=True, comment='变更后数据(JSON)'),
            sa.Column('changed_fields', sa.Text(), nullable=True, comment='变更字段(JSON)'),
            sa.Column('query', sa.Text(), nullable=True, comment='读操作SQL/描述'),
            sa.Column('operator_id', sa.String(length=64), nullable=True, server_default='', comment='操作人ID'),
            sa.Column('operator_name', sa.String(length=64), nullable=True, server_default='', comment='操作人'),
            sa.Column('operator_ip', sa.String(length=128), nullable=True, server_default='', comment='操作IP'),
            sa.Column('request_id', sa.String(length=64), nullable=True, server_default='', comment='请求ID'),
            sa.Column('trace_id', sa.String(length=64), nullable=True, server_default='', comment='链路ID'),
            sa.Column('request_method', sa.String(length=16), nullable=True, server_default='', comment='请求方法'),
            sa.Column('request_path', sa.String(length=255), nullable=True, server_default='', comment='请求路径'),
            sa.Column('user_agent', sa.String(length=255), nullable=True, server_default='', comment='User-Agent'),
            sa.Column('create_time', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='记录时间'),
        )

    existing_indexes = {idx.get('name') for idx in inspector.get_indexes('sys_audit_log')}

    def _create_index_if_missing(name, columns):
        if name in existing_indexes:
            return
        op.create_index(name, 'sys_audit_log', columns)

    _create_index_if_missing('idx_sys_audit_log_table', ['table_name'])
    _create_index_if_missing('idx_sys_audit_log_action', ['action'])
    _create_index_if_missing('idx_sys_audit_log_time', ['create_time'])
    _create_index_if_missing('idx_sys_audit_log_operator', ['operator_name'])


def downgrade() -> None:
    op.drop_index('idx_sys_audit_log_operator', table_name='sys_audit_log')
    op.drop_index('idx_sys_audit_log_time', table_name='sys_audit_log')
    op.drop_index('idx_sys_audit_log_action', table_name='sys_audit_log')
    op.drop_index('idx_sys_audit_log_table', table_name='sys_audit_log')
    op.drop_table('sys_audit_log')

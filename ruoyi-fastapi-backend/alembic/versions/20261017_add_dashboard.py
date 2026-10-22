"""Add revisioned account/scene dashboard storage.

Revision ID: 20261017_dashboard
Revises: 20260405_workflow_object_capability
Create Date: 2026-10-17
"""

import sqlalchemy as sa

from alembic import op

revision = '20261017_dashboard'
down_revision = '20260405_workflow_object_capability'
branch_labels = None
depends_on = None


def upgrade():
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if 'sys_dashboard' not in existing:
        op.create_table(
            'sys_dashboard',
            sa.Column('dashboard_id', sa.String(36), primary_key=True),
            sa.Column('scope', sa.String(16), nullable=False),
            sa.Column('scope_key', sa.String(128), nullable=False),
            sa.Column('account_id', sa.BigInteger(), nullable=False),
            sa.Column('owner_id', sa.BigInteger(), nullable=False),
            sa.Column('document', sa.JSON(), nullable=False),
            sa.Column('revision', sa.Integer(), nullable=False),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('updated_by', sa.BigInteger(), nullable=False),
            sa.UniqueConstraint('scope', 'scope_key', 'account_id', name='uq_dashboard_scope_account'),
        )
    if 'sys_dashboard_version' not in existing:
        op.create_table(
            'sys_dashboard_version',
            sa.Column('version_id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                'dashboard_id',
                sa.String(36),
                sa.ForeignKey('sys_dashboard.dashboard_id', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column('revision', sa.Integer(), nullable=False),
            sa.Column('document', sa.JSON(), nullable=False),
            sa.Column('saved_at', sa.DateTime(), nullable=False),
            sa.Column('saved_by', sa.BigInteger(), nullable=False),
            sa.UniqueConstraint('dashboard_id', 'revision', name='uq_dashboard_version'),
        )


def downgrade():
    op.drop_table('sys_dashboard_version')
    op.drop_table('sys_dashboard')

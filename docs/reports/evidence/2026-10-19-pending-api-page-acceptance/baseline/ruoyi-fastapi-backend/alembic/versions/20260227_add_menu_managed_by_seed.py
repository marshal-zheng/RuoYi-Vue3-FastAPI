"""add managed_by_seed to sys_menu

Revision ID: 20260227_menu_managed_seed
Revises: 20260226_datasource
Create Date: 2026-02-27

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260227_menu_managed_seed'
down_revision = '20260226_datasource'
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    columns = inspector.get_columns(table_name)
    return any(column.get('name') == column_name for column in columns)


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    indexes = inspector.get_indexes(table_name)
    return any(index.get('name') == index_name for index in indexes)


def upgrade() -> None:
    if not _column_exists('sys_menu', 'managed_by_seed'):
        op.add_column(
            'sys_menu',
            sa.Column(
                'managed_by_seed',
                sa.Integer(),
                nullable=False,
                server_default=sa.text('0'),
                comment='是否由种子声明管理(0否1是)',
            ),
        )
    if not _index_exists('sys_menu', 'idx_sys_menu_managed_by_seed'):
        op.create_index('idx_sys_menu_managed_by_seed', 'sys_menu', ['managed_by_seed'], unique=False)


def downgrade() -> None:
    if _index_exists('sys_menu', 'idx_sys_menu_managed_by_seed'):
        op.drop_index('idx_sys_menu_managed_by_seed', table_name='sys_menu')
    if _column_exists('sys_menu', 'managed_by_seed'):
        op.drop_column('sys_menu', 'managed_by_seed')


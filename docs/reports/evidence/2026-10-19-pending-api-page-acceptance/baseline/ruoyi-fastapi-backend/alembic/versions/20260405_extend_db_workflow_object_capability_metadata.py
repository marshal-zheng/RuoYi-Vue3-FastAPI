"""extend db workflow object metadata for capability governance

Revision ID: 20260405_workflow_object_capability
Revises: 20260402_workflow_metadata
Create Date: 2026-04-05

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision = '20260405_workflow_object_capability'
down_revision = '20260402_workflow_metadata'
branch_labels = None
depends_on = None

LEGACY_MODULE_KEY = 'legacy.seed-data'


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(column.get('name') == column_name for column in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(index.get('name') == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    with op.batch_alter_table('sys_db_workflow_object') as batch_op:
        if not _column_exists('sys_db_workflow_object', 'module_key'):
            batch_op.add_column(
                sa.Column(
                    'module_key',
                    sa.String(length=64),
                    nullable=True,
                    server_default=sa.text(f"'{LEGACY_MODULE_KEY}'"),
                    comment='所属 capability 模块键',
                )
            )
        if not _column_exists('sys_db_workflow_object', 'object_domain'):
            batch_op.add_column(
                sa.Column(
                    'object_domain',
                    sa.String(length=32),
                    nullable=True,
                    server_default=sa.text("'menus'"),
                    comment='能力域(menus/role_grants/dict_types/...)',
                )
            )
        if not _column_exists('sys_db_workflow_object', 'source_checksum'):
            batch_op.add_column(
                sa.Column(
                    'source_checksum',
                    sa.String(length=128),
                    nullable=True,
                    server_default=sa.text("''"),
                    comment='声明源内容校验和',
                )
            )

    op.execute(
        sa.text(
            """
            UPDATE sys_db_workflow_object
            SET module_key = COALESCE(module_key, :module_key),
                object_domain = CASE
                    WHEN object_domain IS NOT NULL AND object_domain != '' THEN object_domain
                    WHEN owner_scope = 'role_menus' THEN 'role_grants'
                    ELSE owner_scope
                END,
                source_checksum = COALESCE(NULLIF(source_checksum, ''), checksum)
            """
        ).bindparams(module_key=LEGACY_MODULE_KEY)
    )

    if dialect != 'sqlite':
        with op.batch_alter_table('sys_db_workflow_object') as batch_op:
            batch_op.alter_column(
                'module_key',
                existing_type=sa.String(length=64),
                nullable=False,
                server_default=None,
            )
            batch_op.alter_column(
                'object_domain',
                existing_type=sa.String(length=32),
                nullable=False,
                server_default=None,
            )
            batch_op.alter_column(
                'source_checksum',
                existing_type=sa.String(length=128),
                nullable=False,
                server_default=None,
            )

    if not _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_module'):
        op.create_index('idx_sys_db_workflow_object_module', 'sys_db_workflow_object', ['module_key'], unique=False)
    if not _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_domain'):
        op.create_index('idx_sys_db_workflow_object_domain', 'sys_db_workflow_object', ['object_domain'], unique=False)


def downgrade() -> None:
    if _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_domain'):
        op.drop_index('idx_sys_db_workflow_object_domain', table_name='sys_db_workflow_object')
    if _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_module'):
        op.drop_index('idx_sys_db_workflow_object_module', table_name='sys_db_workflow_object')

    with op.batch_alter_table('sys_db_workflow_object') as batch_op:
        if _column_exists('sys_db_workflow_object', 'source_checksum'):
            batch_op.drop_column('source_checksum')
        if _column_exists('sys_db_workflow_object', 'object_domain'):
            batch_op.drop_column('object_domain')
        if _column_exists('sys_db_workflow_object', 'module_key'):
            batch_op.drop_column('module_key')

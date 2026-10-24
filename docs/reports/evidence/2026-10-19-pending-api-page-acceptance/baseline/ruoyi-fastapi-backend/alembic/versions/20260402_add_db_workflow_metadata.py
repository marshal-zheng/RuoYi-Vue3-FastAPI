"""add db workflow artifact metadata tables

Revision ID: 20260402_workflow_metadata
Revises: 20260227_menu_managed_seed
Create Date: 2026-04-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision = '20260402_workflow_metadata'
down_revision = '20260227_menu_managed_seed'
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    indexes = inspector.get_indexes(table_name)
    return any(index.get('name') == index_name for index in indexes)


def upgrade() -> None:
    artifact_id_type = sa.BigInteger().with_variant(sa.Integer(), 'sqlite')
    object_id_type = sa.BigInteger().with_variant(sa.Integer(), 'sqlite')

    if not _table_exists('sys_db_workflow_artifact'):
        op.create_table(
            'sys_db_workflow_artifact',
            sa.Column('artifact_id', artifact_id_type, primary_key=True, autoincrement=True, comment='工作流产物主键'),
            sa.Column('bundle_id', sa.String(length=64), nullable=False, comment='Bundle 标识'),
            sa.Column(
                'artifact_type',
                sa.String(length=32),
                nullable=False,
                comment='产物类型(managed-data/release-manifest)',
            ),
            sa.Column('artifact_checksum', sa.String(length=128), nullable=False, comment='产物校验和'),
            sa.Column('apply_status', sa.String(length=16), nullable=False, comment='应用状态'),
            sa.Column('applied_at', sa.DateTime(), nullable=False, comment='应用时间'),
            sa.Column('applied_by', sa.String(length=64), nullable=True, comment='应用人/执行器'),
            sa.Column('details_json', sa.Text(), nullable=True, comment='结构化结果明细(JSON)'),
            sa.UniqueConstraint('bundle_id', 'artifact_type', name='uq_sys_db_workflow_artifact_bundle_type'),
        )
    if not _index_exists('sys_db_workflow_artifact', 'idx_sys_db_workflow_artifact_status'):
        op.create_index(
            'idx_sys_db_workflow_artifact_status',
            'sys_db_workflow_artifact',
            ['apply_status'],
            unique=False,
        )
    if not _index_exists('sys_db_workflow_artifact', 'idx_sys_db_workflow_artifact_applied_at'):
        op.create_index(
            'idx_sys_db_workflow_artifact_applied_at',
            'sys_db_workflow_artifact',
            ['applied_at'],
            unique=False,
        )

    if not _table_exists('sys_db_workflow_object'):
        op.create_table(
            'sys_db_workflow_object',
            sa.Column('object_id', object_id_type, primary_key=True, autoincrement=True, comment='受管对象主键'),
            sa.Column(
                'object_type',
                sa.String(length=32),
                nullable=False,
                comment='对象类型(sys_menu/sys_dict_type/...)',
            ),
            sa.Column('object_key', sa.String(length=191), nullable=False, comment='对象业务键'),
            sa.Column('owner_scope', sa.String(length=32), nullable=False, comment='管理范围(menus/dict_types/configs/...)'),
            sa.Column('last_bundle_id', sa.String(length=64), nullable=True, comment='最近一次写入的 bundle_id'),
            sa.Column('last_source_path', sa.String(length=255), nullable=True, comment='最近一次声明来源路径'),
            sa.Column('checksum', sa.String(length=128), nullable=False, comment='当前对象受管内容校验和'),
            sa.Column('active_flag', sa.String(length=1), nullable=False, server_default=sa.text("'Y'"), comment='是否仍由统一工作流受管(Y/N)'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
            sa.UniqueConstraint('object_type', 'object_key', name='uq_sys_db_workflow_object_type_key'),
        )
    if not _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_scope'):
        op.create_index('idx_sys_db_workflow_object_scope', 'sys_db_workflow_object', ['owner_scope'], unique=False)
    if not _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_bundle'):
        op.create_index('idx_sys_db_workflow_object_bundle', 'sys_db_workflow_object', ['last_bundle_id'], unique=False)
    if not _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_active'):
        op.create_index('idx_sys_db_workflow_object_active', 'sys_db_workflow_object', ['active_flag'], unique=False)


def downgrade() -> None:
    if _table_exists('sys_db_workflow_object'):
        if _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_active'):
            op.drop_index('idx_sys_db_workflow_object_active', table_name='sys_db_workflow_object')
        if _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_bundle'):
            op.drop_index('idx_sys_db_workflow_object_bundle', table_name='sys_db_workflow_object')
        if _index_exists('sys_db_workflow_object', 'idx_sys_db_workflow_object_scope'):
            op.drop_index('idx_sys_db_workflow_object_scope', table_name='sys_db_workflow_object')
        op.drop_table('sys_db_workflow_object')

    if _table_exists('sys_db_workflow_artifact'):
        if _index_exists('sys_db_workflow_artifact', 'idx_sys_db_workflow_artifact_applied_at'):
            op.drop_index('idx_sys_db_workflow_artifact_applied_at', table_name='sys_db_workflow_artifact')
        if _index_exists('sys_db_workflow_artifact', 'idx_sys_db_workflow_artifact_status'):
            op.drop_index('idx_sys_db_workflow_artifact_status', table_name='sys_db_workflow_artifact')
        op.drop_table('sys_db_workflow_artifact')

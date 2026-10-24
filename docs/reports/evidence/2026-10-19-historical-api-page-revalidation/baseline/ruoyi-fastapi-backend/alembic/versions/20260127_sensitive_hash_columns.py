"""Add sensitive hash columns for encrypted fields

Revision ID: 20260127_sensitive_hash
Revises: 20260127_audit_log
Create Date: 2026-01-27 18:30:00

Adds hash columns for sensitive fields and adjusts ciphertext length.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260127_sensitive_hash"
down_revision: Union[str, None] = "20260127_audit_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector, table: str, column: str) -> bool:
    return column in {col['name'] for col in inspector.get_columns(table)}


def _index_exists(inspector, table: str, index: str) -> bool:
    for idx in inspector.get_indexes(table):
        if idx.get('name') == index:
            return True
    return False


def _ensure_varchar_length(inspector, table: str, column: str, length: int) -> None:
    for col in inspector.get_columns(table):
        if col['name'] != column:
            continue
        col_type = col.get('type')
        col_length = getattr(col_type, 'length', None)
        if col_length is None or col_length >= length:
            return
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(column, type_=sa.String(length))
        return


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'sys_user' in inspector.get_table_names():
        if not _column_exists(inspector, 'sys_user', 'id_card'):
            op.add_column(
                'sys_user',
                sa.Column('id_card', sa.String(255), nullable=True, comment='身份证号')
            )
        if not _column_exists(inspector, 'sys_user', 'phonenumber_hash'):
            op.add_column(
                'sys_user',
                sa.Column('phonenumber_hash', sa.String(64), nullable=True, comment='手机号码Hash')
            )
        if not _column_exists(inspector, 'sys_user', 'email_hash'):
            op.add_column(
                'sys_user',
                sa.Column('email_hash', sa.String(64), nullable=True, comment='用户邮箱Hash')
            )
        if not _column_exists(inspector, 'sys_user', 'id_card_hash'):
            op.add_column(
                'sys_user',
                sa.Column('id_card_hash', sa.String(64), nullable=True, comment='身份证号Hash')
            )
        _ensure_varchar_length(inspector, 'sys_user', 'phonenumber', 255)
        _ensure_varchar_length(inspector, 'sys_user', 'email', 255)
        _ensure_varchar_length(inspector, 'sys_user', 'id_card', 255)
        if _index_exists(inspector, 'sys_user', 'idx_user_phone'):
            op.drop_index('idx_user_phone', table_name='sys_user')
        if not _index_exists(inspector, 'sys_user', 'idx_user_phone_hash'):
            op.create_index('idx_user_phone_hash', 'sys_user', ['phonenumber_hash'])
        if _index_exists(inspector, 'sys_user', 'idx_user_email'):
            op.drop_index('idx_user_email', table_name='sys_user')
        if not _index_exists(inspector, 'sys_user', 'idx_user_email_hash'):
            op.create_index('idx_user_email_hash', 'sys_user', ['email_hash'])
        if _index_exists(inspector, 'sys_user', 'idx_user_id_card'):
            op.drop_index('idx_user_id_card', table_name='sys_user')
        if not _index_exists(inspector, 'sys_user', 'idx_user_id_card_hash'):
            op.create_index('idx_user_id_card_hash', 'sys_user', ['id_card_hash'])

    if 'sys_dept' in inspector.get_table_names():
        if not _column_exists(inspector, 'sys_dept', 'phone_hash'):
            op.add_column(
                'sys_dept',
                sa.Column('phone_hash', sa.String(64), nullable=True, comment='联系电话Hash')
            )
        _ensure_varchar_length(inspector, 'sys_dept', 'phone', 255)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'sys_user' in inspector.get_table_names():
        if _index_exists(inspector, 'sys_user', 'idx_user_id_card_hash'):
            op.drop_index('idx_user_id_card_hash', table_name='sys_user')
        if _index_exists(inspector, 'sys_user', 'idx_user_email_hash'):
            op.drop_index('idx_user_email_hash', table_name='sys_user')
        if _index_exists(inspector, 'sys_user', 'idx_user_phone_hash'):
            op.drop_index('idx_user_phone_hash', table_name='sys_user')
        if _column_exists(inspector, 'sys_user', 'id_card_hash'):
            op.drop_column('sys_user', 'id_card_hash')
        if _column_exists(inspector, 'sys_user', 'email_hash'):
            op.drop_column('sys_user', 'email_hash')
        if _column_exists(inspector, 'sys_user', 'phonenumber_hash'):
            op.drop_column('sys_user', 'phonenumber_hash')
        if _column_exists(inspector, 'sys_user', 'id_card'):
            op.drop_column('sys_user', 'id_card')

    if 'sys_dept' in inspector.get_table_names():
        if _column_exists(inspector, 'sys_dept', 'phone_hash'):
            op.drop_column('sys_dept', 'phone_hash')

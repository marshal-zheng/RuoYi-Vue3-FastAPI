"""Add create_time to sys_logininfor

Revision ID: 20260127_add_create_time
Revises: 20260123_120000
Create Date: 2026-01-27 12:35:00

This migration adds the create_time column to sys_logininfor table
to match the LogBaseModel definition.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260127_add_create_time"
down_revision: Union[str, None] = "20260123_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add create_time column to sys_logininfor if it doesn't exist"""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if table exists
    if 'sys_logininfor' not in inspector.get_table_names():
        print("Table sys_logininfor does not exist, skipping migration")
        return
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('sys_logininfor')]
    
    if 'create_time' not in columns:
        print("Adding create_time column to sys_logininfor...")
        op.add_column(
            'sys_logininfor',
            sa.Column('create_time', sa.DateTime(), nullable=True, comment='创建时间')
        )
        
        # Update existing rows to set create_time = login_time
        op.execute("""
            UPDATE sys_logininfor 
            SET create_time = login_time 
            WHERE create_time IS NULL
        """)
        
        print("create_time column added successfully")
    else:
        print("create_time column already exists, skipping")


def downgrade() -> None:
    """Remove create_time column from sys_logininfor"""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if table exists
    if 'sys_logininfor' not in inspector.get_table_names():
        return
    
    # Check if column exists
    columns = [col['name'] for col in inspector.get_columns('sys_logininfor')]
    
    if 'create_time' in columns:
        op.drop_column('sys_logininfor', 'create_time')

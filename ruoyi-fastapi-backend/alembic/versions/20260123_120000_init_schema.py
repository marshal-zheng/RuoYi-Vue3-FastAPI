"""Initial migration from ORM models

Revision ID: 20260123_120000
Revises: 
Create Date: 2026-01-23 12:00:00

This migration creates all tables from the ORM models with idempotency checks.
It ensures that tables are only created if they don't already exist, making
the migration safe to run on both empty and existing databases.

Tables created (28 total):
- User management: sys_user, sys_user_role, sys_user_post
- Role management: sys_role, sys_role_menu, sys_role_dept
- Menu management: sys_menu
- Department management: sys_dept
- Position management: sys_post
- Dictionary management: sys_dict_type, sys_dict_data
- Configuration: sys_config
- Notice: sys_notice
- Logging: sys_oper_log, sys_logininfor
- Job scheduling: sys_job, sys_job_log
- Project management: sys_project, sys_project_version, sys_project_topology
- Device management: sys_device, sys_device_category, sys_device_interface
- Protocol management: sys_protocol
- Simulation: sys_simulation_session, sys_simulation_message, 
  sys_simulation_bandwidth, sys_simulation_alarm
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from config.database import Base

# Import all ORM models to populate metadata
from module_admin.entity.do import user_do  # noqa: F401
from module_admin.entity.do import role_do  # noqa: F401
from module_admin.entity.do import menu_do  # noqa: F401
from module_admin.entity.do import dept_do  # noqa: F401
from module_admin.entity.do import post_do  # noqa: F401
from module_admin.entity.do import dict_do  # noqa: F401
from module_admin.entity.do import config_do  # noqa: F401
from module_admin.entity.do import notice_do  # noqa: F401
from module_admin.entity.do import log_do  # noqa: F401
from module_admin.entity.do import job_do  # noqa: F401
from module_admin.entity.do import project_do  # noqa: F401
from module_admin.entity.do import project_version_do  # noqa: F401
from module_admin.entity.do import project_topology_do  # noqa: F401
from module_admin.entity.do import device_do  # noqa: F401
from module_admin.entity.do import device_category_do  # noqa: F401
from module_admin.entity.do import protocol_do  # noqa: F401
from module_admin.entity.do import simulation_do  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20260123_120000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema with idempotency checks.
    
    This function creates all tables defined in the ORM models, but only
    if they don't already exist. This makes the migration safe to run on:
    - Empty databases (fresh installation)
    - Existing databases initialized from SQL files (backward compatibility)
    - Databases where migration was partially applied
    
    The idempotency check inspects the database to get existing table names
    and only creates tables that are missing.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Get all tables from metadata
    tables_to_create = []
    for table_name, table in Base.metadata.tables.items():
        if table_name not in existing_tables:
            tables_to_create.append(table)
    
    # Create only missing tables
    if tables_to_create:
        print(f"Creating {len(tables_to_create)} missing tables...")
        for table in tables_to_create:
            print(f"  - Creating table: {table.name}")
            table.create(bind=bind, checkfirst=True)
        print("Table creation complete.")
    else:
        print("All tables already exist. No changes needed.")


def downgrade() -> None:
    """
    Downgrade schema by dropping all tables.
    
    WARNING: This will drop all tables and delete all data!
    Use with caution, especially in production environments.
    
    The downgrade function drops all tables defined in the metadata.
    This is useful for:
    - Development environments where you want to reset the database
    - Testing scenarios where you need a clean slate
    - Rollback situations (though data will be lost)
    """
    bind = op.get_bind()
    
    print("WARNING: Dropping all tables. This will delete all data!")
    print(f"Dropping {len(Base.metadata.tables)} tables...")
    
    # Drop tables in reverse order to handle foreign key constraints
    Base.metadata.drop_all(bind=bind)
    
    print("All tables dropped successfully.")

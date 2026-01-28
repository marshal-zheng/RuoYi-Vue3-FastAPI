# Alembic Migration Versions

This directory contains all database migration scripts managed by Alembic.

## Initial Migration

### 20260123_120000_init_schema.py

**Purpose**: Creates all database tables from ORM models with idempotency checks.

**Features**:
- Creates 28 tables covering all system modules
- Includes idempotency checks to safely run on existing databases
- Compatible with both MySQL and PostgreSQL
- Supports both fresh installations and migrations from SQL files

**Tables Created**:
- **User Management** (3 tables): sys_user, sys_user_role, sys_user_post
- **Role Management** (3 tables): sys_role, sys_role_menu, sys_role_dept
- **Menu Management** (1 table): sys_menu
- **Department Management** (1 table): sys_dept
- **Position Management** (1 table): sys_post
- **Dictionary Management** (2 tables): sys_dict_type, sys_dict_data
- **Configuration** (1 table): sys_config
- **Notice** (1 table): sys_notice
- **Logging** (2 tables): sys_oper_log, sys_logininfor
- **Job Scheduling** (2 tables): sys_job, sys_job_log
- **Project Management** (3 tables): sys_project, sys_project_version, sys_project_topology
- **Device Management** (3 tables): sys_device, sys_device_category, sys_device_interface
- **Protocol Management** (1 table): sys_protocol
- **Simulation** (4 tables): sys_simulation_session, sys_simulation_message, sys_simulation_bandwidth, sys_simulation_alarm

**Idempotency**:
The migration checks for existing tables before creating them, making it safe to run multiple times. This is crucial for:
- Migrating from SQL file-based initialization
- Recovering from partial migration failures
- Running in containerized environments where migrations may be attempted multiple times

**Usage**:

```bash
# Apply the migration
alembic upgrade head

# Check current revision
alembic current

# View migration history
alembic history

# Rollback (WARNING: drops all tables)
alembic downgrade base
```

## Migration Best Practices

1. **Always review generated migrations** before applying them to production
2. **Test migrations** on a copy of production data before deploying
3. **Backup your database** before running migrations in production
4. **Use transactions** - Alembic automatically wraps migrations in transactions
5. **Document changes** - Add clear descriptions to migration docstrings
6. **Version control** - Always commit migration files to git

## Troubleshooting

### Migration fails with "table already exists"
This shouldn't happen with the initial migration due to idempotency checks. If it does:
1. Check if the migration was partially applied
2. Manually stamp the database: `alembic stamp head`
3. Verify table structure matches ORM models

### Migration fails with foreign key errors
1. Ensure parent tables are created before child tables
2. Check that foreign key constraints are properly defined in ORM models
3. Verify database supports foreign keys (InnoDB for MySQL)

### Need to reset database
```bash
# Drop all tables and reapply migrations
alembic downgrade base
alembic upgrade head
```

## Related Files

- `alembic.ini` - Alembic configuration file
- `alembic/env.py` - Alembic environment configuration
- `config/database.py` - Database connection configuration
- `module_admin/entity/do/` - ORM model definitions

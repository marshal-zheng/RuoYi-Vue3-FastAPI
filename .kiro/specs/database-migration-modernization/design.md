# Design Document: Database Migration Modernization

## Overview

This design establishes a modern, Alembic-based database migration system for RuoYi-Vue3-FastAPI, replacing the current dual SQL file + Alembic approach. The solution follows best practices from FastAPI official templates and enterprise projects like GitLab, establishing Alembic as the single source of truth for schema management.

### Key Design Decisions

1. **Pure Alembic Approach**: Eliminate SQL files entirely, using Alembic migrations as the authoritative schema definition
2. **Python Seed Data**: Replace SQL INSERT statements with Python scripts for better maintainability and environment awareness
3. **Idempotent Operations**: All migrations and seed data operations must be safely repeatable
4. **Docker-First**: Automatic database initialization in containerized environments
5. **Developer Experience**: Provide intuitive CLI tools for common database operations

### Design Goals

- **Single Source of Truth**: Alembic migrations define all schema changes
- **Environment Awareness**: Different seed data for development vs production
- **Zero Downtime**: Support for production migrations without service interruption
- **Backward Compatible**: Seamless migration from existing SQL-based deployments
- **Database Agnostic**: Support both MySQL and PostgreSQL

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (FastAPI Backend with SQLAlchemy ORM Models)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Migration Management Layer                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Alembic    │  │  Seed Data   │  │  CLI Tools   │     │
│  │   Engine     │  │   Manager    │  │  (db_migrate)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│              (MySQL / PostgreSQL)                            │
└─────────────────────────────────────────────────────────────┘
```

### Migration Workflow

```mermaid
graph TD
    A[Developer Changes ORM Model] --> B[Run: db_migrate.sh create 'message']
    B --> C[Alembic Generates Migration Script]
    C --> D[Developer Reviews Migration]
    D --> E{Approved?}
    E -->|No| F[Edit Migration Script]
    F --> D
    E -->|Yes| G[Commit Migration to Git]
    G --> H[Deploy to Environment]
    H --> I[Docker Container Starts]
    I --> J[Run: alembic upgrade head]
    J --> K[Run: seed_data.py]
    K --> L[Application Starts]
```

### Docker Initialization Flow

```mermaid
sequenceDiagram
    participant Docker
    participant InitScript
    participant Alembic
    participant SeedData
    participant Database
    participant App

    Docker->>InitScript: Container Start
    InitScript->>Database: Check Connection
    Database-->>InitScript: Connected
    InitScript->>Alembic: alembic upgrade head
    Alembic->>Database: Apply Migrations
    Database-->>Alembic: Success
    InitScript->>SeedData: python seed_data.py
    SeedData->>Database: Insert Initial Data
    Database-->>SeedData: Success
    InitScript->>App: Start FastAPI Server
```

## Components and Interfaces

### 1. Alembic Configuration

**File**: `ruoyi-fastapi-backend/alembic.ini`

Enhanced configuration for async SQLAlchemy:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME
```

**File**: `ruoyi-fastapi-backend/alembic/env.py`

Key functions:
- `run_migrations_offline()`: Generate SQL without database connection
- `run_migrations_online()`: Apply migrations to database using async engine
- `get_url()`: Load database URL from environment configuration

Configuration requirements:
- Import all ORM models to ensure Alembic detects schema
- Use async engine from `config/database.py`
- Support both MySQL and PostgreSQL connection strings
- Include custom naming conventions for constraints

### 2. Initial Migration Generator

**Component**: `InitialMigrationGenerator`

**Purpose**: Generate comprehensive initial migration from existing ORM models

**Key Functions**:

```python
async def generate_initial_migration() -> str:
    """
    Generate initial migration script from all ORM models.
    
    Returns:
        str: Path to generated migration file
    """
    # Import all DO models
    # Run alembic revision --autogenerate
    # Return migration file path
```

**Implementation Strategy**:
1. Scan `module_admin/entity/do/` for all SQLAlchemy models
2. Import models to populate MetaData
3. Execute `alembic revision --autogenerate -m "Initial migration"`
4. Post-process migration to add idempotency checks

**Idempotency Pattern**:

```python
def upgrade() -> None:
    # Check if table exists before creating
    bind = op.get_bind()
    inspector = inspect(bind)
    
    if 'sys_user' not in inspector.get_table_names():
        op.create_table('sys_user', ...)
    
    if 'sys_role' not in inspector.get_table_names():
        op.create_table('sys_role', ...)
```

### 3. Seed Data Manager

**File**: `ruoyi-fastapi-backend/scripts/seed_data.py`

**Class**: `SeedDataManager`

**Interface**:

```python
class SeedDataManager:
    def __init__(self, env: str = 'dev'):
        """Initialize seed data manager for specific environment."""
        self.env = env
        self.session: AsyncSession = None
    
    async def seed_all(self, reset: bool = False) -> None:
        """Execute all seed data operations."""
        if reset:
            await self.clear_data()
        
        await self.seed_users()
        await self.seed_roles()
        await self.seed_menus()
        await self.seed_dicts()
        await self.seed_config()
        
        if self.env == 'dev':
            await self.seed_test_data()
    
    async def seed_users(self) -> None:
        """Create default admin user."""
        # Check if admin exists
        # Create admin with hashed password
    
    async def seed_roles(self) -> None:
        """Create system roles."""
        # Create admin role
        # Create common user role
    
    async def seed_menus(self) -> None:
        """Create menu structure."""
        # Create parent menus
        # Create child menus with proper ordering
    
    async def seed_dicts(self) -> None:
        """Create dictionary data."""
        # Create dict types
        # Create dict data entries
    
    async def seed_config(self) -> None:
        """Create system configuration."""
        # Create config parameters
    
    async def seed_test_data(self) -> None:
        """Create test data for development."""
        # Create test projects
        # Create test devices
        # Create test protocols
    
    async def clear_data(self) -> None:
        """Clear all seed data (for reset)."""
        # Delete in reverse dependency order
```

**Seed Data Structure**:

```python
# Data organized by entity type
ADMIN_USER = {
    'user_name': 'admin',
    'nick_name': 'Administrator',
    'password': hash_password('admin123'),
    'email': 'admin@example.com',
    'phonenumber': '15888888888',
    'sex': '0',
    'status': '0',
    'create_by': 'system',
    'create_time': datetime.now()
}

ROLES = [
    {
        'role_name': 'Administrator',
        'role_key': 'admin',
        'role_sort': 1,
        'status': '0',
        'create_by': 'system'
    },
    {
        'role_name': 'Common User',
        'role_key': 'common',
        'role_sort': 2,
        'status': '0',
        'create_by': 'system'
    }
]

MENUS = [
    # System Management
    {
        'menu_name': 'System Management',
        'parent_id': 0,
        'order_num': 1,
        'path': 'system',
        'component': None,
        'menu_type': 'M',
        'visible': '0',
        'status': '0',
        'icon': 'system'
    },
    # User Management
    {
        'menu_name': 'User Management',
        'parent_id': 1,  # System Management
        'order_num': 1,
        'path': 'user',
        'component': 'system/user/index',
        'menu_type': 'C',
        'visible': '0',
        'status': '0',
        'perms': 'system:user:list',
        'icon': 'user'
    }
    # ... more menus
]
```

**Idempotency Strategy**:

```python
async def seed_users(self) -> None:
    # Check if admin already exists
    result = await self.session.execute(
        select(SysUser).where(SysUser.user_name == 'admin')
    )
    if result.scalar_one_or_none():
        logger.info("Admin user already exists, skipping")
        return
    
    # Create admin user
    admin = SysUser(**ADMIN_USER)
    self.session.add(admin)
    await self.session.commit()
    logger.info("Created admin user")
```

### 4. Database Management CLI

**File**: `ruoyi-fastapi-backend/scripts/db_migrate.sh`

**Commands**:

```bash
#!/bin/bash

# Database migration management script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

# Load environment
ENV="${ENV:-dev}"
source .env.$ENV

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

case "$1" in
    create)
        # Create new migration
        if [ -z "$2" ]; then
            echo "Error: Migration message required"
            echo "Usage: db_migrate.sh create <message>"
            exit 1
        fi
        alembic revision --autogenerate -m "$2"
        ;;
    
    upgrade)
        # Apply migrations
        REVISION="${2:-head}"
        alembic upgrade "$REVISION"
        ;;
    
    downgrade)
        # Rollback migrations
        STEPS="${2:--1}"
        alembic downgrade "$STEPS"
        ;;
    
    current)
        # Show current revision
        alembic current
        ;;
    
    history)
        # Show migration history
        alembic history --verbose
        ;;
    
    reset)
        # Reset database
        echo "WARNING: This will drop all tables and re-initialize the database"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            alembic downgrade base
            alembic upgrade head
            python scripts/seed_data.py --env "$ENV"
            echo "Database reset complete"
        else
            echo "Reset cancelled"
        fi
        ;;
    
    stamp)
        # Stamp database with revision
        if [ -z "$2" ]; then
            echo "Error: Revision required"
            echo "Usage: db_migrate.sh stamp <revision>"
            exit 1
        fi
        alembic stamp "$2"
        ;;
    
    *)
        echo "Usage: db_migrate.sh {create|upgrade|downgrade|current|history|reset|stamp}"
        echo ""
        echo "Commands:"
        echo "  create <message>     Create new migration"
        echo "  upgrade [revision]   Apply migrations (default: head)"
        echo "  downgrade [steps]    Rollback migrations (default: -1)"
        echo "  current              Show current revision"
        echo "  history              Show migration history"
        echo "  reset                Drop all tables and re-initialize"
        echo "  stamp <revision>     Mark database as being at revision"
        exit 1
        ;;
esac
```

### 5. Docker Integration

**File**: `ruoyi-fastapi-backend/docker-entrypoint.sh`

```bash
#!/bin/bash

set -e

echo "Starting database initialization..."

# Wait for database to be ready
echo "Waiting for database..."
python scripts/wait_for_db.py

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Seed data
echo "Seeding initial data..."
python scripts/seed_data.py --env "${APP_ENV:-prod}"

echo "Database initialization complete"

# Start application
echo "Starting FastAPI application..."
exec "$@"
```

**File**: `ruoyi-fastapi-backend/scripts/wait_for_db.py`

```python
"""Wait for database to be ready."""
import asyncio
import sys
from sqlalchemy import text
from config.database import async_engine

async def wait_for_db(max_retries: int = 30, delay: int = 2):
    """Wait for database connection."""
    for attempt in range(max_retries):
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("Database is ready!")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Database not ready - {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
    
    print("Failed to connect to database")
    return False

if __name__ == "__main__":
    result = asyncio.run(wait_for_db())
    sys.exit(0 if result else 1)
```

**Updated docker-compose.yml**:

```yaml
version: '3.8'

services:
  backend:
    build: ./ruoyi-fastapi-backend
    container_name: ruoyi-backend
    entrypoint: ["/app/docker-entrypoint.sh"]
    command: ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
    environment:
      - APP_ENV=prod
      - DATABASE_URL=mysql+aiomysql://root:password@db:3306/ruoyi-fastapi
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./ruoyi-fastapi-backend/vf_admin:/app/vf_admin
    # Remove SQL file volume mount
    
  db:
    image: mysql:5.7
    container_name: ruoyi-db
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=ruoyi-fastapi
      - MYSQL_CHARACTER_SET_SERVER=utf8mb4
      - MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci
    volumes:
      - db_data:/var/lib/mysql
    # Remove SQL file initialization
    
  redis:
    image: redis:alpine
    container_name: ruoyi-redis

volumes:
  db_data:
```

### 6. Migration Testing Framework

**File**: `ruoyi-fastapi-backend/scripts/test_migrations.py`

```python
"""Test migration scripts for correctness."""
import asyncio
from sqlalchemy import create_engine, inspect, text
from alembic import command
from alembic.config import Config

class MigrationTester:
    def __init__(self, test_db_url: str):
        self.test_db_url = test_db_url
        self.alembic_cfg = Config("alembic.ini")
        self.alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
    
    async def test_upgrade_downgrade(self) -> bool:
        """Test that migrations can upgrade and downgrade."""
        try:
            # Upgrade to head
            command.upgrade(self.alembic_cfg, "head")
            
            # Get current revision
            command.current(self.alembic_cfg)
            
            # Downgrade one step
            command.downgrade(self.alembic_cfg, "-1")
            
            # Upgrade back
            command.upgrade(self.alembic_cfg, "+1")
            
            return True
        except Exception as e:
            print(f"Migration test failed: {e}")
            return False
    
    async def test_idempotency(self) -> bool:
        """Test that migrations are idempotent."""
        try:
            # Apply migrations twice
            command.upgrade(self.alembic_cfg, "head")
            command.upgrade(self.alembic_cfg, "head")
            return True
        except Exception as e:
            print(f"Idempotency test failed: {e}")
            return False
    
    async def compare_schemas(self, before_url: str, after_url: str) -> dict:
        """Compare database schemas."""
        before_engine = create_engine(before_url)
        after_engine = create_engine(after_url)
        
        before_inspector = inspect(before_engine)
        after_inspector = inspect(after_engine)
        
        differences = {
            'added_tables': [],
            'removed_tables': [],
            'modified_tables': []
        }
        
        before_tables = set(before_inspector.get_table_names())
        after_tables = set(after_inspector.get_table_names())
        
        differences['added_tables'] = list(after_tables - before_tables)
        differences['removed_tables'] = list(before_tables - after_tables)
        
        return differences
```

## Data Models

### Migration History Model

Alembic automatically manages the `alembic_version` table:

```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
```

### Seed Data Models

All seed data uses existing ORM models from `module_admin/entity/do/`:

- `SysUser`: User accounts
- `SysRole`: User roles
- `SysMenu`: Menu structure
- `SysDept`: Department structure
- `SysDict`: Dictionary data
- `SysConfig`: System configuration
- `SysRoleMenu`: Role-menu associations
- `SysUserRole`: User-role associations

No new models are required; seed data populates existing schema.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I identified the following patterns:

**Redundancies Eliminated:**
- Multiple idempotency tests (1.3, 2.7, 3.4) can be consolidated into a single comprehensive idempotency property
- CLI command tests (4.1-4.6, 5.1-5.3) are all specific examples, not properties
- Documentation completeness checks (6.1-6.7, 7.4, 8.5, 9.5, 10.5, 11.5, 12.5) are all examples
- Database compatibility tests (8.1-8.4) are specific examples for MySQL and PostgreSQL

**Properties Retained:**
- Migration generation completeness (1.1)
- Schema correctness after migration (1.2)
- Idempotency (consolidated from 1.3, 2.7)
- Migration structure validation (1.4)
- Menu hierarchy integrity (2.3)
- Transaction atomicity on error (2.8, 5.4, 12.1)
- Foreign key dependency ordering (5.7)
- CLI error handling (4.7)
- Data preservation during migration (10.3)
- Migration reversibility (11.2)
- Error logging completeness (12.2)

### Correctness Properties

**Property 1: Migration Generation Completeness**

*For any* set of ORM models in the application, when Alembic generates an initial migration, the migration script should include CREATE TABLE statements for all models.

**Validates: Requirements 1.1**

**Property 2: Schema Correctness After Migration**

*For any* ORM model, after applying migrations to an empty database, introspecting the database schema should reveal tables, columns, indexes, and foreign keys that match the ORM model definitions.

**Validates: Requirements 1.2**

**Property 3: Migration and Seed Data Idempotency**

*For any* database state, applying migrations or seed data multiple times should produce the same final state as applying them once, without errors or duplicate data.

**Validates: Requirements 1.3, 2.7, 3.4**

**Property 4: Migration Script Structure**

*For any* generated migration file, the file should contain both an upgrade() function and a downgrade() function, and both should be syntactically valid Python code.

**Validates: Requirements 1.4**

**Property 5: Menu Hierarchy Integrity**

*For any* menu structure created by seed data, all child menus should reference valid parent menu IDs, and there should be no circular references in the parent-child relationships.

**Validates: Requirements 2.3**

**Property 6: Transaction Atomicity on Error**

*For any* seed data operation or migration that encounters an error, either all changes should be committed or all changes should be rolled back, with no partial data persisted.

**Validates: Requirements 2.8, 5.4, 12.1**

**Property 7: Foreign Key Dependency Ordering**

*For any* set of seed data with foreign key relationships, when data is inserted, parent records should always be inserted before child records that reference them.

**Validates: Requirements 5.7**

**Property 8: CLI Error Handling Consistency**

*For any* CLI command that fails, the command should exit with a non-zero status code and display an error message that includes the failure reason.

**Validates: Requirements 4.7**

**Property 9: Data Preservation During Migration**

*For any* database with existing data, after applying migrations, all data that existed before the migration should still exist and be accessible with the same values.

**Validates: Requirements 10.3**

**Property 10: Migration Reversibility**

*For any* migration, applying upgrade() followed by downgrade() should return the database schema to its original state (round-trip property).

**Validates: Requirements 11.2**

**Property 11: Error Logging Completeness**

*For any* migration or seed data operation that fails, the error log should include the SQL statement or operation that caused the failure.

**Validates: Requirements 12.2**

## Error Handling

### Migration Errors

**Scenario**: Migration fails during upgrade

**Handling**:
1. Alembic automatically wraps migrations in transactions
2. On failure, transaction is rolled back
3. Error message includes:
   - Failed migration revision
   - SQL statement that failed
   - Database error message
4. Database remains at previous revision
5. User can fix migration and retry

**Example Error Message**:
```
ERROR: Migration failed at revision abc123def456
SQL: CREATE TABLE sys_new_table (...)
Database Error: Duplicate column name 'user_id'
Database remains at revision: xyz789abc012
```

### Seed Data Errors

**Scenario**: Seed data insertion fails

**Handling**:
1. All seed operations wrapped in async transaction
2. On failure, rollback entire transaction
3. Error message includes:
   - Entity type being inserted
   - Specific record that failed
   - Database error
4. Database remains empty or at previous state
5. User can fix seed data and retry

**Example Error Message**:
```
ERROR: Seed data failed while inserting SysRole
Record: {'role_name': 'Admin', 'role_key': 'admin'}
Database Error: Duplicate entry 'admin' for key 'role_key'
All changes rolled back
```

### Docker Initialization Errors

**Scenario**: Database initialization fails in Docker container

**Handling**:
1. docker-entrypoint.sh uses `set -e` to exit on any error
2. Each step logs progress
3. On failure:
   - Error logged to container logs
   - Container exits with non-zero code
   - Docker Compose shows failed container
4. User can inspect logs and fix issue

**Example Log Output**:
```
Starting database initialization...
Waiting for database...
Database is ready!
Running database migrations...
ERROR: Migration failed
Container exiting with code 1
```

### Concurrent Migration Attempts

**Scenario**: Multiple containers try to run migrations simultaneously

**Handling**:
1. Alembic uses database-level locking on alembic_version table
2. First container acquires lock and runs migrations
3. Subsequent containers wait for lock
4. After first container completes, others detect migrations already applied
5. All containers proceed to start application

**Note**: This is handled by Alembic's built-in locking mechanism, no custom code required.

### Schema Drift Detection

**Scenario**: Database schema differs from ORM models

**Handling**:
1. Run `alembic revision --autogenerate` to detect differences
2. Alembic compares database schema to ORM metadata
3. Generates migration with detected changes
4. Developer reviews migration before applying
5. If drift is unintentional, investigate root cause

**Prevention**:
- Always use migrations for schema changes
- Never modify database schema manually
- Run `alembic check` in CI/CD to detect drift

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific seed data records (admin user, specific roles)
- CLI command execution with specific arguments
- Docker initialization sequence
- Documentation content verification
- File organization checks

**Property Tests**: Focus on universal properties across all inputs
- Migration generation for any set of ORM models
- Schema correctness for any model
- Idempotency for any operation
- Transaction atomicity for any error
- Foreign key ordering for any data set
- Migration reversibility for any migration

### Property-Based Testing Configuration

**Library**: Use `hypothesis` for Python property-based testing

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tag format: `# Feature: database-migration-modernization, Property N: <property text>`

**Example Property Test**:

```python
from hypothesis import given, strategies as st
import pytest

# Feature: database-migration-modernization, Property 3: Migration and Seed Data Idempotency
@given(st.integers(min_value=1, max_value=5))
async def test_migration_idempotency(num_applications: int):
    """For any number of migration applications, result should be the same."""
    # Setup: Create test database
    test_db = await create_test_database()
    
    # Apply migrations multiple times
    for _ in range(num_applications):
        await run_migrations(test_db)
    
    # Get final schema
    final_schema = await introspect_schema(test_db)
    
    # Apply one more time
    await run_migrations(test_db)
    
    # Schema should be unchanged
    assert await introspect_schema(test_db) == final_schema
    
    # Cleanup
    await drop_test_database(test_db)
```

### Unit Test Examples

**Test: Admin User Creation**
```python
async def test_seed_admin_user():
    """Verify admin user is created with correct credentials."""
    db = await create_test_database()
    await run_migrations(db)
    await seed_data(db, env='prod')
    
    user = await db.execute(
        select(SysUser).where(SysUser.user_name == 'admin')
    )
    user = user.scalar_one()
    
    assert user.user_name == 'admin'
    assert verify_password('admin123', user.password)
    assert user.status == '0'
```

**Test: CLI Create Command**
```python
def test_cli_create_migration():
    """Verify db_migrate.sh create generates migration file."""
    result = subprocess.run(
        ['./scripts/db_migrate.sh', 'create', 'test_migration'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert 'test_migration' in result.stdout
    
    # Verify migration file exists
    migration_files = list(Path('alembic/versions').glob('*_test_migration.py'))
    assert len(migration_files) == 1
```

**Test: Docker Initialization**
```python
def test_docker_initialization():
    """Verify Docker container initializes database correctly."""
    # Start container
    subprocess.run(['docker-compose', 'up', '-d', 'backend'])
    
    # Wait for initialization
    time.sleep(10)
    
    # Check container is running
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=ruoyi-backend'],
        capture_output=True,
        text=True
    )
    assert 'ruoyi-backend' in result.stdout
    
    # Check database has tables
    # Connect to database and verify schema
    # ...
```

### Integration Tests

**Test: Full Migration Workflow**
```python
async def test_full_migration_workflow():
    """Test complete workflow from ORM changes to database update."""
    # 1. Modify ORM model (add column)
    # 2. Generate migration
    # 3. Review migration
    # 4. Apply migration
    # 5. Verify schema updated
    # 6. Rollback migration
    # 7. Verify schema reverted
```

**Test: Seed Data Dependencies**
```python
async def test_seed_data_foreign_keys():
    """Verify seed data respects foreign key constraints."""
    db = await create_test_database()
    await run_migrations(db)
    
    # Seed data should succeed
    await seed_data(db, env='dev')
    
    # Verify all foreign keys are valid
    # Check user_role references valid user and role
    # Check role_menu references valid role and menu
    # etc.
```

### Test Coverage Goals

- **Unit Test Coverage**: 80%+ of seed data and CLI code
- **Property Test Coverage**: All 11 correctness properties
- **Integration Test Coverage**: Key workflows (migration, seeding, Docker init)
- **Documentation Tests**: Verify all documentation files exist and contain required content

### Continuous Integration

**CI Pipeline Steps**:
1. Provision isolated test databases and clean up after each job
2. Run unit tests
3. Run property tests (100 iterations each)
4. Test migrations on MySQL
5. Test migrations on PostgreSQL
6. Test Docker initialization
7. Verify documentation completeness
8. Check for SQL file references in code

**CI Notes**:
- If property tests are heavy, run them in a dedicated pipeline or scheduled job
- Keep test database URLs configurable for local and CI environments

**Pre-commit Hooks**:
- Run `alembic check` to detect schema drift
- Verify migration files have both upgrade and downgrade
- Check that new migrations are added to git

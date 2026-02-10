# Config And Infra Reference

## Table Of Contents

1. Configuration sources
2. Middleware and tracing
3. Exception and response pipeline
4. DB session and transaction behavior
5. Migration workflow
6. Validation and test commands
7. Infra guardrails

## 1. Configuration Sources

Primary configuration module: `ruoyi-fastapi-backend/config/env.py`

Key exported configs:

- `AppConfig`
- `JwtConfig`
- `DataBaseConfig`
- `RedisConfig`
- `CacheConfig`
- `AuditConfig`
- `ErrorHandlingConfig`

Config loading behavior:

- Loads `.env.{APP_ENV}` (defaults to `.env.dev`)
- Supports CLI `--env` outside uvicorn
- Uses cached singleton access via `GetConfig`

## 2. Middleware And Tracing

Middleware assembly is in `ruoyi-fastapi-backend/middlewares/handle.py`.

Registered order:

1. CORS
2. GZip
3. AuditContext middleware
4. Trace middleware

Trace helpers are exported from `middlewares/trace_middleware`.

## 3. Exception And Response Pipeline

- Exception classes: `ruoyi-fastapi-backend/exceptions/exception.py`
- Global handlers: `ruoyi-fastapi-backend/exceptions/handle.py`
- Response utility: `ruoyi-fastapi-backend/utils/response_util.py`

Conventions:

1. Success responses should use `ResponseUtil.success(...)`.
2. Business/system errors should raise typed project exceptions.
3. Global handlers map exceptions to RFC 7807 style payloads.

## 4. DB Session And Transaction Behavior

- Session dependency: `ruoyi-fastapi-backend/config/get_db.py`
- Engine/sessionmaker: `ruoyi-fastapi-backend/config/database.py`
- Transaction helper: `ruoyi-fastapi-backend/utils/transaction_manager.py`

Behavior summary:

1. `get_db()` yields request-scoped `AsyncSession` and handles commit/rollback.
2. Service writes should usually use `@transactional()`.
3. Avoid mixing ad-hoc transaction logic into controllers.

## 5. Migration Workflow

Migration folder: `ruoyi-fastapi-backend/alembic/versions/`

Common commands:

```bash
cd ruoyi-fastapi-backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

Rules:

1. Any DO/schema change should include a migration.
2. Prefer idempotent migrations for legacy table repairs.
3. Keep downgrade behavior valid unless explicitly out of scope.

## 6. Validation And Test Commands

Recommended skill wrapper:

```bash
bash .cursor/skills/backend-conventions/scripts/validate.sh --changed
bash .cursor/skills/backend-conventions/scripts/validate.sh --full --with-mypy --with-tests
```

Equivalent raw commands (inside `ruoyi-fastapi-backend`):

```bash
ruff check .
ruff format --check .
mypy module_admin config utils exceptions middlewares module_generator module_task sub_applications server.py app.py
pytest -q
```

## 7. Infra Guardrails

1. No `eval`/`exec` in backend code.
2. Avoid new `print(...)` debugging; use project logging.
3. Preserve async behavior on request paths.
4. Do not bypass existing exception/response pipeline with custom ad-hoc error payloads.

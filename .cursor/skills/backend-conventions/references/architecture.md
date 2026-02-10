# Architecture Reference

## Table Of Contents

1. Request lifecycle
2. Layer contracts
3. Data access conventions
4. Model conventions (DO/VO)
5. Response and error conventions
6. Transaction boundaries
7. Brownfield decision checklist

## 1. Request Lifecycle

Typical HTTP flow:

1. Middlewares (`middlewares/handle.py`): CORS -> GZip -> AuditContext -> Trace
2. Router/controller (`module_admin/controller/*`)
3. Service (`module_admin/service/*`)
4. Repository (`module_admin/repository/*`)
5. DB session from `get_db()` (`config/get_db.py`)
6. Response via module-local response pattern

Trace/request id is available from `middlewares.trace_middleware` and included in responses.

## 2. Layer Contracts

### Controller

- Owns route definitions, `Depends(...)`, permission checks, and log annotations.
- Should not contain raw SQL query construction.
- Should preserve local endpoint semantics and permission key style.

### Service

- Owns business rules and orchestration.
- Write paths typically use `@transactional()`.
- Naming and return style are module-local; preserve existing style in the touched module.

### Repository

- Owns persistence queries and CRUD helpers.
- `BaseRepository` provides common methods (`get_by_id`, `find_all`, `find_one`, `add`, `update`, `delete_by_id`, `count`, ...).
- New data access should go through repository layer.

## 3. Data Access Conventions

1. Prefer repository imports from `module_admin/repository/__init__.py`.
2. Do not add new DAO dependencies in production code.
3. DAO modules can remain for compatibility and tests; avoid incidental migrations.
4. Keep query logic out of controller methods.

## 4. Model Conventions (DO/VO)

### DO models (`module_admin/entity/do`)

- SQLAlchemy models for persistence.
- Shared mixins and base classes are in `module_admin/entity/do/base.py`.
- Existing tables may still carry legacy fields while newer models use soft-delete mixins.

### VO models (`module_admin/entity/vo`)

- Pydantic models for request/response.
- `CamelModelBase` in `module_admin/entity/vo/base.py` handles snake_case <-> camelCase compatibility.
- Keep API field compatibility unless request explicitly changes contract.

## 5. Response And Error Conventions

1. Keep response shape consistent with neighboring endpoints.
2. For failures, raise typed exceptions from `exceptions/exception.py`.
3. Global handlers in `exceptions/handle.py` translate exceptions into RFC 7807 style error payloads.
4. Do not swallow exceptions silently.

## 6. Transaction Boundaries

1. Primary pattern: annotate service write operations with `@transactional()`.
2. `get_db()` manages request-scoped commit/rollback.
3. Keep transaction scope in service/repository; avoid manual transaction orchestration in controllers.

## 7. Brownfield Decision Checklist

Before changing architecture shape, answer yes/no:

1. Does adjacent module already follow a different but working pattern?
2. Will this change alter endpoint response schema or permission behavior?
3. Will this change require coordinated edits across multiple controllers/services/tests?

If any answer is yes and user did not request refactor, keep changes minimal and local.

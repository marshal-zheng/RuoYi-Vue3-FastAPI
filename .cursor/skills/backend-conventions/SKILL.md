---
name: backend-conventions
description: Adaptive backend conventions for ruoyi-fastapi-backend (FastAPI + SQLAlchemy async). Use when creating or modifying files under ruoyi-fastapi-backend/, including controllers, services, repositories, entities, config, middleware, Alembic migrations, and tests. Prioritize local module patterns over hardcoded business assumptions.
---

# Backend Conventions

Adaptive workflow for `ruoyi-fastapi-backend/` so AI edits stay fast, precise, and robust when business modules are added, removed, or renamed.

## Project Baseline

| Layer | Baseline |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x async |
| Validation | Pydantic v2 |
| DB Migration | Alembic |
| Cache | Redis (`redis.asyncio`) |
| Scheduler | APScheduler |
| Test | pytest + pytest-asyncio + pytest-xdist |
| Static checks | Ruff + mypy |

## AI Execution Contract

Follow this order on every backend task:

1. Read nearby code first
- Inspect sibling files in the touched module (`controller/service/repository/entity/do/entity/vo/tests`).
- Identify local patterns before writing code.

2. Detect local style before enforcing conventions
- Service naming: follow existing style in that module (`*_services` or verb-style).
- Response boundary: follow existing local pattern (controller-wrapped or service-returned payloads).
- Model naming: follow local DO/VO class conventions already used in touched files.
- Do not force architecture migration unless user explicitly requests refactor.

3. Implement minimal, reversible diffs
- Keep scope tied to the user request.
- Avoid broad renames, module moves, or mass rewrites.

4. Validate before finish
- Run `bash .cursor/skills/backend-conventions/scripts/validate.sh --changed`.
- Use `--full --with-mypy --with-tests` for release-level validation.

## Source Of Truth Priority

1. Touched module files (highest priority)
2. Shared foundations:
- `ruoyi-fastapi-backend/config/`
- `ruoyi-fastapi-backend/exceptions/`
- `ruoyi-fastapi-backend/utils/response_util.py`
- `ruoyi-fastapi-backend/utils/transaction_manager.py`
- `ruoyi-fastapi-backend/module_admin/entity/do/base.py`
- `ruoyi-fastapi-backend/module_admin/entity/vo/base.py`
3. This skill and references (fallback guidance)

If this skill conflicts with the touched module, follow the touched module.

## Architecture Guardrails

1. Controller layer
- Own routing, `Depends(...)`, permission checks, and log annotations.
- Do not add raw SQL or heavy business logic to controller methods.

2. Service layer
- Keep business logic and transaction boundaries in services.
- Prefer `@transactional()` on write paths.
- Keep return style consistent with module-local convention.

3. Repository and data access
- New data access should prefer `module_admin/repository/*`.
- Do not introduce new DAO usage in production code.
- Existing DAO files can remain for compatibility/tests.

4. Models (DO/VO)
- DO models are persistence mappings under `entity/do`.
- VO models are API models under `entity/vo`.
- Preserve snake_case internal fields and camelCase API compatibility.

5. Responses and errors
- Keep API response behavior consistent with neighboring endpoints.
- Prefer typed exceptions from `exceptions/exception.py` for failures.
- Avoid swallowing exceptions silently.

## Future-Proofing Policy

1. Never hardcode business module names as mandatory architecture rules.
2. Module additions/removals should require zero changes to skill semantics.
3. Use capability-based rules (layering, transactions, validation, migration) instead of feature-name rules.

## Recommended Defaults For New Modules

Use these only when there is no local precedent:

1. Service write methods use `@transactional()`.
2. Service methods return pure data objects; controller wraps HTTP response.
3. DO class names use `*DO`; VO class names use `*Model`.
4. File names stay snake_case.

## Security And Reliability

1. Never add `eval()` or `exec()`.
2. Do not add `print()` debugging; use project logging.
3. Avoid raw SQL string interpolation with user input.
4. Keep async paths async; avoid blocking calls on request path.
5. When changing schema or DO fields, pair with an Alembic migration.

## Migration Rules

1. Schema changes require Alembic migration under `ruoyi-fastapi-backend/alembic/versions/`.
2. Prefer idempotent migration logic when touching legacy tables.
3. Keep downgrade path valid unless explicitly out of scope.

## Validation Commands

```bash
# Fast iteration (default)
bash .cursor/skills/backend-conventions/scripts/validate.sh --changed

# Full validation before merge/release
bash .cursor/skills/backend-conventions/scripts/validate.sh --full --with-mypy --with-tests
```

## References

| File | Use when |
|---|---|
| [references/brownfield-map.md](references/brownfield-map.md) | Detecting local patterns before editing |
| [references/architecture.md](references/architecture.md) | Layer responsibilities, request lifecycle, transaction boundaries |
| [references/config-and-infra.md](references/config-and-infra.md) | Config, middleware, exception handling, migration and test tooling |

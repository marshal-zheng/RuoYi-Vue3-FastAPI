# Protocol Contract Guide

## Naming Rules

- Repository contracts use `I<ClassName>` format, e.g. `IUserRepository`.
- Service contracts use `I<ClassName>` format, e.g. `IUserService`.
- External contracts use capability names, e.g. `IRedisClient`, `ICacheProvider`.
- New contracts must be added into `ports/<domain>.py` and exported from `ports/__init__.py`.

## Organization Rules

- `ports/repositories.py`: cross-module repository contracts.
- `ports/services.py`: cross-module service contracts.
- `ports/external.py`: infrastructure contracts (redis/cache/audit/event bus).
- Context-private contracts should stay inside context modules (`modules/<context>/ports.py`) after P3 migration.
- Cross-context reusable contracts must remain in shared `ports` package.

## One-Hop Lookup Rule

- Entry point: `from ports import ...`.
- Contract definition lookup:
  - First hop: `ports/__init__.py` export list.
  - Second hop (only when needed): concrete contract file (`ports/repositories.py`, `ports/services.py`, `ports/external.py`).
- Review check: every new `I*` contract must be reachable from `ports/__init__.py`.

## Usage Rules

- Service layer variables and constructor dependencies should be typed against `I*` contracts.
- Avoid type annotations that bind to concrete repository/service implementations.
- Runtime behavior must remain unchanged; contracts are type boundaries, not behavior wrappers.

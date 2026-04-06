# Repository Layer Policy

## Purpose

To reduce architecture drift, runtime code must use the repository layer as the only data access abstraction.

## Rule

1. Runtime modules MUST NOT import `module_admin.dao`.
2. New data access logic MUST be implemented under `module_admin/repository`.
3. Legacy DAO compatibility paths are decommissioned; `module_admin/dao` is removed.

## Phase 6 Status

- Runtime DAO imports have been removed from active code paths.
- Integration smoke tests no longer validate DAO imports as a supported path.
- `module_admin/dao`, `module_generator/dao`, and `tests/unit/dao` have been removed.
- Migration notes: `/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/specs/backend-architecture-p0-foundation/dao-migration-notes.md`

## Enforcement

当前仓库不再保留独立的 DAO 导入治理脚本。

若运行时代码重新引入 `module_admin.dao`，应通过仓储层评审、针对性回归测试与本策略文档一起发现并阻断。

## Scope

Checked runtime paths:
- `module_admin/`
- `module_generator/`
- `module_task/`
- `config/`
- `middlewares/`
- `exceptions/`
- `utils/`
- `server.py`
- `app.py`

Excluded paths:
- `tests/`
- `alembic/`
- `docs/`
- `scripts/`
- `module_admin/dao/`

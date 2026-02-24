# /update-codemaps - Update Code Maps

Analyze the codebase structure and update architecture documentation.

## Scope

Scan the following top-level modules and generate concise code maps:

| File | Content |
|------|---------|
| `docs/codemaps/backend.md` | Backend layered architecture: config, module_admin (controller → service → repository → dao → entity), module_generator, module_task, middlewares, exceptions, utils |
| `docs/codemaps/frontend.md` | Frontend structure: api, views, components (common + business), store, router, plugins, utils, layout, mocks, directives |
| `docs/codemaps/data.md` | Data models (entity/do/vo), Alembic migrations, seed data, database config |
| `docs/codemaps/overview.md` | High-level architecture overview linking backend ↔ frontend, key entry points (`app.py`, `main.ts`), Docker/CI setup |

## What to Capture

For each module, document:

- **Purpose** - one-line description
- **Key files** - entry points and important files only
- **Dependencies** - internal cross-module dependencies
- **Patterns** - architectural patterns in use (e.g., repository pattern, Pinia stores, composables)

## Rules

1. Focus on high-level structure, not implementation details
2. Compute diff percentage against the previous version
3. If changes > 30%, ask the user for approval before overwriting
4. Add a freshness timestamp (`Updated: YYYY-MM-DD`) at the top of each file
5. Keep each file under 200 lines - be concise

## Output

Save code maps to `docs/codemaps/` and a diff summary to `docs/codemaps/.diff-report.txt`.

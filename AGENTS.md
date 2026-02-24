# Repository Guidelines

## Project Structure & Module Organization
This repository is split into two primary modules:
- `ruoyi-fastapi-frontend/`: Vue 3 + TypeScript app (`src/` for code, `tests/` for Vitest suites, `public/` for static assets).
- `ruoyi-fastapi-backend/`: FastAPI service (`module_admin/`, `module_generator/`, `module_task/` for domain code, `alembic/` for migrations, `tests/` for unit/integration tests).

Shared and support files live in:
- `scripts/` (root automation like `setup.sh`, `start.sh`)
- `docs/` (specs, codemaps, reports)
- `.github/workflows/ci.yml` and `.gitlab-ci.yml` (CI checks)

## Build, Test, and Development Commands
- `./scripts/setup.sh`: one-time local environment bootstrap (macOS-focused).
- `./scripts/start.sh`: start backend + frontend for daily development.
- `cd ruoyi-fastapi-frontend && yarn dev`: run frontend dev server.
- `cd ruoyi-fastapi-frontend && yarn build:prod`: production build.
- `cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check && yarn test:run`: frontend quality gate.
- `cd ruoyi-fastapi-backend && python app.py --env=dev`: run backend locally.
- `cd ruoyi-fastapi-backend && pytest tests/ -v`: run backend tests.
- `cd ruoyi-fastapi-backend && ruff check . && ruff format --check .`: backend lint/format check.

## Coding Style & Naming Conventions
- Python (backend): Ruff-managed style, 120-char line length, single quotes, Python 3.11 target.
- TypeScript/Vue (frontend): ESLint + Prettier, 2-space indentation, `singleQuote: true`, semicolons on, `printWidth: 100`.
- Test names:
  - Backend: `test_*.py`, classes `Test*`, functions `test_*`.
  - Frontend: `*.test.ts` / `*.spec.ts` under `src/` or `tests/`.
- Keep backend layering explicit: controller -> service -> repository.

## Testing Guidelines
- Frontend uses Vitest (`ruoyi-fastapi-frontend/vitest.config.ts`) with 70% coverage thresholds for lines/functions/branches/statements.
- Backend uses Pytest (`ruoyi-fastapi-backend/pytest.ini`) with unit/integration markers and coverage reporting to `tests/coverage/`.
- Prefer focused tests for changed modules before full-suite runs.

## Commit & Pull Request Guidelines
- Follow Conventional Commits, with Chinese descriptions (example: `feat(用户管理): 添加角色配置功能`).
- Common commit types in history: `feat`, `fix`, `chore`, `style`.
- PRs should include:
  - clear change summary and affected paths
  - linked issue/task ID
  - test evidence (commands run and results)
  - screenshots or API examples when UI/contract behavior changes
  - migration notes when `alembic/` or SQL files are touched

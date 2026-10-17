# Repository Guidelines

This file applies to the repository root. There is no nested `AGENTS.md`. For daily start, this file takes precedence over README / `scripts/start.sh`.

## 方案选择与在研阶段约束

- **长期整体收益优先**：所有 Bug、需求、重构与优化，默认按正确性、真实业务适配、跨业务复用、长期维护成本和复杂度选择方案；不得默认把最小 diff、最快交付或沿用旧实现当成最优。非简单改动须简要说明选型依据、收益与代价，无需用户重复提醒。
- **先复用成熟方案**：先查仓库已有能力；涉及通用机制、架构或依赖取舍时，定向联网核对成熟社区方案的官方文档与源码，比较直接采用、借鉴设计和局部实现。已有合适能力优先复用，不重复自建基础设施；也不为使用某个库引入本轮不需要的整套机制。
- **在研阶段允许硬切**：当前业务与 ZXUI 均处于在研阶段。在已授权任务范围内，可直接替换或删除不合理的内部 API、架构和旧行为，不因硬切本身再次请求确认。兼容层、双轨、legacy 模式或弃用期必须有已确认的真实消费者、稳定对外契约或数据迁移要求作为依据；不得为假设消费者和历史包袱保留。
- **硬切必须完整收敛**：先查清受影响的真实调用，同步迁移相关业务、公开契约、文档和生成产物，移除已无用途的旧路径。硬切授权不包含破坏生产数据、覆盖无关工作区改动或未经授权的外部发布。
- **复杂度由证据驱动**：覆盖完整业务目标和已确认的扩展需求，选择其中最简单清晰的设计；不为假设场景增加配置组合、缓存体系、调度框架或多层适配。不把长期收益理解为默认大重构，也不以最小修补长期掩盖错误抽象。
- **先查后改，按不确定性验证**：先读真实调用、库实现和已有测试，查清根因与责任。代码已能精确证明的结论可直接给出依据；不确定边界再用最小探针或真实链路验证。明确区分静态判断、内存探针、真实业务验证和未验证项；修复后只补必要回归，不为接入或排查堆测试。
- **库与业务共同闭环**：通用机制问题优先修在 ZXUI，业务保留领域规则与流程。优先通过 `VITE_ZXUI_LOCAL=true`、`VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` 源码直连，用受影响的真实业务验证；不以业务补丁掩盖库缺陷，不以尚未发布 npm 阻塞本地联调。

## Project Structure & Module Organization
This repository is split into two primary modules:
- `ruoyi-fastapi-frontend/`: Vue 3 + TypeScript app (`src/` for code, `tests/` for Vitest suites, `public/` for static assets).
- `ruoyi-fastapi-backend/`: FastAPI service (`module_admin/`, `module_generator/`, `module_task/` for domain code, `alembic/` for migrations, `tests/` for unit/integration tests).

Shared and support files live in:
- `scripts/` (root automation like `setup.sh`, `start.sh`)
- `docs/` (specs, codemaps, reports)
- `.github/workflows/ci.yml` and `.gitlab-ci.yml` (CI checks)

## Daily Development Runtime (this workspace)
This machine does **not** run Homebrew MySQL. Daily MySQL is a **local Docker** container on this Mac.

- Container: `ruoyi-mysql-local` (bound to `127.0.0.1:3306`, not public)
- Image: `docker.1ms.run/library/mysql:8.0` (volume `ruoyi-mysql-local-data`)
- App config stays in `ruoyi-fastapi-backend/.env.dev`: `DB_HOST=127.0.0.1`, `DB_PORT=3306`, `DB_USERNAME=root`, `DB_PASSWORD=admin1234`, database `ruoyi-fastapi`
- Redis: existing `127.0.0.1:6379`. Do not start Homebrew Redis.
- Do **not** use `./scripts/start.sh` (it starts local brew MySQL).
- Do **not** `brew install/reinstall/services start mysql` on this Mac.
- Do **not** use `docker-compose-dev.yml` as the daily path (MySQL is `3307`, Redis/app ports do not match).
- Do **not** SSH-tunnel MySQL from 101 unless the user explicitly asks.

When the user asks to start the project (开发服务 / 前后端):
1. `docker start ruoyi-mysql-local` (create it once if missing; see below)
2. Backend: `cd ruoyi-fastapi-backend && ./venv/bin/python app.py --env=dev` (port `8088`)
3. Frontend: `cd ruoyi-fastapi-frontend && ./node_modules/.bin/vite --host 0.0.0.0 --port 80 --strictPort`
4. URLs: http://localhost:80 , API http://localhost:8088/docs
5. Login: `admin` / `admin123`

Create local MySQL (once):

```bash
docker run -d --name ruoyi-mysql-local --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=admin1234 -e MYSQL_DATABASE=ruoyi-fastapi -e TZ=Asia/Shanghai \
  -p 127.0.0.1:3306:3306 -v ruoyi-mysql-local-data:/var/lib/mysql \
  docker.1ms.run/library/mysql:8.0 \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci \
  --default-authentication-plugin=mysql_native_password
```

Empty local database only (schema first, then seed, then menus):

```bash
cd ruoyi-fastapi-backend
./venv/bin/python scripts/db.py wait-db
./venv/bin/python scripts/db.py dev-sync --invoked-by-startup   # schema; managed-data may fail until roles exist
./venv/bin/python scripts/db.py bootstrap-seed --env dev
./venv/bin/python scripts/db.py dev-sync --invoked-by-startup
```

## Build, Test, and Development Commands
- `./scripts/setup.sh`: one-time local environment bootstrap (macOS-focused). Do not use it to install MySQL on this Mac.
- `cd ruoyi-fastapi-frontend && yarn build:prod`: production build.
- `cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check && yarn test:run`: frontend quality gate.
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

## Frontend Debugging (Chrome DevTools MCP)
- Chrome DevTools MCP 已集成到本项目，启动时需确保 `--autoConnect` 参数已开启。
- 前端开发服务器端口是 `80`（见 Daily Development Runtime），不是默认 Vite `5173`。
- 前端 lint / type-check / test：`cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check && yarn test:run`

## 非仿真表单、弹框与主题约定

- 新增或修改表单弹框使用 `@/components/ui/FormDialog` 的 `useFormDialog({ columns, formRef, ... })`，同一返回值的 `dialogProps/dialogEvents`、`formProps`、`layoutProps` 分别绑定 ZxDialog、原生 ElForm、FormGrid。保留真实 FormInstance；FormGrid 只布局，整行字段用 `data-form-full`。
- 列数只声明一次，标签宽度、横向间距、响应式降列由业务布局策略统一维护；控件高度和纵向节奏消费 ZXUI density。不要在调用点写字段 span、label-width、gutter 或叠加 row-gap。
- 非表单弹框按内容选 `dialogSize` 预设；不用硬编码 width/height。必要限高使用 `dialogStyle.maxHeight`。只读详情使用描述列表，不为其包装表单。
- 主题由 `src/theme/zx-theme-packages.ts` 单一登记，构建端公开 deployment API 交付资产，偏好经统一入口交 Host/Provider。业务不要写核心 `--el-*`/`--zx-*` 值、猜 generated 路径或补写库公开类型。
- 非仿真原生输入统一用 ZxInput（下一主版本原生 input 语义）；数值步进、增强搜索是不同职责，不机械替换 ElInputNumber/ElSelect。生成器与手写表单遵循相同契约，运行 `yarn ui:standards` 检查。
- `src/views/project/simulation/**` 及其专用组件不属于本轮迁移或验收；共享组件覆盖非仿真消费者。完整范围、兼容边界及证据要求见 [ZXUI 表单弹框统一 spec](docs/specs/zxui-form-dialog-convergence/requirements.md)。

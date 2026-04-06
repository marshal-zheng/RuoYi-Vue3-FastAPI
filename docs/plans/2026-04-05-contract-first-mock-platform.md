# Contract-First Mock Platform Implementation Plan

**Goal:** Replace browser-runtime MSW fallback mocking with a contract-first platform where production builds talk only to explicit upstream services and test-time mocks are generated from the backend OpenAPI contract.
**Inputs:** `ruoyi-fastapi-frontend/src/main.ts`, `ruoyi-fastapi-frontend/src/mocks/**/*`, `ruoyi-fastapi-frontend/src/utils/http.ts`, `ruoyi-fastapi-frontend/vite.config.ts`, `ruoyi-fastapi-frontend/nginx.conf`, `ruoyi-fastapi-frontend/package.json`, `ruoyi-fastapi-backend/server.py`, `ruoyi-fastapi-backend/modules/identity/api/security_controller.py`, `ruoyi-fastapi-backend/module_admin/controller/simulation_controller.py`, `docs/plans/2026-03-02-frontend-mock-test-alignment.md`
**Scope Boundaries:** In scope: frontend runtime/network boundary cleanup, backend OpenAPI export, standalone HTTP mock server, generated MSW for tests, explicit demo WebSocket service, CI guardrails, and repository documentation. Out of scope: redesigning backend business logic, full simulation-engine parity in the demo stream service, Storybook adoption, and unrelated UI refactors.
**Assumptions:** Docker is available for the standalone HTTP mock server; backend OpenAPI can be exported from `server.app` without starting the full lifespan; demo real-time support only needs the message shapes already consumed by `useSimulationWebSocket`.

## Task List

### Task 1: Remove Runtime Browser Mocking and Normalize a Single API Prefix

**Files:**
- Create: `ruoyi-fastapi-frontend/.env.demo`
- Modify: `ruoyi-fastapi-frontend/.env.development`
- Modify: `ruoyi-fastapi-frontend/.env.production`
- Modify: `ruoyi-fastapi-frontend/src/main.ts`
- Modify: `ruoyi-fastapi-frontend/vite.config.ts`
- Modify: `ruoyi-fastapi-frontend/nginx.conf`
- Create: `ruoyi-fastapi-frontend/nginx.demo.conf`
- Modify: `ruoyi-fastapi-frontend/package.json`

**Steps:**
1. Remove the `VITE_ENABLE_MOCK` bootstrap path from `src/main.ts` so the production bundle no longer starts MSW in the browser.
2. Normalize `VITE_APP_BASE_API` to a single `/api` prefix across development, demo, and production env files.
3. Add explicit Vite and Nginx proxy targets for `/api` instead of maintaining `/dev-api` and `/prod-api`.
4. Add `build:demo` and `preview:demo` scripts and fix the current `@zxio/zxui/style` build blocker so both `prod` and `demo` bundles can compile.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn build:prod && yarn vite build --mode demo`
- Expect: both builds complete successfully and `dist/index.html` is generated after each build.

**Dependencies:**
none
**Output:**
Frontend runtime that always talks to one explicit upstream contract and no longer contains browser-side fallback mock logic.

### Task 2: Export the Backend OpenAPI Contract as a Versioned Artifact

**Files:**
- Create: `ruoyi-fastapi-backend/scripts/export_openapi.py`
- Create: `ruoyi-fastapi-backend/tests/unit/scripts/test_export_openapi.py`
- Create: `docs/contracts/README.md`
- Create: `docs/contracts/openapi/backend-openapi.json`

**Steps:**
1. Add a backend script that imports `server.app`, renders `app.openapi()`, and writes a deterministic JSON artifact to `docs/contracts/openapi/backend-openapi.json`.
2. Normalize export ordering and metadata stripping in the script so contract diffs are reviewable in git.
3. Add a unit test that validates the exporter writes a valid OpenAPI document with expected top-level keys and stable output.
4. Document the contract artifact lifecycle and ownership in `docs/contracts/README.md`.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && python scripts/export_openapi.py --output ../docs/contracts/openapi/backend-openapi.json`
- Expect: the output file exists and contains `"openapi"` and `"paths"` keys.

**Dependencies:**
Task 1
**Output:**
Single-source OpenAPI artifact that all mock and verification flows can consume.

### Task 3: Stand Up a Standalone HTTP Mock Server from the OpenAPI Contract

**Files:**
- Create: `infra/mock-http/docker-compose.yml`
- Create: `infra/mock-http/README.md`
- Create: `infra/mock-http/prism.yaml`
- Modify: `ruoyi-fastapi-frontend/nginx.demo.conf`
- Test: `docs/contracts/openapi/backend-openapi.json`

**Steps:**
1. Add a Prism-based standalone mock server that mounts `docs/contracts/openapi/backend-openapi.json` and serves deterministic HTTP responses on a fixed demo port.
2. Configure demo Nginx to proxy `/api/` to the mock server instead of the real backend.
3. Define example-selection and validation rules in `prism.yaml` so the mock server prefers explicit examples over generic random payloads.
4. Document local startup and smoke-test commands in `infra/mock-http/README.md`.

**Verification:**
- Run: `docker compose -f infra/mock-http/docker-compose.yml config`
- Expect: the compose file resolves successfully with the OpenAPI artifact mounted into the Prism service.

**Dependencies:**
Task 2
**Output:**
Repository-managed HTTP mock upstream for build/demo mode with no browser interception.

### Task 4: Enrich the OpenAPI Contract with High-Value Examples for Demo Fidelity

**Files:**
- Modify: `ruoyi-fastapi-backend/modules/identity/api/*.py`
- Modify: `ruoyi-fastapi-backend/module_admin/controller/*.py`
- Create: `docs/contracts/examples/README.md`
- Test: `docs/contracts/openapi/backend-openapi.json`

**Steps:**
1. Add explicit response examples for authentication, router/menu loading, system dictionary/dept endpoints, and the highest-traffic project/simulation REST endpoints.
2. Keep example payloads deterministic and aligned with frontend expectations for table pagination, auth tokens, and dashboard cards.
3. Export the contract after each example batch and verify the examples are present in the generated artifact.
4. Track remaining low-priority endpoints in `docs/contracts/examples/README.md` so demo coverage grows from an explicit backlog instead of ad-hoc handlers.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && python scripts/export_openapi.py --output ../docs/contracts/openapi/backend-openapi.json && rg -n "\"example\"|\"examples\"" ../docs/contracts/openapi/backend-openapi.json`
- Expect: the exported contract contains concrete examples for the prioritized endpoints.

**Dependencies:**
Task 3
**Output:**
High-fidelity contract examples that make the standalone mock server useful for real demo flows instead of placeholder payloads.

### Task 5: Generate Test-Time MSW Handlers from the OpenAPI Contract

**Files:**
- Create: `ruoyi-fastapi-frontend/scripts/generate-contract-mocks.mjs`
- Create: `ruoyi-fastapi-frontend/tests/msw/generated/handlers.ts`
- Create: `ruoyi-fastapi-frontend/tests/msw/server.ts`
- Modify: `ruoyi-fastapi-frontend/tests/setup.ts`
- Modify: `ruoyi-fastapi-frontend/package.json`
- Modify: `ruoyi-fastapi-frontend/src/mocks/README.md`

**Steps:**
1. Add a generation script that reads `docs/contracts/openapi/backend-openapi.json` and produces MSW handlers for test-only usage.
2. Wire `tests/setup.ts` to a generated `tests/msw/server.ts` so Vitest uses contract-derived mocks instead of handwritten browser runtime mocks.
3. Mark `src/mocks` as deprecated runtime infrastructure and document the new boundary: standalone mock server for demo, generated MSW for tests only.
4. Add a `mock:generate` script to keep generated handlers reproducible in CI and local development.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn mock:generate && rg -n "export const handlers|setupServer" tests/msw/generated/handlers.ts tests/msw/server.ts`
- Expect: generated handler and server files exist and expose a reusable MSW test runtime.

**Dependencies:**
Task 4
**Output:**
Contract-derived MSW test layer that no longer drifts independently from the backend API contract.

### Task 6: Add an Explicit Demo Real-Time Service for WebSocket Flows

**Files:**
- Create: `infra/mock-rt/app.py`
- Create: `infra/mock-rt/requirements.txt`
- Create: `infra/mock-rt/tests/test_mock_rt.py`
- Modify: `ruoyi-fastapi-frontend/.env.demo`
- Modify: `ruoyi-fastapi-frontend/nginx.demo.conf`
- Modify: `ruoyi-fastapi-frontend/src/views/project/simulation/composables/useSimulationWebSocket.ts`

**Steps:**
1. Create a small FastAPI-based demo real-time service that exposes `/auth/ws-ticket` and `/simulation/sessions/{session_id}/ws` with deterministic canned event streams.
2. Add an explicit demo-time WebSocket base URL or upstream route so the frontend never guesses whether to hit real-time mock or real backend infrastructure.
3. Keep the demo stream service focused on message schemas already consumed by the frontend (`status`, `messages`, `bandwidth`, `alarms`, `animation`, `faults`, `pong`) instead of simulation-engine parity.
4. Add automated tests that validate ticket issuance and WebSocket frame shape so future frontend work can rely on the mock stream contract.

**Verification:**
- Run: `cd infra/mock-rt && python -m pytest tests/test_mock_rt.py -q`
- Expect: the mock real-time service tests pass and confirm both ticket and WebSocket behaviors.

**Dependencies:**
Task 1, Task 4
**Output:**
Explicit demo-time real-time upstream that covers WebSocket flows without any browser-side monkey patching.

### Task 7: Add CI Guardrails and Cleanup Rules for the New Platform

**Files:**
- Create: `scripts/verify-contract-mock-platform.sh`
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitlab-ci.yml`
- Modify: `ruoyi-fastapi-frontend/src/mocks/README.md`
- Modify: `docs/contracts/README.md`

**Steps:**
1. Add a verification script that exports OpenAPI, checks generated MSW artifacts are up to date, and fails on leftover `/dev-api`, `/prod-api`, or `VITE_ENABLE_MOCK` references in frontend runtime files.
2. Add CI jobs for backend contract export, frontend mock generation drift detection, `build:prod`, and `build:demo`.
3. Document the allowed architecture boundary: no browser runtime fallback mocking in shipped bundles; demo mode must point to explicit mock upstream services.
4. Make CI failure output actionable so contributors know whether to update the contract, regenerate handlers, or fix an illegal runtime mock path.

**Verification:**
- Run: `bash scripts/verify-contract-mock-platform.sh`
- Expect: the script exits `0` only when contract export, generated mocks, and frontend runtime boundaries are all aligned.

**Dependencies:**
Task 5, Task 6
**Output:**
Enforced repository rules that keep demo, production, tests, and API contracts aligned over time.

### Task 8: Publish the Operating Model and Retire the Legacy Runtime Mock Path

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/mocks/**/*`
- Modify: `ruoyi-fastapi-frontend/tests/README.md`
- Create: `docs/reports/contract-first-mock-platform-rollout-2026-04-05.md`
- Test: `ruoyi-fastapi-frontend/package.json`

**Steps:**
1. Remove or archive legacy browser-runtime MSW bootstrapping code and leave only migration notes where historical context is still useful.
2. Document the three supported modes: local real backend, build/demo with standalone mock upstreams, and test-time generated MSW.
3. Capture rollout status, covered endpoint families, and remaining contract example backlog in a dated report.
4. Publish the cutover checklist so future contributors know the default path for new endpoints and real-time features.

**Verification:**
- Run: `rg -n "VITE_ENABLE_MOCK|setupBrowserMocks|withBackendFallback|/dev-api|/prod-api" ruoyi-fastapi-frontend/src ruoyi-fastapi-frontend/package.json ruoyi-fastapi-frontend/.env.*`
- Expect: only archival documentation references remain; runtime code no longer depends on legacy browser mock paths.

**Dependencies:**
Task 7
**Output:**
Completed cutover from handwritten runtime mocking to a documented contract-first mock platform.

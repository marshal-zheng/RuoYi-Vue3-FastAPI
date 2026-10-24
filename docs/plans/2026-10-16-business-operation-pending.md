# Business Operation Pending Implementation Plan

WORK_ITEM: none

**Goal:** Replace the global one-second HTTP submission heuristic with operation-owned pending lifecycles while keeping business policy outside @zxio/http.
**Inputs:** Approved chat boundary; root AGENTS.md; existing HTTP round-one report; API and caller inventory; ZXUI useFormModal/useDialog/useDrawer; VueUse and TanStack mutation documentation. No docs/steering/README.md exists in this repository.
**Scope Boundaries:** Audit actual write entry points, reuse existing component confirmation protection, protect uncovered business operations, remove the global sessionObj/repeatSubmit mechanism and migrate its consumers, including active generator templates. Validate duplicate triggering, immediate retry after failure, independent operations and real local business requests. Exclude HTTP library changes, request-preparation error pipeline, retry/logger, query caching, unrelated UI redesign, backend idempotency changes, publishing and commits. Simulation commands must preserve their deliberate repeat/parallel semantics; only change lifecycle protection where the audited operation requires it.
**Assumptions:** Work in the current checkout and preserve previous uncommitted work. No computer use. Temporary probes may create clearly marked local test records and remove only their own records.

## Task List

### Task 1: Inventory callers and lock the operation contract

**Status:** Complete.

**Files:**
- Read: ruoyi-fastapi-frontend/src/api/, views/, components/, store/, security/
- Read: ZXUI packages/components/hooks/use-form-modal/index.ts
- Create: ruoyi-fastapi-frontend/src/utils/operation.test.ts
- Create: docs/reports/evidence/2026-10-16-business-operation-pending/write-entry-inventory.json

**Steps:**
1. Save scoped pre-task snapshots and enumerate API mutation methods and their real callers, including request method helpers and side-effecting GET endpoints.
2. Classify existing dialog/drawer protection, explicit parallel commands, upload queues, authentication and uncovered operations.
3. Verify mature-library boundaries and choose an operation-local lifecycle using existing Vue primitives, without HTTP fingerprints, timers or global registries.
4. Add focused regressions for synchronous reentry, slow completion, failure/cancellation release, return/error retention and independent operation instances; observe red.

**Verification:**
- Run: `node /tmp/ruoyi-http-pending/inventory.cjs`.
- Run: `yarn vitest run src/utils/operation.test.ts` in the frontend.
- Expect: real consumers are classified and the new operation contract fails before implementation.

**Dependencies:**
none
**Output:**
Caller inventory and a bounded operation lifecycle contract.

### Task 2: Migrate lifecycle ownership before retiring the global guard

**Status:** Complete.

**Files:**
- Create: ruoyi-fastapi-frontend/src/utils/operation.ts
- Modify: audited uncovered handlers under ruoyi-fastapi-frontend/src/views/, components/ and store/ where necessary
- Modify: ruoyi-fastapi-frontend/src/utils/http.ts and its existing tests
- Modify: ruoyi-fastapi-frontend/src/api/login.ts, api/device/device.ts, api/protocol/protocol.ts, api/simulation/simulation.ts and tests/helpers/error-assertions.ts
- Modify: active ruoyi-fastapi-backend/module_generator/templates/vue/v3/ templates where generated handlers are uncovered

**Steps:**
1. Implement one operation-local pending/run helper; acquire before validation or confirmation and release in finally without replacing errors or deciding HTTP policy.
2. Reuse existing dialog/drawer submit protection; migrate uncovered handlers and make their promises cover validation, confirmation, requests and completion effects.
3. Bind existing submit controls to their operation state where needed; retain independent action and row semantics identified by the audit.
4. Update active generated Vue handlers to return complete operations.
5. Remove the sessionStorage timestamp guard and all repeatSubmit declarations after caller migration.

**Verification:**
- Run: `yarn vitest run src/utils/operation.test.ts src/utils/http.test.ts tests/generator-form-contract.test.ts`.
- Run: `rg -n 'repeatSubmit|sessionObj|数据正在处理，请勿重复提交' ruoyi-fastapi-frontend/src ruoyi-fastapi-frontend/tests ruoyi-fastapi-backend/module_generator/templates` from the repository root.
- Expect: lifecycle regressions pass, all real write consumers have an explicit disposition, and retired production configuration has no remaining consumers.

**Dependencies:**
Task 1
**Output:**
Operation-owned submission behavior with no business submission strategy in @zxio/http.

### Task 3: Verify real behavior and review the migration

**Status:** Complete.

**Files:**
- Create: docs/reports/2026-10-16-business-operation-pending.md
- Create: sanitized evidence under docs/reports/evidence/2026-10-16-business-operation-pending/

**Steps:**
1. Validate actual business handlers against real FastAPI through source-linked HTTP, controlling slow responses with a forwarding gateway.
2. Prove repeated triggering sends one write, failure permits immediate retry, and different operation instances can run in parallel; verify requests are no longer globally blocked within a second.
3. Run affected suites, frontend lint/type-check/conventions, production build and diff checks; verify generator output with the existing contract suite.
4. Request scoped read-only review, fix concrete findings and recheck the caller inventory.
5. Remove owned probe records, stop only processes started by this task and record limitations, remaining work and evidence.

**Verification:**
- Run: `yarn vitest run src/api src/utils src/store/modules/user.login.test.ts tests/generator-form-contract.test.ts`.
- Run: `yarn lint:check`, `yarn type-check` and `bash .agents/skills/frontend-conventions/scripts/validate.sh --changed`.
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --outDir /tmp/ruoyi-http-pending/build-source`.
- Run: temporary real-backend handler probes and `git diff --check`.
- Expect: real duplicate/retry/parallel behavior is correct, no scoped review blocker remains, and unrelated work and HTTP library policy remain unchanged.

**Dependencies:**
Task 2
**Output:**
Completed migration, reviewed evidence and a Chinese implementation report.

## Execution Handoff

Continue execution in this session after plan structure verification. The user explicitly approved implementation and the boundary; do not stop for a second approval.

## Status Sync Suggestion

None; no work item is attached.

## Execution Results

- Audited 114 API call sites in 58 candidate files plus login/authentication, side-effect GET, upload queues and 12 proxy downloads. The inventory distinguishes protected confirmations, operation-owned handlers, explicit commands, exports and unused sources.
- Migrated 56 handlers and three row-scoped status actions, reusing existing ZXUI confirmation protection and batch-import guards. Closed protocol/parent-save and avatar/crop callback gaps. Retired the HTTP timestamp heuristic and all repeatSubmit consumers.
- Updated two active Vue 3 generator templates; rendered/compiled each and verified reentry and immediate retry without mutating editable checkbox arrays.
- Scoped regression suite: 167 passed, including seven operation lifecycle cases; existing backend generator contract suite: 4 passed; existing ZXUI confirmation suite: 11 passed. Source-linked production build (23.39 seconds), frontend lint/type-check/conventions and diff check passed. Backend convention guardrails passed; its Python lint/format, Mypy and embedded Pytest checks were skipped, as documented in the report.
- Actual business handlers and API modules against real FastAPI: six cases passed in each of source and installed HTTP modes. All marked probe records were removed and the real list query confirmed zero remaining records.
- Five memory seam probes passed. Independent review found and verified repairs for two lifecycle gaps; no remaining scoped blocker. No HTTP library change, commit or publication. Only the task-owned backend and child were stopped.
- Report: docs/reports/2026-10-16-business-operation-pending.md; sanitized evidence under docs/reports/evidence/2026-10-16-business-operation-pending/.

# HTTP Cancellation Lifecycle Implementation Plan

WORK_ITEM: none

**Goal:** Make cancellation lifecycle and error context reliable in ZXUI and preserve that contract in the business adapter.
**Inputs:** Approved chat scope; ZXUI HTTP canceler, concurrency plugin, error factory and client; business HTTP error adapter.
**Scope Boundaries:** Include per-request cleanup, linked signal disposal, cancellation error preservation, quiet business cancellation, and actual backend verification. Preserve the existing duplicate-cancellation policy. Exclude retry policy, request deduplication, timeout, pagination and response-pipeline redesign.
**Assumptions:** Continue in both existing workspaces; retain the preceding Axios and source-integration changes. No `docs/steering/README.md` exists in this checkout.

## Task List

### Task 1: Fix library request ownership and signal cleanup

**Files:**
- Modify: ZXUI `packages/http/src/canceler.ts`, `packages/http/src/plugins/concurrency.ts`
- Test: ZXUI existing canceler, client and concurrency tests

**Steps:**
1. Reproduce superseded-request cleanup, serialized-body cleanup and linked-signal cancellation.
2. Track immutable request registrations and dispose external listeners on completion or cancellation.
3. Make concurrency cancellation operate on the actual dispatched signal and reject cancelled queued work promptly.

**Verification:**
- Run: `cd /Users/hqz/Downloads/element-plus && pnpm exec vitest run packages/http/__tests__`.
- Expect: old completion cannot remove new registrations; completed requests release listeners; running and queued cancellation behave consistently.

**Dependencies:**
none
**Output:**
Library-owned request lifecycle correction.

### Task 2: Preserve cancellation and original errors

**Files:**
- Modify: ZXUI `packages/http/src/errors.ts`, `packages/http/src/client.ts`, `packages/http/README.md`
- Modify: business `ruoyi-fastapi-frontend/src/utils/http.ts` and existing HTTP tests
- Modify: business local HTTP vendor dependency and lockfile if needed for the updated public contract

**Steps:**
1. Add focused failing assertions for original cause/response/config and silent cancellation.
2. Normalize errors in the library without losing original context or rewrapping normalized errors.
3. Enrich those errors with business Problem Details while preserving type, code and cause.
4. Deliver the matching local HTTP package so installed and source modes support the same error contract.

**Verification:**
- Run: `pnpm -C packages/http build` and focused HTTP ESLint in ZXUI; `yarn type-check`, `yarn lint:check`, `./node_modules/.bin/vitest run src/api src/utils src/store/modules/user.login.test.ts --coverage.enabled=false`, and `yarn build:prod` in the business frontend. Repeat tests with a temporary HTTP source alias; build with explicit `VITE_ZXUI_LOCAL=true` and `false`.
- Expect: cancellation rejects as a recognizable cancellation without error feedback; ordinary failures retain response, config, cause and business metadata.

**Dependencies:**
Task 1
**Output:**
Stable public error contract consumed by the business.

### Task 3: Verify actual business cancellation

**Files:**
- Create: `docs/reports/2026-10-15-http-cancellation.md` and small evidence records

**Steps:**
1. Start local services using repository instructions.
2. Exercise actual business functions against FastAPI with controlled delayed delivery.
3. Verify in-flight cancellation, replacement-request survival, post-cancellation recovery and ordinary error context.
4. Complete read-only review and remove temporary verification data/services.

**Verification:**
- Run: `node /tmp/ruoyi-http-cancellation/cancel-probe.cjs source` and `node /tmp/ruoyi-http-cancellation/cancel-probe.cjs installed`; inspect the sanitized evidence files linked in the report.
- Expect: transport aborts, cancelled requests emit no failure/relogin feedback, subsequent requests succeed and original error context survives.

**Dependencies:**
Task 1, Task 2
**Output:**
Evidence-backed delivery report with verification limits.

## Execution Handoff

The plan route continues current-session execution by default unless plan-only output is requested or execution is blocked. This approved scope was executed in the current session in both existing workspaces.

## Status Sync Suggestion

No work item is attached; no work-item registry update is needed. Use the execution report for implementation and review evidence, not the plan-stage checkpoint.

## Execution Results

- Task 1 completed: immutable pending registrations, linked signal disposal, actual transport cancellation, prompt queued cancellation and request-instance isolation for reused public IDs.
- Task 2 completed: original error cause/response/config and cancellation reason survive; the business enriches the existing classified error and bypasses cancellation feedback. The matching local HTTP package is installed without publishing npm.
- Task 3 completed: source and installed modes each passed six actual-backend checks. ZXUI HTTP tests passed 58 assertions; business tests passed 74 assertions in each mode. Package builds, business type/lint checks and both production build modes passed.
- Read-only review found one same-ID queue cancellation issue; the regression was reproduced, fixed and reviewed again successfully.
- Evidence: `docs/reports/2026-10-15-http-cancellation.md` and its linked JSON records.

# HTTP Download Boundary Implementation Plan

WORK_ITEM: none

**Goal:** Decode binary HTTP errors in ZXUI while preserving original context, and make business downloads reject errors, remain quiet on cancellation, and release loading correctly.
**Inputs:** Approved chat scope; ZXUI errors/client; business HTTP adapter, download wrapper and file-save helper; existing real export APIs.
**Scope Boundaries:** Include bounded binary error decoding, original error preservation, download cancellation/feedback/rejection/loading lifecycle, local package delivery and real exports. Exclude retry, duplicate-request policy, query/body rules, logging and unrelated UI refactors.
**Assumptions:** Continue both current workspaces, retain previous HTTP changes and use source integration first. No computer use. No docs/steering/README.md exists.

## Task List

### Task 1: Implement library binary error decoding

**Files:**
- Modify: ZXUI packages/http/src/errors.ts, packages/http/src/client.ts and README.md
- Test: existing packages/http/__tests__/client.test.ts

**Steps:**
1. Reproduce Blob and ArrayBuffer error bodies reaching consumers without decoded fields.
2. Add an asynchronous public error resolver; preserve synchronous createHttpError and original cause/response/raw data.
3. Decode only bounded error bodies, retain cancellation identity, and fall back safely on unreadable or malformed data.

**Verification:**
- Run: `pnpm exec vitest run packages/http/__tests__`, targeted ESLint and `pnpm -C packages/http build` in ZXUI.
- Expect: focused regressions fail before correction, then all relevant tests and build checks pass.

**Dependencies:**
none
**Output:**
Library-owned binary error normalization without replacing original transport context.

### Task 2: Correct business download lifecycle

**Files:**
- Modify: ruoyi-fastapi-frontend/src/utils/http.ts, src/utils/request.ts and src/utils/io-toolkit/download.ts as needed
- Modify: ruoyi-fastapi-frontend/src/views/device/index.vue and src/views/project/index.vue for terminal export event handling
- Test: existing HTTP/download contract tests and focused request.download lifecycle tests

**Steps:**
1. Consume the library decoded error payload in the business Problem Details adapter.
2. Keep cancellation quiet, preserve rejected error identity and use finally for loading cleanup.
3. Account for the fullscreen loading singleton across concurrent downloads.
4. Reuse file saving without losing response headers or interpreting valid JSON attachments as failures.

**Verification:**
- Run: focused HTTP/download tests, then existing API/utils/login tests in source and installed modes.
- Expect: one appropriate failure notification, no cancellation notification, error rejection preserved and the mask closes only after all downloads settle.

**Dependencies:**
Task 1
**Output:**
Business-owned feedback and UI lifecycle consuming the shared library contract.

### Task 3: Deliver and verify actual exports

**Files:**
- Modify: frontend local HTTP vendor dependency and yarn.lock
- Create: docs/reports/2026-10-15-http-download-boundary.md and sanitized evidence

**Steps:**
1. Start the local backend using repository runtime instructions.
2. Verify real successful exports, binary Problem Details failures, cancellation and concurrent loading through actual business functions.
3. Package the matching ZXUI dist locally, repeat installed-mode verification and run type/lint/build checks.
4. Complete read-only review and stop only the verification service started for this task.

**Verification:**
- Run: temporary JSDOM XHR export probe against FastAPI :8088 in source and installed modes.
- Run: `yarn type-check`, `yarn lint:check`, relevant Vitest suites, explicit source/installed `yarn build:prod`, frontend conventions and both repositories' `git diff --check`.
- Expect: actual file bytes/names survive, errors preserve original binary bodies and parsed business details, cancellation is quiet and all loading paths settle.

**Dependencies:**
Task 1, Task 2
**Output:**
Reviewed local delivery with reproducible scope and sanitized verification evidence.

## Execution Handoff

Continue current-session execution after plan verification; the user has approved this scope.

## Status Sync Suggestion

None; no work item is attached.

## Execution Results

- Task 1 complete: bounded public binary error resolver; original transport context retained. HTTP tests: 8 files / 75 passing; lint, format, strict test types and HTTP build passed.
- Task 2 complete: business consumes decoded errors, cancellation stays quiet, the original task remains rejected, and the fullscreen mask closes after the final concurrent download. Device/project terminal handlers were adjusted only for this rejection/cancellation contract.
- Task 3 complete for the client boundary: source and installed business suites each passed 18 files / 85 tests; type/lint/conventions and both production builds passed. Each actual-backend probe passed 9 checks using real Word/ZIP/XML exports, binary errors and lifecycle paths.
- Local package installed and matched against current dist; no npm publication or Git commit. Read-only review found no remaining actionable issues in this scope. The temporary backend was stopped.
- Separate limitation: valid user Excel export stalls even through independent Node fetch and drives the backend worker to about one CPU core. It is not counted as passed; no backend changes were mixed into this task.
- Evidence and details: [download boundary report](../reports/2026-10-15-http-download-boundary.md).

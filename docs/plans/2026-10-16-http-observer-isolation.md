# HTTP Observer Isolation Implementation Plan

WORK_ITEM: none

**Goal:** Keep logging and notification failures from changing request results while retaining response transformation and authentication error semantics.
**Inputs:** User scope; both repositories' AGENTS.md; ZXUI HTTP client, notifier and logger; business HTTP transforms and feedback presenter. No steering document exists.
**Scope Boundaries:** Isolate synchronous exceptions and returned promise rejections from observers; retain synchronous delivery order and avoid awaiting observers. Preserve response hooks, success resolver, token provider and error-hook semantics. No retry, parameter, download or UI redesign.
**Assumptions:** Local source connection remains the integration path; no npm publication is required.

## Task List

### Task 1: Isolate generic observers in ZXUI

**Files:**
- Modify: `/Users/hqz/Downloads/element-plus/packages/http/src/{client,notifier,logger,types}.ts`
- Create: `/Users/hqz/Downloads/element-plus/packages/http/src/observer.ts`
- Test: `/Users/hqz/Downloads/element-plus/packages/http/__tests__/observer.test.ts`
- Modify: package README and HTTP component/guide documentation where observer examples are owned.

**Steps:**
1. Add focused failing regressions for loggers, notifier callbacks/listeners and preserved semantic failures.
2. Introduce a private observer invocation boundary; protect context-exposed observers as well as internal calls.
3. Document returned asynchronous work and unchanged semantic hooks.

**Verification:**
- Run: `pnpm exec vitest run packages/http/__tests__ --maxWorkers=1 --minWorkers=1`
- Run: `pnpm -C packages/http build`
- Expect: HTTP tests and package compilation pass; original semantic failures still reject.

**Dependencies:** none
**Output:** Safe HTTP observation without a new dependency or public configuration mechanism.

### Task 2: Isolate business presentation and recover relogin prompt state

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/utils/feedback/{channel,presenter}.ts`
- Modify: `ruoyi-fastapi-frontend/src/utils/http.ts` and the download feedback observer in `ruoyi-fastapi-frontend/src/utils/request.ts`
- Test: existing presenter, HTTP and download tests.

**Steps:**
1. Add regressions for presentation exceptions and failed relogin prompts.
2. Guard business presentation at its owner, return UI promises to the isolation boundary, and release prompt state on failure.
3. Preserve response enrichment, original errors and authentication decisions.

**Verification:**
- Run: `yarn test:run src/utils/feedback/presenter.test.ts src/utils/http.test.ts`
- Run: `yarn lint:check` and `yarn type-check`
- Expect: Feedback failures are contained and request semantics remain unchanged.

**Dependencies:** Task 1
**Output:** Business feedback can fail without corrupting HTTP results or blocking subsequent prompts.

### Task 3: Verify the real source-connected business chain

**Files:**
- Create: `docs/reports/2026-10-16-http-observer-isolation.md`
- Create: sanitized evidence under `docs/reports/evidence/2026-10-16-http-observer-isolation/`.

**Steps:**
1. Run real login, read/write, failure, authentication and cancellation probes against local FastAPI using production modules and ZXUI source; inject observer failures only.
2. Verify response transformation and authentication exceptions still reject; check mutation pending release and explicit retry.
3. Build with source connection, request independent review, compare workspace hashes and clean up temporary records and owned runtime processes.

**Verification:**
- Run: `node /tmp/ruoyi-http-observers/actual-probe.cjs`
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod`
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Expect: Real scenarios pass and fixture cleanup restores baseline; record any preexisting gate failures separately.

**Dependencies:** Task 2
**Output:** Reproducible evidence and scoped review without browser automation or npm publication.

## Execution Handoff

Continue current-session implementation immediately after verifying this plan. No plan approval is pending.

## Status Sync Suggestion

No work item is bound. Plan-stage status is implementing; final claims require execution evidence.

## Execution Result

All three tasks completed. See `docs/reports/2026-10-16-http-observer-isolation.md` for real business evidence, review, known preexisting gate failure and the out-of-scope COUNT cache observation.

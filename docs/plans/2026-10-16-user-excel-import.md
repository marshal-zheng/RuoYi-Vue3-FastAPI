# User Excel Import Lifecycle Implementation Plan

WORK_ITEM: none

**Goal:** Route user Excel imports through the existing HTTP client and make failure, cancellation, stale completion and loading belong to the active import operation.
**Inputs:** User authorization; both repository AGENTS.md files; UserImportDialog.vue; system/user.ts; HTTP FormData/cancellation implementation; ZXUI Upload and Dialog contracts; Element Plus Upload and Axios cancellation documentation. No steering index exists.
**Scope Boundaries:** User Excel import only. Preserve batch summaries, updateSupport, multipart boundary handling and backend validation. Do not introduce retry policies, HTTP operation deduplication, generic observer isolation, other dialog fixes or backend import changes.
**Assumptions:** Client cancellation cannot roll back a server-side import that already committed. Real verification uses tagged temporary users and cleans them through business APIs. Computer use is prohibited.

## Task List

### Task 1: Prove the active import lifecycle failures

**Files:**
- Test: `ruoyi-fastapi-frontend/tests/unit/components/UserImportDialog.test.ts`
- Read: ZXUI `packages/http/src/client.ts` and `packages/components/upload/src/upload.vue`

**Steps:**
1. Confirm that existing FormData requests support authentication, upload progress, original errors and AbortSignal.
2. Add focused component regressions for failure/retry, overlapping triggers, cancellation and stale results.
3. Run the regressions against the old component and inspect expected failures.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn vitest run tests/unit/components/UserImportDialog.test.ts --reporter=dot`
- Expect: Lifecycle assertions fail before production changes, rather than test setup failures.

**Dependencies:** none
**Output:** A bounded regression baseline and an explicit library/business responsibility decision.

### Task 2: Use one HTTP import operation per dialog session

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/api/system/user.ts`
- Modify: `ruoyi-fastapi-frontend/src/views/system/user/components/UserImportDialog.vue`

**Steps:**
1. Add an explicit import API that reuses request/FormData, passes updateSupport as query, and forwards signal/progress.
2. Use Upload for selection only; reuse validateFile and retain a failed selection for retry.
3. Bind loading to the active operation; abort and invalidate it on every close path and component disposal.
4. Accept progress/results/errors only from the active operation, present one failure and preserve the rejected task for callers.
5. Preserve escaped batch result details and the existing template download.

**Verification:**
- Run: focused component and existing HTTP/upload tests, `yarn lint:check`, `yarn type-check`, and a source-connected production build.
- Expect: Passing targeted checks; no raw upload XHR or business policy added to ZXUI HTTP.

**Dependencies:** Task 1
**Output:** A single import execution path without duplicate transport callbacks.

### Task 3: Validate real imports and review

**Files:**
- Create: `docs/reports/2026-10-16-user-excel-import.md`
- Create: focused evidence under `docs/reports/evidence/2026-10-16-user-excel-import/`

**Steps:**
1. Start only a task-owned backend if needed and log in through the real API.
2. Exercise production import handlers with real multipart XLSX: success/readback, failure/retry, updateSupport and cancellation.
3. Use a gateway only to delay real responses for cancellation; distinguish client cancellation from server rollback.
4. Remove only tagged fixture users, log out and stop task-owned runtime processes.
5. Request independent read-only review and verify pre-existing workspace files remain intact.

**Verification:**
- Run: `node /tmp/ruoyi-user-import/actual-probe.cjs`, workspace hash comparison, `git diff --check`, and the frontend conventions changed-file validator.
- Expect: Real responses and readbacks match the operation lifecycle, no fixture users remain, and unrelated files retain baseline hashes.

**Dependencies:** Task 2
**Output:** Evidence-backed completion with explicit limitations.

## Execution Handoff

Continue execution in this session after checking this plan. No additional approval or formal spec is required for the authorized scope.

## Status Sync Suggestion

None: no work item is bound. The plan itself is not implementation or completion evidence.

# User Editor Read Lifecycle Implementation Plan

WORK_ITEM: none

**Goal:** Make each user editor opening own its detail read so stale responses cannot overwrite a later opening, reopen a closed dialog, display stale failures or release another read's loading.
**Inputs:** Authorized follow-up; both AGENTS.md files; UserFormDialog, user API, user page handlers, existing tests, useFormDialog and ZXUI useDialog/HTTP sources. No steering index exists.
**Scope Boundaries:** User editor read lifecycle and its actual entry points only. Preserve normal/disabled user edit, role/post selection and create-only password handling. Inventory similar readers but do not migrate other domains or change HTTP retry, upload, caching or write-operation policy.
**Assumptions:** Existing HTTP AbortSignal and dialog loading/disabled/visibility contracts are adequate unless verification proves a generic defect. No computer use. Real validation uses task-owned users, real API reads/saves and delayed real responses.

## Task List

### Task 1: Lock the read race with focused regressions

**Files:**
- Modify: `ruoyi-fastapi-frontend/tests/unit/components/UserFormDialog.test.ts`
- Read: `ruoyi-fastapi-frontend/src/components/ui/FormDialog/index.ts`
- Read: ZXUI `packages/components/hooks/use-dialog/index.ts` and `packages/http/src/client.ts`

**Steps:**
1. Verify actual read consumers and existing library ownership.
2. Add delayed-response checks for switching, close/reopen, failure/retry, create intent and disposal.
3. Run existing and new component tests before changing production code.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn vitest run tests/unit/components/UserFormDialog.test.ts --reporter=dot`
- Expect: New lifecycle assertions fail on the old implementation and existing save-contract checks remain valid.

**Dependencies:** none
**Output:** Confirmed failure evidence and necessary regression coverage in the existing test file.

### Task 2: Bind detail loading to the opening

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/api/system/user.ts`
- Modify: `ruoyi-fastapi-frontend/src/views/system/user/components/UserFormDialog.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/user/index.vue`

**Steps:**
1. Forward signal and local-feedback ownership through the existing getUser API.
2. Open the dialog immediately with loading and confirmation disabled, then apply only the active read's result.
3. Abort/invalidate previous reads on a new opening, close and unmount; guard stale success, error and finally.
4. Keep a failed current read visible with confirmation disabled and an explicit retry action.
5. Preserve the open Promise rejection and consume already-presented failures at the actual page/retry event boundaries.

**Verification:**
- Run: focused user form/import/HTTP regressions, frontend lint/type-check and a source-connected build.
- Expect: No request sharing or domain policy added to ZXUI; existing create/edit field contracts preserved.

**Dependencies:** Task 1
**Output:** One explicit read lifecycle for the user editor.

### Task 3: Verify real edits and close out

**Files:**
- Create: `docs/reports/2026-10-16-user-edit-read-lifecycle.md`
- Create: focused evidence under `docs/reports/evidence/2026-10-16-user-edit-read-lifecycle/`

**Steps:**
1. Use production component handlers and source-connected hooks/HTTP against the real local FastAPI service.
2. Verify rapid switching, close/reopen, real failure/retry and saving the final selected normal/disabled user.
3. Delay real backend responses with a gateway; use non-cooperating deferred responses only for deterministic stale-callback regression tests.
4. Clean task-owned users/runtime, request independent read-only review and compare workspace hashes.

**Verification:**
- Run: `node /tmp/ruoyi-user-edit-read/actual-probe.cjs`, `git diff --check`, and the changed-file frontend conventions validator.
- Expect: Real readbacks confirm the final selected user was edited; no task-owned users or unrelated source edits remain.

**Dependencies:** Task 2
**Output:** Evidence-backed implementation and explicit validation boundaries.

## Execution Handoff

Continue in the current session after plan verification; implementation is already authorized.

## Status Sync Suggestion

None; no work item is bound. Completion is determined by actual checks and review, not this plan.

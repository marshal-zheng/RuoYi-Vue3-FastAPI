# Remaining RuoYi API and Page Acceptance Implementation Plan

WORK_ITEM: none

**Goal:** Close the remaining non-simulation API and real-page acceptance gaps, repair demonstrated defects, and leave only explicit operational boundaries.
**Inputs:** User authorization to continue; prior user/role/protocol/session/upload/import reports; current route consumers and production API implementations. No steering or initiative index exists.
**Scope Boundaries:** Department, post, menu, dictionary type/data, configuration, notice editing, project editors and non-simulation project operations; scheduler CRUD and an inspected local no-op job; monitoring/tool page reads and scoped exports. Previously accepted flows are reused as evidence and rerun only when affected. Simulation workflows, publishing, commits, pushes, deleting existing business records, flushing shared caches/logs and terminating other users' sessions are outside scope. Do not replace the concurrent schema-form migration.
**Assumptions:** Reuse the existing local MySQL/Redis and running frontend/backend. Use ZXUI source integration and an isolated QA identity. Register temporary owned menu entries only if an existing page has no live menu; distinguish that from current navigation.

## Task List

### Task 1: Preserve source and reconcile live coverage

**Files:**
- Read: `src/api/system/`, `src/api/monitor/`, `src/api/project/` under `ruoyi-fastapi-frontend/`.
- Read: current system/project/monitor/tool page consumers and prior acceptance reports.
- Create: `docs/reports/evidence/2026-10-19-remaining-api-page-acceptance/coverage.json` and `qa-inventory.md`.

**Steps:**
1. Preserve existing source bytes and Git status before edits.
2. Read the live route tree and OpenAPI operations using the local service.
3. Map remaining workflows to real pages, API receipts and cleanup identities.

**Verification:**
- Run: `git status --short` and local HTTP reads of `/openapi.json`, `/getRouters`.
- Expect: A bounded coverage matrix differentiates historical evidence, new acceptance and excluded global operations.

**Dependencies:** none
**Output:** Validated inventory, source baselines and owned QA identity.

### Task 2: Complete remaining system-management workflows

**Files:**
- Read/modify only for demonstrated defects: `ruoyi-fastapi-frontend/src/views/system/{dept,post,menu,dict,config,notice}/` and matching API/query modules.
- Read/modify only for demonstrated defects: corresponding backend system controllers/services/repositories.
- Test: `ruoyi-fastapi-backend/modules/system/tests/test_{dept,post,menu,dict,config,notice}_write_commands.py` and affected unit tests.

**Steps:**
1. Exercise create validation, owned record creation, detail loading, canceled edits and successful edits through real controls.
2. Verify filtering/clearing, relevant exports, error recovery and stored fields.
3. Repair proven contract or lifecycle defects using existing boundaries and add necessary regressions.

**Verification:**
- Run: affected focused Pytest/Vitest files and actual browser operations against local MySQL/Redis.
- Expect: Correct write counts/statuses, matching readback, useful validation and no stale editor writes.

**Dependencies:** Task 1
**Output:** Completed system-workflow receipts and any verified fixes.

### Task 3: Complete non-simulation project workflows

**Files:**
- Read/modify if needed: `ruoyi-fastapi-frontend/src/views/project/`, `src/views/system/project/` and project API modules.
- Read/modify if needed: `ruoyi-fastapi-backend/modules/project/`.
- Test: `ruoyi-fastapi-backend/tests/unit/services/test_project_service.py`, `test_project_version_service.py`; affected frontend project tests.

**Steps:**
1. Validate the live project create/edit/detail flow and its current API boundary.
2. Exercise owned project export/import and configuration/version controls that are reachable without entering simulation.
3. Mark unreachable duplicate consumers explicitly and repair actual current-call defects before signoff.

**Verification:**
- Run: focused project tests and real page/API operations with owned project IDs.
- Expect: Current public consumers work, exported artifacts are readable, round trips preserve the owned fixture and no existing project is changed.

**Dependencies:** Task 2
**Output:** Project acceptance and explicit reachability evidence.

### Task 4: Validate scheduler and monitoring/tool surfaces

**Files:**
- Read/modify if needed: `ruoyi-fastapi-frontend/src/views/monitor/`, `src/views/tool/` and monitor APIs.
- Read: `ruoyi-fastapi-backend/module_task/scheduler_test.py`.
- Test: `ruoyi-fastapi-backend/tests/unit/controllers/test_job_write_contract.py`, `tests/unit/services/test_job_writes.py`.

**Steps:**
1. Inspect the local job target, then validate owned paused job CRUD and a single harmless manual execution when supported.
2. Visit live monitoring/tool routes and inspect their real responses and visible states.
3. Check scoped downloads and recovery without globally deleting logs/caches or stopping other sessions.

**Verification:**
- Run: affected focused tests and real browser/API receipts.
- Expect: No unexplained 4xx/5xx or uncaught page errors; unavailable infrastructure is precisely identified rather than hidden by mocks.

**Dependencies:** Task 3
**Output:** Scheduler and read-only surface coverage.

### Task 5: Verify fixes, clean owned data and reconcile evidence

**Files:**
- Create: `docs/reports/2026-10-19-remaining-api-page-acceptance.md`.
- Update: this plan and the coverage matrix.
- Evidence: `docs/reports/evidence/2026-10-19-remaining-api-page-acceptance/`.

**Steps:**
1. Run narrow regressions and applicable lint/type checks, comparing existing diagnostics when required.
2. Inspect final states at 1440x1000 and 1100x800 and verify source hashes.
3. Delete only identity-verified owned records, logout owned sessions and close owned browser contexts.
4. Record completed workflows, fixed defects, API/page evidence and explicit boundaries.

**Verification:**
- Run: focused checks plus owned-record readback and frontend/backend health reads.
- Expect: No new unresolved defect in accepted workflows; owned artifacts removed; services running; existing changes preserved; no commit/push.

**Dependencies:** Tasks 2, 3 and 4
**Output:** Reviewable final report and coverage matrix.

## Execution Handoff

After structural validation, continue in the current session immediately. The plan route auto-executes; no further approval is needed for the authorized local acceptance and fixes.

## Status Sync Suggestion

No work item is bound. Execution starts now; completion requires actual API/page evidence, fixes and cleanup rather than this plan artifact.


## Execution Result

All five planned work units are complete within the stated boundaries. Current verification: 127 backend tests, 205 frontend tests across 15 files, frontend type checking and production build passed. Baseline-aware Python lint found no new diagnostics. The OpenAPI artifact is current.

Real controls covered the remaining system editors, project/version/topology/export/import and aggregate deletion, the owned scheduler job, and read-only monitoring/tool surfaces. API-only alternatives and historical evidence are explicitly distinguished in `coverage.json`; shared destructive operations and existing schema/filesystem writes were not executed.

Owned records and account 131 were deleted, project child data was checked separately, owned sessions were closed, and local services remain running. Existing work was preserved without commits or pushes. The final report is `docs/reports/2026-10-19-remaining-api-page-acceptance.md`.

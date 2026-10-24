# Pending RuoYi Acceptance Implementation Plan

WORK_ITEM: none

**Goal:** Execute the 35 pending operations from the previous report, fix demonstrated defects, and verify corresponding real controls.
**Inputs:** User continuation request; previous coverage.json and report; controller/service/consumer discovery. Steering is absent.
**Scope Boundaries:** Owned identities, records, Redis keys and temporary generator tables; isolated databases for global cleanup. Preserve shared records, unrelated edits and existing runtime. No commits or pushes.
**Assumptions:** Existing local MySQL/Redis and source-linked frontend remain available. Expected rejection paths count as executed contracts, not successful mutation paths.

## Task List

### Task 1: Preserve and classify
**Files:**
- Create: `docs/reports/evidence/2026-10-19-pending-api-page-acceptance/` baseline, inventory and receipts.
**Steps:**
1. Snapshot current source bytes and Git state.
2. Inspect pending endpoints and real consumers.
3. Assign each operation an owned or isolated fixture.
**Verification:**
- Run: `curl -fsS http://127.0.0.1:8088/health`
- Expect: Ready providers and 35 explicitly tracked pending operations.
**Dependencies:** none
**Output:** Preserved source and QA inventory.

### Task 2: Execute safe real API and page workflows
**Files:**
- Inspect/modify on demonstrated defects: backend `modules/system/`, `modules/project/`, `module_generator/` and matching frontend consumers.
- Test: affected nearby backend/frontend tests.
**Steps:**
1. Exercise dashboard save/reset, tree reads, scoped exports/deletes and expected errors.
2. Exercise generator create/import/edit/sync/download/delete on owned temporary tables.
3. Exercise owned login unlock, session termination and exact cache deletion.
4. Fix defects using existing mechanisms and verify real controls.
**Verification:**
- Run: focused Pytest/Vitest commands recorded in receipts.
- Expect: Correct persisted states, no unintended adjacent-key deletion and useful failures.
**Dependencies:** Task 1
**Output:** Live receipts, inspected downloads and verified fixes.

### Task 3: Isolate global operations and reconcile
**Files:**
- Create: focused isolated integration checks if required.
- Create: `docs/reports/2026-10-19-pending-api-page-acceptance.md` and updated coverage.
**Steps:**
1. Verify global cleanup/refresh behavior against private fixtures without clearing shared state.
2. Run scoped quality checks and separate visual checks at two viewports.
3. Remove owned data, tables and sessions; verify preservation and service health.
4. Link the previous report to the follow-up with exact live/isolated distinctions.
**Verification:**
- Run: focused regression commands, source hash comparison and owned-record cleanup queries.
- Expect: All pending rows have executed evidence or a concrete unresolved boundary; source preserved and services running.
**Dependencies:** Task 2
**Output:** Reviewable evidence and final report.

## Execution Handoff
Continue current-session execution immediately after structural checks; the user requested execution.

## Status Sync Suggestion
No work item is bound. Completion must be established by executed evidence.

## Execution Result

Tasks 1-3 are complete. All 35 pending operations now have explicit evidence: 28 local running-service contracts and 7 isolated storage integrations. Expected 422/403 paths and dry-run scope are recorded without claiming unexecuted branches.

Repairs cover exact cache deletion, MySQL DDL/schema visibility and SQL validation, non-mutating dictionary reads, and failure-log persistence. Verification includes 56 main backend cases plus 6 port/boundary cases (60 unique), 32 frontend cases, frontend type checking and scoped lint. Owned active data/sessions and temporary tables were removed; the documented empty dashboard tombstone remains. Services are running and prior work is preserved without commits or pushes. Final report: `docs/reports/2026-10-19-pending-api-page-acceptance.md`.

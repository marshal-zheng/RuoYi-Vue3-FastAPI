# Historical RuoYi API and Page Revalidation Implementation Plan

WORK_ITEM: none

**Goal:** Replace the 41 historical-only operation rows with current live API evidence and corresponding real-page acceptance, repairing demonstrated defects.
**Inputs:** User request, latest coverage matrix, user/role and protocol reports, root AGENTS and current controllers/consumers. No steering document is present.
**Scope Boundaries:** Owned users/roles/protocols, profile/avatar files and a temporary routed menu if necessary. Preserve shared business records and all existing edits. No commits, pushes or simulation workflows.
**Assumptions:** Reuse running local Docker dependencies, backend 8088 and ZXUI-source-linked frontend 80.

## Task List

### Task 1: Preserve and establish owned fixtures

**Files:**
- Read/modify only for demonstrated defects: All scoped source files; evidence baseline and qa-inventory.md.

**Steps:**
1. Snapshot bytes and HEAD/status; map the 41 operations; create a dedicated operator and minimal-permission target identities.

**Verification:**
- Run: `curl -fsS http://127.0.0.1:8088/health`
- Expect: Ready services, preserved bytes and isolated identities.

**Dependencies:** none
**Output:** Current receipts, findings and verified state for this work unit.

### Task 2: Revalidate user and profile workflows

**Files:**
- Read/modify only for demonstrated defects: Frontend user/profile components; backend user controller/service/query handlers; affected tests.

**Steps:**
1. Exercise user CRUD, status, password reset, import/template/export, profile/avatar/password and readback using real controls.

**Verification:**
- Run: `./node_modules/.bin/vue-tsc --noEmit`
- Expect: Correct persistence, downloads and authentication using owned accounts.

**Dependencies:** Task 1
**Output:** Current receipts, findings and verified state for this work unit.

### Task 3: Revalidate role and authorization workflows

**Files:**
- Read/modify only for demonstrated defects: Role drawers, assignment pages and current role/user command and repository boundaries.

**Steps:**
1. Exercise role CRUD/status/scope/export and both grant directions, including single/batch revoke; verify only owned relationships.

**Verification:**
- Run: `./venv/bin/python -m pytest tests/unit/services/test_role_service.py -q --no-cov`
- Expect: Consistent role/user readback and guarded failures without partial writes.

**Dependencies:** Task 2
**Output:** Current receipts, findings and verified state for this work unit.

### Task 4: Revalidate protocol workflows

**Files:**
- Read/modify only for demonstrated defects: Protocol drawer/list/import consumers, protocol controller/service and focused tests.

**Steps:**
1. Expose the existing page through an owned menu if needed; exercise create/edit/import/preview/template/export/delete and necessary error recovery.

**Verification:**
- Run: `./venv/bin/python -m pytest tests/unit/services/test_protocol_service.py -q --no-cov`
- Expect: Real page/API receipts and inspected protocol round trips.

**Dependencies:** Task 3
**Output:** Current receipts, findings and verified state for this work unit.

### Task 5: Verify, clean and reconcile

**Files:**
- Read/modify only for demonstrated defects: New report and coverage matrix; affected tests and own fixtures.

**Steps:**
1. Run focused regressions and quality checks; inspect two viewports; clean only owned data/files/sessions and compare source snapshots.

**Verification:**
- Run: `git status --short`
- Expect: All 41 rows have current receipts, no owned active data remains, and prior work is preserved.

**Dependencies:** Tasks 2, 3 and 4
**Output:** Current receipts, findings and verified state for this work unit.

## Execution Handoff

Continue current-session execution immediately after plan checks; no new approval is needed for the authorized local work.

## Status Sync Suggestion

No bound work item. Completion requires live evidence, fixes and cleanup.

## Execution Result

Tasks 1–5 completed in the current session. All 41 historical operation rows now have live receipts: 39 corresponding page workflows and 2 alternate protocol endpoints without page consumers. Four demonstrated defects were repaired. See `docs/reports/2026-10-19-historical-api-page-revalidation.md` for checks, cleanup and the non-reproduced 404 observation. Six owned users, one role, five protocols, one temporary menu, associated session state and the owned avatar were cleaned. No commit or push was performed by this run. Concurrent unrelated source and HEAD changes were retained and recorded in preservation.json.

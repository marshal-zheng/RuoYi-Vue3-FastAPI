# List and Export Query Parity Implementation Plan

WORK_ITEM: none

**Goal:** Make configuration, role, dictionary type/data and operation-log lists and Excel exports use the same current filters.
**Inputs:** User request; root AGENTS.md; existing user-page fix; GridList snapshot/request source; corresponding API controllers and query models. No steering directory exists.
**Scope Boundaries:** Fix query ownership, date conversion, pagination separation and obsolete operation-log GridList calls. Leave HTTP, retry, download feedback, list error handling and backend policies unchanged unless a confirmed parity blocker requires a focused correction.
**Assumptions:** Validate through actual business handlers and ZXUI source against local FastAPI/MySQL; no computer use. Existing unrelated changes must be preserved.

## Task List

### Task 1: Lock down the query contract

**Files:**
- Test: `ruoyi-fastapi-frontend/tests/list-export-query-parity.test.ts`
- Read: five target Vue files and related API/backend query paths

**Steps:**
1. Preserve workspace hashes and source baselines.
2. Execute production handlers against the public GridList snapshot interface.
3. Confirm failures for date filters, current dictionary type and operation-log state updates.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn vitest run tests/list-export-query-parity.test.ts --reporter=verbose`
- Expect: Relevant assertions fail before implementation and pass afterward.

**Dependencies:** none
**Output:** A focused regression test for the authorized contract.

### Task 2: Converge business consumers

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/views/system/config/components/ConfigList.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/role/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/dict/components/DictList.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/dict/data.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/business/Monitor/OperlogGrid.vue`

**Steps:**
1. Obtain export filters from `getStateSnapshot()`.
2. Reuse each page's query transformation for list and export; exclude pagination from export.
3. Replace operation-log legacy parameter/state interfaces and remove unused legacy exposure.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn vitest run tests/list-export-query-parity.test.ts tests/user-query-export.test.ts --reporter=verbose`
- Expect: Same filters, preserved editable state and correct cleared conditions.

**Dependencies:** Task 1
**Output:** Correct business consumers without new query infrastructure or ZXUI patches.

### Task 3: Verify real filtered Excel exports

**Files:**
- Create: `docs/reports/2026-10-16-list-export-query-parity.md`
- Create: `docs/reports/evidence/2026-10-16-list-export-query-parity/actual.json`

**Steps:**
1. Run actual page handlers, business HTTP/download modules and GridList source against the local backend.
2. Compare complete paged lists with parsed Excel rows for combined, empty, cleared and changed filters; cover operation-log module/date/sort and dictionary type changes.
3. Run focused tests, frontend lint/types, source-linked build, changed conventions and independent review.
4. Remove only task-owned temporary data/files, close the task session and stop only the backend started for this validation.

**Verification:**
- Run: `node /tmp/ruoyi-list-export-parity/actual-probe.cjs`
- Run: `cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check`
- Run: `cd ruoyi-fastapi-frontend && VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --outDir /tmp/ruoyi-list-export-parity/build-source`
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Expect: Real list/Excel equality, unchanged unrelated source, no new checks failing; report existing blockers separately.

**Dependencies:** Task 2
**Output:** Concrete verification evidence and concise report.

## Execution Handoff

Continue execution in this session. No additional approval or separate thread is required.

## Status Sync Suggestion

No work item exists. Record implementation and verification results in the report without changing unrelated workflow artifacts.

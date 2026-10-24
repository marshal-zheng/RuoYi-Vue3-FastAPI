# Hidden Route Revalidation Implementation Plan

WORK_ITEM: none

**Goal:** Validate business hidden routes across development updates, refreshes and permission transitions, then fix proven routing defects.
**Inputs:** User request; repository AGENTS.md; prior user-role 404 report; real router, permission/user stores and development menu synchronization. No steering index exists.
**Scope Boundaries:** Eight non-simulation permission routes plus device optional-ID, profile/redirect and public authentication/error boundaries; preserve all dirty changes; no commits or pushes. Simulation execution and unrelated UI redesign are excluded.
**Assumptions:** Existing local services and source-linked ZXUI remain available. Isolated fixtures may be created and removed for validation.

## Task List

### Task 1: Establish baseline and coverage

**Files:**
- Create: `docs/reports/evidence/2026-10-19-hidden-route-revalidation/qa-inventory.md`
- Read: `ruoyi-fastapi-frontend/src/router/index.js`
- Read: `ruoyi-fastapi-frontend/src/store/modules/permission.ts`

**Steps:**
1. Save dirty status and affected source snapshots.
2. Map route permissions, real entry controls and usable isolated records.
3. Record functional, visual and negative scenarios before browser testing.

**Verification:**
- Run: `test -f docs/reports/evidence/2026-10-19-hidden-route-revalidation/qa-inventory.md`
- Expect: Route inventory and evidence targets exist.

**Dependencies:** none
**Output:** Baseline and explicit QA inventory.

### Task 2: Reproduce and repair confirmed routing defects

**Files:**
- Modify if proven: `ruoyi-fastapi-frontend/src/store/modules/permission.ts`
- Modify if proven: `ruoyi-fastapi-frontend/src/store/modules/user.ts`
- Modify if proven: `ruoyi-fastapi-frontend/src/plugins/dev-menu-hot-sync.ts`
- Modify when observed: `ruoyi-fastapi-frontend/src/views/system/dict/data.vue`
- Modify when observed: `ruoyi-fastapi-frontend/src/views/system/user/profile/userAvatar.vue`
- Modify when observed: `ruoyi-fastapi-frontend/src/views/tool/gen/editTable.vue`
- Modify when observed: `ruoyi-fastapi-frontend/src/views/project/components/VersionList.vue`
- Test: `ruoyi-fastapi-frontend/tests/unit/components/DictDataRouteFilter.test.ts`
- Test: `ruoyi-fastapi-frontend/src/store/modules/user.login.test.ts`
- Test: `ruoyi-fastapi-frontend/tests/unit/router/permission-layout.test.ts`
- Test: `ruoyi-fastapi-frontend/tests/unit/stores/permission.test.ts`

**Steps:**
1. Exercise hidden pages through real controls and refresh them.
2. Stage real permission changes and delayed reads; inspect the mounted router.
3. Compare existing mechanisms with official Vue Router dynamic routing guidance.
4. Repair only proven defects and add focused real-router regressions.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && ./node_modules/.bin/vitest run --config ../docs/reports/evidence/2026-10-19-hidden-route-revalidation/source.vitest.config.mts`
- Run: `cd ruoyi-fastapi-frontend && ./node_modules/.bin/vue-tsc --noEmit`
- Expect: Focused routing tests and type check pass.

**Dependencies:** Task 1
**Output:** Reproduction evidence, justified fix and regression results.

### Task 3: Complete real-page verification and cleanup

**Files:**
- Create: `docs/reports/2026-10-19-hidden-route-revalidation.md`
- Create: `docs/reports/evidence/2026-10-19-hidden-route-revalidation/`

**Steps:**
1. Repeat navigation, refresh, HMR and permission transitions after the fix.
2. Inspect screenshots at 1440 by 1000 and 1100 by 800.
3. Remove owned fixtures and sessions, verify their absence, and close browsers.
4. Record exact coverage, exclusions and preserved source changes.

**Verification:**
- Run: `test -f docs/reports/2026-10-19-hidden-route-revalidation.md`
- Expect: Real-page evidence, cleanup receipts and honest coverage boundaries are linked.

**Dependencies:** Task 2
**Output:** Reviewable acceptance report without commit or push.

## Execution Handoff

Continue execution in the current session after plan structure verification. No plan-only stop or approval gate applies.

## Status Sync Suggestion

None; no work item is bound to this plan.


## Execution Result

All three tasks completed in this session. Eight business routes and nine URL variants passed refresh, real HMR and permission revoke/deny/regrant checks. Profile and public route boundaries were also exercised. Observed dictionary cache filtering, avatar sizing and narrow-table visibility defects were repaired using existing mechanisms. Seven test files / 68 tests, full frontend type checking, scoped ESLint and the source-linked build passed. Owned fixtures and sessions were removed; all temporary HMR edits were restored. No commit or push was executed.

Evidence: `docs/reports/2026-10-19-hidden-route-revalidation.md` and its linked evidence directory. Simulation runtime remains excluded by repository instructions.

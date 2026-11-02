# Department Resources Implementation Plan

WORK_ITEM: none

**Goal:** Connect RuoYi department management to ZXUI resources through local source integration and verify shared real reads, post-save refresh, and independent editor drafts.
**Inputs:** User request; root AGENTS.md; existing department API/query/list/dialog implementations; ZXUI DATA-resource-interaction delivery and public resources/UI contracts. No steering or initiative index exists.
**Scope Boundaries:** Department resource definitions, session bridge, management components, existing user department-tree consumers, focused regression tests, local authenticated HTTP/browser validation. Preserve existing native user/role/dictionary owners and all unrelated dirty work. No remote push, production data changes, computer use, new thread, or mandatory commit.
**Assumptions:** Use the local Docker MySQL and existing Redis, backend :8088, frontend :80, and the documented local development account. Create and remove only uniquely marked test departments.

## Route Checkpoint

STATUS: ROUTED
ROUTE: plan
INTENT: route-work
NEXT_SKILL: writing-plans
TARGET: RuoYi department resource integration
NORTH_STAR_CONTEXT: none
AUTONOMY: plan-auto-execute
COORDINATION_NEED: none
COORDINATION_REASON: none
NEXT_ACTION: implement this plan in the current session
WHY_NOW: The library capability is delivered; the remaining gap is real business integration.
BLOCK_REASON: none

## Design Choice

Reuse the existing native QueryClient and ZXUI DataClient/resource bindings. Replace department-owned keys, command capture, publication, and opening coordination with the public resource contracts. Migrate both actual user department-tree consumers to the same public resource binding, with one cache identity. Department writes still invalidate the real native user-list consumers because those rows embed department names; this is a domain effect, not another cache or request engine. Keep the native form as the draft owner; resource snapshots are copied once per opening. Prefer declarative read effects and explicit write receipts over success-event reloads.

Official references checked: https://tanstack.com/query/latest/docs/framework/vue/guides/query-invalidation and https://tanstack.com/query/latest/docs/framework/vue/guides/query-cancellation. Targeted invalidation/refetch and AbortSignal belong to the existing engine; no replacement library is needed.

## Task List

### Task 1: Connect the app session and department resource

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/queries/client.ts`, `src/queries/context.ts`, `src/queries/system/dept.ts` (remaining src paths are relative to the frontend).
- Modify: `ruoyi-fastapi-frontend/src/api/system/dept.ts`, `src/utils/http.ts`.
- Test: `ruoyi-fastapi-frontend/src/queries/system/dept.test.ts`, `src/queries/context.test.ts`.

**Steps:**
1. Capture the dirty baseline and reuse the existing query client with one DataClient.
2. Synchronize resource scope with login/logout/authorization changes.
3. Define list/detail/parent/tree reads and create/update/delete command outcomes, using the existing HTTP adapter with cancellation and no automatic write retry.
4. Remove unused old department coordination APIs and migrate real consumers/tests.

**Verification:**
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn vitest run src/queries/system/dept.test.ts src/queries/context.test.ts --reporter=dot`.
- Expect: shared reads, domain isolation, one dispatch, write-vs-refresh outcomes, and native user-list invalidation pass.

**Dependencies:** none
**Output:** One department resource and app/session integration.

### Task 2: Adopt list and editor bindings

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/views/system/dept/components/DeptList.vue`, `DeptDlg.vue`.
- Test: `ruoyi-fastapi-frontend/tests/unit/components/DeptList.test.ts`, `DeptDlg.test.ts`, `UserFormDialog.test.ts`.

**Steps:**
1. Replace manual list publication with useResourceList and retain tree/filter ownership.
2. Open one detached resource snapshot into each native form; preserve drafts on background refresh.
3. Map command receipts to local status, keep unknown/rejected writes open, and offer read-only recovery after confirmed success with refresh failure.
4. Verify independent dialogs, late openings, close/scope changes, and confirmation races.

**Verification:**
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn vitest run tests/unit/components/DeptList.test.ts tests/unit/components/DeptDlg.test.ts tests/unit/components/UserFormDialog.test.ts --reporter=dot`.
- Expect: existing meaningful behaviors plus independent editor and save-refresh regressions pass.

**Dependencies:** Task 1
**Output:** Real department management uses public bindings without parallel draft state.

### Task 3: Verify authenticated local HTTP and real UI

**Files:**
- Modify: `ruoyi-fastapi-frontend/tests/manual/department-query/real-api.probe.ts`, `README.md`.
- Create: `ruoyi-fastapi-frontend/tests/manual/department-resources/` browser acceptance host and script using real production components.
- Create: `docs/reports/2026-11-02-department-resources.md` and bounded sanitized evidence.
- Modify only if needed: frontend package manifests/vendor artifacts for installable public declarations and normal installed-mode validation.

**Steps:**
1. Run backend and source-connected frontend without mocks.
2. Log in using the documented local account; create only uniquely marked temporary departments.
3. Assert actual management route reads/saves, then use one app with two production dialogs to verify shared detail reads and independent drafts.
4. Save one editor and assert list/tree refresh while the other draft remains untouched; verify the saved value through real HTTP.
5. Remove every owned temporary record and retain sanitized request counts, screenshots and cleanup evidence.
6. Run focused lint/types/contracts, review the diff, and verify unrelated work remains intact.

**Verification:**
- Run: updated opt-in real probe and code-driven Playwright acceptance script (exact commands recorded in their README/report).
- Run: `yarn eslint` on changed code; targeted source-mode typecheck and affected tests; `git diff --check` on task files.
- Expect: no HTTP mocks, authenticated real requests, exact sharing and post-write assertions, independent drafts, and verified cleanup. Explicitly separate baseline failures from task failures.

**Dependencies:** Tasks 1, 2
**Output:** Reproducible real integration evidence and a factual report.

## Execution Handoff

ROUTE: plan continues current-session execution immediately after structure verification. Work on the existing business branch for the user's hot local runtime. Do not spawn implementation agents or create threads. Ask only if an essential authorization or credential cannot be recovered from the approved development instructions.

## Status Sync Suggestion

No bound work item. The plan is not completion evidence; implementation and real validation results belong to the report.

## Progress

- [x] Baseline and current implementation inspected; plan verified.
- [x] Task 1
- [x] Task 2
- [x] Task 3

## Runtime Discovery

The source checkout contains unrelated uncommitted theme artifacts with a core hash that differs from the installed dashboard extension. This predates this integration and blocks full app startup. Validate using a project-local detached clean source checkout at the delivered ZXUI commit, without changing or reverting the user theme work. Port 80 is unavailable (EACCES); use loopback 3100, already covered by backend origin policy. Reuse the existing backend rather than running a duplicate.

## Completion Evidence

See `docs/reports/2026-11-02-department-resources.md`: real source-mode browser acceptance and both HTTP modes pass; 119 source-mode regression checks pass. Whole-workspace types and installed table-render limitations are explicitly recorded. No commit or push was requested.

## Follow-up: Installed Acceptance and Type Closure

The user explicitly authorizes resolving the three remaining type diagnostics and the installed tree interface failure. Reuse this plan and its existing evidence; no new spec or delegation is needed.

### Task 4: Fix dictionary filter type boundaries

**Files:**
- Modify: the three affected dictionary, notice and post list components, or their actual shared dictionary input owner if inspection proves that responsibility.
- Test: relevant dictionary/filter tests and full frontend typecheck.

**Steps:**
1. Inspect the GridList draft and DictSelect value contracts.
2. Use the existing field value semantics to make the binding type-safe without assertions or widening to arbitrary values.
3. Run `yarn type-check` and affected lint/regression checks.

**Verification:**
- Expect: zero full-workspace TypeScript errors and unchanged valid filtering/clear behavior.

**Dependencies:** Task 3
**Output:** Type-safe production filter bindings.

### Task 5: Resolve installed tree API failure and rerun real acceptance

**Files:**
- Inspect/modify as required: `tests/table-render-tree-integration.test.ts`, `tests/manual/department-resources/browser.mjs`, package artifacts/manifests only if the packed implementation is actually deficient.
- Update: report, README and separate installed evidence.

**Steps:**
1. Compare installed runtime, declarations and source; probe the actual parent template ref before attributing the failure to packaging.
2. Fix the demonstrated owner and verify real tree expand/collapse in installed mode.
3. Run all affected installed tests and real authenticated department HTTP/browser acceptance with explicit VITE_ZXUI_LOCAL=false.
4. Verify cleanup of only owned temporary records, zero source imports in installed browser runtime, and preserved unrelated work.

**Verification:**
- Run: `VITE_ZXUI_LOCAL=false yarn vitest run tests/table-render-tree-integration.test.ts` plus department regressions and manual real probes.
- Expect: installed tree interface and real shared reads/save refresh/draft isolation pass; full `yarn type-check` passes.

**Dependencies:** Task 4
**Output:** Installed-mode acceptance evidence and corrected current report.

## Follow-up Plan Checkpoint

STATUS: PLAN_UPDATED
FILES_WRITTEN: docs/plans/2026-11-02-department-resources.md
EVIDENCE: READ affected Vue components, GridList/DictSelect contracts, installed table-render runtime/types and previous report; SEARCH expandedKeys/setExpandedKeys and test instance access; COMMAND plan structure checks.
PLAN_CHANGES: Add Tasks 4-5 under the user's explicit follow-up authorization.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: current-session execution
BLOCK_REASON: none
UNBLOCK_ACTION: none

- [x] Task 4
- [x] Task 5

## Follow-up Completion Evidence

Tasks 4-5 pass: full typecheck exit 0, 130 installed regression tests, installed real HTTP and browser acceptance, two temporary browser records and two HTTP records removed. Installed tree exports were already correct; fix the test to access the production parent template ref. No package changes were necessary. See the updated report and its installed evidence directory.

## Selective Commit Authorization and Verification

The user now explicitly requests a commit containing only department resources, type fixes and acceptance evidence. Validate a task-only staged snapshot in a project-local temporary worktree. Preserve all unrelated work and stage mixed manifests from HEAD plus only required dependencies. The isolated check revealed the committed old SchemaForm lacked TableRender's isValueShape dependency; build its already-committed clean library source into a task-specific vendor archive. Immutable install, prepared-fixture full typecheck, 130 installed tests and task lint pass independently. No unrelated source or package selection is included. Commit locally without pushing.

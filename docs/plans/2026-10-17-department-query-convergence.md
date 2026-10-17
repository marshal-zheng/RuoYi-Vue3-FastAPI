# Department Query Convergence Implementation Plan

WORK_ITEM: none
STEERING: none

**Goal:** Make department writes update department management and user department choices consistently, with explicit read failures and protected editing drafts.
**Inputs:** The user's approved follow-up; root AGENTS.md; the delivered HTTP/Vue Query and THEME-runtime-payload contracts; actual department/user APIs, query factories, GridList and editor consumers. No steering index exists.
**Scope Boundaries:** Department list, detail, parent options, writes, user department tree and its actual consumers. Reuse native TanStack Query, the existing QueryClient/session scope, controlled GridList and FormDialog. Preserve endpoint permissions, server-side exclusion/normal-department filtering, DTO allowlists and editable drafts. Do not change steamer-front, simulation, backend contracts, role data-scope trees, generic templates, or introduce a new cache/CRUD framework. Change ZXUI only if a generic defect is proven.
**Assumptions:** Implementation uses the project-local isolated worktree; source checkouts remain read-only after THEME delivery. Existing dependencies and local vendor packages are reused. No computer use; actual HTTP probes use marked temporary departments and remove only their own records.

## Task List

### Task 1: Establish department resource factories and commands

**Status:** Complete; resource/API regressions passed after observed RED.

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/api/system/dept.ts`
- Create: `ruoyi-fastapi-frontend/src/queries/system/dept.ts`
- Test: `ruoyi-fastapi-frontend/src/queries/system/dept.test.ts`

**Steps:**
1. Verify actual API consumers and forwarding of cancellation/session context.
2. Add focused failing regressions for normalized conditions, distinct endpoint variants, write invalidation, scope rejection and retained data on refresh failure.
3. Implement department-owned native options and captured commands; invalidate the department root and affected user lists after successful writes without awaiting refresh.
4. Keep flat cached rows immutable; tree conversion belongs to copied view projections.

**Verification:**
- Run: `corepack yarn vitest run src/queries/system/dept.test.ts --reporter=dot` from the frontend.
- Expect: Meaningful RED followed by passing resource regressions, with one native cache and distinct permission-dependent tree keys.

**Dependencies:** none
**Output:** Shared department reads and write effects using existing infrastructure.

### Task 2: Reuse the editor wait lifecycle and migrate department components

**Status:** Complete; department and existing user/editor regressions passed.

**Files:**
- Create: `ruoyi-fastapi-frontend/src/queries/editor-read.ts`
- Modify: `ruoyi-fastapi-frontend/src/queries/system/user.ts`
- Modify: `ruoyi-fastapi-frontend/src/views/system/dept/components/DeptList.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/dept/components/DeptDlg.vue`
- Test: existing editor/list tests and focused department component regressions.

**Steps:**
1. Extract the existing user editor's scoped, opening-cancellable wait for native reads, preserving replacement-read joining and shared subscribers.
2. Replace the department loader with a controlled GridList backed by native Query and local draft/submitted filters.
3. Project tree rows from copies; present first errors, paused reads and background refresh failures without returning false empty success.
4. Read an editor snapshot once per opening; update parent options separately and protect drafts, close/reopen and scope changes.
5. Route create/update/delete through captured department commands and remove manual list-refresh bridges.

**Verification:**
- Run: focused department, editor lifecycle, list contract and user resource tests.
- Expect: Shared reads remain alive for other subscribers; drafts and DTO fields remain correct; old responses cannot affect a new opening.

**Dependencies:** Task 1
**Output:** Department management consumes the shared resource through existing generic component contracts.

### Task 3: Close user department selection dependencies

**Status:** Complete; actual native TreeSelect regressions observed RED, then passed for initial empty cache, refreshed labels, fallback labels, retained drafts and keyboard selection.

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/views/system/user/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/user/components/UserFormDialog.vue`
- Modify: related user query/component tests.

**Steps:**
1. Move the user tree factory/key from the user resource to the department resource and migrate all real callers.
2. Let the user page and active editor subscribe to the same permission-correct tree, with local status/retry presentation.
3. Preserve selected values and user editing drafts during department refresh; keep disabled/current-value semantics based on actual server data.
4. Verify renamed department labels in user list rows refresh through the recorded write dependency.
5. Review-discovered P1/P2, fixed: prevent an initial null cache node and reproduce the actual native TreeSelect's stale visible label after asynchronous user detail selects a collapsed descendant. Use the public label slot to render the editor's current department label; preserve selection, fallback labels and keyboard behavior without remounting or touching private control state.

**Verification:**
- Run: `corepack yarn vitest run src/queries/system/user.test.ts tests/unit/components/UserFormDialog.test.ts tests/unit/components/UserSecondaryWrites.test.ts --reporter=dot` plus new cross-component regressions.
- Expect: Concurrent tree subscribers share a request, department writes update consumers, and failed refresh does not replace drafts.

**Dependencies:** Tasks 1 and 2
**Output:** Department management and user selection form one consistent resource lifecycle.

### Task 4: Validate source and local-package behavior and review

**Status:** Complete; final source/local-package r2 builds, 133 files / 1252 tests, lint, types and 23 UI standard tests passed. Round 2 independent review passed with no unresolved P0/P1/P2 after closing both native-control findings. Real API evidence retains one initial unexplained refresh timeout and seven later passing runs; all 16 owned records were soft-deleted and verified absent. The result remains in the task worktree for user validation; no department source delivery or publication occurred.

**Files:**
- Create: `docs/reports/2026-10-17-department-query-convergence.md` and bounded evidence.

**Steps:**
1. Run frontend lint, type-check, affected regressions, full tests and UI standards.
2. Build with `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus` and again with `VITE_ZXUI_LOCAL=false`, using unique temporary output directories.
3. Exercise actual business commands against the local backend: create, rename, disable/enable and delete marked departments; verify user tree filtering and excluded descendants.
4. Distinguish component/Query integration tests from real HTTP evidence and unverified browser interaction.
5. Request independent review, fix material findings, recheck scope and preserve source-only work.

**Verification:**
- Run: `corepack yarn lint:check`, `corepack yarn type-check`, `corepack yarn test:run`, `corepack yarn ui:standards`, source/packed production builds and the bounded real API probe.
- Expect: All declared gates pass, owned temporary records are removed, no forbidden path changes and no unresolved scoped review findings.

**Dependencies:** Tasks 1, 2 and 3
**Output:** Reviewable implementation with reproducible evidence and explicit validation limits.

## Execution Handoff

Continue current-session execution after the plan structure checks. The user has already approved implementation; no additional plan approval is required. Department source delivery or publication is not inferred from THEME delivery authorization.

## Status Sync Suggestion

None; no work item is attached. Record implementation, review and verification in the report and execution metadata; preserve the separate THEME source delivery proof.

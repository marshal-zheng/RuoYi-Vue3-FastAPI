# Role Management and Bidirectional Authorization Implementation Plan

**Goal:** Make role management and both authorization directions share correct scoped reads, safe writes, recoverable UI states and return navigation, then deliver verified changes to the recorded source branch.
**Inputs:** Authorized handoff; root AGENTS.md; existing user/department query resources; ZXUI GridList controlled contract and editor-read lifecycle.
**Scope Boundaries:** RuoYi role list/edit/data scope, user-to-role authorization, role-to-user allocated/unallocated lists, related user list return state, and demonstrated backend cache defects. ZXUI only for demonstrated generic defects. No steamer-front, simulation, THEME, post CRUD, publishing, database resets or computer use.
**Assumptions:** Preserve all existing source dirty files/index entries. Source RuoYi std starts at 3e6936e1a839d21ebb17ac5eec36721772d8862f; ZXUI codex/http-vue-query-phase-a starts at 67e13c6cfa413d4c7a57bfa5d728dabc750d2972.

## Design decisions

Use native TanStack queryOptions/useQuery and existing ZXUI controlled GridList, not a CRUD framework. Put the authorization read keys under the existing users resource so existing scoped userCommands invalidate both directions. Role writes invalidate role reads and users' embedded role catalogs/authorization reads. Keep tree permission identities separate. Editor reads remain one opening's immutable snapshot and existing useEditorRead protects drafts.

Store only submitted list filters and pagination in a small Pinia list navigation store for the user/role routes. It clears on scope change and consumes snapshots on return. Do not cache component instances or editors.

Backend changes require actual controlled evidence and a consumer/transaction review. Never infer a cache defect from a static pattern alone. Real probes create and remove only task-owned fixtures.

References: [query keys](https://tanstack.com/query/latest/docs/framework/vue/guides/query-keys), [invalidation](https://tanstack.com/query/latest/docs/framework/vue/guides/query-invalidation), [Vue Router navigation](https://router.vuejs.org/guide/essentials/navigation.html).

## Task List

### Task 1: Record baseline and reproduce affected contracts
**Files:**
- Read: `ruoyi-fastapi-frontend/src/views/system/role/`, `src/views/system/user/authRole.vue`, `src/queries/system/user.ts`.
- Read: `ruoyi-fastapi-backend/modules/system/application/services/{role,menu,user}_service.py` and real repositories/controllers.
- Evidence: source `.git/codex-delivery-preservation/role-authorization-convergence/`.
**Steps:**
1. Record current source HEAD, branch, dirty content/modes and index before creating the project-local worktree.
2. Compare API and GridList contracts, read/write consumers, source dirty ownership and backend transaction/cache behavior.
3. Run focused existing tests and preserve failures separately from introduced regressions.
**Verification:**
- Run: `git status --porcelain=v1` and `yarn vitest run tests/unit/components/RoleAuthorization.test.ts tests/unit/components/RoleFormDrawer.test.ts src/queries/system/user.test.ts` from the frontend.
- Expect: baseline results and explicit contract findings.
**Dependencies:** none
**Output:** Current preservation snapshot and bounded diagnosis.

### Task 2: Converge role and authorization query resources
**Files:**
- Create: `ruoyi-fastapi-frontend/src/queries/system/role.ts` and focused tests.
- Modify: `src/queries/system/user.ts`, `src/api/system/{role,menu,user}.ts`, role drawer components and tests.
**Steps:**
1. Add normalized parameter snapshots, separate permission-aware read identities, scoped cancellation and shared native options.
2. Reuse editor-read lifecycle and scoped command capture, with explicit write effects and draft protection.
3. Add meaningful shared-read, invalidation, stale-scope and failure regressions before implementation.
**Verification:**
- Run: `yarn vitest run src/queries/system/role.test.ts src/queries/system/user.test.ts tests/unit/components/RoleFormDrawer.test.ts`.
- Expect: RED/GREEN evidence and passing current contracts.
**Dependencies:** Task 1
**Output:** Business-owned role/auth resource factories and command coordination.

### Task 3: Repair lists, authorization selection and return state
**Files:**
- Modify: `src/views/system/role/{index,authUser,selectUser}.vue`, `src/views/system/user/{index,authRole}.vue`.
- Create: focused list navigation state module/test and real mounted component regressions.
**Steps:**
1. Connect controlled lists with correct pagination, submitted filters, latest-key reads and loading/error/paused/retry states.
2. Keep full replacement user-role drafts stable across pages and refreshes; keep role-user writes incremental and selection explicit.
3. Enforce frontend operation availability and immutable query rows; preserve submitted filters/pages when returning from authorization.
**Verification:**
- Run: `yarn vitest run tests/unit/components/RoleAuthorization.test.ts` plus new mounted role/list regressions.
- Expect: single first read, correct page 2, latest search wins, recoverable errors, safe empty replacement, selection and return-state coverage.
**Dependencies:** Task 2
**Output:** Complete related frontend paths with necessary regression evidence.

### Task 4: Prove and repair backend cache risks if demonstrated
**Files:**
- Conditional modify: actual role/menu service cache paths and relevant backend tests.
- Create: bounded controlled probe evidence under `docs/reports/evidence/2026-10-17-role-authorization-convergence/`.
**Steps:**
1. Compare current source rules with committed task baseline and establish runtime inputs.
2. Run isolated old-read/write/cache-fill A/B using only owned fixtures where static analysis identifies a real consumer risk.
3. Apply the simplest evidenced correction and preserve unrelated source rules.
**Verification:**
- Run: scoped `venv/bin/python -m pytest` backend tests and recorded real HTTP/MySQL/Redis probe commands.
- Expect: actual A/B distinction, current independent reads, clean fixtures and honest unverified boundaries.
**Dependencies:** Task 1
**Output:** Evidence-backed cache decision and any required focused correction.

### Task 5: Independently review and validate complete candidate
**Files:**
- Create: `docs/reports/2026-10-17-role-authorization-convergence.md` and finite evidence summaries.
**Steps:**
1. Run meaningful component, query, backend and real API checks; use source-linked and existing local packed ZXUI inputs.
2. Run lint/type/UI standards and both production builds, separating pre-existing diagnostics.
3. Dispatch independent review and resolve important findings; rerun only affected gates after fixes.
**Verification:**
- Run: `yarn lint:check`, `yarn type-check`, `yarn test:run`, `yarn ui:standards`, `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod`, and `VITE_ZXUI_LOCAL=false yarn build:prod`.
- Expect: recorded exit codes and no unresolved P0/P1/P2 in independent review; no browser-acceptance claim.
**Dependencies:** Task 3, Task 4
**Output:** Reviewed implementation and reproducible candidate evidence.

### Task 6: Deliver source, revalidate and clean owned resources
**Files:**
- Evidence: persistent source delivery ledger and preservation metadata.
**Steps:**
1. Rehearse source merge against exact current HEAD and retain all unrelated file/index changes.
2. Commit only task-owned changes, deliver to recorded source branch without push and revalidate the standard source backend without overlays.
3. Preserve ancestry/baseline/cleanup proofs, then remove task worktrees/branches/fixtures/processes while leaving shared services and pre-existing parent directories.
**Verification:**
- Run: ancestry and source-head checks, source baseline gates, preservation hash/mode/index comparisons and owned-resource inventory.
- Expect: delivered source commits, unrelated changes preserved, task-owned resources removed; retain raw delivery-status if dirty source prevents a clean classification.
**Dependencies:** Task 5
**Output:** Accurate final source delivery and cleanup record.

## Progress

- [x] Current source snapshots and isolated task worktree.
- [x] Baseline tests and backend diagnosis.
- [x] Query resources and scoped writes.
- [x] Lists, authorization and navigation state.
- [x] Evidence-backed backend decision.
- [x] Independent review and candidate verification.
- [x] Source delivery, baseline and cleanup.

# Third-party Density Implementation Plan

**Goal:** Extend the existing global density preference to active non-simulation VXE tables and editor chrome without changing content or component size semantics.
**Inputs:** 2026-09-26 table-density report, 2026-09-27 theme convergence report, user instruction to continue density work.
**Scope Boundaries:** VXE public sizing variables and per-table layout refresh, Quill/wangEditor toolbar and popup spacing, focused verification. Display Scaling has a separate execution-ready spec and is not implemented here. TableV2 has only a simulation consumer and remains excluded.

## Task List

### Task 1: Bind VXE geometry to committed theme metrics

**Files:**
- Create: `ruoyi-fastapi-frontend/src/plugins/vxe-density.ts`
- Modify: `ruoyi-fastapi-frontend/src/plugins/vxe-table.ts`, `src/assets/styles/vxe-theme.css`

**Steps:**
1. Inspect installed VXE lifecycle hooks, CSS variables and recalculation behavior.
2. Map row/input/padding values to existing ZXUI control spacing while retaining VXE size offsets and explicit row sizes.
3. Bind each table through its public created hook to the nearest Host scope; recalculate on metric changes and dispose with the table/app.

**Verification:**
- Run: `yarn type-check` and focused ESLint.
- Expect: no new errors; no remount, prop mutation or alternative density state.

**Dependencies:**
none.
**Output:**
Shared third-party adapter using existing public ZXUI APIs.

### Task 2: Adapt editor chrome

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Editor/index.vue`, `src/components/ui/RichEditor/src/Editor.vue`

**Steps:**
1. Inspect toolbar and popup positioning contracts.
2. Adapt vertical spacing and controls, including dependent popup offsets.
3. Preserve document content, explicit heights, icon/font sizes and component APIs.

**Verification:**
- Run: scoped ESLint and browser density switching.
- Expect: toolbar height changes, popup anchors align, serialized content stays unchanged.

**Dependencies:**
Task 1 inspection.
**Output:**
Density-aware editor chrome.

### Task 3: Validate and reconcile coverage

**Files:**
- Modify: `ruoyi-fastapi-frontend/tests/fixtures/theme-consumers/App.vue`
- Create: `docs/reports/2026-09-27-third-party-density.md` and evidence.

**Steps:**
1. Extend the existing in-memory fixture with three densities, VXE sizes, a long virtual table, nested scope and content integrity checks.
2. Verify geometry, last-row reachability, data/edit state and scope inheritance through the browser.
3. Run source/installed builds and existing standards checks; add a focused lifecycle regression only if needed.
4. Restore the original preference and document covered consumers and exclusions.

**Verification:**
- Run: `yarn ui:standards`, `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --outDir /tmp/ruoyi-density-source-build`, `VITE_ZXUI_LOCAL=false yarn build:prod --outDir /tmp/ruoyi-density-installed-build`.
- Expect: passing checks, consistent virtual geometry and unchanged content without full-site coverage claims.

**Dependencies:**
Tasks 1–2.
**Output:**
Verifiable density coverage report.

## Progress

- [x] VXE sizing and lifecycle binding
- [x] Editor chrome
- [x] Verification and scope reconciliation

STATUS: COMPLETED
FILES_WRITTEN: docs/plans/2026-09-27-third-party-density.md
EVIDENCE:
- READ: VXE table source, public interceptor types, CSS variables; editor styles; ZXUI useThemeAdapter implementation.
- SEARCH: four raw protocol tables, shared VxeSchemaTable; TableV2 only under simulation.
- COMMAND: type-check, focused ESLint, ui:standards (14 tests), source and installed builds passed.
- BROWSER: 24 size/density combinations; virtual geometry, nested scope, edited value/selection and serialized content passed; real notice dialog verified.
- REPORT: docs/reports/2026-09-27-third-party-density.md
NEXT_ACTION: This batch is complete; Display Scaling remains a separate unimplemented spec.
BLOCK_REASON: none.
UNBLOCK_ACTION: none.

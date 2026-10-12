# ZXUI Simulation Theme Implementation Plan

WORK_ITEM: none

**Goal:** Make the simulation workspace follow the active ZXUI theme while preserving domain colors and existing interaction behavior.
**Inputs:** Current user handoff; both AGENTS.md files; the three 2026-10-11 theme reports; ZXUI theme-platform codemap; active simulation imports and component contracts. No steering directory exists.
**Scope Boundaries:** Active simulation shell, panels, Canvas/ECharts, dialogs, shared NodeEditDrawer and compatibility styles; public library fixes where reusable. Preserve existing changes, domain palettes and data. No lint, build, tests, commits, package release or new worktree.
**Assumptions:** Existing services on ports 80 and 8088 and the local source plugin remain the validation path.

## Task List

### Task 1: Establish ownership and remove competing theme layers

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/views/project/simulation/styles/*`
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/{tailwind,simulation-palette,simulation-utilities}.css`
- Modify: `ruoyi-fastapi-frontend/src/views/project/simulation/index.vue`

**Steps:**
1. Trace active imports, distinguish archived/export-only components, and compare FloatingPanel contracts.
2. Replace business neutral/decorative colors with public semantic roles; retain protocol/severity/series colors.
3. Remove global Element Plus/ZXUI/VXE dark overrides and unused compatibility utilities.

**Verification:**
- Run: `rg -n 'simulation-active|--el-|--vxe-' ruoyi-fastapi-frontend/src/views/project/simulation/styles`
- Expect: no duplicate core theme ownership in active styles.

**Dependencies:**
none
**Output:**
One Host-owned theme path and explicit domain color boundaries.

### Task 2: Integrate panels and charts through public capabilities

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/views/project/simulation/components/*.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/project/components/{NodeEditDrawer,SimulationResultDialog,SimulationStatusPanel}.vue`
- Modify where justified: ZXUI `packages/theme-chalk/src/structural.css` and independent `packages/chart/src/theme.ts`
- Create: `ruoyi-fastapi-frontend/src/theme/useChartTheme.ts`

**Steps:**
1. Keep ZxFloatingPanel state/geometry ownership and restore semantic surface/foreground pairing.
2. Reuse Host projection and the chart package's color compatibility adapter for ECharts and Canvas.
3. Keep data, animation, series identity, selection and business events unchanged.

**Verification:**
- Run: `git diff --check` in each affected repository.
- Expect: no whitespace errors; browser reload has no new module/compile failures.

**Dependencies:**
Task 1
**Output:**
Reactive chart/panel themes without a second business theme engine.

### Task 3: Verify real pages and record boundaries

**Files:**
- Create: `docs/reports/2026-10-11-zxui-simulation-theme.md`
- Create: `docs/reports/evidence/2026-10-11-zxui-simulation-theme/`

**Steps:**
1. Verify air-gray dark, tech-blue light/dark and army-pine light using real theme controls.
2. Exercise panel drag, resize where enabled, dock hide/show, dialogs/drawer, dropdown and chart tooltip.
3. Inspect the full viewport and a smaller desktop viewport; check theme changes while overlays are open and after panels are reopened.
4. Record actual evidence and distinguish live-data, empty-state and source-only coverage; restore initial preferences.

**Verification:**
- Run: `git diff --check` in business, ZXUI root and chart repositories.
- Expect: valid diffs and saved browser evidence without unnecessary data saves.

**Dependencies:**
Task 2
**Output:**
Concise ownership report, screenshots and explicit unverified boundaries.

## QA Inventory

- Shell/header/dock: theme switch changes neutral surfaces, text, border and interaction colors; screenshot and computed styles.
- Floating panels: pointer drag, keyboard movement, collapse/expand and resize where exposed; geometry persists during theme change (no reload persistence existed).
- Charts: data/series colors preserved; neutral grid/labels/tooltips respond to theme; Canvas color strings are accepted.
- Dialogs/drawer/popovers: open content follows nearest Host scope; no body-wide dark or VXE override wins.
- Domain colors: protocol families, critical/error/warning/healthy states and sequence identity remain distinguishable.
- Exploratory scenarios: switch theme with panels/overlays open; hide/show panels and reduce viewport without losing controls.
- Export-only legacy components and backupindex.vue are not counted as active-page validation.

## Execution Handoff

Continue current-session execution immediately. No separate thread or approval gate is needed.

## Status Sync Suggestion

None: no work item was supplied. The plan is not completion evidence.

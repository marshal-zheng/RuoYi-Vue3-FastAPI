# ZXUI Business Theme Audit Implementation Plan

WORK_ITEM: none

**Goal:** Make the real application's shell and confirmed active UI consumers honor the same theme contracts as ZXUI docs, fixing defects at their owning layer.
**Inputs:** Current user request; both repositories' source and existing uncommitted changes; September 22/23 audit reports as historical evidence only.
**Scope Boundaries:** All nine registered themes, light/dark shell, active non-simulation UI and shared consumers are in scope. Simulation-specific styles, saved document colors, chart/category palettes and unrelated existing changes are excluded. No npm publication or broad new test suite.
**Assumptions:** The existing real backend and port-80 frontend remain the validation environment. Browser validation is explicitly authorized for this session. No workspace steering index exists.

## Route

STATUS: ROUTED
ROUTE: plan
INTENT: route-work
NEXT_SKILL: writing-plans
TARGET: Real business / ZXUI theme ownership audit
NORTH_STAR_CONTEXT: none
AUTONOMY: plan-auto-execute
COORDINATION_NEED: none
COORDINATION_REASON: none
NEXT_ACTION: Execute the verified plan in this session
WHY_NOW: Source and browser evidence identify both library-level and business-level styling concerns
BLOCK_REASON: none

## Task List

### Task 1: Establish current theme ownership and runtime evidence

**Files:**
- Read: `ruoyi-fastapi-frontend/src/theme/`, `src/layout/`, `src/assets/styles/`
- Read: `/Users/hqz/Downloads/element-plus/docs/zh-CN/guide/theming.md`
- Read: `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`

**Steps:**
1. Check catalog, Host/Provider and source-linked deployment against docs.
2. Inspect the real page's surface and descendant computed styles across themes.
3. Separate reachable UI overrides from domain colors and unused legacy definitions.

**Verification:**
- Run: `rg -n 'VITE_ZXUI_LOCAL|VITE_ZXIO_REPO_ROOT' ruoyi-fastapi-frontend/.env.development`
- Expect: Local ZXUI source is enabled at the requested path.
- Browser: Read committed theme identity and computed shell colors via the real theme controls.

**Dependencies:** none
**Output:** Current ownership inventory and a reproducible failing UI state.

### Task 2: Fix reusable library defects first

**Files:**
- Modify: `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`
- Generate: `/Users/hqz/Downloads/element-plus/packages/zxui/style/index.css`
- Test: `/Users/hqz/Downloads/element-plus/scripts/theme-consumer/structural-policy.test.ts` only for a demonstrated regression

**Steps:**
1. Remove reset-level surface painting from ordinary links.
2. Preserve component-owned link backgrounds and regenerate the structural mirror.
3. Refresh the real application and verify the brand surface remains visible beneath links.

**Verification:**
- Run: `pnpm -C /Users/hqz/Downloads/element-plus build:theme`
- Run: `pnpm -C /Users/hqz/Downloads/element-plus theme-consumer:check:structural`
- Expect: Generated output and structural contract pass; business brand links remain transparent.

**Dependencies:** Task 1
**Output:** A reusable ZXUI fix with consumer evidence.

### Task 3: Repair confirmed business overrides and record the remaining inventory

**Files:**
- Modify: Confirmed active non-simulation styles under `ruoyi-fastapi-frontend/src/`
- Create: `docs/reports/2026-09-26-zxui-business-theme-audit.md`

**Steps:**
1. Replace confirmed fixed UI colors with existing ZXUI surface and semantic tokens.
2. Preserve simulation-specific values and content-owned colors where components are shared.
3. Verify affected real pages and nine-theme light/dark navigation states.
4. Record fixed findings, exclusions, and any unavailable runtime evidence separately.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn type-check`
- Run: `cd ruoyi-fastapi-frontend && yarn build:prod`
- Run: `git diff --check`
- Browser: Inspect real shell, representative business pages, and overlays without saving business data.
- Expect: Theme ownership is explicit and changed code passes focused checks.

**Dependencies:** Task 2
**Output:** Reviewable fixes and a current audit report.

## Execution Handoff

Continue current-session execution after plan verification. User authorization covers changes in both repositories and this session's browser validation.

## Status Sync Suggestion

No work item is bound. Record implementation and verification evidence in the audit report.

## Progress

- [x] Confirmed nine registered themes and source-linked real runtime.
- [x] Reproduced a library reset painting over the sidebar brand surface.
- [x] Fix and verify reusable reset behavior.
- [x] Audit and repair confirmed business overrides; record remaining rendering-specific work separately.
- [x] Complete the eighteen-state browser matrix and focused checks; write the ownership report.

Evidence: `docs/reports/2026-09-26-zxui-business-theme-audit.md`. This is an audit with bounded repairs, not a claim that every business component is theme-complete.

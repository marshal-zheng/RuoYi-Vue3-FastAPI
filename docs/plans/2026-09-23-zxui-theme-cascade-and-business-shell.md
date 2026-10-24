# ZXUI Theme Cascade and Business Shell Implementation Plan

WORK_ITEM: none

**Goal:** Make the business shell and numeric controls follow the selected ZXUI theme across all registered themes.
**Inputs:** User report and role-order screenshot; `docs/reports/2026-09-22-zxui-theme-adoption-audit.md`; current business and ZXUI source.
**Scope Boundaries:** Shared shell, non-simulation consumers, and the reusable ZXUI Element Plus theme bridge are in scope. Simulation-specific visuals, saved content colors, and the separate form-dialog migration are out of scope. Preserve both repositories' existing changes.
**Assumptions:** The source-linked development mode in `.env.development` is the verification path. Browser automation is unavailable under the current computer-use constraint.

## Task List

### Task 1: Confirm theme ownership and cascade

**Files:**
- Read: `ruoyi-fastapi-frontend/src/assets/styles/theme.module.css`
- Read: `ruoyi-fastapi-frontend/src/layout/`, `src/views/system/role/components/RoleFormDrawer.vue`
- Read: `/Users/hqz/Downloads/element-plus/packages/theme-compiler/src/adapters/element-plus/index.ts`

**Steps:**
1. Trace the active shell and numeric-control declarations to ZXUI tokens or business CSS.
2. Check generated adapter selectors against Element Plus `:root` selectors and record ownership.

**Verification:**
- Run: `rg -n 'data-zx-surface|top-header-bg|left-menu-bg-color|el-input-number' ruoyi-fastapi-frontend/src/layout ruoyi-fastapi-frontend/src/views/system/role`
- Expect: Active consumers and unused legacy colors are distinguished.

**Dependencies:** none
**Output:** A narrow source-based defect inventory.

### Task 2: Correct reusable ZXUI Element Plus cascade

**Files:**
- Modify: `/Users/hqz/Downloads/element-plus/packages/theme-compiler/src/adapters/element-plus/index.ts`
- Modify: `/Users/hqz/Downloads/element-plus/packages/theme-compiler/src/bootstrap.ts` if required by selector emission
- Test: `/Users/hqz/Downloads/element-plus/packages/theme-compiler/__tests__/element-plus-adapter.test.ts`

**Steps:**
1. Give generated Element Plus aliases enough selector weight to override its default `:root` variables while retaining nested theme scopes.
2. Keep bootstrap transformation and manifest identity consistent with emitted CSS.
3. Regenerate only affected theme artifacts through the owning build script.

**Verification:**
- Run: `cd /Users/hqz/Downloads/element-plus && pnpm exec vitest run packages/theme-compiler/__tests__/element-plus-adapter.test.ts packages/theme-compiler/__tests__/bootstrap.test.ts`
- Expect: Adapter and bootstrap contract cases pass.

**Dependencies:** Task 1
**Output:** Reusable theme bridge fix and generated assets.

### Task 3: Remove active business shell overrides and verify the real consumer build

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/layout/` and `src/assets/styles/` only where active declarations override ZXUI surfaces
- Modify: `ruoyi-fastapi-frontend/src/views/project/index.vue`, `src/components/business/Device/ProtocolListDrawer.vue`, and legacy layout settings files when source evidence confirms business ownership
- Test: `ruoyi-fastapi-frontend/tests/unit/stores/settings.test.ts` (update the existing legacy-setting assertions)
- Modify: `ruoyi-fastapi-frontend/src/views/system/role/components/RoleFormDrawer.vue` only if the business usage itself is wrong
- Create: `docs/reports/2026-09-23-zxui-theme-cascade-audit.md`

**Steps:**
1. Replace active shell colors with ZXUI surface and interaction tokens without changing layout geometry.
2. Validate the numeric-control path through the source-linked ZXUI build.
3. Record remaining non-simulation theme gaps and validation limits.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn type-check && yarn build:demo-offline`
- Expect: Typecheck and production build pass with the local ZXUI source path.
- Run: `git diff --check`
- Expect: No whitespace errors in either repository.

**Dependencies:** Task 2
**Output:** Reviewable business changes and theme ownership report.

## Execution Handoff

Continue current-session execution after verifying this plan. Stop only for a concrete technical blocker.

## Status Sync Suggestion

No work item is bound. Keep this plan's execution status in the report and implementation evidence.

## Execution Record

- [x] Confirmed the ZXUI root-alias specificity defect and the business-owned card/drawer colors.
- [x] Fixed the Element Plus adapter, adjusted bootstrap parsing, and regenerated all nine theme packages.
- [x] Removed dormant navigation color declarations, the misleading legacy sidebar-theme setting, and migrated two active business consumers.
- [x] Ran compiler tests/checks, frontend typecheck and source-linked build; recorded visual verification limits in the report.
- [x] Confirmed the running Vite process served stale pre-fix theme assets, restarted it, and added local-theme rebuild detection to the deployment plugin. Verified all nine served alias assets carry the corrected selector and matching hashes.

# Element Plus Icons On Demand Implementation Plan

WORK_ITEM: none

**Goal:** Remove eager whole-collection icon registration from the business app while preserving dynamic menu artwork, designer icon selection, themes and synchronous common controls.
**Inputs:** User-approved implementation; application main.ts, SvgIcon/svgicon.js, generator consumers; ZXUI core/capabilities and actual composite dependencies; official Element Plus, Vue and Vite documentation.
**Scope Boundaries:** Business owns its finite icon registry, navigation mapping and designer catalog. ZXUI owns generic core composition and resolver support. Keep existing default ZXUI entries compatible. Do not replace unrelated icon families, change menu persistence, publish packages or commit unrelated work.
**Assumptions:** No repository steering entry exists. The designer needs the complete EP catalog when choosing arbitrary icons; it may load that catalog on demand rather than on ordinary startup.

## Task List

### Task 1: Close the generic core component dependency boundary

**Files:**
- Modify: ZXUI packages/zxui/core/index.ts and packages/zxui/resolver/index.ts
- Modify: ZXUI composite implementations for ContentWrap, Drawer, Search, Upload, FloatingPanel, MoreAction, ActionBar and ConfirmInput
- Create: Corresponding single-source core implementations and a core ConfirmInput service entry
- Test: ZXUI packages/zxui/__tests__/resolver.test.ts and existing capability/composite suites

**Steps:**
1. Capture the existing business build and preserve affected dirty sources before editing.
2. Extract single-source core implementations and retain default capability wrappers.
3. Bind fixed internal icons directly and propagate capability contexts to core children.
4. Add public core exports and an explicit resolver core mode.

**Verification:**
- Run: `pnpm exec vitest run packages/components/capabilities/__tests__/capabilities.test.tsx packages/zxui/__tests__/resolver.test.ts`
- Expect: Existing default entry names remain available; core nested components use only explicit registries.

**Dependencies:** none
**Output:** Generic component composition with no business icon names or route rules.

### Task 2: Adopt a finite application registry and defer the arbitrary catalog

**Files:**
- Create: ruoyi-fastapi-frontend/src/icons/element.ts and designer-only catalog loader
- Modify: ruoyi-fastapi-frontend/src/main.ts, vite/plugins/components.ts and direct icon/button/dialog imports
- Delete: ruoyi-fastapi-frontend/src/components/ui/SvgIcon/svgicon.js
- Modify: Designer IconsDialog, RightPanel and generator render/html/js
- Modify: Theme Host ConfirmInput import and affected existing tests

**Steps:**
1. Register actual business string icon names for both native EP and ZXUI core consumers.
2. Resolve application auto-imports and direct imports through public core exports.
3. Mount the complete designer picker only on demand.
4. Resolve saved design icon strings to component references without global collection registration.
5. Emit explicit icon imports and bindings in generated forms.

**Verification:**
- Run: `yarn type-check`
- Run: `yarn exec vitest run tests/component-imports.test.ts tests/unit/components/GeneratorIconResolution.test.ts tests/generator-on-demand.test.ts tests/generator-form-contract.test.ts src/theme/zx-theme-host.test.ts`
- Expect: Dynamic designs and generated forms work without full global registration.

**Dependencies:** Task 1
**Output:** Application-owned registry and lazily reached complete designer capability.

### Task 3: Verify the real delivery and navigation behavior

**Files:**
- Create: docs/reports/2026-10-22-element-icons-on-demand.md and evidence files
- Modify: ZXUI docs/zh-CN/guide/bundle-performance.md

**Steps:**
1. Build the application with ZXUI source linking and inspect initial and lazy icon closures against the baseline.
2. Verify real login, ordinary buttons, dynamic SVG menu configuration/previews, collapsed navigation and TopNav.
3. Verify designer selection, saved uncommon icons, generated output, theme inheritance and focused interactions.
4. Run focused lint/type/tests and the changed-file convention check; record pre-existing failures separately.

**Verification:**
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn vite build --outDir ../.tmp/element-icons-demand/candidate --manifest`
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Expect: No whole icon registry on ordinary startup; complete catalog requested only by dynamic designer functionality; menu and themes preserved.

**Dependencies:** Task 2
**Output:** Measured delivery evidence and source-linked browser acceptance.

## Execution Handoff

Continue implementation in the current session after verifying this plan. No new thread or commit is required.

## Status Sync Suggestion

None; this task is not bound to a work item.

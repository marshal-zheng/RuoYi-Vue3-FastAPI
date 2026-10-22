# Material Symbols Navigation Implementation Plan

WORK_ITEM: none

**Goal:** Use locally bundled filled Material Symbols through ZxIcon throughout the application header, sidebar and TopNav.
**Inputs:** Approved user choice; existing navigation contract; public ZxIcon SVG/component APIs; Google Material Symbols SVG sources. No steering index is present.
**Scope Boundaries:** Application navigation icon assets, one business mapping and affected menu previews; ZXUI only fixes unconditional local SVG stroke. Preserve themes, geometry, permissions, routes and folding behavior. No full-library icon replacement, new font/network dependency, commit or publication.

## Task List

### Task 1: Correct generic local SVG rendering

**Files:**
- Modify: `/Users/hqz/Downloads/element-plus/packages/components/icon/src/icon-core.vue`
- Test: `/Users/hqz/Downloads/element-plus/packages/components/icon/__tests__/icon.test.tsx`
- Modify: `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`
- Generate: `/Users/hqz/Downloads/element-plus/packages/zxui/style/index.css`
- Modify: `/Users/hqz/Downloads/element-plus/docs/zh-CN/component/icon.md`

**Steps:**
1. Add a focused regression for local filled SVG without a forced stroke.
2. Remove the unconditional stroke in both local SVG render paths.
3. Let icon color inherit and remove forced SVG fill; regenerate the existing style mirror with its owning command.

**Verification:**
- Run: `cd /Users/hqz/Downloads/element-plus && pnpm exec vitest run packages/components/icon/__tests__/icon.test.tsx`
- Expect: Regression fails before the fix and passes afterward.

**Dependencies:** none
**Output:** SVG painting follows asset semantics without business-specific behavior.

### Task 2: Converge business navigation icons

**Files:**
- Create: `ruoyi-fastapi-frontend/src/icons/navigation.ts`
- Create: `ruoyi-fastapi-frontend/src/assets/icons/svg/material-symbols/`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/SidebarItem.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Navbar.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/TopNav/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Hamburger/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/IconSelect/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/menu/components/MenuList.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/system/menu/components/MenuDrawer.vue`
- Modify: `ruoyi-fastapi-frontend/src/theme/ZxThemePresetSwitch.vue`
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/sidebar.css`

**Steps:**
1. Inventory real menu identifiers and download only required filled symbols at weight 400 / optical size 24 with source/license provenance.
2. Resolve existing menu identifiers through one application-owned mapping; preserve explicit custom icons.
3. Consume ZxIcon in all navigation surfaces, their previews and controls, retaining public menu interactions and geometry tokens.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn type-check`
- Run: `cd ruoyi-fastapi-frontend && yarn exec vitest run tests/unit/Hamburger.test.ts src/layout/policy.test.ts`
- Expect: Types and existing interaction tests pass; no runtime icon download or theme override is introduced.

**Dependencies:** Task 1
**Output:** One business icon mapping, local SVG assets and aligned consumers.

### Task 3: Verify source-linked navigation and boundaries

**Files:**
- Create: `docs/reports/2026-10-22-navigation-material-symbols.md`
- Create: `docs/reports/navigation-material-symbols-2026-10-22/`

**Steps:**
1. Check real source-linked header/sidebar/TopNav and menu previews in default light and army-pine dark themes.
2. Verify icon size overrides, popup routing, logo hover, folding, keyboard and mobile focus; inspect requested resources for external icon dependencies.
3. Run focused lint/tests/type checks and the changed-file convention script; request an independent review and record evidence.

**Verification:**
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Expect: Navigation checks pass; unrelated existing gate failures are distinguished.

**Dependencies:** Task 2
**Output:** Reviewed screenshots, source-linked evidence and remaining limitations.

## Execution Handoff

Continue in this session after plan checks; implementation and local page verification are explicitly authorized.

## Status Sync Suggestion

No bound work item. Record execution evidence in the report.

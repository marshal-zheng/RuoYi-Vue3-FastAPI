# Navigation Appearance Contract Implementation Plan

WORK_ITEM: none

**Goal:** Match the reference navigation geometry and interaction surfaces while keeping every adjustable navigation value in one application-owned entry point.
**Inputs:** User correction, local ThingsBoard shell-theme/menu sources, current business navigation, and the public ZXUI semantic token contract. No steering index is present.
**Scope Boundaries:** Application header, sidebar, toggle, teleported menu and their existing animations. ZXUI receives no application navigation API, styles or dependencies. Login branding, business forms and unrelated workspace changes remain outside this work.
**Assumptions:** The reference desktop width is 250px (its desktop rule overrides the nominal 200px token); the rail is 50px and icons are 24px. The user's explicit request to remove side gaps takes precedence over reference surface margins.

## Task List

### Task 1: Centralize the application navigation contract

**Files:**
- Create: `ruoyi-fastapi-frontend/src/assets/styles/navigation-tokens.css`
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/index.css`
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/theme.module.css`
- Delete: unreferenced `ruoyi-fastapi-frontend/src/assets/styles/variables.module.less`

**Steps:**
1. Define app-owned geometry, spacing, typography, state and motion variables in one stylesheet.
2. Map theme-dependent values to existing public ZXUI semantic roles without assigning core theme variables.
3. Remove replaced navigation declarations and unused aliases from their former locations.

**Verification:**
- Run: `rg -n -- '--app-nav-|--sidebar-width|--left-menu-' ruoyi-fastapi-frontend/src/assets/styles/navigation-tokens.css ruoyi-fastapi-frontend/src/assets/styles/theme.module.css`
- Expect: the navigation defaults have one owner.

**Dependencies:** none
**Output:** One documented, application-owned adjustment entry point.

### Task 2: Consume the contract and separate surface bounds from content indentation

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/sidebar.css`
- Modify: `ruoyi-fastapi-frontend/src/layout/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/SidebarItem.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/Logo.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Navbar.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Hamburger/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/TopNav/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Breadcrumb/index.vue`

**Steps:**
1. Make hover and selected surfaces span the available row, retaining nested content and guide indentation independently.
2. Match the reference width and icon size through variables; migrate earlier header, rail, popup and motion constants.
3. Replace SidebarItem's local boolean nesting input with a numeric depth propagated by its only recursive caller; use depth only for presentation indentation.
4. Preserve native menu state, routing, logo-hover behavior, folding cancellation and mobile focus ownership.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn exec eslint src/layout/index.vue src/layout/components/Sidebar/index.vue src/layout/components/Sidebar/SidebarItem.vue src/layout/components/Sidebar/Logo.vue src/layout/components/Navbar.vue src/components/ui/Hamburger/index.vue src/components/ui/TopNav/index.vue --max-warnings 0`
- Run: `cd ruoyi-fastapi-frontend && yarn type-check`
- Expect: target lint and type checks pass; no layout-specific numeric dimensions remain scattered through the navigation consumers.

**Dependencies:** Task 1
**Output:** Theme-aware navigation with full row interaction surfaces and consistent nested content.

### Task 3: Verify the real source-linked business and global adjustment

**Files:**
- Create: `docs/reports/2026-10-22-navigation-contract.md`
- Create: `docs/reports/navigation-contract-2026-10-22/`
- Test: existing `ruoyi-fastapi-frontend/tests/unit/Hamburger.test.ts`
- Test: existing `ruoyi-fastapi-frontend/src/layout/policy.test.ts`

**Steps:**
1. Record pre-change geometry and surface gaps as failing browser probes.
2. Verify default and army themes, expanded/rail/nested/popup hover and active states, motion, keyboard and mobile behavior.
3. Override width, rail width, icon size, row height and spacing at a theme scope and verify all affected surfaces update together, including teleports.
4. Restore defaults, run existing focused tests and the changed-file convention script, and request an independent final review.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn exec vitest run tests/unit/Hamburger.test.ts src/layout/policy.test.ts`
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Expect: focused tests pass; existing unrelated convention findings are reported separately. Browser probes confirm zero side gaps, 250/50px widths and 24px icons, with working global overrides.

**Dependencies:** Task 2
**Output:** Real business screenshots, geometry/interaction evidence and an independent review.

## Execution Handoff

Continue implementation in the current session after structure verification; the user authorized the change and local page verification. No new approval, publication or commit is needed.

## Status Sync Suggestion

No work item is bound. Track completion using the implementation evidence, not this plan.

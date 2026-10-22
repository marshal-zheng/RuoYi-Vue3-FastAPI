# ThingsBoard-Inspired Navigation Shell Implementation Plan

**Goal:** Align the business header and sidebar structure and navigation rhythm with the local ThingsBoard reference while retaining ZXUI themes and the top-right user menu.
**Inputs:** Approved conversation design; ThingsBoard `ui-ngx/src/app/modules/home/` and `ui-ngx/src/theme/shell-theme.scss`; existing business layout and layout policy.
**Scope Boundaries:** Business shell geometry, brand placement, menu hierarchy, collapse controls and mobile navigation. Preserve route permissions, theme ownership, page actions and simulation content. No bottom sidebar user area, new navigation package, dependency, publishing or commit.

## Task List

### Task 1: Align shell structure and controls

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/layout/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Navbar.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/Logo.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Hamburger/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Breadcrumb/index.vue`
- Test: `ruoyi-fastapi-frontend/tests/unit/Hamburger.test.ts`

**Steps:**
1. Preserve current targeted sources as local baselines and add a focused accessible-control regression to the existing Hamburger suite.
2. Move the single brand band and desktop collapse control to the full-height sidebar, beside the content header.
3. Make the menu toggle a native labelled button and reuse ElDrawer for mobile focus containment, dismissal and launcher focus return.
4. Retain user/theme controls in the header and clarify the current breadcrumb.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn vitest run tests/unit/Hamburger.test.ts src/layout/policy.test.ts`
- Expect: New control regression fails before implementation and passes afterwards; policy tests pass.

**Dependencies:** none
**Output:** Accessible shell controls with one brand area and retained layout preferences.

### Task 2: Consolidate menu geometry and hierarchy

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/components/ui/TopNav/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/sidebar.css`
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/theme.module.css`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/SidebarItem.vue`

**Steps:**
1. Consolidate expanded width 250px, collapsed width 64px and header height 56px through business layout aliases.
2. Replace conflicting legacy menu styles with 44px rows, 4px gaps, 6px right corners and 3px selected markers.
3. Use group icons and continuous nested guides, retaining Element Plus collapsed popups and keyboard navigation. Reinitialize the menu between rail/expanded modes so native defaultActive restores the current route.
4. Replace TopNav body-width estimates and custom overflow with native ElMenu ellipsis against the actual available width.
5. Consume existing semantic colours and support reduced motion.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn type-check`
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Expect: Type check passes; convention failures are assessed against existing workspace changes.

**Dependencies:** Task 1
**Output:** One consistent geometry/style path for desktop, rail and menu popups.

### Task 3: Verify the real source-linked business

**Files:**
- Create: `docs/reports/2026-10-22-navigation-shell.md`

**Steps:**
1. Verify source-linked runtime and capture desktop expanded, collapsed and nested navigation in the real user and log pages.
2. Exercise fold/expand, popup navigation, keyboard focus, mobile open/close/Escape and top-right user menu.
3. Inspect default light and army-pine dark themes, 1600px, 1024px and mobile widths; verify hidden header and tags preferences.
4. Request a focused independent review, resolve findings and record checks and limitations.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn vitest run tests/unit/Hamburger.test.ts src/layout/policy.test.ts`
- Run: `cd ruoyi-fastapi-frontend && yarn type-check`
- Expect: Relevant tests/type check pass; reviewed local screenshots show aligned bands and readable navigation without clipping or a bottom user area.

**Dependencies:** Task 2
**Output:** Reviewed business changes with local runtime evidence and a concise report.

## Execution Record

All three tasks completed in the current local checkouts. No commit or external publication.

STATUS: PLAN_UPDATED
FILES_WRITTEN:
- docs/plans/2026-10-22-navigation-shell.md
EVIDENCE:
- READ: Local ThingsBoard shell/menu sources, business shell consumers, installed Element Plus drawer/focus/menu sources.
- SEARCH: All 11 targeted source/test paths verified; source-linked runtime paths observed under the ZXUI checkout.
- COMMAND: 9 relevant tests, targeted ESLint, type-check and diff whitespace checks passed.
- REVIEW: Independent review completed; mobile focus and TopNav overflow findings resolved and verified.
NEXT_ACTION: Review the final local screenshots in docs/reports/2026-10-22-navigation-shell.md.
BLOCK_REASON: none
UNBLOCK_ACTION: none

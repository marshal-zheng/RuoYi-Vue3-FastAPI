# ZXUI Live Theme Follow-up Implementation Plan

**Goal:** Audit the real business app against ZXUI theme ownership, resolve confirmed business hardcoded UI colors, and diagnose user-page buttons and navigation without masking library defects.
**Inputs:** User request; `src/theme/zx-theme-packages.ts`; `src/views/system/user/index.vue`; ZXUI `packages/components/button/src/button-core.vue` and `packages/theme-chalk/src/structural.css`.
**Scope Boundaries:** Non-simulation consumers only. Preserve existing edits, domain/device colors and saved content. No lint, production build or new tests requested. Browser automation requires the pending user permission.

STATUS: ROUTED
ROUTE: plan
INTENT: route-work
NEXT_SKILL: writing-plans
TARGET: business/ZXUI live theme consumption audit
NORTH_STAR_CONTEXT: none
AUTONOMY: plan-auto-execute
COORDINATION_NEED: none
COORDINATION_REASON: none
NEXT_ACTION: Execute the verified plan in this session.
WHY_NOW: Current source exposes remaining fixed UI colors; screenshots require distinguishing semantic button types from theme defects.
BLOCK_REASON: none for source work; browser permission pending

## Task List

### Task 1: Verify source integration and ownership

**Files:**
- Read: `ruoyi-fastapi-frontend/src/theme/zx-theme-packages.ts`
- Read: `ruoyi-fastapi-frontend/vite/zxui-theme-packages.ts`
- Read: `ruoyi-fastapi-frontend/src/views/system/user/index.vue`
- Read: `/Users/hqz/Downloads/element-plus/packages/theme-compiler/src/adapters/element-plus/mapping.ts`

**Steps:**
1. Confirm active Vite output resolves ZXUI from the local checkout.
2. Trace button types, disabled state, surface roles and compiled aliases.
3. Separate real consumers from unused examples and simulation-only styling.

**Verification:**
- Run: `curl -s http://localhost/src/main.ts`
- Expect: ZXUI imports point into `/Users/hqz/Downloads/element-plus/packages/`.

**Dependencies:** none
**Output:** Ownership findings in the audit report.

### Task 2: Remove confirmed business hardcoded UI colors

**Files:**
- Modify: shared UI consumers under `ruoyi-fastapi-frontend/src/components/ui/`
- Modify: active protocol and project consumers under `ruoyi-fastapi-frontend/src/`
- Create: `docs/reports/2026-09-28-zxui-live-theme-followup.md`

**Steps:**
1. Replace confirmed UI-only constants with existing ZXUI semantic roles.
2. Leave simulation-specific and persisted graphic colors untouched.
3. Inspect incremental changes and request each affected module from the running Vite server.

**Verification:**
- Run: `git diff --check -- ruoyi-fastapi-frontend/src/components/ui/ ruoyi-fastapi-frontend/src/views/project/ ruoyi-fastapi-frontend/src/components/business/Protocol/`
- Expect: No newly introduced whitespace issues; Vite module requests return successfully.

**Dependencies:** Task 1
**Output:** Focused business changes and explicit verification boundaries.

### Task 3: Verify buttons and shell in the real app

**Files:**
- Read: real `/system/user` page and ZXUI button examples
- Modify if confirmed: library-owned source, never generated theme files
- Update: audit report

**Steps:**
1. After browser permission, inspect active theme, computed button states and navigation surfaces.
2. Compare the same theme and button types with ZXUI examples.
3. Fix only a reproducible defect at its owning layer and restore the original theme.

**Verification:**
- Read computed styles and theme identity on the actual page; no business data mutation.
- If browser permission is unavailable, record source-only conclusions explicitly.

**Dependencies:** Task 1
**Output:** Evidence-backed answer to the screenshot and navigation concern.

## Execution status

- [x] Task 1: Nine theme registrations and the running Vite source connection verified.
- [x] Task 2: Fifteen business files adjusted; Vite SFC/style requests, token presence and whitespace checks passed. Dormant matrix-view trial reverted.
- [ ] Task 3: Screenshot colors traced to rocket-moss dark assets. Live browser comparison remains pending the requested permission.
- [x] Button follow-up: The next screenshot exposed a library defect in disabled foreground pairing. Added per-type disabled foreground roles in ZXUI, generated theme assets, and verified the running Vite deployment. See `docs/reports/2026-09-28-zxui-button-disabled-foreground.md`.

STATUS: PLAN_UPDATED
FILES_WRITTEN: This plan and `docs/reports/2026-09-28-zxui-live-theme-followup.md`.
EVIDENCE: Running Vite output, button source and theme assets; verification JSON linked in the report.
NEXT_ACTION: After browser permission, inspect `/system/user` and shell computed styles using the current theme.
BLOCK_REASON: Browser automation permission has not been received; source work is complete.
UNBLOCK_ACTION: User responds to the pending browser permission question.

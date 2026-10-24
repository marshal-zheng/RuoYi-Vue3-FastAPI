# ZXUI Theme Consumption Recheck Implementation Plan

WORK_ITEM: none

**Goal:** Identify current business surfaces that bypass ZXUI themes and fix confirmed defects in their owning repository, prioritizing the sidebar and header.
**Inputs:** Current user request, both repository AGENTS.md files, ZXUI theme codemap and docs shell, business layout and theme Host sources. No business steering index exists.
**Scope Boundaries:** Audit active non-simulation routes and shared consumers; preserve domain classification colors. Do not run lint/build, add test cases, publish packages, or use computer use without user permission.
**Assumptions:** The running port-80 Vite server and configured local ZXUI checkout are the development verification path. Existing uncommitted work is preserved. Historical reports are reference material rather than current runtime evidence.

## Task List

### Task 1: Trace the current theme delivery and shell consumers

**Files:**
- Inspect: `ruoyi-fastapi-frontend/src/theme/`
- Inspect: `ruoyi-fastapi-frontend/src/layout/`
- Inspect: `ruoyi-fastapi-frontend/src/assets/styles/`
- Inspect: `ruoyi-fastapi-frontend/vite/zxui-theme-packages.ts`
- Inspect: `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`

**Steps:**
1. Compare the business catalog, source integration, Host and Provider with ZXUI docs.
2. Inspect current header/sidebar material consumers and possible overrides.
3. Inspect the live Vite module and deployed theme CSS responses.

**Verification:**
- Run: `curl --noproxy '*' --max-time 10 -I http://localhost/system/role`
- Run: `rg -n 'data-zx-surface|surface-header|surface-panel' ruoyi-fastapi-frontend/src/layout`
- Expect: HTTP 200 and explicit use of public header/panel material facets.

**Dependencies:** none
**Output:** Current theme delivery and shell ownership findings.

### Task 2: Audit active business consumers and correct confirmed bypasses

**Files:**
- Inspect: `ruoyi-fastapi-frontend/src/components/`
- Inspect: `ruoyi-fastapi-frontend/src/views/`
- Modify: Confirmed active business consumer or ZXUI capability owners only.

**Steps:**
1. Inventory fixed palettes, custom mode selectors and unresolved semantic references.
2. Trace each candidate to an active import or route and distinguish domain colors from theme styling.
3. Replace confirmed theme bypasses with existing public semantics or fix the library owner where capabilities are missing.

**Verification:**
- Run: `git diff --check`
- Inspect: Changed SFC/CSS modules through the running Vite server.
- Expect: No invalid patches or module transform errors; preserved business color semantics.

**Dependencies:** Task 1
**Output:** Minimal owner-level fixes and a classified residual inventory.

### Task 3: Record evidence and verification limits

**Files:**
- Create: `docs/reports/2026-10-13-zxui-theme-consumption-recheck.md`

**Steps:**
1. Record theme catalog coverage, source/deployment verification and confirmed ownership.
2. Request permission for real-page computer use if visual verification is still needed.
3. Verify representative theme switches if authorized and report any remaining limits explicitly.

**Verification:**
- Run: `test -f docs/reports/2026-10-13-zxui-theme-consumption-recheck.md`
- Expect: Findings distinguish current source/HTTP evidence from observed browser behavior.

**Dependencies:** Task 2
**Output:** A reviewable business-versus-library assessment with evidence boundaries.

## Execution Handoff

Continue execution in this session after the plan structure checks. The user authorized changes in both repositories. Computer use remains subject to the user's explicit permission rule.

## Status Sync Suggestion

No work item is bound; do not update a ledger. Report execution evidence separately from the plan-stage checkpoint.

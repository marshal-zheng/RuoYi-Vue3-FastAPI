# ZXUI Business Theme Parity Implementation Plan

WORK_ITEM: none

**Goal:** Make the real RuoYi business UI consume the same public ZXUI theme capabilities demonstrated in ZXUI docs, assigning each confirmed defect to its owning repository.
**Inputs:** User request; repository AGENTS.md files; business theme Host, deployment and layout sources; ZXUI structural surface contract and docs integration.
**Scope Boundaries:** Audit all non-simulation business UI; prioritize header/sidebar and shared consumers. Preserve business data/status colors where they carry domain meaning. No npm publishing, lint, build, or new test cases in this pass.
**Assumptions:** The configured local ZXUI checkout is authoritative for development. Existing unrelated work in both repositories is preserved. No project steering index exists.

## Task List

### Task 1: Establish theme ownership and runtime evidence

**Files:**
- Inspect: `ruoyi-fastapi-frontend/src/main.ts`
- Inspect: `ruoyi-fastapi-frontend/src/theme/`
- Inspect: `ruoyi-fastapi-frontend/src/layout/`
- Inspect: `ruoyi-fastapi-frontend/src/assets/styles/`
- Inspect: `/Users/hqz/Downloads/element-plus/packages/theme-compiler/`
- Inspect: `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`

**Steps:**
1. Trace local source aliases, public style imports, deployment assets and Host scopes.
2. Compare header/sidebar computed styles with their declared material tokens.
3. Gather independent read-only inventories of business color residuals and ZXUI capabilities.

**Verification:**
- Run: `curl --noproxy '*' --max-time 10 -I http://localhost/system/role`
- Expect: HTTP 200 from the live Vite server.
- Inspect: Live stylesheet sources and computed surface properties through the persistent browser session.
- Expect: Evidence identifies the winning declarations and owning source.

**Dependencies:** none
**Output:** Confirmed cause and prioritized ownership inventory.

### Task 2: Apply owner-level fixes

**Files:**
- Modify only confirmed owners from Task 1: business theme/layout/style integration or the corresponding ZXUI source integration/material implementation.

**Steps:**
1. Correct the upstream capability if the public library contract is incomplete.
2. Remove or replace confirmed business overrides using the existing public theme contract.
3. Keep the theme catalog and local source integration as the single integration path.

**Verification:**
- Run: `git diff --check`
- Inspect: Reloaded live modules and winning CSS declarations.
- Expect: Header/sidebar consume the canonical material roles; no new core-token overrides.

**Dependencies:** Task 1
**Output:** Minimal fixes in their owning repositories, without new tests.

### Task 3: Verify real theme interaction and record remaining ownership

**Files:**
- Inspect: `ruoyi-fastapi-frontend/src/theme/ZxThemePresetSwitch.vue`
- Inspect: Real role page and representative shared consumers.

**Steps:**
1. Use the real theme selector and light/dark toggle; cover the registered catalog.
2. Inspect the header, sidebar, content, menu selection and role drawer after switching.
3. Check theme reload persistence and at least two boundary states: collapsed sidebar and open overlay.
4. Record confirmed changes, deferred domain styling and any remaining library gaps.

**Verification:**
- Inspect: Screenshots and computed material facets in the persistent browser session.
- Expect: Theme surface fills/highlights/edges match the library contract, controls remain readable, and reload preserves the selected theme.

**Dependencies:** Task 2
**Output:** User-facing ownership assessment and runtime evidence.

## Execution Handoff

### User extension: Search action inside the input

**Reference:** `/Users/hqz/dev/steamer-front/src/components/Common/Search.tsx` and the supplied screenshots.
**Owners:** Add `ZxSearch.buttonPlacement` and `ZxConfigProvider.zxSearch` in ZXUI; configure `inside` once in business `src/App.tsx`.
**Compatibility:** Explicit component prop > nearest Provider > existing `outside` default. Preserve click/input modes, Enter, clear, disabled and loading behavior. Use public theme facets for the action, with no business CSS workaround.
**Verification:** Inspect the real role-page search frame, query request, clear and Enter; inspect the documented demo's defaults, override, sizes, loading and disabled states through the running Vite source chain. No new test files, lint or build.

Continue current-session execution immediately. The user has authorized business and ZXUI changes and requested real-page local-source verification. This pass does not run lint/build or create tests.

## Status Sync Suggestion

No work item is bound. Report implementation and observed runtime evidence separately from this plan.

## Execution checkpoint

Task 1–3 and the Search extension are complete for this pass. Findings, changed owners, real-page evidence and the preserved historical graph-style boundary are recorded in `docs/reports/2026-10-12-zxui-business-theme-parity.md`. No lint/build or new tests were run.

# ZXUI Business Theme Adoption Implementation Plan

**Goal:** Audit the real business application's adoption of ZXUI themes, distinguish business overrides from library gaps, and correct confirmed integration and navigation defects.
**Inputs:** Current frontend source; `/Users/hqz/Downloads/element-plus/docs/zh-CN/guide/theming.md`; ZXUI docs theme registry; `docs/specs/zxui-form-dialog-convergence/`.
**Scope Boundaries:** Audit shared layout and non-simulation business theme ownership; fix confirmed public-theme registration, import ordering and navigation paint defects. The user explicitly excluded the simulation module, including its dedicated charts, dialogs and dark styles, from further investigation, changes and acceptance. Preserve existing uncommitted changes. Do not execute the separate form-dialog migration or mechanically replace chart domain colours. Browser automation requires the user's permission under AGENTS.md.

## Route

STATUS: ROUTED
ROUTE: plan
INTENT: route-work
NEXT_SKILL: writing-plans
TARGET: Business theme adoption audit and confirmed integration fixes
NORTH_STAR_CONTEXT: none
AUTONOMY: plan-auto-execute
COORDINATION_NEED: none
COORDINATION_REASON: Independent read-only audits; no dependent child implementation workflow
NEXT_ACTION: Verify this plan and execute in the current source-linked workspace
WHY_NOW: The current business source already adopts surfaces, but still overrides parts of their appearance
BLOCK_REASON: none

## Task List

### Task 1: Establish ownership and existing-spec boundaries

**Files:**
- Read: `ruoyi-fastapi-frontend/src/theme/`, `src/main.ts`, `src/assets/styles/`, `src/layout/`, `src/views/`
- Read: `docs/specs/zxui-form-dialog-convergence/{requirements,design,tasks}.md`
- Create: `docs/reports/2026-09-22-zxui-theme-adoption-audit.md`

**Steps:**
1. Compare public ZXUI surface tokens and docs registrations with business consumers.
2. Trace imports and actual consumers before classifying hardcoded declarations.
3. Record business defects, library gaps, dormant code and unverified runtime claims separately.

**Verification:**
- Run: `rg -n 'data-zx-surface|box-shadow' ruoyi-fastapi-frontend/src/layout`
- Expect: Existing surface adoption and competing declarations identified with source references.

**Dependencies:** none
**Output:** Evidence-based audit and dialog-spec relationship.

### Task 2: Correct confirmed integration and navigation defects

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/main.ts`
- Modify: `ruoyi-fastapi-frontend/src/theme/zx-theme-packages.ts`
- Modify: `ruoyi-fastapi-frontend/vite/zxui-theme-packages.ts`
- Modify: `ruoyi-fastapi-frontend/src/assets/styles/theme.module.css`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/TopNav/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/Sidebar/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/layout/components/TagsView/ScrollPane.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/login.vue` (confirmed white-on-white conflict in the real dark login page)
- Test: `ruoyi-fastapi-frontend/src/theme/zx-theme-packages.test.ts`

**Steps:**
1. Register rocket-moss using the same generated package and swatch as ZXUI docs.
2. Load Element Plus CSS before ZXUI theme aliases and structural CSS.
3. Use header/panel semantic tokens for navigation states and preserve both surface depth and inner material.
4. Update the existing registry expectation; add no new test suite.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && ./node_modules/.bin/vitest run src/theme/zx-theme-packages.test.ts src/theme/zx-theme-host.test.ts src/theme/theme-export-path.test.ts`
- Expect: Existing focused tests pass.
- Run: `cd ruoyi-fastapi-frontend && ./node_modules/.bin/vite --host 127.0.0.1 --port 80 --strictPort`
- Expect: Source-linked entry modules and changed SFC styles transform without errors.

**Dependencies:** Task 1
**Output:** Confirmed fixes in the real business checkout.

### Task 3: Verify and report the remaining adoption surface

**Files:**
- Modify: `docs/reports/2026-09-22-zxui-theme-adoption-audit.md`
- Modify: this plan's execution record

**Steps:**
1. Run focused lint and compiler checks against changed modules.
2. If browser permission is granted, inspect real page theme changes; otherwise explicitly retain visual verification as outstanding.
3. Reconcile audit findings and checks without claiming the dialog spec or full business migration is complete.

**Verification:**
- Run: `git diff --check -- ruoyi-fastapi-frontend/src/main.ts ruoyi-fastapi-frontend/src/theme/zx-theme-packages.ts ruoyi-fastapi-frontend/vite/zxui-theme-packages.ts`
- Expect: No introduced whitespace errors.
- Expect: Report distinguishes source evidence, test evidence and unperformed browser checks.

**Dependencies:** Task 2
**Output:** Reviewable changes and a remaining-work inventory.

## Delegation Record

TRACKING_MODE: parent-recorded
POST_LAUNCH_CONTROL: parent-observed
RUN_REF: subagent:/root/zxui_theme_contract_audit; subagent:/root/business_theme_inventory; subagent:/root/dialog_spec_reconcile
THREAD_REF: none
RETURN_CONTRACT: Read-only findings with source locations, ownership and uncertainties
NEXT_OBSERVATION_ACTION: Read results and verify referenced sources
OBSERVATION_BOUND: One completed report per audit
EVIDENCE_BOUNDARY: Child summaries are leads; source and local verification support conclusions.

## Execution Record

- Scope correction: simulation is excluded at the user's explicit request; remaining audit actions apply to shared layout and non-simulation business pages.
- [x] Inspect current business and ZXUI source; locate existing dialog spec.
- [x] Apply confirmed integration/navigation corrections and the observed login surface conflict.
- [x] Run focused verification and record the remaining adoption inventory.
- Browser permission granted in the conversation; verified all nine navigation themes in both modes, TopNav underline and login light/dark/autofill.
- Typecheck passed; existing focused tests passed (3 files / 4 cases); targeted lint passed with five pre-existing unused-variable warnings.
- Audit and existing dialog spec assessment: `docs/reports/2026-09-22-zxui-theme-adoption-audit.md`.

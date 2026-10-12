# ZXUI Theme Integration Optimization Implementation Plan

WORK_ITEM: none

**Goal:** Make the business shell follow the committed ZXUI theme and move reusable integration and metadata delivery into public library APIs.
**Inputs:** User authorization, the theme design assessment, both repository guidelines, and existing theme Host/deployment sources. No steering directory is present in the business repository.
**Scope Boundaries:** Header/sidebar, shared theme application integration, compact deployment metadata, and source-linked browser verification are in scope. No lint, build, new tests, simulation changes, commits, or publishing.
**Assumptions:** Preserve pre-existing business edits; use the existing generated theme assets and local MySQL/Redis services.

## Task List

### Task 1: Verify and correct the business shell

**Files:**
- Inspect/modify: `ruoyi-fastapi-frontend/src/layout/index.vue`, `src/layout/components/Sidebar/index.vue`, `src/assets/styles/index.css` (paths after the first are frontend-relative).
**Steps:**
1. Start the documented local services and inspect the real page in the authorized browser.
2. Compare header/sidebar computed surfaces with the active theme and locate the owning rule.
3. Correct the smallest reusable ownership issue and verify preset/mode changes.
**Verification:**
- Run: `curl -I http://localhost/` from the frontend directory.
- Expect: Vite responds; browser header, logo, sidebar and menu selection share the committed theme across light/dark presets and refresh.
**Dependencies:**
- None.
**Output:**
- Correctly themed application shell with browser evidence.

### Task 2: Consolidate public application integration

**Files:**
- Modify/create: ZXUI `packages/zxui/theme-host/` public application integration.
- Modify: business `src/theme/zx-theme-config.ts`, `src/theme/zx-theme-host.ts`, `src/theme/ZxThemePreferenceBridge.tsx`, `src/App.tsx` as required.
**Steps:**
1. Reuse the Host transaction as the sole commit authority.
2. Expose a small public preference/application controller and leave storage migration/catalog choices in the business.
3. Remove duplicate business queues and bind lifecycle cleanup once.
**Verification:**
- Run: `rg -n 'bindZxThemePreferenceUpdater|pendingUpdate|projectZxThemeScope' src/theme` in the frontend directory.
- Expect: Removed duplicated orchestration; browser rapid switches, density changes and refresh retain a coherent committed preference.
**Dependencies:**
- Task 1.
**Output:**
- Public reusable theme integration consumed by the real application.

### Task 3: Share compact deployment metadata and source tooling

**Files:**
- Modify/create: ZXUI `packages/theme-compiler/src/vite/`, `packages/theme-compiler/package.json`, `docs/.vitepress/build/compact-theme-data.ts`.
- Modify: business `vite/zxui-theme-packages.ts` and relevant public documentation.
**Steps:**
1. Move the docs metadata codec into the compiler and reuse it in the public Vite plugin.
2. Provide a supported public source entry for local tooling without touching generated outputs.
3. Compare decoded metadata with the uncompressed payload and record actual byte sizes.
**Verification:**
- Run: `node --import tsx --input-type=module` with an inline diagnostic that loads the plugin's virtual module, imports its emitted JavaScript and compares JSON plus raw/gzip/Brotli bytes.
- Expect: Exact payload parity and a smaller module; source-linked Vite restarts without a build.
**Dependencies:**
- Task 2.
**Output:**
- One codec and a documented source integration path shared by docs and business.

### Task 4: Verify the complete workflow and record evidence

**Files:**
- Update: `docs/reports/2026-10-11-zxui-theme-design-assessment.md` or a linked implementation report.
**Steps:**
1. Exercise representative branded light/dark themes, collapsed navigation, density and a body-mounted dropdown.
2. Inspect console/runtime diagnostics and refresh persistence.
3. Review diffs against the initial dirty-state snapshot and record limitations.
**Verification:**
- Run: `git diff --check` in both repositories.
- Expect: No introduced whitespace defects; browser evidence and diagnostic results are recorded without claiming lint/build/test coverage.
**Dependencies:**
- Tasks 1–3.
**Output:**
- Reviewable implementation and concrete validation evidence.

## Execution Handoff

Continue in the current session immediately after plan verification. No further approval gate is required for the authorized work.

## Status Sync Suggestion

None: no tracked work item is attached. Implementation progress is recorded with execution evidence, not inferred from this plan.

## Plan-Stage Checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN:
- docs/plans/2026-10-11-zxui-theme-integration-optimization.md
EVIDENCE:
- READ: Repository guidance, assessment, shell styles, Host and Vite deployment sources.
- SEARCH: Theme preference ownership, source entry exports and compact codec call sites.
- COMMAND: Plan file existence and all required heading/field searches passed.
PLAN_CHANGES:
- Four ordered tasks; browser verification replaces lint/build/new tests for this authorized iteration.
WORK_ITEM_SYNC_SUGGESTION:
- none
NEXT_ACTION: current-session execution
BLOCK_REASON: none
UNBLOCK_ACTION: none

## Execution Result

All four tasks were executed in this session. The browser exposed an additional concrete business defect: the Logo state class collided with Tailwind's collapse utility. Implementation, matrix observations, compression parity and explicit verification limits are recorded in `../reports/2026-10-11-zxui-theme-integration-optimization.md`. No lint, build or test command was run.

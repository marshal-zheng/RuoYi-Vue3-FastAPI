# ZXUI Layout Regions Implementation Plan

WORK_ITEM: none

**Goal:** Correctly allocate content space when application chrome is hidden, with explicit natural-flow and bounded-region scrolling and no new continuous layout measurements.
**Inputs:** Approved conversation design and performance constraints; both repositories' AGENTS.md; ZXUI fill contract, ContentWrap, Tabs and GridList sources; business layout and page sources. No steering index is present.
**Scope Boundaries:** ZXUI owns reusable region layout and footer observation lifecycle. RuoYi owns application chrome, persisted preferences, route overrides and page intent. Preserve unrelated changes and simulation-specific source. No publishing or commits.
**Assumptions:** ZXUI source checkout is /Users/hqz/Downloads/element-plus. Browser verification uses an isolated automated test environment only when authorized.

## Task List

### Task 1: Library layout and footer lifecycle — Complete

**Files:**
- Create: ZXUI packages/components/page-layout/{index.ts,src/page-layout.vue,src/props.ts,__tests__/page-layout.test.tsx}
- Modify: ZXUI packages/components/content-wrap/src/content-wrap.vue and public exports/style manifests
- Test: ZXUI packages/components/content-wrap/__tests__/content-wrap.test.tsx

**Steps:**
1. Add failing tests for unused footer resources and a public reusable layout module.
2. Implement a CSS-only flow/bounded layout with header, body and footer slots, explicit body/delegated scrolling and a bounded fill root.
3. Register the public component and its generated style/export ownership.
4. Activate legacy viewport-footer measurements only while required; bounded fill footers remain in flow.
5. Document flow, nested-region, scrolling and containment contracts.

**Verification:**
- Run: cd /Users/hqz/Downloads/element-plus && pnpm exec vitest run packages/components/page-layout/__tests__/page-layout.test.tsx packages/components/content-wrap/__tests__/content-wrap.test.tsx
- Expect: No layout-owned observers/listeners, correct resource activation and release, existing footer behavior preserved outside bounded fill.

**Dependencies:** none
**Output:** Public layout capability and corrected ContentWrap resource lifecycle.

### Task 2: Application integration — Complete

**Files:**
- Modify: ruoyi-fastapi-frontend/src/{settings.ts,store/modules/settings.ts,layout/index.vue,layout/components/AppMain.vue,layout/components/Navbar.vue,layout/components/Settings/index.vue,layout/components/Sidebar/index.vue,layout/components/InnerLink/index.vue}
- Modify: representative detail/editor/legacy viewport-height consumers and generator templates
- Create: business layout policy and focused tests

**Steps:**
1. Add independent header, tags and breadcrumb preferences plus non-persistent route overrides.
2. Replace fixed chrome offsets with normal-flow grid/flex allocation and retain a layout recovery entry when header is hidden.
3. Connect AppMain to the library region; ordinary pages scroll naturally and filled pages own internal scrolling.
4. Remove page-specific application-height deductions from detail, editor and iframe consumers.
5. Align generated pages with the shared page contract.

**Verification:**
- Run: cd ruoyi-fastapi-frontend && yarn eslint src/layout src/settings.ts src/store/modules/settings.ts
- Run: bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed
- Expect: Changed layout passes focused checks; unrelated baseline failures are recorded.

**Dependencies:** Task 1
**Output:** Business consumes the library without copying height or scroll mechanisms.

### Task 3: Geometry, performance and delivery verification — Complete within stated evidence scope

**Files:**
- Create: isolated layout test fixture and automated geometry/performance checks
- Create: docs/reports/2026-10-13-zxui-layout-regions.md

**Steps:**
1. Verify header/tags/breadcrumb combinations for lists, natural details, mixed details, editor and iframe.
2. Verify empty/long content, viewport resizing and repeated mounting/unmounting.
3. Check observer/listener counts, idle scheduling and forced-layout traces against a same-environment baseline.
4. Build library-owned generated outputs and verify business source and installed-package consumption.
5. Request a read-only code-review subagent and resolve substantive findings.

**Verification:**
- Run: focused unit tests, library package/style checks, business type check and production build, isolated browser test runner
- Expect: Correct bounds and scroll ownership; zero observers/global listeners introduced by the generic layout; no accumulating resources or continuous idle layout work.

**Dependencies:** Task 2
**Output:** Reviewable two-repository implementation with explicit verification evidence and limitations.

## Execution Handoff

Continue current-session execution under the user's approval. The plan route does not add an approval gate.

## Status Sync Suggestion

No work item is provided. Track task completion in this plan and record final evidence in the report.

## Plan Checkpoint

STATUS: IMPLEMENTED_VERIFIED_WITH_LIMITATIONS
FILES_WRITTEN: docs/plans/2026-10-13-zxui-layout-regions.md; docs/reports/2026-10-13-zxui-layout-regions.md; two-repository implementation and isolated fixture
EVIDENCE:
- READ: repository guidance, fill contract, ContentWrap lifecycle and application shell sources.
- SEARCH: public exports, structural style manifests, height deductions and observation sites.
- COMMAND: Library 27 focused tests, business 5 focused tests, 14 UI/generator contract tests, library build, source-mode business production build and installed fixture build passed.
- BROWSER: 192 visibility/viewport/content cases passed; zero layout-owned observations/measurement/listeners/RAF; active targets stable; idle LayoutCount 0.
- REVIEW: Read-only review completed; all substantive findings fixed and rechecked.
- REPORT: docs/reports/2026-10-13-zxui-layout-regions.md records raw evidence and broader-check limitations.
PLAN_CHANGES: Added CSS stickyHeader after review; fixed X6 existing sensor target cleanup; packed matching hooks dependency; performance timings are local diagnostics, native Table is the resource control.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: none for the approved layout scope; full-project failures are documented separately
BLOCK_REASON: none for layout; existing theme manifest, type, test and whole-repository contract failures prevent a blanket full-project green claim
UNBLOCK_ACTION: See report for exact unrelated failure paths; no release or commit was requested

## Follow-up: legacy Tags-Views preference migration

The user's screenshot revealed a legacy `layout-setting.tagsView: true` overriding
the new default. Added a business-only versioned, one-time migration for that
field while preserving other preferences. Explicit choices saved by the new
settings panel survive reload. Verified RED first, then 7 focused unit tests and
real-store/real-settings headless startup/save/reload/geometry checks passed.
See the report's follow-up section and preferences.json for evidence.

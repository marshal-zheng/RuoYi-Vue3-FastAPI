# ZXUI Priority Fixes Implementation Plan

**Goal:** Fix shared GridList request races and improve readable action text across the nine built-in themes, verified through the source-linked RuoYi app.
**Inputs:** User-approved review in this task; current ZXUI and RuoYi working trees; existing theme and GridList tests.
**Scope Boundaries:** First delivery covers review priorities 1 and 2. Keep business query contracts, brand seeds, and unrelated working-tree changes. Deployment plugin, toolbar, third-party adapters, and display metrics remain subsequent work. Do not publish packages or commit.

## Task List

### Task 1: Own GridList request lifecycle

**Files:**
- Modify: ZXUI `packages/components/grid-list/src/use-grid-request.ts`
- Modify: ZXUI `packages/components/grid-list/src/grid-list.vue`
- Test: ZXUI `packages/components/grid-list/__tests__/use-grid-request.test.ts`
- Test: ZXUI `packages/components/grid-list/__tests__/grid-list.test.tsx`

**Steps:**
1. Add focused regressions for stale success/failure, pending debounce supersession, and disposal.
2. Centralize request generation and queued work ownership without changing public props or loadData payloads.
3. Release queued work and invalidate active results when the component unmounts.

**Verification:**
- Run: `pnpm exec vitest run packages/components/grid-list --cache=false` in ZXUI.
- Expect: Latest-request results survive obsolete success/failure; disposed work cannot update state or start another request.

**Dependencies:** none
**Output:** Shared lifecycle fix with bounded regression coverage.

### Task 2: Separate readable action text from fill colors

**Files:**
- Modify: ZXUI theme token derivation/contract and Element Plus adapter mappings as required.
- Modify: ZXUI `scripts/theme/check-contrast.ts` and existing related tests.
- Generate: Theme assets through their owning compiler and structural build.

**Steps:**
1. Verify the existing semantic and modifier mapping contracts before choosing the smallest compatible correction.
2. Derive readable text roles without changing theme brand seeds.
3. Correct the actual link/button/checkable-control consumers and extend existing checks to nine themes.
4. Regenerate assets and run the affected compiler and token checks.

**Verification:**
- Run: `pnpm theme:check:contrast` and focused Vitest files in ZXUI.
- Run: `pnpm theme-compiler:build` and `pnpm build:theme` in ZXUI.
- Expect: Normal-size actionable text passes the measured foreground/background pairs; generated assets match source.

**Dependencies:** Task 1
**Output:** Theme-level and adapter-level correction shared by all consumers.

### Task 3: Validate in the real consumer

**Files:**
- Create: RuoYi `docs/reports/2026-09-26-zxui-priority-fixes.md`

**Steps:**
1. Use the existing authorized browser session to inspect source-linked RuoYi across the nine light/dark themes.
2. Inspect actual operation links, selected controls, and solid buttons, including hover states where available.
3. Run the local-source production build and record evidence and remaining scope.

**Verification:**
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --outDir /tmp/ruoyi-zxui-priority-build` in RuoYi frontend.
- Run: `git diff --check` in both repositories.
- Expect: Build succeeds; actual business controls consume corrected library colors.

**Dependencies:** Task 2
**Output:** Reviewable implementation and real-consumer evidence.

## Progress

- [x] Task 1: Request lifecycle
- [x] Task 2: Readable theme roles and mappings
- [x] Task 3: Consumer verification

## Plan checkpoint

STATUS: FIRST_BATCH_COMPLETE
FILES_WRITTEN: `docs/plans/2026-09-26-zxui-priority-fixes.md`
EVIDENCE: Read GridList request/state/component code, theme derivation, adapter mappings, contrast gate, and existing tests; reproduced stale failure during the preceding review.
NEXT_ACTION: Continue the remaining review priorities in a subsequent batch.
BLOCK_REASON: none
UNBLOCK_ACTION: none

## Delivery evidence

Report: `docs/reports/2026-09-26-zxui-priority-fixes.md`.
GridList: 15 focused checks. Contrast: 3,800 static pairs across nine themes; 180 browser samples across 18 light/dark combinations. Compiler replay: 1,458 variants match. Source-linked consumer production build passed. Repository-wide pre-existing type, package-fixture, and business formatting failures are documented separately; no full-suite or release claim.

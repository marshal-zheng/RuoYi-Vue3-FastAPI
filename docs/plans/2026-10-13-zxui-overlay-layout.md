# ZXUI Shared Overlay Layout Implementation Plan

**Goal:** Unify Drawer and Dialog spacing, separator geometry, and explicit scroll ownership with one public contract and inherited, theme-aware defaults.
**Inputs:** Approved conversation design; both repository AGENTS.md files; prior divider delivery and the measured spacing review.
**Scope Boundaries:** Work in the existing checkouts. Preserve unrelated dirty files, unrelated behavior. Overlay layout APIs may be hard-cut as explicitly authorized by the user. No commits, registry publishing, device menu changes, or simulation-specific edits. Isolated headless verification is authorized; existing browsers and business services remain untouched.
**Assumptions:** ZXUI source checkout is `/Users/hqz/Downloads/element-plus`. Business consumes source in development and a packed public package for production.

## Task List

### Task 1: Shared API and inheritance contract

**Files:**
- Create: ZXUI `packages/components/_shared/overlay-layout.ts` and its component contract tests
- Modify: ZXUI ConfigProvider types/props/merge/projection, Drawer/Dialog props and Hook options

**Steps:**
1. Add failing component and Hook tests for shared Provider defaults, component-specific defaults, per-edge overrides, explicit zero and restoration to inheritance.
2. Retain padding strings and add numeric/logical-object values; expose public types.
3. Add `overlayLayout` shared defaults and compatible regional padding defaults in `zxDialog`/`zxDrawer`.
4. Add independent `bodyScroll: auto | none` and shared `paddingInline` overrides.
5. Keep all new options reactive, consumed by ZXUI, and excluded from native configuration projection.

**Verification:**
- Run: `pnpm exec vitest run packages/components/_shared/__tests__/overlay-layout.test.tsx packages/components/hooks/use-dialog/__tests__ packages/components/hooks/use-drawer/__tests__ packages/components/config-provider/__tests__`
- Expect: Missing capabilities fail before implementation; inheritance and the new public contracts pass afterward.

**Dependencies:** none
**Output:** Unified public APIs with scalar-to-partial Provider merging and no geometry measurement.

### Task 2: Structural CSS and scroll ownership

**Files:**
- Modify: ZXUI Drawer/Dialog templates, layout bindings and shared modal-scroll helper
- Modify: ZXUI structural CSS, style dependency manifest and generated mirror
- Modify: ZXUI bilingual component documentation and examples

**Steps:**
1. Place non-flow sentinel elements inside the padded content container.
2. Use one shared CSS recipe based on scoped theme/density/display roles; support public component CSS variables and per-region/per-edge overrides.
3. Draw section separators without consuming layout height.
4. Use a bounded flex viewport for delegated scroll ownership and preserve natural Dialog height.
5. Normalize logical alignment, header hit-area compensation, mobile gutters and safe-area handling.
6. Generate leaf/aggregate styles and document compatibility, inheritance, mixed layouts and delegated scrolling.

**Verification:**
- Run: affected Drawer/Dialog/Provider/Hook tests and structural style generation.
- Run: source headless layout matrix at desktop/mobile, multiple themes/densities/display scales and LTR/RTL.
- Expect: Actual content insets match configured values; divider toggles preserve geometry; delegated content owns scrolling; repeated updates add no resources.

**Dependencies:** Task 1
**Output:** Shared CSS geometry with explicit scroll ownership and documented extension points.

### Task 3: Current business integration and delivery verification

**Files:**
- Modify: business RoleFormDrawer external padding patch, public vendor reference and lockfile
- Create: business overlay layout fixture/runner and saved evidence
- Create: `docs/reports/2026-10-13-zxui-overlay-layout.md`

**Steps:**
1. Remove the role form's extra outer inline padding without changing form behavior.
2. Build/pack the public ZXUI package and retain compatible hooks resolution.
3. Verify source and installed-package layouts with real ThemeHost and real business components.
4. Verify actual role creation and a reachable Dialog in an isolated browser, without submitting business records.
5. Run focused business lint/tests, UI standards, appropriate builds/type checks, and independent read-only review.
6. Reconcile findings and save evidence, including unrelated gate limitations; keep port 80/8088 services running.

**Verification:**
- Run: `pnpm build`, focused public package/style contracts and installed fixture checks.
- Run: business focused ESLint, RoleFormDrawer tests, `yarn ui:standards`, `yarn type-check`, source production build and changed validation.
- Expect: Both consumption paths work, current business has correct spacing, and material review findings are resolved.

**Dependencies:** Task 2
**Output:** Reviewable library implementation and current-business evidence with honest validation boundaries.

## Progress

- Task 1: Complete; API, Provider/Hook inheritance and public types implemented. Baseline saved at `/tmp/zxui-overlay-layout-baseline-20261013`.
- Task 2: Complete; shared theme recipe, geometry, scroll ownership, hard-cut cleanup and docs implemented.
- Task 3: Complete; vendor installed, source/installed 156-case matrices, both 26-case divider suites, 8 actual business cases, focused checks/builds and independent review verified. Reported gate failures were resolved in the full validation follow-up.

## Plan Checkpoint

STATUS: IMPLEMENTATION_COMPLETE
FILES_WRITTEN:
- docs/plans/2026-10-13-zxui-overlay-layout.md
EVIDENCE:
- READ: Existing Drawer/Dialog/Provider/Hook implementations, scoped display/density contract, style splitter, and business role form.
- SEARCH: Regional padding APIs, configuration merging, scroll sentinels and style dependency ownership.
- COMMAND: Dirty-state inventory and 27-file pre-change snapshot completed.
NEXT_ACTION: Review the implementation and saved business screenshots.
BLOCK_REASON: none
UNBLOCK_ACTION: none

## Approved scope update

The user explicitly revoked the compatibility requirement because both library and business are in development. Remove redundant legacy layout APIs/variables/classes and migrate known consumers. Both auto bodies use normal flow-root; none explicitly delegates bounded flex/scrolling. noContentPadding is removed in favor of bodyPadding: 0.

## Initial delivery evidence (superseded by full validation)

- Focused library regression: 176 passed; broader attempt preserves 2 pre-existing ConfirmInput color assertion failures.
- Source and installed layout matrices: 156 each; divider suites: 26 each; actual business: 8 cases, no page errors or record writes.
- Library/package/fixture/source builds and UI standards passed. Existing global gate failures are documented in docs/reports/2026-10-13-zxui-overlay-layout.md.
- Independent read-only hard-cut review: no remaining P0/P1/P2.

## Full validation follow-up

User requested resolving the reported type, formatting and ConfirmInput theme assertions, updating tests to the new contract, and running full library/business frontend gates.

- [x] Correct business HTTP mock signature and refresh the public compiler package/type contract.
- [x] Fix full business formatting diagnostics without behavior changes.
- [x] Update ConfirmInput theme tests to semantic surface/field/status roles.
- [x] Resolve root type and package-contract diagnostics found by full validation.
- [x] Run full root lint/typecheck/Vitest/UI contracts/build and affected independent package checks.
- [x] Run full business lint/typecheck/Vitest/UI standards/production build and overlay/browser regression.
- [x] Reconcile independent review, preserve all verification outputs and update delivery report.

Follow-up evidence in progress: business 82 suites / 680 tests, full types, lint (0 errors / 1230 existing warnings), UI standards (505 files / 14 tests), installed production build and isolated offline Playwright core/page-state suites (1 + 8) passed. Compiler codec retains the 500000-byte gzip budget; 4 tests pass at 499009 bytes. New protocol baseline generation 3 was frozen by the official initializer from a passing isolated packed receipt; all earlier frozen bytes remain unchanged and are tested for rejection. Final library gates and reinstalled overlay regressions passed; final counts follow.

## Full validation completion

- Root lint: 0 errors / 0 warnings; five type suites and four UI contract stages pass.
- Full `pnpm test:run`: exit 0; Vitest 338 passed files / 2474 passed tests, two default opt-in timing skips; Node 39/39, MCP 84/84, authority 3 personas / 21 stages valid. Required opt-in timing files were additionally run serially, 3/3 passed.
- Full business frontend: lint 0 errors / 1230 existing warnings; typecheck, 680 tests, 505-file UI standards / 14 tests, installed production build and offline E2E 1+8 pass. Final public compiler rebuilt/reinstalled after the asset watcher/transaction fix; types/build and actual business 8-case browser verification pass again.
- Source and installed overlay matrices: 156 each; divider 26 each; actual business 8 cases, no page errors or role/user writes.
- ConfirmInput and all related semantic assertions migrated; readonly unit race fixed with a real isolated Git fixture; actual compiler asset recovery defect fixed with CSS-only and transaction RED/GREEN, final 9/9.
- Independent read-only reviews: all reported P2s closed; no remaining P0/P1/P2 in this increment. Historical composite/release receipts remain unchanged; these are local standard gate results.
- Complete evidence: docs/reports/evidence/2026-10-13-zxui-overlay-layout/full-validation/.
- No commits or publication. Temporary browser fixture servers stopped; normal 80/8088 services preserved.

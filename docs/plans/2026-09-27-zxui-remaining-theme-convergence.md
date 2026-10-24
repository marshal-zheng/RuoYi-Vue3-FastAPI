# Remaining Theme Convergence Implementation Plan

**Goal:** Close the previously listed non-simulation theme gaps in RuoYi and the reusable ZXUI source integration boundary.
**Inputs:** 2026-09-26 business theme audit, priority fixes, Vite deployment, list toolbar and table density reports; user authorization to continue all remaining work.
**Scope Boundaries:** Active non-simulation topology UI, form designer, Quill/VXE adapters, confirmed residual UI colors, narrow navbar and official source integration. Preserve saved content, domain/category colors and graph coordinates. Simulation-only sources, display scaling, npm publishing and commits are excluded.

## Task List

### Task 1: Topology and form designer

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/components/business/ZxFlow/components/`, `src/components/business/Dag/`, `src/views/device/detail.vue`, `src/views/tool/build/`.
- Create: a business topology adapter using the existing public ZXUI theme consumption API, only if inspection confirms it is needed.

**Steps:**
1. Inspect active consumers and distinguish presentation from saved graph/domain values.
2. Read committed theme values through the public Host API for canvas repaint; use semantic CSS for DOM/SVG chrome.
3. Replace designer chrome literals and inspect generated code for theme ownership.
4. Verify real pages and use one in-memory fixture for otherwise unavailable states.

**Verification:**
- Run: `yarn type-check` and `yarn ui:standards` in the frontend.
- Expect: passing checks; theme switching changes UI without changing graph/content data.

**Dependencies:** none.
**Output:** Theme-aware graph chrome and form designer.

### Task 2: Third-party adapters and business shell

**Files:**
- Modify: `src/components/ui/Editor/index.vue`, `src/plugins/vxe-table.ts`, `src/layout/components/Navbar.vue`, scoped active residual consumers.
- Create: `src/assets/styles/vxe-theme.css` if the installed VXE public variables permit a narrow adapter.

**Steps:**
1. Inspect installed third-party styles and active consumers.
2. Adapt toolbar, field, table, overlay and state surfaces without rewriting user content colors.
3. Repair navbar shrinking/overflow and confirmed residual UI colors.
4. Verify representative pages in light/dark themes and narrow viewports.

**Verification:**
- Run: scoped ESLint on edited TS/Vue files; distinguish existing diagnostics from new ones.
- Expect: no new diagnostics; readable UI and reachable navbar controls.

**Dependencies:** Task 1 inspection.
**Output:** Third-party UI consumes ZXUI tokens, responsive navbar.

### Task 3: Official source integration

**Files:**
- Modify: ZXUI `packages/theme-compiler/src/vite/`, relevant tests/docs and business `vite.config.ts`.

**Steps:**
1. Compare existing source aliases with library-owned resolver conventions.
2. Move reusable source resolution into an exported Vite integration and retain business environment selection only.
3. Add focused resolution regression coverage, build and pack through package owners.
4. Update the business local candidate and verify source/installed builds.

**Verification:**
- Run: `pnpm exec vitest run packages/theme-compiler/__tests__/vite.test.ts` in ZXUI, plus new focused source resolver test if needed.
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod` and `VITE_ZXUI_LOCAL=false yarn build:prod` in RuoYi, with separate temporary output directories.
- Expect: both builds pass and application config no longer owns ZXUI package internals.

**Dependencies:** none.
**Output:** Reusable public source integration with local package delivery.

### Task 4: Reconcile the full inventory

**Files:**
- Create: `docs/reports/2026-09-27-zxui-remaining-theme-convergence.md` and focused evidence.

**Steps:**
1. Recheck every outstanding audit entry against the final implementation.
2. Run targeted checks and browser coverage for changed consumers.
3. Restore the original theme/viewport and record limitations explicitly.
4. Mark only verified scope complete and list any concrete remaining blocker.

**Verification:**
- Run: plan/report link checks and `git diff --check` on changed paths.
- Expect: every original outstanding item has implementation/verification or an explicit evidence-based disposition.

**Dependencies:** Tasks 1–3.
**Output:** Reconciled completion report.

## Progress

- [x] Topology and form designer
- [x] Third-party adapters and business shell
- [x] Official source integration
- [x] Final verification and inventory reconciliation

## Plan checkpoint

STATUS: IMPLEMENTATION_VERIFIED
FILES_WRITTEN: docs/plans/2026-09-27-zxui-remaining-theme-convergence.md
EVIDENCE:
- READ: root guidance, audit reports, graph/grid/background/minimap, designer CSS, Quill/VXE styles, Navbar, business Vite aliases, public Host consumption API.
- SEARCH: active imports, literal colors, theme revision and adapter interfaces.
- COMMAND: 42 library tests, 14 business standards tests, type-check, scoped lint, structural audit and both production builds passed.
- BROWSER: 18 theme states; real designer/device/notice pages and 3 navbar widths checked.
- REPORT: docs/reports/2026-09-27-zxui-remaining-theme-convergence.md. See explicit browser coverage limits.
NEXT_ACTION: None within this plan. Local candidates delivered; publishing and commits remain outside scope.
BLOCK_REASON: none.
UNBLOCK_ACTION: none.

## Execution Handoff

Continue in this session under the existing user authorization; no additional approval gate.

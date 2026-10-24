# ZXUI List Toolbar Integration

## Goal and contract

Move the reusable list action/filter/search layout from RuoYi into ZXUI. Keep queries, permissions, field widths, requests and action callbacks in the consuming application. The component has three named slots (`actions`, `filters`, `search`), no model, no events and no imperative API. Root attributes are forwarded to a native group; controls retain normal Tab navigation. Layout wraps according to available container width and consumes existing theme density spacing.

## Evidence and scope

- RuoYi `ruoyi-fastapi-frontend/src/assets/styles/components.less` owns two duplicate toolbar rule sets with fixed 12px/10px gaps and non-wrapping filters.
- 23 Vue files use `zx-grid-form-bar`; none is simulation-only. The user page at a 1024px viewport has a 536px toolbar and 1064px scroll width.
- ZXUI `packages/components/grid-list/src/grid-list.vue` already exposes a `form` slot; standalone department/menu lists also need this layout. Keep GridList's request/state contract unchanged.
- Preserve unrelated dirty work. Legacy RightToolbar column configuration is a separate issue.

## Execution

- [x] Add `packages/components/list-toolbar/{index.ts,src/list-toolbar.vue,style/index.ts,style/css.ts}` and focused slot/ownership regression coverage. Register in components and ZXUI root, add `packages/zxui/list-toolbar` leaf proxies, package exports/files and UI package contracts. Add the owned section to `packages/theme-chalk/src/structural.css` and its component style manifest entry. Document both languages and a runnable example.
- [x] Replace the 23 legacy wrapper trees with named slots without changing their contents. Remove only the legacy toolbar rules from business `components.less`. Validate all migrated SFC templates and verify their scripts and control attributes remain unchanged.
- [x] Build library styles/UI through their owning pipelines, pack a local UI candidate, update the business vendor dependency. Run focused library tests, business type-check, scoped lint, and source/installed production builds. Verify user/role/department lists at wide and narrow widths, searching and themes in the real browser. Restore the original viewport and army-pine dark preference.

## Verification and delivery

Use focused Vitest tests for slot behavior and consumer-owned state; use actual browser measurements for CSS wrapping rather than implementation-mirroring style assertions. Record build/test results and browser receipts under `docs/reports/2026-09-26-zxui-list-toolbar.md` and its evidence directory. Do not publish or commit.

## Plan checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-09-26-zxui-list-toolbar.md
EVIDENCE:
- READ: both AGENTS.md files, Vue component skill, components.less, GridList, public package exports and style manifest.
- SEARCH: zx-grid-form-bar (23 consumers and business LESS rules); no library component owns this layout.
- COMMAND: browser computed layout confirms 536px client / 1064px scroll width at 1024px viewport.
PLAN_CHANGES: Corrected the initial incomplete search: business LESS does define the legacy layout.
WORK_ITEM_SYNC_SUGGESTION: none (no work item provided).
NEXT_ACTION: Implement the library component and migrate existing consumers.
BLOCK_REASON: none.
UNBLOCK_ACTION: none.


## Completion evidence

All three steps are complete. See `docs/reports/2026-09-26-zxui-list-toolbar.md` and its evidence directory for 18 passing focused tests, successful source/installed builds, public-package smoke checks, unchanged business logic checks, and browser results. The full package-contract gate remains blocked by independent chart/drive declarations; business scoped lint retains exactly 49 pre-existing formatting errors and no new diagnostics. The viewport and army-pine dark preference were restored.


## Evidence-driven amendment: Search clear ordering

Browser verification reproduced a library defect: the clear action emits clear/search while the controlled query still contains the previous text. A focused regression failed with `clear:admin`, `search:admin`, then `model:`. Update the existing Search value watcher to flush synchronously so the existing event contract reaches consumers in model/clear/search order. Keep this bounded to event ordering; rerun Search and shortcut tests, rebuild/repack the local UI candidate, and repeat both business builds and real clear-to-reset verification. Final completion evidence below supersedes the earlier toolbar-only checks.


Final amendment status: complete. The Search ordering regression failed before the fix and passed afterward. All 18 focused tests, the updated local UI build, both business production builds and installed-package type-check passed. The browser confirmed `admin` gives one result and a single clear click restores two results. Final local candidate: `zxio-zxui-3.0.0-next.0-toolbar.20260926.1.tgz`.

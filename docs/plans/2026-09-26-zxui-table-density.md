# Table Theme and Density Convergence

## Scope

Use ZXUI theme values for native Element Plus tables and GridList consumers. Preserve requests, permissions, column widths, alignment and explicit component sizes. Simulation-only sources and TableV2 are outside this change. No new theme tokens, table wrapper or compiler artifact migration is needed.

## Evidence

RuoYi components.less fixes font size at 14px, headers at 60px and body cells at 56px. Browser measurements confirm those values in the real user list. Element Plus table.scss hardcodes size-specific cell padding and 23px text line height; ZXUI currently maps colors and control sizes but has no table density structure rules. Existing theme preferences support density but the production theme menu has no density selector.

### Task 1: Library structural density

**Files:** `/Users/hqz/Downloads/element-plus/packages/theme-chalk/src/structural.css`; existing style tests and GridList example as needed.

**Steps:** Add table cell spacing and line height to the existing Element Plus skin section using semantic spacing/typography. Preserve small/default/large offsets, gutter/expanded cells and special column geometry. Inspect striped/current/hover/fixed-column precedence and fix only confirmed gaps.

**Verification:** `pnpm build:theme`; focused style policy/splitting checks; browser computed geometry and state checks.

**Dependencies:** Baseline source and browser inspection complete.

**Output:** One library-owned density implementation for raw tables and GridList.

### Task 2: Business integration

**Files:** `ruoyi-fastapi-frontend/src/assets/styles/components.less`; `ruoyi-fastapi-frontend/src/theme/ZxThemePresetSwitch.vue`.

**Steps:** Remove generic table paint/height/font overrides; retain operation-column layout with theme spacing. Expose existing compact/default/comfortable preferences in the current theme menu through setZxThemePreference, without a second store or reload.

**Verification:** Focused lint/type-check; real user, role and log list checks across densities and light/dark modes. Verify selection, multi-line content and scrolling. Use a focused fixture only for states not represented in local data.

**Dependencies:** Task 1 structural implementation.

**Output:** Business tables consume the library contract and users can select density normally.

### Task 3: Delivery and reconciliation

**Files:** ZXUI generated style mirror and built UI package; business local vendor candidate, package.json/yarn.lock; `docs/reports/2026-09-26-zxui-table-density.md` and evidence directory.

**Steps:** Build and pack through library owners, update local business dependency, verify source and installed production builds. Record actual check results and existing failures. Restore army-pine dark/default density and original viewport. Do not publish or commit.

**Verification:** Library build; business source/installed builds; installed package style inspection; report links and receipts.

**Dependencies:** Tasks 1 and 2 pass relevant checks.

**Output:** A locally reviewable two-repository delivery.

## Progress

- [x] Library implementation and focused checks
- [x] Business integration and browser validation
- [x] Package delivery and report

## Execution Handoff

Continue implementation in this session under the user's approval.

## Status Sync Suggestion

No work item was provided; no work item files are changed.

## Plan checkpoint

STATUS: COMPLETE
FILES_WRITTEN: docs/plans/2026-09-26-zxui-table-density.md; docs/reports/2026-09-26-zxui-table-density.md
EVIDENCE:
- READ: repository guidance, table.scss, theme mapping, structural skin, business styles and preference control.
- SEARCH: table selectors, density mappings and production density entry points.
- COMMAND: real user-page measurement confirms 60px header / 56px row / 14px font.
PLAN_CHANGES: Exposed the existing density preference. Browser evidence confirmed alpha state fills on sticky cells leaked scrolling text; fixed this in the library with an opaque backing and theme-owned state layer. Added one policy regression and a two-file fixture for 18 density/size/wrapper combinations.
WORK_ITEM_SYNC_SUGGESTION: none.
NEXT_ACTION: None for this batch. See the delivery report for evidence and remaining business layout work.
BLOCK_REASON: none.
UNBLOCK_ACTION: none.

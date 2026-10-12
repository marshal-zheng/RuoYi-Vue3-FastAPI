# Remaining Theme Integration Plan

WORK_ITEM: none

**Goal:** Remove remaining business theme overrides and reuse public ZXUI capabilities for Tailwind, tables, dialogs and charts.
**Inputs:** Existing dirty checkout, source-linked application, repository guidelines and browser observations.
**Scope Boundaries:** No lint/build/test commands or new tests. Simulation-specific visualizations retain their existing domain palette. No publishing or commits.
**Assumptions:** Existing generated themes are available. Keep domain choices in the business and reusable adapters in the library.

## Task List

1. Audit global Tailwind recipes, table adapters, blocking surfaces and chart consumers. Compare browser computed styles before edits.
2. Consume the public Tailwind contract, consolidate duplicate component recipes, and migrate existing semantic utility consumers without redefining standard color scales.
3. Publish the existing VXE variable bridge as an opt-in ZXUI CSS export; correct shared dialog/drawer/table surface pairing in owning CSS sources.
4. Verify cache charts, tooltips, tables and form dialogs in branded light/dark modes through local sources; fix demonstrated chart adapter issues at their owner.
5. Record ownership decisions, screenshots, remaining boundaries and diff whitespace checks.

**Files:** Business `src/assets/styles`, semantic Tailwind consumers, VXE plugin, dependency catalog; ZXUI structural source, optional CSS exports/build copy, source integration; chart package only if inspection demonstrates a reusable defect.
**Verification:** Authorized browser UI actions, computed styles, console diagnostics, targeted source inspection and `git diff --check`. No synthetic test suite or release validation.
**Dependencies:** Audit precedes edits; browser verification follows source hot updates.
**Output:** Reviewable implementation and evidence report.

## Execution Handoff

Continue immediately in this session under existing authorization.

## Status Sync Suggestion

None. Track observed results in the implementation report.

## Plan-Stage Checkpoint

STATUS: PLAN_DRAFTED
EVIDENCE: Read both repository guidelines, public Tailwind adapter, dialog/table structural CSS, business VXE bridge and cache chart projection. Browser confirmed active dark theme and real user form dialog.
NEXT_ACTION: Implement verified ownership corrections.

## Execution Result

Implemented the public Tailwind consumption path, optional VXE bridge, blocking foreground corrections and GridList state precedence. Audited cache charts without changing their independent package; corrected business SVG port paints and residual shared UI colors. Browser observations, screenshots and explicit coverage limits are in `../reports/2026-10-11-zxui-theme-remaining.md`. No lint/build/tests were run.

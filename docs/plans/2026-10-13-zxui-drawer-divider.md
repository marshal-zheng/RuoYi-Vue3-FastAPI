# ZXUI Drawer Divider Implementation Plan

WORK_ITEM: none

**Goal:** Give Drawer the same optional divider policy as Dialog, with CSS-only rendering and business-owned global defaults and local overrides.
**Inputs:** Approved conversation contract; both repositories' AGENTS.md; ZXUI Drawer, Dialog, ConfigProvider, useDrawer and structural style sources. No steering index is present.
**Scope Boundaries:** ZXUI owns component/Provider/Hook contracts and theme-aware section borders. Business owns global defaults and local overrides. Preserve existing portal, focus, resize, scroll, footer, spacing and unrelated changes. No simulation-specific source edits, publishing or commits.
**Assumptions:** Source checkout is /Users/hqz/Downloads/element-plus. Existing authorization permits isolated headless browser verification.

## Task List

### Task 1: Contract and regression coverage

**Status:** Complete. RED failures confirmed before implementation; the affected Drawer/ConfigProvider/Hook/Dialog regression suite passes 135 tests.

**Files:**
- Modify: ZXUI packages/components/{drawer/src/props.ts,drawer/src/drawer.vue,config-provider/src/{props.ts,types.ts,merge.ts,use-global-config.ts},hooks/use-drawer/index.ts}
- Create: ZXUI packages/components/drawer/__tests__/drawer.divider.test.tsx
- Modify: ZXUI packages/components/{config-provider/__tests__/merge.test.ts,hooks/use-drawer/__tests__/use-drawer.test.ts}

**Steps:**
1. Add failing tests for explicit true/false, Provider inheritance/overrides, reactive updates and Hook propagation.
2. Declare divider with undefined as the inheritance sentinel; effective fallback is false.
3. Add zxDrawer configuration to public types, props, nested merge and Element Plus projection exclusion.
4. Bind a computed root class, consuming the prop without forwarding it to the native Drawer.
5. Pass Hook options without defaulting them, preserving inheritance and updateOptions behavior.

**Verification:**
- Run: cd /Users/hqz/Downloads/element-plus && pnpm exec vitest run packages/components/drawer/__tests__/drawer.divider.test.tsx packages/components/config-provider/__tests__/merge.test.ts packages/components/hooks/use-drawer/__tests__/use-drawer.test.ts
- Expect: RED before implementation, then explicit component > nearest Provider > false; no added resource lifecycle.

**Dependencies:** none
**Output:** Public, reactive policy shared with Dialog's precedence.

### Task 2: CSS delivery, documentation and business integration

**Status:** Complete. Structural mirror, leaf styles, docs, business global defaults, five retained explicit opt-ins and the installed public vendor package are delivered. RoleFormDrawer inherits the global divider setting; the user confirmed it through role creation. ZXUI build and focused public contracts pass.

**Files:**
- Modify: ZXUI packages/theme-chalk/src/structural.css
- Modify: ZXUI docs/{zh-CN,en-US}/component/{drawer,dialog,config-provider}.md
- Create: ZXUI docs/examples/drawer/divider.vue
- Modify: selected business editing Drawer Hook options
- Modify: business src/App.tsx and src/views/project/components/NodeEditDrawer.vue for global enablement and one local disable override
- Modify: business vendor dependency and yarn.lock

**Steps:**
1. Remove unconditional Drawer section borders and apply them only under the divider class.
2. Add Drawer-specific header/footer/common CSS variables with the same shared overlay fallback as Dialog.
3. Keep section spacing, scrolling, shadows and geometry ownership outside divider rules.
4. Document migration, inheritance, Hook use and style overrides; regenerate structural mirror.
5. Per the user's follow-up, enable zxDrawer.divider globally in business App and explicitly disable it in NodeEditDrawer for manual comparison. Keep five dense editing drawers explicitly enabled; remove RoleFormDrawer's local true so role creation demonstrates global inheritance. Keep the library default false. Confirm the accessible role menu; do not add the absent device menu for verification.
6. Build and pack the public library and consume it through the business vendor reference.

**Verification:**
- Run: ZXUI structural generation, focused ESLint, pnpm build and selected public package contracts.
- Run: business focused lint/tests and UI standards.
- Expect: Leaf/aggregate style parity, no business substitute for library types, explicit business decisions and correct installed-package consumption.

**Dependencies:** Task 1
**Output:** CSS-only divider delivery and documented, explicit migration.

### Task 3: Browser, resources and review

**Status:** Complete. Source and installed-package Chromium checks pass all policy/geometry cases and lifecycle checks. Independent read-only review has no substantive findings. Existing full-project gate limitations are recorded in the delivery report.

**Files:**
- Create: ruoyi-fastapi-frontend/tests/fixtures/drawer-divider/{App.vue,index.html,main.ts,vite.config.ts,README.md}
- Create: ruoyi-fastapi-frontend/scripts/check-drawer-divider.mjs
- Create: docs/reports/2026-10-13-zxui-drawer-divider.md and browser evidence

**Steps:**
1. Verify modal/inline/push, footer/header absence, custom footer, nested Provider, Hook updates and theme overrides.
2. Verify header/footer spacing, body scroll ownership, resize/fullscreen/mobile geometry and preserved scroll position.
3. Compare observer/listener/measurement counts before and after repeated divider toggles; measure idle layout work after animations settle.
4. Request a read-only review and resolve substantive findings.
5. Record commands, raw browser evidence and unrelated full-project gate failures.

**Verification:**
- Run: isolated headless Chromium runner, affected Drawer/ConfigProvider/Hook tests, business type/build checks as appropriate.
- Expect: Correct border policy and layout; no additional observer/listener/continuous measurement path or resource accumulation.

**Dependencies:** Task 2
**Output:** Reviewable implementation with bounded performance and geometry evidence.

## Execution Handoff

Current-session implementation and independent review are complete under the user's explicit implementation request. No commit or registry publishing was requested.

## Status Sync Suggestion

No work item is provided; no work-item status was changed. Execution evidence is recorded in docs/reports/2026-10-13-zxui-drawer-divider.md.

## Plan Checkpoint

STATUS: PLAN_UPDATED
FILES_WRITTEN:
- docs/plans/2026-10-13-zxui-drawer-divider.md
EVIDENCE:
- READ: component/provider/hook/style sources and both repository instructions.
- SEARCH: public configuration, stylesheet ownership and business Drawer consumers.
- COMMAND: RED contract tests, 135 affected regression tests, ZXUI build/public contracts, business focused tests/UI standards and source/installed browser checks completed; report records gate limitations.
PLAN_CHANGES:
- All three tasks completed; isolated fixture paths and verification evidence added.
- Shared overlay fallback also retains MessageBox's existing Dialog-variable appearance; no MessageBox visibility policy changed.
- Business follow-up reconciled: five explicit true overrides, RoleFormDrawer inheriting global true, and NodeEditDrawer explicitly false. Role creation is the user-confirmed accessible entry; the local database has no matching device menu records.
WORK_ITEM_SYNC_SUGGESTION:
- none
NEXT_ACTION: Return the reconciled records and running service status to the user; await the next request.
BLOCK_REASON: none
UNBLOCK_ACTION: none

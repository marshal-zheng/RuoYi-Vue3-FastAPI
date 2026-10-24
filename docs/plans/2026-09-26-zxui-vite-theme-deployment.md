# ZXUI Vite Theme Deployment Implementation Plan

WORK_ITEM: none

**Goal:** Make verified theme delivery a reusable ZXUI Vite capability and consume it from RuoYi without maintaining a second deployment implementation.
**Inputs:** The approved cross-repository review; RuoYi `vite/zxui-theme-packages.ts`; ZXUI deployment emitter and docs deployment plugin.
**Scope Boundaries:** Public theme deployment plugin, source-workspace theme resolution, raw asset delivery, isolated build output, update/disposal lifecycle, RuoYi adoption and focused verification. Docs retains its specialized catalog compression and SSR bootstrap. Component source aliases, list toolbars, third-party adapters, scaling and simulation pages remain separate batches.
**Assumptions:** Both repositories contain existing user changes to preserve. No steering README exists. The previously authorized local browser validation remains available. No npm publication or commit is needed.

## Task List

### Task 1: Publish the reusable build-tool boundary

**Files:**
- Create: ZXUI `packages/theme-compiler/src/vite/index.ts`
- Create: ZXUI `packages/theme-compiler/src/vite/assets.ts`
- Modify: ZXUI `packages/theme-compiler/{package.json,scripts/build.ts,README.md}`
- Modify: ZXUI `docs/.vitepress/build/theme-deployment.ts`
- Test: ZXUI `packages/theme-compiler/__tests__/vite.test.ts`

**Steps:**
1. Add a public `@zxio/theme-compiler/vite` facet with one deployment plugin and shared asset routing.
2. Resolve installed packages or explicitly selected ZXUI workspace packages through public exports.
3. Use per-instance temporary output and Rollup asset emission, preserving CSS hashes and keeping application public directories untouched.
4. Refresh after exported manifest changes or atomic directory replacement; preserve the last valid deployment on failure and close watchers in middleware mode too.
5. Reuse asset routing in docs while retaining its catalog and SSR behavior.

**Verification:**
- Run in ZXUI: `pnpm exec vitest run packages/theme-compiler/__tests__/vite.test.ts scripts/theme-delivery/theme-deployment-dev-server.test.ts`
- Run in ZXUI: `pnpm --filter @zxio/theme-compiler build`
- Expect: raw dev/build assets, base paths, package identity checks, source refresh and lifecycle tests pass; ESM/CJS/types expose the new facet.

**Dependencies:** none
**Output:** A reusable public plugin and bounded regression evidence.

### Task 2: Adopt from RuoYi

**Files:**
- Modify: RuoYi `ruoyi-fastapi-frontend/vite/zxui-theme-packages.ts`
- Modify: RuoYi `ruoyi-fastapi-frontend/vite.config.ts`
- Modify: RuoYi `ruoyi-fastapi-frontend/src/theme/{zx-theme-deployment.test.ts,theme-deployment.d.ts,zx-theme-host.ts}` as needed for public types
- Modify: RuoYi compiler vendor package and dependency lock only if required for installed-mode availability

**Steps:**
1. Reduce business build code to the single theme catalog and public plugin configuration.
2. Replace hand-written deployment data types with the public compiler output type.
3. Move the old owned public asset directory to a temporary backup to avoid copying stale legacy deployment output.
4. Keep source mode and installed-package mode resolvable without an npm release.

**Verification:**
- Run in frontend: `yarn vitest run src/theme/zx-theme-deployment.test.ts`
- Run in frontend: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --outDir /tmp/ruoyi-zxui-vite-build`
- Expect: catalog checks and production build pass; all deployed CSS hashes match their map.

**Dependencies:** Task 1
**Output:** Business integration delegates theme delivery to ZXUI.

### Task 3: Validate the real page and record boundaries

**Files:**
- Create: RuoYi `docs/reports/2026-09-26-zxui-vite-theme-deployment.md`
- Modify: this plan

**Steps:**
1. Restart the existing source-linked Vite server with the rebuilt compiler.
2. Verify theme/mode switching on the real user-management page and a form dialog.
3. Record focused checks, before/after ownership, and remaining priorities.

**Verification:**
- Run both repositories: `git diff --check`
- Browser: real page, theme identity, loaded styles, theme switching and dialog appearance.
- Expect: no delivery regression; state restored to the user's original theme.

**Dependencies:** Task 2
**Output:** Evidence-backed completion report.

## Execution Handoff

Continue current-session execution after plan verification. The user already approved implementation; no additional planning approval is required.

## Status Sync Suggestion

No work item is bound. Execution is starting; completion will be based on implementation and validation evidence.

## Plan-stage Checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: this plan
EVIDENCE: READ deployment emitter, docs plugin, business integration and package exports; SEARCH existing deployment tests and virtual modules; COMMAND repository status and path discovery passed.
PLAN_CHANGES: Scoped this batch to the theme delivery build boundary.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: current-session execution
BLOCK_REASON: none
UNBLOCK_ACTION: none

## Progress

- [x] Task 1
- [x] Task 2
- [x] Task 3

Implementation evidence is recorded in `docs/reports/2026-09-26-zxui-vite-theme-deployment.md` and its evidence directory. The new compiler facet required matching local vendor theme packages because adapter identities are intentionally exact. Nine theme tarballs and the compiler tarball were packed locally without npm publication; old tarballs remain available for rollback. Source and installed deployment maps are identical, with 2,934 CSS entries verified in each mode. The original public output was verified against its owner inventory and moved to `/tmp/ruoyi-zxui-vite-before/public-zx-theme-assets`.

The compiler package now resolves dependency symlinks during declaration generation: preserving pnpm's Vite symlink hid its Rollup dependency and broke Plugin types. This is scoped to the compiler package and its declaration builder.

Library integration/docs checks passed (11); application catalog/Host checks passed (4); application type-check passed. The real page completed 18 theme/mode selections with computed style evidence and a dialog screenshot. A keybindings event diagnostic observed during browser automation is recorded separately and is not a theme-delivery failure.

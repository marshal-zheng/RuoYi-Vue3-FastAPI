# HTTP Source Integration and Timeout Precedence Implementation Plan

**Goal:** Resolve business HTTP requests to the ZXUI checkout in local mode and honor explicit export timeouts.
**Inputs:** Approved chat scope; business `vite/zxui-theme-packages.ts` and `src/api/project/version.ts`; ZXUI `packages/http` and `packages/theme-compiler/src/vite/source.ts`.
**Scope Boundaries:** Include HTTP source resolution, shared Axios ownership, timeout precedence, focused regression coverage, and real backend exports. Exclude cancellation, retry, deduplication, response-pipeline changes, and npm publication. Preserve the preceding Axios upgrade and existing workspace changes.
**Assumptions:** Continue in the current workspaces for live source integration. No repository steering directory is present.

## Task List

### Task 1: Add opt-in HTTP source integration

**Files:**
- Modify: ZXUI `packages/http/package.json`, `packages/theme-compiler/src/vite/source.ts`
- Modify: business `ruoyi-fastapi-frontend/vite/zxui-theme-packages.ts`
- Test: ZXUI `packages/theme-compiler/__tests__/source-vite.test.ts`

**Steps:**
1. Add a focused failing resolution test.
2. Expose the HTTP workspace source through the existing public-export convention.
3. Extend the public source plugin and enable HTTP in the business integration.

**Verification:**
- Run: `./node_modules/.bin/vitest run packages/theme-compiler/__tests__/source-vite.test.ts --cache=false` in ZXUI.
- Expect: HTTP resolves to `packages/http/src/index.ts`, Axios is deduplicated, and non-opted-in features remain unchanged.

**Dependencies:** none
**Output:** Opt-in source integration owned by ZXUI and consumed by the business.

### Task 2: Honor explicit request timeout values

**Files:**
- Modify: ZXUI `packages/http/src/client.ts`, `packages/http/README.md`
- Test: ZXUI `packages/http/__tests__/client.test.ts`

**Steps:**
1. Add focused failing timeout-precedence cases, including zero and binary export requests.
2. Resolve explicit request options before request Axios configuration, then client defaults.
3. Preserve upload/download presets and document ordinary-request Axios timeout fallback.

**Verification:**
- Run: `./node_modules/.bin/vitest run packages/http/__tests__ --cache=false` in ZXUI.
- Expect: explicit export timeout is 120000 milliseconds and existing package tests pass.

**Dependencies:** Task 1
**Output:** A library-owned timeout correction with focused regression coverage.

### Task 3: Validate actual source resolution and business exports

**Files:**
- Read: business `ruoyi-fastapi-frontend/src/api/project/version.ts`
- Create: `docs/reports/2026-10-15-http-source-timeout.md`

**Steps:**
1. Start local backend and frontend using the repository runtime instructions.
2. Confirm Vite resolves HTTP to the source checkout and Axios to the business installation.
3. Log in through the business client and export an existing local version as Word, Excel ZIP, and XML.
4. Inspect the dispatched XHR timeout and downloaded bytes, then run relevant quality checks and review the diff.

**Verification:**
- Run: focused source/plugin tests, business `yarn type-check`, lint and `yarn build:prod`.
- Expect: source paths are confirmed; real export responses contain valid files and dispatch with a 120000 millisecond timeout.

**Dependencies:** Task 1, Task 2
**Output:** A concise verification report with source-resolution and export evidence.

## Execution Handoff

Continue implementation and verification in the current session. No work-item status update or commit is required.

## Status Sync Suggestion

None; this plan follows the explicit chat request and is not attached to a work item.

## Plan-stage Checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN: docs/plans/2026-10-15-http-source-timeout.md
EVIDENCE: READ public source plugin and timeout pipeline; SEARCH actual business export functions; COMMAND plan structure verification passed.
PLAN_CHANGES: Three dependent tasks, scoped to local source integration and timeout precedence.
WORK_ITEM_SYNC_SUGGESTION: none
NEXT_ACTION: current-session execution
BLOCK_REASON: none
UNBLOCK_ACTION: none

## Execution Results

- Task 1 completed: actual Vite resolution points to HTTP source and consumer Axios 1.20.0. Compiler public types were delivered through one local vendor package.
- Task 2 completed: focused red/green timeout cases and the HTTP package suite pass. Upload/download presets are preserved.
- Task 3 completed: three actual business export formats and a 65043ms delayed XML response passed with a 120000ms XHR timeout. Library and business checks passed, including business tests with HTTP source resolution.
- Review completed without actionable findings. The detailed report records dataset and distribution limitations: `docs/reports/2026-10-15-http-source-timeout.md`.

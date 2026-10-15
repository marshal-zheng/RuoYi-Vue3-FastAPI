# HTTP Response Pipeline Implementation Plan

WORK_ITEM: none

**Goal:** Run all response processors before one success decision and final response extraction, without allowing a plugin to terminate the pipeline.
**Inputs:** Approved chat scope; ZXUI HTTP client, grid-list plugin, response hook types/tests; business HTTP transforms and list APIs.
**Scope Boundaries:** Include response-hook composition, envelope-preserving list processing, native/raw response options, focused regressions and real business validation. Exclude downloads, query/body semantics, duplicate-request policy, retries, timeout, cancellation and logging improvements.
**Assumptions:** Continue in both current dirty workspaces and preserve previous HTTP changes. No `docs/steering/README.md` exists. No computer use is authorized or needed.

## Task List

### Task 1: Reproduce and fix the library response sequence

**Files:**
- Modify: ZXUI `packages/http/src/client.ts`, `packages/http/src/plugins/grid-list.ts`, `packages/http/src/types.ts`, `packages/http/src/resolvers.ts`, `packages/http/README.md`
- Test: ZXUI `packages/http/__tests__/client.test.ts`, `packages/http/__tests__/grid-list-plugin.test.ts`

**Steps:**
1. Add focused failing assertions for continuation after payload returns, runtime hooks, wrapped list success/failure and native/raw modes.
2. Keep all response processors in registration order and move the terminal success/extraction stage outside that list.
3. Preserve list protocol envelopes and processed payloads so the final resolver receives the correct response.
4. Document hook return semantics, execution order and the existing native/raw bypass behavior.

**Verification:**
- Run: `cd /Users/hqz/Downloads/element-plus && pnpm exec vitest run packages/http/__tests__`.
- Run: targeted ESLint and `pnpm -C packages/http build`.
- Expect: new regressions fail before implementation, then all HTTP tests, lint and package type/build checks pass.

**Dependencies:**
none
**Output:**
One library-owned response-processing contract with focused regression coverage.

### Task 2: Validate the real business through source integration

**Files:**
- Create: `docs/reports/2026-10-15-http-response-pipeline.md` and sanitized evidence JSON

**Steps:**
1. Start the local backend using the repository runtime instructions.
2. Execute actual login, project/role/dictionary lists, native/raw list responses and a real validation failure through business functions and ZXUI HTTP source.
3. Confirm list metadata, original response headers, final success decision and appended response hooks survive the complete pipeline.
4. Perform read-only review of the final library change.

**Verification:**
- Run: temporary JSDOM XHR probe against FastAPI :8088.
- Run: business API/utils/login tests using a temporary HTTP source alias.
- Expect: actual list pages keep their data shape; later hooks run; native response remains complete; real failures still reject once with original context.

**Dependencies:**
Task 1
**Output:**
Sanitized actual-backend evidence and reviewed implementation.

### Task 3: Deliver the matching local package and complete checks

**Files:**
- Modify: business `ruoyi-fastapi-frontend/package.json`, `ruoyi-fastapi-frontend/yarn.lock`
- Create: business local HTTP vendor tarball from the verified ZXUI dist

**Steps:**
1. Package the current library dist without publishing npm and update the existing local HTTP dependency.
2. Repeat the actual-backend probe and relevant business tests in installed mode.
3. Run business type/lint checks and explicit source/installed production builds.
4. Record results and stop only the backend service started for this task.

**Verification:**
- Run: `yarn type-check`, `yarn lint:check`, `./node_modules/.bin/vitest run src/api src/utils src/store/modules/user.login.test.ts --coverage.enabled=false` in the frontend.
- Run: `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod` and `VITE_ZXUI_LOCAL=false yarn build:prod` with separate temporary output directories.
- Run: `git diff --check` in both repositories.
- Expect: source and installed contracts agree; all applicable checks pass; prior HTTP fixes remain present.

**Dependencies:**
Task 1, Task 2
**Output:**
Reviewable local delivery and evidence report, with no unrelated HTTP changes.

## Execution Handoff

Continue execution in this session after verifying the plan. No plan-only stop or additional approval is required by the approved scope.

## Status Sync Suggestion

None; no tracked work item is attached.

## Execution Results

- Task 1 completed: all response processors run before the terminal success/extraction stage; Grid preserves protocol envelopes and property descriptors. A primitive false compatibility fix was necessary because processed values now reach the default resolver.
- Focused regressions were observed failing before correction. The complete HTTP suite passed 67 tests; changed tests and public void-return consumers passed strict TypeScript checks; package lint/type/build checks passed.
- Task 2 completed: source mode passed all eight actual-backend checks using existing business login/list/export functions. Read-only final review found no remaining actionable issue.
- Task 3 completed: the matching local dist package is installed without npm publication. Installed mode passed all eight actual-backend checks. Business source and installed suites each passed 74 tests; type/lint/conventions checks and both production builds passed.
- Delivery evidence: `docs/reports/2026-10-15-http-response-pipeline.md` and its linked sanitized JSON records.
- Only the backend started for verification was stopped; existing MySQL/Redis services were preserved.

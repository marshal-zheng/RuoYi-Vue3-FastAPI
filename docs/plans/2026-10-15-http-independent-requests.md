# Independent HTTP Requests Implementation Plan

WORK_ITEM: none

**Goal:** Make ZXUI HTTP requests independent by default, use native Axios cancellation, remove automatic result deduplication, and expose one Axios parameter contract verified in the real business.
**Inputs:** Approved chat decision; both root AGENTS.md files; prior parameter-semantics evidence; HTTP client, cancellation, concurrency, types, examples and metadata generators; business request wrapper and GridList loader. The business has no docs/steering/README.md; ZXUI docs/steering/README.md remains the component/docs responsibility reference.
**Scope Boundaries:** Include the breaking removal of fingerprint cancellation, automatic HTTP deduplication, parameterMode/legacy normalization, obsolete public exports, affected consumers, docs/examples/generated HTTP metadata and a matching local archive. Preserve native AbortSignal cancellation and the explicit concurrency plugin. Exclude the business one-second repeat-submit guard, request-preparation error handling, retry/logger policy, existing dictionary caches, Vue Query adoption, unrelated dirty work, npm publishing and automatic commits.
**Assumptions:** Continue the two current checkouts. The user explicitly authorizes the in-development breaking cleanup. No computer use. Preserve prior uncommitted HTTP/audit work and the newly added repository instructions.

## Task List

### Task 1: Lock independent-request behavior and the default Axios contract

**Status:** Complete.

**Files:**
- Modify: ZXUI packages/http/__tests__/client.test.ts and packages/http/__tests__/utils.test.ts
- Modify: ZXUI packages/http/__tests__/canceler.test.ts and packages/http/__tests__/concurrency.test.ts
- Delete: ZXUI packages/http/__tests__/dedup.test.ts after retiring its implementation

**Steps:**
1. Save scoped pre-task file snapshots and inspect known consumers, including independent package repositories.
2. Make the existing parameter tests assert Axios behavior without opting in; retire legacy-only assertions.
3. Add focused concurrent-request regressions for identical inputs, service/tenant/representation differences, native versus unwrapped results and external cancellation isolation.
4. Observe expected failures before changing runtime code.
5. Confirm the actual business GridList request-generation guard handles stale success, stale failure and disposal.

**Verification:**
- Run: `pnpm exec vitest run packages/http/__tests__/client.test.ts packages/http/__tests__/utils.test.ts` in ZXUI.
- Run: the existing GridList use-grid-request test file identified during discovery.
- Expect: the new default-contract and independent-request regressions fail on current code; existing GridList race checks pass or reveal a narrowly scoped required fix.

**Dependencies:**
none
**Output:**
Observed red tests and a consumer/race inventory defining the migration boundary.

### Task 2: Remove implicit HTTP coordination and migrate public contracts

**Status:** Complete.

**Files:**
- Modify: ZXUI packages/http/src/client.ts, types.ts, utils.ts, index.ts, canceler.ts and package.json
- Delete: ZXUI packages/http/src/dedup.ts
- Modify: ZXUI packages/http/README.md, docs/{zh-CN,en-US}/{component,guide}/http-client.md
- Replace: ZXUI docs/examples/http-client/deduplication.vue with an explicit-cancellation example
- Regenerate: affected HTTP files and entries in docs/public/r/ and docs/public/llms-components.json through existing generators
- Modify: ruoyi-fastapi-frontend/src/utils/http.ts and http.test.ts

**Steps:**
1. Remove the cancel registry and its Axios interceptors; retain only the signal-link helper used by the explicit concurrency plugin.
2. Remove HTTP result-dedup managers, config options, public exports and obsolete tests.
3. Make existing Axios parameter handling unconditional and remove legacy-only helpers without deleting unrelated utility consumers.
4. Remove obsolete business configuration and fixture fields.
5. Document the breaking contract and native signal ownership; update the demo and regenerate affected metadata without overwriting unrelated generated work.

**Verification:**
- Run: `pnpm exec vitest run packages/http/__tests__` and scoped ESLint/Prettier checks.
- Run: `pnpm -C packages/http build` and strict TypeScript checks for affected test files.
- Run: source-mode business API/utils/user-login suites using the existing exact HTTP source alias.
- Expect: independent requests and native cancellation pass, removed exports/options are absent, existing HTTP contracts remain valid, and generated metadata no longer advertises removed APIs.

**Dependencies:**
Task 1
**Output:**
A smaller public HTTP contract with updated consumers, docs and generated metadata.

### Task 3: Deliver and verify source and installed real-business paths

**Status:** Complete.

**Files:**
- Create: ruoyi-fastapi-frontend/vendor/zxio-http-1.0.0-independent.20261015.tgz
- Modify: ruoyi-fastapi-frontend/package.json and yarn.lock
- Create: docs/reports/2026-10-15-http-independent-requests.md and sanitized evidence directory

**Steps:**
1. Build/package the library and install the matching local archive; compare packed and installed payloads to the built output.
2. Verify real login, independent list requests, original external signals, upload/download boundaries and readable user Excel export through actual business modules.
3. Use memory/local transport probes only for cross-service/tenant edge cases that existing endpoints cannot safely express; label evidence boundaries explicitly.
4. Run source/installed business regressions and production builds, business lint/type/conventions and both diff checks.
5. Request scoped read-only review, repair any concrete findings and stop only runtime processes started for this task.
6. Record the breaking API removals, checks, real results, limitations and preserved out-of-scope behavior.

**Verification:**
- Run: `yarn vitest run src/api src/utils src/store/modules/user.login.test.ts` in both delivery modes.
- Run: `yarn lint:check`, `yarn type-check`, frontend changed-file conventions and explicit `VITE_ZXUI_LOCAL=true/false yarn build:prod` builds.
- Run: temporary JSDOM XMLHttpRequest probes against real FastAPI :8088; inspect exported XLSX with openpyxl.
- Run: `git diff --check` in both repositories.
- Expect: default independence and cancellation isolation hold, actual business/export flows pass, review has no remaining scoped blocker, and no unrelated work is changed.

**Dependencies:**
Task 2
**Output:**
Matching local delivery, sanitized evidence and a Chinese completion report.

## Execution Handoff

Continue execution in this session immediately after the plan structure check; the user approved both the design and implementation. Do not stop at planning or request the same breaking-change authorization again.

## Status Sync Suggestion

None; no work item is attached.

## Execution Results

- Default-contract regressions observed 16 expected failures before the runtime changes.
- HTTP tests: 80 passed; existing GridList lifecycle tests: 12 passed; generator tests: 6 passed.
- Business suites: 94 passed in source mode and 94 passed in installed mode; both production builds, lint, type-check, conventions and diff checks passed.
- Real FastAPI probes through actual business modules: 15 passed in each delivery mode, including two successful independent identical calls, cancellation isolation with original signals, multipart preview, readable user Excel export and reverse-completion GridList state.
- Packed, installed and built distribution contents match; retired APIs/artifacts are absent. HTTP metadata was regenerated without changing non-HTTP aggregate entries.
- Independent read-only review found no scoped blockers. Only the backend process started by this task and its child were stopped. No commit or publication was made.
- Report: `docs/reports/2026-10-15-http-independent-requests.md`; sanitized evidence is beside it under `evidence/2026-10-15-http-independent-requests/`.

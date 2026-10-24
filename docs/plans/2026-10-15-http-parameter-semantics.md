# HTTP Parameter Semantics Implementation Plan

WORK_ITEM: none

**Goal:** Add compatible Axios parameter semantics in ZXUI, migrate this business client after auditing its dependencies, and verify real query/body/form/null requests.
**Inputs:** Approved chat scope; ZXUI HTTP client/types/utils; business API inventory and backend Query/Form/Body declarations; existing HTTP and API contract tests.
**Scope Boundaries:** Include query/body separation, URLSearchParams, JSON null preservation, explicit query joining/timestamps, one compatibility mode, existing operation-log parameter retention, local package delivery and real business verification. Exclude duplicate-submit policy, error pipeline changes, retry, dedup identity, HTTP logging enhancements and backend API changes.
**Assumptions:** Continue both current checkouts and preserve unrelated dirty files. No computer use. No docs/steering/README.md exists. Do not publish npm or automatically commit this new task.

## Discovery and Compatibility Decision

- Static import/call inspection found 210 recognized business HTTP call sites and 8 non-GET calls containing params.
- Five active authorization/generator endpoints explicitly consume backend Query fields; the simulation fault endpoint also consumes Query. They do not need implicit body copies.
- Two unused device export API helpers have no corresponding backend routes; keep them unchanged and do not claim their endpoint behavior is verified.
- No production business call enables joinParamsToUrl/joinTime or depends on string params becoming a path segment.
- The existing backend operation-log decorator only reads body/path, implicitly relying on the old body copies for Query-only writes. Retain those audit parameters by reading Query too, without changing log format or storage.
- Keep the library's existing default legacy mode for unknown consumers; add requestOptions.parameterMode = axios as an explicit client/per-request opt-in. This business opts in globally. Legacy behavior remains available without adding individual compatibility flags.
- In Axios mode, params remain query and data remain body; the core does not strip JSON null. URLSearchParams query/body values and duplicate keys survive. Explicit URL joining serializes only query through Axios and consumes it once; optional GET timestamps clone the query input.

## Task List

### Task 1: Lock the library wire contract

**Files:**
- Modify: ZXUI packages/http/__tests__/client.test.ts and packages/http/__tests__/utils.test.ts
- Modify: ZXUI packages/http/src/client.ts, packages/http/src/types.ts, packages/http/src/utils.ts and packages/http/README.md

**Steps:**
1. Add focused adapter regressions for independent query/body, URLSearchParams, null and explicit joining/timestamps.
2. Observe the expected failures before changing runtime code.
3. Add the Axios mode while retaining the default legacy path and per-request precedence.
4. Document mode selection, legacy migration and the intentional Grid List plugin boundary.

**Verification:**
- Run: `pnpm exec vitest run packages/http/__tests__` and targeted ESLint/Prettier in ZXUI.
- Run: `pnpm -C packages/http build`.
- Expect: new regressions fail first, then the HTTP suite and source type/build checks pass.

**Dependencies:**
none
**Output:**
A compatible public parameter mode with explicit wire behavior.

### Task 2: Migrate the business client

**Files:**
- Modify: ruoyi-fastapi-frontend/src/utils/http.ts
- Test: existing ruoyi-fastapi-frontend/src/api/menu-contract.test.ts
- Modify: ruoyi-fastapi-backend/module_admin/annotation/log_annotation.py
- Test: ruoyi-fastapi-backend/tests/unit/test_log_annotation.py
- Modify: ruoyi-fastapi-frontend/package.json and yarn.lock
- Create: matching local HTTP vendor archive

**Steps:**
1. Lock the existing authorization/generator Query dependencies through their real API functions and wire handlers.
2. Observe the old implicit JSON copies, then enable Axios mode in the business client.
3. Build and install the matching local HTTP archive for the installed path.

**Verification:**
- Run: business API/utils/login suites in source and installed modes.
- Run: `yarn type-check`, `yarn lint:check` and frontend conventions changed-file validation.
- Expect: existing APIs keep Query fields without implicit bodies; login forms, file helpers and previous HTTP behavior remain compatible.

**Dependencies:**
Task 1
**Output:**
One business configuration change and verified source/installed delivery.

### Task 3: Verify real business traffic and report

**Files:**
- Create: docs/reports/2026-10-15-http-parameter-semantics.md
- Create: sanitized evidence under docs/reports/evidence/2026-10-15-http-parameter-semantics/

**Steps:**
1. Start the repository's normal local backend with Docker MySQL and existing Redis.
2. Verify real login, parameterized lists, independent query/form Excel export and JSON null version export.
3. Check explicit query joining/custom serialization through the library contract and avoid unnecessary business writes.
4. Run source/installed production builds, request read-only review and stop only this task's backend.

**Verification:**
- Run: temporary JSDOM XHR probes through actual business functions against FastAPI :8088.
- Run: both explicit source/installed `yarn build:prod` modes and both repositories' `git diff --check`.
- Expect: original wire values survive, real returned files remain readable, previous exports do not hang and review finds no remaining scoped issue.

**Dependencies:**
Task 1, Task 2
**Output:**
Sanitized inventory, actual traffic evidence and an honest compatibility report.

## Execution Handoff

Continue current-session execution after the plan structure check; the user approved implementation and real verification.

## Status Sync Suggestion

None; no work item is attached.

## Execution Results

- Task 1 completed: opt-in Axios parameter semantics, unchanged legacy defaults, URLSearchParams/null/query/body regressions, token-aware final query joining and README. Initial eight contract failures and two review-boundary failures were observed before fixes; final HTTP suite: 88 passed.
- Task 2 completed: business globally opts into Axios mode; five existing authorization/generator functions retain Query-only requests. Existing operation logs now initialize from Query before body/form/path overrides. Final source and installed business suites: 90 passed each; backend focused suites: 18 passed. Local archive and lockfile updated; 49 built payload files match installed/packed output, manifests match semantically.
- Task 3 completed: each delivery mode passed nine real requests, including login, lists, conflicting query/form XLSX exports, URLSearchParams duplicates, JSON null and custom query serialization. Real workbooks opened successfully. Both production builds passed; read-only review's P2 was fixed and re-reviewed. Own verification backend stopped, port 8088 released.
- Frontend lint/type/conventions and library checks passed. Backend conventions retain 35 existing Ruff findings in log_annotation.py with unchanged rule counts; new test lint, formatting and guardrails pass. No unrelated cleanup, npm publishing or automatic commit.
- Final Chinese report and sanitized evidence: [HTTP parameter semantics](../reports/2026-10-15-http-parameter-semantics.md).

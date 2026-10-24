# HTTP Preparation Errors Implementation Plan

WORK_ITEM: none

**Goal:** Route request preparation failures through the existing HTTP error pipeline with original causes, cancellation reasons and current request context, without network misclassification or automatic retry.
**Inputs:** User-approved round-three scope; both repositories' AGENTS.md; current HTTP client, error classes, retry manager, business feedback and operation lifecycle; Axios official error/cancellation documentation and installed Axios 1.20.0 source. No steering index exists in the business repository.
**Scope Boundaries:** ZXUI preparation/error classification and public error-hook contract, necessary documentation and package delivery, existing business consumers and focused regressions, source-linked real login/export/cancellation verification. Excludes submission policy, retry policy redesign, logging redesign, query caching, backend changes and UI migration.
**Assumptions:** Existing transform registration and throwing error-hook semantics remain authoritative. Preparation runs once before the retry loop; transport retry behavior remains unchanged. Existing unrelated changes must be preserved.

## Task List

### Task 1: Lock the preparation error contract

**Status:** Complete.

**Files:**
- Test: ZXUI packages/http/__tests__/client.test.ts
- Inspect: ZXUI packages/http/src/{client,errors,types,retry,utils}.ts
- Inspect: ruoyi-fastapi-frontend/src/utils/{http,request,operation}.ts

**Steps:**
1. Audit actual error hooks and request context consumers and compare Axios setup-versus-network classification.
2. Add focused existing-file regressions for preparation/token/serialization failures, latest transformed context, native/custom cancellation reasons and single error dispatch outside retry.
3. Record failing behavior before implementation; retain existing transport failure regressions.

**Verification:**
- Run: `pnpm exec vitest run packages/http/__tests__/client.test.ts` in the ZXUI repository.
- Expect: new contract regressions fail for bypassed error hooks, absent context or network misclassification.

**Dependencies:** none
**Output:** Audited ownership and reproducible regression evidence.

### Task 2: Repair ZXUI preparation boundaries

**Status:** Complete.

**Files:**
- Modify: ZXUI packages/http/src/{client,errors,types}.ts
- Modify: ZXUI packages/http/README.md and docs/{zh-CN,en-US}/{component,guide}/http-client.md as affected
- Modify: ruoyi-fastapi-frontend/src/utils/http.test.ts if needed for the feedback seam
- Modify: generated HTTP metadata and local package delivery only when required by the changed public contract

**Steps:**
1. Track the latest request configuration through preparation and catch failures before retry begins.
2. Normalize preparation failures with their original cause and current configuration; preserve cancellation reasons and classify unissued failures separately from network failures.
3. Dispatch through the existing error pipeline exactly once and retain business feedback ownership and silent options.
4. Update public error-hook types and documentation, build the standalone package and synchronize the actual installed consumer.

**Verification:**
- Run: `pnpm exec vitest run packages/http/__tests__` and `pnpm -C packages/http build` in ZXUI.
- Run: affected strict TypeScript checks and scoped ESLint.
- Run: `yarn vitest run --config ../docs/reports/evidence/2026-10-15-http-independent-requests/vitest-source.config.mts src/utils/http.test.ts src/utils/operation.test.ts src/utils/request.download.test.ts tests/unit/utils/request.test.ts` in the frontend.
- Expect: preparation regressions pass, existing transport/retry semantics remain intact and public consumer types compile.

**Dependencies:** Task 1
**Output:** Generic fix in ZXUI with compatible real business consumption and documented contract.

### Task 3: Verify real business behavior and review

**Status:** Complete.

**Files:**
- Create: docs/reports/2026-10-16-http-preparation-errors.md
- Create: sanitized evidence under docs/reports/evidence/2026-10-16-http-preparation-errors/

**Steps:**
1. Start only the required local backend using the documented Docker runtime.
2. Execute actual business request/operation code with controlled preparation failures and real FastAPI recovery to verify pending release, immediate retry, original cause/context and silent feedback.
3. Verify real login, parse the real user Excel export, and cancel controlled real requests while checking cancellation reasons and loading release.
4. Run affected business suites, frontend lint/type-check, source-linked build and diff checks; obtain scoped read-only independent review and resolve findings.
5. Remove temporary artifacts/data, stop only task-owned processes, and report exact evidence boundaries without browser-click claims.

**Verification:**
- Run: task-local real-backend probes in source and installed modes.
- Run: `yarn lint:check`, `yarn type-check`, `VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod --outDir /tmp/ruoyi-http-preparation/build-source`.
- Run: `git diff --check` in both repositories.
- Expect: failure/retry/pending and login/export/cancellation probes pass, no review blockers remain, and unrelated work is preserved.

**Dependencies:** Task 2
**Output:** Completed third-round fix and a Chinese evidence report.

## Execution Handoff

Continue implementation in this session after plan structure verification. The user has already authorized this scope; no additional plan approval is required.

## Status Sync Suggestion

None; no work item is attached.

## Plan-stage Checkpoint

STATUS: PLAN_DRAFTED
FILES_WRITTEN:
- docs/plans/2026-10-16-http-preparation-errors.md
EVIDENCE:
- READ: both AGENTS.md files, HTTP client/errors/types/retry, business feedback/request/operation and previous reports.
- SEARCH: preparation/error hook callers, error classification, generated public-contract owners and source-link verification entry points.
- COMMAND: plan structure checks run before continuing implementation.
PLAN_CHANGES:
- none
WORK_ITEM_SYNC_SUGGESTION:
- none
NEXT_ACTION: current-session execution
BLOCK_REASON: none
UNBLOCK_ACTION: none

## Execution Results

- Reproduced seven initial bypass/classification failures, then the frozen-error and explicit Axios option-error gaps before their respective repairs.
- ZXUI now normalizes error-hook input, preserves preparation cause/current configuration/cancellation reason, and excludes explicit preparation errors from retry. Unknown local errors remain base HttpError with no default retry; explicit custom retry policy remains caller-owned.
- Business production changes are limited to local error-message fallback. Submission ownership and useOperation are unchanged.
- HTTP tests: 93 passed; existing example-generator tests: 6 passed; strict affected-test types and standalone ESM/CJS build passed. Business affected suites: 24 files / 195 passed in both source and installed modes; lint, type-check and both production builds passed.
- Real FastAPI probes: eight cases passed in each mode; actual ConfigList pending release, zero dispatch on preparation failure, explicit retry, token/encoding failure, login, user Excel export and cancellation verified. Both workbooks parsed; probe records and binary artifacts removed; task-owned backend stopped.
- Independent read-only review found no remaining scoped blocker. Full changed-file convention script reports preexisting console calls in untouched VersionList.vue; unrelated text-editor metadata generator cannot load its keybindings declaration dependency. Targeted HTTP/component metadata generation passed and non-HTTP generated entries were preserved.
- Final local HTTP archive, installation and built payload match across 50 files; manifest JSON equality accounts for pack/install formatting. No commit or publication.
- Report: docs/reports/2026-10-16-http-preparation-errors.md.

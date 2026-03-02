# Frontend Mock/Test Alignment Implementation Plan

**Goal:** Align development mocks and automated tests to a single contract so coverage reflects real behavior under success and failure conditions.
**Inputs:** `ruoyi-fastapi-frontend/src/mocks/**/*`, `ruoyi-fastapi-frontend/tests/**/*`, `ruoyi-fastapi-frontend/vitest.config.ts`, `ruoyi-fastapi-frontend/tests/setup.ts`
**Scope Boundaries:** In scope: frontend mocking/testing architecture, error-path coverage, type safety in `src/mocks`. Out of scope: backend API behavior changes, full E2E redesign, unrelated UI/component refactors.
**Assumptions:** Existing frontend dependencies are already installed and Vitest can run in current workspace.

## Task List

### Task 1: Establish Unified Mocking Policy and Baseline Inventory

**Files:**
- Create: `ruoyi-fastapi-frontend/tests/mocks/README.md`
- Modify: `ruoyi-fastapi-frontend/src/mocks/README.md`
- Test: `ruoyi-fastapi-frontend/tests/README.md`

**Steps:**
1. Document a single-source rule: API behavior tests must use MSW handlers as primary mechanism; `vi.mock` is limited to pure unit isolation (stores/utils without HTTP contract validation).
2. Define test-tier boundaries with examples: contract tests (MSW), unit tests (module mocks), and UI interaction tests (component-level mock APIs only when HTTP is irrelevant).
3. Add a migration inventory table for existing `vi.mock('@/utils/request')` API tests and prioritize high-risk modules first (`project`, `user`, `simulation`).

**Verification:**
- Run: `rg -n "single-source|MSW|vi.mock|contract test" ruoyi-fastapi-frontend/src/mocks/README.md ruoyi-fastapi-frontend/tests/mocks/README.md ruoyi-fastapi-frontend/tests/README.md`
- Expect: policy statements and tier boundaries are present in all three documents.

**Dependencies:**
none
**Output:**
Written policy and migration target list that prevents future mock divergence.

### Task 2: Add Shared MSW Test Runtime for Vitest

**Files:**
- Create: `ruoyi-fastapi-frontend/tests/mocks/server.ts`
- Create: `ruoyi-fastapi-frontend/tests/mocks/lifecycle.ts`
- Modify: `ruoyi-fastapi-frontend/tests/setup.ts`
- Test: `ruoyi-fastapi-frontend/tests/unit/api/project.test.ts`

**Steps:**
1. Create `tests/mocks/server.ts` as the canonical test server factory using `createMockServer('pure')` with explicit scenario control.
2. Add `tests/mocks/lifecycle.ts` to expose `setupMockServerLifecycle()` that wires `beforeAll/afterEach/afterAll` with `listen/resetHandlers/close`.
3. Import lifecycle bootstrap from `tests/setup.ts` so MSW is available in all tests without per-file boilerplate.
4. Keep fallback behavior deterministic in tests by defaulting to `pure` strategy to avoid accidental real backend calls.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn test:run tests/unit/api/project.test.ts`
- Expect: test file passes with MSW lifecycle enabled and no unhandled network request errors.

**Dependencies:**
Task 1
**Output:**
Unified Vitest runtime that can reuse dev MSW handlers directly.

### Task 3: Build Error Scenario Library for Edge Cases

**Files:**
- Create: `ruoyi-fastapi-frontend/src/mocks/scenarios/error.ts`
- Create: `ruoyi-fastapi-frontend/src/mocks/handlers/error-common.ts`
- Modify: `ruoyi-fastapi-frontend/src/mocks/scenarios/index.ts`
- Test: `ruoyi-fastapi-frontend/tests/unit/api/simulation.test.ts`

**Steps:**
1. Introduce reusable error handlers for timeout, `500/503`, and `429` responses with consistent payload shape.
2. Extend scenario router to support explicit error profiles (for example `error-timeout`, `error-5xx`, `error-429`) in Node tests.
3. Keep default/pure scenarios unchanged for current dev flow and make error scenarios opt-in in tests.
4. Add helper metadata headers (e.g., `X-Mock-Scenario`) for easy debugging of active failure mode.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn test:run tests/unit/api/simulation.test.ts`
- Expect: explicit assertions for timeout, 5xx, and 429 pass via scenario-driven handlers.

**Dependencies:**
Task 2
**Output:**
Reusable error scenario matrix that closes boundary-case coverage gaps.

### Task 4: Migrate High-Risk API Tests from Module Mocks to MSW Contract Tests

**Files:**
- Modify: `ruoyi-fastapi-frontend/tests/unit/api/project.test.ts`
- Modify: `ruoyi-fastapi-frontend/tests/unit/api/config.test.ts`
- Modify: `ruoyi-fastapi-frontend/tests/unit/api/menu.test.ts`
- Test: `ruoyi-fastapi-frontend/tests/unit/api/*.test.ts`

**Steps:**
1. Replace `vi.mock('@/utils/request')` in prioritized API suites with real calls through `@/utils/request` and MSW interception.
2. Convert existing assertions to validate user-observable contract behavior (status mapping, message handling, and payload mapping), not mocked function call details.
3. Add dedicated tests for `429` throttling and `503` availability errors in each migrated suite.
4. Keep existing low-level utility tests for `request` internals separate to avoid conflating contract and implementation tests.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn test:run tests/unit/api/project.test.ts tests/unit/api/config.test.ts tests/unit/api/menu.test.ts`
- Expect: migrated suites pass without direct `vi.mock('@/utils/request')` usage.

**Dependencies:**
Task 3
**Output:**
Contract-level API tests aligned with development mock behavior.

### Task 5: Remove `@ts-nocheck` in `src/mocks` with Strong Type Contracts

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/mocks/types.ts`
- Modify: `ruoyi-fastapi-frontend/src/mocks/factories/user.ts`
- Modify: `ruoyi-fastapi-frontend/src/mocks/factories/system.ts`
- Modify: `ruoyi-fastapi-frontend/src/mocks/handlers/user.ts`
- Modify: `ruoyi-fastapi-frontend/src/mocks/handlers/system.ts`
- Modify: `ruoyi-fastapi-frontend/src/mocks/handlers/monitor.ts`
- Modify: `ruoyi-fastapi-frontend/src/mocks/scenarios/*.ts`
- Test: `ruoyi-fastapi-frontend/src/mocks/**/*`

**Steps:**
1. Define shared response/request model types in `src/mocks/types.ts` for handler IO and factory outputs.
2. Refactor factories to export typed builders and avoid implicit `any`/widened literals.
3. Remove `@ts-nocheck` progressively (handlers first, then scenarios/utils), fixing type errors instead of suppressing them.
4. Add strict type-check gate for mocks in CI by running `yarn type-check:strict` and resolving remaining violations.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn type-check:strict`
- Expect: pass with zero `@ts-nocheck` under `src/mocks`.

**Dependencies:**
Task 3
**Output:**
Type-safe mock pipeline from factories to handlers with compile-time guarantees.

### Task 6: Add Guardrails in CI to Prevent Regression

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitlab-ci.yml`
- Create: `ruoyi-fastapi-frontend/scripts/check-mock-standards.sh`
- Test: `ruoyi-fastapi-frontend/scripts/check-mock-standards.sh`

**Steps:**
1. Add a script that fails on new `@ts-nocheck` in `src/mocks` and disallowed `vi.mock('@/utils/request')` in contract API tests.
2. Add CI jobs to run targeted API contract suite plus `type-check:strict`.
3. Report clear failure output with migration guidance so contributors can fix quickly.
4. Keep exceptions explicit and documented (for legacy tests not yet migrated).

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && bash scripts/check-mock-standards.sh`
- Expect: script exits `0` after migration and nonzero on introduced violations.

**Dependencies:**
Task 4, Task 5
**Output:**
Enforced quality gates that keep mock/test/type alignment stable.

### Task 7: Measure Outcome and Complete Rollout

**Files:**
- Modify: `ruoyi-fastapi-frontend/tests/README.md`
- Create: `docs/reports/frontend-mock-alignment-2026-03-02.md`
- Test: `ruoyi-fastapi-frontend/tests/coverage/coverage-summary.json` (generated artifact)

**Steps:**
1. Run full frontend quality gate and capture baseline vs post-migration results.
2. Summarize migrated suites, added edge cases (`timeout`, `5xx`, `429`), and remaining backlog tests.
3. Publish rollout guidance for future test authors with examples of when to use MSW vs `vi.mock`.
4. Mark completion criteria and open follow-up tasks for remaining modules.

**Verification:**
- Run: `cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check && yarn test:run && yarn test:coverage`
- Expect: all commands pass; coverage report generated and no new policy violations.

**Dependencies:**
Task 6
**Output:**
Completed rollout report with measurable quality improvements and maintenance guidance.

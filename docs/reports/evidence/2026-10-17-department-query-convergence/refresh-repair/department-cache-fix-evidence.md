# Department cache consistency fix

Scope: task worktree only; no source checkout product changes, no imported source dirty state, no commit, no computer use. Backend conventions and TDD read before edits.

## Change

`modules/system/application/services/dept_service.py` removes Redis results for list, normal-user tree, edit parent options, and detail, together with department-only invalidation calls/helper. Repository SELECTs, filter/scope arguments, DTO conversion, write validation, transactions, and baseline empty-detail behavior remain intact. Frontend QueryClient still owns shared reads. This avoids an unbounded correctness mechanism for the measured small department read set.

## Red / Green

1. New `test_dept_read_freshness.py`: real DeptService and QueryCache, scheduled in-memory repository/Redis visibility boundaries. Four independently repeated reads must see newly committed names, an old in-flight tree released after commit must not poison a later request (with and without hypothetical post-commit delete), and an own-transaction detail rolled back must not appear in another request.
2. Before production change: 7 failed, all stale-value assertions, 0 errors (`department-cache-freshness-red.log`). This is a controlled service/cache race probe, not SQL transaction or historical request attribution.
3. After change: 34 passed including 7 regressions plus old service tests (`department-cache-freshness-green.log`).
4. Final focused service/controller/transaction suites: 50 passed, 1 existing `regex` deprecation (`department-cache-focused-green.log`).
5. New test Ruff lint and format pass; task `git diff --check` pass.

## Baseline limits verified by A/B

Existing broader department integration suite with service/controller/transaction: original HEAD service and fixed service each produce the same 3 failed, 45 passed, 3 errors. The fixed run including new regressions produces 3 failed, 52 passed, 3 errors. Failures are existing platform capability HTTP 403 assertions; setup errors are asyncmy pooled Future objects bound to another TestClient event loop. A/B uses a read-only Python import finder that loads the exact HEAD service from Git metadata; working product files are never swapped. Runs start and stop their own TestClient lifespans; no requested department write succeeds through the blocked routes.

Backend convention `--changed` was executed and reports the same 15 existing Service Ruff diagnostics as HEAD (codes/messages identical), plus the existing Service formatting failure. Guardrails all pass. The new test file is clean. See `department-cache-impact-comparison.json` and exact baseline/fixed logs. No unrelated service style or integration harness rules changed merely to mask these baseline constraints.

## Evidence boundaries

Tests deliberately use `query_db=None`: existing transaction decorator is bypassed; explicit repository commit/rollback events model visibility and are not live MySQL transaction validation. Parent owns real API/MySQL verification, source/packed builds and source delivery. The audit agent's post-fix service probe also passes, but its hardcoded eventOrder strings still mention invalidation/cache writes and must be neutralized or qualified before being used as a literal post-fix chronology.

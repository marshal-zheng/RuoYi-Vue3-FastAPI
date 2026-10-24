# HTTP Error Classification Implementation Plan

**Goal:** Keep genuine authentication failures at 401, return 403 for user authorization/protected-operation failures and 422 for an incorrect old password.
**Inputs:** Approved request in this conversation; existing user service, identity validation, exception classes, Problem Details handler and business HTTP feedback.
**Scope Boundaries:** Correct the three confirmed user-service misclassifications and verify user-management/profile callers. Reuse existing exceptions and feedback; preserve authentication/session behavior. No frontend business-code whitelist, global error remapping, other write DTOs, caching, retries or query migration.

## Task List

### Task 1: Establish failing business classification regressions

**Files:**
- Modify: `ruoyi-fastapi-backend/tests/unit/services/test_user_service.py`
- Modify: `ruoyi-fastapi-backend/tests/unit/controllers/test_user_role_write_contract.py`
- Test: existing identity and exception tests

**Steps:**
1. Assert protected admin operations are authorization failures.
2. Assert out-of-scope user data returns 403 with its existing error code.
3. Assert incorrect old-password validation returns 422 with an oldPassword field error and never updates the password.
4. Reject missing/null/empty profile password credentials before they can bypass old-password verification; preserve the separate SMS-reset internal command.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && ./venv/bin/python -m pytest tests/unit/services/test_user_service.py -q --no-cov -n0`
- Expect: three classification regressions fail before implementation and pass after Task 2.

**Dependencies:** none
**Output:** Focused red evidence against real service decisions.

### Task 2: Reuse the correct exceptions and verify existing feedback

**Files:**
- Modify: `ruoyi-fastapi-backend/modules/system/application/services/user_service.py`
- Modify: `ruoyi-fastapi-backend/module_admin/entity/vo/user_vo.py`
- Modify: `ruoyi-fastapi-frontend/src/utils/http.test.ts`
- Modify: `shared/openapi.json` and its generated frontend types
- Test: user commands, identity/security, exception and feedback tests

**Steps:**
1. Replace the two authorization AuthException calls with PermissionException.
2. Replace old-password AuthException with ValidationException using the existing error code and field feedback.
3. Verify 403/422 use the existing normal error channel and never prompt relogin; retain real 401 recovery.
4. Keep the password command's CQRS validation limited to supplied user fields, reusing the established partial-validation pattern. Real HTTP exposed an inherited username-required check that otherwise returned 500 before old-password comparison; retain construction-time password syntax validation.
5. Require nonempty oldPassword/newPassword on the profile HTTP input and regenerate the affected schema/types. This closes a bypass made reachable by repairing the command pipeline; other HTTP input models and SMS reset semantics stay unchanged.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && ./venv/bin/python -m pytest tests/unit/services/test_user_service.py tests/unit/services/test_login_service_core.py tests/unit/services/test_security_token_service.py tests/unit/test_exceptions.py modules/system/tests/test_user_write_commands.py -q --no-cov -n0`
- Run: `cd ruoyi-fastapi-frontend && yarn vitest run src/utils/http.test.ts src/utils/feedback/presenter.test.ts src/utils/operation.test.ts --reporter=dot`
- Expect: corrected classifications pass; identity and existing feedback remain valid.

**Dependencies:** Task 1
**Output:** Business failures no longer masquerade as expired sessions; frontend production policy remains unchanged.

### Task 3: Verify real business, review and record evidence

**Files:**
- Create: `docs/reports/2026-10-16-http-error-classification.md`
- Create: evidence under `docs/reports/evidence/2026-10-16-http-error-classification/`

**Steps:**
1. Verify missing/invalid/revoked sessions remain 401 through real HTTP.
2. Verify interface/data-scope/protected-operation 403 through real user-management requests.
3. Verify wrong old password gives 422 through the production profile form, preserves the password/session and allows successful correction.
4. Remove owned temporary records, obtain independent review and compare both workspace baselines.

**Verification:**
- Run: `bash .cursor/skills/backend-conventions/scripts/validate.sh --changed`
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Run: `cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check`
- Run: `cd ruoyi-fastapi-backend && ./venv/bin/python scripts/export_openapi.py --check --output ../shared/openapi.json`
- Expect: real classifications, Problem Details and feedback pass; all owned test data cleaned; unrelated work, schema and frontend production policy preserved.

**Dependencies:** Task 2
**Output:** Reviewed change with clear static, focused-test and real-business evidence boundaries.

## Completion

Tasks 1–3 completed on 2026-10-16. Focused backend tests: 98 passed; frontend feedback/HTTP tests: 45 passed; real-business checks: 25 groups passed with zero unhandled rejections and owned temporary records removed. Lint, type-check and OpenAPI consistency passed. Only the profile password schema and matching generated input type changed. Independent review confirmed the old-password bypass is closed and found no remaining blockers. Evidence and existing convention/Ruff limitations are recorded in `docs/reports/2026-10-16-http-error-classification.md`.

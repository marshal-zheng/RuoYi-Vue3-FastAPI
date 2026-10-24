# Department Write Contract Implementation Plan

**Goal:** Restrict department HTTP writes to operation fields and validate parent changes without breaking root, subtree, or status behavior.
**Inputs:** Approved user request; existing department controller, service, repository, and DeptDlg.
**Scope Boundaries:** Department create/update inputs, parent authorization and hierarchy validation, generated types, and focused business verification. Other HTTP work and ZXUI mechanisms are outside this change.
**Assumptions:** Parent ID 0 represents the virtual root. Administrators may create/move roots; restricted users cannot use root placement to bypass data scope. An existing root can be edited without changing its parent.

## Task List

### Task 1: Establish failing regressions

**Files:**
- Create: `ruoyi-fastapi-backend/tests/unit/controllers/test_dept_write_contract.py`
- Create: `ruoyi-fastapi-backend/tests/unit/services/test_dept_write_boundaries.py`
- Test: `ruoyi-fastapi-frontend/tests/unit/components/EditorReadLifecycle.test.ts`

**Steps:**
1. Verify actual registered HTTP body models reject forbidden fields and require edit identity.
2. Cover missing/inaccessible parents, hierarchy cycles, partial writes, roots, and status behavior.
3. Cover operation-only form payloads.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && ./venv/bin/pytest tests/unit/controllers/test_dept_write_contract.py tests/unit/services/test_dept_write_boundaries.py --no-cov -n 0 -q`
- Expect: Failures expose current contract and hierarchy gaps.

**Dependencies:** none
**Output:** Failing behavior regressions.

### Task 2: Converge department writes

**Files:**
- Create: `ruoyi-fastapi-backend/module_admin/entity/vo/dept_write_vo.py`
- Modify: Department controller, command context/handlers, service, service protocol, DeptDlg, and department API module.
- Modify: `shared/openapi.json` and generated frontend types.

**Steps:**
1. Introduce strict operation inputs and trusted audit conversion.
2. Validate parent existence, scope, and parent-link cycles before writing server-derived ancestors.
3. Whitelist writable fields and preserve omitted values and existing status rules.
4. Send explicit form fields and regenerate the public contract.

**Verification:**
- Run: Focused backend regressions and existing department/detail/command tests.
- Run: `cd ruoyi-fastapi-frontend && yarn type-check && yarn vitest run tests/unit/components/EditorReadLifecycle.test.ts`
- Expect: Focused checks pass; generated artifacts are deterministic.

**Dependencies:** Task 1
**Output:** Implemented contract and synchronized consumers.

### Task 3: Verify actual business behavior and review

**Files:**
- Create: `docs/reports/2026-10-16-dept-write-contract.md`
- Create: Focused evidence under `docs/reports/evidence/2026-10-16-dept-write-contract/`.

**Steps:**
1. Verify production form/API/HTTP behavior against local FastAPI/MySQL with temporary owned records.
2. Verify scoped users, normal subtree moves, roots, statuses, and rejection without mutation.
3. Request independent code review and resolve material findings.
4. Check task-only diff and preserve unrelated workspace changes.

**Verification:**
- Run: Actual business probe; focused tests, lint/type checks, local ZXUI production build, OpenAPI check.
- Expect: Business assertions pass, temporary records are cleaned, and no unrelated files change.

**Dependencies:** Task 2
**Output:** Reviewable implementation and evidence report with explicit verification limits.

## Execution Evidence

- Tasks 1–3 completed in the current session.
- Backend: 124 focused tests passed; frontend: 240 focused tests passed.
- Actual business probe: 38 checks passed with exact original inventory restored.
- Generated contract delta is limited to department POST/PUT and two input models.
- Independent review findings were fixed and re-reviewed with no remaining blockers.
- Detailed evidence: `docs/reports/2026-10-16-dept-write-contract.md`.

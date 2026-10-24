# User and Role Write Contract Implementation Plan

**Goal:** Restrict each user/role HTTP write to its intended fields while preserving omitted-versus-empty relationship semantics.
**Inputs:** Approved request in the current conversation; `AGENTS.md`; current user/role controllers, command handlers, services, business forms and generated API artifacts.
**Scope Boundaries:** Profile, user/role create and ordinary edit, status, role data scope; frontend generated contract and real affected callers. Preserve password/avatar workflows and response/error policy. No unrelated HTTP, cache, lifecycle or UI optimization.

## Task List

### Task 1: Establish failing boundary and relationship regressions

**Files:**
- Create: `ruoyi-fastapi-backend/tests/unit/controllers/test_user_role_write_contract.py`
- Create: `ruoyi-fastapi-backend/tests/unit/services/test_role_write_relations.py`
- Test: existing user/role service and write-command tests

**Steps:**
1. Verify real request models and map controller fields to service writes.
2. Test rejection of operation-inappropriate fields and missing operation identity/status.
3. Test profile mapping without association snapshots and role omitted/empty/null relationships.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && ./venv/bin/python -m pytest tests/unit/controllers/test_user_role_write_contract.py tests/unit/services/test_role_write_relations.py -q --no-cov`
- Expect: targeted failures before production changes; all pass after Task 2.

**Dependencies:** none
**Output:** Regression evidence against actual route models, controller mapping and persistence behavior.

### Task 2: Enforce explicit HTTP inputs and operation write fields

**Files:**
- Create: `ruoyi-fastapi-backend/module_admin/entity/vo/user_write_vo.py`
- Create: `ruoyi-fastapi-backend/module_admin/entity/vo/role_write_vo.py`
- Modify: user/role controllers, services, and affected command handler

**Steps:**
1. Use independent Pydantic input models with forbidden extra fields and operation identities.
2. Convert validated input to existing internal commands, preserving `exclude_unset` field presence.
3. Whitelist persistence fields by operation and retain omitted associations.
4. Keep profile updates bound to the authenticated user without rewriting roles/posts.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && ./venv/bin/python -m pytest tests/unit/controllers/test_user_role_write_contract.py tests/unit/services/test_role_write_relations.py tests/unit/services/test_user_service.py tests/unit/services/test_role_service.py modules/system/tests/test_user_write_commands.py modules/system/tests/test_role_write_commands.py -q --no-cov`
- Expect: passing contract, association and existing command regressions.

**Dependencies:** Task 1
**Output:** Enforced backend contract with existing Problem Details and authorization behavior.

### Task 3: Regenerate and migrate frontend consumers

**Files:**
- Modify: `shared/openapi.json`, `ruoyi-fastapi-frontend/src/api/_generated/`
- Modify: `ruoyi-fastapi-frontend/src/api/system/user.ts`, `role.ts`, affected business forms
- Create: focused API/form contract regressions

**Steps:**
1. Export OpenAPI from the current backend and generate with the locked local generator.
2. Apply generated input types to handwritten API modules.
3. Submit explicit editable fields, including data-scope payload without display-only role fields.
4. Verify user/role components and error feedback through existing HTTP handling.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && ./venv/bin/python scripts/export_openapi.py --output ../shared/openapi.json`
- Run: `bash scripts/generate-api-types.sh --artifact`
- Run: `cd ruoyi-fastapi-frontend && yarn lint:check && yarn type-check`
- Expect: generated artifact consistency and passing frontend gates.

**Dependencies:** Task 2
**Output:** Backend and frontend agree on operation-specific inputs.

### Task 4: Verify real business and review scope

**Files:**
- Create: `docs/reports/2026-10-16-user-role-write-contract.md`
- Create: compact evidence under `docs/reports/evidence/2026-10-16-user-role-write-contract/`

**Steps:**
1. Validate allowed and forbidden writes against real FastAPI/MySQL using temporary records.
2. Verify omitted, empty and null relationships, profile isolation and status/data-scope persistence.
3. Check frontend source build, focused tests and repository convention scripts.
4. Request independent review, fix confirmed issues and compare workspace baseline hashes.

**Verification:**
- Run: `bash .cursor/skills/backend-conventions/scripts/validate.sh --changed`
- Run: `bash .cursor/skills/frontend-conventions/scripts/validate.sh --changed`
- Run: `cd ruoyi-fastapi-frontend && VITE_ZXUI_LOCAL=true VITE_ZXIO_REPO_ROOT=/Users/hqz/Downloads/element-plus yarn build:prod`
- Expect: affected behavior passes; baseline-only diagnostics reported separately; owned test records removed and unrelated workspace work preserved.

**Dependencies:** Task 3
**Output:** Reviewable implementation and precise verification evidence.

## Completion

Tasks 1–4 completed on 2026-10-16. Backend focused tests: 115 passed. Frontend related tests: 277 passed. Real FastAPI/MySQL and production component submission checks: 23 groups passed, temporary records removed. OpenAPI and generated types agree and regenerate without drift; lint, type-check and source-linked build passed. Independent review found no blockers. Existing Ruff/convention diagnostics and the limits of nonvisual verification are recorded in `docs/reports/2026-10-16-user-role-write-contract.md`.

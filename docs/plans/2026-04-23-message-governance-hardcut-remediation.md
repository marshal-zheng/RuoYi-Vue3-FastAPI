# Message Governance Hardcut Remediation Implementation Plan

**Goal:** Close the remaining implementation gaps in the message-governance hardcut so code, gates, and documentation all reflect the same contract truth.
**Inputs:** `docs/specs/message-governance-contract/requirements.md`, `docs/specs/message-governance-contract/design.md`, `docs/specs/message-governance-contract/tasks.md`, `docs/specs/message-governance-contract/migration-inventory.md`
**Scope Boundaries:** In scope: backend live-path pagination contract fixes, governance gate expansion, frontend hard-cut cleanup for old feedback APIs, and truthful inventory/status updates. Out of scope: new requirements/design authoring, non-governed protocol endpoints, broad UI redesign, and unrelated refactors.
**Assumptions:** The approved contract remains the existing hard-cut design: success uses resource-oriented responses, list responses use `items/total/page/pageSize`, and default CRUD feedback ownership belongs to wrapper-level feedback with explicit manual exceptions only where justified.

## Task List

### Task 1: Fix backend project pagination live path

**Files:**
- Modify: `ruoyi-fastapi-backend/modules/project/application/services/project_service.py`
- Modify: `ruoyi-fastapi-backend/modules/project/application/services/project_version_service.py`
- Modify: `ruoyi-fastapi-backend/tests/unit/services/test_project_service.py`
- Modify: `ruoyi-fastapi-backend/tests/unit/services/test_project_version_service.py`
- Modify: `ruoyi-fastapi-backend/tests/integration/test_success_contract_responses.py`
- Test: `ruoyi-fastapi-backend/tests/unit/services/test_project_service.py`
- Test: `ruoyi-fastapi-backend/tests/unit/services/test_project_version_service.py`
- Test: `ruoyi-fastapi-backend/tests/integration/test_success_contract_responses.py`

**Steps:**
1. Replace `page_num` reads with `page` on the `project` and `project_version` service live path.
2. Stop rebuilding paged payloads with `rows` and return the native `PageResponseModel` / `items` contract.
3. Add targeted service and integration assertions that list responses on the live path use `items/total/page/pageSize` and never expose `rows`.

**Verification:**
- Run: `cd ruoyi-fastapi-backend && pytest tests/unit/services/test_project_service.py tests/unit/services/test_project_version_service.py tests/integration/test_success_contract_responses.py -q`
- Expect: targeted tests pass and list-contract assertions use `items/total/page/pageSize`

**Dependencies:**
none
**Output:**
The active `project` and `project_version` list path matches the hard-cut pagination contract.

### Task 2: Expand backend governance gates to catch service/repository regressions

**Files:**
- Modify: `scripts/check_message_governance_backend.py`
- Modify: `ruoyi-fastapi-backend/modules/system/infrastructure/log_repository.py`
- Test: `scripts/check_message_governance_backend.py`

**Steps:**
1. Expand backend scanning scope beyond controller/template files to include application services and governed repositories.
2. Add checks that fail on old list-contract patterns such as `page_num`, `rows`, and old cursor field names on governed HTTP paths.
3. Either migrate governed cursor helper outputs to `items/pageSize/nextCursor` or explicitly remove them from governed scope with code comments and inventory alignment.

**Verification:**
- Run: `python3 scripts/check_message_governance_backend.py`
- Expect: script passes only after service/repository old-contract patterns are removed or formally excluded

**Dependencies:**
Task 1
**Output:**
Backend gate fails on the exact stale patterns that previously slipped through.

### Task 3: Hard-cut frontend feedback ownership and delete old modal message APIs

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/plugins/modal.js`
- Modify: `ruoyi-fastapi-frontend/src/views/protocol/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/device/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/views/project/simulation/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/api/simulation/simulation.ts`
- Modify: `scripts/check_message_governance_frontend.mjs`
- Test: `ruoyi-fastapi-frontend/src/utils/feedback/presenter.test.ts`
- Test: `ruoyi-fastapi-frontend/src/utils/feedback/registry.test.ts`

**Steps:**
1. Classify remaining page-level feedback calls into allowed manual cases and disallowed default CRUD ownership leaks.
2. Migrate disallowed cases to wrapper-level `feedback: { mode: 'auto', key: ... }` and registry-owned messages.
3. Remove deprecated `$modal.msg*` helpers once all remaining business call sites are migrated or converted to explicitly local-only feedback.

**Verification:**
- Run: `node scripts/check_message_governance_frontend.mjs`
- Expect: script fails on page-level default CRUD feedback leaks and passes only after the remaining violations are removed

**Dependencies:**
Task 2
**Output:**
Frontend default CRUD feedback ownership is centralized, and `$modal.msg*` is no longer a business-path dependency.

### Task 4: Reconcile documentation with implementation truth

**Files:**
- Modify: `docs/specs/message-governance-contract/migration-inventory.md`
- Modify: `docs/specs/message-governance-contract/release-notes.md`

**Steps:**
1. Replace the false “100% closed” claim with the current truthful remediation status while work is in progress.
2. Mark the inventory complete only after Tasks 1-3 and their checks are green.
3. Record the final hard-cut acceptance evidence in release notes and inventory wording.

**Verification:**
- Run: `rg -n "100%|收口|未勾选|真实状态" docs/specs/message-governance-contract/migration-inventory.md docs/specs/message-governance-contract/release-notes.md`
- Expect: docs describe the real completion state and final evidence instead of an unsupported blanket closure claim

**Dependencies:**
Task 3
**Output:**
Spec-adjacent docs match the actual code and gate state.

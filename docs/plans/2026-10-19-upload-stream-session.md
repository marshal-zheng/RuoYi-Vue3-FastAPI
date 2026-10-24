# Upload and Stream Session Implementation Plan

WORK_ITEM: none

**Goal:** Reuse the authenticated HTTP session for uploads and verify real import and stream reconnection across access expiry and revocation.
**Inputs:** User authorization to continue the three recommended acceptance gaps; prior session renewal report; actual Element Plus upload implementation and business consumers. No steering index exists.
**Scope Boundaries:** FileUpload, ImageUpload, notice editor uploads, real user Excel import, dev-menu SSE reconnection and WebSocket authentication/reconnection probes. Preserve existing work and production data; no commit or push. Simulation screens and workflows are not migrated.
**Assumptions:** Existing local Docker MySQL/Redis and the source integration remain the runtime. File/image wrappers are globally registered but currently only generated forms consume them; their real browser acceptance may use a temporary mounted fixture, explicitly distinguished from the real notice and user-import pages.

## Task List

### Task 1: Preserve and reuse the authenticated upload boundary

**Files:**
- Modify: `ruoyi-fastapi-frontend/src/components/ui/FileUpload/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/ImageUpload/index.vue`
- Modify: `ruoyi-fastapi-frontend/src/components/ui/Editor/index.vue`
- Create: `ruoyi-fastapi-frontend/src/composables/useAuthenticatedUpload.ts`
- Test: `ruoyi-fastapi-frontend/tests/unit/components/AuthenticatedUpload.test.ts`

**Steps:**
1. Preserve current source bytes and inspect actual Element Plus request, callback and abort behavior.
2. Route the three upload entry points through the current HTTP client, sharing session renewal, FormData serialization and progress.
3. Keep the component props, string-valued model emissions, file/image preview and editor insertion contracts stable. Use one file list owner instead of batch counters; cancel on remove, scope end and unmount.

**Verification:**
- Run: `./node_modules/.bin/vitest run tests/unit/components/AuthenticatedUpload.test.ts src/utils/session.test.ts src/utils/io-toolkit/upload.contract.test.ts --reporter=dot`
- Expect: Current credentials, exactly one success/error callback, correct progress and model updates, no stale update after removal or unmount, and mixed success/failure settles.

**Dependencies:** none
**Output:** Shared authenticated upload transport and focused regressions.

### Task 2: Verify and repair stream reconnection boundaries

**Files:**
- Read/modify if necessary: `ruoyi-fastapi-frontend/src/plugins/dev-menu-hot-sync.ts`
- Test: `ruoyi-fastapi-frontend/src/plugins/dev-menu-hot-sync.test.ts`
- Read/modify if necessary: `ruoyi-fastapi-backend/modules/identity/api/security_controller.py`
- Read/modify if necessary: `ruoyi-fastapi-backend/modules/identity/application/services/security_token_service.py`
- Test: `ruoyi-fastapi-backend/tests/unit/services/test_security_token_service.py`

**Steps:**
1. Exercise SSE reconnection with expired credentials and after local session termination.
2. Verify fresh WebSocket ticket acquisition, single use, path binding and logout revocation; repair only proven session defects.
3. Ensure disconnected or superseded operations cannot reopen connections after logout.

**Verification:**
- Run: `./node_modules/.bin/vitest run src/plugins/dev-menu-hot-sync.test.ts --reporter=dot`
- Run: `./venv/bin/python -m pytest -o addopts='' tests/unit/services/test_security_token_service.py -q`
- Expect: Reconnect renews credentials, old callbacks cannot reopen a stopped session, and revoked credentials cannot establish a new connection.

**Dependencies:** Task 1
**Output:** Evidence-backed stream session behavior.

### Task 3: Complete real runtime acceptance and cleanup

**Files:**
- Create: `docs/reports/2026-10-19-upload-stream-session.md`
- Evidence: `docs/reports/evidence/2026-10-19-upload-stream-session/`

**Steps:**
1. Restore the existing local dependencies and run frontend with ZXUI source integration.
2. Use a headed browser to import a valid owned-user workbook and upload an image through the real notice editor, then verify stored content.
3. Verify FileUpload/ImageUpload in a clearly labelled browser fixture using real backend uploads, including expiry, failure, removal and unmount.
4. Probe SSE and WebSocket authentication with owned local sessions; capture only sanitized evidence.
5. Remove only QA-owned users, notices, sessions and uploaded files, and reconcile source hashes and diagnostics.

**Verification:**
- Run: Focused tests and lint, baseline-comparable source typecheck, browser/API probes.
- Expect: Real upload/import succeeds after expiry; revoked sessions fail; no duplicate writes or stale model changes; all owned artifacts cleaned. Application services remain available.

**Dependencies:** Tasks 1 and 2
**Output:** Completed acceptance report with exact scope and limitations.

## Execution Handoff

Execute in the current session immediately after plan structure validation. Plan-route work auto-executes without a further approval step.

## Status Sync Suggestion

No work item is bound. Tasks 1–3 completed on 2026-10-19. Focused frontend 37 tests, source integration 81 tests and backend 27 tests passed; baseline comparisons introduce no new diagnostics. Real notice upload after 633.54 seconds, import retry/readback, labelled upload fixture, SSE reconnection, WebSocket handshake/revocation and terminal relogin were verified. All owned QA data and the temporary fixture were cleaned. Scope and remaining boundaries are recorded in `docs/reports/2026-10-19-upload-stream-session.md`; no commit or push.

# Session Renewal Implementation Plan

WORK_ITEM: none

**Goal:** Keep an active authenticated browser usable beyond the ten-minute access token lifetime while enforcing refresh rotation and session revocation.
**Inputs:** The local acceptance 401 at 15:52:53 following login at 15:42:51; identity token service, login controller, HTTP transport and user store. No steering index exists.
**Scope Boundaries:** RuoYi browser session transport, refresh session persistence and revocation, focused regressions and actual local browser/API verification. Preserve unrelated edits; no commits, pushes or authentication policy changes.
**Assumptions:** Access lifetime remains 600 seconds and refresh lifetime remains 604800 seconds. Existing Redis and Axios are retained.

## Task List

### Task 1: Establish the incident and preserve the working tree

**Files:**
- Read: `ruoyi-fastapi-backend/modules/identity/application/services/security_token_service.py`
- Read: `ruoyi-fastapi-frontend/src/utils/http.ts`

**Steps:**
1. Correlate login, last success, first failure and process restart timestamps.
2. Snapshot the current versions of files before editing.

**Verification:**
- Run: Parse the existing backend JSON log and compare configured lifetimes.
- Expect: First failure is 602 seconds after login, before the later reload; no runtime refresh request.

**Dependencies:** none
**Output:** Sanitized incident evidence and baseline hashes.

### Task 2: Repair session renewal and revocation

**Files:**
- Modify: `ruoyi-fastapi-backend/modules/identity/application/services/security_token_service.py`
- Modify: `ruoyi-fastapi-backend/modules/identity/api/login_controller.py`
- Modify: `ruoyi-fastapi-frontend/src/utils/auth.ts`
- Modify: `ruoyi-fastapi-frontend/src/utils/http.ts`
- Modify: `ruoyi-fastapi-frontend/src/store/modules/user.ts`
- Create: `ruoyi-fastapi-frontend/src/utils/session.ts`

**Steps:**
1. Retain authoritative session metadata for the refresh lifetime and atomically rotate only an existing current refresh session.
2. Make revocation atomic and avoid removing another session's active pointer.
3. Renew before access expiry and recover one authentication rejection using a shared refresh flight and the original transport body.
4. Preserve cancellation, scope ownership, terminal feedback and login/logout boundaries.

**Verification:**
- Run: `RUOYI_SESSION_REDIS_TEST_URL=redis://127.0.0.1:6379/2 ./venv/bin/python -m pytest -o addopts='' tests/unit/controllers/test_login_controller_refresh.py tests/unit/services/test_security_token_service.py tests/integration/security/test_user_session_renewal.py -q` in backend.
- Run: `./node_modules/.bin/vitest run src/utils/session.test.ts src/utils/http.test.ts src/store/modules/user.login.test.ts --reporter=dot` in frontend.
- Expect: Expired access renews once; concurrent failures coalesce; writes are dispatched once after renewal; revoked or replayed refresh sessions fail.

**Dependencies:** Task 1
**Output:** Session renewal implementation and focused regressions.

### Task 3: Verify the real application and reconcile evidence

**Files:**
- Create: `docs/reports/2026-10-18-session-renewal.md`
- Update: Parent acceptance report in the ZXUI working tree.

**Steps:**
1. Use a headed browser to log in through the real page and exercise requests beyond the actual access lifetime.
2. Probe access expiry, concurrent refresh, rotation replay, revocation and logout with isolated local sessions.
3. Capture sanitized API timings, screenshots, test logs and changed-file hashes.

**Verification:**
- Run: Focused lint and baseline-comparable frontend typecheck; actual local browser/API scenarios.
- Expect: No relogin prompt after access expiry, no duplicate write, and revoked refresh cannot restore access. No tokens in evidence.

**Dependencies:** Task 2
**Output:** Root-cause report with limitations and reproducible validation evidence.

## Execution Handoff

Continue execution in this session immediately after plan verification. No new thread, commit or push.

## Status Sync Suggestion

No work item is bound. Plan-stage status is implementing; completion requires implementation and runtime evidence.

## Execution Result

All three tasks completed in the current session. Backend: 15 passing tests. Frontend authentication: 50 passing tests; source integration: 171 passing tests. Typecheck and lint introduce no diagnostics. The isolated browser waited 617 seconds before renewal, and 23 runtime checks passed. Owned test data and sessions were cleaned. No commit or push. See `docs/reports/2026-10-18-session-renewal.md`.

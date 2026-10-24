# Scheduled Job Write Contract Implementation Plan

**Goal:** Separate job create, edit, status and run inputs while preserving valid calls and consistent database/scheduler state.
**Inputs:** Approved user request; current JobService, SchedulerUtil, registry and monitor job page.
**Scope Boundaries:** Four job operations, their DTOs and actual consumers; generated contract and focused verification. No general HTTP or scheduler architecture migration.

## Task List

### Task 1: Reproduce contract and state failures

**Files:**
- Create: `ruoyi-fastapi-backend/tests/unit/controllers/test_job_write_contract.py`
- Create: `ruoyi-fastapi-backend/tests/unit/services/test_job_writes.py`
- Create: `ruoyi-fastapi-frontend/tests/unit/components/JobWriteContract.test.ts`

**Steps:**
1. Cover forbidden metadata/type, required identity and operation fields.
2. Exercise real scheduler state with an isolated memory scheduler and real SQLite session.
3. Verify form payloads exclude read metadata.

**Verification:**
- Run focused pytest/Vitest; observe the expected failures before implementation.

**Dependencies:** none
**Output:** Failing regressions.

### Task 2: Converge writes and scheduler updates

**Files:**
- Create: `ruoyi-fastapi-backend/module_admin/entity/vo/job_write_vo.py`
- Modify: Job controller/service/protocol, SchedulerUtil, module_task registrations, job API/page and generated types.

**Steps:**
1. Separate strict public inputs; derive operation and audit fields on the server.
2. Validate registry target, cron, parameters and scheduler options before mutation.
3. Preserve omitted edit fields; update scheduling from the effective persisted state.
4. Replace schedules with existing APScheduler APIs and restore prior scheduling on failed writes/commit.
5. Preserve paused/active run-once semantics and return authoritative job identity/group.
6. Send operation payloads and regenerate OpenAPI/types.

**Verification:**
- Run focused backend/frontend regressions, lint/type checks and contract generation check.

**Dependencies:** Task 1
**Output:** Reviewable operation contracts and bounded job write consistency handling.

### Task 3: Real business verification and independent review

**Files:**
- Create: `docs/reports/2026-10-16-job-write-contract.md`
- Create: Evidence under `docs/reports/evidence/2026-10-16-job-write-contract/`.

**Steps:**
1. Verify production frontend API/form flow against local FastAPI/MySQL and real APScheduler.
2. Exercise registered harmless calls, parameters, status transitions, immediate execution and rejected writes.
3. Obtain independent review and fix material findings.
4. Clean owned records and verify unchanged original inventory/workspace.

**Verification:**
- Focused tests, production build, deterministic type generation and business probe all pass.
- Document native UI, crash/secondary-store failure and full-suite verification limits.

**Dependencies:** Task 2
**Output:** Final implementation and scoped evidence report.

## Execution Outcome

All three tasks completed. Independent review findings on pre-commit execution and concurrent compensation were reproduced and fixed. Same-job operations now serialize before reading, with a current database read after waiting. Backend 70, frontend 39 and real-business 40 checks passed; generated contracts repeat with stable hashes. Unrelated operation-log enum ordering was retained and schema equality was checked with enum order normalization only. See `docs/reports/2026-10-16-job-write-contract.md` for evidence, workspace audit and verification limits.

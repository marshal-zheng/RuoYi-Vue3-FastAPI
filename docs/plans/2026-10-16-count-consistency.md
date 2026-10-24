# Transaction-Consistent Pagination Count Implementation Plan

WORK_ITEM: none

**Goal:** Keep paginated totals consistent with transaction-visible records after parameter creation, deletion and rollback.
**Inputs:** User scope, AGENTS.md, repository/service/session/cache code, real deletion reproduction, SQLAlchemy/MySQL documentation and fastapi-pagination source. No steering document exists.
**Scope Boundaries:** Remove the transparent COUNT result cache and its exclusive wiring; count the original query through the existing Session. Preserve transaction boundaries, business parameter-value Redis cache, query cache, pagination/filter/order contracts and frontend behavior. No new cache framework, dependency or schema migration.
**Assumptions:** Current consumers require current pagination totals; no measured performance requirement or explicit cache-enabled consumer exists.

## Task List

### Task 1: Establish the cache and transaction failure modes

**Files:**
- Read: backend COUNT cache, PageUtil, BaseRepository, ConfigRepository, ConfigService, TransactionManager, get_db and container.
- Create: `ruoyi-fastapi-backend/tests/unit/utils/test_page_count_consistency.py`

**Steps:**
1. Inspect real readers, writes, invalidation, nested savepoints and final commit ownership.
2. Reproduce stale totals with production business APIs against local FastAPI/MySQL.
3. Add focused regressions for committed mutations, rolled-back local counts and filtered counts.

**Verification:**
- Run: `node /tmp/ruoyi-count-consistency/before-real.cjs`
- Run: `./venv/bin/python -m pytest tests/unit/utils/test_page_count_consistency.py -o addopts='' -q`
- Expect: Real deletion returns zero items with total one; regressions fail before the change.

**Dependencies:** none
**Output:** Evidence supporting removal of cross-transaction COUNT result sharing instead of a larger invalidation framework.

### Task 2: Consolidate count ownership in the existing Session

**Files:**
- Modify: backend `utils/page_util.py`, `module_admin/repository/base_repository.py`, `container/app_container.py`, `server.py`, `config/env.py` and generator repository/test.
- Delete: `ruoyi-fastapi-backend/utils/count_cache.py`

**Steps:**
1. Use the original query subquery for COUNT in the same Session as items.
2. Remove obsolete cache switches, repository invalidations and dedicated runtime/configuration wiring.
3. Migrate the generator bypass and its existing regression; retain unrelated caches and transaction logic.

**Verification:**
- Run: `./venv/bin/python -m pytest tests/unit/utils/test_page_count_consistency.py tests/unit/module_generator/test_gen_table_paging.py tests/unit/container tests/unit/repositories/test_base_repository.py tests/unit/utils/test_transaction_manager.py tests/unit/services/test_config_service.py -o addopts='' -q`
- Run: `rg -n 'count_cache|CountCache|use_count_cache' ruoyi-fastapi-backend --glob '*.py' --glob '!venv/**'`
- Expect: Regressions pass, obsolete production references are absent and no new lint violations are introduced into legacy files.

**Dependencies:** Task 1
**Output:** Pagination totals derived from the current database transaction, with no cache invalidation lifecycle to coordinate.

### Task 3: Verify real committed writes, rollback and pagination

**Files:**
- Create: `docs/reports/2026-10-16-count-consistency.md`
- Create: sanitized evidence under `docs/reports/evidence/2026-10-16-count-consistency/`.

**Steps:**
1. Verify immediate totals after real parameter creation/deletion, multiple page sizes, filtered queries, empty trailing pages and failed writes.
2. Verify real MySQL transaction snapshots and rollback, and record COUNT query timings without extrapolating to large datasets.
3. Request independent review, compare preexisting workspace hashes, delete owned fixtures and stop owned backend processes.

**Verification:**
- Run: `node /tmp/ruoyi-count-consistency/actual-probe.cjs`
- Run: `./venv/bin/python /tmp/ruoyi-count-consistency/mysql-probe.py`
- Run: `bash .cursor/skills/backend-conventions/scripts/validate.sh --changed`
- Expect: Real totals match committed/snapshot-visible data, no fixture records remain, and any preexisting validation failures are reported separately.

**Dependencies:** Task 2
**Output:** Real business and transaction evidence, a scoped review and a clean fixture/runtime lifecycle.

## Execution Handoff

Continue implementation in this session after plan checks. No approval is pending; hard-cutting unsupported internal behavior is authorized by repository instructions.

## Status Sync Suggestion

No work item is bound. Current status is implementing; final claims require execution evidence.

## Execution Result

All three tasks completed. See `docs/reports/2026-10-16-count-consistency.md` for red/green regressions, real parameter and transaction evidence, scoped review, performance limits and cleanup.

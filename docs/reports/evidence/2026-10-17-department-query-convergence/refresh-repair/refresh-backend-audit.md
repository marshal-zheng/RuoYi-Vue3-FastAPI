# Department refresh backend audit

Date: 2026-10-17. Read-only audit of source backend `/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-backend` against base `94528292c3483af52cdfeab6a95cb0d76d87bbb9`. No production files edited, no database writes, no computer use. Probe outputs live only beside this report in Git metadata.

## Finding and evidence boundary

A specific server-side stale-result mechanism is proved by original code and a controlled schedule of the true `DeptService` + `QueryCache`: a pre-commit or earlier request can load the old department tree, a write invalidates the cache and commits, then that older request writes its old result back into Redis. A later independent read hits the old result without calling the repository. This is sufficient to produce settled, successfully fetched frontend queries missing the just-created child for the default 300-second cache lifetime.

The historical `installed-initial-failure.json` did not retain per-query owned node snapshots or cache generation/timing, so this audit cannot uniquely attribute that specific historical run to this mechanism. The deterministic reproduction proves the defect can cause its observed class of failure, not that another historical cause is logically excluded. The parent's frontend schedule audit and a controlled real HTTP A/B should be combined with this evidence before a final causal claim.

## Precise original code references

All line numbers below refer to the source checkout bytes before the proposed cache removal.

- `modules/system/application/services/dept_service.py:40-60`: tree key is built, loader reads `find_all_for_tree`, then `QueryCache.get_or_set` serializes the result. Tree data is not versioned.
- Same file `:70-87` edit choices, `:97-119` management list, `:335-353` detail: hand-written cache get → database load → set with no generation guard. All four reads can refill obsolete results.
- Same file `:235-237`, `:291-295`, `:324-326`: create/update/delete await `_invalidate_dept_cache()` while still inside `@transactional()` body.
- Same file `:386-389`: wildcard invalidation calls `delete_pattern('query_cache:dept:*')`. Deleting current keys cannot stop a pending loader.
- `module_admin/repository/base_repository.py:255-267`: add flushes the database session rather than committing it.
- `utils/transaction_manager.py:73-85`: an existing transaction gets a nested SAVEPOINT; releasing this is not committing its parent. `:128-140` wraps new transactions. `:311-325` executes decorated service inside this context. Cache invalidation is inside the yielded body, before context exit.
- `modules/system/application/behaviors/command_behaviors.py:95-111`: command pipeline also wraps the same session in `TransactionManager`; no after-commit invalidation is registered. `:133-138` enqueues domain events into the request transaction, not a synchronous cache publication barrier.
- `config/get_db.py:41-58`: request dependency commits at exit after the endpoint, or rolls back on failure. Different requests get different sessions.
- `utils/query_cache.py:154-186`: both locked and unlocked `get_or_set` perform unconditional post-loader `set`. Lock only serializes loaders for the same key within this process; writes do not acquire it. `:204-224` KEYS + DEL is not a fill fence.
- `config/env.py:296-303`: defaults enable query result caching with TTL 300 seconds and lock enabled.
- `modules/system/application/handlers/query/user_query_handlers.py:72-80`: user department tree delegates to exactly the same `DeptService.get_dept_tree_services` path. `role_query_handlers.py:55-93` also consumes this path with its independent role-selection checked keys contract. Removing DeptService Redis result caching affects its tree freshness but does not merge API permissions or response contracts.
- `modules/system/infrastructure/dept_repository.py:82-116`, `:151-192`: each normal tree/list call emits one bounded-by-department-count SELECT; normal/deletion/data-scope filters remain database-owned.

No existing after-commit callback registry, cache generation/version fencing or atomic conditional fill was found in `utils/`, `config/`, `events/`, or system services. Outbox events exist, but are delivered asynchronously by `events/dispatcher.py:79-94` and committed later at `:162`; relying on that would add an eventual-consistency delay to the required read-after-write behavior.

## Runtime contract checked

Installed source runtime versions: FastAPI 0.115.8, Starlette 0.45.3, SQLAlchemy 2.0.48, redis-py 5.2.1. In FastAPI 0.115.8, the dependency `AsyncExitStack` at installed `fastapi/routing.py:290-341` exits before returning the response object at `:355`. Consequently a completed successful HTTP write does not itself mean the client was notified before `get_db` committed. The problematic old read is concurrent or has a transaction snapshot established earlier.

Official contracts checked:

- [FastAPI dependency yield history](https://fastapi.tiangolo.com/advanced/advanced-dependencies/): versions between 0.106 and 0.118 exit yield dependencies before sending the response. Do not apply the newer default response-after-exit ordering to installed 0.115.8.
- [MySQL 8 consistent nonlocking reads](https://dev.mysql.com/doc/refman/8.0/en/innodb-consistent-read.html): REPEATABLE READ keeps the snapshot of the first consistent read for the transaction. A request may already have read during authentication before its department query runs.
- [SQLAlchemy Session after_commit](https://docs.sqlalchemy.org/en/20/orm/events.html#sqlalchemy.orm.SessionEvents.after_commit): after_commit is a transaction event; the session is no longer active for SQL there. This is a lifecycle hook, not a fence against another task's old loader.
- [SQLAlchemy asyncio events](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-events-with-the-asyncio-extension): asyncio support retains synchronous-style events. A correct Redis version/publish barrier would require explicit awaited coordination and rollback/nested-transaction semantics; no suitable existing mechanism is present to reuse.

## Source versus task baseline

The source backend contains the user's existing dirty department write contracts (allowlisted inputs must be intentionally snapshotted if needed for real verification). Compared with base, DeptService changed placement, server-owned write fields, data-scope and detail-not-found validation. Both base and source nevertheless contain all four Redis result-cache reads, three invalidation-before-commit calls and the same unversioned QueryCache implementation. The race is pre-existing in the baseline, rather than introduced by the department Vue Query closure or these dirty write-boundary edits.

The recorded original source DeptService SHA-256 is `ec9f02b5a696b0c70026f7622a5d2293095ec435563405be5ed3e6a41872b072`; QueryCache SHA-256 is `020403cc564a564989a6dea233d36ccfe5b68ed4331d7a09b9da9ec0f6c811fb`, matching the prior actual validation runtime manifest.

## Controlled schedule evidence

`refresh-backend-memory-schedule.json` uses the actual QueryCache class with fake asynchronous Redis. Four schedules cover lock on/off and hypothetical post-commit deletion on/off. All demonstrate committed owned child count 1, independent read owned child count 0, independent loader not called. A post-commit DEL still loses if the old loader finishes after that DEL.

`refresh-backend-service-probe.py` upgrades this to true original `DeptService.add_dept_services` and `get_dept_tree_services` entry points, the actual DeptDO/DeptModel and actual QueryCache. Only Redis transport and repository are fakes. The repository blocks a tree read after copying the old committed snapshot, publishes staged child at an explicit outer_commit event, then releases the old read. `query_db=None` deliberately bypasses actual SQL transactions; this is a controlled service/cache scheduling probe and writes no database. The original result is in `refresh-backend-service-red.json`: both with and without additional post-commit delete, the post-commit independent service call returns no child and makes zero repository calls. The probe can be rerun against the fixed backend path unchanged to establish A/B; it tolerates removal of the `get_query_cache` import.

## Actual cost and choice

Read-only aggregate SQL against existing local MySQL: 75 stored department rows, 10 active, 10 selectable; isolation `REPEATABLE-READ`. No names, IDs or other business rows are retained. Three simple COUNT reads were 3.843 / 1.892 / 1.680 ms.

Actual current DeptRepository calls with no Redis layer returned 10 rows each. Management list: 45.367 / 9.928 / 4.791 ms, tree: 2.893 / 2.823 / 2.834 ms. Each call uses one SELECT. These are only three local samples including pool/model startup on the first call, not a throughput benchmark or a prediction for all deployments. Full output is `refresh-backend-readonly-repository-cost.json`.

Recommended simplest long-term-correct option for this scope: remove Redis result caching from DeptService's four read methods and remove its now-unused invalidations/imports. Keep domain filters, transactions, public HTTP contracts, QueryClient request sharing and frontend successful-write invalidation. It removes a redundant department-state authority and the old-fill window, including across processes, without introducing cache infrastructure. Tradeoff: every department HTTP read performs its one small SQL query instead of possibly hitting Redis; current local data and timings do not justify distributed result caching. QueryClient still deduplicates the two active frontend subscribers into one HTTP request.

Alternative version-fenced result caching would need an atomic cross-process generation check / conditional publish and generation advance tied to actual outer commit, plus handling rollback, nested transactions and Redis failure. A version check performed only before a normal SET still races; a late old loader must not overwrite the current generation. There is no existing mechanism to reuse here, so implementing that system is unjustified complexity for 10 active departments. Plain after-commit deletion, double deletion with fixed sleeps, longer client wait, retries, manual invalidation or awaiting one create's refresh before the next are not complete corrections.

## Minimal real HTTP A/B corroboration plan

Use a task-owned loopback backend process and process-local probe hooks only; no product route, API shape, configuration or source changes for instrumentation. Reuse real login/write/query pipeline. Instrument only an owned trace/marker, retain owned-node booleans and counts, and restore hooks/stop own backend afterward.

1. Create an owned temporary parent using existing API, so its ordinary invalidation empties the department result cache. Start GET `/system/user/deptTree` with an owned probe context. Wrap the real repository call to pause **after it has read SQL and copied its result**, before returning that result to the true service cache writer; record only whether owned parent/child is present.
2. While that old read is paused, create its owned temporary child through normal POST. Await successful response and verify an independent read-only DB count for that marker sees both records, proving outer commit.
3. Release the old GET; the original service publishes its pre-child result. Issue a fresh independent GET with no reused frontend cache. Original behavior should miss the child with zero new repository calls (Redis hit); fixed service should read the DB and include it. The old in-flight response may legitimately describe the snapshot it read; the violation is contaminating later independent requests.
4. Optionally run a management filtered-list counterpart with marker-only filter. A direct GET result missing the child isolates the server cause from Vue scheduling. For QueryClient end-to-end, feed the same server schedule while allowing its normal cancellation/second invalidation, then require the final settled list/tree include the child without manual refetch.
5. Finally delete child then parent using their exact returned owned IDs, verify no active marker records through normal list API, logout own session. Persist only HTTP status, event sequence, owned marker booleans/counts, call counts and cleanup facts; no tokens, headers, passwords or unrelated tree/user data.

If a stock backend does not reproduce in repeated uncontrolled rounds, that is not a reason to report this race eliminated. Controlled A/B is the specific verification needed for this defect.

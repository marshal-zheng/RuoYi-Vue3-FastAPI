# Backend Architecture P0 Foundation Tasks

## Phase 1: Architecture Baseline

- [x] T1.1 Freeze DAO expansion and define repository-only policy
  - DoD: coding guideline updated and lint/static check added for new DAO imports.

- [x] T1.2 Migrate first service group from DAO calls to repository calls
  - DoD: selected module has zero DAO usage in runtime code paths.
  - Note: `ProjectService`, `ProtocolService`, `RoleService` legacy DAO compatibility methods removed; runtime path is repository-only.
  - Note: `DictService` test-only compatibility wrapper removed; runtime now uses `DictTypeService`/`DictDataService`.

- [x] T1.3 Introduce constructor-based service classes with FastAPI dependency providers
  - DoD: selected services run as instance-based classes and tests pass.
  - Note: `DictTypeService` and `DictDataService` converted to constructor injection (`query_db`) with FastAPI providers (`get_dict_type_service` / `get_dict_data_service`).
  - Note: `dict_controller` now resolves services through `Depends(...)` and calls instance methods only.

- [x] T1.4 Refactor controllers to thin handlers
  - DoD: business logic moved to service layer and controller files contain routing/validation only.
  - Note: `dict_controller` no longer sets audit fields/timestamps; these business decisions are moved into `DictTypeService`/`DictDataService`.

## Phase 2: Runtime Consistency

- [x] T2.1 Externalize simulation session runtime state to Redis
  - DoD: session state no longer depends on process-local dictionaries.
  - Note: Added `SimulationRuntimeStateStore` (`sim:session:{session_id}:meta` + stream keys) with Redis-first persistence and in-process fallback.
  - Note: `SimulationService` now persists session snapshots on create/start/pause/resume/stop/speed/duration and rebuilds config from shared snapshot.

- [x] T2.2 Implement session-level single producer for websocket push
  - DoD: no duplicate competing push loops under concurrent websocket clients.
  - Note: `ConnectionManager` now enforces one producer task per session per worker; all websocket clients for the same session share that producer.
  - Note: Producer writes owner-worker increments to Redis streams and non-owner workers consume shared streams by offset.

- [x] T2.3 Add multi-worker simulation smoke tests
  - DoD: tests verify stable behavior across at least two worker processes.
  - Note: Added cross-process smoke test `tests/unit/services/test_simulation_multi_worker_smoke.py` using two worker processes to verify shared session snapshot and offset-based incremental event consumption.

## Phase 3: API Safety

- [x] T3.1 Implement idempotency middleware for selected write endpoints
  - DoD: retries with same key and same payload return identical response without duplicate side effects.
  - Note: Added `middlewares/idempotency_middleware.py` as ASGI middleware (Redis-first cache + in-process fallback) with request fingerprinting (`method + path + query + normalized payload`) and successful response replay.
  - Note: Middleware registration added in `middlewares/handle.py` and feature config added in `config/env.py` (`IdempotencyConfig`).

- [x] T3.2 Add payload mismatch conflict behavior for reused idempotency key
  - DoD: same key with different payload returns conflict response and is covered by tests.
  - Note: Same key with mismatched fingerprint now returns HTTP 409 (`application/problem+json`), including in-flight collision handling.
  - Note: Added unit tests `tests/unit/middlewares/test_idempotency_middleware.py` covering replay, mismatch conflict, pass-through without key, and concurrent same-key retry.

- [x] T3.3 Implement tiered rate limiting (IP and user scopes)
  - DoD: auth/write/read policy tiers enforced and return HTTP 429 with retry metadata.
  - Note: Added `middlewares/rate_limit_middleware.py` with tier routing (`auth`/`write`/`read`) and dual-scope counters (IP + user), including `Retry-After` and `X-RateLimit-*` metadata.
  - Note: Middleware registered in `middlewares/handle.py`; settings added in `config/env.py` (`RateLimitConfig`).
  - Note: Added unit tests `tests/unit/middlewares/test_rate_limit_middleware.py` for auth tier/IP throttle, write tier/user throttle, and read tier throttle.

## Phase 4: Observability

- [x] T4.1 Migrate logging to structured JSON format
  - DoD: request logs include request_id, trace_id, user_id, method, path, status_code, duration_ms.
  - Note: `utils/log_util.py` now supports JSON structured output by default (`LogConfig.log_json_enabled=true`) and injects `request_id`/`trace_id` into log records.
  - Note: Added `middlewares/request_logging_middleware.py` to emit one structured `http_request` log per request with required fields and dynamic level by status code.
  - Note: Middleware registration added in `middlewares/handle.py`; tests cover success/500 request logging fields.

- [x] T4.2 Integrate OpenTelemetry instrumentation for FastAPI, DB, and Redis
  - DoD: traces visible end-to-end with correlated spans.
  - Note: Added centralized OTel bootstrap `utils/otel_tracing.py` with config-gated initialization, OTLP/console exporters, and graceful downgrade when dependencies are unavailable.
  - Note: `server.py` now initializes tracing at startup and instruments FastAPI + SQLAlchemy + Redis.
  - Note: Added unit tests `tests/unit/utils/test_otel_tracing.py` to cover disabled/missing-deps/success paths.

- [x] T4.3 Expose Prometheus metrics endpoint
  - DoD: `/metrics` endpoint exports request latency/error and dependency metrics.
  - Note: Added lightweight Prometheus text registry `utils/prometheus_metrics.py` and request metrics middleware `middlewares/prometheus_middleware.py`.
  - Note: `/metrics` endpoint now exported in `server.py`, including request counters/histograms plus DB/Redis dependency health/query metrics.
  - Note: Added unit tests `tests/unit/middlewares/test_prometheus_middleware.py` for metrics collection and output format.

## Phase 5: Release Guardrails

- [x] T5.1 Add Alembic migration drift check to CI
  - DoD: PR pipeline fails on model/migration mismatch.
  - Note: Added CI job `migration-drift-check` (MySQL service); the historical drift check script has since been removed, and the capability is now represented by `ruoyi-fastapi-backend/scripts/db.py verify`.

- [x] T5.2 Replace magic status/deletion string literals with enums/constants
  - DoD: no new raw literals for status and deletion flags in changed modules.
  - Note: Introduced `LockStatusEnum` and replaced raw status/lock literals in changed modules (`project_service`, `project_version_service`, `project_version_repository`, `project_version_controller`, `dict_service`, `job_service`, `protocol_service`, `project_version_do`).

- [x] T5.3 Add regression tests for idempotency, rate limiting, and simulation consistency
  - DoD: tests run in CI and gate merge for touched modules.
  - Note: Added CI job `architecture-regression-tests` to gate merge with targeted regression suite for idempotency, rate limiting, and simulation runtime consistency.

## Phase 6: Completion

- [x] T6.1 Remove obsolete DAO code paths after parity validation
  - DoD: removed code has no runtime references and migration notes are documented.
  - Note: Removed DAO import assertions from integration smoke tests, switched generator output to repository template, and physically removed `module_admin/dao` + `module_generator/dao` + `tests/unit/dao`.
  - Note: Migration and decommission details documented in `/docs/specs/backend-architecture-p0-foundation/dao-migration-notes.md`.

- [x] T6.2 Publish rollout notes and operational runbook updates
  - DoD: docs include fallback, rollback, and degraded-mode handling.
  - Note: Added runbook `/docs/specs/backend-architecture-p0-foundation/runbook.md` with feature toggles, degraded-mode behavior, rollback procedure, and recovery checklist.

- [x] T6.3 Final acceptance review
  - DoD: all requirements in `requirements.md` are mapped to passing tests or monitoring evidence.
  - Note: Added acceptance matrix `/docs/specs/backend-architecture-p0-foundation/acceptance-review.md` mapping R1-R15 to tests, CI guardrails, and code evidence.

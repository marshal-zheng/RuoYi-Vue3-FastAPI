# Backend Architecture P0 Foundation Requirements

## Goal

Deliver the minimum architecture baseline required for stable multi-worker runtime, predictable release safety, and AI-ready platform observability.

## Scope

This spec covers P0 architecture work only:
- Repository unification
- Service dependency injection
- Thin controller boundary
- Shared simulation runtime state
- Idempotency and rate limiting for write APIs
- Structured logging, tracing, and metrics
- Migration consistency checks in CI
- Removal of magic status/deletion string literals

## Out of Scope

- Full DDD aggregate redesign
- Full CQRS split
- Event bus and outbox rollout
- Feature flags platform

## User Stories

As a backend developer, I want one data access pattern so that code is easier to maintain and review.

As an SRE, I want standard logs, traces, and metrics so that I can find incidents quickly.

As a platform engineer, I want migration checks in CI so that schema drift is blocked before merge.

As an API consumer, I want idempotent write APIs so that retries do not create duplicate side effects.

As a simulation operator, I want runtime session state shared across workers so that websocket and API behavior is consistent.

## Functional Requirements (EARS)

1. WHEN new data access code is added THE SYSTEM SHALL implement it through repository classes and SHALL NOT introduce new DAO calls.
2. WHEN existing service logic accesses persistence THE SYSTEM SHALL use repository interfaces only.
3. WHEN service methods require dependencies THE SYSTEM SHALL receive repositories and infrastructure clients through constructor injection and FastAPI dependency providers.
4. WHEN controller handlers are invoked THE SYSTEM SHALL keep controller responsibilities limited to request parsing, auth checks, and response mapping.
5. WHEN controller handlers require business decisions THE SYSTEM SHALL delegate those decisions to service methods.
6. WHEN a simulation session is created or updated THE SYSTEM SHALL persist runtime state in shared storage accessible by all application workers.
7. WHEN websocket connections consume simulation updates THE SYSTEM SHALL use a single session-level producer model to avoid duplicate or competing consumers.
8. WHEN a POST or PUT request includes `X-Idempotency-Key` THE SYSTEM SHALL store and reuse the first successful response for matching key plus normalized payload within TTL.
9. WHEN the same `X-Idempotency-Key` is reused with a different payload THE SYSTEM SHALL return a conflict response.
10. WHEN request rate exceeds configured limits THE SYSTEM SHALL return HTTP 429 with retry metadata.
11. WHEN any request starts and ends THE SYSTEM SHALL emit structured JSON logs including `request_id`, `trace_id`, `user_id` (if present), `path`, `method`, `status_code`, and `duration_ms`.
12. WHEN HTTP, DB, or Redis operations execute THE SYSTEM SHALL emit OpenTelemetry spans correlated by trace context.
13. WHEN `/metrics` is scraped THE SYSTEM SHALL expose Prometheus-compatible counters, histograms, and gauges for request and dependency health.
14. WHEN ORM models and Alembic migrations diverge THE SYSTEM SHALL fail CI before merge.
15. WHEN deletion/status flags are referenced in backend code THE SYSTEM SHALL use enums or shared constants instead of raw string literals.

## Non-Functional Requirements

1. P95 request latency overhead from observability middleware SHALL remain under 5% for baseline endpoints.
2. Shared simulation state operations SHALL tolerate process restarts without orphaning active sessions.
3. P0 migration SHALL preserve backward-compatible response payloads for existing frontend paths.
4. CI checks added by this feature SHALL complete within 10 minutes on standard pipeline agents.

## Acceptance Criteria

1. All new and modified modules in scope pass lint, tests, and CI migration checks.
2. Multi-worker simulation smoke test shows consistent session behavior across worker boundaries.
3. Repeated write requests with same idempotency key produce no duplicate side effects.
4. Logs, traces, and metrics can be correlated by the same request or trace identifiers.

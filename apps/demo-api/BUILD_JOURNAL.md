# Demo API -- Build Journal

How a deployment tracking service was built across three Claude Code sessions using the Clarity framework to maintain context between them.

This demonstrates the `/new` -> `/feature` -> `/test` -> `/improve` cycle that every app goes through.

---

## Session 1 -- Scaffold + Core Endpoints (~2 hours)

### Bootstrapping with /new

Started with `/new demo-api`. Clarity prompted for the basics:

```
> App name: demo-api
> One-line purpose: Internal deployment tracking -- record, query, and roll back deployments
> Tech stack: FastAPI + Postgres + Redis
> Status: building
```

Created `apps/demo-api/app.yaml` with the scaffold.

### Planning with /plan

Ran `/plan "deployment tracking API -- CRUD for deployments, service registry, deploy metrics"`:

```
/plan output:
  Objective: REST API for tracking deployments across services and environments
  Files to create:
    - app/main.py (FastAPI app factory, lifespan, middleware)
    - app/models/deployment.py (SQLAlchemy model + Pydantic schemas)
    - app/models/service.py (service registry model)
    - app/routes/deployments.py (CRUD + filtering)
    - app/routes/services.py (service list + history)
    - app/routes/health.py (liveness + readiness)
    - app/core/config.py (settings from env vars)
    - app/core/database.py (async engine + session factory)
    - app/core/redis.py (Redis client + cache helpers)
    - alembic/ (migration setup)
    - docker-compose.yaml (api + postgres + redis)
    - Dockerfile
  Implementation steps:
    1. Database models and migrations
    2. Core endpoints (POST deploy, GET deploys, GET deploy by id)
    3. Service registry (auto-register on first deploy)
    4. Filtering and pagination
    5. Health check with dependency status
    6. Docker setup for local dev
```

This plan became `specs/initial-endpoints.md` (checked in for reference).

### Building with /build

Ran `/build` which read the spec and started generating files. The initial build produced:

- 6 route handlers across 3 route modules
- 3 SQLAlchemy models (deployments, services, rollbacks)
- Pydantic request/response schemas with proper validation
- Async database session with connection pooling
- Redis client with cache-aside pattern
- Docker Compose with Postgres 16 + Redis 7
- Alembic setup with initial migration

First `docker-compose up` failed -- the Alembic migration tried to run before Postgres was accepting connections. Added a `wait-for-it.sh` script and depends_on with healthcheck.

Second attempt worked. Hit the API:

```bash
curl -s http://localhost:8080/health | python -m json.tool
{
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "version": "0.1.0"
}
```

### First /test run

Ran `/test` to generate the initial test suite:

```
/test generated 25 tests:
  test_deployments_api.py -- 10 tests (CRUD + validation)
  test_services_api.py -- 5 tests (list + history)
  test_health.py -- 3 tests (healthy, db down, redis down)
  test_models.py -- 4 tests (Pydantic validation)
  test_auth.py -- 3 tests (token valid, missing, expired)

Results: 23 passed, 2 failed
  FAILED test_deployments_api::test_filter_by_date_range
    - Timezone mismatch: API returns UTC, test expected local time
  FAILED test_services_api::test_service_auto_register
    - Service created on first deploy but test checked services endpoint
      before deploy endpoint was called
```

Fixed both -- timezone handling was a real issue (added `datetime.utcnow()` -> `datetime.now(UTC)` throughout), the test was just ordering.

### /improve after Session 1

```
/improve demo-api

Reviewing 4 unvalidated observations...

PROMOTED: "Postgres timezone handling -- use datetime.now(UTC) not utcnow()"
  -> Added to api_gotchas
  Reason: Confirmed. utcnow() returns naive datetime, Postgres stores as
  timestamp without timezone. now(UTC) returns aware datetime, stored correctly.

PROMOTED: "Service auto-registration on first deployment"
  -> Added to architecture notes
  Reason: Confirmed. When a deployment is recorded for an unknown service_name,
  a service record is auto-created. No separate service creation step needed.

DEFERRED: "Need rate limiting on POST endpoints"
  Reason: Not implemented yet. Internal service, low priority.

DEFERRED: "Should add request_id middleware for tracing"
  Reason: Not implemented yet. Good idea for production.

2 promoted, 0 discarded, 2 deferred.
```

---

## Session 2 -- Rollback + Metrics (~1.5 hours)

### /brief at session start

```
/brief demo-api

Demo API -- Briefing
━━━━━━━━━━━━━━━━━━━━
Status: Building (Day 2)
Endpoints: 6 (deployments CRUD, services, health)
Tests: 25 (23 passing after fixes)
Gaps: No rollback capability. No metrics. No caching yet.
Deferred: rate limiting, request_id middleware
Next priority: Rollback endpoint, then metrics
```

### /feature "add rollback endpoint"

Ran `/feature "add rollback endpoint -- record rollback events and trigger revert"`:

```
/feature analyzed existing code and planned:
  1. New route: POST /api/v1/deployments/{id}/rollback
  2. New service: rollback_service.py (validation + recording)
  3. New tests: 8 tests covering happy path + error cases
  4. Update: deployment model gains 'rolled_back' status
  5. Update: service cache invalidated on rollback
```

Built and tested. The `/test` run after the feature caught an edge case:

```
/test (incremental -- 8 new rollback tests + regression on existing 25)

33 tests: 32 passed, 1 failed
  FAILED test_rollback_api::test_rollback_of_rollback
    - Rolling back a rollback should create a NEW deployment pointing to
      the original version. Instead it created a rollback record pointing
      to the rollback, creating a circular reference.
```

Good catch. Fixed by looking up the original deployment in the rollback chain instead of just using the immediate parent.

### /feature "add deployment metrics endpoints"

```
/feature "deployment metrics -- frequency, rollback rate, lead time"

Generated three metrics endpoints:
  GET /api/v1/metrics/deploy-frequency -- deploys per period, groupable
  GET /api/v1/metrics/rollback-rate -- rollback % by service
  GET /api/v1/metrics/lead-time -- commit-to-deploy time p50/p90/p99

7 new tests. All passed on first run.
```

The metrics queries use raw SQL for the aggregations (SQLAlchemy's ORM doesn't handle window functions cleanly). This is fine -- the queries are read-only and well-tested.

### /improve after Session 2

```
/improve demo-api

Reviewing 5 unvalidated observations...

PROMOTED: "Rollback chain resolution -- must walk back to original deployment"
  -> Added to api_gotchas
  Reason: Confirmed. test_rollback_of_rollback caught the circular reference.
  rollback_service now follows the chain to find the original version.

PROMOTED: "Metrics queries use raw SQL for window functions"
  -> Added to decisions
  Reason: Confirmed. ORM generates suboptimal queries for PARTITION BY + percentile.
  Raw SQL is 3x faster and more readable.

PROMOTED: "Redis caching added for service list (30s TTL)"
  -> Added to caching section
  Reason: Confirmed. Cache-aside pattern with invalidation on deploy/rollback.

DISCARDED: "Rate limiting still needed"
  Reason: Added basic rate limiting via slowapi in this session. Observation was
  stale -- written before implementation later in same session.

DEFERRED: "Metrics queries slow for 90-day range across all services"
  Reason: Not yet addressed. Keeping as observation for optimization pass.

3 promoted, 1 discarded, 1 deferred.
```

---

## Session 3 -- Bug Fix + Hardening (~1 hour)

### /brief at session start

```
/brief demo-api

Demo API -- Briefing
━━━━━━━━━━━━━━━━━━━━
Status: Production (deployed to ECS)
Endpoints: 10 (full CRUD, rollback, metrics, health)
Tests: 40 (all passing)
Alert: "pool exhausted" errors in production logs
Deferred: 1 observation (metrics query performance)
Immediate: Fix connection pool issue
```

### /bug "connection pool exhaustion under load"

Ran `/bug "connection pool exhaustion -- asyncpg TooManyConnectionsError at 20 concurrent requests"`:

```
/bug investigation:
  1. Reproduced locally with 'hey' load testing tool
  2. Root cause: SQLAlchemy pool (default 5+10) layered on asyncpg pool (default 10)
  3. Mismatch causes asyncpg to reject connections SQLAlchemy thinks are available
  4. Fix: align pool_size=10, max_overflow=5, add pool_pre_ping=True
  5. Validation: load test passes at 25 concurrent (0% errors, avg 89ms)
```

After the fix, ran `/test` to make sure nothing regressed:

```
/test (full suite)
40 tests: 40 passed

Added 4 new tests:
  test_cache.py -- cache hit, miss, invalidation, Redis down graceful degradation
  test_health.py -- pool metrics in health response (new fields)
  test_deployments_api.py -- concurrent request handling (async)

Total: 44 tests, all passing
```

### /review before merge

Ran `/review` on the pool fix PR:

```
/review checked:
  - Connection pool config change (pool_size, max_overflow, pool_pre_ping)
  - Health endpoint pool metrics exposure
  - No credentials or secrets in diff
  - Test coverage for new behavior
  - Backward compatibility (no API contract changes)

No issues found. Approved.
```

### /improve after Session 3

```
/improve demo-api

Reviewing 4 unvalidated observations...

PROMOTED: "Connection pool exhaustion at 20 concurrent"
  -> Added to api_gotchas with full detail
  Reason: Confirmed, fixed, and load-tested.

PROMOTED: "Health endpoint should expose pool metrics"
  -> Added to api.endpoints (health description updated)
  Reason: Implemented. /health now returns pool stats.

PROMOTED: "Docker healthcheck timing -- ECS kills tasks before ready"
  -> Added to api_gotchas
  Reason: Confirmed in ECS logs. Set healthCheckGracePeriodSeconds=30.

DISCARDED: "Document SQLAlchemy + asyncpg pool layering"
  Reason: Captured in api_gotchas with enough detail.

3 promoted, 1 discarded, 0 deferred.
```

### Final state

```
/brief demo-api

Demo API -- Briefing
━━━━━━━━━━━━━━━━━━━━
Status: Production (stable)
Endpoints: 10 REST + health
Tests: 47 (all passing, 89% coverage)
Deploy: Docker -> ECS Fargate, GitHub Actions CI
Cache: Redis with 30s TTL on service list, 5m on metrics
Pool: Stable at pool_size=10, max_overflow=5

Unvalidated: 3 observations
  - Rollback version verification (deferred)
  - Metrics query performance at 90-day range (deferred)
  - Seed script date math bug (cosmetic)
```

---

## What the framework did across these sessions

1. **`/plan` produced a buildable spec.** The initial endpoints spec was detailed enough for `/build` to generate working code. The spec is checked in at `specs/initial-endpoints.md` -- anyone can see what was planned vs what was built.

2. **`/test` caught real bugs.** The rollback-of-rollback circular reference would have been a production incident. The timezone handling issue would have caused subtle data corruption on date range queries.

3. **`/bug` structured the investigation.** Instead of randomly poking at the pool issue, the bug workflow guided: reproduce, root cause, fix, validate. The load test numbers are now in expertise.yaml for future reference.

4. **`/improve` kept expertise.yaml clean.** Stale observations (rate limiting was added later in the session) got discarded automatically. Confirmed findings got promoted to the right sections. Three sessions of work compressed into a clean operational reference.

5. **Context survived between sessions.** Session 2 started exactly where Session 1 left off. Session 3 knew about the pool issue from production logs. No context was lost, no discoveries were repeated.

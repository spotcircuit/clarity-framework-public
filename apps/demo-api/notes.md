# Demo API -- Development Notes

Running notes from feature and bug sessions. Each entry shows how Clarity commands feed observations into expertise.yaml.

---

## Feature: Deployment Rollback Endpoint (2026-04-07)

**Trigger:** `/feature "add rollback endpoint -- record rollback events and trigger revert"`

Started by reading the current expertise.yaml via `/brief demo-api`:

```
Demo API -- Briefing
━━━━━━━━━━━━━━━━━━━━
Status: Building (Day 2)
Endpoints: 7 (deployments CRUD, services, health, metrics)
Gap: No rollback capability. Deployments are record-only.
Unvalidated: 1 observation (Redis cache invalidation timing)
```

### Implementation

Added three pieces:

1. **Route:** `POST /api/v1/deployments/{id}/rollback`
   - Validates deployment exists and is in `completed` status
   - Creates a rollback record linked to the deployment
   - Updates deployment status to `rolled_back`
   - Invalidates service cache (the rolled-back service's current version changes)

2. **Service layer:** `rollback_service.py`
   - `initiate_rollback(deployment_id, reason, initiated_by)` -- validates + records
   - `get_rollback_history(deployment_id)` -- returns chain of rollbacks for a deployment
   - Emits a log line with deployment_id, from_version, to_version for audit trail

3. **Tests:** 8 new tests in `test_rollback_api.py`
   - Happy path: rollback successful, status updated, cache invalidated
   - Already rolled back: returns 409 Conflict
   - Deployment not found: returns 404
   - Deployment in progress: returns 422 (can't roll back something still deploying)
   - Rollback of a rollback: creates a new deployment record pointing to the original version
   - Missing reason field: returns 422 validation error
   - Auth: missing token returns 401, invalid token returns 403
   - History: rollback chain is returned in reverse chronological order

### Observations generated

After the feature session, these were appended to `unvalidated_observations`:

```yaml
- "Rollback endpoint should verify the target version actually existed before"
- "Rollback + deployment status update should be in a transaction -- currently two separate commits"
- "Need a webhook or callback for rollback completion -- callers poll /deployments/{id} for status"
```

Ran `/improve`:

```
✓ PROMOTED: "Rollback + deployment status update should be in a transaction"
  → Added to api_gotchas
  Reason: Confirmed. If the status update fails after rollback record creation,
  the data is inconsistent. Wrapped both in async with session.begin().

○ DEFERRED: "Rollback should verify target version existed"
  Reason: Not implemented yet. Keeping as observation.

○ DEFERRED: "Need webhook for rollback completion"
  Reason: Not implemented. Low priority for internal tool.
```

---

## Bug: Connection Pool Exhaustion Under Load (2026-04-08)

**Trigger:** `/bug "connection pool exhaustion -- 'pool exhausted' errors at 20 concurrent requests"`

### Investigation

The `/brief` flagged this as a known risk area:

```
Demo API -- Briefing
━━━━━━━━━━━━━━━━━━━━
Status: Production
Recent: Rollback endpoint added
Alert: "pool exhausted" errors in production logs (3 occurrences in last hour)
Unvalidated: 2 deferred observations
```

Reproduced locally with a simple load test:

```bash
# 25 concurrent requests to /api/v1/deployments
hey -n 100 -c 25 -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/deployments
```

Results: 23% error rate, all `500 Internal Server Error` with `asyncpg.exceptions.TooManyConnectionsError` in logs.

### Root cause

Default SQLAlchemy async engine settings:

```python
engine = create_async_engine(
    DATABASE_URL,
    # pool_size defaults to 5
    # max_overflow defaults to 10
    # But asyncpg has its own pool with min_size=10, max_size=10
)
```

The problem: SQLAlchemy's pool and asyncpg's pool are layered. With defaults, SQLAlchemy allows 15 connections (5 + 10 overflow) but asyncpg's pool caps at 10. The mismatch means SQLAlchemy thinks it has headroom but asyncpg rejects the connection.

### Fix

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {"jit": "off"},  # faster for short queries
    },
)
```

Also added pool metrics to the `/health` endpoint:

```python
@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    pool = db.bind.pool
    return {
        "status": "healthy",
        "db": {
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
        },
        "redis": await check_redis(),
    }
```

### Post-fix load test

```bash
hey -n 100 -c 25 -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/deployments

Summary:
  Total:        2.4s
  Slowest:      0.312s
  Average:      0.089s
  Requests/sec: 41.2
  0% errors
```

### Observations generated

```yaml
- "Connection pool exhaustion at 20 concurrent -- fixed with pool_size=10, max_overflow=5"
- "SQLAlchemy + asyncpg pool layering is confusing -- document the interaction"
- "Health endpoint should expose pool metrics for monitoring"
```

Ran `/improve`:

```
✓ PROMOTED: "Connection pool exhaustion at 20 concurrent"
  → Added to api_gotchas with full detail
  Reason: Confirmed, fixed, and load-tested. This is a real gotcha for anyone using
  SQLAlchemy async with asyncpg.

✓ PROMOTED: "Health endpoint should expose pool metrics"
  → Added to api.endpoints (health endpoint description updated)
  Reason: Implemented. /health now returns pool_size, checked_out, overflow, checked_in.

○ DISCARDED: "Document SQLAlchemy + asyncpg pool layering"
  Reason: Captured in the api_gotchas entry with enough detail. Separate doc not needed.
```

---

## Notes for next session

- The three unvalidated observations in expertise.yaml need attention:
  1. Rollback version verification -- should be a quick validation add
  2. Metrics query performance -- might need a materialized view for the 90-day range
  3. Seed script date bug -- cosmetic but embarrassing in demos
- Consider adding `/api/v1/deployments/{id}/logs` for deployment log streaming
- The test suite is at 47 tests but has no load/stress tests -- the pool bug would have been caught earlier

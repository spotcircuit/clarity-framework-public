# Idempotency Guard

Prevent duplicate processing when the same operation is submitted twice. Retries, network failures, and impatient users all cause duplicate requests. The system should handle them gracefully.

## The pattern

Before processing an operation, check if it has already been processed using a unique key. If yes, return the cached result. If no, process it and store the result.

```python
from datetime import datetime, timedelta

class IdempotencyGuard:
    def __init__(self, ttl_hours: int = 24):
        self._store: dict[str, tuple[any, datetime]] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def check(self, key: str) -> tuple[bool, any]:
        """Returns (already_processed, cached_result)."""
        if key in self._store:
            result, timestamp = self._store[key]
            if datetime.utcnow() - timestamp < self._ttl:
                return True, result
            del self._store[key]
        return False, None

    def record(self, key: str, result: any):
        """Record that this key has been processed."""
        self._store[key] = (result, datetime.utcnow())
```

## Usage in an API endpoint

```python
idempotency = IdempotencyGuard(ttl_hours=24)

@app.post("/api/generate-site")
async def generate_site(request: GenerateRequest):
    # Key on the inputs that define uniqueness
    key = f"{request.maps_url}:{request.template_name}"

    already_done, cached = idempotency.check(key)
    if already_done:
        return cached  # Return previous result, skip pipeline

    result = await run_pipeline(request)
    idempotency.record(key, result)
    return result
```

## Where it matters

**Customs filing (Acme Integration).** The customs broker API is async -- you submit a filing and poll for results. If the initial submission times out and you re-submit, you get duplicate filings. Each filing has legal and financial consequences. The idempotency guard uses the shipment ID + HTS code as the key. A retry returns the existing tracking ID instead of creating a new filing.

```python
# From the Acme Integration customs_filing flow
key = f"filing:{shipment_id}:{hts_code}"
already_filed, tracking_id = idempotency.check(key)
if already_filed:
    logger.info(f"Duplicate filing attempt for {shipment_id}, returning {tracking_id}")
    return {"tracking_id": tracking_id, "status": "already_filed"}
```

**Site deployment.** Cloudflare Pages has project limits. Deploying the same site twice creates two projects and burns through the limit. The deploy step checks if a project with the sanitized name already exists before creating a new one.

## TTL matters

The guard needs a time-to-live. Without one:
- Storage grows forever
- Legitimate re-submissions (user actually wants a fresh generation) are blocked

For the site-builder: 3-day TTL for undeployed jobs, 7-day TTL for deployed ones. For customs filing: 30-day TTL (regulatory retention requirement).

## Production alternatives

The in-memory dict works for single-instance services. For distributed systems:
- Redis with `SET key value EX ttl NX` (atomic check-and-set)
- PostgreSQL with a unique constraint on the idempotency key column
- DynamoDB with conditional writes

## Related

- [Correlation ID](correlation-id.md) -- The correlation ID often doubles as the idempotency key
- [Config-Driven Routing](config-driven-routing.md) -- Idempotency checks can be configured per-route

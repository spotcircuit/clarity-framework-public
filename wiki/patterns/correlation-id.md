# Correlation ID

Track a single request or operation across multiple services, logs, and async steps. When something fails at step 5, you can trace back through steps 1-4 without grepping timestamps.

## The pattern

Generate a unique ID at the entry point. Pass it through every service call, log line, database write, and queue message. Every log line includes the correlation ID so you can filter the entire request lifecycle.

```python
import uuid
from contextvars import ContextVar

# Thread-safe correlation ID (works with asyncio)
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

def new_correlation_id() -> str:
    """Generate and set a new correlation ID. Call once at request entry point."""
    cid = uuid.uuid4().hex[:12]
    correlation_id.set(cid)
    return cid

def get_correlation_id() -> str:
    return correlation_id.get()
```

## Middleware (FastAPI example)

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Accept from upstream or generate new
        cid = request.headers.get("X-Correlation-ID") or new_correlation_id()
        correlation_id.set(cid)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response
```

## In logs

```python
import logging

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True

# Format: [a3f82b1c9d01] 2026-04-10 14:23:01 Starting pipeline step 3
formatter = logging.Formatter('[%(correlation_id)s] %(asctime)s %(message)s')
```

## In async pipelines

The site-builder pipeline passes a job_id through all 7 steps. Each step logs with the job_id, the WebSocket broadcasts include it, and the error log records it. When a Cloudflare deploy fails, you trace back through the generation, scraping, and parsing steps for that specific job.

```python
async def run_pipeline(job_id: str, maps_url: str):
    correlation_id.set(job_id)
    logger.info("Starting pipeline")           # [job_abc123] Starting pipeline
    data = await scrape_maps(maps_url)          # [job_abc123] Scraping maps.google.com
    content = await generate_content(data)      # [job_abc123] Claude returned 2.3KB
    await deploy(content)                       # [job_abc123] Deployed to xyz.pages.dev
```

## When to use it

- Multi-step pipelines (like site-builder's 7-step generation)
- Microservice architectures where a request crosses service boundaries
- Async job processing where the request and the work happen at different times
- Any system where "what happened to request X?" is a frequent debugging question

## Related

- [Idempotency Guard](idempotency-guard.md) -- Often paired with correlation IDs (the ID also serves as the idempotency key)
- [Config-Driven Routing](config-driven-routing.md) -- Routing decisions can be logged with correlation IDs for auditability

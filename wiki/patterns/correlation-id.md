# Correlation ID Pattern

#patterns #observability #logging #tracing

A correlation ID is a unique identifier set at the entry point of any processing flow and passed through every step, node, and external call. It makes a single execution traceable across services, logs, and external systems without a distributed tracing infrastructure.

## The Pattern

1. **Set at entry** -- generate a UUID (or accept one from the caller) at the first node/handler before any other work.
2. **Never replace the message object** -- carry the ID as a field on the existing message, not as a wrapper or replacement.
3. **Include in every log line** -- every log statement emits `correlationId` alongside the message and context.
4. **Pass to external systems** -- use the `X-Correlation-Id` HTTP header on all outbound calls so downstream services can log it too.
5. **Return to callers** -- include the ID in error responses so the caller can reference it in support requests.

## Why It Matters

Without a correlation ID, a failure in a multi-step pipeline produces logs scattered across nodes with no way to reconstruct which records belong to the same execution. With one, a single ID surfaces the complete execution trace.

## Implementation Notes

- If the incoming request already contains a correlation ID header, use it rather than generating a new one. This preserves traceability across system boundaries.
- Store the ID in a consistent field name (e.g. `msg.correlationId` or `context.traceId`) and document that field name in the service's readme.
- Short-lived IDs are fine -- they only need to survive one execution, not forever.

## Anti-Patterns

- Generating a new ID mid-flow (breaks the trace).
- Logging without including the ID (defeats the purpose).
- Replacing the full message object in a node (loses the ID).

Source: Derived from distributed systems tracing practices. Validated in multi-step integration flows.

## Related

- [[idempotency-guard]] -- idempotency keys and correlation IDs are related but distinct
- [[config-driven-routing]] -- routing decisions logged with correlation ID for auditability

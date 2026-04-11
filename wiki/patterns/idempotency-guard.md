# Idempotency Guard Pattern

#patterns #reliability #deduplication #integration

An idempotency guard prevents the same record or event from being processed more than once. It is the first check after an entry point and the last thing removed when debugging.

## The Pattern

1. **Status gate at entry** -- before doing any work, check the record's processing status.
2. **Skip if already processed** -- if status is `PROCESSED`, `COMPLETE`, or equivalent, exit immediately with a success response. Do not reprocess.
3. **Set status to PROCESSING before starting** -- mark the record in-flight before doing any external calls. This closes the window where two concurrent executions could both pass the gate.
4. **Write final status on completion or failure** -- always update the status field, even on error, so the gate has accurate state.

## Status Flow

```
NEW / PENDING
    |
    v
[gate check] --> if already PROCESSED: skip
    |
    v
PROCESSING
    |
    +-- success --> PROCESSED / COMPLETE
    |
    +-- failure --> FAILED / ERROR
```

## Why It Matters

External systems send duplicates. Webhooks retry. Users resubmit. Without an idempotency guard, any of these produces double-processing, double-billing, or duplicate records downstream. The guard is not optional for any flow that produces external side effects.

## Implementation Notes

- The gate check and the status-set-to-PROCESSING should be as close together as possible, ideally atomic if the data store supports it.
- Use the same record store for the status as for the record itself -- avoid a separate "processed IDs" table that can drift out of sync.
- For batch flows, gate at the individual record level, not the batch level. Partial batch failures require per-record retry.

## Anti-Patterns

- Checking status but not setting PROCESSING before the external call (race condition).
- Using a time-based deduplication window instead of explicit status (fragile under load).
- Not writing FAILED status on error (leaves records in PROCESSING forever).

Source: Derived from integration reliability patterns. Validated in event-driven pipeline work.

## Related

- [[correlation-id]] -- pair with correlation ID for full traceability
- [[config-driven-routing]] -- unknown types (no config found) are unrecoverable errors

# Config-Driven Routing Pattern

#patterns #architecture #extensibility #routing

Routing logic as data, not code. Processing rules live in configuration records rather than in flow branches or conditionals. Adding a new input type means adding a config record -- zero code changes, zero deployments.

## The Pattern

1. **Config records map input type to processing rules** -- a record store holds entries like `{ inputType: "TYPE_A", processor: "handler-a", schema: "schema-a", validations: [...] }`.
2. **Flow reads config at runtime** -- the flow looks up the config record for the incoming type, then routes accordingly.
3. **No hardcoded branches** -- the flow does not have a switch/case or if/else for each type. It has one lookup and one dispatch.
4. **Per-source configuration profiles** -- different sources can have different rules for the same logical type (e.g., partner A sends dates as YYYY-MM-DD, partner B sends them as epoch ms -- the config record handles the difference).

## Structure

```
[ingest] --> [lookup config by type] --> [apply config-specified processor]
                        |
                [config record store]
                  type | processor | schema | rules | source_profile
                  -----+-----------+--------+-------+---------------
                  TYPE_A | handler-a | schema-a | [...] | default
                  TYPE_B | handler-b | schema-b | [...] | default
                  TYPE_A | handler-a | schema-a | [...] | partner-x
```

## Why It Matters

Code-driven routing creates a deployment dependency for every new type. Product teams, clients, or operators cannot add types without an engineer. Config-driven routing moves that power to whoever manages the config store -- often ops or the client themselves.

## When to Use It

- When the set of input types is expected to grow over time.
- When different sources send the same data in different formats.
- When non-engineers need to be able to add or modify routing rules.
- When you want to A/B test processors without a code change.

## When Not to Use It

- When the routing logic is inherently complex and conditional (config becomes unreadable).
- When there are only 2-3 types that will never grow (over-engineering).

## Implementation Notes

- Config records should be versioned. Changing a config record is a deployment event even if no code changed.
- Include a `source_profile` or `partner` field from the start, even if all sources use the same config initially. Retrofitting it later requires a migration.
- Cache config lookups if the record store has high latency -- but invalidate the cache on config changes.

Source: Derived from integration extensibility patterns. Validated in multi-format processing work.

## Related

- [[correlation-id]] -- routing decisions are logged with correlation ID for auditability
- [[idempotency-guard]] -- guard before routing prevents duplicate processing

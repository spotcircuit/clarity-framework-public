# Clarity Wiki

Knowledge base for the Clarity Framework. Built on the Karpathy LLM Wiki pattern -- one concept per page, cross-linked, always growing.

Read `wiki/index.md` first, then drill into pages via `[[wiki links]]`.

---

## Platform

The framework, orchestration, and infrastructure that everything runs on.

- [[clarity-framework]] -- Open-source agentic intelligence framework. Self-learn loop, 9 commands, 3 knowledge systems.

## Patterns

Reusable engineering patterns across projects.

- [[correlation-id]] -- Unique ID at entry point, propagated through all steps for full execution traceability.
- [[idempotency-guard]] -- Status gate prevents duplicate processing in event-driven pipelines.
- [[config-driven-routing]] -- Routing logic in config records, not code. Zero-deploy extensibility.

## Decisions

Architectural decisions with rationale.

- [[karpathy-wiki-comparison]] -- Why three separate systems (YAML, memory, wiki) instead of Karpathy's single-wiki approach.
- [[three-knowledge-systems]] -- The decision to keep expertise.yaml, memory, and wiki separate instead of consolidating.

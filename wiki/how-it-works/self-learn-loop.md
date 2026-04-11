# The Self-Learn Loop

Every Clarity command appends raw observations to `unvalidated_observations:` in expertise.yaml. Running `/improve` validates each one against current state and either promotes it to a structured section, defers it, or discards it.

This is the core feedback mechanism. Knowledge accumulates automatically through normal work, not through documentation sessions.

## How it works

```
  Build / investigate / discover
            │
            ▼
  Observations appended to expertise.yaml
  (unvalidated_observations: section)
            │
            ▼
  Run /improve
            │
            ├── PROMOTED: confirmed fact → moved to relevant section
            ├── DEFERRED: not yet verifiable → stays in observations
            └── DISCARDED: stale or already captured → removed
```

## Real example: site-builder Session 2

During a build session, the framework appended four observations:

```yaml
unvalidated_observations:
  - "Website scraper color extraction is brittle — only works with CSS custom properties"
  - "Gemini hero images: simple subjects > scene compositions"
  - "WebSocket progress reporting would be useful"
  - "Need to handle Maps listings with no website URL gracefully"
```

Running `/improve` produced:

```
Reviewing 4 unvalidated observations...

PROMOTED: "Website scraper color extraction is brittle"
  → Added to scraping.known_limitations
  Reason: Confirmed. Only checks :root and body CSS custom properties.

PROMOTED: "Gemini hero images: simple subjects > scene compositions"
  → Added to pipeline.ai_images notes
  Reason: Confirmed via testing. "A modern plumbing company" generates better
  than "An aerial view of a plumbing van parked outside a suburban home."

PROMOTED: "Need to handle Maps listings with no website URL"
  → Added to pipeline.steps (website scraper marked "optional")
  Reason: Confirmed. Conditional skip added in orchestrator.

DISCARDED: "WebSocket progress reporting would be useful"
  Reason: Already implemented. ws_manager.py sends stage-by-stage progress.
  Observation was written before the WebSocket endpoint was added
  later in the same session.

3 promoted, 1 discarded, 0 deferred.
```

The discarded observation is the important case. It described a problem that got fixed later in the same session. Without `/improve`, it would have lingered as a "known issue" that was not an issue anymore.

## Rules

1. Never manually edit `unvalidated_observations:` -- let commands append to it.
2. Run `/improve` after any significant investigation or discovery session.
3. Keep expertise.yaml under 1000 lines -- `/improve` compresses when needed.
4. YAML must always be valid: `python3 -c "import yaml; yaml.safe_load(open('expertise.yaml'))"`

## What makes it work

The loop works because observations are cheap to write and expensive to promote. During a build session, anything notable gets appended without slowing down work. The validation step is separate and deliberate. This means:

- You never lose an insight because you were too busy to document it properly.
- Stale information gets cleaned up instead of rotting in a doc.
- Expertise.yaml stays accurate because every fact in it has been validated at least once.

## Related

- [Three Knowledge Systems](three-systems.md) -- Where expertise.yaml fits alongside memory and wiki
- [Commands](commands.md) -- `/improve`, `/brief`, and other commands that drive the loop
- [Site Builder](../examples/site-builder.md) -- Four sessions showing the loop in action

# Clarity Framework

#platform #clarity #framework #open-source

An agentic intelligence framework for technical engagements. Gives any engineer full project context on day one and grows smarter throughout the engagement.

## What It Is

Clarity is based on Andrej Karpathy's LLM Wiki pattern, extended with structured operational data and behavioral memory. It provides persistent project intelligence across LLM sessions.

## Three Knowledge Systems

| System | Purpose | Format |
|---|---|---|
| `expertise.yaml` | Operational data (project state, API gotchas, results) | Structured YAML |
| `.claude/memory/` | Behavioral rules (user preferences, guardrails) | Markdown + frontmatter |
| `wiki/` | Synthesized knowledge (patterns, decisions, concepts) | Obsidian markdown + [[links]] |

## The Self-Learn Loop

1. Every `/se:*` command appends raw observations to `unvalidated_observations:`
2. `/se:self-improve` validates each observation against current live state
3. Confirmed facts get promoted into the relevant expertise section
4. Stale observations get discarded

## 9 SE Commands

| Command | What It Does |
|---|---|
| `/se:create` | Create a new client or app |
| `/se:discover` | Phase 0 auto-generation, seed expertise.yaml |
| `/se:brief` | Standup/handoff summary |
| `/se:self-improve` | Validate observations, integrate confirmed facts |
| `/se:check` | Design guidelines compliance check |
| `/se:wiki-ingest` | Process raw/ files into wiki pages |
| `/se:wiki-file` | File a conversation insight as a wiki page |
| `/se:wiki-lint` | Health check: orphans, broken links, stale pages |
| `/se:meeting` | Ingest meeting notes |

## Structure

```
clarity-framework/
  clients/        # External engagements
  apps/           # Internal tools and products
  wiki/           # Knowledge wiki (this site)
  system/         # Orchestration + agents
  scripts/        # Automation (sync, post, humanize)
```

## Links

- GitHub: https://github.com/spotcircuit/clarity-framework

## Related

- [[karpathy-wiki-comparison]] -- how Clarity extends the original pattern
- [[three-knowledge-systems]] -- the architectural decision behind the three layers
- [[correlation-id]] -- example of a reusable pattern page
- [[idempotency-guard]] -- another pattern showing wiki structure
- [[config-driven-routing]] -- config-as-data pattern

---
Source: CLAUDE.md, README.md | Filed: 2026-04-08

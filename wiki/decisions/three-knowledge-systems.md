# Three Knowledge Systems

#decision #architecture #knowledge-management

**Decision:** Keep three separate knowledge systems (expertise.yaml, memory, wiki) instead of consolidating into one.

**Date:** 2025

**Status:** Accepted

## Context

LLMs need persistent context to be useful across sessions. The naive approach is one big document, but different types of knowledge have different update patterns, access patterns, and lifespans.

## The Three Systems

| System | What Goes Here | Updated By | Format |
|---|---|---|---|
| `expertise.yaml` | Operational data -- API endpoints, env configs, deploy states, gotchas | `/se:*` commands automatically | Structured YAML |
| `.claude/memory/` | Behavioral rules -- user preferences, guardrails, workflow habits | LLM automatically | Markdown + frontmatter |
| `wiki/` | Synthesized knowledge -- patterns, decisions, architecture, people | `/se:wiki-*` commands | Obsidian markdown + `[[links]]` |

## Why Not One System?

**Structured data needs to be queryable.** expertise.yaml is YAML so you can parse it, validate it, diff it, and programmatically update specific fields. Try doing that reliably with free-form markdown.

**Behavioral rules need to persist silently.** Memory files are read automatically at session start. They're small, stable, and rarely change. Mixing them with fast-changing operational data means the LLM re-reads noise every session.

**Synthesized knowledge needs cross-linking.** Wiki pages reference each other with `[[links]]`. This creates a graph you can traverse. A flat YAML file or a memory doc can't do that.

## Alternatives Considered

**Single markdown file:** Tried this first. It grew to 2000+ lines, became slow to parse, and conflicting update patterns caused data loss during concurrent edits.

**Database:** Too heavy for the use case. The knowledge needs to live in the repo, be version-controlled, and be readable by both humans and LLMs without tooling.

**Vector store:** Good for retrieval, bad for structure. You lose the ability to browse, cross-link, and maintain a coherent knowledge graph.

## Consequences

- Engineers need to understand which system to use for what (mitigated by clear docs in CLAUDE.md)
- Three places to check when looking for information (mitigated by index.md as entry point)
- More resilient: a bug in wiki-ingest doesn't corrupt your operational data or behavioral rules

Source: framework design decision, informed by experience with single-file context approaches

## Related

- [[clarity-framework]] -- overview of the framework and how the systems fit together

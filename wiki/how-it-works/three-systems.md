# Three Knowledge Systems

Clarity uses three separate knowledge systems. Each serves a different purpose, has a different format, and is updated differently. They do not overlap and should not be merged.

## The three systems

| System | Stores | Format | Updated by | Example |
|--------|--------|--------|------------|---------|
| `expertise.yaml` | Operational data -- architecture, API gotchas, pipeline state, test results | Structured YAML | `/improve`, `/discover`, `/brief` commands | "Cloudflare project names must be lowercase alphanumeric with hyphens" |
| `.claude/memory/` | Behavioral rules -- user preferences, guardrails, process rules | Markdown + frontmatter | Claude automatically when patterns emerge | "User prefers Railway for backend deploys" |
| `wiki/` | Synthesized knowledge -- reusable patterns, decisions, concepts | Markdown with links | `/wiki-file`, `/wiki-ingest`, `/wiki-lint` | "Correlation ID pattern for cross-service tracing" |

## Why three, not one

**expertise.yaml is per-project and structured.** It answers "what do I need to know to work on this project right now?" An AI agent reads it at session start and has full context. YAML because it is machine-readable and diffable. One file per project.

**Memory is per-user and behavioral.** It answers "how does this user want me to work?" Things like commit message style, preferred tools, guardrails ("never run npm dev unless asked"). Claude updates it automatically. It is not project-specific.

**Wiki is cross-project and durable.** It answers "has anyone figured this out before?" Patterns, decisions, and concepts that apply across multiple projects. When a project discovers something reusable, `/wiki-file` captures it permanently.

## How they interact

```
During a build session:
  1. Read expertise.yaml → understand project context
  2. Read memory → understand user preferences
  3. Do the work
  4. Observations → unvalidated_observations in expertise.yaml
  5. /improve → validate and promote observations
  6. If something is reusable → /wiki-file captures it in wiki/

expertise.yaml grows per-project knowledge
memory grows per-user preferences
wiki grows cross-project knowledge
```

## Real example

The site-builder project discovered that Cloudflare Pages project names must be lowercase alphanumeric with hyphens. This went through all three systems:

1. **expertise.yaml** -- Captured as an API gotcha: "Business names with special characters get sanitized, which can cause collisions." This lives in `apps/site-builder/expertise.yaml` and is read at the start of every session.

2. **memory** -- If the user always deploys to Cloudflare, memory might note "prefers Cloudflare Pages for static site deployment." This affects future suggestions.

3. **wiki** -- If the naming constraint is relevant to other projects, `/wiki-file cloudflare-naming` creates a wiki page explaining the pattern. Next time any project hits this, the wiki has the answer.

## Related

- [The Self-Learn Loop](self-learn-loop.md) -- How expertise.yaml accumulates knowledge
- [Commands](commands.md) -- Which commands update which system
- [Site Builder](../examples/site-builder.md) -- Real project showing all three systems in use

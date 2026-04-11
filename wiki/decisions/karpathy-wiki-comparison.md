# Karpathy LLM Wiki vs Three-System Knowledge Architecture

#decisions #architecture #wiki #knowledge-management

Comparison of Andrej Karpathy's "LLM Wiki" pattern (published April 2026) against a three-system knowledge architecture: structured operational data (e.g., expertise.yaml), cross-session behavioral memory, and a wiki.

Sources: [Karpathy's gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), [Extended Brain Substack analysis](https://extendedbrain.substack.com/p/the-wiki-that-writes-itself), [VentureBeat coverage](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an).

---

## Part 1: Karpathy's Architecture

### Three-Layer Structure

```
project/
  raw/                  # Layer 1: Immutable source documents
    assets/             # Downloaded images
    *.md, *.pdf, etc.   # Articles, papers, data files -- LLM reads, never writes
  wiki/                 # Layer 2: LLM-generated and LLM-maintained
    index.md            # Content catalog -- every page with one-line summary, by category
    log.md              # Append-only chronological record of ingests, queries, lint passes
    [entity pages]      # e.g. people, organizations, technologies
    [concept pages]     # e.g. theories, patterns, frameworks
    [summary pages]     # Source summaries, comparisons, analyses
  CLAUDE.md             # Layer 3: Schema -- tells LLM how wiki is structured, conventions, workflows
```

### Processing Pipeline

**Ingest (raw -> wiki):**
1. User drops source document into `raw/`
2. User tells LLM to process it
3. LLM reads source, discusses key takeaways with user
4. LLM writes a summary page in wiki/
5. LLM updates `index.md` with new page listing
6. LLM updates relevant entity and concept pages across wiki (10-15 pages per source)
7. LLM appends entry to `log.md`
8. User reviews in Obsidian in real-time

**Query (wiki -> answer -> wiki):**
1. User asks a question
2. LLM reads `index.md` first to locate relevant pages
3. LLM drills into those pages, follows links
4. LLM synthesizes answer with citations
5. Good answers get filed back into wiki as new pages -- this is the compounding mechanism

**Lint (wiki -> wiki):**
1. Periodic health check, user-initiated
2. LLM scans for contradictions between pages
3. Flags stale claims superseded by newer sources
4. Identifies orphan pages with no inbound links
5. Suggests missing pages for important concepts

### What Makes It Different From RAG

| Aspect | RAG | Karpathy Wiki |
|--------|-----|---------------|
| Knowledge state | Re-derived on every query | Compiled once, kept current |
| Accumulation | Nothing compounds | Everything compounds |
| Cross-references | Rebuilt each time via retrieval | Already exist in wiki pages |
| Contradictions | Discovered per-query (maybe) | Flagged during lint passes |
| Infrastructure | Vector DB, embeddings, retrieval pipeline | Plain markdown files + index |
| Transparency | Embeddings are black box | Every claim traceable to a .md file |
| Scale ceiling | Scales well | Works to ~100 sources / ~400k words, then needs search tooling |

---

## Part 2: The Three-System Architecture

### System 1: Structured Operational Data (expertise.yaml)

Structured YAML with defined sections: project state, known issues, filing results, implementation patterns, unvalidated observations. Machine-readable. Commands can parse it programmatically. Capped at a defined size. Must always be valid (enforced by tooling).

**Best for:** Operational data that automation reads. Live state, API results, known issues, counts, versions.

**Limitations:** Rigid schema, no cross-references, per-project silo.

### System 2: Behavioral Memory (.claude/memory/)

Per-project folder of short markdown files with frontmatter. Each file captures a user preference, critical guardrail, or process rule. Injected into every session automatically. Created by the LLM when important patterns emerge in conversation.

**Best for:** How to work (user preferences, guardrails, process rules). Things the LLM needs to remember about behavior, not content.

**Limitations:** User does not control what gets remembered, no links between entries, can go stale.

### System 3: Wiki (Obsidian-Compatible)

Markdown files with `[[wiki links]]` and `#tags`. Organized into categories: platform patterns, decisions, people, concepts. Index file with per-page summaries. Append-only log. Obsidian-compatible for graph view and Dataview queries.

**Best for:** Synthesized knowledge, architectural decisions with rationale, cross-cutting concepts, relationship-rich knowledge.

**Limitations:** Requires discipline to maintain. No automated ingest or lint pipeline by default.

---

## Part 3: Gaps vs Karpathy

### What Karpathy Does That The Three-System Architecture Doesn't (By Default)

1. **Automated ingest pipeline** -- drop a file in `raw/`, LLM processes and updates 10-15 pages. The three-system architecture has a `raw/` folder concept but no default automation.
2. **Query-to-wiki filing** -- good answers compound into new wiki pages. Without this convention, synthesis disappears into chat history.
3. **Lint/health-check** -- periodic scan for contradictions, orphans, stale pages. No equivalent for the wiki layer by default.
4. **LLM-navigable index** -- Karpathy's `index.md` lists every page with a one-line summary. A folder-listing index is not useful as an LLM navigation aid.
5. **Source traceability** -- every wiki page traces back to a `raw/` source. The three-system wiki pages often cite "session notes" without linking to originals.

### What The Three-System Architecture Does That Karpathy Doesn't

1. **Machine-readable structured knowledge** -- Karpathy's wiki is for humans and LLMs. Structured YAML is for programmatic parsing by commands and automation.
2. **Validation against live state** -- a self-improve command can validate observations against actual live systems. Karpathy's lint checks internal consistency only.
3. **Command-driven integration** -- knowledge is updated as a side effect of doing work, not as a separate activity.
4. **Behavioral memory** -- user preferences and critical guardrails injected into every session. Karpathy has no equivalent.
5. **Multi-project architecture** -- per-project knowledge isolation plus cross-project memory.

---

## Part 4: Key Decision

**Keep all three systems. They serve distinct purposes.**

Karpathy has one system because he has one use case (research). An engineering operations framework has three use cases: operational data, behavioral rules, and synthesized knowledge. The right move is to connect the systems, not merge them.

Connection points:
- When structured data is updated with significant findings, create/update corresponding wiki pages.
- When behavioral memory captures an architectural decision, it should also exist as a wiki decision page.
- When wiki lint finds a contradiction with structured data, flag for resolution.

The single most important thing to adopt from Karpathy: **the compounding loop**. Every good answer becomes a wiki page. The system gets smarter by being used.

---

## Related

- [[clarity-framework]] -- the framework that implements the three-system architecture
- [[config-driven-routing]] -- example of a well-structured pattern page

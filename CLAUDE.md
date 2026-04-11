# Clarity

An agentic intelligence framework for technical engagements. Gives any engineer full project context on day one and grows smarter throughout the engagement through a self-learn loop.

Based on Andrej Karpathy's LLM Wiki pattern, extended with structured operational data and behavioral memory.

---

## Quick Start

**For clients (external engagements):**
1. Copy `clients/_templates/client.yaml` to `clients/{name}/client.yaml` and fill it in
2. Run `/discover {name}` to generate Phase 0 doc and seed expertise
3. Use `/check`, `/brief`, `/improve` throughout the engagement

**For apps (internal tools/products):**
1. Copy `apps/_templates/app.yaml` to `apps/{name}/app.yaml` and fill it in
2. Same commands work: `/brief {name}`, `/improve {name}`, etc.
3. All `/*` commands auto-resolve names from both `clients/` and `apps/`

**For knowledge:**
4. Drop files in `raw/` and run `/wiki-ingest` to build the wiki

---

## Commands

| Command | What It Does |
|---|---|
| `/create <client>` | Create a new client -- prompts progressively, creates config files |
| `/discover <client>` | Phase 0 auto-generation. Seeds expertise.yaml. |
| `/brief <client>` | Standup/handoff summary from expertise.yaml |
| `/improve <client>` | Validate observations, integrate confirmed facts |
| `/check <client>` | Design guidelines compliance check |
| `/wiki-ingest` | Process files in `raw/` into wiki pages |
| `/wiki-file <topic>` | File a conversation insight as a wiki page |
| `/wiki-lint` | Health check: orphans, broken links, stale pages |

---

## Directory Structure

Both `clients/` and `apps/` use the same layout. All `/*` commands resolve names from either.

```
clients/{name}/                    apps/{name}/
  client.yaml   <- GITIGNORED       app.yaml      <- GITIGNORED
  phase-0-discovery.md               phase-0-discovery.md
  expertise.yaml                     expertise.yaml
  notes.md                           notes.md
  specs/                             specs/
  research/     <- GITIGNORED        research/     <- GITIGNORED
```

- `clients/` = external engagements (revenue-generating)
- `apps/` = internal tools and products (site-builder, etc.)

Templates: `clients/_templates/`, `apps/_templates/`

---

## Knowledge Wiki

Clarity includes an Obsidian-compatible wiki at `wiki/` with a `raw/` intake folder.

### Wiki Structure

```
wiki/
  index.md          -- per-page summaries, LLM reads this first for navigation
  log.md            -- append-only processing log
  platform/         -- platform patterns, API behavior, gotchas
  clients/          -- per-client knowledge, architecture, results
  patterns/         -- reusable patterns, error handling, logging
  decisions/        -- architectural decisions with rationale
  people/           -- team members, roles, ownership
raw/                -- drop zone for incoming files (web clips, transcripts, PDFs)
  processed/        -- files moved here after wiki-ingest processes them
```

### Wiki Commands

| Command | What It Does |
|---|---|
| `/wiki-ingest` | Process files in `raw/` into wiki pages. Creates/updates pages, links, index, log. |
| `/wiki-file <topic>` | File a conversation insight as a wiki page. The compounding loop. |
| `/wiki-lint` | Health check: orphans, broken links, stale pages, contradictions, missing pages. |

### Wiki Operations

**Ingest (raw/ -> wiki/):**
1. User drops file in `raw/` (web clip, meeting notes, PDF, transcript)
2. Run `/wiki-ingest`
3. LLM reads source, creates/updates wiki pages in correct categories
4. Cross-links added to existing pages
5. `index.md` updated with per-page summaries
6. `log.md` appended with processing record
7. Source file moved to `raw/processed/`

**Query (wiki -> answer -> wiki):**
1. LLM reads `wiki/index.md` first to locate relevant pages
2. Drills into pages, follows `[[wiki links]]`
3. Synthesizes answer
4. If the answer is valuable, run `/wiki-file <topic>` to capture it permanently

**Lint (periodic health check):**
1. Run `/wiki-lint` weekly or after major changes
2. Fixes orphans, broken links, stale pages, missing index entries
3. Pass `fix` argument to auto-repair

### Three Knowledge Systems

Each serves a different purpose. Do not merge them.

| System | Purpose | Format | Updated By |
|---|---|---|---|
| `expertise.yaml` | Operational data (project state, API gotchas, results) | Structured YAML | `/*` commands |
| `.claude/memory/` | Behavioral rules (user preferences, guardrails, process rules) | Markdown + frontmatter | Claude automatically |
| `wiki/` | Synthesized knowledge (patterns, decisions, people, concepts) | Obsidian markdown + `[[links]]` | `/wiki-*` commands |

### Wiki Page Format

```markdown
# Page Title

#tag1 #tag2 #category

Content here. One concept per page. Concise.

Source: who confirmed, when, or raw/filename

## Related

- [[other-page]] -- why it connects
- [[another-page]] -- how it relates
```

### Rules
- One concept per page
- `[[wiki links]]` for cross-references
- `#tags` on line 2
- Source attribution on every page
- `## Related` section at bottom with links
- Keep pages concise -- wiki, not documentation
- Questions that produce good answers get filed as pages (compounding loop)
- expertise.yaml = runtime data, wiki = durable knowledge, memory = behavioral rules

---

## The Self-Learn Loop

Every `/*` command appends raw observations to `unvalidated_observations:` in expertise.yaml.

Running `/improve {client}` validates each observation against current live state
and either:
- Promotes confirmed facts into the relevant expertise section
- Discards observations that are stale or already captured

### Self-Learn Rules
1. Never manually edit `unvalidated_observations:` -- let commands append to it
2. Run `/improve` after any significant investigation or discovery session
3. Keep expertise.yaml under 1000 lines -- self-improve compresses when needed
4. YAML must always be valid: `python3 -c "import yaml; yaml.safe_load(open('clients/{client}/expertise.yaml'))"`

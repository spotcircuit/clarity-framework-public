# Clarity Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Commands](https://img.shields.io/badge/commands-23-green.svg)](.claude/commands/)
[![Wiki](https://img.shields.io/badge/docs-live-brightgreen.svg)](https://spotcircuit.github.io/clarity-wiki/)

**Claude Code forgets everything between sessions. Clarity fixes that.**

23 slash commands that capture what your AI learns and make it persistent. You explain your project once. Every session after that starts with full context.

**[Browse the Docs](https://spotcircuit.github.io/clarity-wiki/)** | [Getting Started](wiki/getting-started.md) | [All Commands](wiki/how-it-works/commands.md) | [Examples](wiki/examples/)

## The Problem

```
Session 1: "Here's our architecture, we use FastAPI, the deploy goes to..."
Session 2: "Remember yesterday? We use FastAPI, the deploy goes to..."
Session 3: "So like I was saying, FastAPI, and the deploy..."
```

Every Claude Code session starts from zero. Project context lives in your head. Tribal knowledge stays tribal.

## How Clarity Fixes It

```bash
git clone https://github.com/spotcircuit/clarity-framework-public.git
cd clarity-framework-public

# In Claude Code:
/create my-project        # Set up the project
/discover my-project      # Auto-generate expertise.yaml from your codebase
```

That's it. Now every session starts by reading `expertise.yaml` — your project's structured memory.

As you work, commands capture what you learn:
```
/improve my-project       # Validate observations against live code
                          # Promotes confirmed facts, discards stale ones
                          # Your context compounds over time
```

[Full getting started guide →](wiki/getting-started.md)

## What You Get

**Not a CLI tool, SDK, or plugin.** These are markdown files in `.claude/commands/` that Claude Code reads as instructions. Clone the repo and the commands just work.

### Context that persists

| What happens | Without Clarity | With Clarity |
|---|---|---|
| Session 1 | Explain everything | `/discover` captures it |
| Session 2 | Explain it again | Claude reads expertise.yaml |
| Session 3 | Explain it again | Claude already knows |
| After a bug fix | You remember, AI doesn't | `/improve` captures the gotcha |
| New team member | 2 weeks onboarding | `/brief` gives full context |

### 23 commands across four categories

**Project context** — `/create`, `/discover`, `/brief`, `/check`, `/improve`, `/meeting`

**Development** — `/new`, `/feature`, `/bug`, `/takeover`, `/plan`, `/build`, `/test`, `/review`

**Knowledge** — `/wiki-ingest`, `/wiki-file`, `/wiki-lint`

**Advanced** — `/plan-build-improve`, `/test-learn`, `/plan-scout`, `/build-parallel`, `/scout`, `/meta-prompt`

[See all commands with examples →](wiki/how-it-works/commands.md)

### Three places knowledge lives

| File | What it holds | How it updates |
|---|---|---|
| `expertise.yaml` | Project state, API gotchas, architecture decisions | Commands append, `/improve` validates |
| `.claude/memory/` | Your preferences, guardrails, behavioral rules | Claude updates automatically |
| `wiki/` | Patterns, decisions, synthesized knowledge | `/wiki-ingest`, `/wiki-file` |

They're separate because they change at different speeds. `expertise.yaml` updates every session. Memory updates when Claude notices a preference. Wiki updates when durable knowledge emerges.

## Real Examples

### What expertise.yaml looks like after 4 sessions

```yaml
# apps/site-builder/expertise.yaml (real, not generated for this README)
architecture:
  backend: FastAPI + Python 3.13 + asyncio
  frontend: Vue 3 + TypeScript + Pinia
  ai_content: Claude Sonnet
  deploy_primary: Cloudflare Pages

api_gotchas:
  - "Google Maps blocks headless Chrome without stealth plugin"
  - "Claude sometimes returns markdown in HTML fields — sanitize"
  - "Cloudflare Pages has a 100-project limit — auto-delete oldest"

key_decisions:
  - "Vue for dashboard, React for generated sites — different concerns"
  - "WebSocket for progress — real-time feedback matters for 60s generation"

unvalidated_observations: []  # Clean — all validated by /improve
```

[See the full expertise.yaml →](apps/site-builder/expertise.yaml)
[See the build journal showing how it grew →](apps/site-builder/BUILD_JOURNAL.md)

### What raw file ingestion looks like

Drop a messy meeting transcript in `raw/`:
```
raw/demo-meeting-transcript.md  ← messy Teams transcript
raw/demo-slack-export.md        ← #incidents channel dump
raw/demo-jira-notes.md          ← sprint tickets
```

Run `/wiki-ingest`. Get structured wiki pages with cross-references.

[See the raw files →](raw/) | [See what came out →](wiki/examples/demo-corp.md)

## How is this different from X?

**"Just use a good README"** — READMEs are static. Clarity's expertise.yaml updates as you work. `/improve` validates observations against actual code so the context stays accurate.

**"Just use Obsidian"** — Obsidian is manual curation. Clarity captures knowledge during development and validates it programmatically. The wiki/ folder IS an Obsidian vault if you want it.

**"Confluence / Notion"** — Those are for humans to maintain. Clarity's files are designed to be read and written by an LLM during work. They live in your repo, not a separate tool.

**"I'll just use CLAUDE.md"** — CLAUDE.md is one file. Clarity adds structured per-project expertise, a validation loop, 23 commands, and a wiki. CLAUDE.md is part of the system, not the whole system.

## Optional: Agent Orchestration

7 Paperclip agents that run on a schedule (not required for the core framework):

| Agent | What it does |
|---|---|
| Clarity Steward | Validates expertise.yaml health every 4 hours |
| Wiki Curator | Processes raw/ intake every 30 minutes |
| GTM Agent | Tracks engagement and adjusts content strategy |
| Triage Agent | Routes issues to the right agent |

```bash
npm install -g paperclipai
export PAPERCLIP_COMPANY_ID=your-id
bash scripts/paperclip-sync.sh
```

## Directory Structure

```
clarity-framework/
  .claude/commands/     # 23 slash commands
  apps/                 # Your apps (site-builder, demo-api examples included)
  clients/              # Your clients (demo-corp, acme-integration examples)
  wiki/                 # Knowledge wiki (Obsidian-compatible, Quartz-rendered)
  raw/                  # Drop zone for files to ingest
  system/               # Agent configs, Paperclip orchestration
  scripts/              # Wiki sync, Obsidian sync, Paperclip sync
```

## Inspiration

The wiki pattern is based on [Andrej Karpathy's LLM Wiki](https://karpathy.ai/) concept — using structured markdown as a knowledge layer that LLMs read natively. Clarity extends it with structured YAML for operational data, a validation loop, and a full development command suite.

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI
- Python 3.10+ (for YAML validation)
- Node.js 18+ (only for Paperclip agents, optional)

## License

MIT — see [LICENSE](LICENSE).

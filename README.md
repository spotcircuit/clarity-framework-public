# Clarity Framework

Structured knowledge management for engineering teams using Claude Code.

## What This Is (and Isn't)

This is a set of structured prompts and conventions for Claude Code. It is not a CLI tool, SDK, or plugin. The slash commands are markdown files that Claude Code reads and executes as instructions.

What you get:
- **10 slash commands** that build and maintain a knowledge base for any project
- **Three knowledge systems** (structured YAML, behavioral memory, Obsidian wiki) that serve different purposes and stay in sync
- **A self-learn loop** where commands append findings as YAML entries, and a validation command checks each against the current codebase and either promotes or discards them
- **Agent orchestration** via Paperclip with 6 pre-configured agents (optional)

Inspired by Andrej Karpathy's LLM Wiki pattern, extended with structured operational data and behavioral memory.

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed and authenticated
- Python 3.10+ (for YAML validation and config parsing)
- Node.js 18+ (only needed for Paperclip agent orchestration)

## Quick Start

### For clients (external engagements)

```bash
# 1. Create a new client
/create my-client

# 2. Generate Phase 0 discovery doc + seed expertise
/discover my-client

# 3. Use throughout the engagement
/brief my-client        # standup summary
/improve my-client  # validate and promote observations
/check my-client         # design guidelines compliance
```

### For apps (internal tools)

```bash
# 1. Copy template
cp apps/_templates/app.yaml apps/my-app/app.yaml

# 2. Same commands work
/discover my-app
/brief my-app
```

### For knowledge

```bash
# Drop files in raw/ and ingest
/wiki-ingest

# File insights from conversations
/wiki-file "topic name"

# Health check
/wiki-lint
```

## Commands

| Command | What It Does |
|---|---|
| `/create <name>` | Create a new client or app interactively |
| `/discover <name>` | Phase 0 auto-generation. Seeds expertise.yaml. |
| `/brief <name>` | Standup/handoff summary from expertise.yaml |
| `/improve <name>` | Validate observations, integrate confirmed facts |
| `/check <name>` | Design guidelines compliance check |
| `/meeting <name>` | Ingest meeting notes from Gmail into expertise |
| `/wiki-ingest` | Process files in `raw/` into wiki pages |
| `/wiki-file <topic>` | File a conversation insight as a wiki page |
| `/wiki-lint` | Health check: orphans, broken links, stale pages |

## Directory Structure

```
clarity-framework/
  .claude/commands/se/    # 10 slash commands (the core product)
  clients/
    _templates/           # Copy these to start a new client
    spotcircuit/          # Working example
  apps/
    _templates/           # Copy these to start a new app
  wiki/
    index.md              # LLM reads this first for navigation
  system/
    agents/               # Paperclip agent definitions
    paperclip.yaml        # Agent orchestration config
    drafts/               # Working drafts
  scripts/
    paperclip-sync.sh     # Sync agents to Paperclip
    wiki-sync.sh          # Sync wiki to external tools
    sync-obsidian.sh      # Obsidian vault sync
```

## Three Knowledge Systems

Each serves a different purpose. Do not merge them.

| System | Purpose | Format | Updated By |
|---|---|---|---|
| `expertise.yaml` | Operational data (project state, API gotchas, results) | Structured YAML | `slash commands` commands |
| `.claude/memory/` | Behavioral rules (user preferences, guardrails) | Markdown + frontmatter | Claude automatically |
| `wiki/` | Synthesized knowledge (patterns, decisions, concepts) | Obsidian markdown + `[[links]]` | `/wiki-*` commands |

## The Self-Learn Loop

```
You work --> commands append observations --> /improve validates
    ^                                              |
    |                                              v
    +--- confirmed facts promoted into expertise.yaml
```

Every `slash commands` command appends raw observations to `unvalidated_observations:` in expertise.yaml. Running `/improve` validates each one against current live state and either promotes confirmed facts into the relevant expertise section or discards stale ones.

## Comparison

**Why not Obsidian alone?**
Obsidian is great for human-readable knowledge, but it does not handle structured operational data (API endpoints, record counts, deployment status). Clarity uses Obsidian-compatible wiki pages for durable knowledge and YAML for operational data that commands can parse and update programmatically.

**Why not Confluence / Notion?**
Those tools are designed for human editors. Clarity's knowledge systems are designed to be read and written by an LLM during work, not maintained separately. The wiki, YAML, and memory files live in the repo alongside the code.

**Why three systems instead of one?**
Each has a different update frequency and consumer. `expertise.yaml` changes every session (operational state). `.claude/memory/` changes when Claude learns a new behavioral preference. `wiki/` changes when durable knowledge is synthesized. Merging them would make each harder to maintain and query.

## Agent Orchestration

Clarity includes 6 pre-configured Paperclip agents (optional -- the core framework works without them):

| Agent | Role | Schedule |
|---|---|---|
| Clarity Steward | Maintains expertise.yaml health | Every 4 hours |
| Wiki Curator | Processes raw/ intake, fixes links | Every 30 min |
| Site Builder Agent | Manages app lifecycle | Every 6 hours |
| Social Media Agent | Daily posting pipeline | Weekdays 9am |
| Outreach Agent | Monitors and responds to comments | Every 30 min |
| Triage Agent | Routes new issues to agents | Every 5 min |

```bash
# Requires PAPERCLIP_COMPANY_ID environment variable
export PAPERCLIP_COMPANY_ID=your-company-id
bash scripts/paperclip-sync.sh
```

## Install

```bash
git clone https://github.com/spotcircuit/clarity-framework.git
cd clarity-framework

# Start using slash commands immediately in Claude Code
/create my-first-client
```

For Paperclip agent orchestration:
```bash
npm install -g paperclipai
export PAPERCLIP_COMPANY_ID=your-company-id
bash scripts/paperclip-sync.sh
```

## License

MIT -- see [LICENSE](LICENSE).

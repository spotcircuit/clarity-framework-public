# Clarity Framework

Agentic intelligence framework for technical engagements. Gives any engineer full project context on day one and grows smarter throughout the engagement through a self-learn loop.

Based on Andrej Karpathy's LLM Wiki pattern, extended with structured operational data and behavioral memory.

## What It Does

- **Day-one context**: Run `/se:discover` on any codebase and get a structured knowledge base immediately
- **Self-learn loop**: Every command appends observations. `/se:self-improve` validates them against live state and promotes confirmed facts.
- **Three knowledge systems**: Structured YAML (operational data), markdown memory (behavioral rules), Obsidian wiki (durable knowledge)
- **9 slash commands** for Claude Code that chain together into autonomous workflows
- **Agent orchestration** via Paperclip with 6 pre-configured agents

## Quick Start

### For clients (external engagements)

```bash
# 1. Create a new client
/se:create my-client

# 2. Generate Phase 0 discovery doc + seed expertise
/se:discover my-client

# 3. Use throughout the engagement
/se:brief my-client        # standup summary
/se:self-improve my-client  # validate and promote observations
/se:check my-client         # design guidelines compliance
```

### For apps (internal tools)

```bash
# 1. Copy template
cp apps/_templates/app.yaml apps/my-app/app.yaml

# 2. Same commands work
/se:discover my-app
/se:brief my-app
```

### For knowledge

```bash
# Drop files in raw/ and ingest
/se:wiki-ingest

# File insights from conversations
/se:wiki-file "topic name"

# Health check
/se:wiki-lint
```

## Commands

| Command | What It Does |
|---|---|
| `/se:create <name>` | Create a new client or app interactively |
| `/se:discover <name>` | Phase 0 auto-generation. Seeds expertise.yaml. |
| `/se:brief <name>` | Standup/handoff summary from expertise.yaml |
| `/se:self-improve <name>` | Validate observations, integrate confirmed facts |
| `/se:check <name>` | Design guidelines compliance check |
| `/se:wiki-ingest` | Process files in `raw/` into wiki pages |
| `/se:wiki-file <topic>` | File a conversation insight as a wiki page |
| `/se:wiki-lint` | Health check: orphans, broken links, stale pages |
| `/se:meeting <name>` | Ingest meeting notes into expertise |

## Directory Structure

```
clarity-framework/
  .claude/commands/se/    # 9 slash commands (the core product)
  clients/
    _templates/           # Copy these to start a new client
    spotcircuit/          # Example client
  apps/
    _templates/           # Copy these to start a new app
    site-builder/         # Example app
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
| `expertise.yaml` | Operational data (project state, API gotchas, results) | Structured YAML | `/se:*` commands |
| `.claude/memory/` | Behavioral rules (user preferences, guardrails) | Markdown + frontmatter | Claude automatically |
| `wiki/` | Synthesized knowledge (patterns, decisions, concepts) | Obsidian markdown + `[[links]]` | `/se:wiki-*` commands |

## The Self-Learn Loop

```
You work --> commands append observations --> /se:self-improve validates
    ^                                              |
    |                                              v
    +--- confirmed facts promoted into expertise.yaml
```

Every `/se:*` command appends raw observations to `unvalidated_observations:` in expertise.yaml. Running `/se:self-improve` validates each one against current live state and either promotes confirmed facts or discards stale ones.

## Agent Orchestration

Clarity includes 6 pre-configured Paperclip agents:

| Agent | Role | Schedule |
|---|---|---|
| Clarity Steward | Maintains expertise.yaml health | Every 4 hours |
| Wiki Curator | Processes raw/ intake, fixes links | Every 30 min |
| Site Builder Agent | Manages app lifecycle | Every 6 hours |
| Social Media Agent | Daily posting pipeline | Weekdays 9am |
| Outreach Agent | Monitors and responds to comments | Every 30 min |
| Triage Agent | Routes new issues to agents | Every 5 min |

```bash
# Start Paperclip and sync agents
bash scripts/paperclip-sync.sh

# Check status
bash scripts/paperclip-sync.sh status

# Trigger a heartbeat
bash scripts/paperclip-sync.sh heartbeat clarity-steward
```

## Setup

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- Python 3.10+
- Node.js 18+ (for Paperclip)

### Install

```bash
git clone https://github.com/spotcircuit/clarity-framework-public.git
cd clarity-framework-public

# Start using slash commands immediately
/se:create my-first-client
```

No dependencies to install for the core framework. It's just YAML, markdown, and Claude Code commands.

For Paperclip agent orchestration:
```bash
npm install -g paperclipai
bash scripts/paperclip-sync.sh
```

## License

MIT

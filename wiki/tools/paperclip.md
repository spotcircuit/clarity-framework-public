# Paperclip Agent Orchestration

Paperclip is a local agent management system that runs Clarity's 7 autonomous agents. Each agent has a defined role, a heartbeat schedule, and a monthly budget cap. Paperclip handles scheduling, issue routing, and execution tracking.

## Architecture

The framework defines agents declaratively in `system/paperclip.yaml`. A sync script pushes definitions to the Paperclip API. Paperclip then manages heartbeats, issue assignment, and budget enforcement.

```
system/paperclip.yaml          # source of truth for all agent config
system/agents/*.yaml           # detailed per-agent definitions
system/.paperclip-ids.json     # cached API IDs after first sync
tools/paperclip-sync.sh        # CLI for sync, status, heartbeat, issues
```

## The 7 Agents

### Clarity Steward
**Role:** Maintenance | **Schedule:** Every 4 hours | **Budget:** $5/mo

Maintains expertise.yaml health across all clients and apps. On each heartbeat:
1. Validates YAML syntax for every expertise.yaml
2. Flags files over 900 lines (cap is 1000)
3. Counts unvalidated observations -- runs `/improve` if over 10 pending
4. Compresses bloated files

### Wiki Curator
**Role:** Maintenance | **Schedule:** Every 30 minutes | **Budget:** $3/mo

Keeps the knowledge wiki healthy. On each heartbeat:
1. Checks `raw/` for unprocessed files
2. If files found, runs `/wiki-ingest` and reports results
3. If no files, runs `/wiki-lint` in quick mode
4. Auto-fixes broken links and orphaned pages (up to 5 per run)

### Site Builder Agent
**Role:** Engineer | **Schedule:** Every 6 hours | **Budget:** $8/mo

Manages the site-builder app lifecycle. Picks up build requests from the issue queue, executes the pipeline, and records results in expertise.yaml. Escalates failures to the Triage Agent.

### Social Media Agent
**Role:** CMO | **Schedule:** Weekdays at 9am | **Budget:** $2/mo

Runs the daily social media pipeline:
1. Topic rotation (services, clarity, case study)
2. Draft generation from templates
3. Humanization via Claude
4. Image card generation (HTML to PNG)
5. Post to LinkedIn and Facebook
6. Save drafts and file to wiki

### Outreach Agent
**Role:** Engineer | **Schedule:** Every 30 minutes | **Budget:** $3/mo

Monitors posts for new comments. Classifies each comment (question, objection, compliment), generates a reply using the outreach framework, humanizes it, and posts. Alternates scouting between LinkedIn and Reddit each heartbeat.

### GTM Agent
**Role:** CMO | **Schedule:** Weekdays at 8am | **Budget:** $4/mo

Go-to-market orchestrator. Runs daily before the Social Media Agent:
1. Pulls engagement metrics from LinkedIn, Reddit, GitHub
2. Identifies prospects by scanning comments and profiles
3. Manages the content calendar across 6 services
4. Coordinates with Outreach and Social Media agents
5. Generates weekly GTM reports every Friday

### Triage Agent
**Role:** PM | **Schedule:** Every 5 minutes | **Budget:** $1/mo

Lightweight issue router. Reads new unassigned issues and classifies them:
- Wiki/ingest keywords -> Wiki Curator
- Build/deploy/site keywords -> Site Builder Agent
- Expertise/validation keywords -> Clarity Steward
- Unknown -> leaves unassigned with a clarification comment

## Setup

### Install Paperclip

```bash
npm install -g paperclipai
# or run directly
npx paperclipai run
```

Paperclip starts a local API server on `http://127.0.0.1:3100`.

### Sync Agent Definitions

Push all 7 agents from `system/paperclip.yaml` to the Paperclip API:

```bash
bash tools/paperclip-sync.sh agents
```

```
[paperclip-sync] Syncing agent definitions to Paperclip...
[paperclip-sync]   Creating agent 'Clarity Steward'...
[paperclip-sync]   Created 'Clarity Steward' with id: abc123
[paperclip-sync]   Creating agent 'Wiki Curator'...
[paperclip-sync]   Created 'Wiki Curator' with id: def456
...
[paperclip-sync] Sync complete.
```

Agent IDs are cached in `system/.paperclip-ids.json` so subsequent syncs skip already-registered agents.

### Check Status

```bash
bash tools/paperclip-sync.sh status
```

```
[paperclip-sync] Paperclip is running.
[paperclip-sync] Registered agents:
  - Clarity Steward (id: abc123, role: devops)
  - Wiki Curator (id: def456, role: researcher)
  - Triage Agent (id: ghi789, role: pm)
  ...
```

### Trigger a Heartbeat Manually

```bash
bash tools/paperclip-sync.sh heartbeat clarity-steward
```

This runs the agent's heartbeat routine immediately instead of waiting for the cron schedule.

### Create an Issue

```bash
bash tools/paperclip-sync.sh issue "Ingest meeting notes from Dec 15" wiki-curator
```

Creates an issue in the Clarity Ops project and assigns it to the specified agent.

## Event Hooks

Clarity events automatically create Paperclip issues:

| Event | Issue Created | Assigned To |
|---|---|---|
| New file in `raw/` | "Ingest: {filename}" | Wiki Curator |
| Self-improve overdue | "Self-improve: {target}" | Clarity Steward |
| Build requested | "Build: {app_name}" | Site Builder Agent |

## Editing Agent Definitions

1. Edit `system/paperclip.yaml` or `system/agents/{name}.yaml`
2. Run `bash tools/paperclip-sync.sh agents` to push changes
3. Paperclip picks up the new config on the next heartbeat

The YAML files are the source of truth. The Paperclip API is a downstream consumer.

## Related

- [Architecture](../diagrams/architecture.md) -- how agents fit into the overall system
- [Commands](../how-it-works/commands.md) -- the slash commands agents execute
- [Self-Learn Loop](../how-it-works/self-learn-loop.md) -- what Clarity Steward maintains

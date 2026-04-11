# Getting Started

A 15-minute walkthrough from clone to working framework.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- Python 3.10+ (for YAML validation)
- Git

## 1. Clone the Repo

```bash
git clone https://github.com/spotcircuit/clarity-framework.git
cd clarity-framework
```

You should see this structure:

```
clarity-framework/
  clients/          # external engagements
  apps/             # internal tools/products
  wiki/             # knowledge wiki (Obsidian-compatible)
  raw/              # drop zone for incoming files
  system/           # agent definitions, drafts, config
  scripts/          # sync and utility scripts
  .claude/commands/ # slash command definitions
  CLAUDE.md         # framework instructions (Claude reads this automatically)
```

## 2. Create Your First Client

```
> /create my-client
```

Claude prompts you progressively for what you know:

```
Client name: my-client
Display name: My Client Inc
Industry: fintech
Goal: Migrate legacy payment flows to event-driven architecture
Tech stack: Node.js, PostgreSQL, RabbitMQ
```

This creates:

```
clients/my-client/
  client.yaml       # config (gitignored -- contains sensitive data)
  expertise.yaml    # starts nearly empty, grows over time
  notes.md          # session notes
  specs/            # implementation plans
```

## 3. Run Discovery

```
> /discover my-client
```

Discovery pulls from every available source -- Jira, Slack, live systems, codebase -- and generates a Phase 0 document plus initial expertise.yaml entries.

```
Phase 0 identified:
  - 3 core payment flows (checkout, refund, subscription)
  - RabbitMQ as message broker, 12 existing queues
  - PostgreSQL 14 with 47 tables, no migration tooling
  - Auth: JWT with Redis session cache
  - Deployment: Docker Compose on EC2 (no k8s)

Created: clients/my-client/phase-0-discovery.md
Seeded: clients/my-client/expertise.yaml (23 entries)
Appended: 5 unvalidated observations
```

Anything Discovery cannot derive is marked `TODO` in the Phase 0 doc for you to fill in.

## 4. Your First Build Cycle

### Plan

```
> /plan migrate checkout flow to event-driven pattern
```

Claude explores the existing codebase, reads expertise.yaml for context, and writes a detailed implementation plan:

```
Created: clients/my-client/specs/checkout-event-driven.md

Plan summary:
  1. Define CheckoutInitiated, PaymentProcessed, CheckoutCompleted events
  2. Create RabbitMQ exchange: checkout.events (topic)
  3. Refactor checkout controller to publish events instead of direct calls
  4. Add consumer services for inventory, notification, analytics
  5. Migration: run both paths in parallel for 1 week, then cut over

Estimated: 4 files modified, 3 new files, ~400 lines
```

### Build

```
> /build clients/my-client/specs/checkout-event-driven.md
```

Claude implements the plan top-to-bottom, validating as it goes:

```
Building checkout-event-driven.md...

[1/5] Event definitions created
[2/5] RabbitMQ exchange configured
[3/5] Checkout controller refactored
[4/5] Consumer services created
[5/5] Migration toggle added

Build complete. 4 files modified, 3 new files.
Appended 3 observations to expertise.yaml
```

### Test

```
> /test my-client backend
```

```
Running test suite...

47 passed, 2 failed

FAIL: test_checkout_event_published
  Expected: CheckoutInitiated event in queue
  Got: ConnectionRefusedError on RabbitMQ
  Location: tests/checkout/test_events.py:34

FAIL: test_inventory_consumer
  Expected: stock decremented
  Got: AssertionError (stock unchanged)
  Location: tests/consumers/test_inventory.py:22

Fix these before proceeding? (y/n)
```

## 5. Self-Improvement

After building and testing, run self-improve to process observations:

```
> /improve my-client
```

```
Reviewing 8 unvalidated observations...

PROMOTED: "RabbitMQ connection requires explicit heartbeat config"
  -> Added to infrastructure.known_issues

PROMOTED: "Checkout controller has 3 direct DB calls that bypass the ORM"
  -> Added to codebase.tech_debt

DISCARDED: "Docker Compose might need network aliases"
  -> Already configured in docker-compose.yml

DEFERRED: "Redis session TTL may need tuning for event-driven flow"
  -> Cannot verify without load testing

5 promoted, 2 discarded, 1 deferred.
```

Each `/improve` cycle makes expertise.yaml more accurate. Over time, it becomes a complete operational reference that gives any engineer (human or AI) full context on the project.

## 6. Wiki Knowledge Capture

Drop any file into `raw/` -- meeting notes, web clips, PDFs, transcripts -- and ingest it:

```
> /wiki-ingest
```

```
Processing raw/...

Found 2 unprocessed files:
  1. raw/rabbitmq-retry-patterns.md
  2. raw/meeting-notes-2024-12-15.txt

Created: wiki/platform/rabbitmq-retry-patterns.md
Updated: wiki/clients/my-client-architecture.md (added retry section)
Updated: wiki/index.md (2 new entries)
Appended: wiki/log.md

Moved to raw/processed/:
  - rabbitmq-retry-patterns.md
  - meeting-notes-2024-12-15.txt
```

When a conversation produces a valuable insight, capture it immediately:

```
> /wiki-file rabbitmq dead letter exchange gotcha
```

This creates a permanent wiki page so the knowledge never has to be rediscovered.

## What Next

- Run `/brief my-client` at the start of every session for a standup summary
- Run `/check my-client` to verify compliance against the Phase 0 doc
- Run `/review my-client` after changes for code review
- Run `/wiki-lint` periodically to keep the wiki healthy
- See [Commands](how-it-works/commands.md) for all 19 slash commands
- See [Paperclip](tools/paperclip.md) for autonomous agent orchestration

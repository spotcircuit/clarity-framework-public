# Commands

Clarity has 19 slash commands organized into four groups: client/app management, development workflow, wiki management, and utilities.

All commands auto-resolve names from both `clients/` and `apps/` directories.

## Client / App Management

### `/create <name>`
Create a new client or app. Prompts progressively for what you know, creates config files, then hands off to `/discover`.

```
> Client name: acme-integration
> Display name: Acme Logistics Integration
> Industry: trade compliance / logistics
> Goal: AI-assisted flow generation and deployment for Node-RED platform
```

### `/discover <name>`
Auto-generate a Phase 0 discovery document and seed expertise.yaml. Pulls from every available source (Jira, Slack, live systems, codebase). Marks anything it cannot derive as TODO.

```
Phase 0 identified:
  - 4 core flows (receiving, compliance, filing, tracking)
  - Node-RED Admin API as deployment target
  - Credential nodes as special case (not returned by GET)
  - MQTT as inter-flow communication
```

### `/brief <name>`
Generate a standup/handoff summary from expertise.yaml. This is typically the first command at the start of each session.

```
Site Builder — Briefing
━━━━━━━━━━━━━━━━━━━━━━
Status: Building (Day 2)
Pipeline: 4 steps, URL→Scrape→Generate→Build
Key gap: Content quality (generic output)
Unvalidated: 2 deferred observations (reviews, images)
Next priority: Enrich business data before generation step

Suggested focus:
  1. Add review scraping to maps_scraper.py
  2. Consider website scraping as supplementary data source
  3. Image generation for hero/gallery sections
```

### `/improve <name>`
Validate unvalidated observations against current state. Promotes confirmed facts, discards stale ones, defers unverifiable ones.

```
Reviewing 4 unvalidated observations...

PROMOTED: "Website scraper color extraction is brittle"
  → Added to scraping.known_limitations

DISCARDED: "WebSocket progress reporting would be useful"
  Reason: Already implemented later in the same session.

3 promoted, 1 discarded, 0 deferred.
```

### `/check <name>`
Design guidelines compliance check against a Phase 0 document. Reports what is compliant, incomplete, or missing.

## Development Workflow

### `/new <app-name> <description>`
Scaffold a new application under `apps/` with expertise.yaml initialized and expertise bootstrapped.

### `/takeover <app-name>`
Understand an existing app, build its expertise domain, and produce a prime context file. After this, the app is integrated into the framework and ready for `/feature`.

### `/feature <app-name> <request>`
Expertise-informed feature workflow: load context, plan, build, then update the self-learn loop.

### `/bug <app-name> <symptom>`
Investigation-first bug fixing: reproduce, locate faulty code, make minimal change, verify. Fires self-learn at the end to capture the bug pattern.

### `/plan <prompt>`
Create a detailed implementation plan and save it to `specs/`. Explores the codebase to understand existing patterns before planning. Supports parallel scout subagents for complex features.

### `/build <path-to-plan>`
Implement a plan file top-to-bottom, validate the work, then append passive expertise observations.

### `/test <app-name> [backend|frontend|all]`
Run the test suite, parse results, report failures with exact locations. Optionally fix failures before reporting.

### `/review <app-name>`
Code review of recent changes for correctness, security, pattern compliance, and test coverage. Produces a structured report with CRITICAL / WARNING / NOTE classifications.

### `/scout <app-name> <question>`
Read-only codebase investigation. Analyzes issues, identifies root causes, suggests fixes without modifying files.

## Wiki Management

### `/wiki-ingest`
Scan `raw/` folder for unprocessed files (markdown, PDF, text, HTML) and ingest them into wiki pages. Updates index, adds cross-links, moves processed files to `raw/processed/`.

### `/wiki-file <topic>`
Capture an insight from the current conversation as a permanent wiki page. This is the compounding loop -- when something is figured out, it never has to be figured out again.

### `/wiki-lint [fix]`
Health check on `wiki/`: orphan pages, broken links, stale pages, contradictions with expertise.yaml, missing index entries. Pass `fix` to auto-repair.

## Utilities

### `/meeting <client> [keyword]`
Ingest meeting notes from Gmail (Gemini auto-notes) into notes.md and expertise.yaml.

### `/meta-prompt <request>`
Create a new slash command prompt based on a description.

## Related

- [The Self-Learn Loop](self-learn-loop.md) -- How `/improve` drives the feedback cycle
- [Three Knowledge Systems](three-systems.md) -- Which commands update which system
- [Site Builder](../examples/site-builder.md) -- Commands used across four build sessions

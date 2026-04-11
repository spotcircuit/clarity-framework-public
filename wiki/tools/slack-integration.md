# Slack Integration

#tools #slack #mcp #knowledge-capture

Capture tribal knowledge from Slack channels into the Clarity wiki. Two approaches: MCP server for live access, or export ingestion for bulk processing.

## Approach 1: MCP Slack Server (Live Access)

### Setup

Add the Slack MCP server to Claude Desktop config:

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic/mcp-remote",
        "https://mcp.slack.com/sse"
      ]
    }
  }
}
```

For Claude Code, add to `.mcp.json`:

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic/mcp-remote",
        "https://mcp.slack.com/sse"
      ]
    }
  }
}
```

Restart and authorize via Slack OAuth when prompted.

### What You Can Do

With the MCP server connected, Claude can:

- **Read channels:** `slack_read_channel` -- pull recent messages from any accessible channel
- **Search messages:** `slack_search_public` -- find messages matching keywords across public channels
- **Read threads:** `slack_read_thread` -- get full thread context for a specific message
- **Get user profiles:** `slack_read_user_profile` -- resolve who said what

### Example: Capturing an Incident Discussion

```
> Read the #incidents channel from this week and summarize root causes

Reading #incidents...

Found 2 incidents this week:

1. 2026-04-08: Redis connection timeout (45 min outage)
   Root cause: ElastiCache maintenance window overlapped with peak traffic
   Fix: Moved maintenance window to 3am UTC
   Thread: 12 messages, resolved by @ops-team

2. 2026-04-09: Deploy pipeline stuck (20 min)
   Root cause: GitHub Actions runner pool exhausted by parallel PR builds
   Fix: Added concurrency limit to CI workflow
   Thread: 8 messages, resolved by @devops

> /wiki-file "incident-redis-timeout-2026-04-08"
Created wiki/incidents/redis-timeout-2026-04-08.md
```

## Approach 2: Export Ingestion (Bulk)

For teams that prefer not to grant live Slack access, or for processing historical data.

### Setup

1. Export channel history from Slack (Settings > Import/Export Data, or use `slack-export` CLI tool)
2. Drop the export folder or JSON files in `raw/`:

```
raw/
  slack-export-2026-04/
    general/
      2026-04-01.json
      2026-04-02.json
    incidents/
      2026-04-08.json
      2026-04-09.json
    architecture-decisions/
      2026-04-05.json
```

3. Run `/wiki-ingest`:

```
/wiki-ingest

Processing raw/slack-export-2026-04/...
  incidents/2026-04-08.json -> wiki/incidents/redis-timeout-2026-04-08.md
  incidents/2026-04-09.json -> wiki/incidents/ci-runner-exhaustion-2026-04-09.md
  architecture-decisions/2026-04-05.json -> wiki/decisions/redis-vs-memcached.md

3 wiki pages created, 2 existing pages updated with cross-links.
Source files moved to raw/processed/
```

### What /wiki-ingest Extracts from Slack

| Slack Content | Wiki Output |
|---|---|
| Incident threads | `wiki/incidents/` pages with timeline, root cause, fix |
| Architecture discussions | `wiki/decisions/` pages with rationale and dissenting views |
| Debugging threads | `wiki/patterns/` pages with symptoms, diagnosis, solution |
| Onboarding questions | `wiki/getting-started/` FAQ updates |
| Deploy announcements | Cross-referenced with `expertise.yaml` deployment records |

### Example: Slack Thread to Wiki Page

Slack thread in #architecture-decisions:

```
@sarah: Should we use Redis or Memcached for the deployment status cache?
@brian: Redis. We need TTL per key and the pub/sub for cache invalidation.
@sarah: Memcached is simpler and faster for pure key-value.
@brian: True but we also want sorted sets later for leaderboards. Redis gives us that.
@sarah: Fair. Redis it is. Let's use ElastiCache since we're already on AWS.
@brian: +1. cache.t3.micro for now, upgrade when we hit the memory limit.
```

After `/wiki-ingest`, this becomes:

```markdown
# Redis vs Memcached for Deployment Cache

#decisions #redis #caching

Decided to use Redis over Memcached for deployment status caching.

## Decision: Redis (via AWS ElastiCache)

## Rationale
- Need TTL per key for cache expiry
- Pub/sub for cross-instance cache invalidation
- Sorted sets for future leaderboard/ranking features
- ElastiCache gives managed Redis on existing AWS infrastructure

## Alternatives Considered
- **Memcached**: Simpler, slightly faster for pure key-value. Rejected because
  we need pub/sub and sorted sets.

## Sizing
- Starting with cache.t3.micro
- Upgrade trigger: memory utilization > 80%

Source: #architecture-decisions, 2026-04-05, @sarah + @brian

## Related
- [[demo-api-architecture]] -- uses this caching layer
- [[aws-elasticache-setup]] -- configuration details
```

## Channel Monitoring Patterns

Useful channels to watch and what they produce:

| Channel | Watch For | Wiki Category |
|---|---|---|
| #incidents | Outage threads with root cause | `wiki/incidents/` |
| #architecture-decisions | Design discussions with rationale | `wiki/decisions/` |
| #til (today-i-learned) | Quick tips and gotchas | `wiki/patterns/` |
| #deploys | Deploy announcements + issues | Cross-ref with expertise.yaml |
| #onboarding | Recurring questions | `wiki/getting-started/` FAQ |

## Tips

- The MCP server approach is better for ongoing capture (read channels periodically)
- The export approach is better for initial knowledge bootstrap (dump 6 months of history)
- Threads are more valuable than top-level messages -- the discussion contains the context
- Always attribute: "Source: #channel, date, @person" on wiki pages
- Combine with Jira integration: when Slack mentions ticket IDs, link them in the wiki page

Source: MCP Slack server, Slack export API

## Related

- [Jira Integration](jira-integration.md) -- ticket context
- [GitHub Integration](github-integration.md) -- code context
- [Claude Desktop](claude-desktop.md) -- MCP server configuration

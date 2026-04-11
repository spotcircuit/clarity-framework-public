# Jira Integration

#tools #jira #mcp #project-management

Connect Clarity to Jira for automatic ticket context in expertise.yaml. Uses the MCP Jira server so Claude can read sprints, tickets, and blockers directly.

## Setup

### 1. Install the MCP Jira Server

Add the Atlassian MCP server to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic/mcp-remote",
        "https://mcp.atlassian.com/v1/sse"
      ]
    }
  }
}
```

Restart Claude Desktop. It will prompt for Atlassian OAuth on first use.

For Claude Code, add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic/mcp-remote",
        "https://mcp.atlassian.com/v1/sse"
      ]
    }
  }
}
```

### 2. Verify Access

After auth, test with a simple query:

```
> Search for open issues in project DEMO

Found 14 open issues in DEMO:
  DEMO-456: Rollback endpoint returns 500 on concurrent requests (Bug, High)
  DEMO-455: Add deployment metrics dashboard (Story, Medium)
  ...
```

## What /discover Pulls from Jira

When you run `/discover {client}`, Clarity reads Jira to seed expertise.yaml with project state:

| Data | Where It Goes | Example |
|---|---|---|
| Open ticket count by type | `project_health.backlog` | `bugs: 3, stories: 8, tasks: 2` |
| Current sprint tickets | `project_health.current_sprint` | `sprint: "Sprint 14", committed: 8, completed: 3` |
| Blockers and dependencies | `project_health.blockers` | `"DEMO-456 blocked by DEMO-123 (auth service migration)"` |
| Recent velocity | `project_health.velocity` | `last_3_sprints: [18, 21, 16]` |
| Component owners | `team.ownership` | `"auth-service: @sarah, deploy-api: @brian"` |

### Example expertise.yaml section

After `/discover` with Jira connected:

```yaml
project_health:
  backlog:
    total: 23
    bugs: 3
    stories: 14
    tasks: 6
  current_sprint:
    name: "Sprint 14"
    goal: "Deployment metrics + rollback hardening"
    committed: 8
    completed: 3
    days_remaining: 5
  blockers:
    - ticket: DEMO-456
      title: "Rollback endpoint returns 500 on concurrent requests"
      blocked_by: DEMO-123
      reason: "Auth service migration must complete before rollback can verify service tokens"
      days_blocked: 3
  velocity:
    last_3_sprints: [18, 21, 16]
    average: 18.3
```

## What /meeting Extracts

When meeting notes reference Jira tickets, Clarity links them:

```
Meeting notes mention: "DEMO-456 is blocked by the auth migration"

/meeting extracts:
  - Links DEMO-456 to DEMO-123 dependency
  - Captures "3 days blocked" timeline
  - Notes owner (@sarah) committed to unblocking by Thursday
  - Appends to unvalidated_observations:
    "DEMO-456 blocked by DEMO-123 (auth migration) -- @sarah targeting Thursday unblock"
```

## Jira Queries Clarity Uses

These JQL queries power the integration:

```
# Open issues for a project
project = DEMO AND status != Done ORDER BY priority DESC

# Current sprint
project = DEMO AND sprint in openSprints()

# Blockers
project = DEMO AND status = "Blocked" OR issueFunction in linkedIssuesOf("is blocked by")

# Recent completions (velocity calc)
project = DEMO AND status = Done AND resolved >= -21d

# Issues by component/label
project = DEMO AND component = "auth-service"
```

## Tips

- Run `/discover` at the start of each sprint to refresh project health data
- Blocker information is especially valuable for `/brief` -- it surfaces what's stuck
- Jira ticket IDs in expertise.yaml observations make them searchable
- The MCP server respects Jira permissions -- Claude only sees what your account can see

Source: MCP Atlassian server docs, tested with Jira Cloud

## Related

- [GitHub Integration](github-integration.md) -- PR and CI context
- [Slack Integration](slack-integration.md) -- team communication context
- [Claude Desktop](claude-desktop.md) -- MCP server configuration

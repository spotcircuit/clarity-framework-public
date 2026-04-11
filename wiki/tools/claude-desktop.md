# Claude Desktop Integration

Claude Desktop can access the full Clarity Framework knowledge base through the MCP filesystem server. This gives Claude Desktop the same context available in Claude Code -- wiki pages, expertise.yaml, agent definitions, and client data.

## How It Works

Claude Desktop supports MCP (Model Context Protocol) servers that provide file access. The `@modelcontextprotocol/server-filesystem` server gives Claude Desktop read access to specified directories.

The `sync-obsidian.sh` script already syncs framework files to a Windows-accessible path, so Claude Desktop can reach them without WSL path translation.

## Setup

### 1. Sync Framework Files to Windows

The Obsidian sync script copies framework directories to a Windows path:

```bash
bash scripts/sync-obsidian.sh
```

This syncs to a Windows-accessible location:
- `wiki/` -- knowledge wiki
- `apps/` -- app configurations and expertise
- `clients/` -- client configurations and expertise
- `system/` -- agent definitions and config
- `.claude/commands/` -- slash command definitions
- `CLAUDE.md` -- framework instructions

### 2. Configure MCP in Claude Desktop

Add the filesystem server to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "clarity-framework": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\path\\to\\clarity-framework\\wiki",
        "C:\\path\\to\\clarity-framework\\apps",
        "C:\\path\\to\\clarity-framework\\clients",
        "C:\\path\\to\\clarity-framework\\system"
      ]
    }
  }
}
```

Restart Claude Desktop after editing the config.

### 3. Add Project Instructions

In Claude Desktop, create a project and add this to the project instructions:

```
Read wiki/index.md first for navigation. Follow [[wiki links]] to drill into topics.
Read system/paperclip.yaml for agent definitions.
Read clients/{name}/expertise.yaml for project-specific context.
```

This tells Claude Desktop where to start when answering questions about the framework.

## What Claude Desktop Can Access

| Path | Content |
|---|---|
| `wiki/` | Knowledge wiki -- patterns, decisions, platform knowledge |
| `wiki/index.md` | Page summaries and navigation (read this first) |
| `apps/*/expertise.yaml` | App-specific operational data |
| `clients/*/expertise.yaml` | Client-specific operational data |
| `system/paperclip.yaml` | Agent orchestration config |
| `system/agents/*.yaml` | Detailed agent definitions |

## Same Knowledge, Multiple Interfaces

The framework's knowledge is stored in plain files. This means the same context is available across all interfaces:

| Interface | Access Method |
|---|---|
| Claude Code (CLI) | Direct file reads, slash commands |
| Claude Desktop | MCP filesystem server |
| Claude.ai (web) | Upload files or paste content |
| Obsidian | Direct vault on `wiki/` directory |
| Quartz site | Rendered wiki at GitHub Pages URL |

The self-learn loop (expertise.yaml) and wiki grow through Claude Code sessions. Claude Desktop reads the results. The sync script keeps everything current.

## Related

- [Obsidian](obsidian.md) -- local wiki editing
- [Quartz](quartz.md) -- wiki as a website
- [Paperclip](paperclip.md) -- agent orchestration

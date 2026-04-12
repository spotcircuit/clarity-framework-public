# Contributing to Clarity Framework

## Reporting Bugs

Open a GitHub issue with:
- What you expected to happen
- What actually happened
- Which slash command (if any) was involved
- Claude Code version and OS

## Contributing Code

1. Fork the repository
2. Create a feature branch (`git checkout -b fix/description`)
3. Make your changes
4. Test: ensure YAML files validate (`python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"`)
5. Submit a pull request against `master`

## Code Style

- **YAML files** must pass `yaml.safe_load()` without errors
- **Wiki pages** follow the format: title, brief description, content, Related section with links
- **Slash commands** are markdown files in `.claude/commands/` — they are Claude Code prompts, not traditional code. They use a frontmatter block for tool permissions and a structured markdown body that Claude interprets as instructions. Edit them like you would edit a detailed prompt, not a script.
- Keep expertise.yaml under 1000 lines
- One concept per wiki page
- Use relative markdown links for cross-references in wiki pages

## What Lives Where

| Directory | What It Contains |
|---|---|
| `.claude/commands/` | 19 slash command prompts (knowledge + dev workflow) |
| `clients/_templates/` | Templates for new client engagements |
| `apps/_templates/` | Templates for internal tools/apps |
| `wiki/` | Knowledge wiki (rendered via [Quartz](https://spotcircuit.github.io/clarity-wiki/)) |
| `scripts/` | Shell scripts for Paperclip sync, Obsidian sync, wiki sync |
| `system/agents/` | 7 Paperclip agent definitions |
| `system/paperclip.yaml` | Agent orchestration config |
| `raw/` | Intake folder for files to be ingested by `/wiki-ingest` |

## Key Technologies

| Tool | Purpose |
|---|---|
| [Claude Code](https://claude.ai/code) | AI-powered development environment that runs the slash commands |
| [Paperclip](https://github.com/paperclipai/paperclip) | Agent orchestration. Manages 7 autonomous agents with heartbeats and issue routing |
| [Quartz](https://quartz.jzhao.xyz/) | Renders the wiki/ folder as a searchable website |
| [Obsidian](https://obsidian.md/) | Optional. The wiki/ folder works as an Obsidian vault with cross-links |

## Testing Slash Commands

Slash commands run inside Claude Code. To test a change:
1. Open Claude Code in a repo that has Clarity set up
2. Run the command (e.g., `/brief my-client`)
3. Verify the output and any file changes are correct

There is no automated test suite for prompt-based commands. Review changes carefully and test manually.

## Command Categories

**Knowledge management:** `/create`, `/discover`, `/brief`, `/check`, `/improve`, `/meeting`

**Wiki:** `/wiki-ingest`, `/wiki-file`, `/wiki-lint`

**Development workflow:** `/new`, `/feature`, `/bug`, `/takeover`, `/plan`, `/build`, `/test`, `/review`

**Utilities:** `/scout`, `/meta-prompt`

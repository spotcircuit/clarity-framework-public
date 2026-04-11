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
- **Wiki pages** follow the format in CLAUDE.md: title, tags on line 2, content, Related section, source attribution
- **Slash commands** are markdown files in `.claude/commands/se/` -- they are Claude Code prompts, not traditional code. They use a frontmatter block for tool permissions and a structured markdown body that Claude interprets as instructions. Edit them like you would edit a detailed prompt, not a script.
- Keep expertise.yaml under 1000 lines
- One concept per wiki page
- Use `[[wiki links]]` for cross-references in wiki pages

## What Lives Where

| Directory | What It Contains |
|---|---|
| `.claude/commands/se/` | Slash command prompts (the core product) |
| `clients/_templates/` | Templates for new client engagements |
| `apps/_templates/` | Templates for internal tools/apps |
| `wiki/` | Obsidian-compatible knowledge wiki |
| `scripts/` | Shell scripts for Paperclip agent sync |
| `system/` | Agent definitions and guidelines |

## Testing Slash Commands

Slash commands run inside Claude Code. To test a change:
1. Open Claude Code in a repo that has Clarity set up
2. Run the command (e.g., `/brief my-client`)
3. Verify the output and any file changes are correct

There is no automated test suite for prompt-based commands. Review changes carefully and test manually.

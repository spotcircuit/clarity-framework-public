# Obsidian Integration

The Clarity wiki folder (`wiki/`) is a fully compatible Obsidian vault. You can browse, edit, and link wiki pages in Obsidian's graph view while the framework continues to manage them programmatically.

## How It Works

The `wiki/` directory uses standard Obsidian conventions:
- `[[wiki links]]` for cross-references between pages
- `#tags` on line 2 of each page
- Standard markdown with `## Related` sections at the bottom
- One concept per page

Obsidian reads these files directly. No conversion or export is needed.

## Setup

### 1. Create an Obsidian Vault

Open Obsidian and select "Open folder as vault." Point it at the `wiki/` directory inside your Clarity Framework installation:

```
/path/to/clarity-framework/wiki/
```

Obsidian will index all existing pages and render the `[[wiki links]]` as navigable connections.

### 2. Bidirectional Sync (WSL/Windows)

If you run the framework in WSL but use Obsidian on Windows, the `sync-obsidian.sh` script keeps both sides in sync:

```bash
# One-time sync
bash scripts/sync-obsidian.sh

# Continuous watch mode (syncs every 5 seconds)
bash scripts/sync-obsidian.sh watch
```

The script syncs:
- `wiki/` -- all wiki pages, bidirectional (newer files win)
- `raw/` -- drop zone for incoming files
- `.obsidian/` -- vault settings (WSL to Windows)
- `CLAUDE.md` and `README.md` -- framework docs

It also syncs framework files to a Windows path for Claude Desktop access (see [Claude Desktop](claude-desktop.md)).

### 3. Recommended Obsidian Plugins

These are optional but improve the experience:
- **Dataview** -- query wiki pages by tags or frontmatter
- **Graph Analysis** -- visualize connections between knowledge pages
- **Templater** -- create new wiki pages with the standard format
- **Git** -- commit wiki changes from within Obsidian

## Workflow

### Framework Creates Pages, Obsidian Displays Them

When you run `/wiki-ingest` or `/wiki-file`, the framework creates pages in `wiki/` with proper `[[links]]` and `#tags`. Obsidian picks them up instantly (or on the next sync cycle in WSL).

### Obsidian Edits Flow Back

If you edit a page in Obsidian -- add a note, fix a link, reorganize content -- the sync script carries those changes back to WSL. The framework respects manual edits and will not overwrite them.

### Graph View

Obsidian's graph view shows how wiki pages connect. Pages with many incoming links are knowledge hubs. Orphaned pages (no links) show up as disconnected nodes -- run `/wiki-lint` to fix them.

## Wiki Page Format

Every wiki page follows this structure (works in both Obsidian and the framework):

```markdown
# Page Title

#tag1 #tag2 #category

Content here. One concept per page. Concise.

Source: who confirmed, when, or raw/filename

## Related

- [[other-page]] -- why it connects
- [[another-page]] -- how it relates
```

## Related

- [Quartz](quartz.md) -- render the wiki as a website
- [Wiki Commands](../how-it-works/commands.md#wiki-management) -- `/wiki-ingest`, `/wiki-file`, `/wiki-lint`
- [Three Knowledge Systems](../how-it-works/three-systems.md) -- where the wiki fits

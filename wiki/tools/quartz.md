# Quartz Wiki Site

Quartz turns the `wiki/` markdown into a searchable, navigable website. The framework includes a sync script that pushes wiki content to a Quartz repository, which deploys automatically via GitHub Pages.

## How It Works

```
wiki/ (markdown) --> wiki-sync.sh --> Quartz repo (content/) --> GitHub Pages
```

Quartz renders:
- Full-text search across all wiki pages
- `[[wiki links]]` as clickable navigation
- Graph view showing page connections
- Tag pages grouping content by `#tags`
- Backlinks showing which pages reference the current one

## Setup

### 1. Create a Quartz Repository

```bash
git clone https://github.com/jackyzha0/quartz.git clarity-wiki-site
cd clarity-wiki-site
npm install
```

### 2. Configure Quartz

Edit `quartz.config.ts` to set your site title and base URL:

```typescript
const config: QuartzConfig = {
  configuration: {
    pageTitle: "Clarity Wiki",
    enableSPA: true,
    enablePopovers: true,
    baseUrl: "yourusername.github.io/clarity-wiki-site",
  },
  // ...
}
```

### 3. Sync Wiki Content

The `wiki-sync.sh` script copies all wiki pages into the Quartz content directory:

```bash
bash scripts/wiki-sync.sh
```

```
[wiki-sync] Syncing wiki/ to Quartz content/...
[wiki-sync] Copied 34 pages.
[wiki-sync] Pushed to GitHub. Deploy will start automatically.
[wiki-sync] Site: https://yourusername.github.io/clarity-wiki-site/
```

The script:
1. Clears the Quartz `content/` directory
2. Copies `wiki/index.md` and all subdirectories (patterns, platform, decisions, clients, people, apps)
3. Commits and pushes to the Quartz repo
4. GitHub Actions builds and deploys the site

### 4. GitHub Pages Deployment

In the Quartz repo settings on GitHub:
1. Go to Settings > Pages
2. Set Source to "GitHub Actions"
3. Quartz includes a workflow file that builds and deploys on every push

### 5. Run Locally

Preview the site before deploying:

```bash
cd clarity-wiki-site
npx quartz build --serve
```

Open `http://localhost:8080` to browse the rendered wiki.

## Workflow

### After Wiki Changes

Any time the wiki grows -- after `/wiki-ingest`, `/wiki-file`, or manual edits -- run the sync to update the site:

```bash
bash scripts/wiki-sync.sh
```

### Automated Sync

The Wiki Curator agent runs every 30 minutes and processes new files. You can chain wiki-sync after it by adding a post-heartbeat hook, or just run it manually when you want the site updated.

## What Gets Synced

The script syncs these wiki subdirectories:

| Directory | Content |
|---|---|
| `patterns/` | Reusable engineering patterns |
| `platform/` | Platform-specific knowledge, API behavior |
| `decisions/` | Architectural decisions with rationale |
| `clients/` | Per-client knowledge and architecture |
| `people/` | Team members, roles, ownership |
| `apps/` | Per-app knowledge |

The `raw/` directory is never synced (it contains unprocessed intake files).

## Related

- [Obsidian](obsidian.md) -- edit the wiki locally with Obsidian
- [Wiki Curator](paperclip.md#wiki-curator) -- the agent that keeps the wiki healthy
- [Three Knowledge Systems](../how-it-works/three-systems.md) -- where the wiki fits

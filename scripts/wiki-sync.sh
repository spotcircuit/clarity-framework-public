#!/bin/bash
# wiki-sync.sh — Sync wiki/ to the Quartz site repo and trigger deploy
#
# Usage: bash scripts/wiki-sync.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WIKI_SRC="$ROOT/wiki"
QUARTZ_REPO="/home/spotcircuit/clarity-wiki-site"
QUARTZ_CONTENT="$QUARTZ_REPO/content"

log() { echo "[wiki-sync] $*"; }

if [ ! -d "$QUARTZ_REPO" ]; then
  log "ERROR: Quartz repo not found at $QUARTZ_REPO"
  exit 1
fi

# Sync wiki content to Quartz
log "Syncing wiki/ to Quartz content/..."
rm -rf "$QUARTZ_CONTENT"/*

# Copy index
cp "$WIKI_SRC/index.md" "$QUARTZ_CONTENT/index.md"

# Copy all subdirectories
for dir in patterns platform decisions clients people apps; do
  if [ -d "$WIKI_SRC/$dir" ]; then
    mkdir -p "$QUARTZ_CONTENT/$dir"
    cp "$WIKI_SRC/$dir"/*.md "$QUARTZ_CONTENT/$dir/" 2>/dev/null || true
  fi
done

page_count=$(find "$QUARTZ_CONTENT" -name "*.md" | wc -l)
log "Copied $page_count pages."

# Commit and push
cd "$QUARTZ_REPO"
git add -A
if git diff --cached --quiet; then
  log "No changes to deploy."
else
  git commit -m "Wiki sync: $(date +%Y-%m-%d) ($page_count pages)"
  git push origin main
  log "Pushed to GitHub. Deploy will start automatically."
  log "Site: https://spotcircuit.github.io/clarity-wiki-site/"
fi

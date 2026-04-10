#!/bin/bash
# sync-obsidian.sh -- Keeps WSL and Windows Obsidian vault in sync
#
# Usage:
#   bash scripts/sync-obsidian.sh        # one-time sync
#   bash scripts/sync-obsidian.sh watch   # continuous watch mode (every 5s)
#
# Syncs bidirectionally -- whichever side has newer files wins.

WSL_PATH="/home/spotcircuit/clarity"
WIN_PATH="/mnt/c/clarity"
EXCLUDE="--exclude node_modules --exclude .git --exclude '*.pyc' --exclude __pycache__"

sync_once() {
  # WSL -> Windows (newer files win)
  rsync -av --update --delete \
    --exclude node_modules \
    --exclude .git \
    --exclude '*.pyc' \
    --exclude __pycache__ \
    --exclude '.claude/projects' \
    "$WSL_PATH/wiki/" "$WIN_PATH/wiki/"

  rsync -av --update --delete \
    --exclude node_modules \
    --exclude .git \
    "$WSL_PATH/raw/" "$WIN_PATH/raw/" 2>/dev/null

  rsync -av --update \
    --exclude node_modules \
    --exclude .git \
    "$WSL_PATH/.obsidian/" "$WIN_PATH/.obsidian/"

  rsync -av --update \
    "$WSL_PATH/CLAUDE.md" "$WIN_PATH/CLAUDE.md" 2>/dev/null

  rsync -av --update \
    "$WSL_PATH/README.md" "$WIN_PATH/README.md" 2>/dev/null

  # Windows -> WSL (pick up Obsidian edits and web clips)
  rsync -av --update \
    "$WIN_PATH/wiki/" "$WSL_PATH/wiki/"

  rsync -av --update \
    "$WIN_PATH/raw/" "$WSL_PATH/raw/" 2>/dev/null

  echo "[$(date '+%H:%M:%S')] Synced"
}

if [ "$1" = "watch" ]; then
  echo "Watching for changes (Ctrl+C to stop)..."
  while true; do
    sync_once 2>/dev/null
    sleep 5
  done
else
  sync_once
fi

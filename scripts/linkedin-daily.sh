#!/bin/bash
# linkedin-daily.sh — Daily LinkedIn posting pipeline
#
# Called by Paperclip LinkedIn Agent heartbeat.
# Flow: pick topic → generate draft → humanize → save → post
#
# Usage: bash scripts/linkedin-daily.sh [--dry-run]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/system/.venv/bin/python3"
DRAFTS="$ROOT/system/drafts"
TODAY=$(date +%Y-%m-%d)
DRY_RUN="${1:-}"

mkdir -p "$DRAFTS"

log() { echo "[linkedin-daily] $*"; }

# --- Step 1: Pick a topic (rotate through templates + custom) ---

# Check what was posted recently
recent=$(ls "$DRAFTS"/linkedin-*.md 2>/dev/null | tail -5 | xargs -I{} basename {} | grep -o 'services\|clarity\|casestudy' || echo "")

# Rotate: services → clarity → casestudy → repeat
if echo "$recent" | tail -1 | grep -q "casestudy"; then
  TOPIC="services"
elif echo "$recent" | tail -1 | grep -q "services"; then
  TOPIC="clarity"
else
  TOPIC="casestudy"
fi

log "Today's topic: $TOPIC"

# --- Step 2: Generate draft ---

DRAFT_FILE="$DRAFTS/linkedin-${TODAY}-${TOPIC}.md"

log "Generating draft..."
$VENV "$ROOT/scripts/linkedin-post.py" --generate "$TOPIC" --draft > "$DRAFT_FILE"

# Strip the draft header/footer markers
sed -i '/^====/d; /^DRAFT/d; /^Characters:/d' "$DRAFT_FILE"

log "Draft saved: $DRAFT_FILE"

# --- Step 3: Humanize ---

if [ "$DRY_RUN" != "--dry-run" ]; then
  log "Humanizing..."
  HUMANIZED=$(python3 "$ROOT/scripts/humanize.py" --file "$DRAFT_FILE" 2>&1) || true

  if [ -n "$HUMANIZED" ] && ! echo "$HUMANIZED" | grep -q "ERROR:"; then
    echo "$HUMANIZED" > "$DRAFT_FILE"
    log "Humanized and saved."
  else
    log "WARNING: Humanize failed or returned empty. Using original draft."
    log "  $HUMANIZED"
  fi
else
  log "Skipping humanize (dry-run)."
fi

# --- Step 4: Post (or dry-run) ---

if [ "$DRY_RUN" = "--dry-run" ]; then
  log "DRY RUN — not posting. Draft at: $DRAFT_FILE"
  echo ""
  cat "$DRAFT_FILE"
else
  log "Posting to LinkedIn..."
  $VENV "$ROOT/scripts/linkedin-post.py" --file "$DRAFT_FILE"
  log "Done! Posted: $TOPIC"

  # --- Step 5: File to wiki ---
  log "Filing to wiki..."
  WIKI_FILE="$ROOT/wiki/clients/linkedin-post-${TODAY}.md"
  mkdir -p "$ROOT/wiki/clients"
  cat > "$WIKI_FILE" << WIKI
# LinkedIn Post: ${TODAY} — ${TOPIC}

#linkedin #content #${TOPIC} #spotcircuit

Posted to LinkedIn on ${TODAY}. Topic: ${TOPIC}.

## Post Content

$(cat "$DRAFT_FILE")

## Related

- [[site-builder-overview]]
- [[ai-content-pipeline]]

---
Source: system/drafts/linkedin-${TODAY}-${TOPIC}.md | Filed: ${TODAY}
WIKI

  # Update index if not already there
  if ! grep -q "linkedin-post-${TODAY}" "$ROOT/wiki/index.md" 2>/dev/null; then
    sed -i "/^## Platform/i - [[linkedin-post-${TODAY}]] -- LinkedIn post: ${TOPIC} (${TODAY})" "$ROOT/wiki/index.md"
  fi

  # Append to log
  echo "| ${TODAY} | linkedin-daily.sh | linkedin-post-${TODAY}.md | 1 created | 0 updated |" >> "$ROOT/wiki/log.md"

  log "Wiki page created: wiki/clients/linkedin-post-${TODAY}.md"
fi

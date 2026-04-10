#!/bin/bash
# social-daily.sh — Daily social media pipeline (LinkedIn + Facebook)
#
# Called by Paperclip Social Media Agent heartbeat.
# Flow: pick topic → generate draft → humanize → generate image → post LinkedIn → post Facebook → wiki
#
# Usage: bash scripts/social-daily.sh [--dry-run] [--linkedin-only] [--facebook-only]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/system/.venv/bin/python3"
DRAFTS="$ROOT/system/drafts"
TODAY=$(date +%Y-%m-%d)
DRY_RUN=""
LINKEDIN=true
FACEBOOK=true

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    --linkedin-only) FACEBOOK=false ;;
    --facebook-only) LINKEDIN=false ;;
  esac
done

mkdir -p "$DRAFTS"
log() { echo "[social-daily] $*"; }

# --- Step 1: Pick topic ---
recent=$(ls "$DRAFTS"/linkedin-*.md 2>/dev/null | tail -5 | xargs -I{} basename {} | grep -o 'services\|clarity\|casestudy' || echo "")
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
sed -i '/^====/d; /^DRAFT/d; /^Characters:/d' "$DRAFT_FILE"

# --- Step 3: Humanize ---
if [ -z "$DRY_RUN" ]; then
  log "Humanizing..."
  HUMANIZED=$(python3 "$ROOT/scripts/humanize.py" --file "$DRAFT_FILE" 2>&1) || true
  if [ -n "$HUMANIZED" ] && ! echo "$HUMANIZED" | grep -q "ERROR:"; then
    echo "$HUMANIZED" > "$DRAFT_FILE"
    log "Humanized."
  else
    log "WARNING: Humanize failed. Using original."
  fi
fi

# --- Step 4: Generate image ---
IMAGE_FILE="$DRAFTS/linkedin-image-${TOPIC}.png"
if [ ! -f "$IMAGE_FILE" ]; then
  log "Generating image..."
  $VENV "$ROOT/scripts/linkedin-image.py" --topic "$TOPIC" --style card 2>/dev/null || log "Image generation failed — posting without"
fi

# --- Step 5: Post to LinkedIn ---
if [ "$LINKEDIN" = true ]; then
  if [ -z "$DRY_RUN" ]; then
    log "Posting to LinkedIn..."
    if [ -f "$IMAGE_FILE" ]; then
      $VENV "$ROOT/scripts/linkedin-post.py" --file "$DRAFT_FILE" --image "$IMAGE_FILE" && log "LinkedIn: posted with image" || log "LinkedIn: posted without image"
    else
      $VENV "$ROOT/scripts/linkedin-post.py" --file "$DRAFT_FILE" && log "LinkedIn: posted"
    fi
  else
    log "LinkedIn: DRY RUN"
    cat "$DRAFT_FILE"
  fi
fi

# --- Step 6: Post to Facebook ---
if [ "$FACEBOOK" = true ]; then
  if [ -z "$DRY_RUN" ]; then
    log "Posting to Facebook..."
    # Use image URL for Facebook (URL preview trick)
    IMAGE_URL="https://spotcircuit.github.io/clarity-wiki-site/static/linkedin-image-${TOPIC}.png"
    $VENV "$ROOT/scripts/facebook-post.py" --file "$DRAFT_FILE" --image "$IMAGE_URL" && log "Facebook: posted" || log "Facebook: failed (Chrome debug port may not be running)"
  else
    log "Facebook: DRY RUN"
  fi
fi

# --- Step 7: File to wiki ---
if [ -z "$DRY_RUN" ]; then
  log "Filing to wiki..."
  WIKI_FILE="$ROOT/wiki/clients/social-post-${TODAY}.md"
  mkdir -p "$ROOT/wiki/clients"
  cat > "$WIKI_FILE" << WIKI
# Social Post: ${TODAY} — ${TOPIC}

#social #content #${TOPIC} #spotcircuit

Posted to LinkedIn and Facebook on ${TODAY}. Topic: ${TOPIC}.

## Post Content

$(cat "$DRAFT_FILE")

## Related

- [[spotcircuit-services]]
- [[clarity-framework]]

---
Source: system/drafts/linkedin-${TODAY}-${TOPIC}.md | Filed: ${TODAY}
WIKI

  if ! grep -q "social-post-${TODAY}" "$ROOT/wiki/index.md" 2>/dev/null; then
    sed -i "/^## Platform/i - [[social-post-${TODAY}]] -- Social post: ${TOPIC} (${TODAY})" "$ROOT/wiki/index.md"
  fi
  echo "| ${TODAY} | social-daily.sh | social-post-${TODAY}.md | 1 created | 0 updated |" >> "$ROOT/wiki/log.md"
  log "Wiki page: wiki/clients/social-post-${TODAY}.md"
fi

log "Done!"

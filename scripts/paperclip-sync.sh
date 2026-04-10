#!/bin/bash
# paperclip-sync.sh -- Sync agent definitions from system/paperclip.yaml to Paperclip API
#
# Usage:
#   bash scripts/paperclip-sync.sh              # sync all agents
#   bash scripts/paperclip-sync.sh agents       # sync agents only
#   bash scripts/paperclip-sync.sh status       # check Paperclip status + list agents
#   bash scripts/paperclip-sync.sh heartbeat <agent-key>  # trigger a heartbeat
#   bash scripts/paperclip-sync.sh issue <title> [assignee-key]  # create an issue
#
# Requires: curl, python3 (for YAML parsing), jq

set -euo pipefail

CLARITY_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$CLARITY_ROOT/system/paperclip.yaml"
ID_CACHE="$CLARITY_ROOT/system/.paperclip-ids.json"
API_BASE="http://127.0.0.1:3100"
COMPANY_ID="d7dfb458-5fbc-4afd-8b9e-f765d253726f"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log() { echo "[paperclip-sync] $*"; }
err() { echo "[paperclip-sync] ERROR: $*" >&2; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { err "Required command not found: $1"; exit 1; }
}

require_cmd curl
require_cmd python3
require_cmd jq

# Parse a value from paperclip.yaml using Python
yaml_get() {
  local query="$1"
  python3 -c "
import yaml, sys
with open('$CONFIG') as f:
    data = yaml.safe_load(f)
# Navigate dotted path
obj = data
for key in '$query'.split('.'):
    if isinstance(obj, dict):
        obj = obj.get(key)
    else:
        obj = None
        break
if obj is not None:
    print(obj)
else:
    sys.exit(1)
" 2>/dev/null
}

# Get all agent keys from paperclip.yaml
yaml_agent_keys() {
  python3 -c "
import yaml
with open('$CONFIG') as f:
    data = yaml.safe_load(f)
for key in data.get('agents', {}):
    print(key)
"
}

# Get agent field
yaml_agent_field() {
  local agent_key="$1" field="$2"
  python3 -c "
import yaml, json, sys
with open('$CONFIG') as f:
    data = yaml.safe_load(f)
agent = data.get('agents', {}).get('$agent_key', {})
val = agent.get('$field')
if val is not None:
    print(val)
else:
    sys.exit(1)
" 2>/dev/null
}

# Read/write ID cache
cache_get() {
  local key="$1"
  if [ -f "$ID_CACHE" ]; then
    jq -r ".\"$key\" // empty" "$ID_CACHE" 2>/dev/null
  fi
}

cache_set() {
  local key="$1" value="$2"
  if [ -f "$ID_CACHE" ]; then
    jq --arg k "$key" --arg v "$value" '.[$k] = $v' "$ID_CACHE" > "${ID_CACHE}.tmp" \
      && mv "${ID_CACHE}.tmp" "$ID_CACHE"
  else
    echo "{\"$key\": \"$value\"}" > "$ID_CACHE"
  fi
}

# Check if Paperclip is running, start if not
ensure_paperclip() {
  if curl -sf "$API_BASE/api/health" >/dev/null 2>&1; then
    return 0
  fi

  log "Paperclip not responding. Attempting to start..."

  # Start Paperclip via npx
  log "Running: npx paperclipai run (background)..."
  nohup npx paperclipai run > /tmp/paperclip.log 2>&1 &
  sleep 5

  # Verify
  local retries=5
  while [ $retries -gt 0 ]; do
    if curl -sf "$API_BASE/api/health" >/dev/null 2>&1; then
      log "Paperclip is running."
      return 0
    fi
    retries=$((retries - 1))
    sleep 2
  done

  err "Could not start Paperclip at $API_BASE"
  err "Start it manually and re-run this script."
  exit 1
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

cmd_status() {
  log "Checking Paperclip at $API_BASE ..."

  if ! curl -sf "$API_BASE/api/health" >/dev/null 2>&1; then
    err "Paperclip is not running at $API_BASE"
    exit 1
  fi
  log "Paperclip is running."

  log ""
  log "Registered agents:"
  local response
  response=$(curl -sf "$API_BASE/api/companies/$COMPANY_ID/agents" 2>/dev/null || echo "[]")
  echo "$response" | jq -r '.[] | "  - \(.name) (id: \(.id), role: \(.role // "n/a"))"' 2>/dev/null || echo "  (none or error parsing response)"

  log ""
  log "Local agent definitions:"
  for key in $(yaml_agent_keys); do
    local name
    name=$(yaml_agent_field "$key" "name" || echo "$key")
    local cached_id
    cached_id=$(cache_get "agent:$key")
    if [ -n "$cached_id" ]; then
      echo "  - $name ($key) -> synced as $cached_id"
    else
      echo "  - $name ($key) -> not yet synced"
    fi
  done
}

cmd_sync_agents() {
  ensure_paperclip

  log "Syncing agent definitions to Paperclip..."

  for key in $(yaml_agent_keys); do
    local name description role
    name=$(yaml_agent_field "$key" "name")
    description=$(yaml_agent_field "$key" "description" || echo "")
    role=$(yaml_agent_field "$key" "role" || echo "general")

    local existing_id
    existing_id=$(cache_get "agent:$key")

    if [ -n "$existing_id" ]; then
      # Check if agent still exists in Paperclip
      local check
      check=$(curl -s "$API_BASE/api/agents/$existing_id" 2>/dev/null || echo "")
      if [ -n "$check" ]; then
        log "  Agent '$name' already registered (id: $existing_id). Skipping."
        continue
      fi
    fi

    # Create agent
    log "  Creating agent '$name'..."
    local response
    local budget
    budget=$(yaml_agent_field "$key" "budget_cents" 2>/dev/null || echo "500")

    response=$(curl -s -X POST \
      "$API_BASE/api/companies/$COMPANY_ID/agents" \
      -H "Content-Type: application/json" \
      -d "$(jq -n \
        --arg name "$name" \
        --arg caps "$description" \
        --arg role "$role" \
        --argjson budget "$budget" \
        '{name: $name, capabilities: $caps, role: $role, adapterType: "claude_local", adapterConfig: {}, budgetMonthlyCents: $budget}'
      )" 2>&1) || {
        err "  Failed to create agent '$name': $response"
        continue
      }

    local agent_id
    agent_id=$(echo "$response" | jq -r '.id // empty' 2>/dev/null)
    if [ -n "$agent_id" ]; then
      cache_set "agent:$key" "$agent_id"
      log "  Created '$name' with id: $agent_id"
    else
      err "  Unexpected response for '$name': $response"
    fi
  done

  log "Sync complete."
}

cmd_heartbeat() {
  local agent_key="${1:-}"
  if [ -z "$agent_key" ]; then
    err "Usage: paperclip-sync.sh heartbeat <agent-key>"
    err "Agent keys: $(yaml_agent_keys | tr '\n' ' ')"
    exit 1
  fi

  ensure_paperclip

  local agent_id
  agent_id=$(cache_get "agent:$agent_key")
  if [ -z "$agent_id" ]; then
    err "Agent '$agent_key' not synced yet. Run: bash scripts/paperclip-sync.sh agents"
    exit 1
  fi

  log "Triggering heartbeat for '$agent_key' (id: $agent_id)..."
  local response
  response=$(curl -sf -X POST \
    "$API_BASE/api/agents/$agent_id/heartbeat/invoke" \
    -H "Content-Type: application/json" \
    -d '{}' 2>&1) || {
      err "Heartbeat failed: $response"
      exit 1
    }

  log "Heartbeat triggered. Response:"
  echo "$response" | jq . 2>/dev/null || echo "$response"
}

cmd_issue() {
  local title="${1:-}"
  local assignee_key="${2:-}"

  if [ -z "$title" ]; then
    err "Usage: paperclip-sync.sh issue <title> [assignee-key]"
    exit 1
  fi

  ensure_paperclip

  local body="{}"
  local assignee_id=""

  if [ -n "$assignee_key" ]; then
    assignee_id=$(cache_get "agent:$assignee_key")
    if [ -z "$assignee_id" ]; then
      err "Agent '$assignee_key' not synced. Run sync first."
      exit 1
    fi
  fi

  body=$(jq -n \
    --arg title "$title" \
    --arg desc "Created by Clarity CLI" \
    --arg status "backlog" \
    --arg priority "medium" \
    --arg assignee "$assignee_id" \
    '{
      title: $title,
      description: $desc,
      status: $status,
      priority: $priority
    } + (if $assignee != "" then {assigneeAgentId: $assignee} else {} end)'
  )

  log "Creating issue: $title"
  local response
  response=$(curl -sf -X POST \
    "$API_BASE/api/companies/$COMPANY_ID/issues" \
    -H "Content-Type: application/json" \
    -d "$body" 2>&1) || {
      err "Failed to create issue: $response"
      exit 1
    }

  local issue_id
  issue_id=$(echo "$response" | jq -r '.id // empty' 2>/dev/null)
  if [ -n "$issue_id" ]; then
    log "Created issue: $issue_id"
    echo "$response" | jq . 2>/dev/null || echo "$response"
  else
    err "Unexpected response: $response"
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

case "${1:-agents}" in
  status)
    cmd_status
    ;;
  agents)
    cmd_sync_agents
    ;;
  heartbeat)
    cmd_heartbeat "${2:-}"
    ;;
  issue)
    cmd_issue "${2:-}" "${3:-}"
    ;;
  *)
    echo "Usage: paperclip-sync.sh {agents|status|heartbeat <key>|issue <title> [assignee]}"
    exit 1
    ;;
esac

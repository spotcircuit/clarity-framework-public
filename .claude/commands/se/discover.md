---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
description: Auto-generate a Phase 0 discovery document and seed the expertise file for a platform client
argument-hint: <client-name>
---

# SE: Discover

Auto-generate a Phase 0 discovery document and seed `expertise.yaml` for a client engagement.
Pulls from every available source: Jira, Slack, live tenant, codebase. Marks anything
it cannot derive as `<!-- TODO -->` for the engineer to fill in.

## Variables

CLIENT: $ARGUMENTS

## Resolution

Resolve CLIENT to a base directory. Check `clients/CLIENT` first, then `apps/CLIENT`:
- If `clients/CLIENT/` exists → BASE_DIR = `clients/CLIENT`
- Else if `apps/CLIENT/` exists → BASE_DIR = `apps/CLIENT`
- Else if CLIENT is empty: scan both `clients/` and `apps/` (excluding `_templates`). List all and ask.

CLIENT_DIR: BASE_DIR
CONFIG: BASE_DIR/client.yaml
PHASE0: BASE_DIR/phase-0-discovery.md
EXPERTISE: BASE_DIR/expertise.yaml
TEMPLATE_PHASE0: clients/_templates/phase-0-discovery.md
TEMPLATE_EXPERTISE: clients/_templates/expertise.yaml

## Instructions

- If CLIENT is empty: list both `ls clients/` and `ls apps/` (excluding `_templates`) and ask which one.
- This command is NON-DESTRUCTIVE on existing files — if phase-0 or expertise already exist, run in UPDATE mode (merge, don't overwrite).
- Mark every field you cannot derive with `<!-- TODO: Ask {appropriate party} -->`.
- All tenant queries are READ-ONLY regardless of client.yaml access setting -- never write records.
- If a data source is unavailable (no token, no MCP connection), skip it gracefully and note it in the Source Intelligence section.
- Do NOT use Flowcraft MCP tools (list_tenants, switch_tenant, etc.) -- use curl/API calls directly against the tenant URLs from client.yaml. Flowcraft is a separate tool for flow editing and is not part of the discover workflow.
- Use `ctxl` CLI or direct curl calls for all tenant queries. If ctxl is not configured for this tenant, fall back to curl with the bearer token from .env.

---

## Step 1: Verify Client Config

```bash
ls clients/CLIENT/ 2>/dev/null || echo "NOT FOUND"
```

If NOT FOUND: create `clients/CLIENT/` directory, then stop and tell the user:
> `clients/CLIENT/client.yaml` does not exist. Copy `clients/_templates/client.yaml` to `clients/CLIENT/client.yaml` and fill in your Jira project keys, Slack channel, and tenant details.

If found, read `clients/CLIENT/client.yaml` and extract:
- `jira.project_keys` — list of Jira project keys
- `slack.channel` + `slack.channels` — Slack channels to read
- `tenant.dev.id`, `tenant.dev.url`, `tenant.dev.bearer_token`, `tenant.dev.access`
- `codebase.path` — if present

---

## Step 2: Jira Intelligence

For each project key in `jira.project_keys`:

**2a. Pull project metadata and active tickets:**
Use Jira MCP to query:
- Project name, description, lead
- Active sprint tickets (status != Done, sorted by priority)
- Recent closed tickets (last 14 days) — captures recent decisions
- Team members (assignees across active tickets)
- Any tickets tagged as bugs or blockers

**2b. Extract from Jira:**
- What the solution does (from epic descriptions or project description)
- Active bugs and their assignees
- Open questions (tickets in "Needs Info" or "Blocked" status)
- Team structure (who owns what)

If Jira MCP unavailable: note `<!-- TODO: Pull Jira data — project keys: {keys} -->` in the output.

---

## Step 3: Slack Intelligence

For each channel in `slack.channel` + `slack.channels`:

Read the last 14 days of messages. Extract:
- Decisions made (look for: "we decided", "going with", "confirmed", "agreed")
- Open questions (look for: "?", "anyone know", "waiting on", "need to clarify")
- Escalations or blockers (look for: "stuck", "blocked", "urgent", "escalate")
- Client contacts mentioned by name
- Any known bugs or incidents discussed

If Slack MCP unavailable: note `<!-- TODO: Review #channel-name for recent context -->`.

---

## Step 4: Tenant Intelligence

Tenant intelligence comes from three sources. All are READ-ONLY.
If bearer token is not set, skip gracefully and mark all fields TODO.

**Token guide:**
- Registry bearer token (`${CLIENT_DEV_TOKEN}`) — audience `https://platform/no-api` — used for records list/get
- Management token (`${CLIENT_MGT_TOKEN}`) — audience `https://platform/api` — required for listing object types and flows
- If management token is missing, type listing will be skipped (403) — note in Source Intelligence and continue

Resolve tokens from the env var references stored in `client.yaml`:

```bash
BEARER_VAR=$(python3 -c "
import yaml, sys
c = yaml.safe_load(open('clients/CLIENT/client.yaml'))
print(c.get('tenant', {}).get('dev', {}).get('bearer_token', ''))
")
BEARER=$(eval echo $BEARER_VAR)

MGT_VAR=$(python3 -c "
import yaml, sys
c = yaml.safe_load(open('clients/CLIENT/client.yaml'))
print(c.get('tenant', {}).get('dev', {}).get('management_token', ''))
")
MGT=$(eval echo $MGT_VAR)

NO_URL=$(python3 -c "
import yaml, sys
c = yaml.safe_load(open('clients/CLIENT/client.yaml'))
print(c.get('tenant', {}).get('dev', {}).get('native_object_url', ''))
")
REG_URL=$(python3 -c "
import yaml, sys
c = yaml.safe_load(open('clients/CLIENT/client.yaml'))
print(c.get('tenant', {}).get('dev', {}).get('registry_url', ''))
")
TENANT_ID=$(python3 -c "
import yaml, sys
c = yaml.safe_load(open('clients/CLIENT/client.yaml'))
print(c.get('tenant', {}).get('dev', {}).get('id', ''))
")

# Management API base URL — all management endpoints go through this proxy
MGT_BASE="https://api.prod-001.prod.platform.io"
```

---

### 4a: Object Types

**Primary — ctxl CLI (uses registry bearer token):**

```bash
PLATFORM_BEARER_TOKEN=$BEARER \
  npx --yes @platform-io/cli@latest --tenant-url $NO_URL \
  types list 2>/dev/null
```

**Fallback — management proxy with management token (if ctxl unavailable):**

```bash
curl -s -H "Authorization: Bearer $MGT" -H "X-Org-Id: $TENANT_ID" \
  "$MGT_BASE/p/native-object-registry/types" 2>/dev/null
```

If both return errors or empty: note "0 object types — blank tenant or management token missing" in Source Intelligence and continue. Do NOT block on this.

From this output extract:
- Total count of object types
- Full list of type names
- Descriptions where available (infer purpose from name if not)
- **Record counts** per type (use `?pageSize=1&includeTotal=true` to get totals without pulling data)
- **Multi-tenant patterns** — look for prefixed type copies (e.g., `purchase-order` + `value-heating-cooling-inc-purchase-order`). If found, document the white-label pattern: what's the template, what's client-specific, what's the prefix token.
- **Triggers on each type** — check `triggers.postInsert`, `triggers.postUpdate` to map the event chain
- **Sample records** — pull 1-2 records from high-volume types to understand actual data shapes (field population, state distribution)

```bash
# 2. For each of the 10 most important types (prioritise by Jira/Slack context):
#    Get records grouped by status to find stuck records and backlogs
PLATFORM_BEARER_TOKEN=$BEARER \
  npx --yes @platform-io/cli@latest --tenant-url $NO_URL \
  records list --type "{type-name}" --limit 100 2>/dev/null | \
  python3 -c "
import json, sys, collections
records = json.load(sys.stdin).get('records', [])
counts = collections.Counter(r.get('status') or r.get('fields', {}).get('status') for r in records)
print(json.dumps(dict(counts), indent=2))
"
```

Populate `platform_state.record_counts` and flag any type with records in
unexpected terminal states as `platform_state.stuck_records`.

---

### 4b: Native Object API — Schema per Key Type

For each key type identified in 4a, fetch the full schema to populate `data_model.key_types`:

```bash
# Get full type definition (field definitions, status values) via management proxy
curl -s -H "Authorization: Bearer $MGT" -H "X-Org-Id: $TENANT_ID" \
  "$MGT_BASE/p/native-object-registry/types/{type-name}" | jq '.'
```

Extract per type:
- All field names and types
- Valid status values (the `enum` on the status field)
- Required vs optional fields
- Any field marked as the "status" field

Populate `data_model.key_types[].statuses` and `data_model.key_types[].fields` from this.

---

### 4c: Management API — Flows, Agents, Connections

The management API reveals what's actually deployed and running on the tenant.
All endpoints require the management token (`$MGT`) and the `X-Org-Id` header.

```bash
# List active flows
curl -s -H "Authorization: Bearer $MGT" -H "X-Org-Id: $TENANT_ID" \
  "$MGT_BASE/p/native-object/flow" | jq '[.[] | {name: .name, status: .status}]'

# List deployed agents
curl -s -H "Authorization: Bearer $MGT" -H "X-Org-Id: $TENANT_ID" \
  "$MGT_BASE/p/native-object/agent" | jq '[.[] | {name: .name, image: .image, status: .status}]'

# List connections (API configurations)
curl -s -H "Authorization: Bearer $MGT" -H "X-Org-Id: $TENANT_ID" \
  "$MGT_BASE/p/native-object/api-configuration" | jq '[.[] | {name: .name, type: .type, status: .status}]'
```

Populate:
- `platform_state.flows` — names, count, deployment status
- `platform_state.agents` — names, image versions, running status
- `platform_state.connections` — names, types (azure-blob, smtp, external-api, etc.), status

**Note on agents:** Image versions matter — if an agent is on an outdated image it may
behave differently from current documentation. Flag version mismatches as observations.

---

### 4d: Stuck Record Deep Dive

For any type where stuck records were found in 4a, fetch a sample to understand the failure:

```bash
PLATFORM_BEARER_TOKEN=$BEARER \
  npx --yes @platform-io/cli@latest --tenant-url $NO_URL \
  records list --type "{type-name}" \
  --filter.status "{stuck-status}" --limit 3 2>/dev/null
```

Extract from sample records:
- What fields are empty that shouldn't be
- What the last updated timestamp is (how long stuck)
- Any error or message fields

Add findings to `data_model.key_types[].known_edge_cases` and `unvalidated_observations`.

---

If bearer token not set or API unavailable:
```
<!-- TODO: Tenant scan skipped — set tokens in clients/{client}/client.yaml
     native_object_url: https://native-object.{tenant}.my.platform.io/api/v1
     bearer_token: ${CLIENT_DEV_TOKEN}
     management_token: ${CLIENT_MGT_TOKEN}  (browser JWT — needed for flows, agents, connections, types)
-->
```

---

## Step 4e: Flow Intelligence (Deep Dive)

For each flow found in 4c, fetch the node list to understand what the flow actually does:

```bash
curl -s -H "Authorization: Bearer $MGT" -H "X-Org-Id: $TENANT_ID" \
  "$MGT_BASE/p/native-object/flow/{flow-id}" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for n in d.get('node_red_data', {}).get('flows', []):
    t = n.get('type', '')
    if t in ('tab', 'comment', 'group', 'native-object-config'): continue
    print(f'  {t:25s} | {n.get(\"name\", \"\")[:50]}')
"
```

This reveals:
- What node types are used (AI nodes, HTTP requests, native object CRUD, loops)
- External system calls (http-request nodes with URLs)
- AI integration points (ai-generate, ai-tool nodes)
- The processing pipeline structure

## Step 4f: Service & Connection Architecture

For each service, check what it bundles:

```bash
curl -s -H "Authorization: Bearer $MGT" -H "X-Org-Id: $TENANT_ID" \
  "$MGT_BASE/p/services/services/{service-id}" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Service:', d.get('id'), 'v' + str(d.get('version', '?')))
"
```

For connections, identify the integration pattern:
- Per-client connections (OAuth per customer) vs shared connections (API keys)
- Which connections are authorization-code-grant (require user OAuth flow)
- Which are client-grant or bearer (can be automated)

---

## Step 5: Codebase Intelligence

If `codebase.path` is set in client.yaml and the path exists:

```bash
find {codebase.path} -type f | grep -v node_modules | grep -v .git | head -60
```

Read:
- `README.md` — if present
- `package.json` or `requirements.txt` — stack detection
- Entry point (`index.ts`, `main.py`, `App.vue`, etc.)

Extract: frontend stack, auth pattern, key routes/pages, API endpoint patterns.

---

## Step 6: Generate Phase 0 Document

Copy `clients/_templates/phase-0-discovery.md` as the base.

Fill in every field you can derive from Steps 2-5. For every field you cannot fill:
- Use `<!-- TODO: Ask {appropriate party} — {what specifically is needed} -->`
- "appropriate party" = client, project lead, Jira ticket owner, or "team to confirm"

**Required fills from data sources:**
- Client name, Project Lead, Date → from client.yaml + current date
- Problem definition → from Jira epic/project description + Slack context
- Trigger → from Jira tickets + Slack discussions
- Human roles → from Jira assignees + Slack mentions
- Volume/latency → from Jira + Slack if discussed, otherwise TODO
- Object types table → from tenant scan (Step 4)
- Active flows → from tenant scan
- Active connections → from tenant scan
- Open questions → from Jira blocked tickets + Slack open questions
- Known issues → from Jira bugs

Add a **Source Intelligence** section at the top of the generated doc:

```markdown
## Source Intelligence

*Auto-generated by Clarity /se:discover on {date}*

| Source | Status | Data Points Extracted |
|---|---|---|
| Jira | ✅ Connected / ❌ Unavailable | {N tickets, N team members} |
| Slack | ✅ Connected / ❌ Unavailable | {N messages scanned, N decisions found} |
| Tenant (dev) | ✅ Connected / ❌ Unavailable | {N object types, N flows} |
| Codebase | ✅ Found / ❌ Not configured | {stack summary} |

**Fields auto-filled:** {N}
**Fields requiring SE input (TODO):** {N}
```

Write the completed doc to `clients/CLIENT/phase-0-discovery.md`.

---

## Step 7: Seed expertise.yaml

Copy `clients/_templates/expertise.yaml` as the base (or read existing if present).

Populate from discovered data:

```yaml
meta:
  client: CLIENT
  display_name: {from client.yaml or Jira}
  phase: 0
  last_updated: {today}
  project_lead: {from client.yaml or prompt SE}

solution:
  description: {from Jira + Slack — or ~ if not found}
  trigger: {from Jira + Slack — or ~ if not found}
  end_state: ~   # TODO — requires SE + client confirmation
  latency_expectation: {from Jira/Slack if discussed — or ~}

platform_state:
  tenant: {tenant.dev.id}
  last_scan: {today}
  object_types: {count from Step 4}
  active_flows: {count from Step 4}
  connections: [{list from Step 4}]
  record_counts: {from Step 4 queries}

data_model:
  key_types: [{names from Step 4 with statuses if discoverable}]

known_issues: [{from Jira bugs found in Step 2}]

team: [{from Jira assignees in Step 2}]

compliance:
  last_checked: {today}
  phase_0_complete: false
  gaps: [{list of TODO fields from Phase 0 doc}]

unvalidated_observations:
  - "Initial discover run — {N} object types, {N} flows found on {tenant} ({today})"
  - {any notable patterns found during discovery}
```

Write to `clients/CLIENT/expertise.yaml`.
Validate: `python3 -c "import yaml; yaml.safe_load(open('clients/CLIENT/expertise.yaml'))"`

---

## Step 8: Report

```
✅ Clarity Discover: CLIENT

Sources Queried:
  Jira:    ✅ {N projects, N tickets} / ❌ unavailable
  Slack:   ✅ {N channels, N messages} / ❌ unavailable
  Tenant:  ✅ {N object types, N flows} / ❌ unavailable
  Code:    ✅ {stack} / ❌ not configured

Phase 0 Document: clients/CLIENT/phase-0-discovery.md
  Fields auto-filled:       {N}
  Fields requiring SE input: {N}

Expertise File: clients/CLIENT/expertise.yaml
  Solution: {filled / TODO}
  Platform state: {N object types, N flows}
  Known issues: {N from Jira}
  Team members: {N from Jira}

Next Steps:
  1. Open clients/CLIENT/phase-0-discovery.md and fill in TODO fields
  2. Share with client to confirm trigger, end state, and volume expectations
  3. Run /se:check CLIENT when Phase 0 is complete
  4. Run /se:self-improve CLIENT after your first investigation session
```

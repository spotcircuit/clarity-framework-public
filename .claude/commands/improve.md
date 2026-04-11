---
allowed-tools: Read, Write, Edit, Bash
description: Validate unvalidated observations and integrate confirmed facts into a client's expertise.yaml
argument-hint: <client-name>
---

# SE: Self-Improve

Validates `unvalidated_observations:` in a client's expertise.yaml against current live state
(Jira, Slack, tenant) and integrates confirmed facts into the main expertise sections.
Discards stale or already-captured observations. Enforces the 1000-line cap.

## Variables

CLIENT: $ARGUMENTS

## Resolution

Resolve CLIENT to a base directory. Check `BASE_DIR` first, then `apps/CLIENT`:
- If `BASE_DIR/expertise.yaml` exists → BASE_DIR = `BASE_DIR`
- Else if `apps/CLIENT/expertise.yaml` exists → BASE_DIR = `apps/CLIENT`
- Else if CLIENT is empty: scan both `clients/*/expertise.yaml` and `apps/*/expertise.yaml` (excluding `_templates`). If exactly one match, use it. Otherwise list all and ask.

EXPERTISE: BASE_DIR/expertise.yaml

## Instructions

- Read `BASE_DIR/expertise.yaml` — stop if it doesn't exist (run `/discover` first)
- This command ONLY modifies expertise.yaml — never touches phase-0-discovery.md
- Be conservative: only promote an observation if it's clearly confirmed by current live data
- When in doubt, leave it in unvalidated_observations with a note

---

## Step 1: Read Current State

Read `BASE_DIR/expertise.yaml` in full.
Read `BASE_DIR/client.yaml` for data source access.

Extract all entries from `unvalidated_observations:`.
If empty: report "No unvalidated observations to process" and exit.

---

## Step 2: Validate Each Observation

For each observation in `unvalidated_observations:`, check against live sources:

**Against Jira:**
- If observation references a ticket (e.g., "AJS-301"): fetch current ticket status
- If observation says something was fixed/resolved: confirm ticket is closed
- If observation names a team member: confirm they're still assigned

**Against Slack:**
- If observation references a decision or conclusion: search for corroboration
- If observation says something was escalated or resolved: check recent channel history

**Against Tenant (if available):**
- If observation references a record count or stuck state: query current count
- If observation identifies a root cause: check if the stuck records still exist

**Classification for each observation:**
- ✅ CONFIRMED — integrate into main expertise section, remove from unvalidated
- ❌ STALE — no longer true (ticket closed, records cleared), discard
- ⚠️ UNVERIFIABLE — cannot check right now, leave in unvalidated with date + note
- 🔄 ALREADY CAPTURED — already in main expertise, discard duplicate

**Platform-level check:** For each observation (regardless of classification), ask: "Would an SE on a completely different client find this useful?" If yes, append `(platform-level)` to the observation text. Examples:
- Platform API behavior (query syntax, endpoint gotchas, env vars) = platform-level
- Reusable flow patterns (error handling, idempotency, logging) = platform-level
- Client-specific bugs, field mappings, team decisions = NOT platform-level
These tagged observations are candidates for `/contribute` to the SE knowledge base repo.

---

## Step 3: Integrate Confirmed Observations

For each CONFIRMED observation, add it to the correct expertise section:
- Bug/incident → `known_issues:`
- Root cause → update relevant `known_issues:` entry or `data_model.known_edge_cases:`
- Team/ownership → `team:` or `implementation_patterns.exception_owner:`
- Pattern → `implementation_patterns:`
- Volume/status → `platform_state.record_counts:`
- Scope/decision → `solution.in_scope:` or `solution.out_of_scope:`

---

## Step 4: Enforce 1000-Line Cap

```bash
wc -l BASE_DIR/expertise.yaml
```

If over 1000 lines:
- Compress `known_issues:` — merge resolved issues into a one-line summary
- Compress `platform_state.record_counts` — keep only types with non-zero counts
- Compress `unvalidated_observations` — remove duplicates, summarize related observations
- Never compress: `solution`, `data_model`, `implementation_patterns`, `team`

---

## Step 5: Validate and Write

Write updated expertise.yaml.
Validate: `python3 -c "import yaml; yaml.safe_load(open('BASE_DIR/expertise.yaml'))"`

---

## Step 6: Report

```
✅ Self-Improve: CLIENT

Observations processed: {N}
  ✅ Confirmed + integrated: {N}
  ❌ Stale + discarded:     {N}
  ⚠️  Left unverified:       {N}
  🔄 Duplicate + discarded:  {N}

expertise.yaml: {N lines / 1000}

Integrated into:
  - known_issues: {what was added}
  - implementation_patterns: {what was added}
  - platform_state: {what was updated}
```

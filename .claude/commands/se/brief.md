---
allowed-tools: Read
description: Generate a standup/handoff summary from a client's expertise.yaml
argument-hint: <client-name>
---

# SE: Brief

Generates a one-page summary of a client engagement — suitable for standup, handoff,
or onboarding a new SE. Reads entirely from expertise.yaml (no live queries).

## Variables

CLIENT: $ARGUMENTS

## Resolution

Resolve CLIENT to a base directory. Check `clients/CLIENT` first, then `apps/CLIENT`:
- If `BASE_DIR/expertise.yaml` exists → BASE_DIR = `clients/CLIENT`
- Else if `apps/CLIENT/expertise.yaml` exists → BASE_DIR = `apps/CLIENT`
- Else if CLIENT is empty: scan both `clients/*/expertise.yaml` and `apps/*/expertise.yaml` (excluding `_templates`). If exactly one match, use it. Otherwise list all and ask.

EXPERTISE: BASE_DIR/expertise.yaml

## Instructions

- Read `BASE_DIR/expertise.yaml` — stop if it doesn't exist
- This is READ ONLY — no files are modified
- Keep output concise and human-readable — this is for people, not agents
- If a section is empty or ~, say "not yet documented" rather than showing the raw YAML

---

## Step 1: Read expertise.yaml

Read `BASE_DIR/expertise.yaml` in full.

---

## Step 2: Generate Brief

Output the following summary to the terminal:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLARITY BRIEF: {display_name} ({client})
Generated: {today} | Project Phase: {phase}/9 | Project Lead: {project_lead}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT THIS SOLUTION DOES
{solution.description}

Trigger:  {solution.trigger}
End state: {solution.end_state}
Latency:  {solution.latency_expectation}

PLATFORM STATE (as of {platform_state.last_scan})
Tenant: {platform_state.tenant}
  {platform_state.object_types} object types | {platform_state.active_flows} active flows
  Connections: {platform_state.connections}

  Notable record counts:
  {for each type in platform_state.record_counts with non-zero counts:}
    {type}: {status breakdown}

ACTIVE ISSUES ({count} open)
{for each in known_issues where status != resolved:}
  [{jira}] {title}
    Root cause: {root_cause}
    Workaround: {workaround}

TEAM
{for each in team:}
  {name} — {role} ({slack})

EXCEPTION OWNER: {implementation_patterns.exception_owner}

PHASE 0 COMPLIANCE
{compliance.phase_0_complete ? "✅ Complete" : "⚠️ Incomplete"}
{if gaps:}
  Open gaps:
  {for each gap:}
    - {gap}

SCOPE BOUNDARIES
  In scope:
  {for each in solution.in_scope:} - {item}

  Out of scope:
  {for each in solution.out_of_scope:} - {item}

PENDING OBSERVATIONS
{count of unvalidated_observations} observations queued for /se:self-improve

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next: /se:check CLIENT | /se:self-improve CLIENT | /se:update CLIENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

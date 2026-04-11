---
allowed-tools: Read, Edit, Bash
description: SE Design & Build Guidelines compliance check against a client's Phase 0 document
argument-hint: <client-name>
---

# SE: Check

Validates a client's `phase-0-discovery.md` against the SE Design & Build Guidelines Phase 0
requirements. Reports what's compliant, what's incomplete, and what's missing entirely.
Updates `compliance:` section in expertise.yaml with results.

## Variables

CLIENT: $ARGUMENTS
GUIDELINES: se-guidelines/design-and-build.md

## Resolution

Resolve CLIENT to a base directory. Check `BASE_DIR` first, then `apps/CLIENT`:
- If `BASE_DIR/expertise.yaml` exists → BASE_DIR = `BASE_DIR`
- Else if `apps/CLIENT/expertise.yaml` exists → BASE_DIR = `apps/CLIENT`
- Else if CLIENT is empty: scan both `clients/*/expertise.yaml` and `apps/*/expertise.yaml` (excluding `_templates`). If exactly one match, use it. Otherwise list all and ask.

PHASE0: BASE_DIR/phase-0-discovery.md
EXPERTISE: BASE_DIR/expertise.yaml

## Instructions

- Read `BASE_DIR/phase-0-discovery.md` — stop if it doesn't exist (run `/discover` first)
- Count `<!-- TODO` markers as incomplete fields
- Be specific about WHAT is missing, not just THAT it's missing
- This command writes a sign-off block to the bottom of `phase-0-discovery.md` after every run (pass or fail), replacing any previous sign-off block

---

## Step 1: Read Documents

Read `BASE_DIR/phase-0-discovery.md` in full.
Read `se-guidelines/design-and-build.md` sections §0.1, §0.2, §0.3.

---

## Step 2: Run Compliance Checks

Evaluate each requirement. Score: ✅ Complete | ⚠️ Incomplete | ❌ Missing

### Phase 0.1 — Problem Definition

| Check | Criterion | Status |
|---|---|---|
| Solution description | Written as one clear paragraph, not a list of features | |
| Trigger defined | Specific event + system + payload described (not just "webhook") | |
| End state defined | Named record type + specific fields + terminal status | |
| Human roles | At least Initiates and Owns Exceptions are named people/roles | |
| Compliance addressed | PII, data residency, audit trail explicitly considered (even if N/A) | |

### Phase 0.2 — Data Inventory

| Check | Criterion | Status |
|---|---|---|
| Input types documented | Not just clean examples — edge cases and old formats asked for | |
| Volume documented | Numbers given, not "TBD" — average/day AND peak/day | |
| Latency expectation set | Real-time / 10-min window / batch — with justification | |
| Downstream systems | At least one system listed WITH expected schema/format | |

### Phase 0.3 — Scope Boundaries

| Check | Criterion | Status |
|---|---|---|
| Out of scope written | At least one explicit item (not blank) | |
| Exception ownership | Named owner + SLA + escalation path | |
| Reversibility addressed | Can a processed record be unprocessed? Answer documented. | |

### Platform Snapshot

| Check | Criterion | Status |
|---|---|---|
| Object types listed | At least key types identified | |
| Flows listed | Active flows or "none yet" explicitly stated | |
| Open questions tracked | At least one entry (or explicit "none") | |

---

## Step 3: Count TODO Markers

```bash
grep -c "TODO" BASE_DIR/phase-0-discovery.md 2>/dev/null || echo "0"
```

Each TODO = a field the SE still needs to fill in with the client.

---

## Step 4: Update expertise.yaml

If `BASE_DIR/expertise.yaml` exists, update the `compliance:` section:

```yaml
compliance:
  last_checked: {today}
  phase_0_complete: {true if all checks pass}
  gaps:
    - {list of ⚠️ Incomplete and ❌ Missing items}
```

Also append to `unvalidated_observations:`:
```yaml
  - "Phase 0 compliance check: {N}/{total} checks passing, {N} TODOs remaining ({today})"
```

---

## Step 4.5: Write Sign-off Block to phase-0-discovery.md

Remove any existing `<!-- phase-0-signoff -->` block from the bottom of `phase-0-discovery.md`,
then append the following (replacing `{...}` with actual values):

**If all checks pass (0 gaps, 0 TODOs):**

```markdown
<!-- phase-0-signoff -->
---

## Phase 0 Sign-off

✅ Passed `/check` on {today} — {N}/{total} checks passing, 0 TODO markers remaining.

**Signed off by:** {se_lead from expertise.yaml}
**Ready for:** Phase 1 — Data Model & Schema Design
```

**If gaps or TODOs remain:**

```markdown
<!-- phase-0-signoff -->
---

## Phase 0 Sign-off

⚠️ Incomplete as of {today} — {N}/{total} checks passing, {TODO_count} TODO markers remaining.

**Gaps to resolve before Phase 1:**
- {gap 1}
- {gap 2}

**Signed off by:** {se_lead from expertise.yaml}
```

This block is always replaced on re-run — it reflects the most recent check result.

---

## Step 5: Report

```
📋 Phase 0 Compliance: CLIENT

Phase 0.1 — Problem Definition
  ✅ / ⚠️ / ❌  Solution description
  ✅ / ⚠️ / ❌  Trigger defined
  ✅ / ⚠️ / ❌  End state defined
  ✅ / ⚠️ / ❌  Human roles
  ✅ / ⚠️ / ❌  Compliance addressed

Phase 0.2 — Data Inventory
  ✅ / ⚠️ / ❌  Input types
  ✅ / ⚠️ / ❌  Volume
  ✅ / ⚠️ / ❌  Latency expectation
  ✅ / ⚠️ / ❌  Downstream systems

Phase 0.3 — Scope Boundaries
  ✅ / ⚠️ / ❌  Out of scope written
  ✅ / ⚠️ / ❌  Exception ownership
  ✅ / ⚠️ / ❌  Reversibility addressed

Platform Snapshot
  ✅ / ⚠️ / ❌  Object types
  ✅ / ⚠️ / ❌  Flows
  ✅ / ⚠️ / ❌  Open questions

Summary: {N}/{total} checks passing | {N} TODO markers remaining

{if gaps exist}
⚠️  Not ready for Phase 1. Address these before starting build:
  - {specific gap 1}
  - {specific gap 2}

{if all pass}
✅  Phase 0 complete. Ready for Phase 1 — Data Model & Schema Design.
   Run /brief CLIENT to generate a handoff summary.
```

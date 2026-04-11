---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate
description: Fix a bug in an existing app — investigation-first, minimal change, verified resolution
argument-hint: <app-name> <symptom description>
---

# App: Bug

Fix a bug in an existing app. Unlike a feature workflow, bug fixing is investigation-first: reproduce the symptom, locate the faulty code, make the minimal change that resolves it — nothing more. Self-learn fires at the end to capture the bug pattern.

## Variables

ARGUMENTS: $ARGUMENTS
APP_NAME: first word of ARGUMENTS
BUG_REPORT: everything after the first word of ARGUMENTS
EXPERTISE_FILE: .claude/commands/apps/APP_NAME/expertise.yaml

## Instructions

- IMPORTANT: Parse ARGUMENTS immediately: APP_NAME = first whitespace-delimited token; BUG_REPORT = remainder. If either is empty, stop and ask.
- Verify `apps/APP_NAME/` exists before proceeding
- **Minimal change principle**: touch only the code that is wrong. Do not refactor surrounding code, do not improve unrelated logic, do not add features while fixing a bug.
- No scouts, no parallel build — bugs are local by definition
- If the symptom cannot be understood from BUG_REPORT alone, ask the user for more detail before investigating
- Load domain expertise (database, websocket) only if the bug description clearly implicates that domain
- If `apps/APP_NAME/.forge/client.yaml` exists, execute the **Client Config Preamble** from `client_config_protocol.md` before any other steps — creates the feature branch + worktree, enforces readonly tenant mode if configured.

## Workflow

### Step 1: Verify App Exists
```bash
ls apps/APP_NAME/ || echo "NOT FOUND"
```
If NOT FOUND: stop and tell user to run `/new APP_NAME <description>` first.

### Step 2: Load Context
1. Read `EXPERTISE_FILE` — understand app architecture and key files
2. Identify which code paths are implicated by BUG_REPORT
3. Read only those files — do not load unrelated modules

### Step 3: Reproduce and Locate
- Understand the exact symptom and trigger conditions from BUG_REPORT
- Trace the code path involved: grep for relevant route paths, function names, error messages
- Read the specific files in the failure path
- Identify the exact line(s) responsible
- State clearly before proceeding: "The bug is at [file:line] because [reason]"

If you cannot identify the fault location after reasonable investigation, report what you found and ask the user for additional reproduction steps.

### Step 4: Fix
- Make the minimal change that corrects the behavior
- Touch nothing outside the fault location unless strictly required for correctness
- Do not refactor, improve, or clean up surrounding code
- Add a brief inline comment if the fix is non-obvious

### Step 5: Test
Run `/test APP_NAME` to confirm the fix and check for regressions.

If `test_commands` is missing from EXPERTISE_FILE: skip automated tests and proceed with manual verification only.

**Manual verification** (always do this):
- Trace through the fix to confirm the specific symptom from BUG_REPORT is resolved
- Confirm no adjacent behavior is broken by the change

State: "The fix resolves [symptom] by [how]. Adjacent behavior [is/is not] affected because [reason]."

### Step 6: Self-Learn
Open `EXPERTISE_FILE` and append to `unvalidated_observations:` (create the key if absent):
```yaml
unvalidated_observations:
  - "[DATE] BUG: [short description] — root cause: [what was wrong], fix: [what changed at file:line]"
```

### Step 7: Finalize Client Workflow
If `apps/APP_NAME/.forge/client.yaml` exists and `git.workflow: feature_branch`, execute the **Client Config Postamble** from `client_config_protocol.md`: commit fix, push branch, create PR to configured reviewer, clean up worktree.

## Report

```
Bug Fixed: APP_NAME

Symptom: BUG_REPORT
Root Cause: [what was wrong and why]
Location: [file:line]

Fix Applied:
- [what changed]

Test Results:
- [N passed / N failed / SKIPPED if no test_commands]

Verification:
- Symptom resolved: Yes
- Adjacent behavior affected: No / [describe if yes]

Observation appended to expertise.yaml
```

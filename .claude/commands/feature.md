---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TaskCreate, Task, Skill
description: Expertise-informed feature workflow for an existing app — plan, build, and self-learn
argument-hint: <app-name> <feature-request>
---

# App: Feature

Add a feature to an existing app using the full expertise-informed workflow: load context, plan, build, then update the self-learn loop (passive + active). This is the standard development cycle for any work on an existing app.

## Variables

ARGUMENTS: $ARGUMENTS
APP_NAME: first word of ARGUMENTS
FEATURE_REQUEST: everything after the first word of ARGUMENTS
EXPERTISE_DIR: .claude/commands/apps/APP_NAME
APP_DIR: apps/APP_NAME
USE_SCOUTS: false
USE_PARALLEL_BUILD: false

## Instructions

- IMPORTANT: Parse ARGUMENTS immediately: APP_NAME = first whitespace-delimited token; FEATURE_REQUEST = remainder of the string after that token. If either is empty after parsing, stop and ask for both.
- Before doing anything, verify `apps/APP_NAME/` exists — if not, direct user to `/new APP_NAME` first
- If `apps/APP_NAME/.forge/client.yaml` exists, execute the **Client Config Preamble** from `client_config_protocol.md` before any other steps — creates the feature branch + worktree, enforces readonly tenant mode if configured.
- Load ALL relevant expertise before planning — this is what makes plans domain-aware
- Detect which domains the feature touches: database, websocket, or app-specific
- For complex features (multi-file, new endpoints, schema changes), set USE_SCOUTS=true
- For large features (5+ files to create/modify), set USE_PARALLEL_BUILD=true
- HYBRID SELF-LEARN fires automatically at the end — do not skip either layer

## Workflow

### Step 1: Verify App Exists
```bash
ls apps/APP_NAME/ || echo "NOT FOUND"
```
If NOT FOUND: stop and tell user to run `/new APP_NAME <description>` first.

### Step 2: Detect Domains and Load Context

**Step 2a: Domain detection (keyword scan — no file reads yet)**
Scan FEATURE_REQUEST for these keywords to determine which expertise to load:
- DB domain: `database`, `sql`, `table`, `migration`, `query`, `model`, `schema`, `postgres`, `asyncpg`, `row`, `column`
- WS domain: `websocket`, `ws`, `realtime`, `real-time`, `broadcast`, `event`, `live`, `socket`, `stream`

Set:
- `LOAD_DB_EXPERTISE=true` if any DB keyword matched
- `LOAD_WS_EXPERTISE=true` if any WS keyword matched

**Step 2b: Load expertise selectively**
1. Read `EXPERTISE_DIR/expertise.yaml` — always load (app mental model)
2. If LOAD_DB_EXPERTISE: grep `.claude/commands/apps/database/expertise.yaml` for sections relevant to FEATURE_REQUEST (e.g., grep for table names, model names, or operation types mentioned). Read only matched sections — do not load the full file unless the feature is broadly database-related.
3. If LOAD_WS_EXPERTISE: grep `.claude/commands/apps/websocket/expertise.yaml` for sections relevant to FEATURE_REQUEST. Read only matched sections.
4. Read `apps/APP_NAME/README.md` if it exists
5. Scan the backend entry point and `apps/APP_NAME/frontend/src/App.vue` for current state:
   - TypeScript apps: try `apps/APP_NAME/backend/src/index.ts` (Hono/Express)
   - Python apps: try `apps/APP_NAME/backend/main.py` (FastAPI)
   - Use `key_files.backend.entry.path` from expertise.yaml if present — it is always correct

**Step 2c: Set build flags**
Count app files: `find apps/APP_NAME -type f | wc -l` → APP_FILE_COUNT

Set USE_SCOUTS=true ONLY IF:
- Feature is complex (new endpoints, schema migrations, multi-component changes) AND
- APP_FILE_COUNT > 50

Set USE_PARALLEL_BUILD=true if 5+ files need creating.

### Step 3: Plan (Expertise-Informed)
The expertise loaded in Step 2 is now in context. Run planning:

If USE_SCOUTS is false:
  Run `/plan "FEATURE_REQUEST"`

If USE_SCOUTS is true:
  Run `/plan "FEATURE_REQUEST" use_scouts=true`

Note the path to the generated plan file.

### Step 4: Build
If USE_PARALLEL_BUILD is false:
  Run `/build <plan-path>`

If USE_PARALLEL_BUILD is true:
  Run `/build_in_parallel <plan-path>`

Note all files changed.

### Step 5: Test
Run `/test APP_NAME` to execute the test suite for what was just built.

If `test_commands` is missing from EXPERTISE_DIR/expertise.yaml:
- Note: "No test_commands configured — skipping automated tests. Add test infrastructure with `/feature APP_NAME 'add test infrastructure'`"
- Continue to Step 6

If tests fail:
- For each failing test, run `/resolve_failed_test APP_NAME <failure_json>` (up to 4 retries per test; stop if 0 resolved in an iteration)
- If still failing after retry exhaustion: document failures in report, continue to Step 6

### Step 6: Test E2E (if configured)

**Step 6a: Audit E2E spec coverage for new features**
Before running, check whether the feature added new frontend views or public API endpoints. For each new view/endpoint, verify a corresponding spec exists in `apps/APP_NAME/e2e/`:
```bash
ls apps/APP_NAME/e2e/
```
If a new view or endpoint has no E2E spec: create one at `apps/APP_NAME/e2e/test_<feature_name>.md` covering the critical user flows. Also add the test function to `agents/e2e/APP_NAME/run_tests.py` (the Python playwright runner).

**Step 6b: Run E2E suite**
Check if `apps/APP_NAME/e2e/` exists. If not: note "No E2E specs configured — skipping browser tests".

If E2E specs exist:
  Run `/test_e2e APP_NAME` — uses playwright-python runner at `agents/e2e/APP_NAME/run_tests.py`
  For each failure: run `/resolve_failed_e2e_test APP_NAME <failure_json>` (up to 2 retries)

### Step 7: Review
Run `/review APP_NAME diff` to check the changed files for correctness, security, and pattern compliance.

If CRITICAL findings exist:
- Create a bug task for each: `/bug APP_NAME "<critical finding description>"`
- Fix all CRITICAL issues before marking feature complete
- Re-run `/test APP_NAME` after fixes

### Step 8: Hybrid Self-Learn

#### 8a. Passive Layer (append observations)
For each expertise file touched by this feature (app-specific + any domain expertise):
- Open the expertise.yaml
- Add raw observations under `unvalidated_observations:` (create the key if absent):
  ```yaml
  unvalidated_observations:
    - "[DATE] <observation about what was built, patterns noticed, gotchas>"
    - "[DATE] <another observation>"
  ```
- Max 5 observations per build run
- NEVER restructure the expertise — append only

#### 8b. Active Layer (validate and promote)
For each domain touched by the feature, run:
  `/improve <domain> true`

The `true` flag triggers git diff check — focuses validation on what just changed.
This processes any unvalidated_observations from 7a before running codebase validation.

### Step 9: Finalize Client Workflow
If `apps/APP_NAME/.forge/client.yaml` exists and `git.workflow: feature_branch`, execute the **Client Config Postamble** from `client_config_protocol.md`: commit all changes, push branch, create PR to configured reviewer, clean up worktree.

## Report

```
✅ Feature Complete: FEATURE_REQUEST
App: APP_NAME

Steps: Plan → Build → Unit Test → E2E Test → Review → Self-Learn

Plan: [path to plan file]
Files Changed: [git diff --stat summary]

Domains Touched: [list]

Unit Tests:
- Backend: [N passed / N failed / skipped]
- Frontend: [N passed / N failed / skipped]
- Status: PASS / FAIL / SKIPPED (no test_commands)

E2E Tests:
- Specs: [N passed / N failed / SKIPPED (no e2e_specs)]
- Retries used: [N]

Review: [APPROVED / APPROVED WITH WARNINGS / BLOCKED]
- Critical: [N]  Warnings: [N]  Notes: [N]
- Report: [path to review report]

Self-Learn:
- Passive observations added: [count] in [expertise files]
- Active self-improve: [domains validated]
- Expertise updated: Yes/No
- Final line counts: [domain: N/1000]
```

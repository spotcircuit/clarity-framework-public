---
allowed-tools: Read, Bash, Grep, Glob, Edit, Write, TaskCreate
description: Run tests for an app, report failures, optionally fix and retry
argument-hint: <app-name> [backend|frontend|all] [fix=true|false]
---

# Test

Run the test suite for an app. Parse results, report failures with exact locations, and optionally attempt to fix failures before reporting.

## Variables

ARGUMENTS: $ARGUMENTS
APP_NAME: first word of ARGUMENTS
FOCUS: second word of ARGUMENTS (default "all" — "backend", "frontend", or "all")
FIX_FAILURES: third word or "fix=true" flag (default false)
EXPERTISE_FILE: .claude/commands/apps/APP_NAME/expertise.yaml
MAX_FIX_RETRIES: 4

## Instructions

- IMPORTANT: Parse APP_NAME from first token of ARGUMENTS. If empty, ask.
- Read expertise.yaml to find `test_commands` — do NOT guess test commands
- If `test_commands` is absent from expertise: report that test infrastructure is not configured, stop, tell user to run `/feature APP_NAME "add test infrastructure"` first
- Run tests with full output capture — do not suppress stderr
- Parse results into structured format: passed, failed, skipped, duration
- If FIX_FAILURES=true and failures exist: attempt targeted fixes (see Step 4)
- Always produce a structured Test Report at the end

## Workflow

### Step 1: Load Test Configuration
Read EXPERTISE_FILE. Find the `test_commands` section:
```yaml
test_commands:
  backend: "cd apps/APP_NAME/backend && bun test"
  frontend: "cd apps/APP_NAME/frontend && bun run test"
  all: "<combined command>"
```

If not found: stop with message:
> "No test_commands found in expertise.yaml for APP_NAME. Add a `test_commands` section or run `/feature APP_NAME 'add test infrastructure'` to scaffold tests."

Determine which commands to run based on FOCUS (default: all).

### Step 2: Run Tests
Run the appropriate command(s) from test_commands. Capture full stdout + stderr.

For each test run, parse the output and extract:
- **Pass count** — tests that passed
- **Fail count** — tests that failed
- **Skip count** — tests that were skipped
- **Duration** — total run time
- **Failures** — for each failed test:
  - Test name / describe block
  - File path and line number
  - Expected vs actual (if assertion failure)
  - Error message (if exception)

### Step 3: Report Results (If All Pass)
If fail count = 0:
```
✅ Tests Passed: APP_NAME (FOCUS)
  Backend:  N passed, N skipped — Xs
  Frontend: N passed, N skipped — Xs
  Total:    N passed | 0 failed | N skipped
```
Stop here — no further action needed.

### Step 4: Handle Failures
If fail count > 0 and FIX_FAILURES=false:
Produce failure report (see Report section) and stop.

If fail count > 0 and FIX_FAILURES=true:
Attempt up to MAX_FIX_RETRIES fix cycles:

**Fix cycle:**
1. For each failed test, read the test file and the source file under test
2. Identify whether the failure is:
   - **Test is wrong** (wrong expectation, stale snapshot, API changed) → fix the test
   - **Implementation is wrong** (regression, logic error) → fix the source code
   - **Environment issue** (missing env var, port conflict) → report and stop
3. Apply the minimal fix
4. Re-run the failing tests only (not the full suite)
5. If all fixed: run full suite to confirm no regressions
6. If still failing after MAX_FIX_RETRIES: stop and report remaining failures

State before each fix: "Fixing [test name] — [test is wrong / regression] at [file:line] because [reason]"

### Step 5: Append Observation
If tests were run (pass or fail), open EXPERTISE_FILE and append to `unvalidated_observations:`:
```yaml
- "[DATE] TEST: APP_NAME (FOCUS) — N passed, N failed; [brief note about any failures or notable coverage gaps]"
```

## Report

```
Test Report: APP_NAME
Focus: FOCUS
─────────────────────────────────
Backend:   [N passed] [N failed] [N skipped] — [Xs]
Frontend:  [N passed] [N failed] [N skipped] — [Xs]
─────────────────────────────────
Total:     N passed | N failed | N skipped

[If failures:]
FAILURES:
  ✗ [test name]
    File: [path:line]
    Expected: [value]
    Actual:   [value]
    Error: [message]

[If fix attempted:]
FIX ATTEMPTS: N/MAX_FIX_RETRIES
  ✓ Fixed: [test name] — [what changed at file:line]
  ✗ Unresolved: [test name] — [why it couldn't be fixed automatically]

Status: PASS / FAIL / PARTIAL
```

## Machine Output

IMPORTANT: After the human-readable report above, ALWAYS output this JSON block. It is required for programmatic consumption by `forge_sdlc.py`. Output every test as an entry — both passing and failing.

```json
[
  {
    "test_name": "<describe block + test name, e.g. 'personas > POST /personas > creates a persona'>",
    "passed": true,
    "execution_command": "<exact command that ran this test suite, e.g. 'cd apps/prepitch/backend && bun test src/tests/'>",
    "test_purpose": "<one-line description of what this test validates>",
    "error": null
  },
  {
    "test_name": "<test name>",
    "passed": false,
    "execution_command": "<command>",
    "test_purpose": "<what it validates>",
    "error": "<full error message including expected vs actual>"
  }
]
```

Rules:
- Include ALL tests — not just failures
- `error` must be `null` (not `""`) for passing tests
- `test_name` must be unique across backend + frontend results — prefix with "backend:" or "frontend:" if names collide
- The JSON block must be the LAST thing output (after the human report) so `parse_json()` finds it cleanly

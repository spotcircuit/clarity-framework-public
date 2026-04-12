---
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
description: Run tests, analyze results, and self-improve expertise based on what the tests reveal
argument-hint: <app-name> [focus_area]
---

# Test-Learn: Run Tests → Analyze → Update Expertise

Runs the test suite for an app, analyzes results (passes, failures, coverage gaps), then updates expertise.yaml with what the tests revealed about the system.

This is the "test → learn → reuse" cycle. Different from /test (which just runs tests) and /improve (which validates observations). This command uses test results as a source of truth to discover undocumented behavior.

## Variables

APP: $1 (REQUIRED)
FOCUS_AREA: $2 (optional — focus the analysis on a specific area)

## Resolution

Resolve APP to a base directory:
- If `apps/APP/expertise.yaml` exists → APP_DIR = `apps/APP`
- If `clients/APP/expertise.yaml` exists → APP_DIR = `clients/APP`
- Else: list available and ask

EXPERTISE: APP_DIR/expertise.yaml

## Workflow

### Step 1: Read Expertise and Find Test Commands

Read EXPERTISE to understand:
- The stack (determines test runners: pytest, vitest, jest, playwright, etc.)
- Any documented test commands in the `testing:` section
- What's already known about the system

### Step 2: Run Tests

Execute the test commands found in expertise or auto-detect:
- Python: `pytest tests/ -v --tb=short`
- Node: `npm test` or `npx vitest run`
- E2E: `npx playwright test` (if servers are running)

Capture full output. Note:
- Total passed/failed/skipped per suite
- Any failures (test name, error, traceback)
- Duration

### Step 3: Analyze Test Results

From the results, identify:

1. **Coverage gaps** — What parts of the system have NO tests?
2. **Architecture insights** — What do passing tests reveal about how things work?
3. **Expertise gaps** — What should be in expertise.yaml but isn't?
   - Endpoints not documented
   - Features not captured
   - Patterns not recorded

### Step 4: Update Expertise

Read current EXPERTISE. Update with:
- Missing features discovered through tests
- Updated test counts and coverage
- Architecture patterns revealed by the test structure
- Any gotchas exposed by failures

Keep under 1000 lines. Validate YAML:
```bash
python3 -c "import yaml; yaml.safe_load(open('EXPERTISE'))"
```

### Step 5: Suggest New Tests

Based on the analysis, suggest 3-5 specific tests that would increase coverage for the most critical paths.

## Report

```
Test-Learn Cycle: APP

| Suite | Passed | Failed | Skipped | Duration |
|-------|--------|--------|---------|----------|
| ... | ... | ... | ... | ... |

Failures: [if any]
Coverage gaps: [list]
Expertise updates: [what was added/changed]
Suggested tests: [3-5 suggestions]
Lessons learned: [key insights]
```

---
allowed-tools: Read, Bash, Grep, Glob, Write, TaskCreate
description: Code review of recent changes — correctness, security, patterns, test coverage
argument-hint: <app-name> [scope: diff|all] [save=true|false]
---

# Review

Perform a structured code review on recent changes to an app. Reviews for correctness, security vulnerabilities, edge cases, pattern compliance, and test coverage. Produces a structured report with CRITICAL / WARNING / NOTE classifications.

## Variables

ARGUMENTS: $ARGUMENTS
APP_NAME: first word of ARGUMENTS
SCOPE: second word (default "diff" — "diff" reviews only changed files, "all" reviews full app)
SAVE_REPORT: "save=true" flag (default true — writes report to specs/)
EXPERTISE_FILE: .claude/commands/apps/APP_NAME/expertise.yaml
REPORT_PATH: specs/review_APP_NAME_DATE.md

## Instructions

- Always load expertise first — review must check compliance with established patterns
- For SCOPE=diff: get changed files with `git diff HEAD~1..HEAD --name-only 2>/dev/null || git diff --root HEAD --name-only` (fallback handles first commit)
- Review every changed file — do not skip any
- Classify findings strictly: CRITICAL = must fix before ship, WARNING = should fix, NOTE = suggestion
- A review with zero CRITICAL findings = APPROVED
- If CRITICAL findings exist: identify which entry flow should fix them (bug vs feature)
- Save report to REPORT_PATH by default

## Workflow

### Step 1: Load Context
1. Read EXPERTISE_FILE — understand expected patterns, best practices, known issues
2. Get changed files:
   - SCOPE=diff: `git diff HEAD~1..HEAD --name-only 2>/dev/null || git diff --root HEAD --name-only` (fallback handles first commit; also try `--staged` if working tree is clean)
   - SCOPE=all: `find apps/APP_NAME -type f -name "*.ts" -o -name "*.py" -o -name "*.vue"`
3. Read each changed file fully

### Step 2: Review Each File

For each file, check all applicable categories:

**Correctness**
- Does the logic implement what the surrounding code implies?
- Are return values and error cases handled?
- Are async operations properly awaited?
- Is data transformed/serialized correctly at API boundaries?

**Security**
- SQL injection: parameterized queries only — no string interpolation in queries
- Input validation: are user inputs validated before use?
- Auth bypass: are protected routes actually protected?
- Data exposure: does the response include fields that shouldn't be exposed?
- CORS: are allowed origins and methods appropriate?
- Dependency issues: any obvious CVE-vulnerable patterns?

**Edge Cases**
- Null/undefined handling on all optional fields
- Empty array/string handling
- Integer overflow / type coercion issues
- Concurrent request handling

**Pattern Compliance** (check against expertise.yaml)
- Are architecture patterns followed?
- Are best practices respected?
- Are known issues avoided?

**Test Coverage**
- Is the changed code covered by tests?
- Are new endpoints/functions tested?
- Are edge cases tested?

### Step 3: Classify Findings

For each finding assign a severity:

**CRITICAL** — Must fix before shipping:
- Security vulnerability (any category)
- Data loss risk
- Production crash path (unhandled exception that kills the server)
- Breaking change without migration
- Auth/permission bypass

**WARNING** — Should fix soon:
- Missing error handling on likely failure path
- Missing input validation on user-controlled data
- Pattern violation that will cause confusion
- Untested critical path
- Performance issue that will hit at scale

**NOTE** — Suggestions:
- Code clarity improvements
- Test coverage gaps on non-critical paths
- Minor pattern deviations
- Documentation gaps

### Step 4: Compile and Save Report

Compile findings into structured report. Save to REPORT_PATH if SAVE_REPORT=true.

### Step 5: Append Observation
Open EXPERTISE_FILE and append to `unvalidated_observations:`:
```yaml
- "[DATE] REVIEW: APP_NAME — N critical, N warnings, N notes; [key finding if any]"
```

## Report

```markdown
# Code Review: APP_NAME
Date: YYYY-MM-DD
Scope: SCOPE (N files reviewed)
Reviewer: Claude Code

## Summary
Status: ✅ APPROVED / ⚠️ APPROVED WITH WARNINGS / ❌ BLOCKED (N critical issues)

| Severity | Count |
|---|---|
| CRITICAL | N |
| WARNING  | N |
| NOTE     | N |

## Critical Issues (Must Fix)
### [File: path/to/file.ts:line]
**Issue:** [description]
**Risk:** [what can go wrong]
**Fix:** [specific change needed]

## Warnings (Should Fix)
### [File: path/to/file.ts:line]
**Issue:** [description]
**Suggestion:** [recommended change]

## Notes (Suggestions)
### [File: path/to/file.ts:line]
**Note:** [observation]

## What Looks Good
- [positive finding 1]
- [positive finding 2]

## Action Required
[If CRITICAL:]
Run: `/bug APP_NAME "<issue description>"` for each critical issue

[If APPROVED:]
No blocking issues. Proceed to document or ship.
```

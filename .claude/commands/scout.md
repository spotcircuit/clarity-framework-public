---
allowed-tools: Read, Glob, Grep, Bash
description: Read-only codebase investigation — analyzes issues, identifies root causes, suggests fixes with structured reports
argument-hint: <app-name> <question or issue>
---

# Scout: Codebase Investigation

Read-only analysis of a codebase. Does NOT modify any files. Investigates an issue, identifies root causes, and suggests fixes with a structured report.

## Variables

APP: first argument (app name)
QUESTION: remaining arguments (what to investigate)

## Resolution

Resolve APP to a directory:
- If `apps/APP/expertise.yaml` exists → APP_DIR = `apps/APP`
- If `clients/APP/expertise.yaml` exists → APP_DIR = `clients/APP`
- Else: list available apps/clients and ask

## Instructions

1. Read `APP_DIR/expertise.yaml` for context
2. Investigate the QUESTION using only read-only tools:
   - Grep for relevant code patterns
   - Glob for related files
   - Read source files to understand the flow
   - Run non-destructive bash commands (git log, git diff, test runs)
3. Do NOT edit, write, or delete any files
4. Produce a structured report

## Report Format

```
🔍 Scout Report: APP — QUESTION

## Summary
One paragraph: what was found.

## Root Cause
What is causing the issue and why.

## Evidence
- File: path/to/file.py:line — what it shows
- File: path/to/other.py:line — supporting evidence

## Suggested Fix
Step-by-step what should change (but do NOT make the changes).

## Risk Assessment
- Impact: high/medium/low
- Confidence: high/medium/low
- Files affected: list

## Observations
Append to expertise.yaml unvalidated_observations:
  - "Scout: {one-line finding} ({today})"
```

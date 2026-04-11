---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, MultiEdit, TaskCreate
description: Implement a plan file top-to-bottom, validate the work, then append passive expertise observations
argument-hint: <path-to-plan>
---

# Build

Implement the plan at PATH_TO_PLAN completely — top to bottom, no skipping steps. Validate the work at the end. Then append passive observations to relevant expertise files.

## Variables

PATH_TO_PLAN: $ARGUMENTS
MAX_FIX_ATTEMPTS: 3

## Instructions

- IMPORTANT: If PATH_TO_PLAN is not provided, STOP and ask for it.
- Read the plan fully before starting — understand the full scope before touching any file
- Implement every step in order. Do not stop between steps.
- Do not stop until validation commands have been run
- If validation fails, fix issues before stopping
- Make best-judgment decisions when the plan is ambiguous — everything critical should be in the plan
- After implementation: append raw observations to expertise files (passive learn layer)

## Workflow

### Step 1: Read and Understand the Plan
Read the plan at PATH_TO_PLAN. Understand:
- All files to create or modify
- The intended architecture and patterns
- The validation commands at the end

### Step 2: Implement
Execute every step in the plan, top to bottom:
- Follow the exact order specified
- Use existing codebase patterns (read similar files if needed for reference)
- Do not add unrequested features or abstractions
- Keep changes minimal and focused

### Step 3: Validate
Run the validation commands specified in the plan.
If validation fails: identify root cause, fix, re-validate.
Maximum fix attempts: MAX_FIX_ATTEMPTS (3). If validation still fails after 3 attempts: stop, report the failure with full error output and what was tried. Do not loop indefinitely.

### Step 4: Passive Expertise Update (Self-Learn Layer)
After successful implementation, identify which expertise.yamls were touched by this build.
For each relevant expertise file at `.claude/commands/apps/<domain>/expertise.yaml`:

**If no expertise file exists for a touched domain:** skip observation writing for that domain and note it in the report — do not create a new file or guess a path.

- Read the expertise file
- Add raw observations under `unvalidated_observations:` (create key if absent):
  ```yaml
  unvalidated_observations:
    - "[YYYY-MM-DD] <raw observation about what was built>"
    - "[YYYY-MM-DD] <pattern noticed, gotcha hit, or architectural insight>"
  ```
- Max 5 observations per build — prioritize the most surprising or non-obvious findings
- NEVER restructure the expertise file — append to unvalidated_observations only
- These will be validated and promoted by the next `/improve` run

## Report

Summarize completed work:
- Bullet points of what was implemented
- Files and total lines changed: `git diff --stat`
- Validation result: passed/fixed/outstanding
- Passive observations added: [count] across [N expertise files]

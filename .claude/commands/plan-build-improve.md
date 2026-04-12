---
allowed-tools: Read, Skill, TodoWrite, Grep, Glob, Bash, Agent, Edit, Write
description: Generic plan-build-improve workflow for any expert domain
argument-hint: <domain> <user_request>
---

# Purpose

Generic workflow that orchestrates a complete implementation cycle for **any** expert domain by chaining three steps: expertise-informed planning, building from the plan, and self-improving the expertise based on changes made.

Works with any domain that has an expertise file at `apps/{APP} or clients/{APP}/expertise.yaml`.

## Variables

APP: $1 (REQUIRED - e.g. "websocket", "database", "site-builder")
USER_REQUEST: $2 (REQUIRED - the feature/change to implement)
EXPERTISE_FILE: .claude/commands/apps/${APP}/expertise.yaml or clients/${APP}/expertise.yaml

## Instructions

- Execute steps 1-3 sequentially
- Each step depends on the previous step's output
- DO NOT STOP between steps - complete the entire workflow
- If APP is empty, list available domains: `ls .claude/commands/experts/`
- If the expertise file doesn't exist for the domain, error and stop

## Workflow

### Step 1: Create Plan (Expertise-Informed)

1. Read the EXPERTISE_FILE to load domain knowledge as mental model
2. Read critical implementation files documented in the expertise
3. Run `/plan ${USER_REQUEST}` — the loaded expertise context ensures the plan is domain-aware
4. Note the path to the generated plan file

### Step 2: Build from Plan

1. Run `/build <path_to_plan>` with the plan file from Step 1
2. Implement the entire plan
3. Note all files changed

### Step 3: Self-Improve Expertise

1. Run `/improve ${APP} true` to validate expertise against the changes just made
2. The git diff check (true) ensures newly changed files are prioritized
3. Note the self-improvement report

## Report

```
Plan-Build-Improve Complete: ${APP}

User Request: ${USER_REQUEST}
Steps Completed: 3/3

Step 1: Planning
- Plan file: [path]
- Key decisions: [summary]

Step 2: Build
- Files changed: [count]
- Summary: [what was built]

Step 3: Self-Improve
- Discrepancies found: [count]
- Expertise updated: Yes/No
- Line count: [N/1000]

Final Status: Complete
```

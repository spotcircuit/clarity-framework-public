---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, MultiEdit, Task
description: Creates a comprehensive implementation plan, saves it to specs/. Use use_scouts=true for complex features.
argument-hint: <user_prompt> [use_scouts (true/false)]
---

# Plan

Create a detailed implementation plan based on USER_PROMPT. Explore the codebase to understand existing patterns, then save a comprehensive spec to `specs/`. For complex features, deploy parallel scout subagents to map the codebase before planning.

## Variables

USER_PROMPT: $1
USE_SCOUTS: $2 (default false)
TOTAL_BASE_SCOUTS: 3
TOTAL_FAST_SCOUTS: 5
PLAN_OUTPUT_DIRECTORY: specs/

## Instructions

- IMPORTANT: If USER_PROMPT is empty, stop and ask the user to provide it.
- Determine task type (chore|feature|refactor|fix|enhancement) and complexity (simple|medium|complex)
- Scout gate: only consider scouts if complexity is "complex" AND the app has > 50 files (`find apps/ -type f | wc -l`). Scouts on a small app are pure waste.
- If USE_SCOUTS is true OR (complexity is "complex" AND file count > 50): deploy parallel scout subagents
- If USE_SCOUTS is false: explore the codebase directly (read key files, grep patterns)
- Generate a descriptive kebab-case filename based on the plan topic
- The plan must be detailed enough that another agent can implement it without additional context
- Include code examples or pseudo-code for complex concepts
- Consider edge cases, error handling, and scalability

## Workflow

### Step 1: Analyze Requirements
Parse USER_PROMPT to understand:
- Core problem and desired outcome
- Task type and complexity
- Which parts of the codebase are affected

### Step 2: Explore Codebase

**If USE_SCOUTS is false (simple/medium tasks):**
- Read relevant existing files directly
- Grep for key patterns, functions, and imports
- Understand existing architecture

**If USE_SCOUTS is true (complex tasks, file count > 50):**
Deploy TOTAL_BASE_SCOUTS + TOTAL_FAST_SCOUTS subagents IN PARALLEL:
- Give each agent a different area to explore (backend, frontend, tests, config, etc.)
- Each agent: read files, grep patterns, summarize findings
- Consolidate results and manually validate — look for missing files
- Use the consolidated map for Step 3

### Step 3: Design Solution
Develop technical approach:
- Architecture decisions
- Implementation strategy
- Files to create/modify
- Dependencies and risks

### Step 4: Document Plan
Structure the plan using this format:

```md
# Plan: <task name>

## Task Description
<describe the task in detail>

## Objective
<what will be accomplished when complete>

## Problem Statement (for features/complex tasks)
<the specific problem or opportunity>

## Solution Approach (for features/complex tasks)
<proposed solution and how it addresses the objective>

## Relevant Files
<list files with bullet points explaining why each matters>

### New Files (if any)
<list files to be created>

## Implementation Phases (for medium/complex tasks)
### Phase 1: Foundation
### Phase 2: Core Implementation
### Phase 3: Integration & Polish

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. <First Task Name>
- <specific action>

### 2. <Second Task Name>
- <specific action>

## Testing Strategy (for features/complex tasks)
<testing approach, unit tests, edge cases>

## Acceptance Criteria
<specific, measurable criteria for completion>

## Validation Commands
<exact commands to run to validate the work>

## Notes
<additional context, new libraries needed (use uv add), dependencies>
```

### Step 5: Generate Filename and Save
- Create a descriptive kebab-case filename with timestamp: `<topic>-<subtopic>-YYYYMMDD-HHmmss.md`
  - Example: `search-endpoint-price-filter-20260319-143022.md`
  - Timestamp prevents collisions when the same feature is planned multiple times
- Save to `PLAN_OUTPUT_DIRECTORY/<filename>.md`

## Report

```
✅ Implementation Plan Created

File: PLAN_OUTPUT_DIRECTORY/<filename>.md
Topic: <brief description>
Scouts used: Yes/No
Key Components:
- <component 1>
- <component 2>
- <component 3>
```

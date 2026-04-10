---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
description: File a wiki page from a good answer or synthesis in the current conversation
argument-hint: <topic> [category]
---

# SE: Wiki-File

Captures an insight from the current conversation as a permanent wiki page.
This is the compounding loop -- when something is figured out, it never has to be figured out again.

## Variables

ARGS: $ARGUMENTS
TOPIC: $ARGUMENTS (everything before the last word if last word is a known category, otherwise all of it)
CATEGORY: $ARGUMENTS (last word if it matches: platform, clients, patterns, decisions, people -- otherwise auto-detect)
WIKI_DIR: wiki/
TODAY: current date in YYYY-MM-DD format

---

## Step 1: Parse Arguments

Split ARGS:
- If the last word matches one of: `platform`, `clients`, `patterns`, `decisions`, `people` -- that is CATEGORY, the rest is TOPIC
- Otherwise -- TOPIC is all of ARGS, CATEGORY is "auto-detect"

Generate SLUG: lowercase TOPIC, replace spaces with hyphens, strip special chars.
Example: "Native Object Reserved Names" -> `native-object-reserved-names`

If TOPIC is empty, ask the user what topic to file. Do not proceed without a topic.

---

## Step 2: Auto-Detect Category (if not provided)

If CATEGORY is "auto-detect", classify TOPIC using these rules:

- **platform** -- anything about platform internals: node types, APIs, agent config, flow structure, deployment, service dependencies, triggers, schema behavior, env vars, auth
- **clients** -- anything scoped to a specific client: their flows, data model, team, integration quirks, business rules
- **patterns** -- reusable design or implementation patterns: error handling, polling loops, event chains, config-driven routing, idempotency, retry logic
- **decisions** -- choices made and why: architecture decisions, tradeoffs, things ruled out, lessons that changed behavior
- **people** -- individual people: contact info, expertise, org role, working style

If still ambiguous, default to **patterns**.

---

## Step 3: Check for Existing Page

Check if `wiki/CATEGORY/SLUG.md` already exists:

```bash
ls wiki/CATEGORY/SLUG.md 2>/dev/null && echo "EXISTS" || echo "NEW"
```

If EXISTS: this is an UPDATE -- append new findings, do not overwrite existing content.
If NEW: this is a CREATE.

---

## Step 4: Synthesize the Content

Read the recent conversation. Identify:
- What was the core question or problem?
- What was learned or decided?
- What is the actionable takeaway for an SE who hits this situation?
- What prompted this (a bug, a client call, a build failure)?

**Write the INSIGHT, not the transcript.**
- One focused concept per page
- No step-by-step conversation recap
- Concrete facts, not hedged summaries
- Include code snippets, config examples, or command patterns if they're the point

---

## Step 5: Write or Update the Page

### If NEW page:

Create `wiki/CATEGORY/SLUG.md` with this structure:

```markdown
# {Human-Readable Title}

#{tag1} #{tag2} #{tag3}

{2-4 sentence synthesis of the insight. What is it, why does it matter, what does an SE need to know?}

## Detail

{Deeper explanation, code examples, config snippets, gotchas, edge cases.
Be concrete. If there's a pattern, show the pattern. If there's a fix, show the fix.}

## Source

Conversation {TODAY} -- {one sentence on what prompted this: e.g., "debugging a CBP writeback failure", "Jeff direction call on entry types"}

## Related

- [[{related-slug}]] -- {why it connects}
- [[{related-slug}]] -- {why it connects}
```

Fill in 2-5 relevant tags from: `#platform`, `#native-object`, `#flow`, `#agent`, `#api`, `#pattern`, `#decision`, `#client`, `#bug`, `#workaround`, `#config`, `#deployment`, `#polling`, `#error-handling`, `#schema`, `#auth`, `#people`

### If EXISTING page:

Read the current file first. Then append at the bottom:

```markdown

---

## Update {TODAY}

{New findings that weren't in the original page. Only add what's genuinely new -- no duplication.}

Source: Conversation {TODAY} -- {what prompted the update}
```

---

## Step 6: Find Related Pages

Scan existing wiki pages for connection points:

```bash
grep -r "TOPIC_KEYWORDS" wiki/ -l
```

Also check these natural connections by category:
- platform pages: check if patterns pages reference the same nodes/APIs
- client pages: check if platform or patterns pages cover the underlying mechanism
- decisions pages: check if other decisions pages reference the same tradeoff

Add `[[wiki-links]]` to the Related section for any pages that genuinely connect. Don't force connections.

---

## Step 7: Update wiki/index.md

Read `wiki/index.md`.

Find the correct category line (e.g., `**Platform**`).

If NEW page: append `| [[SLUG]]` to that category's link list.
If UPDATE: no change to index needed.

Write the updated index.

---

## Step 8: Append to wiki/log.md

Read `wiki/log.md`.

Append a new row to the table:

```
| {TODAY} | conversation -- {TOPIC} | {CREATE: "wiki/CATEGORY/SLUG.md" | UPDATE: "wiki/CATEGORY/SLUG.md (new findings)"} |
```

Write the updated log.

---

## Step 9: Report

```
Wiki Filed: {TOPIC}

File:     wiki/CATEGORY/SLUG.md  ({created | updated})
Category: CATEGORY
Tags:     #{tag1} #{tag2} ...

{If related pages were found:}
Cross-linked: [[slug1]] | [[slug2]]

{If this is an update:}
Previous version preserved. New findings appended under "Update {TODAY}".

To view: wiki/CATEGORY/SLUG.md
```

---

## Rules

- Capture the insight, not the conversation. No transcript dumps.
- One concept per page. If the topic spans multiple areas, put it in the primary category and cross-link.
- If a page already exists, always UPDATE -- never overwrite. Accumulated pages gain value over time.
- The Related section is load-bearing. Good cross-links make the wiki navigable.
- Source attribution is required. Always note what triggered the learning.
- YAML is never written by this command -- wiki pages are markdown only.

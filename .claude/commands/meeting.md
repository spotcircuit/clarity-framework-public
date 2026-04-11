---
allowed-tools: Read, Write, Edit, Bash
description: Ingest meeting notes for a client from Gmail (Gemini auto-notes) into notes.md and expertise.yaml
argument-hint: <client-name> [meeting-title-keyword]
---

# SE: Meeting

Finds meeting notes for a client in Gmail (sent by Gemini auto-notes), extracts decisions,
action items, issues, and team contacts, then updates `clients/{client}/notes.md` and
appends observations to `expertise.yaml`. Makes meeting intelligence searchable and
persistent across sessions.

## Variables

CLIENT: first word of $ARGUMENTS
KEYWORD: remaining words of $ARGUMENTS (optional — narrows Gmail search)

## Resolution

Resolve CLIENT to a base directory. Check `BASE_DIR` first, then `apps/CLIENT`:
- If `BASE_DIR/expertise.yaml` exists → BASE_DIR = `BASE_DIR`
- Else if `apps/CLIENT/expertise.yaml` exists → BASE_DIR = `apps/CLIENT`
- Else if CLIENT is empty: scan both `clients/*/expertise.yaml` and `apps/*/expertise.yaml` (excluding `_templates`). If exactly one match, use it. Otherwise list all and ask.

NOTES: BASE_DIR/notes.md
EXPERTISE: BASE_DIR/expertise.yaml
CONFIG: BASE_DIR/client.yaml

## Instructions

- If CLIENT is empty: list both `ls clients/` and `ls apps/` and ask which one
- Gemini auto-notes always come from `gemini-notes@google.com`
- If KEYWORD is provided, use it to narrow the search (e.g., "standup", "discovery", "review")
- If multiple meetings are found, list them and ask which to ingest (or ingest all if user says "all")
- Never overwrite existing meeting notes — append a new dated section
- Keep extracted content faithful to the source — don't editorialize

---

## Step 1: Read Client Config

Read `BASE_DIR/client.yaml` to get `client.display_name`.

---

## Step 2: Search Gmail for Meeting Notes

Search Gmail using the Gmail MCP tool:

```
from:gemini-notes@google.com {client.display_name OR CLIENT} after:{date 14 days ago}
```

If KEYWORD is provided, add it to the query:
```
from:gemini-notes@google.com {CLIENT} {KEYWORD} after:{date 14 days ago}
```

If no results: try broader search (30 days, then 90 days).
If still no results: tell the user and suggest pasting the meeting notes directly.

---

## Step 3: Select Meeting(s)

If one result: proceed.
If multiple results: list them with date and title, ask which to ingest.
If user says "all": process each in chronological order.

---

## Step 4: Read Full Meeting Content

Read the full email body for each selected meeting.

---

## Step 5: Extract Intelligence

From the meeting body, extract:

**Decisions made** (look for: "agreed to", "decided", "confirmed", "going with", "will", past-tense conclusions)

**Action items** (look for: named person + "will" + action)
- Note who the owner is for each action
- Flag any where YOUR_NAME is the owner

**New issues or bugs** (look for: "critical", "blocking", "stuck", "not working", "only applies to", error descriptions)

**New team members mentioned** (any name not already in expertise.yaml `team:` section)

**Deployment/release events** (look for: "promoted to production", "deployed", "released", "ready for install")

**Scope changes** (anything that expands or clarifies what the solution does)

---

## Step 6: Update notes.md

Append a new section to `BASE_DIR/notes.md`:

```markdown
### {Meeting Title} — {YYYY-MM-DD}

**Attendees:** {list from meeting if available}

**Summary**
{1-2 sentence summary}

**Decisions**
- {decision 1}
- {decision 2}

**Issues Raised**
- {issue 1}
- {issue 2}

**Action Items**
- {name} — {action}
- ⭐ YOUR_NAME — {action}   ← flag Brian's items with star

**Notes**
{any other relevant context}
```

---

## Step 7: Update expertise.yaml

**Add new team members** to `team:` section (with `~` for unknown fields).

**Append to `unvalidated_observations:`**:
- One observation per decision, issue, deployment event, or scope clarification
- Format: `"{observation text} (YYYY-MM-DD — from {Meeting Title})"`
- Keep each observation atomic — one fact per line

**Update `known_issues:`** if a new blocking issue was raised:
```yaml
- jira: ~   # TODO: find Jira ticket
  title: {issue title}
  root_cause: {if known}
  workaround: {if mentioned}
  status: open
```

Validate YAML after writing:
```bash
python3 -c "import yaml; yaml.safe_load(open('BASE_DIR/expertise.yaml'))"
```

---

## Step 8: Report

```
📋 Meeting Ingested: {Meeting Title} ({date})

Extracted:
  Decisions:      {N}
  Action items:   {N} ({N} assigned to Brian)
  Issues raised:  {N} new
  Team members:   {N} new contacts added

Updated:
  BASE_DIR/notes.md       ← new section appended
  BASE_DIR/expertise.yaml ← {N} observations queued

⭐ Brian's Action Items:
  - {action 1}
  - {action 2}

Run /improve CLIENT to validate and integrate observations.
```
